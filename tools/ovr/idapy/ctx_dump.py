"""在既有資料庫上做唯讀查詢（./ida.sh reuse MAIN.EXE ctx_dump.py <輸出檔> 段:偏移:長度 ... -- 函式位址 ...）。

段:偏移:長度 皆十六進位，段為 IDA 選擇子，輸出該範圍的反組譯。
「--」之後的每個 段:偏移 列出指向該位址所在函式的呼叫點（含所屬段落與類別）。
最後附 ovr 段落的 code／data／未定義 byte 統計。結尾寫 "== done"。
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
args = sys.argv[1:]
out = open(args[0], "w", encoding="utf-8")
rest = args[1:]
ranges, funcs = [], []
if "--" in rest:
    k = rest.index("--")
    ranges, funcs = rest[:k], rest[k + 1:]
else:
    ranges = rest


def addr(ea):
    seg = ida_segment.getseg(ea)
    sel = seg.sel if seg else 0
    return "%04X:%04X" % (sel, ea - (sel << 4))


def segname(ea):
    seg = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(seg) if seg else "?"


for spec in ranges:
    seg, off, ln = [int(x, 16) for x in spec.split(":")]
    ea = (seg << 4) + off
    end = ea + ln
    out.write(f"== {seg:04X}:{off:04X} len {ln:#x}（{segname(ea)}）\n")
    while ea < end:
        n = max(1, idc.get_item_size(ea))
        b = (ida_bytes.get_bytes(ea, min(n, 10)) or b"").hex(" ")
        nm = idc.get_name(ea) or ""
        if nm and ida_bytes.is_code(ida_bytes.get_flags(ea)):
            out.write(f"{addr(ea)}  {'':24} {nm}:\n")
        out.write(f"{addr(ea)}  {b:24} {idc.generate_disasm_line(ea, 0)}\n")
        ea += n

for spec in funcs:
    seg, off = [int(x, 16) for x in spec.split(":")]
    ea = (seg << 4) + off
    f = ida_funcs.get_func(ea)
    st = f.start_ea if f else ea
    xs = list(idautils.CodeRefsTo(st, 0))
    out.write(f"== 呼叫 {addr(st)} {idc.get_func_name(st)}（{segname(st)}）的位置：{len(xs)}\n")
    for x in xs:
        cf = ida_funcs.get_func(x)
        out.write(f"   {addr(x)} [{segname(x)}] 在 {idc.get_func_name(x)}  {idc.generate_disasm_line(x, 0)}\n")

code = data = undef = 0
for s in idautils.Segments():
    seg = ida_segment.getseg(s)
    if not ida_segment.get_segm_name(seg).startswith("ovr"):
        continue
    ea = seg.start_ea
    while ea < seg.end_ea:
        fl = ida_bytes.get_flags(ea)
        n = max(1, idc.get_item_size(ea))
        if ida_bytes.is_code(fl):
            code += n
        elif ida_bytes.is_unknown(fl):
            undef += 1
            n = 1
        else:
            data += n
        ea += n
out.write(f"== ovr 段落 byte 統計：code {code}，data {data}，未定義 {undef}\n")
out.write("== done\n")
out.close()
ida_pro.qexit(0)
