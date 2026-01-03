'''
作成日: 2025年09月29日
修正日: 2026年01月01日
作成者: tamate masayuki
機能: GazoTools メインアプリケーション (UI)
'''
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import ImageTk, Image
from tkinterdnd2 import *
import shutil
import psutil                 # CPU／メモリ取得用
import threading              # バックグラウンドスレッド用
import time                   # スリープ用

# ロジックモジュールのインポート
from GazoToolsLogic import load_config, save_config, HakoData, GazoPicture, calculate_file_hash, VectorBatchProcessor
from lib.GazoToolsBasicLib import tkConvertWinSize
from lib.GazoToolsLib import GetKoFolder, GetGazoFiles

# --- 設定の読み込みと初期化 ---
CONFIG_DATA = load_config()
DEFOLDER = CONFIG_DATA["last_folder"]
SAVED_GEOS = CONFIG_DATA.get("geometries", {})
SAVED_SETTINGS = CONFIG_DATA.get("settings", {})

# --- 共通のUI更新処理 ---
def refresh_ui(new_path):
    """パスに基づいてUIを全更新するのじゃ。のじゃ。"""
    global DEFOLDER
    if not os.path.exists(new_path): return
    DEFOLDER = new_path
    
    try:
        all_items = os.listdir(DEFOLDER)
        folders = GetKoFolder(all_items, DEFOLDER)
        files = GetGazoFiles(all_items, DEFOLDER)
    except Exception as e:
        print(f"再読み込みエラー: {e}")
        return

    data_manager.SetGazoFiles(files, DEFOLDER)
    GazoControl.SetFolder(DEFOLDER)
    
    koRoot.title("画像tools - " + DEFOLDER)
    save_config(DEFOLDER)
    
    folder_listbox.delete(0, tk.END)
    try:
        current_name = os.path.basename(DEFOLDER) or DEFOLDER
        folder_listbox.insert(tk.END, f"({len(files)}) [現在] {current_name}")
    except:
        folder_listbox.insert(tk.END, "(-) [現在] ???")

    for f in folders:
        try:
            sub_items = os.listdir(os.path.join(DEFOLDER, f))
            count = len(GetGazoFiles(sub_items, os.path.join(DEFOLDER, f)))
            folder_listbox.insert(tk.END, f"({count}) {f}")
        except:
            folder_listbox.insert(tk.END, f"(-) {f}")
    
    file_listbox.delete(0, tk.END)
    for f in files:
        file_listbox.insert(tk.END, f)

    if 'folder_win' in globals() and 'file_win' in globals():
        adjust_window_layouts(folders, files)

def adjust_window_layouts(folders, files):
    """ウィンドウ配置の自動調整なのじゃ。のじゃ。"""
    root_x, root_y = koRoot.winfo_x(), koRoot.winfo_y()
    root_w = koRoot.winfo_width()

    f_count = len(folders) + 1
    current_base = os.path.basename(DEFOLDER) or DEFOLDER
    f_names = [f"({len(files)}) [現在] {current_base}"] + [f"({len(folders)}) {f}" for f in folders]
    max_f = max([len(f) for f in f_names]) if f_names else 5
    w_f = max(200, min(600, max_f * 10 + 60))
    h_f = max(120, min(800, f_count * 20 + 90))
    x_f, y_f = root_x + root_w + 10, root_y
    folder_win.geometry(f"{w_f}x{h_f}+{x_f}+{y_f}")
    
    g_count = len(files)
    max_g = max([len(f) for f in files]) if files else 5
    w_g = max(200, min(600, max_g * 8 + 80))
    h_g = max(120, min(800, g_count * 20 + 70))
    x_g, y_g = x_f + w_f + 10, root_y
    
    screen_w = koRoot.winfo_screenwidth()
    if x_g + w_g > screen_w:
        x_g = max(10, root_x - w_g - 10)
    file_win.geometry(f"{w_g}x{h_g}+{x_g}+{y_g}")

