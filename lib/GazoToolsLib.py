'''
Created on 2025 09 04


'''
print("GazoToolsLib.py loaded!　ロードを確認")  # 追加
import os

#子フォルダの取得
def GetKoFolder(files, base_path):
    '''
    指定したパス(base_path)内のfilesリストから、子フォルダのみを抽出して返す
    '''
    folder = []
    for f in files:
        if not str(f).startswith("."):
            full_path = os.path.join(base_path, f)
            if os.path.isdir(full_path):
                folder.append(f)

    return folder

def GetGazoFiles(folder, base_path):
    '''
    
    '''
    Files = []
    for f in folder:
        full_path = os.path.join(base_path, f)
        if str(f).endswith(".jpg") or str(f).endswith(".png") or str(f).endswith(".webp") or str(f).endswith(".bmp") or str(f).endswith(".JPG"):
            Files.append(f)

    return Files 