"""匯出 IDA 資料庫的所有段（名稱、選擇子、起訖線性位址、類別）。

用法（經 tools/ida.sh）：ida_draw_segs.py <輸出檔>
欄位：段名、選擇子、起點線性位址、終點線性位址、大小、類別。唯讀。
"""
import sys

import ida_auto
import ida_pro
import ida_segment
import idautils

ida_auto.auto_wait()
out = open(sys.argv[1], "w", encoding="utf-8")
out.write("name\tsel\tstart\tend\tsize\tclass\n")
for s in idautils.Segments():
    seg = ida_segment.getseg(s)
    out.write(
        f"{ida_segment.get_segm_name(seg)}\t{seg.sel:04X}\t{seg.start_ea:#x}\t{seg.end_ea:#x}\t{seg.end_ea - seg.start_ea}\t"
        f"{ida_segment.get_segm_class(seg)}\n"
    )
out.close()
ida_pro.qexit(0)
