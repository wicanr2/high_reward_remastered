"""F2/F3/F4 讀鍵普查，第一階段：全庫 int、in/out、原始位元組樣式、IVT 與 BIOS 資料區存取。

用法（經 tools/ida.sh）：ida_fkey_scan.py
輸出（容器 /work/out/）：
  fkey_ints.tsv     每個 `int n` 指令（所有段，含 overlay 與 stub），附 AH／AX 回溯與前置指令
  fkey_inout.tsv    每個 in／out／ins／outs 指令
  fkey_raw.tsv      原始位元組樣式 CD 09／CD 16／CD 21／E4 60／E5 60 的命中，標明是否為 IDA 認定的指令起點
  fkey_segzero.tsv  把 ES／DS 設為 0 或 0x40 的指令（IVT 與 BIOS 資料區存取的候選）
  fkey_scan_meta.txt 段落清單與計數
只讀 IDA 已建立的資料庫，不改資料庫。
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
OUT = "/work/out/"


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    sel = seg.sel if seg else 0
    return "%04X:%04X" % (sel & 0xFFFF, (ea - (sel << 4)) & 0xFFFFF)


def segname(ea):
    seg = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(seg) if seg else "?"


def func_of(ea):
    f = ida_funcs.get_func(ea)
    if not f:
        return ("-", "-")
    return ("%X" % f.start_ea, idc.get_func_name(f.start_ea))


def dis(ea):
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0).split(";")[0].strip())


def num(s):
    s = s.strip()
    if s.endswith(("h", "H")):
        return int(s[:-1], 16)
    return int(s, 16) if re.fullmatch(r"[0-9A-Fa-f]+", s) and re.search(r"[A-Fa-f]", s) else int(s)


MOV_AX = re.compile(r"^mov ax, (\w+)$")
MOV_AH = re.compile(r"^mov ah, (\w+)$")
MOV_AL = re.compile(r"^mov al, (\w+)$")

# ---- A. int
rows = []
for ea in idautils.Heads():
    if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
        continue
    if idc.print_insn_mnem(ea) != "int":
        continue
    n = idc.get_operand_value(ea, 0)
    ah = al = ax = None
    trail = []
    p = ea
    for _ in range(14):
        p = idc.prev_head(p, 0)
        if p == idc.BADADDR:
            break
        t = dis(p)
        trail.append("%s %s" % (sel_off(p), t))
        m = MOV_AX.match(t)
        if m and ax is None and ah is None:
            try:
                ax = num(m.group(1))
            except ValueError:
                pass
            break
        m = MOV_AH.match(t)
        if m and ah is None:
            try:
                ah = num(m.group(1))
            except ValueError:
                pass
        m = MOV_AL.match(t)
        if m and al is None:
            try:
                al = num(m.group(1))
            except ValueError:
                pass
        if t in ("xor ah, ah",) and ah is None:
            ah = 0
        if t == "xor ax, ax" and ax is None and ah is None:
            ax = 0
            break
        if t.startswith(("retn", "retf", "jmp", "call")):
            break
    if ax is not None:
        key = "AX=%04X" % ax
    elif ah is not None:
        key = "AH=%02X" % ah + (" AL=%02X" % al if al is not None else "")
    else:
        key = "AH=?"
    fa, fnm = func_of(ea)
    rows.append((ea, n, key, fa, fnm, " ; ".join(reversed(trail))))

with open(OUT + "fkey_ints.tsv", "w", encoding="utf-8") as fh:
    fh.write("linear\tsel_off\tsegment\tint\tahax\tfunc_start\tfunc_name\ttrail(oldest first)\n")
    for ea, n, key, fa, fnm, trail in rows:
        fh.write("%X\t%s\t%s\t%02X\t%s\t%s\t%s\t%s\n" % (ea, sel_off(ea), segname(ea), n, key, fa, fnm, trail))

# ---- B. in/out
io = []
for ea in idautils.Heads():
    if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
        continue
    mn = idc.print_insn_mnem(ea)
    if mn in ("in", "out", "insb", "insw", "outsb", "outsw", "insd", "outsd"):
        io.append(ea)
with open(OUT + "fkey_inout.tsv", "w", encoding="utf-8") as fh:
    fh.write("linear\tsel_off\tsegment\tfunc_start\tfunc_name\tdisasm\tprev4\n")
    for ea in io:
        fa, fnm = func_of(ea)
        pr = []
        p = ea
        for _ in range(4):
            p = idc.prev_head(p, 0)
            if p == idc.BADADDR:
                break
            pr.append(dis(p))
        fh.write("%X\t%s\t%s\t%s\t%s\t%s\t%s\n" % (ea, sel_off(ea), segname(ea), fa, fnm, dis(ea), " ; ".join(reversed(pr))))

# ---- C. raw byte
PATS = [("CD09", b"\xcd\x09"), ("CD16", b"\xcd\x16"), ("CD21", b"\xcd\x21"), ("E460", b"\xe4\x60"), ("E560", b"\xe5\x60")]
raw = []
meta = []
for s in range(ida_segment.get_segm_qty()):
    seg = ida_segment.getnseg(s)
    start, end = seg.start_ea, seg.end_ea
    meta.append("%s\t%X\t%X\t%d" % (ida_segment.get_segm_name(seg), start, end, end - start))
    data = ida_bytes.get_bytes(start, end - start)
    if not data:
        continue
    for name, pat in PATS:
        i = 0
        while True:
            i = data.find(pat, i)
            if i < 0:
                break
            ea = start + i
            fl = ida_bytes.get_flags(ea)
            is_head = ida_bytes.is_head(fl)
            is_code = ida_bytes.is_code(fl)
            is_unk = ida_bytes.is_unknown(fl)
            raw.append((name, ea, is_head, is_code, is_unk, ida_bytes.is_data(fl)))
            i += 1
with open(OUT + "fkey_raw.tsv", "w", encoding="utf-8") as fh:
    fh.write("pattern\tlinear\tsel_off\tsegment\tis_head\tis_code\tis_unknown\tis_data\tfunc_name\tdisasm_at_head\n")
    for name, ea, ih, ic, iu, idt in raw:
        h = ea if ih else idc.get_item_head(ea)
        fh.write("%s\t%X\t%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s\n" % (name, ea, sel_off(ea), segname(ea), ih, ic, iu, idt, func_of(ea)[1], dis(h) if ic else ""))

# ---- D. ES／DS 設為 0 或 0x40
sz = []
for ea in idautils.Heads():
    if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
        continue
    t = dis(ea)
    if t in ("pop es", "pop ds"):
        # push 0／push 40h 之後 pop es／ds
        q = idc.prev_head(ea, 0)
        if q != idc.BADADDR and re.match(r"^push (0|40h|0040h)$", dis(q)):
            sz.append((ea, t, [dis(q)]))
        continue
    m = re.match(r"^mov (es|ds), (\w+)$", t)
    if not m:
        continue
    reg = m.group(2)
    pr = []
    p = ea
    hit = False
    for _ in range(10):
        p = idc.prev_head(p, 0)
        if p == idc.BADADDR:
            break
        pt = dis(p)
        pr.append(pt)
        mn = idc.print_insn_mnem(p)
        if mn in ("call", "retn", "retf", "jmp", "iret"):
            break
        # 往回找第一個改寫 reg 的指令：是 xor reg,reg 或 mov reg,0／40h 才算命中，否則停
        if mn in ("cmp", "test", "push", "out"):
            continue
        if idc.print_operand(p, 0) == reg and mn not in ("cmp", "test", "push"):
            if re.match(r"^xor (\w+), \1$", pt) or re.match(r"^mov %s, (0|40h|0040h)$" % re.escape(reg), pt):
                hit = True
            break
    if re.match(r"^mov (es|ds), (0|40h)$", t):
        hit = True
    if hit:
        sz.append((ea, t, list(reversed(pr))))
with open(OUT + "fkey_segzero.tsv", "w", encoding="utf-8") as fh:
    fh.write("linear\tsel_off\tsegment\tfunc_start\tfunc_name\tdisasm\tprev4\n")
    for ea, t, pr in sz:
        fa, fnm = func_of(ea)
        fh.write("%X\t%s\t%s\t%s\t%s\t%s\t%s\n" % (ea, sel_off(ea), segname(ea), fa, fnm, t, " ; ".join(pr)))

import ida_kernwin

nheads = sum(1 for h in idautils.Heads() if ida_bytes.is_code(ida_bytes.get_flags(h)))
nfuncs = len(list(idautils.Functions()))
with open(OUT + "fkey_scan_meta.txt", "w", encoding="utf-8") as fh:
    fh.write("kernel_version=%s code_heads=%d functions=%d\n" % (ida_kernwin.get_kernel_version(), nheads, nfuncs))
    fh.write("ints=%d inout=%d raw=%d segzero=%d segments=%d\n" % (len(rows), len(io), len(raw), len(sz), ida_segment.get_segm_qty()))
    fh.write("segment\tstart\tend\tsize\n")
    fh.write("\n".join(meta) + "\n")
ida_pro.qexit(0)
