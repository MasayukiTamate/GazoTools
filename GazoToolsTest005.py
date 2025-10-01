'''
Created on 2025 09 29

@author: tamate masayuki

行程１：主窓表示
行程２：子絵窓表示
行程３：子データ窓表示
行程４：絵のフォルダ選択

'''
from lib.GazoToolsBasicLib import tkConvertWinSize
from lib.GazoToolsLib import GetKoFolder, GetGazoFiles
import os
import tkinter as tk
from PIL import ImageTk, Image
from tkinterdnd2 import *
import random

#DEFOLDER = "C:\\Windows"
DEFOLDER = "C:\\"
DEFOLDER = "K:\\格納-V\\新しいフォルダー"
DEFOLDER = "C:\\最強に最高に最強\\"
'''/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
クラス　メインデータ

クラス　画像窓描画

_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
'''
class HakoData():
    def __init__(self):
        self.StartFolder = "c:"
        self.GazoFiles = []
        self.GazoDrawingFlag = []
        self.GazoDrawingNumFlag = []
        pass
    def GetGazoFiles(self, GazoFiles):
        self.GazoFiles.append(GazoFiles)
        
        for _ in range(len(GazoFiles)):
            self.GazoDrawingFlag.append(0)
        pass
    def RandamGazoSet(self):
        number = int(random.random(0,len(self.GazoFiles)))
        if not number in self.GazoDrawingNumFlag:
            self.GazoDrawingNumFlag.append(number)
            self.GazoDrawingFlag[number] = "1"
        
        return self.GazoFiles[number]

class GazoPicture():
    def __init__(self):

        self.StartFolder = "c:"
        pass
    def SetFolder(self, folder):
        self.StartFolder = folder

    def Drawing(self, fileName):
        imageFolder = self.StartFolder
#        print(f"{imageFolder=} {fileName=}")
        fullName = imageFolder + "\\" + fileName
        print(f"{fullName=}")
        img = Image.open(fullName)
        
        img = img.resize([int(img.width / 2 ),int(img.width / 2)])
        tkimg = ImageTk.PhotoImage(img)
        width = tkimg.width()
        height = tkimg.height()

        
        Gazo = tk.Tk()
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
TKWINSIZEANDXY = tkConvertWinSize(list([200, 100]))
TKWINSIZEANDXY = tkConvertWinSize(list([200, 100, 200, 20]))

#主窓
root = tk.Tk()
root.geometry(TKWINSIZEANDXY)
root.title("画像tools")
#子窓
koRoot = TkinterDnD.Tk()
KOWINDSIZEXY = tkConvertWinSize(list([200, 100, 200+200, 20]))
koRoot.geometry(KOWINDSIZEXY)
koRoot.title(DADTEXT)


ZanFolders = []

ZanFolders.append(GetKoFolder(os.listdir(DEFOLDER),DEFOLDER))
#print(f"{ZanFolders=}")

ZanGazoFiles = []
ZanGazoFiles.append(GetGazoFiles(os.listdir(DEFOLDER),DEFOLDER))
#print(f"{ZanGazoFiles=}")

#画像窓
#スイッチで表示

GazoWindows = []
GazoPic = []

#GazoWindows.append(tk.Tk())

Gazo = GazoPicture()

Gazo.SetFolder(DEFOLDER)


   
#子窓のラベル
text = tk.StringVar(koRoot)
DADTEXT = "ドラッグアンドドロップ\nしてください"
DADLabel = tk.Label(koRoot, text=text, bg="lightblue", font=("Helvetica", "10"))
DADLabel.drop_target_register(DND_FILES)
DADLabel.dnd_bind("<<Drop>>",drop)
DADLabel.grid(row=0, column=0, padx=2)

root.mainloop()
