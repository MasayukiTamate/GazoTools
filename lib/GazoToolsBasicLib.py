'''
Created on 2025 09 29

@author: tamate masayuki

'''



def tkConvertWinSize(tateyokoList):
    '''
    最初にサイズの文字の場合も対応する予定
    '''
    res = ""
    dec = "","x","+","+"

    for l, d in zip(tateyokoList, dec):
        res = res + str(d)
        res = res + str(l)

    return res
