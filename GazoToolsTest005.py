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

DEFOLDER = "K:\\格納-V\\新しいフォルダー"
DEFOLDER = "C:\\最強に最高に最強\\"
DEFOLDER = "C:\\"
'''/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
クラス　メインデータ

クラス　画像窓描画

_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
'''
class HakoData():
    def __init__(self):
        self.StartFolder = "c:"
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
        '''
        画像の窓
        '''
        self.StartFolder = "c:"
        self.x = 0
        self.y = 0
        pass
    def SetFolder(self, folder):
        '''
        画像のあるフォルダをセット
        '''
        self.StartFolder = folder
    def SetRandamXY(self,width,height):
        '''
        ランダムでxy座標をセット
        '''
        self.x = int(random.random() * width)
        self.y = int(random.random() * height)
        pass
    def Drawing(self, fileName):
        imageFolder = self.StartFolder

        
        conjunction = "\\"
        if imageFolder.endswith("\\"):
            conjunction = ""
        fullName = imageFolder + conjunction + fileName

        '''
        ファイル名のフルパスの合成完了
        '''
        img = Image.open(fullName)
        
        img = img.resize([int(img.width / 2 ),int(img.width / 2)])
        tkimg = ImageTk.PhotoImage(img)
        width = tkimg.width()
        height = tkimg.height()

        
        Gazo = tk.Toplevel()
        GAZOSIZEXY = tkConvertWinSize(list([width, height, self.x, self.y]))
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

WIDTH = 1200
HEIGHT = 800
#主窓
root = tk.Tk()
print(root.winfo_screenwidth())
print(root.winfo_screenheight())

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



e = str(ZanGazoFiles[0][0])


GazoPic.append(GazoPicture())
GazoPic.append(GazoPicture())
GazoPic[0].SetFolder(DEFOLDER)
GazoPic[0].SetRandamXY(1500,1000)
GazoPic[0].Drawing(e)
GazoPic[1].SetFolder(DEFOLDER)
GazoPic[1].Drawing(e)


#子窓のラベル
text = tk.StringVar(koRoot)
DADTEXT = "ドラッグアンドドロップ\nしてください"
DADLabel = tk.Label(koRoot, text=text, bg="lightblue", font=("Helvetica", "10"))
DADLabel.drop_target_register(DND_FILES)
DADLabel.dnd_bind("<<Drop>>",drop)
DADLabel.grid(row=0, column=0, padx=2)

root.mainloop()
