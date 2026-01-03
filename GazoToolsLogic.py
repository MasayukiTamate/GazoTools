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
from lib.GazoToolsVectorInterpreter import get_interpreter
from lib.GazoToolsExceptions import (
    ConfigError, ImageLoadError, FileHashError, TagManagementError,
    VectorProcessingError, FileOperationError, FolderAccessError
)
from lib.GazoToolsLogger import LoggerManager
from lib.config_defaults import (
    get_default_config, MOVE_DESTINATION_SLOTS,
    TAG_CSV_FILE, VECTOR_DATA_FILE, RATING_DATA_FILE, CONFIG_FILE
)
from lib.GazoToolsState import get_app_state

# グローバル AppState を取得
app_state = get_app_state()
import threading
import time

# ロギング設定
logger = LoggerManager.get_logger(__name__)

def load_config():
    """設定ファイルを読み込むのじゃ。のじゃ。
    
    config_defaults.py のデフォルト値を使用して、ファイルから設定を読み込みます。
    ファイルが存在しない場合はデフォルト値を返します。
    
    Returns:
        dict: 設定辞書
        
    Raises:
        ConfigError: 設定ファイルの読み込み失敗時
    """
    config = get_default_config()
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config["last_folder"] = data.get("last_folder", os.getcwd())
                config["geometries"] = data.get("geometries", {})
                saved_settings = data.get("settings", {})
                config["settings"].update(saved_settings)
                
                # move_dest_list の長さを MOVE_DESTINATION_SLOTS に強制するのじゃ（IndexError対策）
                cur_list = config["settings"].get("move_dest_list", [])
                if len(cur_list) < MOVE_DESTINATION_SLOTS:
                    config["settings"]["move_dest_list"] = (cur_list + [""] * MOVE_DESTINATION_SLOTS)[:MOVE_DESTINATION_SLOTS]

                if not os.path.exists(config["last_folder"]):
                    config["last_folder"] = os.getcwd()
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルのJSON解析に失敗: {CONFIG_FILE}", exc_info=True)
            raise ConfigError(f"Invalid JSON in config file: {e}") from e
        except IOError as e:
            logger.error(f"設定ファイルの読み込み失敗: {CONFIG_FILE}", exc_info=True)
            raise ConfigError(f"Cannot read config file: {e}") from e
        except Exception as e:
            logger.error(f"設定ファイル読み込み中に予期しないエラー: {e}", exc_info=True)
            raise ConfigError(f"Unexpected error loading config: {e}") from e
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
        logger.info(f"設定を保存しました: {path}")
    except IOError as e:
        logger.error(f"設定ファイルの書き込み失敗: {CONFIG_FILE}", exc_info=True)
        raise ConfigError(f"Cannot write config file: {e}") from e
    except Exception as e:
        logger.error(f"設定保存中に予期しないエラー: {e}", exc_info=True)
        raise ConfigError(f"Unexpected error saving config: {e}") from e