def create_folder_list_window(parent, folders):
    win = tk.Toplevel(parent)
    win.title("子データ窓 - フォルダ一覧")
    win.attributes("-topmost", True)
    
    btn_frame = tk.Frame(win)
    btn_frame.pack(fill=tk.X, padx=5, pady=5)
    tk.Button(btn_frame, text="↑ 上のフォルダへ", command=lambda: refresh_ui(os.path.dirname(DEFOLDER))).pack(fill=tk.X)

    frame = tk.Frame(win)
    frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    lb = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    for folder in folders: lb.insert(tk.END, folder)
    lb.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    scrollbar.config(command=lb.yview)

    def on_right_click(event):
        """右クリックで移動先スロットに登録するコンテキストメニューを表示するのじゃ。"""
        try:
            # クリック位置のインデックスを取得
            idx = lb.nearest(event.y)
            lb.selection_clear(0, tk.END)
            lb.selection_set(idx)
            lb.activate(idx)
            
            sel = lb.get(idx)
            if idx == 0:
                target_path = DEFOLDER
            else:
                if ") " in sel: sel = sel.split(") ", 1)[1]
                target_path = os.path.join(DEFOLDER, sel)
            
            if not os.path.isdir(target_path): return

            # メニューの作成
            popup = tk.Menu(win, tearoff=0)
            
            def insert_reg():
                global move_reg_idx
                move_dest_list[move_reg_idx] = target_path
                print(f"[CONTEXT] スロット{move_reg_idx+1}に挿入登録: {target_path}")
                move_reg_idx = (move_reg_idx + 1) % move_dest_count
                update_dd_display()

            popup.add_command(label="登録を挿入", font=("MS Gothic", 9, "bold"), command=insert_reg)
            popup.add_separator()

            def make_reg_func(s_idx, p):
                def reg():
                    move_dest_list[s_idx] = p
                    update_dd_display()
                    print(f"[CONTEXT] スロット{s_idx+1}に直接登録: {p}")
                return reg

            # 全てのスロットの状況（フォルダ名または未登録）を表示するのじゃ
            for i in range(move_dest_count):
                cur_path = move_dest_list[i]
                if cur_path:
                    label_text = f"{i+1}: [{os.path.basename(cur_path)}]"
                else:
                    label_text = f"{i+1}: (未登録)"
                
                popup.add_command(label=label_text, command=make_reg_func(i, target_path))

            popup.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"右クリックエラー: {e}")

    def on_double_click(event):
        try:
            idx = lb.curselection()[0]
            sel = lb.get(idx)
            if idx == 0: refresh_ui(DEFOLDER); return
            if ") " in sel: sel = sel.split(") ", 1)[1]
            refresh_ui(os.path.join(DEFOLDER, sel))
        except: pass

    lb.bind("<Button-3>", on_right_click)
    lb.bind("<Double-Button-1>", on_double_click)
    return win, lb

def create_file_list_window(parent, files, draw_func):
    win = tk.Toplevel(parent)
    win.title("子絵窓 - ファイル一覧")
    win.attributes("-topmost", True)
    tk.Label(win, text="画像ファイル一覧 (Wクリックで表示)", font=("Helvetica", "9", "bold")).pack(pady=5)
    
    frame = tk.Frame(win)
    frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    lb = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    for f in files: lb.insert(tk.END, f)
    lb.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    scrollbar.config(command=lb.yview)
    
    # ダブルクリックで表示
    def on_double_click(event):
        try:
            idx = lb.curselection()
            if idx: draw_func(lb.get(idx[0]))
        except: pass
    lb.bind("<Double-Button-1>", on_double_click)

    # 右クリックメニュー
    def on_right_click(event):
        try:
            # クリック位置を選択状態にする
            idx = lb.nearest(event.y)
            lb.selection_clear(0, tk.END)
            lb.selection_set(idx)
            lb.activate(idx)
            filename = lb.get(idx)
            full_path = os.path.join(DEFOLDER, filename)

            popup = tk.Menu(win, tearoff=0)

            # 名前変更
            def rename_file():
                root, ext = os.path.splitext(filename)
                new_root = simpledialog.askstring("名前変更", f"新しいファイル名を入力してほしいのじゃ（{ext}は自動付与）:", initialvalue=root, parent=win)
                if new_root and new_root != root:
                    try:
                        new_name = new_root + ext
                        new_path = os.path.join(DEFOLDER, new_name)
                        os.rename(full_path, new_path)
                        refresh_ui(DEFOLDER)
                        print(f"[RENAME] {filename} -> {new_name}")
                    except Exception as e:
                        messagebox.showerror("エラー", f"名前変更に失敗したのじゃ: {e}")
            
            popup.add_command(label="名前変更", command=rename_file)

            # 登録フォルダに移動
            move_menu = tk.Menu(popup, tearoff=0)
            popup.add_cascade(label="登録フォルダに移動", menu=move_menu)
            
            def make_move_func(dest):
                return lambda: execute_move(full_path, dest)

            for i in range(move_dest_count):
                dest = move_dest_list[i]
                if dest:
                    move_menu.add_command(label=f"{i+1}: {os.path.basename(dest)}", command=make_move_func(dest))
                else:
                    move_menu.add_command(label=f"{i+1}: (未登録)", state="disabled")

            # タグ追加
            def add_tag():
                h = calculate_file_hash(full_path)
                if h:
                    GazoControl.edit_tag_dialog(win, filename, h, update_target_win=None)
                else:
                    messagebox.showerror("エラー", "ハッシュ計算に失敗したのじゃ")

            popup.add_command(label="タグ追加/編集", command=add_tag)

            popup.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"ファイル一覧右クリックエラー: {e}")

    lb.bind("<Button-3>", on_right_click)

    return win, lb

