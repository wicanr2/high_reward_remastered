"""多倍率可行性樣張：每類別 3 張，以同一管線與同一類別參數輸出 S 倍。

用法：python3 art_samples.py <原圖根目錄> <輸出根目錄> <S>
輸出維持相同的相對路徑。結果用 validate.py 以相同 S 檢查契約。
"""
import os
import sys
import time

from PIL import Image

import art_lib
import art_upscale

SAMPLES = [
    # 頭像
    "MRG/FACE.MRG/FACE.MRG_000.png", "MRG/FACE.MRG/FACE.MRG_010.png", "MRG/FACE.MRG/FACE.MRG_050.png",
    # 小精靈與道具
    "MRG/ITEM.MRG/ITEM.MRG_005.png", "MRG/KOMA.MRG/KOMA.MRG_012.png", "MRG/SPOINT.MRG/SPOINT.MRG_004.png",
    # 戰場單位
    "MRG/BC32.MRG/BC32.MRG_019.png", "MRG/BC32.MRG/BC32.MRG_059.png", "MRG/FCHAR.MRG/FCHAR.MRG_002.png",
    # 按鈕與框
    "MRG/BUTTON.MRG/BUTTON.MRG_000.png", "MRG/BUTTON.MRG/BUTTON.MRG_005.png", "MRG/BUTTON.MRG/BUTTON.MRG_011.png",
    # 全畫面插圖
    "GS/ED0.GS.png", "GS/OP4.GS.png", "GS/IMG.GS.png",
    # 地圖
    "PXZ/MAP01.PXZ.png", "PXZ/MAP05.PXZ.png", "PXS/GMAP.PXS.png",
    # 類照片的戰鬥畫面
    "MRG/VS.MRG/VS.MRG_000.png", "MRG/CANNON.MRG/CANNON.MRG_000.png", "MRG/PLANE.MRG/PLANE.MRG_000.png",
    # 舞台與底圖
    "MRG/BSTAGE.MRG/BSTAGE.MRG_000.png", "MRG/BSTAGE.MRG/BSTAGE.MRG_003.png", "MRG/NOWEAPON.MRG/NOWEAPON.MRG_000.png",
    # 文字
    "GS/OP9.GS.png", "FONT/CFONT.15_sample.png", "PCX/H-TXT.PCX.png",
]


def main():
    src, dst, S = sys.argv[1], sys.argv[2], int(sys.argv[3])
    for rel in SAMPLES:
        p = os.path.join(src, rel)
        if not os.path.exists(p):
            d = os.path.dirname(p)
            alt = sorted(f for f in os.listdir(d) if f.endswith(".png"))
            print("缺", rel, "改用", alt[0])
            p = os.path.join(d, alt[0])
            rel = os.path.relpath(p, src)
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        t = time.time()
        Image.fromarray(art_lib.process(p, S, art_upscale.options(rel)), "RGBA").save(out)
        print(rel, f"{time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
