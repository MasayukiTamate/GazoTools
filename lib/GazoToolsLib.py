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
    print(f"{files=}")
    print(f"{base_path=}")
    for f in files:
        print(f)
        if not str(f).startswith("."):
            full_path = os.path.join(base_path, f)
            print(f"{full_path=}")
            print(f"{os.path.isdir(full_path)=}")
            if os.path.isdir(full_path):
                folder.append(f)
    for f in folder:
        print(f)
    return folder

def GetFiles(folder):
    Files = []
    return Files 