# --- メイン処理 ---
koRoot = TkinterDnD.Tk()
koRoot.attributes("-topmost", True)
koRoot.geometry(tkConvertWinSize(list([200, 150, 50, 100])))
koRoot.title("画像tools")

# ★ ここからステータスラベルを追加 ★
status_label = tk.Label(koRoot, text="CPU: 0%  MEM: 0 MB", anchor="e")
status_label.pack(fill=tk.X, side=tk.BOTTOM)

# 状態管理 (SS mode)
ss_mode = tk.BooleanVar(value=SAVED_SETTINGS.get("ss_mode", False))
ss_interval = tk.IntVar(value=SAVED_SETTINGS.get("ss_interval", 5))
ss_ai_mode = tk.BooleanVar(value=SAVED_SETTINGS.get("ss_ai_mode", False))
ss_ai_threshold = tk.DoubleVar(value=SAVED_SETTINGS.get("ss_ai_threshold", 0.65))
ss_after_id = None

# --- D&Dエリアの構築（複数移動先・循環登録） ---
move_dest_list = SAVED_SETTINGS.get("move_dest_list", [""] * 12)
move_reg_idx = SAVED_SETTINGS.get("move_reg_idx", 0)
move_dest_count = SAVED_SETTINGS.get("move_dest_count", 2)
move_labels = [] # 動的生成したラベルの保持用
move_text_vars = [] # 動的生成したStringVarの保持用

def update_dd_display():
    """D&Dエリアの表示内容を最新の状態にするのじゃ。のじゃ。"""
    marks = []
    for i in range(move_dest_count):
        if i == move_reg_idx:
            marks.append("◎") # 次の登録先なのじゃ
        elif move_dest_list[i]:
            marks.append("●") # 登録済み
        else:
            marks.append("○") # 未登録
    
    text_reg.set(f"登録[次:{move_reg_idx+1}]: {' '.join(marks)}")
    
    # 各移動ラベルのテキストを更新
    for i in range(move_dest_count):
        if i < len(move_text_vars):
            # 要素数が足りない事態に備えて安全にアクセスするのじゃ
            path = move_dest_list[i] if i < len(move_dest_list) else ""
            if path: move_text_vars[i].set(f"{i+1}: {os.path.basename(path)}")
            else: move_text_vars[i].set(f"{i+1}: (未登録)")

def auto_slideshow():
    global ss_after_id
    if ss_mode.get():
        next_image = None
        # AIモードかランダムモードかで分岐するのじゃ
        if ss_ai_mode.get():
            try:
                next_image = data_manager.GetNextAIImage(ss_ai_threshold.get())
            except Exception as e:
                print(f"AI再生エラー: {e}")
                next_image = data_manager.RandamGazoSet()
        else:
            next_image = data_manager.RandamGazoSet()

        GazoControl.Drawing(next_image)
        ms = max(1000, ss_interval.get() * 1000)
        ss_after_id = koRoot.after(ms, auto_slideshow)
    else:
        ss_after_id = None

def toggle_ss():
    global ss_after_id
    if ss_after_id:
        koRoot.after_cancel(ss_after_id)
    if ss_mode.get():
        auto_slideshow()

