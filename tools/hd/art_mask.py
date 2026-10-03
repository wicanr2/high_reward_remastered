"""週期性抖色偵測的視覺化（診斷用）。

用法：python3 art_mask.py <輸出 png> <z> <crop> <原圖>
輸出三格：原圖、偵測為抖色的像素（紅框）、去抖色後的 C。
"""
import sys

import numpy as np
from PIL import Image

import art_lib

out, z, crop, path = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
d = art_lib.load(path)
C, dith = art_lib.periodic_dedither(d["idx"], d["rgb"], max_colors=int(sys.argv[5]) if len(sys.argv) > 5 else 2)
H, W = d["idx"].shape
x, y, w, h = (0, 0, W, H) if crop == "all" else [int(v) for v in crop.split(",")]
w, h = min(w, W - x), min(h, H - y)
BG = np.array([110, 60, 130], np.float32)


def comp(rgb):
    return np.where(d["valid"][..., None], rgb, BG)


o = comp(d["rgb"])[y:y + h, x:x + w]
c = comp(C)[y:y + h, x:x + w]
m = dith[y:y + h, x:x + w]
ov = o.copy()
ov[m] = ov[m] * 0.45 + np.array([255, 0, 0]) * 0.55
tiles = [np.kron(t.astype(np.uint8), np.ones((z, z, 1), np.uint8)) for t in (o, ov, c)]
gap = np.full((tiles[0].shape[0], 6, 3), 255, np.uint8)
Image.fromarray(np.concatenate([tiles[0], gap, tiles[1], gap, tiles[2]], 1)).save(out)
print(out, "dith frac", dith[d["valid"]].mean())
