"""HD 合成圖與原版放大圖並排（驗收用）。

用法：python3 pair_compare.py <目錄>
目錄內成對的 <名稱>-hd.png 與 <名稱>-base.png（hrhd 的 -png 輸出，1280x960，遊戲區在第 80 至 879 列）
裁成遊戲區，左＝原版最近鄰放大，右＝HD 合成，輸出 <名稱>-compare.png。
輸出是原版美術的衍生物，只放 workplace/。
"""
import os
import sys

from PIL import Image

d = sys.argv[1]
n = 0
for f in sorted(os.listdir(d)):
    if not f.endswith("-hd.png"):
        continue
    name = f[:-len("-hd.png")]
    b = os.path.join(d, name + "-base.png")
    if not os.path.exists(b):
        continue
    hd = Image.open(os.path.join(d, f)).convert("RGB").crop((0, 80, 1280, 880))
    base = Image.open(b).convert("RGB").crop((0, 80, 1280, 880))
    out = Image.new("RGB", (1280 * 2 + 8, 800), (255, 255, 255))
    out.paste(base, (0, 0))
    out.paste(hd, (1288, 0))
    out.save(os.path.join(d, name + "-compare.png"))
    n += 1
print("並排 %d 組" % n)
