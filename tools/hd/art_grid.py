"""多變體並排表（實驗用）：每列一張圖，欄為 原圖 | 基準 v1 | 變體 ...

用法：python3 art_grid.py <輸出 png> <z> <變體字串;變體字串;...> <路徑[@x,y,w,h]> [<路徑[@crop]> ...]
  z       原版一像素的顯示邊長（偶數）
  變體    art_lib.process 的參數字串（逗號分隔 key=value），以分號分隔多個；空字串 ＝ 不加變體
  路徑    /w/re-img/out 底下的 png；基準 v1 取自 /w/hd-work/x2 的同名檔
結果也存各變體的完整輸出到 /w/hd-work/proto2/grid/。
"""
import os
import sys

import numpy as np
from PIL import Image

import art_lib

BG = np.array([110, 60, 130], np.float32)


def flat(rgba, S, crop, z):
    x, y, w, h = crop
    sub = rgba[y * S:(y + h) * S, x * S:(x + w) * S].astype(np.float32)
    al = sub[..., 3:4] / 255.0
    rgb = sub[..., :3] * al + BG * (1 - al)
    k = z // S
    return np.kron(rgb.astype(np.uint8), np.ones((k, k, 1), np.uint8))


def main():
    out, z = sys.argv[1], int(sys.argv[2])
    variants = [v for v in sys.argv[3].split(";") if v]
    rows = []
    os.makedirs("/w/hd-work/proto2/grid", exist_ok=True)
    for spec in sys.argv[4:]:
        path, _, crop = spec.partition("@")
        o = np.array(Image.open(path).convert("RGBA"))
        H, W = o.shape[:2]
        c = (0, 0, W, H) if not crop else tuple(int(v) for v in crop.split(","))
        c = (c[0], c[1], min(c[2], W - c[0]), min(c[3], H - c[1]))
        tiles = [flat(o, 1, c, z)]
        base = path.replace("/w/re-img/out", "/w/hd-work/x2")
        if os.path.exists(base):
            tiles.append(flat(np.array(Image.open(base).convert("RGBA")), 2, c, z))
        for i, v in enumerate(variants):
            opt = dict(kv.split("=") for kv in v.split(",") if kv)
            rgba = art_lib.process(path, int(opt.get("S", 2)), opt)
            nm = os.path.basename(path)[:-4] + f"_{opt.get('name', i)}.png"
            Image.fromarray(rgba, "RGBA").save("/w/hd-work/proto2/grid/" + nm)
            tiles.append(flat(rgba, int(opt.get("S", 2)), c, z))
        gap = np.full((tiles[0].shape[0], 6, 3), 255, np.uint8)
        row = []
        for i, t in enumerate(tiles):
            if i:
                row.append(gap)
            row.append(t)
        rows.append(np.concatenate(row, 1))
        print(spec, "ok")
    W = max(r.shape[1] for r in rows)
    pad = [np.pad(r, ((0, 6), (0, W - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
    Image.fromarray(np.concatenate(pad, 0)).save(out)
    print(out)


if __name__ == "__main__":
    main()
