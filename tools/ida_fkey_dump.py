"""F2/F3/F4 讀鍵普查，通用傾印：依規格檔傾印函式、呼叫者與位址附近的反組譯。

用法（經 tools/ida.sh）：ida_fkey_dump.py <規格檔> <輸出檔>
規格檔（容器內路徑，例如 /work/out/spec_1.txt）每行一項，位址一律是 IDA 線性位址（十六進位）：
  func <ea>                 傾印包含 ea 的整個函式（位址、bytes、反組譯）
  callers <ea> <前> <後>    列出函式（包含 ea 的函式起點）的所有 xref 來源，每個來源附前後各 N 道指令；
                            來源是 stub（短函式內的 jmp）時，再往上追它的呼叫者
  ctx <ea> <前> <後>        ea 前後各 N 道指令
  bytes <ea> <長度>         傾印原始位元組與 IDA 對每個 head 的解讀
  flowdump <ea> <深度>      函式反組譯後，對其內的 call 目標遞迴傾印到指定深度（只列名稱與位址）
只讀，不改資料庫。
"""
import re
import sys

import ida_auto
import ida_bytes
import ida_funcs
import ida_pro
import ida_segment
import ida_xref
import idautils
import idc

ida_auto.auto_wait()
spec_path, out_path = sys.argv[1], sys.argv[2]
out = open(out_path, "w", encoding="utf-8")


def w(s=""):
    out.write(s + "\n")


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    sel = seg.sel if seg else 0
    return "%04X:%04X" % (sel & 0xFFFF, (ea - (sel << 4)) & 0xFFFFF)


def segname(ea):
    seg = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(seg) if seg else "?"


def line(ea, mark=""):
    sz = idc.get_item_size(ea)
    bs = ida_bytes.get_bytes(ea, min(sz, 8)) or b""
    return "%s%s  %X  %-18s %s" % (mark, sel_off(ea), ea, " ".join("%02x" % b for b in bs), re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0)))


def fstart(ea):
    f = ida_funcs.get_func(ea)
    return f.start_ea if f else None


def fname(ea):
    s = fstart(ea)
    return idc.get_func_name(s) if s is not None else "-"


def dump_func(ea):
    f = ida_funcs.get_func(ea)
    if not f:
        w("(no function at %X)" % ea)
        return
    w("== func %s %s %X..%X size %d seg %s" % (idc.get_func_name(f.start_ea), sel_off(f.start_ea), f.start_ea, f.end_ea, f.end_ea - f.start_ea, segname(f.start_ea)))
    for h in idautils.FuncItems(f.start_ea):
        w(line(h, "  "))
    w()


def window(ea, nb, na):
    head = idc.get_item_head(ea)
    before = []
    p = head
    for _ in range(nb):
        p = idc.prev_head(p, 0)
        if p == idc.BADADDR:
            break
        before.append(p)
    before.reverse()
    after = []
    p = head
    for _ in range(na):
        p = idc.next_head(p, idc.BADADDR)
        if p == idc.BADADDR:
            break
        after.append(p)
    for p in before:
        w(line(p, "    "))
    w(line(head, " >> "))
    for p in after:
        w(line(p, "    "))


def callers(ea, nb, na, depth=0, seen=None):
    seen = seen if seen is not None else set()
    s = fstart(ea)
    if s is None:
        s = ea
    if s in seen:
        return
    seen.add(s)
    ind = "  " * depth
    w("%s== callers of %s %s %X" % (ind, idc.get_func_name(s), sel_off(s), s))
    xs = list(idautils.XrefsTo(s, ida_xref.XREF_ALL))
    if not xs:
        w(ind + "  (no xrefs)")
    for x in xs:
        frm = x.frm
        tn = idautils.XrefTypeName(x.type)
        mn = idc.print_insn_mnem(frm)
        ff = fstart(frm)
        fsz = (ida_funcs.get_func(frm).end_ea - ida_funcs.get_func(frm).start_ea) if ff is not None else 0
        w("%s  -- from %s %X seg %s func %s type %s mnem %s" % (ind, sel_off(frm), frm, segname(frm), fname(frm), tn, mn))
        if mn == "jmp" and ff is not None and fsz <= 8 and depth < 2:
            w(ind + "     (stub alias: %s)" % fname(frm))
            callers(frm, nb, na, depth + 1, seen)
        else:
            window(frm, nb, na)
    w()


def flowdump(ea, depth, seen=None, ind=0):
    seen = seen if seen is not None else set()
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea in seen:
        return
    seen.add(f.start_ea)
    w("%s%s %s %X size %d" % ("  " * ind, idc.get_func_name(f.start_ea), sel_off(f.start_ea), f.start_ea, f.end_ea - f.start_ea))
    if depth <= 0:
        return
    for h in idautils.FuncItems(f.start_ea):
        if idc.print_insn_mnem(h) == "call":
            for x in idautils.XrefsFrom(h, ida_xref.XREF_FAR):
                if x.iscode and x.type in (ida_xref.fl_CN, ida_xref.fl_CF):
                    flowdump(x.to, depth - 1, seen, ind + 1)


