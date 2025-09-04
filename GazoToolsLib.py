'''
Created on 2025 09 04


'''
print("GazoToolsLib.py loaded!　ロードしたぞ")  # 追加
import os

#子フォルダの取得
def GetKoFolder(files, base_path="."):
    '''
    指定したパス(base_path)内のfilesリストから、子フォルダのみを抽出して返す
    '''
    folder = []
    for f in files:
        if not str(f).startswith("."):
            full_path = os.path.join(base_path, f)
            if os.path.isdir(full_path):
                folder.append(f)
    for f in folder:
        print(f)
    return folder


'''
def GetKoFolder(files):

    子フォルダの取得

    folder = []

    for f in files:
        o = str(f)
        if not(o[0] == "."):
            if len(o) >= 4:
                if not(o[-4]=="."):
                    if not(o[-3]=="."):
                        if not(o[-5]=="."):
                            folder.append(o)
            else:
                folder.append(o)

    for f in folder:
        print(f)

    return folder
'''