"""匯出 IDA 辨識出的所有字串（位址、內容）及指向它的程式碼 xref。

用法（經 tools/ida.sh）：ida_draw_strings.py <輸出檔>
欄位：selector:offset、長度、字串（反斜線跳脫）、xref 來源（selector:offset，最多 6 個）。
唯讀。內容為 Big5 的字串可能顯示為亂碼，只用來找 ASCII 診斷訊息與檔名。
"""
import sys

import ida_auto
import ida_pro
import ida_segment
import idautils
import ida_nalt

ida_auto.auto_wait()


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return f"????:{ea:05X}"
    return f"{seg.sel:04X}:{ea - (seg.sel << 4):04X}"


out = open(sys.argv[1], "w", encoding="utf-8")
sc = idautils.Strings()
for s in sc:
    try:
        txt = str(s)
    except Exception:
        txt = "?"
    refs = [sel_off(x.frm) for x in idautils.XrefsTo(s.ea, 0)][:6]
    out.write(f"{sel_off(s.ea)}\t{s.length}\t{txt.encode('unicode_escape').decode('ascii')}\t{' '.join(refs)}\n")
out.close()
ida_pro.qexit(0)
