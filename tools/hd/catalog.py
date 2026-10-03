"""產生 HD 清冊（docs/spec/004 第 3 節）：以解碼後的像素內容為鍵。

雜湊 ＝ SHA-256( u16le 寬 ∥ u16le 高 ∥ 逐列每像素一個位元組的索引色 ) 的完整 64 個十六進位字元，
索引 0 至 15 是顏色，16 表示透明。輸入是 tools/img 解出的 PNG（調色盤，索引 16 為透明）。

用法：python3 catalog.py <inventory.tsv> <PNG 根目錄> <輸出 catalog.tsv> [HD 根目錄 [執行期取樣根目錄]]
HD 根目錄給了就把存在的 HD PNG 相對路徑填進 hd 欄。內容相同的圖合併成一列，id 以分號列出。
執行期取樣根目錄放執行期才產生、不在檔案內的圖（例如游標，`hrhd -dump-unknown` 的輸出），結構為 <群組>/<名稱>.png；
這些列的 id 是 RUNTIME:<群組>/<名稱>.png，hd 欄是同一個相對路徑。
"""
import hashlib
import os
import struct
import sys

from PIL import Image

inv, png_root, out = sys.argv[1], sys.argv[2], sys.argv[3]
hd_root = sys.argv[4] if len(sys.argv) > 4 else None
extra_root = sys.argv[5] if len(sys.argv) > 5 else None


def kind_of(src, fmt, transparency):
    s = src.upper()
    if s.endswith("FACE.MRG"):
        return "face"
    if s.endswith(".PXZ") or s.endswith(".PXS"):
        return "map"
    if s.endswith(".GS") or s.endswith(".PCX"):
        return "bg"
    if "transparent" in transparency:
        return "sprite"
    return "bg"


def idx_hash(png_path):
    im = Image.open(png_path)
    if im.mode != "P":
        raise SystemExit(f"{png_path} 不是調色盤 PNG（{im.mode}）")
    w, h = im.size
    data = im.tobytes()
    return hashlib.sha256(struct.pack("<HH", w, h) + data).hexdigest(), w, h, max(data), im.getpalette()


rows = {}
pals = {}
with open(inv, encoding="utf-8") as f:
    header = next(f).rstrip("\n").split("\t")
    col = {n: i for i, n in enumerate(header)}
    for ln in f:
        c = ln.rstrip("\n").split("\t")
        src, index, png, fmt, transp = c[col["src"]], c[col["index"]], c[col["png"]], c[col["format"]], c[col["transparency"]]
        if "glyph" in fmt or src.upper().startswith("CFONT"):
            continue
        p = os.path.join(png_root, os.path.relpath(png, "out"))
        if not os.path.exists(p):
            raise SystemExit(f"缺 PNG：{p}")
        h, w, hh, mx, pal = idx_hash(p)
        palname = "MAIN" if c[col["palette_source"]].startswith("MAIN.EXE") else c[col["palette_source"]].split()[0]
        pals.setdefault(palname, pal[:48])
        if mx <= 16 and pals[palname] != pal[:48]:
            raise SystemExit(f"{p}：調色盤 {palname} 前 16 色與先前的項目不同")
        ident = src if index in ("-", "") else f"{src}:{index}"
        hd_rel = ""
        if hd_root:
            cand = os.path.join(hd_root, os.path.relpath(png, "out"))
            if os.path.exists(cand):
                hd_rel = os.path.relpath(png, "out")
        key = (h, w, hh)
        kind = "bg256" if mx > 16 else kind_of(src, fmt, transp)
        r = rows.setdefault(key, {"ids": [], "kind": kind, "hd": hd_rel, "pal": palname})
        r["ids"].append(ident)
        if not r["hd"]:
            r["hd"] = hd_rel
if extra_root:
    for dp, _, fs in sorted(os.walk(extra_root)):
        for fn in sorted(fs):
            if not fn.endswith(".png"):
                continue
            p = os.path.join(dp, fn)
            h, w, hh, mx, pal = idx_hash(p)
            rel = os.path.relpath(p, extra_root).replace(os.sep, "/")
            hd_rel = rel if hd_root and os.path.exists(os.path.join(hd_root, rel)) else ""
            r = rows.setdefault((h, w, hh), {"ids": [], "kind": "sprite", "hd": hd_rel, "pal": "MAIN"})
            r["ids"].append("RUNTIME:" + rel)
            if not r["hd"]:
                r["hd"] = hd_rel
with open(out, "w", encoding="utf-8") as o:
    o.write("hash\tid\tw\th\tkind\tpal\thd\n")
    for (h, w, hh), r in sorted(rows.items(), key=lambda kv: kv[1]["ids"][0]):
        o.write(f"{h}\t{';'.join(r['ids'])}\t{w}\t{hh}\t{r['kind']}\t{r['pal']}\t{r['hd']}\n")
total = sum(len(r["ids"]) for r in rows.values())
print(f"項目 {total}，不同內容 {len(rows)}，合併 {total - len(rows)}")
pal_out = os.path.join(os.path.dirname(out), "palettes.tsv")
with open(pal_out, "w", encoding="utf-8") as o:
    o.write("name\tpalette16\n")
    for name, p in sorted(pals.items()):
        o.write(name + "\t" + " ".join("%02X%02X%02X" % tuple(p[i * 3:i * 3 + 3]) for i in range(16)) + "\n")
print(f"調色盤 {len(pals)} 種 → {pal_out}")
