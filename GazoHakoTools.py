'''
Created on 2025 08 27

@author: tamate masayuki

hakoNamae~BoxName
namaeHenkou=nameChange
hajimari=begins,start

フォルダを取得するときに子フォルダも取得する
ファイルのリスト化
ファイルのリストをテキストボックスで表示

'''
import tkinter as tk
import tkinter.simpledialog
import tkinter.filedialog
import os
from PIL import Image, ImageTk

WIDTH =  200
HEIGHT = 200
WS = ""
WINDOWSSIZE = "".join([str(WIDTH),"x",str(HEIGHT)])

dirName = "K:\\100-eMomo"
fileName = "1165046190117.jpg"
fullFileName = dirName + "\\" + fileName
print(fullFileName)
img = []
HakoNamae = []
DEFHAKOANMAE = ["色々、保存する箱"]
for n in DEFHAKOANMAE:
    HakoNamae.append(n)

def Hajimari():
    Gazo = tk.Tk()
    Gazo.geometry("100x50")
    Gazo.title("画像１")
    GazoCanvas = tk.Canvas(Gazo, width=100, height=50)
    GazoCanvas.pack()
    fileStr = fullFileName
    #ランダムで表示する＋同じ絵は出てほしくない
    GazoHyoji(GazoCanvas,fileStr)
    Gazo.update()

def GazoHyoji(GazoCanvas,fileStr):
#    img.append(ImageTk.open(open(str(fileStr),"rb")))
    img.append(ImageTk.PhotoImage(file=str(fullFileName)))
    GazoCanvas.create_image(0,0,image=img,tag="illust",anchor="nw")

    pass

def hako_info(event):
    hakoLabel["text"] = HakoNamae


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
            Hako.append(tk.Button(root,text=hn+"\n"+dirName, command=Hajimari,width=int(WIDTH/10),height=int(HEIGHT/22)))
        for hk in Hako:
            hk.pack()

def kaisouHenkou():
    global dirName
    if dirName:
        iDir = dirName
    else:
        iDir = os.path.abspath(os.path.dirname(__file__))
    iDirPath = tk.filedialog.askdirectory(initialdir = iDir)

    dirName = iDirPath
    print(dirName)  # fの中身を表示する


    pass

def HakoSakusei():
    Hako = []
    for hn in HakoNamae:
        Hako.append(tk.Button(root,text=hn+"\n"+dirName, command=Hajimari,width=int(WIDTH/10),height=int(HEIGHT/22)))
    for hk in Hako:
        hk.pack()

    pass












#基本のウィンドウ作成
root = tk.Tk()
root.attributes("-topmost",True)
root.geometry(WINDOWSSIZE)

root.title(str(""))

#ボタンの作成
HakoSakusei()

pmenu = tk.Menu(root, tearoff=0)
pmenu.add_command(label="名前変更", command=namaeHenkou)
pmenu.add_command(label="フォルダ指定",command=kaisouHenkou)
pmenu.add_command(label="Exit", command=root.quit)

hakoLabel = tk.Label(root, bg="lightblue", font=("Helvetica", "17"))
geo_label = tk.Label(root, bg="lightblue", font=("Helvetica", "17"))
geo_label.pack(anchor="center", expand=1)


#アプデ予定：右クリック＋座標またはどのボタンの上かを引数にして命令を続ける
root.bind("<Button-3>", showMenu)
root.bind("<Configure>", hako_info)
root.bind("<Configure>", show_geometry_info)

root.mainloop()