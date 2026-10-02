"""列出指定函式的所有呼叫點，並嘗試解出第一個參數（呼叫前最近的一道 push）。

用法（經 tools/ida.sh）：ida_music_callargs.py <輸出檔> <段:偏移>...
cdecl 遠呼叫的第一個參數最後 push，所以取呼叫前最近的 push（略過 nop、push cs）。
push 立即值直接記數值；`mov ax, imm` 後接 push ax 也解；其餘列出原文。
只讀，不改資料庫。
"""
import re
import sys

import ida_auto
import ida_bytes
import ida_funcs
import ida_pro
import ida_segment
import idautils
import idc

ida_auto.auto_wait()
out = open(sys.argv[1], "w", encoding="utf-8")


def addr(ea):
    seg = ida_segment.getseg(ea)
    sel = seg.sel if seg else 0
    return "%04X:%04X" % (sel, ea - (sel << 4))


def fn(ea):
    f = ida_funcs.get_func(ea)
    return "%s@%s" % (idc.get_func_name(f.start_ea), addr(f.start_ea)) if f else "-"


def txt(ea):
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0).split(";")[0]).strip()


for spec in sys.argv[2:]:
    seg, off = [int(x, 16) for x in spec.split(":")]
    tgt = (seg << 4) + off
    out.write("== 目標 %s\n" % spec)
    hist = {}
    for r in sorted(set(idautils.CodeRefsTo(tgt, 0))):
        p = r
        val = None
        for _ in range(6):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            t = txt(p)
            if t in ("nop", "push cs"):
                continue
            m = re.match(r"^push ([0-9A-Fa-f]+)h?$", t)
            if m and not re.match(r"^push (ax|bx|cx|dx|si|di|bp|cs|ds|es|ss)$", t):
                val = "imm %d (0x%X)" % (int(m.group(1), 16), int(m.group(1), 16))
                break
            if t == "push ax":
                q = p
                for _ in range(3):
                    q = idc.prev_head(q, 0)
                    tq = txt(q)
                    mm = re.match(r"^mov ax, ([0-9A-Fa-f]+)h?$", tq)
                    if mm:
                        val = "imm %d (0x%X) via ax" % (int(mm.group(1), 16), int(mm.group(1), 16))
                        break
                if val is None:
                    val = "push ax（來源未解）"
                break
            val = "其他: " + t
            break
        out.write("%s  in %s  arg0=%s\n" % (addr(r), fn(r), val))
        hist[val] = hist.get(val, 0) + 1
    out.write("-- 次數 %d；參數分佈：\n" % sum(hist.values()))
    for k, v in sorted(hist.items(), key=lambda kv: -kv[1]):
        out.write("   %-40s %d\n" % (k, v))
out.write("== done\n")
out.close()
ida_pro.qexit(0)
