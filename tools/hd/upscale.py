"""批次產生 HD 圖（基準演算法 v1）。

用法：python3 upscale.py <輸入根目錄> <輸出根目錄> [S]
輸入根目錄是 tools/img 的輸出（內含 MRG/、GS/、PXZ/ 等子目錄的 PNG）；輸出維持相同的相對路徑。
"""
import os
import sys

import hdlib

src, dst = sys.argv[1], sys.argv[2]
S = int(sys.argv[3]) if len(sys.argv) > 3 else 2
n = 0
for root, _, files in os.walk(src):
    for f in sorted(files):
        if not f.lower().endswith(".png"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, src)
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        hdlib.upscale(p, S).save(out)
        n += 1
print(f"完成 {n} 張，S={S}")
