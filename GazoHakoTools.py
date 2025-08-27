'''
Created on 2025 08 27

@author: tamate masayuki
'''
import tkinter as tk

WIDTH =  200
HEIGHT = 200
WS = ""
WINDOWSSIZE = "".join([str(WIDTH),"x",str(HEIGHT)])

HakoNamae = []
DEFHAKOANMAE = ["癖に刺さる"]
for n in DEFHAKOANMAE:
    HakoNamae.append(n)

def Hajimari():
    Gazo = tk.Tk()
    Gazo.geometry("100x50")
    Gazo.title("画像１")

def show_geometry_info(event):
    geo_label["text"] = root.geometry()


#基本のウィンドウ作成
root = tk.Tk()
root.attributes("-topmost",True)
root.geometry(WINDOWSSIZE)

root.title(str(""))
Hako = []
for hn in HakoNamae:
    Hako.append(tk.Button(root,text=hn, command=Hajimari,width=int(WIDTH/10),height=int(HEIGHT/22)))

for hk in Hako:
    hk.pack()


geo_label = tk.Label(root, bg="lightblue", font=("Helvetica", "17"))
geo_label.pack(anchor="center", expand=1)
root.bind("<Configure>", show_geometry_info)

root.mainloop()