for raw in open(spec_path, encoding="utf-8"):
    raw = raw.split("#")[0].strip()
    if not raw:
        continue
    parts = raw.split()
    cmd = parts[0]
    w("##### " + raw)
    try:
        if cmd == "func":
            dump_func(int(parts[1], 16))
        elif cmd == "callers":
            callers(int(parts[1], 16), int(parts[2]), int(parts[3]))
        elif cmd == "ctx":
            window(int(parts[1], 16), int(parts[2]), int(parts[3]))
            w()
        elif cmd == "bytes":
            ea = int(parts[1], 16)
            n = int(parts[2])
            bs = ida_bytes.get_bytes(ea, n) or b""
            w("bytes " + " ".join("%02x" % b for b in bs))
            p = idc.get_item_head(ea)
            while p < ea + n and p != idc.BADADDR:
                w(line(p, "  "))
                p = idc.next_head(p, idc.BADADDR)
            w()
        elif cmd == "flowdump":
            flowdump(int(parts[1], 16), int(parts[2]))
            w()
        elif cmd == "xrefrange":
            # xrefrange <ea> <長度>：範圍內每個位址的 xref 來源（只列有 xref 的位址）
            a0 = int(parts[1], 16)
            ln = int(parts[2], 16)
            for a in range(a0, a0 + ln):
                for x in idautils.XrefsTo(a, ida_xref.XREF_ALL):
                    w("  %X <- %s %X func %s type %s : %s" % (a, sel_off(x.frm), x.frm, fname(x.frm), idautils.XrefTypeName(x.type), re.sub(r"\s+", " ", idc.generate_disasm_line(x.frm, 0))))
            w()
        elif cmd == "pushargs":
            # pushargs <ea>：每個呼叫者往回收集到上一個 call／add sp／ret／jmp 之間的 push 運算元（執行順序，第一個是最右邊的參數）
            ea0 = int(parts[1], 16)
            s0 = fstart(ea0)
            for x in idautils.XrefsTo(s0 if s0 is not None else ea0, ida_xref.XREF_ALL):
                if not x.iscode:
                    continue
                p = x.frm
                args = []
                for _ in range(24):
                    p = idc.prev_head(p, 0)
                    if p == idc.BADADDR:
                        break
                    mn = idc.print_insn_mnem(p)
                    if mn in ("call", "retn", "retf", "jmp", "iret"):
                        break
                    if mn == "add" and idc.print_operand(p, 0) == "sp":
                        break
                    if mn == "push":
                        args.append(re.sub(r"\s+", " ", idc.generate_disasm_line(p, 0).split(";")[0].strip()))
                args.reverse()
                w("  %s %X func %s : %s" % (sel_off(x.frm), x.frm, fname(x.frm), " | ".join(args)))
            w()
        elif cmd == "grepc":
            # grepc <regex> <前> <後> [最大筆數]：符合的指令附前後 N 道指令
            rx = re.compile(parts[1], re.I)
            nb, na = int(parts[2]), int(parts[3])
            mx = int(parts[4]) if len(parts) > 4 else 100
            n = 0
            for h in idautils.Heads():
                if not ida_bytes.is_code(ida_bytes.get_flags(h)):
                    continue
                t = re.sub(r"\s+", " ", idc.generate_disasm_line(h, 0).split(";")[0].strip())
                if rx.search(t):
                    n += 1
                    if n <= mx:
                        w("  -- %s %X seg %s func %s" % (sel_off(h), h, segname(h), fname(h)))
                        window(h, nb, na)
            w("  total %d" % n)
            w()
        elif cmd == "seqgrep":
            # seqgrep <K> <rx_prev> <rx_cur> [最大筆數]：rx_cur 命中的指令，前 K 道指令內有 rx_prev 命中者
            K = int(parts[1])
            rp = re.compile(parts[2], re.I)
            rc = re.compile(parts[3], re.I)
            mx = int(parts[4]) if len(parts) > 4 else 100
            n = 0
            for h in idautils.Heads():
                if not ida_bytes.is_code(ida_bytes.get_flags(h)):
                    continue
                t = re.sub(r"\s+", " ", idc.generate_disasm_line(h, 0).split(";")[0].strip())
                if not rc.search(t):
                    continue
                p = h
                prev = []
                hit = False
                for _ in range(K):
                    p = idc.prev_head(p, 0)
                    if p == idc.BADADDR:
                        break
                    pt = re.sub(r"\s+", " ", idc.generate_disasm_line(p, 0).split(";")[0].strip())
                    prev.append(pt)
                    if rp.search(pt):
                        hit = True
                if hit:
                    n += 1
                    if n <= mx:
                        w("  %s %X %-8s %s  <= %s  [%s]" % (sel_off(h), h, segname(h), t, " ; ".join(reversed(prev)), fname(h)))
            w("  total %d" % n)
            w()
        elif cmd == "name":
            # name <regex>：列出名稱符合的符號（位址、名稱）
            rx = re.compile(parts[1], re.I)
            for ea, nm in idautils.Names():
                if rx.search(nm):
                    w("  %s %X %s" % (sel_off(ea), ea, nm))
            w()
        elif cmd == "unkstat":
            # unkstat：每段未定義 byte 數（前 40 段）；常駐段（seg 開頭）另列 >=32 bytes 的連續區間與前 12 bytes
            rows = []
            for s in range(ida_segment.get_segm_qty()):
                seg = ida_segment.getnseg(s)
                nm = ida_segment.get_segm_name(seg)
                n = 0
                ranges = []
                ea = seg.start_ea
                cur = None
                while ea < seg.end_ea:
                    fl = ida_bytes.get_flags(ea)
                    if ida_bytes.is_unknown(fl):
                        n += 1
                        if cur is None:
                            cur = ea
                    else:
                        if cur is not None:
                            ranges.append((cur, ea - cur))
                            cur = None
                    ea += 1
                if cur is not None:
                    ranges.append((cur, seg.end_ea - cur))
                rows.append((n, nm, seg.start_ea, seg.end_ea - seg.start_ea, ranges))
            rows.sort(reverse=True)
            tot = sum(r[0] for r in rows)
            w("  total unknown bytes %d in %d segments" % (tot, len(rows)))
            for n, nm, st, sz, ranges in rows[:40]:
                w("  %-8s start %X size %d unknown %d ranges %d" % (nm, st, sz, n, len(ranges)))
            w("  -- big unknown ranges (>=32) in segments not starting with ovr/stub")
            for n, nm, st, sz, ranges in rows:
                if nm.startswith(("ovr", "stub")):
                    continue
                for a, ln in ranges:
                    if ln >= 32:
                        bs = ida_bytes.get_bytes(a, 12) or b""
                        w("  %s %X len %d : %s" % (nm, a, ln, " ".join("%02x" % b for b in bs)))
            w()
        elif cmd == "xrefsto":
            ea = int(parts[1], 16)
            for x in idautils.XrefsTo(ea, ida_xref.XREF_ALL):
                w("  from %s %X seg %s func %s type %s : %s" % (sel_off(x.frm), x.frm, segname(x.frm), fname(x.frm), idautils.XrefTypeName(x.type), re.sub(r"\s+", " ", idc.generate_disasm_line(x.frm, 0))))
            w()
        elif cmd == "grep":
            # grep <regex（不含空白，用 \s 代替）> [最大行數]
            rx = re.compile(parts[1], re.I)
            mx = int(parts[2]) if len(parts) > 2 else 200
            n = 0
            for h in idautils.Heads():
                if not ida_bytes.is_code(ida_bytes.get_flags(h)):
                    continue
                t = re.sub(r"\s+", " ", idc.generate_disasm_line(h, 0).split(";")[0].strip())
                if rx.search(t):
                    n += 1
                    if n <= mx:
                        w("  %s %X %-18s %s  [%s]" % (sel_off(h), h, segname(h), t, fname(h)))
            w("  total %d" % n)
            w()
        elif cmd == "rawpat":
            # rawpat <十六進位位元組，無空白> ：全庫原始位元組搜尋，標明 head／code／data 狀態
            pat = bytes.fromhex(parts[1])
            n = 0
            for s in range(ida_segment.get_segm_qty()):
                seg = ida_segment.getnseg(s)
                data = ida_bytes.get_bytes(seg.start_ea, seg.end_ea - seg.start_ea)
                if not data:
                    continue
                i = 0
                while True:
                    i = data.find(pat, i)
                    if i < 0:
                        break
                    ea = seg.start_ea + i
                    fl = ida_bytes.get_flags(ea)
                    n += 1
                    if n <= 100:
                        w("  %s %X seg %s head=%d code=%d unk=%d data=%d func %s : %s" % (sel_off(ea), ea, segname(ea), ida_bytes.is_head(fl), ida_bytes.is_code(fl), ida_bytes.is_unknown(fl), ida_bytes.is_data(fl), fname(ea), re.sub(r"\s+", " ", idc.generate_disasm_line(idc.get_item_head(ea), 0))))
                    i += 1
            w("  total %d" % n)
            w()
        else:
            w("(unknown command)")
    except Exception as e:  # noqa
        w("ERROR: %r" % (e,))
out.close()
ida_pro.qexit(0)
