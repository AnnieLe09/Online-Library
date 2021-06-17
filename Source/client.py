import socket, struct, sys, os
import tkinter as tk
import json, threading
from PIL import Image, ImageTk
from tkinter import ttk, filedialog, scrolledtext

main = tk.Tk()
main.geometry("567x756")
main.title("Online Library")
main.resizable(False, False)
main.protocol("WM_DELETE_WINDOW", lambda: close_event(main))

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#Global variables
###############################################################################
BUFSIZ = 1024 * 4
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
###############################################################################

#Exit
###############################################################################
def close_event(main):
    global client, conn
    try: 
        data = {"act": 7, "ID" : "", "name" : "", "author" : "", "year" : "", "type" : ""}
        data = json.dumps(data)
        client.sendall(bytes(data, "utf8"))
    except:
        pass
    client.close()
    conn.close()
    main.destroy()
###############################################################################
    
#Canvas
###############################################################################    
canvas = tk.Canvas(main, width = 567, height = 756)
bg = Image.open(resource_path('bg.jpg'))
width, height = bg.size
bg = ImageTk.PhotoImage(bg.resize((int(2.1 * width / 3), int(2.2 * height / 3)), Image.ANTIALIAS))
canvas.create_image(0, 0, anchor = "nw", image = bg)
canvas.place(x = 0, y = 0)
frame = tk.Frame(canvas, width = 500, height = 500)
###############################################################################

#Receive raw data
###############################################################################
def Receive():
    global client
    data = b""
    while True:
        try:
            packet = client.recv(BUFSIZ)
            if len(packet) < BUFSIZ:
                data += packet
                break
            data += packet
        except:
            pass
    return data

def recvall(sock, size):
    message = bytearray()
    while len(message) < size:
        buffer = sock.recv(size - len(message))
        if not buffer:
            raise EOFError('Could not receive all expected data!')
        message.extend(buffer)
    return bytes(message)
###############################################################################

#Read book
###############################################################################
def read():
    global main, booklist, client
    ops = booklist.item(booklist.selection())['values']
    if len(ops) > 0:
        data = {"act": 4, "ID" : ops[0], "name" : ops[1], "author" : ops[2], "year" : ops[3], "type" : ops[4]}
        rw = tk.Toplevel(main)
        rw.geometry("567x756")
        rw.title(data["name"])
        data = json.dumps(data)
        try: client.sendall(bytes(data, "utf8"))
        except: 
             tk.messagebox.showerror(message = "Server disconnected!")
             close_event(main)
        cv = tk.Label(rw)
        cv.place(x = 283, y = 378, anchor = 'center')
        bg = Image.open(resource_path('bg2.jpg'))
        width, height = bg.size
        bg = ImageTk.PhotoImage(bg.resize((int(2.1 * width / 3), int(2.2 * height / 3)), Image.ANTIALIAS))
        cv.configure(image = bg)
        cv.image = bg
        content = scrolledtext.ScrolledText(rw, wrap = tk.WORD, height = 35, width = 63)
        content.place(x = 20, y = 150)
        #data = Receive()
        
        packed = recvall(client, struct.calcsize('!I'))
        size = struct.unpack('!I', packed)[0]
        data = recvall(client, size)
        
        s = data.decode("utf8")
        content.insert(tk.END, s)
        content.config(state = "disable")    
###############################################################################    

#Download book
###############################################################################
def download():
    global booklist, client
    ops = booklist.item(booklist.selection())['values']
    if len(ops) > 0:
        d = {"act": 5, "ID" : ops[0], "name" : ops[1], "author" : ops[2], "year" : ops[3], "type" : ops[4]}
        data = json.dumps(d)
        client.sendall(bytes(data, "utf8"))
        file = filedialog.asksaveasfilename(defaultextension = '.txt', filetypes = [("Text file", ".txt"), ("All files", ".*")], title = "Choose filename")
        if not file:
            return
        
        packed = recvall(client, struct.calcsize('!I'))
        size = struct.unpack('!I', packed)[0]
        data = recvall(client, size)
        
        with open(file, 'wb') as f:
            f.write(data)
            f.close()        
###############################################################################

