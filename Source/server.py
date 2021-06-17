import socket, struct, gc
import tkinter as tk
import threading, json


main = tk.Tk()
main.geometry("600x500")
main.title('Online Library Server')
main.resizable(False, False)
main.protocol("WM_DELETE_WINDOW", lambda: close_event(main))

current_status = tk.Text(main)
current_status.config(state='disable')
current_status.pack()

#Global variables
###############################################################################
clients = []
conns = []
BUFSIZ = 1024 * 4
THREADS = 10
acc_db = 'accounts.json'
books_db = 'books.json'
books_path = 'resources/'
###############################################################################    
def close_event(main):
    global num, label, btn, n_entry, exit_btn, current_status
    for conn in conns:
        try: 
            conn.sendall(bytes("QUIT", "utf8"))
        except: 
            pass
        
    for conn in conns:
        conn.close()
        conns.remove(conn)
        
    for client in clients:
        client.close()
        clients.remove(client)
    main.destroy()
    main = None
    num = None
    label = None
    btn = None
    n_entry = None
    exit_btn = None
    current_status = None
    gc.collect()
    
    
def parse_request(d):
    return d['ID'], d['name'], d['author'], d['year'], d['type']

def update_status(line):
    global current_status
    current_status.config(state='normal')
    current_status.insert(tk.END, "\n" + line)
    current_status.config(state='disable')

#load database ======================
def load_database(db_name):
    data = list()
    try:
        with open(db_name) as f:
            data = json.load(f)
            f.close()
    except:
        pass
    return data
        
def sendbook(client, addr, ID):
    global books_path
    with open(books_path + ID + '.txt', 'rb') as f:
         data = f.read()
         f.close()
    size = struct.pack('!I', len(data))
    data = size + data
    client.sendall(data)

#Search
def find_book(client, addr, key, value):
    global books_db
    book_list = load_database(books_db)
    res = list()
    cnt = 0
    for book in book_list:
        if str(value).lower() in str(book[key]).lower():
            res.append(book)
            cnt += 1
    res = json.dumps(res)
    client.sendall(bytes(res, "utf8"))
    
def search(client, addr, req):
    ID, name, author, year, typ = parse_request(req)
    if len(ID) > 0:
        find_book(client, addr, "ID", ID)
        return ID + ' by ID' 
    elif len(name) > 0:
        find_book(client, addr, "name", name)
        return name + ' by name' 
    elif len(author) > 0:
        find_book(client, addr, "author", author)
        return author + ' by author' 
    elif len(year) > 0:
        find_book(client, addr, "year", year)
        return year + ' by year' 
    else:
        find_book(client, addr, "type", typ)
        return typ + ' by type' 
        

def login(client, addr, username, password):
    global acc_db, current_status
    acc_list = load_database(acc_db)
    for account in acc_list:
        if account['username'] == username:
            if account['password'] == password:
                update_status(addr + ' - ' + username + ' : login successfully')
                client.sendall(bytes("1", "utf8"))
                return '1'
            else:
                update_status(addr + ' - ' + username + ' : login wrong password')
                client.sendall(bytes("2", "utf8"))
                return '2'
    update_status(addr + ' - ' + username + ' : login unavailable account')
    client.sendall(bytes("3", "utf8"))
    return '3'

def add_account(username, password):
    global acc_db
    acc_list = load_database(acc_db);
    acc_list.append({"username" : username, "password" : password})
    with open(acc_db, 'w') as f:
        new_data = json.dumps(acc_list, indent = 4)
        f.write(new_data)
        f.close()
        
def signup(client, addr, username, password):
    global acc_db
    acc_list = load_database(acc_db);
    for account in acc_list:
        if account['username'] == username:
            update_status(addr + ' - ' + username + ' : sign up existing account')
            client.sendall(bytes("0", "utf8"))
            return '0'
    add_account(username, password)
    client.sendall(bytes("1", "utf8"))
    update_status(addr + ' - ' + username + ' : sign up successfully')
    return '1'

def client_handler(client, addr, conn):
    global clients, conns, count
    while True:
        msg = ""
        try:
            msg = client.recv(BUFSIZ).decode("utf8")
        except:
            return
        msg = json.loads(msg)
        ID = msg['act']
        if ID == 7:
            update_status(addr + ' : disconnected')
            clients.remove(client)
            conns.remove(conn)
            return
        un = msg['username']
        pw = msg['password']
        if ID == 2:
            signup(client, addr, un, pw)
        elif ID == 1:
            res = login(client, addr, un, pw)
            if res == "1":
                while True:
                    req = ""
                    try:
                        req = client.recv(BUFSIZ).decode("utf8")
                    except: 
                        return
                    req = json.loads(req)
                    act = req['act']
                    if act == 3:
                        tmp = search(client, addr, req)
                        update_status(addr + ' - ' + un + ' : search for ' + tmp)
                    elif act == 4:
                        sendbook(client, addr, req['ID'])
                        update_status(addr + ' - ' + un + ' : read book that has ID ' + req['ID'])
                    elif act == 5:
                        sendbook(client, addr, req['ID'])
                        update_status(addr + ' - ' + un + ' : download book that has ID ' + req['ID'])
                    elif act == 6:
                        update_status(addr + ' - ' + un + ' : logout')
                        break
                    elif act == 7:
                        update_status(addr + ' : disconnected')
                        clients.remove(client)
                        conns.remove(conn)
                        return               

#Connect    
def connect(n):
    n = int(n)
    global exit_btn, main, clients, conns
    exit_btn = tk.Button(main, text = "EXIT", width = 15, height = 3, bg = "gray", fg = "yellow", command = lambda: close_event(main))
    exit_btn.pack()
    #Port 1713
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 1713))
    s.listen(n)
    #Port 1317
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    c.bind(('', 1317))
    c.listen(n)
    while True:
        client, addr = s.accept()
        conn, add = c.accept()
        if len(clients) == n:
            client.sendall(bytes("0", "utf8"))
            client.close()
            conn.close()
        else:
            client.sendall(bytes("1", "utf8"))
            ip_addr, port = client.getpeername()
            update_status(ip_addr + ' : connected to server')
            clients.append(client)
            conns.append(conn)
            threading._start_new_thread(client_handler, (client, ip_addr, conn))

def f1():
    global num, label, btn, n_entry 
    n = num.get()
    if n.isnumeric() and int(n) > 0: 
        label.pack_forget()
        btn.pack_forget()
        n_entry.pack_forget()
        threading._start_new_thread(connect, (n, )) 
    else:
        tk.messagebox.showerror(message = "The input must be a number greater than 0!")
    

def f0():
    global main, label, num, n_entry, btn
    label = tk.Label(main, text = "Input the number of clients")
    label.pack()
    num = tk.StringVar()
    n_entry = tk.Entry(main, textvariable = num, width = 38, borderwidth = 3)
    n_entry.pack()    
    btn = tk.Button(main, text = "OPEN", width = 15, height = 3, bg = "gray", fg = "yellow", command = f1)
    btn.pack()
if __name__ == "__main__":
    f0()
    main.mainloop()
