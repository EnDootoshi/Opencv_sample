import os
import sys
import shutil
from datetime import datetime
from enum import Enum, auto

import tkinter, tkinter.filedialog
from PIL import Image
import cv2

FACE_ICON_FILE = 'smile.png' # アイコン画像
WM_FILE = 'watermark.png' # ウォーターマーク画像
CASCADE_FILE = 'haarcascade_frontalface_default.xml' # カスケードファイル

class Mode(Enum):
    BLG = auto() # ブログ用
    TMB = auto() # サムネイル用

def mask_face(img_cv, cascade, img_pil, mask):
    """顔をアイコン画像で隠す
    :param img_cv: 元画像(OpenCV)
    :param cascade: カスケードファイル
    :param img_pil: 元画像(PIL)
    :param mask: 顔を隠す用の画像(PIL)
    """
    # 顔認識を実行
    faces = cascade.detectMultiScale(img_cv, scaleFactor=1.5)

    # 認識された顔にアイコンを貼り付け
    for (x, y, w, h) in faces:
        mask = mask.resize((w, h))
        img_pil.paste(mask, (x, y), mask)

def mkdir_dto(img, output_dir_path):
    """画像の撮影日のフォルダーを作成する
    :param img: 画像(PIL)
    :param output_dir_path: 出力先のフォルダーのパス
    :return: 作成したフォルダーのパス
    """
    EXIF_DTO = 36867 # Exifの撮影日（DateTimeOriginal）のタグ番号

    # 移動先フォルダー作成。フォルダー名はExifの撮影日からyyyymmdd形式で生成
    exif = img._getexif()
    dt = datetime.strptime(exif[EXIF_DTO], '%Y:%m:%d %H:%M:%S')
    output_sub_dir = dt.strftime('%Y%m%d')
    output_path = os.path.join(output_dir_path, output_sub_dir)
    os.makedirs(output_path, exist_ok=True)

    return output_path

def make_img(img, img_name, mode, watermark, output_path):
    """画像をリサイズし、ウオーターマークを貼り付け、別名で保存する
    :param img: 画像(PIL)
    :param img_name: 画像(PIL)ファイル名
    :param mode: Mode.BLGならブログ用、Mode.TMBならサムネイル用
    :param watermark: ウオーターマーク画像(PIL)
    :param output_path: 出力先フォルダーのパス
    """
    BLG_CHAR = '_s' # ブログ画像のファイル名に付加する文字列
    TMB_CHAR = '_tmb' # サムネイル画像のファイル名に付加する文字列
    MAX_W_BLG = 600 # ブログ画像の幅の上限
    MAX_H_BLG = 600 # ブログ画像の高さの上限

    MAX_W_TMB = 300 # サムネイル画像の幅の上限
    MAX_H_TMB = 300 # サムネイル画像の高さの上限

    # サイズ、ファイル名の末尾に付加する文字列を設定
    if (mode == Mode.BLG): # ブログ用
        w, h = MAX_W_BLG, MAX_H_BLG
        add_chr = BLG_CHAR
    elif (mode == Mode.TMB): # サムネイル用
        w, h = MAX_W_TMB, MAX_H_TMB
        add_chr = TMB_CHAR
    else:
        return None

    # リサイズ
    img.thumbnail((w, h))

    # ウォーターマークを追加
    w_img, h_img = img.size
    w_wm, h_wm = watermark.size
    img.paste(watermark, (w_img - w_wm, h_img- h_wm), watermark)

    # ファイル名に文字列を付加して保存
    fname, ext = os.path.splitext(img_name)
    img.save(os.path.join(output_path, fname + add_chr + ext))

# 顔アイコン画像とウォーターマーク画像読込み
face_icon = Image.open(FACE_ICON_FILE)
watermark = Image.open(WM_FILE)

# 認識器生成
cascade = cv2.CascadeClassifier(CASCADE_FILE)

# 元画像フォルダー選択
root = tkinter.Tk()
root.withdraw()
msg = '画像フォルダーを選択してください。'
img_dir_path = tkinter.filedialog.askdirectory(title=msg)
if (not img_dir_path): # ［キャンセル]クリック時の処理
    print('フォルダーを選んでください。')
    sys.exit()

# 出力先フォルダー選択
msg = '出力先フォルダーを選択してください。'
output_dir_path = tkinter.filedialog.askdirectory(title=msg)
if (not output_dir_path): # ［キャンセル]クリック時の処理
    print('フォルダーを選んでください。')
    sys.exit()

# 元画像フォルダー内のファイル1つずつ処理
for img_file in os.listdir(img_dir_path):
    # 元画像読み込み（PIL）
    img_path = os.path.join(img_dir_path, img_file)
    img_pil = Image.open(img_path)

    # 顔認識用にOpenCVで元画像をグレースケールで別途読込
    img_cv = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    # 顔を隠す
    mask_face(img_cv, cascade, img_pil, face_icon)

    # ファイルの移動先フォルダー作成
    output_path = mkdir_dto(img_pil, output_dir_path)

    # ブログ用画像とサムネイル用画像を作成
    make_img(img_pil.copy(), img_file, Mode.BLG, watermark, output_path)
    make_img(img_pil, img_file, Mode.TMB, watermark, output_path)

    # 元画像（PIL）を閉じる
    img_pil.close()

    # 元画像を移動
    shutil.move(img_path, output_path)
