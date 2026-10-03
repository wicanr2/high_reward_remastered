"""對指定函式的每個呼叫點，解出前 N 個參數並附呼叫後 M 道指令。唯讀。

用法（經 tools/ida.sh）：ida_text2_callers.py <輸出檔> <N> <M> <段:偏移>...
參數（cdecl，arg0 是最後 push 的）：立即值寫成「十進位(0x十六進位)」；暫存器來源往前 8 道指令收集對該暫存器的改寫，
遇 mov reg, imm 或 xor reg, reg 即停。near 呼叫的 push cs 略過。呼叫後 M 道指令用來看傳回值有沒有被測試。
每個呼叫點一列：呼叫點 \\t 所在函式 \\t args \\t after。
"""
import re
import sys
import traceback

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


def num(s, t):
    return int(s, 16) if (t.endswith("h") or re.search(r"[A-Fa-f]", s)) else int(s, 10)


def resolve(push_ea, op):
    m = re.match(r"^push ([0-9A-Fa-f]+)h?$", op)
    if m and m.group(1) not in REGS:
        v = num(m.group(1), op)
        return "%d(0x%X)" % (v, v)
    r = op[5:]
    if r in REGS:
        coll = []
        p = push_ea
        for _ in range(8):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            t = txt(p)
            mm = re.match(r"^mov %s, ([0-9A-Fa-f]+)h?$" % r, t)
            if mm:
                v = num(mm.group(1), t)
                if not coll:
                    return "%d(0x%X)" % (v, v)
                coll.append(t)
                break
            if t == "xor %s, %s" % (r, r):
                if not coll:
                    return "0"
                coll.append(t)
                break
            if re.match(r"^(mov|lea|add|sub|shl|shr|les|lds|pop|imul|and|or|xor|inc|dec|cwd|cbw) %s\b" % r, t):
                coll.append(t)
                if re.match(r"^(mov|lea|les|lds|pop) %s\b" % r, t):
                    break
            if idc.print_insn_mnem(p) in ("call", "retn", "retf"):
                break
        return "%s<=[%s]" % (r, " ; ".join(reversed(coll))) if coll else r
    return op[5:]


def main():
    out = open(sys.argv[1], "w", encoding="utf-8")
    N = int(sys.argv[2])
    M = int(sys.argv[3])
    for spec in sys.argv[4:]:
        seg, off = [int(x, 16) for x in spec.split(":")]
        tgt = (seg << 4) + off
        out.write("== 目標 %s\n" % spec)
        n = 0
        for s in sorted(set(x.frm for x in idautils.XrefsTo(tgt, 0) if x.iscode)):
            f = ida_funcs.get_func(s)
            args = []
            p = s
            for _ in range(60):
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
            aft = []
            q = s
            for _ in range(M):
                q = idc.next_head(q, idc.BADADDR)
                if q == idc.BADADDR:
                    break
                aft.append(txt(q))
            out.write("%s\t%s\t%s\t%s\n" % (sel_off(s), sel_off(f.start_ea) if f else "-",
                                           " | ".join(args), " ; ".join(aft)))
            n += 1
        out.write("-- 呼叫點 %d\n" % n)
    out.write("== done\n")
    out.close()


try:
    main()
except Exception:
    with open(sys.argv[1] + ".error", "w", encoding="utf-8") as e:
        e.write(traceback.format_exc())
ida_pro.qexit(0)
