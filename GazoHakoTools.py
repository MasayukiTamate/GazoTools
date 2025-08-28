'''
Created on 2025 08 27

@author: tamate masayuki
'''
import tkinter as tk
import tkinter.simpledialog


WIDTH =  200
HEIGHT = 200
WS = ""
WINDOWSSIZE = "".join([str(WIDTH),"x",str(HEIGHT)])

HakoNamae = []
DEFHAKOANMAE = ["色々、保存する箱"]
for n in DEFHAKOANMAE:
    HakoNamae.append(n)

def Hajimari():
    Gazo = tk.Tk()
    Gazo.geometry("100x50")
    Gazo.title("画像１")

def show_geometry_info(event):
    geo_label["text"] = root.geometry()

def showMenu(e):

    pmenu.post(e.x_root, e.y_root)

def namaeHenkou():
    new_name = tk.simpledialog.askstring("名前変更", "新しい名前を入力してください:", initialvalue=HakoNamae[0])
    if new_name:
        HakoNamae[0] = new_name
        for widget in root.winfo_children():
            widget.destroy()
        Hako = []
        for hn in HakoNamae:
            Hako.append(tk.Button(root,text=hn, command=Hajimari,width=int(WIDTH/10),height=int(HEIGHT/22)))
        for hk in Hako:
            hk.pack()




#基本のウィンドウ作成
root = tk.Tk()
root.attributes("-topmost",True)
root.geometry(WINDOWSSIZE)

root.title(str(""))

#ボタンの作成
Hako = []
for hn in HakoNamae:
    Hako.append(tk.Button(root,text=hn, command=Hajimari,width=int(WIDTH/10),height=int(HEIGHT/22)))
for hk in Hako:
    hk.pack()

pmenu = tk.Menu(root, tearoff=0)
pmenu.add_command(label="名前変更", command=namaeHenkou)
pmenu.add_command(label="Exit", command=root.quit)


geo_label = tk.Label(root, bg="lightblue", font=("Helvetica", "17"))
geo_label.pack(anchor="center", expand=1)

root.bind("<Button-3>", showMenu)
root.bind("<Configure>", show_geometry_info)

root.mainloop()