def reset_move_destinations():
    """登録済みの移動先フォルダを全てリセットするのじゃ。のじゃ。"""
    if not messagebox.askyesno("確認", "全ての登録フォルダ設定をリセットしても良いかの？"):
        return
    global move_reg_idx
    for i in range(len(move_dest_list)):
        move_dest_list[i] = ""
    move_reg_idx = 0
    update_dd_display()
    print("[RESET] 全ての移動先をリセットしたのじゃ。")

def on_closing_main():
    try:
        geos = {"main": koRoot.winfo_geometry(), "folder": folder_win.winfo_geometry(), "file": file_win.winfo_geometry()}
        sets = {
            "random_pos": GazoControl.random_pos.get(), 
            "topmost": koRoot.attributes("-topmost"), 
            "show_folder": show_folder_win.get(), 
            "show_file": show_file_win.get(),
            "ss_mode": ss_mode.get(),
            "ss_interval": ss_interval.get(),
            "ss_ai_mode": ss_ai_mode.get(),
            "ss_ai_threshold": ss_ai_threshold.get(),
            "move_dest_list": move_dest_list,
            "move_reg_idx": move_reg_idx,
            "move_dest_count": move_dest_count
        }
        save_config(DEFOLDER, geos, sets)
    except: pass
    koRoot.destroy()
    sys.exit()

def safe_select_folder():
    wins = [koRoot, folder_win, file_win]
    prev_states = [w.attributes("-topmost") for w in wins]
    for w in wins: w.attributes("-topmost", False)
    path = filedialog.askdirectory(title="画像フォルダを選択してください")
    for i, w in enumerate(wins): w.attributes("-topmost", prev_states[i])
    return path

def disable_all_topmost():
    koRoot.attributes("-topmost", False)
    folder_win.attributes("-topmost", False)
    file_win.attributes("-topmost", False)
    GazoControl.disable_all_topmost()

# 実体生成
data_manager = HakoData(DEFOLDER)
GazoControl = GazoPicture(koRoot, DEFOLDER)
GazoControl.random_pos.set(SAVED_SETTINGS.get("random_pos", False))
koRoot.attributes("-topmost", SAVED_SETTINGS.get("topmost", True))

# --- リソース表示設定 (ユーザー設定) ---
# 背景色のグラデーション用設定変数 (デフォルトは緑→赤)
cpu_low_color = tk.StringVar(value=SAVED_SETTINGS.get("cpu_low_color", "#e0ffe0"))   # 低負荷時の色
cpu_high_color = tk.StringVar(value=SAVED_SETTINGS.get("cpu_high_color", "#ff8080"))  # 高負荷時の色

def set_cpu_low_color():
    val = simpledialog.askstring("リソース表示設定", "CPU低負荷時の背景色 (hex) を入力してください:", initialvalue=cpu_low_color.get())
    if val:
        cpu_low_color.set(val)
        # 設定保存は on_closing_main で行われる

def set_cpu_high_color():
    val = simpledialog.askstring("リソース表示設定", "CPU高負荷時の背景色 (hex) を入力してください:", initialvalue=cpu_high_color.get())
    if val:
        cpu_high_color.set(val)

# カラーブレンド関数 (hex -> hex)
def blend_color(hex_low, hex_high, ratio):
    # ratio: 0.0 (low) .. 1.0 (high)
    low = int(hex_low.lstrip('#'), 16)
    high = int(hex_high.lstrip('#'), 16)
    r = int(((low >> 16) & 0xFF) * (1 - ratio) + ((high >> 16) & 0xFF) * ratio)
    g = int(((low >> 8) & 0xFF) * (1 - ratio) + ((high >> 8) & 0xFF) * ratio)
    b = int((low & 0xFF) * (1 - ratio) + (high & 0xFF) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"

# ★ ここからリソース監視スレッドを起動 ★
def _update_resource_usage():
    while True:
        cpu = psutil.cpu_percent(interval=1)          # 1 秒ごとに測定
        mem = psutil.Process().memory_info().rss // (1024 * 1024)  # MB 単位
        # CPU 使用率に応じて背景色をブレンド
        ratio = min(cpu / 100.0, 1.0)
        bg = blend_color(cpu_low_color.get(), cpu_high_color.get(), ratio)
        status_label.config(text=f"CPU: {cpu}%  MEM: {mem} MB", bg=bg)
        time.sleep(1)
threading.Thread(target=_update_resource_usage, daemon=True).start()
# ★ ここまで ★

# --- メニューに設定項目を追加 ---
menubar = tk.Menu(koRoot)
koRoot.config(menu=menubar)
config_menu = tk.Menu(menubar, tearoff=0) 

# 既存の config_menu 定義の直後に以下を追加
resource_sub = tk.Menu(config_menu, tearoff=0)
config_menu.add_cascade(label="リソース表示設定", menu=resource_sub)
resource_sub.add_command(label="CPU低負荷時の色設定", command=set_cpu_low_color)
resource_sub.add_command(label="CPU高負荷時の色設定", command=set_cpu_high_color)



file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="ファイル(F)", menu=file_menu)
file_menu.add_command(label="フォルダを開く...", command=lambda: refresh_ui(safe_select_folder()))
def open_explorer():
    """現在のフォルダをエクスプローラーで開くのじゃ。のじゃ。"""
    try:
        os.startfile(DEFOLDER)
    except Exception as e:
        messagebox.showerror("エラー", f"エクスプローラーを開けなかったのじゃ: {e}")

