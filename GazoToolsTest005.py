'''
Created on 2025 09 29

@author: tamate masayuki

行程１：主窓表示
行程２：子絵窓表示
行程３：子データ窓表示
行程４：絵のフォルダ選択

'''
from lib.GazoToolsBasicLib import tkConvertWinSize
import tkinter as tk
from PIL import ImageTk, Image
import time
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
        img = Image.open("C:\\Teisyutubutu\\GazoTools\\data\\folder_32.png")
        tkimg = ImageTk.PhotoImage(img)
        width = tkimg.width()
        height = tkimg.height()

        Gazo = tk.Toplevel()
        GazoCanvas = tk.Canvas(Gazo, width=width,height=height)
        GazoCanvas.pack()
        GazoCanvas.image = tkimg
        GazoCanvas.create_image(0, 0, image=tkimg, anchor=tk.NW)
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

TKWINSIZEANDXY = tkConvertWinSize(list([200, 200, 400, 20]))
TKWINSIZEANDXY = tkConvertWinSize(list([200, 200]))

root = tk.Tk()
root.geometry(TKWINSIZEANDXY)


Gazo = GazoPicture()#画像窓出した


Gazo.Drawing()

root.mainloop()
