'''
作成日: 2025年09月29日
修正日: 2026年01月01日
作成者: tamate masayuki
機能: GazoTools メインアプリケーション (UI)
'''
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk, Image
from tkinterdnd2 import *
import shutil

# ロジックモジュールのインポート
from GazoToolsLogic import load_config, save_config, HakoData, GazoPicture
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
    tk.Label(win, text="画像ファイル一覧 (クリックで表示)", font=("Helvetica", "9", "bold")).pack(pady=5)
    
    frame = tk.Frame(win)
    frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    lb = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    for f in files: lb.insert(tk.END, f)
    lb.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    scrollbar.config(command=lb.yview)
    
    def on_select(event):
        try:
            idx = lb.curselection()
            if idx: draw_func(lb.get(idx[0]))
        except: pass
    lb.bind("<<ListboxSelect>>", on_select)
    return win, lb

# --- メイン処理 ---
koRoot = TkinterDnD.Tk()
koRoot.attributes("-topmost", True)
koRoot.geometry(tkConvertWinSize(list([200, 150, 50, 100])))
koRoot.title("画像tools")

# 状態管理
ss_mode = tk.BooleanVar(value=SAVED_SETTINGS.get("ss_mode", False))
ss_interval = tk.IntVar(value=SAVED_SETTINGS.get("ss_interval", 5))
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
        GazoControl.Drawing(data_manager.RandamGazoSet())
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

menubar = tk.Menu(koRoot)
koRoot.config(menu=menubar)
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
config_menu.add_cascade(label="再生間隔（秒）", menu=ss_sub)
for sec in [1, 2, 3, 5, 10, 20, 30]:
    ss_sub.add_radiobutton(label=f"{sec}秒", variable=ss_interval, value=sec)

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
move_frame.pack(fill=tk.BOTH, padx=5, pady=(0, 5))

def execute_move(file_path, dest_folder):
    if not dest_folder or not os.path.exists(dest_folder):
        messagebox.showerror("エラー", "移動先フォルダが正しく登録されていないのじゃ！")
        return
    try:
        filename = os.path.basename(file_path)
        shutil.move(file_path, os.path.join(dest_folder, filename))
        print(f"[MOVE] {filename} -> {dest_folder}")
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
            return lambda e: (
                data := e.data[1:-1] if e.data.startswith('{') else e.data,
                execute_move(os.path.normpath(data), move_dest_list[idx]) if not os.path.isdir(os.path.normpath(data)) else messagebox.showwarning("注意", "ここはファイル移動用なのじゃ！")
            )
        
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
