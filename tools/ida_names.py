"""匯出 IDA 資料庫內所有函式（名稱、位址、大小、所在段），名稱不是 sub_ 開頭的標為具名。

用法（經 tools/ida.sh）：ida_names.py <輸出.tsv>
欄位：selector:offset、線性位址、大小、段名、函式名、是否具名（非 sub_／loc_／nullsub_ 預設名）。
只讀，不改資料庫。輸出檔明寫 utf-8。
"""
import sys

import ida_auto
import ida_funcs
import ida_pro
import ida_segment
import idautils
import idc

ida_auto.auto_wait()
out_path = sys.argv[1] if len(sys.argv) > 1 else "/work/out/names.tsv"
rows = []
for ea in idautils.Functions():
    f = ida_funcs.get_func(ea)
    name = idc.get_func_name(ea)
    seg = ida_segment.getseg(ea)
    segname = ida_segment.get_segm_name(seg) if seg else ""
    sel = seg.sel if seg else 0
    named = not (name.startswith("sub_") or name.startswith("loc_") or name.startswith("nullsub_") or name.startswith("j_"))
    rows.append((sel, ea - (sel << 4), ea, f.end_ea - f.start_ea if f else 0, segname, name, int(named)))
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write("sel_off\tlinear\tsize\tsegment\tname\tnamed\n")
    for sel, off, ea, size, segname, name, named in rows:
        fh.write(f"{sel:04X}:{off:04X}\t{ea:#x}\t{size}\t{segname}\t{name}\t{named}\n")
ida_pro.qexit(0)
