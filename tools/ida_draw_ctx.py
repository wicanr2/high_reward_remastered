"""列出對指定函式的每一個呼叫點，連同呼叫前 N 道指令（看參數怎麼推入）與呼叫後 M 道指令。

用法（經 tools/ida.sh）：ida_draw_ctx.py <輸出檔> <前N> <後M> <段:偏移>...
段:偏移 是 IDA 選擇子（十六進位）。唯讀，不改資料庫。
"""
import sys

import ida_auto
import ida_bytes
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
    out.write(f"目標 {spec.upper()}\n")
    sites = sorted(x.frm for x in idautils.XrefsTo(target, 0) if x.iscode)
    for s in sites:
        f = ida_funcs.get_func(s)
        out.write("-" * 60 + "\n")
        out.write(f"呼叫點 {sel_off(s)}  所在函式 {sel_off(f.start_ea) if f else '無'}\n")
        lines = []
        p = s
        for _ in range(before):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            lines.append(p)
        for p in reversed(lines):
            out.write(f"  {sel_off(p)}  {idc.generate_disasm_line(p, 0)}\n")
        out.write(f"* {sel_off(s)}  {idc.generate_disasm_line(s, 0)}\n")
        p = s
        for _ in range(after):
            p = idc.next_head(p, idc.BADADDR)
            if p == idc.BADADDR:
                break
            out.write(f"  {sel_off(p)}  {idc.generate_disasm_line(p, 0)}\n")
out.close()
ida_pro.qexit(0)
