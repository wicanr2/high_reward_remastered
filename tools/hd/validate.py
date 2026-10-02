"""檢查 HD 圖是否符合 docs/spec/004 第 4 節的契約。

用法：python3 validate.py <原圖根目錄> <HD 根目錄> [S]
HD 根目錄內每張 PNG 要有對應的原圖；回報違規與缺漏。結束碼 0 ＝ 全數通過。
"""
import os
import sys

import hdlib

src, dst = sys.argv[1], sys.argv[2]
S = int(sys.argv[3]) if len(sys.argv) > 3 else 2
bad = 0
total = 0
for root, _, files in os.walk(dst):
    for f in sorted(files):
        if not f.lower().endswith(".png"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, dst)
        o = os.path.join(src, rel)
        total += 1
        if not os.path.exists(o):
            print(f"{rel}: 沒有對應的原圖")
            bad += 1
            continue
        errs = hdlib.check_contract(o, p, S)
        if errs:
            bad += 1
            print(f"{rel}: " + "；".join(errs))
print(f"檢查 {total} 張，違規 {bad} 張")
sys.exit(1 if bad else 0)