#Search for book
###############################################################################
def search():
    global search_entry, booklist, classify_ops, client
    search = search_entry.get()
    ops = classify_ops.get()
    if len(search) > 0 and "Search By" not in ops:
        data = {"act": 3, "ID" : "", "name" : "", "author" : "", "year" : "", "type" : ""}
        data[ops] = search
        data = json.dumps(data)
        client.sendall(bytes(data, "utf8"))
        res = client.recv(BUFSIZ).decode("utf8")
        res = json.loads(res)
        for i in booklist.get_children():
            booklist.delete(i)
        for book in res:
            booklist.insert(parent = '', index = 'end', text = '', values = (book['ID'], book['name'], book['author'], book['year'], book['type']))
    return
###############################################################################
#Logout
###############################################################################
def logout():
    global client, booklist, search_btn, read_btn, download_btn, logout_btn, search_bar, classify_menu, scroll, frame
    data = {"act": 6, "ID" : "", "name" : "", "author" : "", "year" : "", "type" : ""}
    data = json.dumps(data)
    client.sendall(bytes(data, "utf8"))
    frame.place_forget()
    #booklist.grid_forget() 
    #scroll.grid_forget()
    search_btn.place_forget() 
    read_btn.place_forget() 
    download_btn.place_forget() 
    logout_btn.place_forget()
    search_bar.place_forget() 
    classify_menu.place_forget()
    f1()
###############################################################################

#Frame 2
###############################################################################
def hide_f1():
     global acc_label, pw_label, acc_in, pw_in, login_btn, signup_btn
     acc_label.place_forget() 
     pw_label.place_forget() 
     acc_in.place_forget()
     pw_in.place_forget()
     login_btn.place_forget()
     signup_btn.place_forget()
     
def f2():
    global canvas, search_entry, booklist, classify_ops, search_btn, read_btn, download_btn, logout_btn, search_bar, classify_menu, scroll, frame
    hide_f1()
    #Search bar
    search_entry = tk.StringVar()
    search_bar = tk.Entry(canvas, textvariable = search_entry, width = 50, borderwidth = 5)
    search_bar.place(x = 30, y = 50)
    #Option menu
    classify_ops = tk.StringVar()
    classify_ops.set("Search By")
    classify_menu = tk.OptionMenu(canvas, classify_ops, "ID", "name", "type", "author")
    classify_menu.config(width = 7)
    classify_menu.place(x = 340, y = 48)
    #Book List
    #f2 = tk.Frame(width = 500, height = 500)
    frame.place(x = 20, y = 180)
    scroll = tk.Scrollbar(frame)
    scroll.grid(row = 1, column = 6, sticky = "nsew")
    booklist = ttk.Treeview(frame, height = 22)
    scroll.configure(command = booklist.yview)
    booklist.configure(yscrollcommand = scroll.set)
    booklist['columns'] = ("ID", "name", "author", "year", "type")
    booklist.column('#0', width=0)
    booklist.column("ID", anchor="center", width = 50, minwidth = 10, stretch = True)
    booklist.column("name", anchor="center", width = 150, minwidth = 10, stretch = True)
    booklist.column("author", anchor="center", width = 150, minwidth = 10, stretch = True)
    booklist.column("year", anchor="center", width = 50, minwidth = 10, stretch = True)
    booklist.column("type", anchor="center", width = 100, minwidth = 10, stretch = True)
    booklist.heading('#0', text='')
    booklist.heading("ID", text = "ID")
    booklist.heading("name", text = "Name")
    booklist.heading("author", text = "Author")
    booklist.heading("year", text = "Year")
    booklist.heading("type", text = "Type")
    booklist.grid(row = 1, column = 0, columnspan = 6, sticky = "nse")
    #Buttons
    search_btn = tk.Button(canvas, text = 'SEARCH', width = 10, height = 1, bg = 'IndianRed3', command = search)
    search_btn.place(x = 430, y = 50)    
    read_btn = tk.Button(canvas, text = 'READ', width = 30, height = 2, bg = 'IndianRed3', command = read)
    read_btn.place(x = 50, y = 650)
    download_btn = tk.Button(canvas, text = 'DOWNLOAD', width = 30, height = 2, bg = 'IndianRed3', command = download)
    download_btn.place(x = 300, y = 650)   
    logout_btn = tk.Button(canvas, text = 'LOG OUT', width = 66, height = 1, bg = 'royalblue4', command = logout)
    logout_btn.place(x = 50, y = 700)
