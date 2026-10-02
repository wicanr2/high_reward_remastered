"""縮圖總表（診斷用）。

用法：python3 art_sheet.py <輸出 png> <欄數> <縮圖寬> <圖> [<圖> ...]
透明處以洋紅底色顯示，縮放用箱形濾波。
"""
import sys

import numpy as np
from PIL import Image

out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
paths = sys.argv[4:]
BG = (110, 60, 130)
tiles = []
for p in paths:
    im = Image.open(p).convert("RGBA")
    a = np.array(im).astype(np.float32)
    al = a[..., 3:4] / 255
    rgb = (a[..., :3] * al + np.array(BG, np.float32) * (1 - al)).astype(np.uint8)
    im = Image.fromarray(rgb)
    th = max(1, round(im.size[1] * tw / im.size[0]))
    tiles.append(im.resize((tw, th), Image.BOX if im.size[0] > tw else Image.NEAREST))
rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
H = sum(max(t.size[1] for t in r) + 4 for r in rows)
sheet = Image.new("RGB", (cols * (tw + 4), H), (255, 255, 255))
y = 0
for r in rows:
    for i, t in enumerate(r):
        sheet.paste(t, (i * (tw + 4), y))
    y += max(t.size[1] for t in r) + 4
sheet.save(out)
print(out, sheet.size)
