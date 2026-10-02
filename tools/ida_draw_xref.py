"""列出對指定資料位址的所有 xref，連同引用處前後數道指令。

用法（經 tools/ida.sh）：ida_draw_xref.py <輸出檔> <前N> <後M> <段:偏移>...
段:偏移 是 IDA 選擇子（十六進位）。唯讀，不改資料庫。
"""
import sys

import ida_auto
import ida_funcs
import ida_pro
import ida_segment
import idautils
import idc

ida_auto.auto_wait()


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return f"????:{ea:05X}"
    return f"{seg.sel:04X}:{ea - (seg.sel << 4):04X}"


out = open(sys.argv[1], "w", encoding="utf-8")
before = int(sys.argv[2])
after = int(sys.argv[3])
for spec in sys.argv[4:]:
    seg, off = [int(x, 16) for x in spec.split(":")]
    target = (seg << 4) + off
    out.write("#" * 78 + "\n")
    out.write(f"目標 {spec.upper()}  內容 bytes: {' '.join('%02x' % idc.get_wide_byte(target + i) for i in range(16))}\n")
    for x in sorted(idautils.XrefsTo(target, 0), key=lambda r: r.frm):
        f = ida_funcs.get_func(x.frm)
        out.write("-" * 60 + "\n")
        out.write(f"引用 {sel_off(x.frm)}  所在函式 {sel_off(f.start_ea) if f else '無'}  code={x.iscode}\n")
        p = x.frm
        lines = []
        for _ in range(before):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            lines.append(p)
        for p in reversed(lines):
            out.write(f"  {sel_off(p)}  {idc.generate_disasm_line(p, 0)}\n")
        out.write(f"* {sel_off(x.frm)}  {idc.generate_disasm_line(x.frm, 0)}\n")
        p = x.frm
        for _ in range(after):
            p = idc.next_head(p, idc.BADADDR)
            if p == idc.BADADDR:
                break
            out.write(f"  {sel_off(p)}  {idc.generate_disasm_line(p, 0)}\n")
out.close()
ida_pro.qexit(0)
