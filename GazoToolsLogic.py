'''
作成者: tamate masayuki (Refactored by Antigravity)
機能: GazoTools のデータ管理、設定管理、およびロジック制御
※ 純粋なビジネスロジック（計算・判断）を集約しているのじゃ。
'''
import os
from lib.GazoToolsLogger import LoggerManager

# ロギング設定
logger = LoggerManager.get_logger(__name__)

# Data access functions (re-exported for compatibility if needed)
from lib.GazoToolsData import (
    load_config, save_config, calculate_file_hash,
    load_tags, save_tags, load_ratings, save_ratings,
    load_vectors, save_vectors
)

from lib.config_defaults import (
    calculate_folder_window_width, calculate_folder_window_height,
    calculate_file_window_width, calculate_file_window_height,
    WINDOW_SPACING
)

# ----------------------------------------------------------------------
# 画面レイアウト計算ロジック
# ----------------------------------------------------------------------
def calculate_window_layout(root_x, root_y, root_w, screen_w, folders, files, current_folder_name):
    """メインウィンドウの位置とサイズを基準に、サブウィンドウの最適な配置を計算するのじゃ。
    
    Args:
        root_x, root_y: メインウィンドウの座標
        root_w: メインウィンドウの幅
        screen_w: 画面幅
        folders: フォルダリスト
        files: ファイルリスト
        current_folder_name: カレントフォルダ名
        
    Returns:
        tuple: (folder_win_geometry, file_win_geometry)
        geometry文字列 ("WxH+X+Y") を返すのじゃ。
    """
    f_count = len(folders) + 1
    current_base = os.path.basename(current_folder_name) or current_folder_name
    
    # フォルダウィンドウ計算
    f_names = [f"({len(files)}) [現在] {current_base}"] + [f"({len(folders)}) {f}" for f in folders]
    max_f = max([len(f) for f in f_names]) if f_names else 5
    w_f = calculate_folder_window_width(max_f)
    h_f = calculate_folder_window_height(f_count)
    x_f, y_f = root_x + root_w + WINDOW_SPACING, root_y
    f_geo = f"{w_f}x{h_f}+{x_f}+{y_f}"
    
    # ファイルウィンドウ計算
    g_count = len(files)
    max_g = max([len(f) for f in files]) if files else 5
    w_g = calculate_file_window_width(max_g)
    h_g = calculate_file_window_height(g_count)
    x_g, y_g = x_f + w_f + WINDOW_SPACING, root_y
    
    # 画面ハミ出しチェック
    if x_g + w_g > screen_w:
        x_g = max(10, root_x - w_g - WINDOW_SPACING)
        
    g_geo = f"{w_g}x{h_g}+{x_g}+{y_g}"
    
    return f_geo, g_geo

# ----------------------------------------------------------------------
# スライドショーの次画像決定ロジック
# ----------------------------------------------------------------------
def decide_next_image(data_manager, is_ai_mode, ai_threshold):
    """スライドショーで次に表示する画像を決定するのじゃ。
    
    Args:
        data_manager (HakoData): データ管理オブジェクト
        is_ai_mode (bool): AIモードかどうか
        ai_threshold (float): AI類似度の閾値
        
    Returns:
        str or None: 次の画像のパス
    """
    if is_ai_mode:
        try:
            return data_manager.GetNextAIImage(ai_threshold)
        except Exception as e:
            logger.error(f"AI再生判断エラー: {e}")
            # エラー時はランダムにフォールバック
            return data_manager.RandamGazoSet()
    else:
        return data_manager.RandamGazoSet()

# ----------------------------------------------------------------------
# リソースモニターのグラデーション計算ロジック
# ----------------------------------------------------------------------
def blend_color(hex_low, hex_high, ratio):
    """CPU使用率に応じて色をブレンドして返すのじゃ。
    
    Args:
        hex_low (str): 低負荷時の色 (#RRGGBB)
        hex_high (str): 高負荷時の色 (#RRGGBB)
        ratio (float): ブレンド率 (0.0 - 1.0)
    
    Returns:
        str: ブレンド後の色 (#RRGGBB)
    """
    # ratio: 0.0 (low) .. 1.0 (high)
    try:
        low = int(hex_low.lstrip('#'), 16)
        high = int(hex_high.lstrip('#'), 16)
        r = int(((low >> 16) & 0xFF) * (1 - ratio) + ((high >> 16) & 0xFF) * ratio)
        g = int(((low >> 8) & 0xFF) * (1 - ratio) + ((high >> 8) & 0xFF) * ratio)
        b = int((low & 0xFF) * (1 - ratio) + (high & 0xFF) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_low # エラー時はlowを返す
