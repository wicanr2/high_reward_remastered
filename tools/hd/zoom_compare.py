"""HD 合成圖的局部放大對照（驗收用）。

用法：python3 zoom_compare.py <目錄> <名稱> <x0,y0,x1,y1> <輸出名稱> [放大倍率]
從 <目錄>/<名稱>-base.png 與 <名稱>-hd.png（1280x960，HD 座標）裁同一個矩形，最近鄰放大後左右並排。
輸出是原版美術的衍生物，只放 workplace/。
"""
import os
import sys

from PIL import Image

d, name, rect, out = sys.argv[1], sys.argv[2], tuple(int(v) for v in sys.argv[3].split(",")), sys.argv[4]
k = int(sys.argv[5]) if len(sys.argv) > 5 else 3
a = Image.open(os.path.join(d, name + "-base.png")).convert("RGB").crop(rect)
b = Image.open(os.path.join(d, name + "-hd.png")).convert("RGB").crop(rect)
w, h = a.size
o = Image.new("RGB", (w * k * 2 + 12, h * k), (255, 255, 255))
o.paste(a.resize((w * k, h * k), Image.NEAREST), (0, 0))
o.paste(b.resize((w * k, h * k), Image.NEAREST), (w * k + 12, 0))
o.save(os.path.join(d, out))
print(out, o.size)
