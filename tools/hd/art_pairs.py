"""偏差最大處的對照表：每張圖取低通差異最大的視窗，並排顯示原圖與 HD。

用法：python3 art_pairs.py <輸出 png> <z> <原圖根目錄> <HD 根目錄> <S> <欄數> <視窗寬> <視窗高> <相對路徑> [...]
每格：左原版（最近鄰），右 HD；視窗以原版像素計。
"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import art_lib

BG = np.array([110, 60, 130], np.float32)


def comp(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    return (rgba[..., :3] * a + BG * (1 - a)).astype(np.uint8)


def main():
    out, z, src, dst, S, cols, cw, ch = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8])
    rels = sys.argv[9:]
    tiles = []
    for rel in rels:
        d = art_lib.load(f"{src}/{rel}")
        o = np.array(Image.open(f"{src}/{rel}").convert("RGBA"))
        h = np.array(Image.open(f"{dst}/{rel}").convert("RGBA"))
        H, W = d["valid"].shape
        down = h[..., :3].astype(np.float32).reshape(H, S, W, S, 3).mean((1, 3))
        lo = art_lib.gaussian_norm(d["rgb"], d["valid"], 1.5)
        lh = art_lib.gaussian_norm(down, d["valid"], 1.5)
        diff = np.abs(lo - lh).max(-1) * d["valid"]
        w_, h_ = min(cw, W), min(ch, H)
        sm = ndimage.uniform_filter(diff, size=(h_, w_), mode="constant")
        y, x = np.unravel_index(np.argmax(sm), sm.shape)
        y0 = int(np.clip(y - h_ // 2, 0, H - h_))
        x0 = int(np.clip(x - w_ // 2, 0, W - w_))
        po = comp(o[y0:y0 + h_, x0:x0 + w_])
        ph = comp(h[y0 * S:(y0 + h_) * S, x0 * S:(x0 + w_) * S])
        po = np.kron(po, np.ones((z, z, 1), np.uint8))
        ph = np.kron(ph, np.ones((z // S, z // S, 1), np.uint8))
        gap = np.full((po.shape[0], 4, 3), 255, np.uint8)
        t = np.concatenate([po, gap, ph], 1)
        tiles.append(np.pad(t, ((0, 6), (0, 10), (0, 0)), constant_values=255))
        print(rel, (x0, y0, w_, h_))
    rows = []
    for i in range(0, len(tiles), cols):
        r = tiles[i:i + cols]
        hh = max(t.shape[0] for t in r)
        ww = max(t.shape[1] for t in r)
        r = [np.pad(t, ((0, hh - t.shape[0]), (0, ww - t.shape[1]), (0, 0)), constant_values=255) for t in r]
        rows.append(np.concatenate(r, 1))
    W = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    print(out)


if __name__ == "__main__":
    main()
