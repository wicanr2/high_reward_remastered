"""可散布的包不得夾帶原版檔：依 docs/re/source-inventory.tsv 的檔名與 SHA-256 掃描目錄。

用法：python3 leakscan.py <清冊 tsv> <要掃的目錄>   有命中就回傳 1。
判準是原版目錄裡實際有哪些檔名與雜湊，不是猜副檔名。
"""
import hashlib
import os
import sys

inv, root = sys.argv[1], sys.argv[2]
names, hashes = set(), set()
with open(inv, encoding="utf-8") as f:
    next(f)
    for ln in f:
        c = ln.rstrip("\n").split("\t")
        if len(c) >= 3:
            names.add(c[0].upper())
            if c[1] != "0":
                hashes.add(c[2])
hit = []
for r, _, files in os.walk(root):
    for n in files:
        p = os.path.join(r, n)
        if n.upper() in names:
            hit.append(("檔名", p))
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h in hashes:
            hit.append(("雜湊", p))
for kind, p in hit:
    print("洩漏", kind, p)
print("掃描完成，命中", len(hit))
sys.exit(1 if hit else 0)