file_menu.add_command(label="エクスプローラーで開く(E)", command=open_explorer)
file_menu.add_separator()
file_menu.add_command(label="終了(X)", command=on_closing_main)

show_folder_win = tk.BooleanVar(value=SAVED_SETTINGS.get("show_folder", True))
show_file_win = tk.BooleanVar(value=SAVED_SETTINGS.get("show_file", True))

def update_visibility():
    if show_folder_win.get(): folder_win.deiconify()
    else: folder_win.withdraw()
    if show_file_win.get(): file_win.deiconify()
    else: file_win.withdraw()

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="表示(V)", menu=view_menu)
view_menu.add_checkbutton(label="フォルダ一覧を表示", variable=show_folder_win, command=update_visibility)
view_menu.add_checkbutton(label="ファイル一覧を表示", variable=show_file_win, command=update_visibility)
view_menu.add_command(label="全ての画像を閉じる(R)", command=lambda: GazoControl.CloseAll())
view_menu.add_command(label="全ての画像を整列(T)", command=lambda: GazoControl.TileWindows())
view_menu.add_separator()
view_menu.add_command(label="全ての最前面表示をOFF", command=disable_all_topmost)

config_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="設定(S)", menu=config_menu)
config_menu.add_checkbutton(label="表示位置をランダムにする", variable=GazoControl.random_pos)
config_menu.add_separator()
config_menu.add_checkbutton(label="スクリーンセーバー(自動再生)", variable=ss_mode, command=toggle_ss)

ss_sub = tk.Menu(config_menu, tearoff=0)
config_menu.add_cascade(label="SS設定", menu=ss_sub)

# 再生間隔
ss_interval_menu = tk.Menu(ss_sub, tearoff=0)
ss_sub.add_cascade(label="再生間隔（秒）", menu=ss_interval_menu)
for sec in [1, 2, 3, 5, 10, 20, 30]:
    ss_interval_menu.add_radiobutton(label=f"{sec}秒", variable=ss_interval, value=sec)

# AI設定
ss_sub.add_separator()
ss_sub.add_checkbutton(label="AI類似度順で再生", variable=ss_ai_mode)

def set_ai_threshold():
    val = simpledialog.askfloat("AI設定", "類似度スコアの閾値(0.0〜1.0)を設定してほしいのじゃ：", 
                                initialvalue=ss_ai_threshold.get(), minvalue=0.0, maxvalue=1.0)
    if val is not None:
        ss_ai_threshold.set(val)

ss_sub.add_command(label="類似度の閾値を設定...", command=set_ai_threshold)

# ツールメニュー
tools_menu = tk.Menu(menubar, tearoff=0)

menubar.add_cascade(label="ツール(T)", menu=tools_menu)

processor = None
def run_vector_update():
    """AIベクトル更新を実行するのじゃ。のじゃ。"""
    global processor
    if processor and processor.is_alive():
        messagebox.showinfo("情報", "既にバックグラウンドで処理中なのじゃ。")
        return

    msg = "AI(MobileNetV3)を使って画像のベクトル化を行うのじゃ。\n処理はバックグラウンドで行われるので、ウィンドウ操作は継続できるのじゃ。\n\n開始しても良いかの？"
    if not messagebox.askyesno("確認", msg):
        return

    # プログレスコールバック
    def on_progress(current, total, filename):
        # メインスレッドでUI更新（after経由）
        koRoot.after(0, lambda: koRoot.title(f"画像tools - {current}/{total} {filename} を解析中..."))

    # 完了コールバック
    def on_finish(message):
        def _finish_ui():
            koRoot.title(f"画像tools - {DEFOLDER}")
            messagebox.showinfo("完了", message)
        koRoot.after(0, _finish_ui)

    processor = VectorBatchProcessor(DEFOLDER, on_progress, on_finish)
    processor.start()

