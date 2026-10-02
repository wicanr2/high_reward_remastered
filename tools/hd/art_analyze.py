"""統計每張原圖的顏色數與 2x2 區塊圖樣分布（診斷用）。

用法：python3 art_analyze.py <原圖根目錄> <輸出 tsv>
"""
import os
import sys

import numpy as np
from PIL import Image


def block_types(idx, valid):
    a, b = idx[:-1, :-1], idx[:-1, 1:]
    c, d = idx[1:, :-1], idx[1:, 1:]
    ok = valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, :-1] & valid[1:, 1:]
    stack = np.stack([a, b, c, d], 0)
    ncol = np.zeros(a.shape, np.int32)
    for v in range(0, 17):
        ncol += (stack == v).any(0)
    flat = ncol == 1
    two = ncol == 2
    checker = two & (a == d) & (b == c)
    hl = two & (a == b) & (c == d)
    vl = two & (a == c) & (b == d)
    t31 = two & ~checker & ~hl & ~vl
    res = {
        "flat": (flat & ok).sum(),
        "checker": (checker & ok).sum(),
        "hline": (hl & ok).sum(),
        "vline": (vl & ok).sum(),
        "3+1": (t31 & ok).sum(),
        "3col": ((ncol == 3) & ok).sum(),
        "4col": ((ncol == 4) & ok).sum(),
        "n": ok.sum(),
    }
    return res


def main():
    src, out = sys.argv[1], sys.argv[2]
    rows = []
    for root, _, files in os.walk(src):
        for f in sorted(files):
            if not f.lower().endswith(".png"):
                continue
            p = os.path.join(root, f)
            im = Image.open(p)
            a = np.array(im.convert("RGBA"))
            valid = a[..., 3] > 127
            rgb = a[..., :3].astype(np.int32)
            key = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
            uniq, inv = np.unique(key, return_inverse=True)
            idx = inv.reshape(key.shape)
            idx = np.where(valid, idx, 16)
            nuniq = len(np.unique(idx[valid])) if valid.any() else 0
            r = block_types(idx, valid)
            n = max(r["n"], 1)
            rows.append(
                [os.path.relpath(p, src), f"{a.shape[1]}x{a.shape[0]}", nuniq]
                + [f"{r[k] / n:.3f}" for k in ["flat", "checker", "hline", "vline", "3+1", "3col", "4col"]]
            )
    with open(out, "w") as fh:
        fh.write("file\tsize\tncolors\tflat\tchecker\thline\tvline\t3+1\t3col\t4col\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print(len(rows))


if __name__ == "__main__":
    main()
