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
import sys

#DEFOLDER = "C:\\Windows"

DEFOLDER = "K:\\格納-V\\新しいフォルダー"
DEFOLDER = "C:\\"
DEFOLDER = "C:\\Users\\manaby\\Pictures\\pp.6-6"
DEFOLDER = "C:\\最強に最高に最強\\"
'''/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
クラス　メインデータ

クラス　画像窓描画

_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
'''
class HakoData():
    def __init__(self):
        self.StartFolder = "c:"
        self.GazoDrawingNumFlag = []
        self.count = 0
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
        print(f"{imageFolder=}, {fileName=}")
        
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
        HakoData1.count += 1
        pass

def drop(event):
    print(event.data)
    text.set(event.data)
    pass

def GazoRoad( gp, fileName):
    gp.Drawing(fileName)
    root.after(1000,GazoRoad)
    pass


class Gazoload():
    def __init__(self):
        self.count = 0
        pass

    def load(self, gp, fileName):
        '''
        
        '''
        self.count = self.count + 1
        gp.Drawing(fileName)

        if self.count > 10:
            root.after(100, self.load)
        pass
def key_Down(event):

    if event.keycode == 32:
        sys.exit()
    if event.keycode == "escape":
        sys.exit()
        
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
root.overrideredirect(True)
root.title("画像tools")
#子窓
koRoot = TkinterDnD.Tk()
KOWINDSIZEXY = tkConvertWinSize(list([200, 100, 200+200, 20]))
koRoot.geometry(KOWINDSIZEXY)
koRoot.overrideredirect(True)
koRoot.title(DADTEXT)


ZanFolders = []

ZanFolders.append(GetKoFolder(os.listdir(DEFOLDER),DEFOLDER))
print(f"{ZanFolders=}")

ZanGazoFiles = []
ZanGazoFiles.append(GetGazoFiles(os.listdir(DEFOLDER),DEFOLDER))
print(f"{ZanGazoFiles=}")

#画像窓
#スイッチで表示

GazoWindows = []
GazoPic = []

#至急！2次元配列を1次元配列に
GazoDrawPictureData = [GazoPicture() for _ in range(len(ZanGazoFiles[0]))]

print(f"{ZanGazoFiles[0]=}")
for Gazo, GazoP in zip(ZanGazoFiles[0], GazoDrawPictureData):
    GazoP.SetFolder(DEFOLDER)
    GazoP.SetRandamXY(WIDTH,HEIGHT)
#    print(f"{Gazo=}")
#    GazoP.Drawing(Gazo)


HakoData1 = HakoData()


ProgressButton = tk.Button(root, text="画像表示", command=lambda: GazoDrawPictureData[HakoData1.count].Drawing( ZanGazoFiles[0][HakoData1.count] ) )
ProgressButton.grid(row=0, column=0, padx=2)


#子窓のラベル
text = tk.StringVar(koRoot)
DADTEXT = "ドラッグアンドドロップ\nしてください"
DADLabel = tk.Label(koRoot, text=text, bg="lightblue", font=("Helvetica", "10"))
DADLabel.drop_target_register(DND_FILES)
DADLabel.dnd_bind("<<Drop>>",drop)
DADLabel.grid(row=0, column=0, padx=2)


root.mainloop()
