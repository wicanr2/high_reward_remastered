"""對指定函式的每個呼叫點，解出前 N 個參數（cdecl，arg0 是最後 push 的）。

用法（經 tools/ida.sh）：ida_text_callargs.py <輸出檔> <N> <段:偏移>...
輸出每個目標一段：每個呼叫點一列「呼叫點 \\t 所在函式 \\t arg0 | arg1 | ...」，
立即值寫成十進位與十六進位；暫存器來源往前 4 道指令找 mov reg, imm；其餘寫原文。
往前最多掃 50 道指令，遇到 call、retn、retf 即停（跨分支只能近似，所以是下限）。唯讀。
"""
import re
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
        return "????:%05X" % ea
    return "%04X:%04X" % (seg.sel, ea - (seg.sel << 4))


def txt(ea):
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0).split(";")[0]).strip()


REGS = ("ax", "bx", "cx", "dx", "si", "di", "bp", "cs", "ds", "es", "ss")


def resolve(push_ea, op):
    m = re.match(r"^push ([0-9A-Fa-f]+)h?$", op)
    if m and m.group(1) not in REGS:
        v = int(m.group(1), 16) if (op.endswith("h") or re.search(r"[A-Fa-f]", m.group(1))) else int(m.group(1), 10)
        return "%d(0x%X)" % (v, v)
    r = op[5:]
    if r in REGS:
        p = push_ea
        for _ in range(4):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            t = txt(p)
            mm = re.match(r"^mov %s, ([0-9A-Fa-f]+)h?$" % r, t)
            if mm:
                s = mm.group(1)
                v = int(s, 16) if (t.endswith("h") or re.search(r"[A-Fa-f]", s)) else int(s, 10)
                return "%d(0x%X)" % (v, v)
            if t == "xor %s, %s" % (r, r):
                return "0"
            if re.match(r"^mov %s, " % r, t):
                return "%s<=%s" % (r, t[len("mov %s, " % r):])
            if t.startswith("pop %s" % r):
                break
        return r
    return op[5:]


out = open(sys.argv[1], "w", encoding="utf-8")
N = int(sys.argv[2])
for spec in sys.argv[3:]:
    seg, off = [int(x, 16) for x in spec.split(":")]
    tgt = (seg << 4) + off
    out.write("== 目標 %s\n" % spec)
    n = 0
    for s in sorted(set(x.frm for x in idautils.XrefsTo(tgt, 0) if x.iscode)):
        f = ida_funcs.get_func(s)
        args = []
        p = s
        for _ in range(50):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            mn = idc.print_insn_mnem(p)
            if mn in ("call", "retn", "retf"):
                break
            if mn == "push":
                t = txt(p)
                if t == "push cs":
                    continue
                args.append(resolve(p, t))
                if len(args) == N:
                    break
        out.write("%s\t%s\t%s\n" % (sel_off(s), sel_off(f.start_ea) if f else "-", " | ".join(args)))
        n += 1
    out.write("-- 呼叫點 %d\n" % n)
out.write("== done\n")
out.close()
ida_pro.qexit(0)