def calculate_file_hash(filepath):
    """ファイルのMD5ハッシュ値を計算するのじゃ。のじゃ。"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        logger.debug(f"ハッシュ計算完了: {os.path.basename(filepath)}")
        return hash_md5.hexdigest()
    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {filepath}", exc_info=True)
        raise FileHashError(f"File not found: {filepath}") from e
    except IOError as e:
        logger.error(f"ファイル読み込みエラー: {filepath}", exc_info=True)
        raise FileHashError(f"Cannot read file: {filepath}") from e
    except Exception as e:
        logger.error(f"ハッシュ計算中に予期しないエラー: {filepath}", exc_info=True)
        raise FileHashError(f"Unexpected error calculating hash: {e}") from e

def load_tags():
    """タグデータと評価データを読み込むのじゃ。のじゃ。"""
    tags = {} # key: hash, value: {tag: "...", hint: "...", rating: int or None}
    if os.path.exists(TAG_CSV_FILE):
        try:
            with open(TAG_CSV_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        h = row[0]
                        t = row[1]
                        hint = row[2] if len(row) > 2 else ""
                        rating = int(row[3]) if len(row) > 3 and row[3] else None
                        tags[h] = {"tag": t, "hint": hint, "rating": rating}
            logger.info(f"タグ・評価データを読み込みました: {len(tags)}件")
        except IOError as e:
            logger.error(f"タグファイル読み込みエラー: {TAG_CSV_FILE}", exc_info=True)
            raise TagManagementError(f"Cannot read tag file: {e}") from e
        except csv.Error as e:
            logger.error(f"CSVファイル解析エラー: {TAG_CSV_FILE}", exc_info=True)
            raise TagManagementError(f"Invalid CSV format in tag file: {e}") from e
        except Exception as e:
            logger.error(f"タグ読み込み中に予期しないエラー: {e}", exc_info=True)
            raise TagManagementError(f"Unexpected error loading tags: {e}") from e
    return tags

def save_tags(tags):
    """タグデータと評価データを保存するのじゃ。のじゃ。"""
    try:
        os.makedirs(os.path.dirname(TAG_CSV_FILE), exist_ok=True)
        with open(TAG_CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for h, data in tags.items():
                rating = data.get("rating", "")
                writer.writerow([h, data["tag"], data["hint"], rating])
        logger.info(f"タグ・評価データを保存しました: {len(tags)}件")
    except IOError as e:
        logger.error(f"タグファイル書き込みエラー: {TAG_CSV_FILE}", exc_info=True)
        raise TagManagementError(f"Cannot write tag file: {e}") from e


def load_ratings():
    """評価データを読み込むのじゃ。のじゃ。"""
    ratings = {}  # key: rating_id, value: {name: "...", rating: int, color: "..."}
    if os.path.exists(RATING_DATA_FILE):
        try:
            with open(RATING_DATA_FILE, "r", encoding="utf-8") as f:
                ratings = json.load(f)
            logger.info(f"評価データを読み込みました: {len(ratings)}件")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"評価データファイル読み込みエラー: {RATING_DATA_FILE}", exc_info=True)
            raise FileOperationError(f"Cannot read rating file: {e}") from e
    return ratings


def save_ratings(ratings):
    """評価データを保存するのじゃ。のじゃ。"""
    try:
        os.makedirs(os.path.dirname(RATING_DATA_FILE), exist_ok=True)
        with open(RATING_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(ratings, f, ensure_ascii=False, indent=2)
        logger.info(f"評価データを保存しました: {len(ratings)}件")
    except IOError as e:
        logger.error(f"評価データファイル書き込みエラー: {RATING_DATA_FILE}", exc_info=True)
        raise FileOperationError(f"Cannot write rating file: {e}") from e
    except Exception as e:
        logger.error(f"タグ保存中に予期しないエラー: {e}", exc_info=True)
        raise TagManagementError(f"Unexpected error saving tags: {e}") from e

def load_vectors():
    """ベクトルデータを読み込むのじゃ。のじゃ。"""
    if os.path.exists(VECTOR_DATA_FILE):
        try:
            with open(VECTOR_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"ベクトルデータを読み込みました: {len(data)}件")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"ベクトルファイルのJSON解析エラー: {VECTOR_DATA_FILE}", exc_info=True)
            raise VectorProcessingError(f"Invalid JSON in vector file: {e}") from e
        except IOError as e:
            logger.error(f"ベクトルファイル読み込みエラー: {VECTOR_DATA_FILE}", exc_info=True)
            raise VectorProcessingError(f"Cannot read vector file: {e}") from e
        except Exception as e:
            logger.error(f"ベクトル読み込み中に予期しないエラー: {e}", exc_info=True)
            raise VectorProcessingError(f"Unexpected error loading vectors: {e}") from e
    return {}

def save_vectors(vectors):
    """ベクトルデータを保存するのじゃ。のじゃ。"""
    try:
        os.makedirs(os.path.dirname(VECTOR_DATA_FILE), exist_ok=True)
        with open(VECTOR_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(vectors, f)
        logger.info(f"ベクトルデータを保存しました: {len(vectors)}件")
    except IOError as e:
        logger.error(f"ベクトルファイル書き込みエラー: {VECTOR_DATA_FILE}", exc_info=True)
        raise VectorProcessingError(f"Cannot write vector file: {e}") from e
    except Exception as e:
        logger.error(f"ベクトル保存中に予期しないエラー: {e}", exc_info=True)
        raise VectorProcessingError(f"Unexpected error saving vectors: {e}") from e

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
        try:
            engine = VectorEngine.get_instance()
            if not engine.check_available():
                logger.error("AIモデルが利用できません")
                if self.callback_finish: 
                    self.callback_finish("AIモデルが利用できないのじゃ")
                return

            all_items = os.listdir(self.folder_path)
            files = GetGazoFiles(all_items, self.folder_path)
            total = len(files)
            
            try:
                vectors = load_vectors()
            except VectorProcessingError as e:
                logger.warning(f"既存ベクトルデータの読み込み失敗、新規作成します: {e}")
                vectors = {}
            
            updated_count = 0
            failed_count = 0
            
            logger.info(f"ベクトル更新開始: {total}ファイルをチェック")
            
            start_time = time.time()
            last_log_time = start_time
            
            for i, filename in enumerate(files):
                if not self.running: 
                    logger.info("ベクトル化処理が中止されました")
                    break
                
                # タイムアウトチェック (10分)
                current_time = time.time()
                elapsed = current_time - start_time
                if elapsed > 600:
                    logger.warning(f"ベクトル化処理がタイムアウト (10分経過)")
                    if self.callback_finish:
                        self.callback_finish("タイムアウトにより停止したのじゃ")
                    break

                # 経過表示 (1分ごと)
                if current_time - last_log_time >= 60:
                    logger.info(f"ベクトル化処理中... {i}/{total} ({int(elapsed)}秒経過)")
                    last_log_time = current_time

                full_path = os.path.join(self.folder_path, filename)
                
                try:
                    file_hash = calculate_file_hash(full_path)
                except FileHashError as e:
                    logger.warning(f"ハッシュ計算失敗: {filename}")
                    failed_count += 1
                    continue
                
                # まだベクトルがない、あるいはハッシュが変わった場合のみ計算
                if file_hash and file_hash not in vectors:
                    try:
                        vec = engine.get_image_feature(full_path)
                        if vec:
                            vectors[file_hash] = vec
                            updated_count += 1
                    except Exception as e:
                        logger.warning(f"ベクトル化失敗: {filename} - {e}")
                        failed_count += 1
                
                if self.callback_progress:
                    self.callback_progress(i + 1, total, filename)
                
                # 少し休みを入れてCPUを占有しすぎないようにするのじゃ
                time.sleep(0.01)

            # ベクトルを保存
            try:
                if updated_count > 0:
                    save_vectors(vectors)
            except VectorProcessingError as e:
                logger.error(f"ベクトルデータ保存失敗: {e}")
                if self.callback_finish:
                    self.callback_finish(f"ベクトル保存エラー: {e}")
                return
                
            if self.callback_finish:
                message = f"完了！ {updated_count}件のベクトルを新規追加したのじゃ。"
                if failed_count > 0:
                    message += f"({failed_count}件失敗)"
                self.callback_finish(message)
            
            logger.info(f"ベクトル更新完了: 追加{updated_count}件、失敗{failed_count}件")
            
        except Exception as e:
            logger.error(f"ベクトル化スレッド処理中に予期しないエラー: {e}", exc_info=True)
            if self.callback_finish:
                self.callback_finish(f"予期しないエラーが発生したのじゃ: {e}")

    def stop(self):
        logger.info("ベクトル化処理停止要求")
        self.running = False

class HakoData():
    """画像データ保持クラスなのじゃ。のじゃ。"""
    def __init__(self, def_folder):
        self.StartFolder = def_folder
        self.GazoFiles = []
        self.vectors_cache = {}
        self.ai_playlist = []     # AI再生用のキュー
        self.visited_files = set() # 表示済みファイル（AIモード用）

    def SetGazoFiles(self, GazoFiles, folder_path, include_subfolders=False):
        """画像ファイルリストを設定するのじゃ。のじゃ。
        
        Args:
            GazoFiles: 現在のフォルダの画像ファイルリスト
            folder_path: フォルダパス
            include_subfolders: 子フォルダを含めるかどうか
        """
        self.StartFolder = folder_path
        self.GazoFiles = GazoFiles
        
        # 子フォルダを含める場合は再帰的に収集
        if include_subfolders:
            self.GazoFiles = self._collect_all_images(folder_path)
        
        # フォルダが変わったらキャッシュと状態をリセット
        self.vectors_cache = load_vectors()
        self.ai_playlist = []
        self.visited_files = set()

    def _collect_all_images(self, base_folder):
        """ベースフォルダとその子フォルダから全ての画像を収集するのじゃ。のじゃ。
        
        Args:
            base_folder: 基準となるフォルダパス
            
        Returns:
            list: ベースフォルダからの相対パスのリスト
        """
        all_images = []
        
        def collect_recursive(current_folder, base_path):
            """再帰的に画像を収集する内部関数なのじゃ。"""
            try:
                items = os.listdir(current_folder)
                folders = GetKoFolder(items, current_folder)
                files = GetGazoFiles(items, current_folder)
                
                # 現在のフォルダの画像を追加（ベースフォルダからの相対パス）
                for f in files:
                    full_path = os.path.join(current_folder, f)
                    relative_path = os.path.relpath(full_path, base_path)
                    all_images.append(relative_path)
                
                # サブフォルダを再帰的に処理
                for folder in folders:
                    subfolder_path = os.path.join(current_folder, folder)
                    collect_recursive(subfolder_path, base_path)
            except PermissionError:
                logger.warning(f"アクセス権限がありません: {current_folder}")
            except Exception as e:
                logger.warning(f"フォルダ読み込みエラー: {current_folder} - {e}")
        
        collect_recursive(base_folder, base_folder)
        logger.info(f"子フォルダを含めて{len(all_images)}件の画像を収集しました")
        return all_images

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
            # 相対パスまたはファイル名からフルパスを構築
            if os.path.isabs(seed_file):
                seed_path = seed_file
            else:
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
                    
                    # 相対パスまたはファイル名からフルパスを構築
                    if os.path.isabs(f):
                        f_path = f
                    else:
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

    # 評価ウィンドウ（独立した子ウィンドウ）
    _rating_window = None
    _current_image_hash = None

    # 情報ウィンドウ（独立した子ウィンドウ）
    _info_window = None

    def __init__(self, parent, def_folder):
        self.parent = parent
        self.StartFolder = def_folder
        self.random_pos = tk.BooleanVar(value=False)
        self.random_size = tk.BooleanVar(value=False)
        self.open_windows = {}
        self.folder_win = None
        self.file_win = None
        self.tag_dict = load_tags()
        self.rating_dict = load_ratings()  # 評価データ（名前付き評価）
        self.image_rating_map = {}  # 画像ハッシュ -> 評価ID のマッピング

        # 既存のタグデータから評価マッピングを復元
        for image_hash, data in self.tag_dict.items():
            if "assigned_rating" in data and data["assigned_rating"]:
                self.image_rating_map[image_hash] = data["assigned_rating"]

    def create_rating_window(self):
        """独立した子ウィンドウとして評価ウィンドウを作成（評価選択機能付き）"""
        if GazoPicture._rating_window is not None:
            try:
                if GazoPicture._rating_window.winfo_exists():
                    return GazoPicture._rating_window
            except:
                pass

        try:
            # メインウィンドウの子として評価ウィンドウを作成
            rating_win = tk.Toplevel(self.parent)
            rating_win.title("評価")
            rating_win.attributes("-topmost", True)
            rating_win.overrideredirect(True)  # タイトルバーなし
            rating_win.attributes("-alpha", 0.9)  # 半透明

            # ディスプレイ中央の最下部に配置（サイズを大きくする）
            screen_w = rating_win.winfo_screenwidth()
            screen_h = rating_win.winfo_screenheight()
            win_width = 300
            win_height = 120
            x = (screen_w - win_width) // 2
            y = screen_h - win_height - 10  # 最下部から10px上
            rating_win.geometry(f"{win_width}x{win_height}+{x}+{y}")

            # 背景フレーム
            frame = tk.Frame(rating_win, bg="#2c3e50", bd=2, relief="raised")
            frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 評価選択ドロップダウン
            rating_frame = tk.Frame(frame, bg="#34495e")
            rating_frame.pack(fill=tk.X, pady=(5, 2))

            tk.Label(rating_frame, text="評価:", font=("Arial", 9),
                    fg="#ecf0f1", bg="#34495e").pack(side=tk.LEFT, padx=(5, 2))

            # 評価リストを作成（デフォルト評価 + 名前付き評価）
            rating_options = ["未選択"] + [name for name in self.rating_dict.keys()]
            self._rating_var = tk.StringVar(value="未選択")

            rating_menu = tk.OptionMenu(rating_frame, self._rating_var,
                                       *rating_options, command=self._on_rating_selected)
            rating_menu.config(bg="#34495e", fg="#ecf0f1", font=("Arial", 9),
                             highlightthickness=0, bd=0)
            rating_menu.pack(side=tk.LEFT, padx=(0, 5))

            # 新規評価作成ボタン
            create_btn = tk.Button(rating_frame, text="+", font=("Arial", 8, "bold"),
                                 bg="#27ae60", fg="white", bd=0, padx=3,
                                 command=self._create_new_rating)
            create_btn.pack(side=tk.RIGHT, padx=(2, 5))

            # 現在の評価表示エリア
            display_frame = tk.Frame(frame, bg="#2c3e50")
            display_frame.pack(fill=tk.X, pady=(2, 5))

            # 評価名ラベル
            self._current_rating_name_label = tk.Label(display_frame, text="未選択",
                                                     font=("Arial", 10, "bold"),
                                                     fg="#f39c12", bg="#2c3e50")
            self._current_rating_name_label.pack(anchor="center", pady=(0, 3))

            # 星のラベルを作成（6個：5個の通常評価＋1個の特別評価）
            star_labels = []
            star_frame = tk.Frame(display_frame, bg="#2c3e50")
            star_frame.pack(anchor="center")

            for i in range(6):
                star_text = "★" if i < 5 else "☆"  # 6つ目は特別な星マーク
                star_label = tk.Label(star_frame, text=star_text,
                                    font=("Arial", 16, "bold"),
                                    fg="#cccccc", bg="#2c3e50", cursor="hand2")
                star_label.pack(side=tk.LEFT, padx=1)
                star_label.bind("<Button-1>", lambda e, rating=i+1: self._on_rating_value_click(rating))
                star_labels.append(star_label)

            # 星ラベルを保存
            rating_win._star_labels = star_labels
            GazoPicture._rating_window = rating_win

            # 初期状態を表示
            self._update_rating_display(star_labels, 0)

            return rating_win

        except Exception as e:
            logger.error(f"評価ウィンドウ作成エラー: {e}")
            return None

    def update_rating_window(self, image_hash=None):
        """評価ウィンドウを更新"""
        try:
            # 評価ウィンドウが存在することを確認
            rating_win = self.create_rating_window()
            if not rating_win:
                return

            # 画像ハッシュを保存
            GazoPicture._current_image_hash = image_hash

            if image_hash:
                # 現在の評価を取得して表示
                tag_data = self.tag_dict.get(image_hash)
                current_rating = tag_data["rating"] if tag_data and tag_data.get("rating") else 0
                self._update_rating_display(rating_win._star_labels, current_rating)

                # ウィンドウを表示
                rating_win.deiconify()
            else:
                # 画像がない場合は非表示
                rating_win.withdraw()

        except Exception as e:
            logger.error(f"評価ウィンドウ更新エラー: {e}")

    def _on_rating_selected(self, rating_name):
        """評価選択時の処理"""
        try:
            if rating_name == "未選択":
                # 現在の画像から評価を解除
                image_hash = GazoPicture._current_image_hash
                if image_hash and image_hash in self.image_rating_map:
                    del self.image_rating_map[image_hash]
                    self._update_current_rating_display(0)
                    self._update_info_window_for_current_image()
                    logger.debug(f"画像から評価を解除: {image_hash[:8]}...")
            else:
                # 選択された評価を現在の画像に適用
                image_hash = GazoPicture._current_image_hash
                if image_hash:
                    self.image_rating_map[image_hash] = rating_name
                    rating_data = self.rating_dict.get(rating_name, {})
                    rating_value = rating_data.get("rating", 0)
                    self._update_current_rating_display(rating_value)
                    self._update_info_window_for_current_image()
                    logger.debug(f"画像に評価適用: {image_hash[:8]}... -> {rating_name}")
        except Exception as e:
            logger.error(f"評価選択エラー: {e}")

    def _on_rating_value_click(self, rating):
        """星クリック時の処理（評価値変更用）"""
        try:
            selected_rating = self._rating_var.get()
            if selected_rating and selected_rating != "未選択":
                # 選択されている評価の値を変更
                if selected_rating not in self.rating_dict:
                    self.rating_dict[selected_rating] = {"name": selected_rating, "rating": 0}

                self.rating_dict[selected_rating]["rating"] = rating
                save_ratings(self.rating_dict)

                # 現在の画像がこの評価を使っている場合、表示を更新
                image_hash = GazoPicture._current_image_hash
                if image_hash and self.image_rating_map.get(image_hash) == selected_rating:
                    self._update_current_rating_display(rating)
                    self._update_info_window_for_current_image()

                logger.debug(f"評価値変更: {selected_rating} = {rating}")
            else:
                logger.warning("評価が選択されていません")
        except Exception as e:
            logger.error(f"評価値変更エラー: {e}")

    def _create_new_rating(self):
        """新規評価作成ダイアログ"""
        try:
            # 新しい評価の名前を入力
            rating_name = simpledialog.askstring("新規評価作成", "評価の名前を入力してください:",
                                               parent=GazoPicture._rating_window)
            if rating_name and rating_name.strip():
                rating_name = rating_name.strip()
                if rating_name not in self.rating_dict:
                    # 新しい評価を作成
                    self.rating_dict[rating_name] = {
                        "name": rating_name,
                        "rating": 3,  # デフォルトで3つ星
                    }
                    save_ratings(self.rating_dict)

                    # ドロップダウンを更新
                    self._update_rating_dropdown()

                    # 新しい評価を選択
                    self._rating_var.set(rating_name)
                    self._on_rating_selected(rating_name)

                    logger.debug(f"新規評価作成: {rating_name}")
                else:
                    messagebox.showwarning("警告", f"評価名「{rating_name}」は既に存在します。")
        except Exception as e:
            logger.error(f"新規評価作成エラー: {e}")

    def _update_rating_dropdown(self):
        """評価ドロップダウンを更新"""
        try:
            if GazoPicture._rating_window:
                # 現在の選択を保存
                current_selection = self._rating_var.get()

                # メニューを再構築
                rating_frame = None
                for child in GazoPicture._rating_window.winfo_children():
                    if isinstance(child, tk.Frame) and str(child.cget('bg')) == '#34495e':
                        rating_frame = child
                        break

                if rating_frame:
                    # OptionMenuを探して更新
                    for child in rating_frame.winfo_children():
                        if isinstance(child, tk.OptionMenu):
                            child.destroy()
                            break

                    # 新しい評価リスト
                    rating_options = ["未選択"] + list(self.rating_dict.keys())

                    # 新しいOptionMenuを作成
                    rating_menu = tk.OptionMenu(rating_frame, self._rating_var,
                                               *rating_options, command=self._on_rating_selected)
                    rating_menu.config(bg="#34495e", fg="#ecf0f1", font=("Arial", 9),
                                     highlightthickness=0, bd=0)
                    rating_menu.pack(side=tk.LEFT, padx=(0, 5))

                    # 選択を復元（可能であれば）
                    if current_selection in rating_options:
                        self._rating_var.set(current_selection)
        except Exception as e:
            logger.error(f"評価ドロップダウン更新エラー: {e}")

    def _update_current_rating_display(self, rating_value):
        """現在の評価表示を更新"""
        try:
            if GazoPicture._rating_window and hasattr(GazoPicture._rating_window, '_star_labels'):
                self._update_rating_display(GazoPicture._rating_window._star_labels, rating_value)

                # 評価名も更新
                selected_rating = self._rating_var.get()
                if selected_rating and selected_rating != "未選択":
                    self._current_rating_name_label.config(text=selected_rating)
                else:
                    self._current_rating_name_label.config(text="未選択")
        except Exception as e:
            logger.error(f"評価表示更新エラー: {e}")

    def _update_info_window_for_current_image(self):
        """現在の画像の情報ウィンドウを更新"""
        try:
            image_hash = GazoPicture._current_image_hash
            if image_hash:
                # 評価情報を更新
                selected_rating = self.image_rating_map.get(image_hash)
                if selected_rating and selected_rating in self.rating_dict:
                    rating_value = self.rating_dict[selected_rating].get("rating", 0)
                else:
                    rating_value = 0

                # 情報ウィンドウの評価情報を更新
                if hasattr(self, 'update_info_window_rating'):
                    self.update_info_window_rating(image_hash, rating_value)
        except Exception as e:
            logger.error(f"情報ウィンドウ更新エラー: {e}")

    def update_rating_window_for_image(self, image_hash):
        """画像ハッシュに基づいて評価ウィンドウを更新"""
        try:
            # 評価ウィンドウが存在することを確認
            rating_win = self.create_rating_window()
            if not rating_win:
                return

            # 画像ハッシュを保存
            GazoPicture._current_image_hash = image_hash

            if image_hash:
                # この画像に割り当てられている評価を取得
                assigned_rating = self.image_rating_map.get(image_hash)
                if assigned_rating and assigned_rating in self.rating_dict:
                    # 割り当てられている評価を選択
                    self._rating_var.set(assigned_rating)
                    rating_value = self.rating_dict[assigned_rating].get("rating", 0)
                    self._update_current_rating_display(rating_value)
                else:
                    # 評価が割り当てられていない場合
                    self._rating_var.set("未選択")
                    self._update_current_rating_display(0)

                # ウィンドウを表示
                rating_win.deiconify()
            else:
                # 画像がない場合は非表示
                rating_win.withdraw()

        except Exception as e:
            logger.error(f"評価ウィンドウ更新エラー: {e}")

    def update_info_window_rating(self, image_hash, rating):
        """情報ウィンドウの評価情報を更新"""
        try:
            if GazoPicture._info_window and hasattr(self, '_info_labels'):
                rating_text = f"{rating}/6" + (" ★" * rating)
                self._info_labels["rating"].config(text=rating_text)
        except Exception as e:
            logger.error(f"情報ウィンドウ評価更新エラー: {e}")

    def create_info_window(self):
        """独立した子ウィンドウとして情報ウィンドウを作成"""
        if GazoPicture._info_window is not None:
            try:
                if GazoPicture._info_window.winfo_exists():
                    return GazoPicture._info_window
            except:
                pass

        try:
            # メインウィンドウの子として情報ウィンドウを作成
            info_win = tk.Toplevel(self.parent)
            info_win.title("画像情報")
            info_win.attributes("-topmost", True)
            info_win.overrideredirect(True)  # タイトルバーなし
            info_win.attributes("-alpha", 0.9)  # 半透明

            # ディスプレイ右上に配置
            screen_w = info_win.winfo_screenwidth()
            screen_h = info_win.winfo_screenheight()
            win_width = 300
            win_height = 200
            x = screen_w - win_width - 10  # 右端から10px左
            y = 10  # 上端から10px下
            info_win.geometry(f"{win_width}x{win_height}+{x}+{y}")

            # 背景フレーム
            frame = tk.Frame(info_win, bg="#2c3e50", bd=2, relief="raised")
            frame.pack(fill=tk.BOTH, expand=True)

            # タイトルラベル
            title_label = tk.Label(frame, text="画像情報", font=("Arial", 12, "bold"),
                                 fg="#ffffff", bg="#2c3e50")
            title_label.pack(pady=(10, 5))

            # 情報表示用のフレーム
            info_frame = tk.Frame(frame, bg="#34495e")
            info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # 情報ラベル群
            self._info_labels = {}

            info_items = [
                ("filename", "ファイル名:"),
                ("size", "画像サイズ:"),
                ("filesize", "ファイルサイズ:"),
                ("zoom", "ズーム倍率:"),
                ("tags", "タグ:"),
                ("rating", "評価:")
            ]

            for key, label_text in info_items:
                # ラベルフレーム
                item_frame = tk.Frame(info_frame, bg="#34495e")
                item_frame.pack(fill=tk.X, pady=1)

                # 項目名ラベル
                label = tk.Label(item_frame, text=label_text, font=("Arial", 9),
                               fg="#ecf0f1", bg="#34495e", anchor="w")
                label.pack(side=tk.LEFT, padx=(0, 5))

                # 値ラベル
                value_label = tk.Label(item_frame, text="", font=("Arial", 9),
                                     fg="#f39c12", bg="#34495e", anchor="w")
                value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self._info_labels[key] = value_label

            GazoPicture._info_window = info_win
            return info_win

        except Exception as e:
            logger.error(f"情報ウィンドウ作成エラー: {e}")
            return None

    def update_info_window(self, image_path=None, image_hash=None, width=None, height=None, zoom_percent=None):
        """情報ウィンドウを更新"""
        try:
            # 情報ウィンドウが存在することを確認
            info_win = self.create_info_window()
            if not info_win or not hasattr(self, '_info_labels'):
                return

            if image_path and image_hash:
                # ファイル名
                filename = os.path.basename(image_path)
                self._info_labels["filename"].config(text=filename)

                # 画像サイズ
                if width and height:
                    size_text = f"{width} × {height}"
                else:
                    size_text = "不明"
                self._info_labels["size"].config(text=size_text)

                # ファイルサイズ
                try:
                    if os.path.exists(image_path):
                        file_size = os.path.getsize(image_path)
                        if file_size < 1024:
                            size_text = f"{file_size} B"
                        elif file_size < 1024 * 1024:
                            size_text = f"{file_size / 1024:.1f} KB"
                        else:
                            size_text = f"{file_size / (1024 * 1024):.1f} MB"
                    else:
                        size_text = "不明"
                except:
                    size_text = "不明"
                self._info_labels["filesize"].config(text=size_text)

                # ズーム倍率
                if zoom_percent:
                    zoom_text = f"{zoom_percent}%"
                else:
                    zoom_text = "100%"
                self._info_labels["zoom"].config(text=zoom_text)

                # タグ情報
                tag_data = self.tag_dict.get(image_hash)
                if tag_data and tag_data.get("tag"):
                    tags_text = tag_data["tag"]
                else:
                    tags_text = "なし"
                self._info_labels["tags"].config(text=tags_text)

                # 評価情報（新しい評価システム）
                assigned_rating = self.image_rating_map.get(image_hash)
                if assigned_rating and assigned_rating in self.rating_dict:
                    rating_data = self.rating_dict[assigned_rating]
                    rating_value = rating_data.get("rating", 0)
                    rating_text = f"{assigned_rating}: {rating_value}/6" + (" ★" * rating_value)
                else:
                    rating_text = "未評価"
                self._info_labels["rating"].config(text=rating_text)

                # ウィンドウを表示
                info_win.deiconify()
            else:
                # 情報がない場合は非表示
                info_win.withdraw()

        except Exception as e:
            logger.error(f"情報ウィンドウ更新エラー: {e}")

    def _update_rating_display(self, star_labels, rating):
        """評価表示を更新"""
        try:
            for i, star_label in enumerate(star_labels):
                if i < rating:
                    # 評価済みの星（金色）
                    star_label.config(fg="#ffd700")
                else:
                    # 未評価の星（灰色）
                    star_label.config(fg="#cccccc")
        except Exception as e:
            logger.error(f"評価表示更新エラー: {e}")

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

        # 評価ウィンドウと情報ウィンドウは非表示にする（独立しているため閉じない）
        GazoPicture._current_image_hash = None
        if GazoPicture._rating_window:
            GazoPicture._rating_window.withdraw()
        if GazoPicture._info_window:
            GazoPicture._info_window.withdraw()

    def Drawing(self, fileName):
        if not fileName: return
        
        # 相対パスの場合はStartFolderと結合、フルパスの場合はそのまま使用
        if os.path.isabs(fileName):
            fullName = os.path.normcase(os.path.abspath(fileName))
            # ベースフォルダを取得（表示用）
            imageFolder = self.StartFolder
        else:
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
                
                # 最大サイズの決定（0の場合は画面サイズの80%を使用）
                if app_state.image_max_width > 0:
                    limit_w = app_state.image_max_width
                else:
                    limit_w = screen_w * 0.8
                
                if app_state.image_max_height > 0:
                    limit_h = app_state.image_max_height
                else:
                    limit_h = screen_h * 0.8
                
                # アスペクト比を維持してスケールを計算
                scale = min(limit_w / orig_w, limit_h / orig_h)
                new_w, new_h = int(orig_w * scale), int(orig_h * scale)
                
                # 最小サイズを適用（元の画像が小さい場合に拡大）
                if new_w < app_state.image_min_width and new_h < app_state.image_min_height:
                    # 最小サイズに合わせて拡大（アスペクト比を維持）
                    scale_w = app_state.image_min_width / orig_w
                    scale_h = app_state.image_min_height / orig_h
                    scale = max(scale_w, scale_h)
                    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
                elif new_w < app_state.image_min_width:
                    # 幅が最小サイズ未満の場合
                    scale = app_state.image_min_width / orig_w
                    new_w = app_state.image_min_width
                    new_h = int(orig_h * scale)
                elif new_h < app_state.image_min_height:
                    # 高さが最小サイズ未満の場合
                    scale = app_state.image_min_height / orig_h
                    new_w = int(orig_w * scale)
                    new_h = app_state.image_min_height
                
                # 最大サイズを再チェック（最小サイズ適用後の確認）
                if app_state.image_max_width > 0 and new_w > app_state.image_max_width:
                    scale = app_state.image_max_width / new_w
                    new_w = app_state.image_max_width
                    new_h = int(new_h * scale)
                if app_state.image_max_height > 0 and new_h > app_state.image_max_height:
                    scale = app_state.image_max_height / new_h
                    new_w = int(new_w * scale)
                    new_h = app_state.image_max_height

                # ランダムサイズが有効な場合、スケールをランダムに変更
                if self.random_size.get():
                    # 最小スケールと最大スケールを計算
                    min_scale_w = app_state.image_min_width / new_w if app_state.image_min_width > 0 and new_w > 0 else 0.5
                    min_scale_h = app_state.image_min_height / new_h if app_state.image_min_height > 0 and new_h > 0 else 0.5
                    min_scale = max(min_scale_w, min_scale_h)
                    
                    # 最大サイズが設定されている場合
                    if app_state.image_max_width > 0 or app_state.image_max_height > 0:
                        max_scale_w = app_state.image_max_width / new_w if app_state.image_max_width > 0 and new_w > 0 else 2.0
                        max_scale_h = app_state.image_max_height / new_h if app_state.image_max_height > 0 and new_h > 0 else 2.0
                        max_scale = min(max_scale_w, max_scale_h)
                    else:
                        # 最大サイズが0の場合は画面サイズの80%を上限とする
                        max_scale_w = (screen_w * 0.8) / new_w if new_w > 0 else 2.0
                        max_scale_h = (screen_h * 0.8) / new_h if new_h > 0 else 2.0
                        max_scale = min(max_scale_w, max_scale_h)
                    
                    # ランダムスケールを生成（最小と最大の間、ただし最小は0.5以上）
                    min_scale = max(min_scale, 0.5)
                    max_scale = max(max_scale, min_scale + 0.1)  # 最低限の範囲を確保
                    random_scale = random.uniform(min_scale, max_scale)
                    new_w = int(new_w * random_scale)
                    new_h = int(new_h * random_scale)
                    
                    # 最小サイズを再チェック
                    if app_state.image_min_width > 0 and new_w < app_state.image_min_width:
                        scale = app_state.image_min_width / new_w if new_w > 0 else 1.0
                        new_w = app_state.image_min_width
                        new_h = int(new_h * scale)
                    if app_state.image_min_height > 0 and new_h < app_state.image_min_height:
                        scale = app_state.image_min_height / new_h if new_h > 0 else 1.0
                        new_w = int(new_w * scale)
                        new_h = app_state.image_min_height
                    
                    # 最大サイズを再チェック
                    if app_state.image_max_width > 0 and new_w > app_state.image_max_width:
                        scale = app_state.image_max_width / new_w if new_w > 0 else 1.0
                        new_w = app_state.image_max_width
                        new_h = int(new_h * scale)
                    if app_state.image_max_height > 0 and new_h > app_state.image_max_height:
                        scale = app_state.image_max_height / new_h if new_h > 0 else 1.0
                        new_w = int(new_w * scale)
                        new_h = app_state.image_max_height

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
            # ファイル名を表示（相対パスの場合はベースネームを使用）
            display_name = os.path.basename(fileName) if os.path.sep in fileName or os.path.altsep in fileName else fileName
            win.title(f"{display_name} ({int(scale*100)}%)")
            win.attributes("-topmost", True)
            self.open_windows[fullName] = win
            
            def on_img_close():
                if fullName in self.open_windows:
                    del self.open_windows[fullName]
                win.destroy()
            win.protocol("WM_DELETE_WINDOW", on_img_close)

            # 表示するUI要素によって高さを動的に調整
            text_area_h = 0

            # ベクトル表示が有効な場合
            if app_state.vector_display.get("enabled", True):
                text_area_h += 40  # ベクトル表示領域の高さ

            # 評価は独立ウィンドウでのみ管理するため、画像ウィンドウの高さには加算しない

            win.geometry(f"{new_w}x{new_h + text_area_h}+{base_x}+{base_y}")
            
            # メイン領域: 画像キャンバス
            frame = tk.Frame(win)
            frame.pack(expand=True, fill=tk.BOTH)
            canvas = tk.Canvas(frame, width=new_w, height=new_h)
            canvas.pack(side=tk.TOP)
            canvas.image = tkimg
            canvas.create_image(0, 0, image=tkimg, anchor=tk.NW)

                # 解釈テキストを表示するラベル（スクロール不要の短い要約を想定）
            interp_label = tk.Label(frame, text="", justify=tk.LEFT, anchor="w", bg="#ffffff", fg="#000000", wraplength=new_w - 8)
            interp_label.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(4,6))

            # ベクトルがあれば解釈を取得して表示（設定による）
            if app_state.vector_display.get("enabled", True):
                try:
                    vec = self.vectors_cache.get(win._image_hash)
                    if vec:
                        interpreter = get_interpreter({"vector_display": getattr(app_state, 'vector_display', {})})
                        interp = interpreter.interpret_vector(vec)
                        interp_text = interpreter.format_interpretation_text(interp)
                        interp_label.config(text=interp_text)
                        interp_label.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(4,6))  # ベクトル表示時はpack
                    else:
                        interp_label.config(text="(ベクトル未登録) ベクトルデータを先に作成してください")
                        interp_label.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(4,6))  # ベクトル表示時はpack
                except Exception as e:
                    interp_label.config(text=f"解釈取得エラー: {e}")
                    interp_label.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(4,6))  # ベクトル表示時はpack
            # ベクトル表示が無効の場合、ラベルをpackしない（スペースを取らない）

            # 評価は独立した評価ウィンドウでのみ管理するため、画像ウィンドウ内には表示しない

            # 評価変更時のコールバック登録
            def on_rating_changed(event_name, data):
                if event_name == "image_rating_changed" and data["image_hash"] == win._image_hash:
                    self._update_rating_display(star_labels, data["new_rating"])

            app_state.register_callback(on_rating_changed)

            # ウィンドウ破棄時にコールバック解除
            def cleanup_callback():
                try:
                    app_state.unregister_callback(on_rating_changed)
                except:
                    pass
                win.after_cancel(cleanup_callback)

            # ウィンドウ破棄時にコールバック解除（少し遅延させて確実に実行）
            win.bind("<Destroy>", lambda e: win.after(100, cleanup_callback))

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

            # 評価ウィンドウを更新（画像表示時）
            if app_state.show_rating_window:
                self.update_rating_window_for_image(win._image_hash)

            # 情報ウィンドウを更新（画像表示時）
            if app_state.show_info_window:
                zoom_percent = int(scale * 100)
                self.update_info_window(fileName, win._image_hash, new_w, new_h, zoom_percent)

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
            current_rating = data["rating"] if data and data.get("rating") else None

            new_tag = simpledialog.askstring("タグ編集", f"{filename} のタグを入力してください（;区切り）:", initialvalue=current_tag, parent=parent_win)

            if new_tag is not None:
                # ハッシュをキーにして保存するのじゃ（評価も保持）
                if image_hash not in self.tag_dict:
                    self.tag_dict[image_hash] = {"tag": "", "hint": "", "rating": None}
                self.tag_dict[image_hash]["tag"] = new_tag
                self.tag_dict[image_hash]["hint"] = filename
                # 既存の評価を保持
                if current_rating is not None:
                    self.tag_dict[image_hash]["rating"] = current_rating
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
