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
import tkinter.messagebox as msgbox


#DEFOLDER = "C:\\Windows"
DEFOLDER = "C:\\"

DEFOLDER = "C:\\Users\\manaby\\Pictures\\pp.6-6"
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
        self.GazoDrawingNumFlag = []
        self.count = 0
        self.MaxCountPic = 0
        self.ListRandmPic = []
        self.GazoFiles = []
        self.GazoDrawingFlag = []
        self.PicDrawFlag = False
        pass
    def GetGazoFiles(self, GazoFiles):
        self.GazoFiles.append(GazoFiles)
        
        for _ in range(len(GazoFiles)):
            self.GazoDrawingFlag.append(0)
        pass
    def RandamGazoSet(self):
        number = int(random.uniform(0, len(self.GazoFiles)))
        print(f"{number=}")
        if not number in self.GazoDrawingNumFlag:
            self.GazoDrawingNumFlag.append(number)
            self.GazoDrawingFlag[number] = "1"
        
        return self.GazoFiles[number]
    def setMaxCountPic(self, MaxCnt):
        self.MaxCountPic = MaxCnt
        pass



class GazoPicture():
    def __init__(self):
        '''
        画像の窓
        '''
        self.StartFolder = "c:"
        self.x = 0
        self.y = 0
        self.title = "なにもない"
        self.ModeShuffle = True
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

        if HakoData1.count >= HakoData1.MaxCountPic:
            msgbox.showerror("終了処理","ファイルがないか、閲覧数が０です")
            root.quit()

            exit()           

        imageFolder = self.StartFolder
        print(f"{imageFolder=}, {fileName=}")
        
        conjunction = "\\"
        if imageFolder.endswith("\\"):
            conjunction = ""

        if self.ModeShuffle:
            fileName = HakoData1.RandamGazoSet()
        fullName = imageFolder + conjunction + fileName

        '''
        ファイル名のフルパスの合成完了
        '''
        img = Image.open(fullName)
        print(f"{img.width=} {img.height}")
        img = img.resize([int(img.width / 4 ),int(img.height / 4)])
        tkimg = ImageTk.PhotoImage(img)
        width = tkimg.width()
        height = tkimg.height()

        
        Gazo = tk.Toplevel()
        ratio = 0
        if width > height:
            ratio = width / height
        
        else:
            ratio = height / width

        self.title = str(width) + "×" + str(height) + " " + str(ratio)
        print(f"{self.title=} {ratio=}")


        GAZOSIZEXY = tkConvertWinSize(list([width, height, self.x, self.y]))
        Gazo.geometry(GAZOSIZEXY)
        Gazo.title = fullName + " " +self.title



        GazoCanvas = tk.Canvas(Gazo, width=width,height=height)
        GazoCanvas.pack()
        GazoCanvas.image = tkimg
        GazoCanvas.create_image(0, 0, image=tkimg, anchor=tk.NW)


        HakoData1.count += 1
        if HakoData1.count >= HakoData1.MaxCountPic:
            if msgbox.askyesno(title="終了処理",message="終わりますか？"):
                pass
            root.quit()


        HakoData1.PicDrawFlag = True
        
        pass
    def setTitle(self, title):
        self.title = title
        pass

def drop(event):
    print(event.data)
    text.set(event.data)
    pass

def GazoRoad( gp, fileName):
    gp.Drawing(fileName)
    root.after(1000,GazoRoad)
    pass

def key_Down(event):

    if event.keycode == 32:
        sys.exit()
    if event.keycode == "escape":
        sys.exit()

class FileTextdatProtocol():
    def __init__(self):
        FoldersList = []
        FilesList = []

        pass

class WindowsPpositionManagement():
    def __init__(self):
        MainWin = XY()
        SubWin = XY()
        TextBoxWin = XY()
        PicWin = []
        pass

    def SetPosition():
        pass

class XY():
    def __init__(self):        
        self.x = 0
        self.y = 0
        self.Widht = 200
        self.Height = 200
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
TKWINSIZEANDXY = tkConvertWinSize(list([200, 100, 1000, 20]))

WIDTH = 2400
HEIGHT = 600.
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
#文窓
TboxRoot = tk.Toplevel()
w = 200
h = 100
KOWINDSIZEXY = tkConvertWinSize(list([w, h, 200+200+200+10, 20]))
TboxRoot.geometry(KOWINDSIZEXY)
TboxRoot.overrideredirect(True)
TboxRoot.title(DADTEXT)
textbox = tk.Text(TboxRoot, width=w, height=h)
textbox.pack()


#文窓　表示関連
TEXTBOXFONTSIZE = 12

ZanFolders = []
ZanFolders.append(GetKoFolder(os.listdir(DEFOLDER),DEFOLDER))
print(f"{ZanFolders=}")

textbox.insert(tk.END, "フォルダ\n")
if not ZanFolders[0]:
    textbox.insert(tk.END, "なし\n")

for ZanFol in ZanFolders:
    textbox.insert(tk.END,ZanFol)
    textbox.insert(tk.END,"\n")
#繰り返している


h = TEXTBOXFONTSIZE * 3 + TEXTBOXFONTSIZE * len(ZanFolders)
KOWINDSIZEXY = tkConvertWinSize(list([w, h, 200+200+200+10, 20]))
TboxRoot.geometry(KOWINDSIZEXY)
#繰り返している

ZanGazoFiles = []
ZanGazoFiles.append(GetGazoFiles(os.listdir(DEFOLDER),DEFOLDER))
print(f"{ZanGazoFiles=}")

textbox.insert(tk.END,"ファイル\n")
for ZgF in ZanGazoFiles[0]:
    textbox.insert(tk.END,ZgF)
    textbox.insert(tk.END,"\n")
#繰り返している

h = h + TEXTBOXFONTSIZE * 1 + TEXTBOXFONTSIZE * len(ZanGazoFiles[0]) + TEXTBOXFONTSIZE * 2
KOWINDSIZEXY = tkConvertWinSize(list([w, h, 200+200+200+10, 20]))
TboxRoot.geometry(KOWINDSIZEXY)
#繰り返している


textbox.insert(tk.END,"ファイル数\n" + str(len(ZanGazoFiles[0])) +"枚\n")

HakoData1 = HakoData()
HakoData1.setMaxCountPic(len(ZanGazoFiles[0]))

#要枠
#画像窓
GazoWindows = []
GazoPic = []

#至急！2次元配列を1次元配列に
GazoDrawPictureData = [GazoPicture() for _ in range(len(ZanGazoFiles[0]))]

print(f"{ZanGazoFiles[0]=}")
for Gazo, GazoP in zip(ZanGazoFiles[0], GazoDrawPictureData):
    GazoP.SetFolder(DEFOLDER)
    GazoP.SetRandamXY(WIDTH,HEIGHT)

for gz in ZanGazoFiles[0]:
    HakoData1.GetGazoFiles(gz)

PicName = HakoData1.RandamGazoSet()

ProgressButton = tk.Button(root, text="画像表示", command=lambda: GazoDrawPictureData[HakoData1.count].Drawing( PicName ) )
ProgressButton.grid(row=0, column=0, padx=2)


#子窓のラベル
text = tk.StringVar(koRoot)
text = DEFOLDER
DADTEXT = "ドラッグアンドドロップ\nしてください"
DADLabel = tk.Label(koRoot, text=text, bg="lightblue", font=("Helvetica", "10"))
DADLabel.drop_target_register(DND_FILES)
DADLabel.dnd_bind("<<Drop>>",drop)
DADLabel.grid(row=0, column=0, padx=2)



root.mainloop()