tools_menu.add_command(label="AIベクトルを更新・作成", command=run_vector_update)

# 移動先フォルダ数の設定メニュー
count_var = tk.IntVar(value=move_dest_count)
def change_move_count():
    global move_dest_count
    move_dest_count = count_var.get()
    rebuild_move_area()

count_sub = tk.Menu(config_menu, tearoff=0)
config_menu.add_cascade(label="移動先フォルダ数", menu=count_sub)
for c in [2, 4, 6, 8, 10, 12]:
    count_sub.add_radiobutton(label=f"{c}個", variable=count_var, value=c, command=change_move_count)

config_menu.add_separator()
config_menu.add_command(label="全登録フォルダをリセット", command=reset_move_destinations)
config_menu.add_separator()
config_menu.add_command(label="常に最前面(T) ON/OFF", command=lambda: koRoot.attributes("-topmost", not koRoot.attributes("-topmost")))

all_items = os.listdir(DEFOLDER)
folder_win, folder_listbox = create_folder_list_window(koRoot, GetKoFolder(all_items, DEFOLDER))
file_win, file_listbox = create_file_list_window(koRoot, GetGazoFiles(all_items, DEFOLDER), GazoControl.Drawing)
GazoControl.SetUI(folder_win, file_win)

if "main" in SAVED_GEOS: koRoot.geometry(SAVED_GEOS["main"])
if "folder" in SAVED_GEOS: folder_win.geometry(SAVED_GEOS["folder"])
if "file" in SAVED_GEOS: file_win.geometry(SAVED_GEOS["file"])
update_visibility()

folder_win.protocol("WM_DELETE_WINDOW", lambda: (show_folder_win.set(False), folder_win.withdraw()))
file_win.protocol("WM_DELETE_WINDOW", lambda: (show_file_win.set(False), file_win.withdraw()))
koRoot.protocol("WM_DELETE_WINDOW", on_closing_main)

refresh_ui(DEFOLDER)

# --- D&Dエリアの構築（2段構え） ---
text_reg = tk.StringVar(koRoot)
lbl_reg = tk.Label(koRoot, textvariable=text_reg, bg="#e0f0ff", height=2, bd=2, relief="groove")
lbl_reg.drop_target_register(DND_FILES)

def handle_drop_register(event):
    global move_reg_idx
    data = event.data
    if data.startswith('{') and data.endswith('}'): data = data[1:-1]
    path = os.path.normpath(data)
    
    if os.path.isdir(path):
        move_dest_list[move_reg_idx] = path
        # 現在の数で循環させるのじゃ
        move_reg_idx = (move_reg_idx + 1) % move_dest_count
        update_dd_display()
        print(f"[REGISTER] {move_reg_idx}番目に登録: {path}")
    else:
        messagebox.showwarning("注意", "ここはフォルダ登録用なのじゃ！ファイルを動かしたいなら下へ入れるのじゃ。")

lbl_reg.dnd_bind("<<Drop>>", handle_drop_register)
lbl_reg.pack(fill=tk.BOTH, padx=5, pady=(5, 15)) # 15ピクセルの余白をあけるのじゃ

# 移動エリアを保持するフレーム
move_frame = tk.Frame(koRoot)
move_frame.pack(fill=tk.BOTH, padx=5, pady=(0, 5), expand=True)

def execute_move(file_path, dest_folder, refresh=True):
    if not dest_folder or not os.path.exists(dest_folder):
        messagebox.showerror("エラー", "移動先フォルダが正しく登録されていないのじゃ！")
        return
    try:
        filename = os.path.basename(file_path)
        shutil.move(file_path, os.path.join(dest_folder, filename))
        print(f"[MOVE] {filename} -> {dest_folder}")
        if refresh:
            refresh_ui(DEFOLDER)
    except Exception as e:
        messagebox.showerror("失敗", f"移動中にエラーが起きたのじゃ: {e}")

