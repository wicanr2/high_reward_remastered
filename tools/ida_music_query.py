"""在新資料庫上批次執行唯讀查詢。命令寫在命令檔，一行一道，# 開頭為註解。

用法（經 tools/ida.sh）：ida_music_query.py <命令檔> <輸出檔>
命令（段皆為 IDA 選擇子，十六進位）：
  dis  SEG:OFF:LEN        依範圍輸出反組譯（含位元組）
  func SEG:OFF            輸出該位址所在函式的完整反組譯，另列呼叫者與被呼叫者
  refs SEG:OFF            列出指向該位址（或其所在函式起點）的所有 code 與 data 參照
  hex  SEG:OFF:LEN        十六進位傾印加 ASCII（只用於程式內部的小表，不貼原版資料內容）
  callers SEG:OFF         只列呼叫者（含參照類型），向上展開 depth 層：callers SEG:OFF depth
  find IMM                列出所有 code 指令中立即值或位移等於 IMM 的位置（16 位元）
  io                      列出所有 in／out 指令
  int                     列出所有 int n 指令（含 n）
只讀，不改資料庫。輸出檔 utf-8，結尾寫 "== done"。
"""
import re
import sys

import ida_auto
import ida_bytes
import ida_funcs
import ida_pro
import ida_segment
import ida_ua
import idautils
import idc

ida_auto.auto_wait()
cmd_path, out_path = sys.argv[1], sys.argv[2]
out = open(out_path, "w", encoding="utf-8")


def sel_of(ea):
    seg = ida_segment.getseg(ea)
    return seg.sel if seg else 0


def addr(ea):
    s = sel_of(ea)
    return "%04X:%04X" % (s, (ea - (s << 4)) & 0xFFFFFFFF)


def segname(ea):
    seg = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(seg) if seg else "?"


def fn(ea):
    f = ida_funcs.get_func(ea)
    if not f:
        return "-"
    return "%s@%s" % (idc.get_func_name(f.start_ea), addr(f.start_ea))


def parse(spec):
    p = spec.split(":")
    seg, off = int(p[0], 16), int(p[1], 16)
    ln = int(p[2], 16) if len(p) > 2 else 0
    return (seg << 4) + off, ln


def dis_line(ea):
    n = max(1, idc.get_item_size(ea))
    b = (ida_bytes.get_bytes(ea, min(n, 10)) or b"").hex(" ")
    if ida_bytes.is_code(ida_bytes.get_flags(ea)):
        txt = idc.generate_disasm_line(ea, 0)
    else:
        txt = "db %02Xh" % ida_bytes.get_byte(ea) if n == 1 else idc.generate_disasm_line(ea, 0)
    return n, "%s  %-24s %s" % (addr(ea), b, txt)


def dump_range(ea, end):
    while ea < end:
        nm = idc.get_name(ea) or ""
        n, line = dis_line(ea)
        if nm and not nm.startswith(("loc_", "locret_")) and ida_bytes.is_code(ida_bytes.get_flags(ea)):
            out.write("%s  %-24s %s:\n" % (addr(ea), "", nm))
        out.write(line + "\n")
        ea += n


def callers(st, depth, seen, indent=0):
    for r in sorted(set(idautils.CodeRefsTo(st, 0))):
        f = ida_funcs.get_func(r)
        fs = f.start_ea if f else r
        out.write("%s%s  in %s\n" % ("  " * indent, addr(r), fn(r)))
        if depth > 1 and f and fs not in seen:
            seen.add(fs)
            callers(fs, depth - 1, seen, indent + 1)


for raw in open(cmd_path, encoding="utf-8"):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split()
    c = parts[0]
    out.write("\n=== %s\n" % line)
    try:
        if c == "dis":
            ea, ln = parse(parts[1])
            dump_range(ea, ea + ln)
        elif c == "func":
            ea, _ = parse(parts[1])
            f = ida_funcs.get_func(ea)
            if not f:
                out.write("(沒有函式)\n")
                continue
            out.write("函式 %s %s 範圍 %s-%s（%s）\n" % (idc.get_func_name(f.start_ea), addr(f.start_ea), addr(f.start_ea), addr(f.end_ea), segname(f.start_ea)))
            out.write("-- 呼叫者:\n")
            callers(f.start_ea, 1, set())
            out.write("-- 被呼叫者:\n")
            callees = {}
            for h in idautils.FuncItems(f.start_ea):
                for r in idautils.CodeRefsFrom(h, 0):
                    g = ida_funcs.get_func(r)
                    if g and g.start_ea != f.start_ea and r == g.start_ea:
                        callees.setdefault(g.start_ea, []).append(addr(h))
            for g, sites in sorted(callees.items()):
                out.write("  %s %s <- %s\n" % (addr(g), idc.get_func_name(g), ",".join(sites[:6])))
            out.write("-- 反組譯:\n")
            dump_range(f.start_ea, f.end_ea)
        elif c == "refs":
            ea, _ = parse(parts[1])
            for r in sorted(set(idautils.XrefsTo(ea, 0)), key=lambda x: x.frm):
                out.write("%s  type=%d  in %s\n" % (addr(r.frm), r.type, fn(r.frm)))
            f = ida_funcs.get_func(ea)
            if f and f.start_ea != ea:
                out.write("(該位址在函式 %s 內，函式起點參照如下)\n" % fn(ea))
                for r in sorted(set(idautils.XrefsTo(f.start_ea, 0)), key=lambda x: x.frm):
                    out.write("%s  type=%d  in %s\n" % (addr(r.frm), r.type, fn(r.frm)))
        elif c == "callers":
            ea, _ = parse(parts[1])
            depth = int(parts[2]) if len(parts) > 2 else 1
            f = ida_funcs.get_func(ea)
            callers(f.start_ea if f else ea, depth, set())
        elif c == "hex":
            ea, ln = parse(parts[1])
            for i in range(0, ln, 16):
                bs = ida_bytes.get_bytes(ea + i, min(16, ln - i)) or b""
                asc = "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in bs)
                out.write("%s  %-48s %s\n" % (addr(ea + i), bs.hex(" "), asc))
        elif c == "find":
            v = int(parts[1], 16) & 0xFFFF
            for ea in idautils.Heads():
                if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
                    continue
                for opn in (0, 1, 2):
                    t = idc.get_operand_type(ea, opn)
                    if t in (idc.o_imm, idc.o_mem, idc.o_displ, idc.o_near, idc.o_far):
                        if t in (idc.o_near, idc.o_far):
                            continue
                        if (idc.get_operand_value(ea, opn) & 0xFFFF) == v:
                            out.write("%s  %s  in %s\n" % (addr(ea), idc.generate_disasm_line(ea, 0), fn(ea)))
                            break
        elif c == "io":
            for ea in idautils.Heads():
                if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
                    continue
                mn = idc.print_insn_mnem(ea)
                if mn in ("in", "out", "insb", "insw", "outsb", "outsw"):
                    out.write("%s  %s  in %s\n" % (addr(ea), idc.generate_disasm_line(ea, 0), fn(ea)))
        elif c == "int":
            for ea in idautils.Heads():
                if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
                    continue
                if idc.print_insn_mnem(ea) in ("int", "into"):
                    out.write("%s  %s  in %s\n" % (addr(ea), idc.generate_disasm_line(ea, 0), fn(ea)))
        else:
            out.write("(未知命令)\n")
    except Exception as e:  # 單一命令失敗不影響其餘
        out.write("(錯誤: %r)\n" % (e,))
    out.flush()
out.write("== done\n")
out.close()
ida_pro.qexit(0)
