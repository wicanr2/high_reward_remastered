"""每個文字載入呼叫點（237B:0464、24B2:0111、24B2:0030）往後掃，標出同一函式內接著用到的顯示函式。唯讀。

用法（經 tools/ida.sh）：ida_text2_espmap.py <輸出檔> <N> <window> <段:偏移>...
輸出每個呼叫點一列：目標 \\t 呼叫點 \\t 所在函式 \\t args（前 N 個，立即值為十進位） \\t 往後 window 道指令內依序出現的顯示呼叫。
掃描依線性位址順序（不追蹤控制流），遇到下一個載入呼叫或 retf 即停；結果是推論用的對照，不是控制流證明。
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

DISPLAY = {
    "237B:01A3": "dlgA(01A3)",
    "237B:06CF": "dlgB(06CF)",
    "237B:07FE": "dlgC(07FE)",
    "25DC:18AC": "18AC",
    "25DC:1676": "1676",
    "25DC:15E7": "15E7",
    "25DC:0180": "mkobj(0180)",
    "237B:02C7": "face(02C7)",
}
LOADERS = ["237B:0464", "24B2:0111", "24B2:0030"]


def lin(spec):
    s, o = [int(x, 16) for x in spec.split(":")]
    return (s << 4) + o


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
        return "%d" % v
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
                return "%d" % v if not coll else "%s<=[%s]" % (r, " ; ".join(reversed(coll + [t])))
            if t == "xor %s, %s" % (r, r):
                return "0" if not coll else "%s<=[%s]" % (r, " ; ".join(reversed(coll + [t])))
            if re.match(r"^(mov|lea|add|sub|shl|shr|les|lds|pop|imul|and|or|xor|inc|dec) %s\b" % r, t):
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
    W = int(sys.argv[3])
    loaders = {lin(s) for s in LOADERS}
    disp = {lin(k): v for k, v in DISPLAY.items()}
    for spec in sys.argv[4:]:
        tgt = lin(spec)
        out.write("== 目標 %s\n" % spec)
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
            seen = []
            q = s
            for _ in range(W):
                q = idc.next_head(q, idc.BADADDR)
                if q == idc.BADADDR:
                    break
                mn = idc.print_insn_mnem(q)
                if mn == "retf":
                    break
                if mn == "call":
                    for x in idautils.XrefsFrom(q, 0):
                        if x.iscode and x.to in loaders:
                            q = idc.BADADDR
                            break
                        if x.iscode and x.to in disp:
                            seen.append(disp[x.to])
                    if q == idc.BADADDR:
                        break
            out.write("%s\t%s\t%s\t%s\t%s\n" % (spec, sel_off(s), sel_off(f.start_ea) if f else "-",
                                               " | ".join(args), ",".join(seen)))
    out.write("== done\n")
    out.close()


try:
    main()
except Exception:
    with open(sys.argv[1] + ".error", "w", encoding="utf-8") as e:
        e.write(traceback.format_exc())
ida_pro.qexit(0)
