'''
作成者: tamate masayuki (Refactored by Antigravity)
機能: GazoTools のデータ管理、設定管理、およびロジック制御
'''
import os
import json
import random
import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageOps
import math
import ctypes
from ctypes import wintypes
from lib.GazoToolsLib import GetKoFolder, GetGazoFiles

CONFIG_FILE = "config.json"

def load_config():
    """設定ファイルを読み込むのじゃ。のじゃ。"""
    config = {
        "last_folder": os.getcwd(),
        "geometries": {},
        "settings": {
            "random_pos": False,
            "topmost": True,
            "show_folder": True,
            "show_file": True,
            "ss_mode": False,
            "ss_interval": 5,
            "move_dest_list": [""] * 12,
            "move_reg_idx": 0,
            "move_dest_count": 2
        }
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config["last_folder"] = data.get("last_folder", os.getcwd())
                config["geometries"] = data.get("geometries", {})
                saved_settings = data.get("settings", {})
                config["settings"].update(saved_settings)
                
                # move_dest_list の長さを12に強制するのじゃ（IndexError対策）
                cur_list = config["settings"].get("move_dest_list", [])
                if len(cur_list) < 12:
                    config["settings"]["move_dest_list"] = (cur_list + [""] * 12)[:12]

                if not os.path.exists(config["last_folder"]):
                    config["last_folder"] = os.getcwd()
        except:
            pass
    return config

def save_config(path, geometries=None, settings=None):
    """設定を保存するのじゃ。のじゃ。"""
    try:
        prev = load_config()
        data = {
            "last_folder": path,
            "geometries": geometries if geometries is not None else prev.get("geometries", {}),
            "settings": settings if settings is not None else prev.get("settings", {})
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"設定保存エラー: {e}")

class HakoData():
    """画像データ保持クラスなのじゃ。のじゃ。"""
    def __init__(self, def_folder):
        self.StartFolder = def_folder
        self.GazoFiles = []

    def SetGazoFiles(self, GazoFiles, folder_path):
        self.StartFolder = folder_path
        self.GazoFiles = GazoFiles

    def RandamGazoSet(self):
        if not self.GazoFiles:
            return None
        return random.choice(self.GazoFiles)

class GazoPicture():
    """画像表示制御クラスなのじゃ。のじゃ。"""
    def __init__(self, parent, def_folder):
        self.parent = parent
        self.StartFolder = def_folder
        self.random_pos = tk.BooleanVar(value=False)
        self.open_windows = {}
        self.folder_win = None
        self.file_win = None

    def SetUI(self, folder_win, file_win):
        """UIウィンドウの参照を保持するのじゃ。のじゃ。"""
        self.folder_win = folder_win
        self.file_win = file_win

    def SetFolder(self, folder):
        self.StartFolder = folder
        self.CloseAll()

    def CloseAll(self):
        """全ての画像ウィンドウを閉じるのじゃ。のじゃ。"""
        for win in list(self.open_windows.values()):
            try:
                win.destroy()
            except: pass
        self.open_windows.clear()

    def Drawing(self, fileName):
        if not fileName: return
        imageFolder = self.StartFolder
        fullName = os.path.normcase(os.path.abspath(os.path.join(imageFolder, fileName)))
        
        # 既に開いている場合は一度閉じてから再表示（リフレッシュ）
        if fullName in self.open_windows:
            try:
                self.open_windows[fullName].destroy()
            except: pass
            if fullName in self.open_windows:
                del self.open_windows[fullName]

        try:
            with Image.open(fullName) as img:
                orig_w, orig_h = img.width, img.height
                screen_w = self.parent.winfo_screenwidth()
                screen_h = self.parent.winfo_screenheight()
                limit_w, limit_h = screen_w * 0.8, screen_h * 0.8
                scale = min(limit_w / orig_w, limit_h / orig_h)
                new_w, new_h = int(orig_w * scale), int(orig_h * scale)

                img_resized = img.resize((new_w, new_h), Image.LANCZOS)
                tkimg = ImageTk.PhotoImage(img_resized)
                del img_resized # 不要になったので即座に掃除するのじゃ
            
            # 表示位置の計算
            if self.random_pos.get():
                base_x = random.randint(0, max(0, screen_w - new_w))
                base_y = random.randint(0, max(0, screen_h - new_h))
            else:
                try:
                    # 参照されているUI窓がある場合はその右横に
                    if self.file_win:
                        base_x = self.file_win.winfo_x() + self.file_win.winfo_width() + 20
                        base_y = self.file_win.winfo_y()
                        if base_x + new_w > screen_w and self.folder_win:
                            base_x = max(10, self.folder_win.winfo_x() - new_w - 20)
                    else:
                        base_x, base_y = 400, 100
                except:
                    base_x, base_y = 400, 100

            win = tk.Toplevel(self.parent)
            win.title(f"{fileName} ({int(scale*100)}%)")
            win.attributes("-topmost", True)
            self.open_windows[fullName] = win
            
            def on_img_close():
                if fullName in self.open_windows:
                    del self.open_windows[fullName]
                win.destroy()
            win.protocol("WM_DELETE_WINDOW", on_img_close)
            win.geometry(f"{new_w}x{new_h}+{base_x}+{base_y}")
            
            canvas = tk.Canvas(win, width=new_w, height=new_h)
            canvas.pack()
            canvas.image = tkimg
            canvas.create_image(0, 0, image=tkimg, anchor=tk.NW)

            # ウィンドウドラッグ移動機能の実装なのじゃ（安定版）
            def start_drag(event, target_win):
                target_win._drag_start_x = event.x_root - target_win.winfo_x()
                target_win._drag_start_y = event.y_root - target_win.winfo_y()

            def do_drag(event, target_win):
                nx = event.x_root - target_win._drag_start_x
                ny = event.y_root - target_win._drag_start_y
                target_win.geometry(f"+{nx}+{ny}")

            canvas.bind("<Button-1>", lambda e: start_drag(e, win))
            canvas.bind("<B1-Motion>", lambda e: do_drag(e, win))
        except Exception as e:
            print(f"画像表示エラー: {e}")

    def disable_all_topmost(self):
        """管理下の全ての画像ウィンドウの最前面表示を解除するのじゃ。のじゃ。"""
        for win in self.open_windows.values():
            try:
                win.attributes("-topmost", False)
            except: pass

    def get_windows_workarea(self):
        """Windows のタスクバーを除いた有効な画面領域（ワークエリア）を取得するのじゃ。のじゃ。"""
        try:
            user32 = ctypes.windll.user32
            rect = wintypes.RECT()
            # SPI_GETWORKAREA (0x0030 = 48) を呼び出してワークエリアを取得するのじゃ
            if user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        except Exception as e:
            print(f"ワークエリア取得失敗: {e}")
        
        # 失敗した場合は全画面サイズを返す（少しマージンを引くのじゃ）
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()
        return 0, 0, sw, sh - 40

    def TileWindows(self):
        """全ての画像ウィンドウをパズルのように隙間なく画面に敷き詰めるのじゃ。のじゃ。"""
        win_list = list(self.open_windows.items()) # (fullName, win) のリスト
        n = len(win_list)
        if n == 0: return

        # 画面サイズの取得（ワークエリアを考慮するのじゃ）
        avail_x, avail_y, avail_w, avail_h = self.get_windows_workarea()

        # 再帰的に領域を分割する内部関数なのじゃ
        def partition(x, y, w, h, count):
            if count <= 1:
                return [(x, y, w, h)]
            
            # 分割方向の決定（長い方を割るのじゃ）
            if w > h:
                # 縦に割る（横に並べる）
                n1 = count // 2
                n2 = count - n1
                w1 = int(w * (n1 / count))
                return partition(x, y, w1, h, n1) + partition(x + w1, y, w - w1, h, n2)
            else:
                # 横に割る（縦に並べる）
                n1 = count // 2
                n2 = count - n1
                h1 = int(h * (n1 / count))
                return partition(x, y, w, h1, n1) + partition(x, y + h1, w, h - h1, n2)

        # パズルのピース（各窓の領域）を計算
        rects = partition(avail_x, avail_y, avail_w, avail_h, n)

        # 四隅を優先したいという前回の魂を継承し、端の領域から順に画像を割り当てるのじゃ
        # (rectsの順序は分割アルゴリズム上、それなりに端から並ぶはずなのじゃ)
        
        for idx, (fullName, win) in enumerate(win_list):
            if idx >= len(rects): break
            try:
                rx, ry, rw, rh = rects[idx]
                
                # 画像を読み込んで「びっちり」させるのじゃ
                with Image.open(fullName) as img:
                    # ImageOps.fit を使ってアスペクト比を維持しつつ領域を完全に埋める（クロップあり）
                    img_fitted = ImageOps.fit(img, (rw, rh), Image.LANCZOS)
                    tkimg = ImageTk.PhotoImage(img_fitted)
                    del img_fitted
                
                # ウィンドウの更新（枠なし！）
                win.overrideredirect(True)
                win.geometry(f"{rw}x{rh}+{rx}+{ry}")
                
                # キャンバスの更新
                canvas = win.winfo_children()[0]
                canvas.config(width=rw, height=rh)
                canvas.delete("all")
                canvas.image = tkimg
                canvas.create_image(0, 0, image=tkimg, anchor=tk.NW)
                
                # ドラッグ情報の更新（枠なし移動を維持）
                def start_drag_puz(event, target_win):
                    target_win._drag_start_x = event.x_root - target_win.winfo_x()
                    target_win._drag_start_y = event.y_root - target_win.winfo_y()
                def do_drag_puz(event, target_win):
                    nx = event.x_root - target_win._drag_start_x
                    ny = event.y_root - target_win._drag_start_y
                    target_win.geometry(f"+{nx}+{ny}")
                
                canvas.bind("<Button-1>", lambda e, w=win: start_drag_puz(e, w))
                canvas.bind("<B1-Motion>", lambda e, w=win: do_drag_puz(e, w))

                print(f"[PUZZLE] {os.path.basename(fullName)} を {rw}x{rh}@{rx},{ry} に敷き詰めたのじゃ。")
            except Exception as e:
                print(f"パズル整列エラー({fullName}): {e}")
