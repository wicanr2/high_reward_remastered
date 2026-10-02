"""對指定函式的每個呼叫點，往前找最近 N 個 push 指令（依推入順序輸出），歸納參數來源。

用法（經 tools/ida.sh）：ida_draw_sbargs.py <輸出檔> <N> <段:偏移>
輸出每行：呼叫點、所在函式、依推入順序的 N 個 push 運算元（以 | 分隔）。
往前掃最多 40 道指令，遇到 call／retn／retf 即停止（跨分支的情形只能近似）。唯讀。
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
n = int(sys.argv[2])
seg, off = [int(x, 16) for x in sys.argv[3].split(":")]
target = (seg << 4) + off
out.write("site\tfunc\tpushes(in push order)\n")
for s in sorted(x.frm for x in idautils.XrefsTo(target, 0) if x.iscode):
    f = ida_funcs.get_func(s)
    pushes = []
    p = s
    for _ in range(40):
        p = idc.prev_head(p, 0)
        if p == idc.BADADDR:
            break
        mn = idc.print_insn_mnem(p)
        if mn in ("call", "retn", "retf"):
            break
        if mn == "push":
            txt = idc.generate_disasm_line(p, 0).split(";")[0].strip()
            pushes.append(" ".join(txt.split()))
            if len(pushes) == n:
                break
    out.write(f"{sel_off(s)}\t{sel_off(f.start_ea) if f else '-'}\t{' | '.join(reversed(pushes))}\n")
out.close()
ida_pro.qexit(0)
