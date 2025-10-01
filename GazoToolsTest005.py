'''
Created on 2025 09 29

@author: tamate masayuki

行程１：主窓表示
行程２：子絵窓表示
行程３：子データ窓表示
行程４：絵のフォルダ選択

'''
from lib.GazoToolsBasicLib import tkConvertWinSize
from lib.GazoToolsLib import GetKoFolder
import os
import tkinter as tk
from PIL import ImageTk, Image
from tkinterdnd2 import *


DEFOLDER = "C:\\最強に最高に最強\\"
#DEFOLDER = "C:\\Windows"
DEFOLDER = "C:\\"
'''/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
クラス　メインデータ

クラス　画像窓描画

_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
'''
class HakoData():
    def __init__(self):
        StartFolder = "c:"
        pass

class GazoPicture():
    def __init__(self):

        self.StartFolder = "c:"
        pass
    def Drawing(self):
        self.folder = ""
        imageFolder = self.folder
#        img = Image.open("C:\\Teisyutubutu\\GazoTools\\data\\folder_32.png")
        img = Image.open("C:\\最強に最高に最強\\0-5bca3cde-4992-4ccc-9ca5-257c5782f870.png")
        tkimg = ImageTk.PhotoImage(img)
        width = tkimg.width()
        height = tkimg.height()

        Gazo = tk.Toplevel()
        GAZOSIZEXY = tkConvertWinSize(list([width, height, 400 + 200, 20]))
        Gazo.geometry(GAZOSIZEXY)
        GazoCanvas = tk.Canvas(Gazo, width=width,height=height)
        GazoCanvas.pack()
        GazoCanvas.image = tkimg
        GazoCanvas.create_image(0, 0, image=tkimg, anchor=tk.NW)
        pass

def drop(event):
    print(event.data)
    text.set(event.data)
    pass
'''_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_//_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/

メイン

主窓初期化
↓
画像窓初期化
↓
画像窓表示
↓
入力系
↓
主窓機能
↓
メインループ（）
_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
'''
DADTEXT = "ドラッグアンドドロップしてください"
TKWINSIZEANDXY = tkConvertWinSize(list([200, 100, 400, 20]))
TKWINSIZEANDXY = tkConvertWinSize(list([200, 100]))

#主窓
root = tk.Tk()
root.geometry(TKWINSIZEANDXY)
root.title("画像tools")
#子窓
koRoot = TkinterDnD.Tk()
koRoot.geometry(TKWINSIZEANDXY)
koRoot.title(DADTEXT)


ZanFolder = []


ZanFolder.append(GetKoFolder(os.listdir(DEFOLDER),DEFOLDER))

sefety = 0
print(f"{ZanFolder=}")
for ZanFo in ZanFolder:
    for z in ZanFo:
        print(f"{z=}")


#画像窓
#スイッチで表示
Gazo = GazoPicture()#画像窓出した
#Gazo.Drawing()

   
#子窓のラベル
text = tk.StringVar(koRoot)
DADTEXT = "ドラッグアンドドロップ\nしてください"
DADLabel = tk.Label(koRoot, text=text, bg="lightblue", font=("Helvetica", "10"))
DADLabel.drop_target_register(DND_FILES)
DADLabel.dnd_bind("<<Drop>>",drop)
DADLabel.grid(row=0, column=0, padx=2)

root.mainloop()
