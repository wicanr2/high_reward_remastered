#!/usr/bin/env python3
"""由 overlays.json（docs/re/007，tools 在 workplace/re-ovr）產生 apps/hr/runtime/ovrtab.go。
只輸出版面中繼資料：stub 執行期段、overlay 編號、IDA 載入段。不含原版程式碼或資料。
用法（容器內）：python3 gen_ovr_table.py <overlays.json> <輸出 .go>
"""
import json, sys

src, dst = sys.argv[1], sys.argv[2]
j = json.load(open(src))
ovs = None
for k, v in j.items():
    if isinstance(v, list) and v and isinstance(v[0], dict) and "stub_seg_dosgolem" in v[0]:
        ovs = v
        break
if ovs is None:
    sys.exit("overlays.json 找不到含 stub_seg_dosgolem 的陣列")
rows = sorted(((int(o["stub_seg_dosgolem"], 16), o["idx"], int(o["load_seg"], 16)) for o in ovs))
segs = [r[0] for r in rows]
if len(set(segs)) != len(segs):
    sys.exit("stub_seg_dosgolem 有重複值")
sha = j.get("input", {}).get("sha256", "")
out = ["// 本檔由 tools/gen_ovr_table.py 產生，不要手改（docs/spec/005 第 5.1 節）。",
       "// 來源：MAIN.EXE（SHA-256 %s）的 overlays.json（docs/re/007）。" % sha,
       "// 只含版面中繼資料：stub 執行期段、overlay 編號、IDA 載入段。",
       "",
       "package runtime",
       "",
       "// ovrStub 是一個 overlay 的 stub 執行期段與它在 IDA 內的載入段。",
       "type ovrStub struct {",
       "\tStubSeg uint16 // stub 的執行期段（stub_seg_dosgolem）",
       "\tIdx     uint16 // overlay 編號（IDA 的 ovrNNN）",
       "\tLoadSeg uint16 // IDA 內的載入段（偏移不變）",
       "}",
       "",
       "// ovrStubs 依 StubSeg 遞增排列，共 %d 筆。" % len(rows),
       "var ovrStubs = [...]ovrStub{"]
for s, i, l in rows:
    out.append("\t{0x%04X, %d, 0x%04X}," % (s, i, l))
out.append("}")
open(dst, "w").write("\n".join(out) + "\n")
print("寫出 %d 筆到 %s" % (len(rows), dst))
