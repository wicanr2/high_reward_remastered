"""並排對照圖：左為原版（最近鄰放大），右為一或多個 HD 版本。

用法：python3 art_cmp.py <輸出 png> <z> <crop> <原圖> <HD 圖> [<HD 圖> ...]
  z     原版一像素在輸出中的邊長（需為 S 的倍數，HD 以 z/S 的最近鄰顯示）
  crop  x,y,w,h（原版像素），或 all
HD 圖的倍率 S 由尺寸比自動判斷。透明處以洋紅底色顯示。
"""
import sys

import numpy as np
from PIL import Image

BG = (110, 60, 130)


def flat(im, bg=BG):
    a = np.array(im.convert("RGBA")).astype(np.float32)
    al = a[..., 3:4] / 255.0
    rgb = a[..., :3] * al + np.array(bg, np.float32) * (1 - al)
    return rgb.astype(np.uint8)


def panel(im, S, crop, z):
    x, y, w, h = crop
    sub = im.crop((x * S, y * S, (x + w) * S, (y + h) * S))
    k = z // S
    arr = flat(sub)
    arr = np.kron(arr, np.ones((k, k, 1), np.uint8))
    return arr


def main():
    out, z, crop, orig = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    hds = sys.argv[5:]
    o = Image.open(orig).convert("RGBA")
    W, H = o.size
    if crop == "all":
        c = (0, 0, W, H)
    else:
        c = tuple(int(v) for v in crop.split(","))
        c = (c[0], c[1], min(c[2], W - c[0]), min(c[3], H - c[1]))
    panels = [panel(o, 1, c, z)]
    for p in hds:
        im = Image.open(p).convert("RGBA")
        S = im.size[0] // W
        panels.append(panel(im, S, c, z))
    gap = np.full((panels[0].shape[0], 6, 3), 255, np.uint8)
    row = []
    for i, p in enumerate(panels):
        if i:
            row.append(gap)
        row.append(p)
    Image.fromarray(np.concatenate(row, axis=1)).save(out)
    print(out, np.concatenate(row, axis=1).shape)


if __name__ == "__main__":
    main()
