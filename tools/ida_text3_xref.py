"""M10 證據探針（第三輪）：237B:0464 與 "ESPMES.MRG" 字串的所有參照（程式碼、資料、原始位元組搜尋）。

用法（經 tools/ida.sh）：ida_text3_xref.py <輸出檔>
輸出只有位址與計數。用來回答「ESPMES 的 394 個沒有靜態呼叫點的項目，是否另有載入路徑」。
"""
import sys
import traceback

import ida_auto
import ida_bytes
import ida_pro
import ida_segment
import idautils
import idc

ida_auto.auto_wait()
OUT = open(sys.argv[1], "w", encoding="utf-8")
w = OUT.write


def lin(s, o):
    return (s << 4) + o


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return "????:%05X" % ea
    return "%04X:%04X" % (seg.sel, ea - (seg.sel << 4))


def bsearch(pat):
    hits = []
    for s in idautils.Segments():
        a, b = idc.get_segm_start(s), idc.get_segm_end(s)
        n = b - a
        if n <= 0:
            continue
        data = ida_bytes.get_bytes(a, n) or b""
        i = data.find(pat)
        while i >= 0:
            hits.append(a + i)
            i = data.find(pat, i + 1)
    return hits


try:
    tgt = lin(0x237B, 0x464)
    xr = list(idautils.XrefsTo(tgt, 0))
    kinds = {}
    for x in xr:
        k = ("code" if x.iscode else "data", x.type)
        kinds[k] = kinds.get(k, 0) + 1
    w("# XrefsTo 237B:0464：%d 筆；分類（型別代碼）：%s\n" % (len(xr), ", ".join("%s/%d x%d" % (k[0], k[1], v) for k, v in sorted(kinds.items()))))
    data_x = [x for x in xr if not x.iscode]
    w("資料型參照 %d 筆：%s\n" % (len(data_x), ", ".join(sel_off(x.frm) for x in data_x)))
    w("\n# 原始位元組搜尋（IDA 資料庫內全部段）\n")
    for name, pat in (("call far 237B:0464 (9A 64 04 7B 23)", b"\x9a\x64\x04\x7b\x23"),
                      ("jmp far 237B:0464 (EA 64 04 7B 23)", b"\xea\x64\x04\x7b\x23"),
                      ("遠指標 64 04 7B 23（資料）", b"\x64\x04\x7b\x23")):
        h = bsearch(pat)
        w("%s：%d 處\n" % (name, len(h)))
        if len(h) != 630 and len(h) < 40:
            w("  位置：%s\n" % ", ".join(sel_off(a) for a in h))
    # 字串
    w("\n# \"ESPMES.MRG\" 字串\n")
    for name, pat in (("ESPMES.MRG", b"ESPMES.MRG"), ("espmes.mrg", b"espmes.mrg"), ("ESPMES", b"ESPMES"), ("espmes", b"espmes"), (".MRG", b".MRG")):
        h = bsearch(pat)
        w("%s：%d 處%s\n" % (name, len(h), "：" + ", ".join(sel_off(a) for a in h) if len(h) <= 12 else ""))
    h = bsearch(b"ESPMES.MRG\x00")
    for a in h:
        xs = list(idautils.XrefsTo(a, 0))
        w("字串 %s 的 xref %d 筆：%s\n" % (sel_off(a), len(xs), ", ".join(sel_off(x.frm) for x in xs)))
        # 段內偏移 0x18 的字串，也以立即值搜尋 push offset
    # 3E41:0018 push imm16 (68 18 00) 次數（在 237B 段內）
    seg_a = lin(0x237B, 0)
    code = ida_bytes.get_bytes(seg_a, 0x1000)
    pos = []
    i = code.find(b"\x68\x18\x00")
    while i >= 0:
        pos.append(i)
        i = code.find(b"\x68\x18\x00", i + 1)
    w("237B:0000..0FFF 內 `68 18 00`（push 0018h）出現位置：%s\n" % ", ".join("237B:%04X" % p for p in pos))
except Exception:
    w("ERROR\n" + traceback.format_exc())
OUT.close()
ida_pro.qexit(0)