###############################################################################

#Login
###############################################################################    
def login():
    global acc_entry, pw_entry, client
    data = json.dumps({"act": 1, "username": acc_entry.get(), "password": pw_entry.get()})
    client.sendall(bytes(data, "utf8"))
    msg = client.recv(BUFSIZ).decode()
    if '1' in msg:
        f2()
    elif '2' in msg:
        tk.messagebox.showerror(message = "Wrong password!")
    else:
        tk.messagebox.showerror(message = "Account doesn't exist!")
###############################################################################
        
#Sign up
###############################################################################
def signup():
    global acc_entry, pw_entry, client
    acc = acc_entry.get()
    pw = pw_entry.get()
    if len(pw) < 6:
        tk.messagebox.showerror(message = "Password must contain at least 6 characters!")
        return
    if not pw.isalnum():
        tk.messagebox.showerror(message = "Password must only contain alphabets and numbers!")
        return
    if not acc.isalnum():
        tk.messagebox.showerror(message = "Username must only contain alphabets and numbers!")
        return
    data = json.dumps({"act": 2, "username": acc, "password": pw})
    client.sendall(bytes(data, "utf8"))
    msg = client.recv(BUFSIZ).decode()
    if '1' in msg:
        tk.messagebox.showinfo(message = "Sign up successfully!")
    else:
        tk.messagebox.showerror(message = "Account exists!")
###############################################################################
        
#Frame 1
###############################################################################        
def f1():
    global canvas, acc_entry, pw_entry, acc_label, pw_label, acc_in, pw_in, login_btn, signup_btn
    acc_label = tk.Label(canvas, text = 'Username')
    acc_label.place(x = 140, y = 510)
    pw_label = tk.Label(canvas, text = 'Password')
    pw_label.place(x = 140, y = 560)
    acc_entry = tk.StringVar()
    acc_in = tk.Entry(canvas, textvariable = acc_entry, width = 38, borderwidth = 5)
    acc_in.place(x = 220, y = 500, width = 240, height = 40)
    pw_entry = tk.StringVar()
    pw_in = tk.Entry(canvas, show = "*", textvariable = pw_entry, width = 38, borderwidth = 5)
    pw_in.place(x = 220, y = 550, width = 240, height = 40)
    login_btn = tk.Button(canvas, text = 'LOGIN', width = 20, height = 2, bg = 'IndianRed3', command = login)
    login_btn.place(x = 140, y = 600)
    signup_btn = tk.Button(canvas, text = 'SIGN UP', width = 20, height = 2, bg = 'royalblue4', command = signup)
    signup_btn.place(x = 310, y = 600)
###############################################################################

#Disconnect to server
###############################################################################
def disconnect():
    global conn, main
    while True:
        try:
            msg = conn.recv(BUFSIZ).decode("utf8")
            tk.messagebox.showerror(message = "Server disconnected!")
            close_event(main)
        except:
            pass
###############################################################################
            
#Connect
###############################################################################
def connect(ip, ip_entry, conn_btn):
        global client, conn
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_addr = ip.get()
        try:
            client.connect((ip_addr, 1713))
            conn.connect((ip_addr, 1317))
            msg = client.recv(BUFSIZ).decode("utf8")
            if "1" in msg:
                tk.messagebox.showinfo(message = "Connect successfully!")
                ip_entry.place_forget()
                conn_btn.place_forget()
                threading.Thread(target = disconnect).start()
                f1()
            elif "0" in msg:
                tk.messagebox.showerror(message = "Cannot connect!")
                client.close()
                conn.close()
        except:
            tk.messagebox.showerror(message = "Cannot connect!")       
###############################################################################

#Frame 0
###############################################################################
def f0():
    global client, canvas
    ip = tk.StringVar()
    ip_entry = tk.Entry(canvas, textvariable = ip, width = 38, borderwidth = 3)
    ip_entry.place(x = 100, y = 500, width = 240, height = 40)
    conn_btn = tk.Button(canvas, text = 'CONNECT', width = 20, height = 2, bg = 'IndianRed3', command = lambda: connect(ip, ip_entry, conn_btn))
    conn_btn.place(x = 342, y = 500)
###############################################################################

f0()
main.mainloop()
