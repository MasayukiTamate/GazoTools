'''
Created on 2021/12/19

@author: magor
'''
import tkinter as tk
import tkinter.filedialog
import os
from PIL import Image, ImageTk
import tkinter.messagebox as msg
import random

root = 0
canvas = 0 
img1 = []
img2 = []
folder = []
j = 0
rectangles = {}
num = 0
#基本のウィンドウ作成
root = tk.Tk()
root.attributes("-fullscreen", True)
root.title(str(""))
canvas = tk.Canvas(root, width=1920, height=1080)
canvas.place(x=0, y=0)
#ここまで
file_namae = []

#ダイアログからフォルダ名取得関数
def GetDiaFolder():
    
    #file_path = tk.filedialog.askdirectory(initialdir = dir)


    x_path = file_path.split("/")
    f_name = file_path[0:len(file_path)-(len(x_path[-1]))]
    x = file_path[:len(file_path)-(len(x_path[-1]))-1]
    files = os.listdir(x)
    
    return files, f_name
#ループ１
#ループ２
#格納したデータを再描画
def Kurikaesi():
#    global img1
    flag1 = 1
    while flag1:
        canvas.create_image(random.randint(0,1000),random.randint(0,500),image=img1[i],tag="illust",anchor=tk.NW)
        i = i + 1
        if i >= len(img1):
            flag1 = 0
        root.update()
#クリックした画像を一番最後に描写
def Kurikaesi2(n):
    global num
    flag1 = 1
    i = 0 
    img4 = [ImageTk.PhotoImage(image.copy()) for image in img1]
    for i in img2:
        canvas.delete(i)
    while flag1:
            
        

        

#        x1 = random.randint(0,1000)
#        y1 = random.randint(0,500)
#        x2 = x1 + img4[i].width()
#        y2 = y1 + img4[i].height()
        if not(n == i):
#            rectangle = canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
            canvas.create_image(x1,y1,image=img4[i],tag="illust",anchor=tk.NW)
#            rectangles[rectangle] = num# 四角形に番号を割り当てる
            
        num = num + 1
        root.update()
 
        i = i + 1
        if i >= len(img4):
            flag1 = 0
        
#    x1 = random.randint(0,1000)
#   y1 = random.randint(0,500)
#    x2 = x1 + img4[n].width()
#    y2 = y1 + img4[n].height()
#    rectangle = canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
    canvas.create_image(x1,y1,image=img4[n],tag="illust",anchor=tk.NW)
#    rectangles[rectangle] = num# 四角形に番号を割り当てる
    num = num + 1
    root.update()


#ループ３
#取得したフォルダの新しい画像データを読み込む
#def GetDiaFileName():
def SinByouGa():
#    global j,img1
    flag2 = 1
    i = len(img1)
    while flag2:
        x_path = file_path.split("/")
        f_name = file_path[0:len(file_path)-(len(x_path[-1]))]
        x = file_path[:len(file_path)-(len(x_path[-1]))-1]
        fol = x + "/" + folder[j] + "/"
        files = os.listdir(fol)

        msg.showinfo(folder[j],str(len(files)) + "個")

        for f in files:
            o = str(f)

            if(o[-4:]==".jpg" or o[-4:]==".png"):
                global num
                img1.append(Image.open(open(str(fol)+str(o), 'rb')))
                img1[i].thumbnail((500, 500), 0)
                img1[i] = ImageTk.PhotoImage(img1[i])
                x1 = random.randint(0,1000)
                y1 = random.randint(0,500)
                x2 = x1 + img1[i].width()
                y2 = y1 + img1[i].height()
        
                rectangle = canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
                rectangles[rectangle] = num# 四角形に番号を割り当てる
                canvas.create_image(x1,y1,image=img1[i],tag="illust",anchor=tk.NW)

                num = num + 1
                i = i + 1
                root.update()
        
        flag2 = 0

    return
#再描画クリックした画像を一番上
#子フォルダの取得
def GetKoFolder(files):
    for f in files:
        o = str(f)
        if not(o[0] == "."):
            if len(o) >= 4:
                if not(o[-4]=="."):
                    if not(o[-3]=="."):
                        folder.append(o)
            else:
                folder.append(o)

    for f in folder:
        print(f)

    return


file_path = tk.filedialog.askopenfilename(initialdir=".")

files, f_name = GetDiaFolder()
GetKoFolder(files)
msg.showinfo("","")


i = 0
for f in files:
    o = str(f)
    if(o[-4:]==".jpg" or o[-4:]==".png"):
        
        img1.append(Image.open(open(str(f_name)+str(o), 'rb')))
        img1[i].thumbnail((500, 500), 0)
        img2.append(ImageTk.PhotoImage(img1[i]))
        x1 = random.randint(0,1000)
        y1 = random.randint(0,500)
        x2 = x1 + img2[i].width()
        y2 = y1 + img2[i].height()
        
        rectangle = canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
        rectangles[rectangle] = num# 四角形に番号を割り当てる
        canvas.create_image(x1,y1,image=img2[i],tag="illust",anchor=tk.NW)

        root.update()

        num = num + 1
        
        i = i + 1

img3 = [ImageTk.PhotoImage(image.copy()) for image in img1]


def on_canvas_click(self, event):
    msg.showinfo("終わりのか…")
    exit()
    return
    

#def leftClick(event):
def rightClick(event):
    global j,folder
    if j >= len(folder):
        a = msg.askokcancel("", "終わり？")
        if a:
            exit()
        else:
            global file_path, f_name
            file_path = tk.filedialog.askopenfilename(initialdir=".")
            files, f_name = GetDiaFolder()
            GetKoFolder(files)


#        msg.showinfo("終わり","")
#        exit()

    SinByouGa()

    j = j + 1
    return
    

def middleClick(event):
#    print('Middle')
    exit()
    return

def leftClick(event):
    print('left')

    item = canvas.find_closest(event.x, event.y)[0]
    print(item)
    item1 = item - 1
    rectangle_number = 0
    if item1 in rectangles:
        rectangle_number = rectangles[item1]
        print(f"Rectangle number: {rectangle_number}")    
        Kurikaesi2(rectangle_number)
    return

def ReturnDown(event):
    print("エンター")
    global j,folder
    if j >= len(folder):
        a = msg.askokcancel("", "終わり？")
        if a:
            exit()
        else:
            global file_path, f_name
            file_path = tk.filedialog.askopenfilename(initialdir=".")
            files, f_name = GetDiaFolder()
            GetKoFolder(files)

    SinByouGa()

    j = j + 1

    return

def key_event(e):
    print(e.keysym)
    global j,folder

    if e.keysym == "Return" or e.keysym == "space":
        if j >= len(folder):
            a = msg.askokcancel("", "終わり？")
            if a:
                exit()
            else:
                msg.showinfo("","",x=0)
                global file_path, f_name
                file_path = tk.filedialog.askopenfilename(initialdir=".")
                files, f_name = GetDiaFolder()
                GetKoFolder(files)

        SinByouGa()

    j = j + 1

    return
canvas.bind('<Button-1>', leftClick)
canvas.bind('<Button-2>', middleClick)
canvas.bind('<Button-3>', rightClick)
canvas.bind("<Return>", ReturnDown)
root.bind("<KeyPress>", key_event)
canvas.pack()



root.mainloop()