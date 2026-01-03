'''
作成者: tamate masayuki (Refactored by Antigravity)
機能: GazoTools のデータ管理、設定管理、およびロジック制御
'''
import os
import json
import random
import csv
import hashlib
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import ImageTk, Image, ImageOps
import math
import ctypes
from ctypes import wintypes
from lib.GazoToolsLib import GetKoFolder, GetGazoFiles
from lib.GazoToolsAI import VectorEngine
import threading
import time

TAG_CSV_FILE = os.path.join(os.path.dirname(__file__), "data", "tagdata.csv")
VECTOR_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "vectordata.json")

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
            "ss_ai_mode": False,   # AI類似度再生モード
            "ss_ai_threshold": 0.65, # 類似度の閾値
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

def calculate_file_hash(filepath):
    """ファイルのMD5ハッシュ値を計算するのじゃ。のじゃ。"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def load_tags():
    """タグデータを読み込むのじゃ。のじゃ。"""
    tags = {} # key: hash, value: {tag: "...", hint: "..."}
    if os.path.exists(TAG_CSV_FILE):
        try:
            with open(TAG_CSV_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        h = row[0]
                        t = row[1]
                        hint = row[2] if len(row) > 2 else ""
                        tags[h] = {"tag": t, "hint": hint}
        except Exception as e:
            print(f"タグ読み込みエラー: {e}")
    return tags

def save_tags(tags):
    """タグデータを保存するのじゃ。のじゃ。"""
    try:
        os.makedirs(os.path.dirname(TAG_CSV_FILE), exist_ok=True)
        with open(TAG_CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for h, data in tags.items():
                writer.writerow([h, data["tag"], data["hint"]])
    except Exception as e:
        print(f"タグ保存エラー: {e}")

def load_vectors():
    """ベクトルデータを読み込むのじゃ。のじゃ。"""
    if os.path.exists(VECTOR_DATA_FILE):
        try:
            with open(VECTOR_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_vectors(vectors):
    """ベクトルデータを保存するのじゃ。のじゃ。"""
    try:
        os.makedirs(os.path.dirname(VECTOR_DATA_FILE), exist_ok=True)
        with open(VECTOR_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(vectors, f)
    except Exception as e:
        print(f"ベクトル保存エラー: {e}")

class VectorBatchProcessor(threading.Thread):
    """バックグラウンドでベクトル化を行うスレッドクラスなのじゃ。"""
    def __init__(self, folder_path, callback_progress=None, callback_finish=None):
        super().__init__()
        self.folder_path = folder_path
        self.callback_progress = callback_progress
        self.callback_finish = callback_finish
        self.daemon = True # メイン終了時に一緒に終わるようにするのじゃ
        self.running = True

    def run(self):
        engine = VectorEngine.get_instance()
        if not engine.check_available():
            if self.callback_finish: self.callback_finish("AIモデルが利用できないのじゃ")
            return

        all_items = os.listdir(self.folder_path)
        files = GetGazoFiles(all_items, self.folder_path)
        total = len(files)
        vectors = load_vectors()
        updated_count = 0
        
        print(f"ベクトル更新開始: {total}ファイルをチェックするのじゃ")
        
        start_time = time.time()
        last_log_time = start_time
        
        for i, filename in enumerate(files):
            if not self.running: break
            
            # タイムアウトチェック (10分)
            current_time = time.time()
            elapsed = current_time - start_time
            if elapsed > 600:
                print(f"ベクトル化処理がタイムアウトしたのじゃ (10分経過)。ここで打ち切るのじゃ。")
                if self.callback_finish:
                    self.callback_finish("タイムアウトにより停止したのじゃ")
                break

            # 経過表示 (1分ごと)
            if current_time - last_log_time >= 60:
                print(f"ベクトル化処理中... {i}/{total} ({int(elapsed)}秒経過)")
                last_log_time = current_time

            full_path = os.path.join(self.folder_path, filename)
            file_hash = calculate_file_hash(full_path)
            
            # まだベクトルがない、あるいはハッシュが変わった場合のみ計算
            if file_hash and file_hash not in vectors:
                vec = engine.get_image_feature(full_path)
                if vec:
                    vectors[file_hash] = vec
                    updated_count += 1
            
            if self.callback_progress:
                self.callback_progress(i + 1, total, filename)
            
            # 少し休みを入れてCPUを占有しすぎないようにするのじゃ
            time.sleep(0.01)

        if updated_count > 0:
            save_vectors(vectors)
            
        if self.callback_finish:
            self.callback_finish(f"完了！ {updated_count}件のベクトルを新規追加したのじゃ。")

    def stop(self):
        self.running = False

class HakoData():
    """画像データ保持クラスなのじゃ。のじゃ。"""
    def __init__(self, def_folder):
        self.StartFolder = def_folder
        self.GazoFiles = []
        self.vectors_cache = {}
        self.ai_playlist = []     # AI再生用のキュー
        self.visited_files = set() # 表示済みファイル（AIモード用）

    def SetGazoFiles(self, GazoFiles, folder_path):
        self.StartFolder = folder_path
        self.GazoFiles = GazoFiles
        # フォルダが変わったらキャッシュと状態をリセット
        self.vectors_cache = load_vectors()
        self.ai_playlist = []
        self.visited_files = set()

    def RandamGazoSet(self):
        """ランダム、またはAI順序で画像を返すのじゃ。のじゃ。"""
        if not self.GazoFiles:
            return None
        return random.choice(self.GazoFiles)

    def GetNextAIImage(self, threshold):
        """AI類似度順で次の画像を取得するのじゃ。のじゃ。"""
        if not self.GazoFiles:
            return None
            
        # プレイリストに残りがあればそれを返す
        if self.ai_playlist:
            next_img = self.ai_playlist.pop(0)
            self.visited_files.add(next_img)
            return next_img
            
        # プレイリストが空の場合、新しい「シード」を探す
        # 未訪問のファイルの中から最初のものをシードにするのじゃ
        seed_cand = [f for f in self.GazoFiles if f not in self.visited_files]
        
        if not seed_cand:
            # 全て訪問済みの場合はリセットして最初から
            self.visited_files.clear()
            seed_cand = self.GazoFiles
            
        # シード決定（リストの先頭＝フォルダ順の若いもの＝「1番目の画像」）
        seed_file = seed_cand[0]
        
        # シードをプレイリストの先頭に追加
        self.ai_playlist.append(seed_file)
        
        # 類似画像を検索してプレイリストの後ろに繋げる処理
        engine = VectorEngine.get_instance()
        if engine.check_available():
            seed_path = os.path.join(self.StartFolder, seed_file)
            seed_hash = calculate_file_hash(seed_path)
            
            # シードのベクトル取得（キャッシュにあればラッキー）
            seed_vec = self.vectors_cache.get(seed_hash)
            if not seed_vec:
                # 無ければ計算してみる
                seed_vec = engine.get_image_feature(seed_path)
                if seed_vec and seed_hash:
                    self.vectors_cache[seed_hash] = seed_vec

            if seed_vec:
                # 他の画像の類似度を計算して高い順に並べる
                sim_list = []
                for f in seed_cand: # 自分自身も含むが、それは後で除外されるか、最初にpopされるのでOK
                    if f == seed_file: continue
                    
                    f_path = os.path.join(self.StartFolder, f)
                    f_hash = calculate_file_hash(f_path)
                    f_vec = self.vectors_cache.get(f_hash)
                    
                    if not f_vec:
                        # リアルタイム計算は重いので、キャッシュにない場合スキップするか検討。
                        # ここではスキップするのじゃ（高速化のため）
                        continue
                        
                    score = engine.compare_features(seed_vec, f_vec)
                    if score >= threshold:
                        sim_list.append((f, score))
                
                # 類似度が高い順にソート
                sim_list.sort(key=lambda x: x[1], reverse=True)
                
                # プレイリストに追加
                for f, s in sim_list:
                    self.ai_playlist.append(f)
                    # 訪問済みに追加しておかないと、次のシードとして選ばれてしまう可能性があるが、
                    # 実際にはプレイリスト消化時に visited に入るのでOK。
                    # ただし、二重登録を防ぐためにここで visited 扱いには...しないほうがいい。
                    # プレイリストにあるものを次のシード候補から除外するロジックが必要。
                    
        # 準備できたので1つ返す
        return self.GetNextAIImage(threshold) # 再帰呼び出しでpop(0)へ


class GazoPicture():
    """画像表示制御クラスなのじゃ。のじゃ。"""
    def __init__(self, parent, def_folder):
        self.parent = parent
        self.StartFolder = def_folder
        self.random_pos = tk.BooleanVar(value=False)
        self.open_windows = {}
        self.folder_win = None
        self.file_win = None
        self.tag_dict = load_tags()

    def set_image_tag(self, img_window, image_hash):
        """画像ウィンドウにタグラベルを付与するのじゃ。のじゃ。"""
        if not image_hash: return
        data = self.tag_dict.get(image_hash)
        tag = data["tag"] if data else ""
        
        if tag:
            # 既存のラベルがあれば更新、なければ作成
            if hasattr(img_window, "_tag_label"):
                img_window._tag_label.config(text=tag)
            else:
                lbl = tk.Label(img_window, text=tag, bg="#fffae6", fg="#333", font=("MS Gothic", 9), relief="solid")
                lbl.place(relx=0, rely=0) # 左上に固定
                img_window._tag_label = lbl
        else:
            # タグが空ならラベルを隠す
            if hasattr(img_window, "_tag_label"):
                img_window._tag_label.place_forget()

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

            # --- タグ機能の実装（ハッシュベース） ---
            win._image_path = fileName
            win._image_hash = calculate_file_hash(fullName)
            self.set_image_tag(win, win._image_hash)

            def open_tag_menu(event):
                menu = tk.Menu(win, tearoff=0)
                menu.add_command(label="タグを編集", command=lambda: self.edit_tag_dialog(win, fileName, win._image_hash, update_target_win=win))
                menu.post(event.x_root, event.y_root)

            canvas.bind("<Button-1>", lambda e: start_drag(e, win))
            canvas.bind("<B1-Motion>", lambda e: do_drag(e, win))
            canvas.bind("<Button-3>", open_tag_menu) # 右クリックでメニュー表示

        except Exception as e:
            print(f"画像表示エラー: {e}")

    def edit_tag_dialog(self, parent_win, filename, image_hash, update_target_win=None):
        """タグ編集ダイアログを表示するのじゃ。のじゃ。"""
        try:
            if not image_hash:
                print("ハッシュ計算に失敗しているためタグ付けできないのじゃ。")
                return

            data = self.tag_dict.get(image_hash)
            current_tag = data["tag"] if data else ""
            
            new_tag = simpledialog.askstring("タグ編集", f"{filename} のタグを入力してください（;区切り）:", initialvalue=current_tag, parent=parent_win)
            
            if new_tag is not None:
                # ハッシュをキーにして保存するのじゃ
                self.tag_dict[image_hash] = {"tag": new_tag, "hint": filename}
                save_tags(self.tag_dict)
                if update_target_win:
                    self.set_image_tag(update_target_win, image_hash)
        except Exception as e:
            print(f"タグ編集エラー: {e}")

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
