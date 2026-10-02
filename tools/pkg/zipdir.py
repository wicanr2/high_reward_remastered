"""把目錄壓成 zip，保留 unix 權限位元（macOS 解開後執行位元還在）。

用法：python3 zipdir.py <來源目錄> <輸出 zip> [頂層資料夾名]
來源目錄內容放在頂層資料夾下；檔名排序、時間戳固定，使同樣的輸入得到同樣的 zip。
"""
import os
import sys
import zipfile

src, out = sys.argv[1], sys.argv[2]
top = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(os.path.normpath(src))
ts = (2026, 1, 1, 0, 0, 0)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, dirs, files in os.walk(src):
        dirs.sort()
        for name in sorted(files) + sorted(dirs):
            p = os.path.join(root, name)
            rel = os.path.join(top, os.path.relpath(p, src))
            st = os.lstat(p)
            if os.path.isdir(p) and not os.path.islink(p):
                zi = zipfile.ZipInfo(rel + "/", ts)
                zi.external_attr = (0o40755 << 16) | 0x10
                z.writestr(zi, b"")
                continue
            zi = zipfile.ZipInfo(rel, ts)
            zi.external_attr = (st.st_mode & 0xFFFF) << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(p, "rb") as f:
                z.writestr(zi, f.read())
print(out, os.path.getsize(out))