def rebuild_move_area():
    """移動先エリアを数に合わせて作り直すのじゃ。のじゃ。"""
    global move_labels, move_text_vars
    # 既存のラベルを掃除
    for lbl in move_labels: lbl.destroy()
    move_labels.clear()
    move_text_vars.clear()

    # 最大12個。列数は3列を基本にするのじゃ
    cols = 3 if move_dest_count > 4 else 2
    if move_dest_count == 2: cols = 2

    for i in range(move_dest_count):
        tv = tk.StringVar(koRoot)
        # 背景色を交互に変えて視認性を上げるのじゃ
        bg_color = "#e0ffe0" if (i % 2 == 0) else "#f0ffe0"
        # 12個の時は少しフォントを小さくするのじゃ
        f_size = 8 if move_dest_count > 8 else 9
        
        l = tk.Label(move_frame, textvariable=tv, bg=bg_color, font=("MS Gothic", f_size), height=2, bd=1, relief="ridge")
        l.drop_target_register(DND_FILES)
        
        # クロージャ問題対策のため、iを引数で固定するのじゃ
        def make_drop_func(idx):
            def drop_handler(event):
                try:
                    # 複数ファイルのパース処理（Tkinterのsplitlistを使うと波括弧なども正しく捌けるのじゃ）
                    files = koRoot.tk.splitlist(event.data)
                    count = 0
                    for f in files:
                        p = os.path.normpath(f)
                        if os.path.isfile(p):
                            # ループ中はrefresh=Falseにして高速化するのじゃ
                            execute_move(p, move_dest_list[idx], refresh=False)
                            count += 1
                        elif os.path.isdir(p):
                             messagebox.showwarning("注意", f"フォルダは移動できないのじゃ: {p}")
                    
                    if count > 0:
                        refresh_ui(DEFOLDER)
                        print(f"[BATCH MOVE] 合計 {count} 個のファイルを移動して画面を更新したのじゃ。")
                except Exception as e:
                    print(f"ドロップ処理エラー: {e}")
            return drop_handler
        
        l.dnd_bind("<<Drop>>", make_drop_func(i))
        l.grid(row=i // cols, column=i % cols, sticky="nsew", padx=1, pady=1)
        
        move_labels.append(l)
        move_text_vars.append(tv)

    # 全ての列と行が均等に広がるようにするのじゃ
    for c in range(cols): move_frame.columnconfigure(c, weight=1)
    for r in range((move_dest_count + cols - 1) // cols): move_frame.rowconfigure(r, weight=1)
    
    update_dd_display()

# 初期ビルド
rebuild_move_area()

# リセットボタン（最下部）
btn_reset = tk.Button(koRoot, text="全登録フォルダをリセット", bg="#fff0f0", font=("MS Gothic", 8), command=reset_move_destinations)
btn_reset.pack(fill=tk.X, padx=5, pady=(0, 5))

def on_escape(event):
    if ss_mode.get():
        ss_mode.set(False)
        toggle_ss()

def on_ctrl_f(event):
    koRoot.attributes("-topmost", True)
    koRoot.focus_force()

def on_ctrl_r(event):
    """Ctrl + R で全ての画像を閉じるのじゃ。のじゃ。"""
    GazoControl.CloseAll()
    print("[HOTKEY] Ctrl+R: 全ての画像を閉じました")

def on_ctrl_e(event):
    """Ctrl + E でエクスプローラーを開くのじゃ。のじゃ。"""
    open_explorer()
    print("[HOTKEY] Ctrl+E: エクスプローラーを開きました")

def on_ctrl_t(event):
    """Ctrl + T で全ての画像をタイル状に並べるのじゃ。のじゃ。"""
    GazoControl.TileWindows()
    print("[HOTKEY] Ctrl+T: 画像をタイル表示にしました")

def on_space(event):
    GazoControl.Drawing(data_manager.RandamGazoSet())

koRoot.bind("<space>", on_space)
koRoot.bind("<Escape>", on_escape)
koRoot.bind_all("<Control-f>", on_ctrl_f)
koRoot.bind_all("<Control-r>", on_ctrl_r)
koRoot.bind_all("<Control-e>", on_ctrl_e)
koRoot.bind_all("<Control-t>", on_ctrl_t)

if ss_mode.get():
    koRoot.after(1000, auto_slideshow)

koRoot.mainloop()
