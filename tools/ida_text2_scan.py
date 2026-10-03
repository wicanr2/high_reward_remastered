"""M10 證據探針（第二輪）：資料表寫入者、緩衝鄰居、檔名字串 xref、INT 21h AH 普查。唯讀。

用法（經 tools/ida.sh）：ida_text2_scan.py <輸出前綴>
輸出（皆在 <前綴> 之後加後綴；每一節各自 try/except，錯誤寫入 -error.txt）：
  -segs.txt     全部段（選擇子、起訖、名稱、類別）
  -names.txt    3E41:0300 至 3E41:1400 內有名稱的項目與其大小
  -ops.txt      指令運算元落在指定偏移範圍的清單（位址 所在函式 種類 寫入旗標 offset旗標 值 反組譯）
  -xrefs.txt    對 3E41:0423 起的逐位元組 xref
  -strs.txt     指定檔名字串的位置與 xref
  -int21.txt    INT 21h 的 AH 普查，與 AH=4Eh 的全部站點（含所在函式、上游呼叫者）
範圍與目標寫死在腳本內，位址一律為 IDA 選擇子（執行期 ＋ 0x0EF0）。
"""
import re
import sys
import traceback

import ida_auto
import ida_bytes
import ida_funcs
import ida_idp
import ida_pro
import ida_segment
import ida_ua
import idautils
import idc

ida_auto.auto_wait()
PFX = sys.argv[1]
SEG3E41 = 0x3E41 << 4


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return "????:%05X" % ea
    return "%04X:%04X" % (seg.sel, ea - (seg.sel << 4))


def fname(ea):
    f = ida_funcs.get_func(ea)
    return sel_off(f.start_ea) if f else "-"


def txt(ea):
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0)).strip()


def ctext(ea):
    """不含註解的反組譯文字，供樣式比對。"""
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0).split(";")[0]).strip()


def segs():
    for i in range(ida_segment.get_segm_qty()):
        yield ida_segment.getnseg(i)


def code_segs():
    for s in segs():
        if ida_segment.get_segm_class(s) == "CODE" or ida_segment.segtype(s.start_ea) == ida_segment.SEG_CODE:
            yield s


def code_heads():
    for s in code_segs():
        for ea in idautils.Heads(s.start_ea, s.end_ea):
            if ida_bytes.is_code(ida_bytes.get_flags(ea)):
                yield ea


def sec_segs():
    with open(PFX + "-segs.txt", "w", encoding="utf-8") as o:
        for s in segs():
            o.write("%04X\t%05X-%05X\t%s\t%s\ttype=%d\n" % (
                s.sel, s.start_ea, s.end_ea, ida_segment.get_segm_name(s), ida_segment.get_segm_class(s),
                ida_segment.segtype(s.start_ea)))


def sec_names():
    with open(PFX + "-names.txt", "w", encoding="utf-8") as o:
        o.write("# 3E41:0300 至 3E41:1400 內有名稱的項目（位址 名稱 項目大小 旗標）\n")
        allnames = list(idautils.Names())
        for ea, name in allnames:
            if SEG3E41 + 0x300 <= ea <= SEG3E41 + 0x1400:
                fl = ida_bytes.get_flags(ea)
                o.write("%s\t%s\tsize=%d\tcode=%s data=%s\n" % (
                    sel_off(ea), name, ida_bytes.get_item_size(ea), ida_bytes.is_code(fl), ida_bytes.is_data(fl)))
        s = ida_segment.getseg(SEG3E41 + 0x423)
        o.write("# 含 3E41:0423 的段：sel=%04X %05X-%05X %s\n" % (
            s.sel, s.start_ea, s.end_ea, ida_segment.get_segm_name(s)))
        o.write("# 3E41:0423 之後的具名項目與 3E41:0423 之差：\n")
        nxt = sorted(ea for ea, n in allnames if SEG3E41 + 0x423 < ea <= SEG3E41 + 0x1400)
        for ea in nxt[:6]:
            o.write("%s\t差=%#x\n" % (sel_off(ea), ea - (SEG3E41 + 0x423)))


def sec_xrefs():
    with open(PFX + "-xrefs.txt", "w", encoding="utf-8") as o:
        for ea in range(SEG3E41 + 0x423, SEG3E41 + 0x723):
            for x in idautils.XrefsTo(ea, 0):
                o.write("to %s\tfrom %s\t%s\tfunc %s\ttype=%s\t%s\n" % (
                    sel_off(ea), sel_off(x.frm), "code" if x.iscode else "data", fname(x.frm),
                    idautils.XrefTypeName(x.type), txt(x.frm)))


RANGES = [
    ("mbtable_09D1", 0x09D1, 0x0AD0),
    ("ctype_040F", 0x040F, 0x050F),
    ("buf_0423", 0x0423, 0x0622),
]


def sec_ops():
    hits = {n: [] for n, _, _ in RANGES}
    for ea in code_heads():
        insn = ida_ua.insn_t()
        if ida_ua.decode_insn(insn, ea) == 0:
            continue
        feat = insn.get_canon_feature()
        for i in range(8):
            op = insn.ops[i]
            if op.type == ida_ua.o_void:
                break
            if op.type in (ida_ua.o_mem, ida_ua.o_displ):
                val = op.addr & 0xFFFF
            elif op.type == ida_ua.o_imm:
                val = op.value & 0xFFFF
            else:
                continue
            for n, lo, hi in RANGES:
                if lo <= val <= hi:
                    is_mem = op.type in (ida_ua.o_mem, ida_ua.o_displ)
                    wr = bool(is_mem and ida_idp.has_cf_chg(feat, i))
                    isoff = ida_bytes.is_off(ida_bytes.get_flags(ea), i)
                    hits[n].append((ea, "mem" if is_mem else "imm", wr, isoff, val))
    with open(PFX + "-ops.txt", "w", encoding="utf-8") as o:
        for n, lo, hi in RANGES:
            h = hits[n]
            o.write("== %s 偏移 %04X-%04X：共 %d 筆（mem 寫入 %d）\n" % (
                n, lo, hi, len(h), sum(1 for r in h if r[2])))
            for ea, kind, wr, isoff, val in h:
                o.write("%s\t%s\t%s\t%s\toffset=%s\t%04X\t%s\n" % (
                    sel_off(ea), fname(ea), kind, "WRITE" if wr else "read", isoff, val, txt(ea)))


NAMES = [b"sp.mes", b"uwasa.mes", b"country.mes", b"shoptab.tbl", b"system.mes", b"powermes.mes",
         b"espmes.mrg", b"cfont.15", b"face.mrg", b"gmap.pxs", b"spoint.mrg"]


def sec_strs():
    found = {n: [] for n in NAMES}
    for s in segs():
        sz = s.end_ea - s.start_ea
        if sz <= 0 or sz > 0x20000:
            continue
        data = ida_bytes.get_bytes(s.start_ea, sz)
        if not data:
            continue
        low = data.lower()
        for n in NAMES:
            k = 0
            while True:
                k = low.find(n, k)
                if k < 0:
                    break
                pre_ok = k == 0 or data[k - 1] == 0
                post_ok = k + len(n) < len(data) and data[k + len(n)] == 0
                if pre_ok and post_ok:
                    found[n].append(s.start_ea + k)
                k += 1
    noxref = []
    with open(PFX + "-strs.txt", "w", encoding="utf-8") as o:
        for n in NAMES:
            o.write("== %s：%d 處字串\n" % (n.decode(), len(found[n])))
            for ea in found[n]:
                o.write("-- 字串 %s  name=%s\n" % (sel_off(ea), idc.get_name(ea)))
                xs = sorted(idautils.XrefsTo(ea, 0), key=lambda r: r.frm)
                if not xs:
                    noxref.append((n, ea))
                for x in xs:
                    o.write("   xref %s  func %s  %s  %s\n" % (
                        sel_off(x.frm), fname(x.frm), idautils.XrefTypeName(x.type), txt(x.frm)))
        o.write("\n== 立即值等於字串偏移的指令（只列 IDA 沒有 xref 的字串）\n")
        if noxref:
            offs = {}
            for n, ea in noxref:
                seg = ida_segment.getseg(ea)
                offs.setdefault(ea - (seg.sel << 4), []).append((n, ea))
            for ia in code_heads():
                insn = ida_ua.insn_t()
                if ida_ua.decode_insn(insn, ia) == 0:
                    continue
                for i in range(8):
                    op = insn.ops[i]
                    if op.type == ida_ua.o_void:
                        break
                    if op.type == ida_ua.o_imm and (op.value & 0xFFFF) in offs:
                        o.write("   imm %s  func %s  %s  <-字串 %s\n" % (
                            sel_off(ia), fname(ia), txt(ia),
                            ",".join("%s@%s" % (n.decode(), sel_off(e)) for n, e in offs[op.value & 0xFFFF])))


def num(s, t):
    return int(s, 16) if (t.endswith("h") or re.search(r"[A-Fa-f]", s)) else int(s, 10)


def ah_of(ea, limit=12):
    p = ea
    for _ in range(limit):
        p = idc.prev_head(p, 0)
        if p == idc.BADADDR:
            return None
        t = ctext(p)
        m = re.match(r"^mov ah, ([0-9A-Fa-f]+)h?$", t)
        if m:
            return num(m.group(1), t)
        m = re.match(r"^mov ax, ([0-9A-Fa-f]+)h?$", t)
        if m:
            return (num(m.group(1), t) >> 8) & 0xFF
        if re.match(r"^(mov|xor|lea|les|lds|pop|add|sub) (ah|ax)\b", t):
            return "var<=" + t
        if idc.print_insn_mnem(p) in ("retn", "retf"):
            return None
    return None


def sec_int21():
    sites = []
    for ea in code_heads():
        if idc.print_insn_mnem(ea) == "int" and idc.get_operand_value(ea, 0) == 0x21:
            sites.append((ea, ah_of(ea)))
    cnt = {}
    for ea, ah in sites:
        k = ("%02X" % ah) if isinstance(ah, int) else ("?" if ah is None else "var")
        cnt[k] = cnt.get(k, 0) + 1
    with open(PFX + "-int21.txt", "w", encoding="utf-8") as o:
        o.write("INT 21h 站點共 %d；AH 分布：%s\n" % (len(sites), ", ".join("%s:%d" % kv for kv in sorted(cnt.items()))))
        o.write("\n== AH=4Eh 站點（FindFirst）\n")
        for ea, ah in sites:
            if ah == 0x4E:
                o.write("%s  func %s  %s\n" % (sel_off(ea), fname(ea), txt(ea)))
                f = ida_funcs.get_func(ea)
                if f:
                    for x in sorted(idautils.XrefsTo(f.start_ea, 0), key=lambda r: r.frm):
                        o.write("   caller %s  func %s  %s\n" % (sel_off(x.frm), fname(x.frm), txt(x.frm)))
        o.write("\n== AH 無法由前 12 道指令判定（?）或來自變數（var）的站點\n")
        for ea, ah in sites:
            if not isinstance(ah, int):
                o.write("%s  func %s  ah=%s  %s\n" % (sel_off(ea), fname(ea), ah, txt(ea)))
        o.write("\n== AH=4Fh（FindNext）與 AH=11h／12h（FCB 搜尋）\n")
        for ea, ah in sites:
            if ah in (0x4F, 0x11, 0x12):
                o.write("%s  func %s  ah=%02X  %s\n" % (sel_off(ea), fname(ea), ah, txt(ea)))
        o.write("\n== 名稱含 find 的符號\n")
        for ea, name in idautils.Names():
            if "find" in name.lower():
                o.write("%s  %s\n" % (sel_off(ea), name))
        o.write("\n== 全部 INT 21h 站點的 AH 值（位址 AH）\n")
        for ea, ah in sites:
            o.write("%s  %s\n" % (sel_off(ea), ("%02X" % ah) if isinstance(ah, int) else str(ah)))


def sec_dosapi():
    subs = ("int86", "intdos", "intr", "bdos", "dos", "find", "ffblk", "search", "dir", "geninterrupt")
    with open(PFX + "-dosapi.txt", "w", encoding="utf-8") as o:
        o.write("== 名稱含 %s 的符號\n" % ",".join(subs))
        for ea, name in idautils.Names():
            if any(k in name.lower() for k in subs):
                o.write("%s  %s\n" % (sel_off(ea), name))
        o.write("\n== 寫入記憶體的立即值 0x4E 或 0x4E00（可能是 r.h.ah ＝ 4Eh 或 r.x.ax ＝ 4E00h 的準備）\n")
        for ea in code_heads():
            insn = ida_ua.insn_t()
            if ida_ua.decode_insn(insn, ea) == 0:
                continue
            if idc.print_insn_mnem(ea) != "mov":
                continue
            o0, o1 = insn.ops[0], insn.ops[1]
            if o0.type in (ida_ua.o_mem, ida_ua.o_displ, ida_ua.o_phrase) and o1.type == ida_ua.o_imm \
                    and (o1.value & 0xFFFF) in (0x4E, 0x4E00):
                o.write("%s  func %s  %s\n" % (sel_off(ea), fname(ea), txt(ea)))
        o.write("\n== 非 INT 21h 的 INT 站點（向量 位址 所在函式）\n")
        for ea in code_heads():
            if idc.print_insn_mnem(ea) == "int":
                v = idc.get_operand_value(ea, 0)
                if v != 0x21:
                    o.write("%02Xh  %s  func %s\n" % (v, sel_off(ea), fname(ea)))


def sec_segusers():
    """載入段值 0x3E41（對話緩衝所在段）或 0x62FF（dseg）的函式，以及它們內部落在範圍內的記憶體運算元。"""
    targets = {0x3E41: ("seg3E41", [(0x423, 0x622)]), 0x62FF: ("dseg", [(0x9D1, 0xAD0), (0x40F, 0x50F)])}
    users = {k: {} for k in targets}
    for ea in code_heads():
        insn = ida_ua.insn_t()
        if ida_ua.decode_insn(insn, ea) == 0:
            continue
        for i in range(8):
            op = insn.ops[i]
            if op.type == ida_ua.o_void:
                break
            if op.type == ida_ua.o_imm and (op.value & 0xFFFF) in targets:
                f = ida_funcs.get_func(ea)
                users[op.value & 0xFFFF].setdefault(f.start_ea if f else ea, []).append(ea)
    with open(PFX + "-segusers.txt", "w", encoding="utf-8") as o:
        for sv, (nm, ranges) in targets.items():
            o.write("== %s（段值 %04X）：載入此段值的函式 %d 個\n" % (nm, sv, len(users[sv])))
            for fs, loads in sorted(users[sv].items()):
                f = ida_funcs.get_func(fs)
                end = f.end_ea if f else fs + 1
                o.write("-- 函式 %s（載入於 %s）\n" % (sel_off(fs), ",".join(sel_off(x) for x in loads[:4])))
                for ea in idautils.Heads(fs, end):
                    if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
                        continue
                    insn = ida_ua.insn_t()
                    if ida_ua.decode_insn(insn, ea) == 0:
                        continue
                    feat = insn.get_canon_feature()
                    for i in range(8):
                        op = insn.ops[i]
                        if op.type == ida_ua.o_void:
                            break
                        if op.type in (ida_ua.o_mem, ida_ua.o_displ):
                            val = op.addr & 0xFFFF
                            if any(lo <= val <= hi for lo, hi in ranges):
                                o.write("     %s  %s  %s\n" % (sel_off(ea), "WRITE" if ida_idp.has_cf_chg(feat, i) else "read",
                                                              txt(ea)))
                        elif op.type == ida_ua.o_imm and any(lo <= (op.value & 0xFFFF) <= hi for lo, hi in ranges):
                            o.write("     %s  imm   %s\n" % (sel_off(ea), txt(ea)))


def sec_rawcd21():
    """原始位元組層：全部 CD 21 的出現位置，與 IDA 判定的 INT 21h 站點比對；列出 IDA 沒認成指令的，以及前 8 bytes 含 B4 4E／B8 xx 4E 者。"""
    code_sites = set()
    for ea in code_heads():
        if idc.print_insn_mnem(ea) == "int" and idc.get_operand_value(ea, 0) == 0x21:
            code_sites.add(ea)
    total = 0
    unmatched = []
    hits4e = []
    for s in segs():
        sz = s.end_ea - s.start_ea
        if sz <= 0 or sz > 0x40000:
            continue
        data = ida_bytes.get_bytes(s.start_ea, sz)
        if not data:
            continue
        k = 0
        while True:
            k = data.find(b"\xcd\x21", k)
            if k < 0:
                break
            ea = s.start_ea + k
            total += 1
            pre = data[max(0, k - 8):k]
            is4e = b"\xb4\x4e" in pre or (len(pre) >= 3 and any(pre[i] == 0xB8 and pre[i + 2] == 0x4E for i in range(len(pre) - 2)))
            if ea not in code_sites:
                unmatched.append((ea, pre.hex(), data[k:k + 4].hex()))
            if is4e:
                hits4e.append((ea, ea in code_sites, pre.hex()))
            k += 1
    with open(PFX + "-rawcd21.txt", "w", encoding="utf-8") as o:
        o.write("原始位元組 CD 21 共 %d 處（段大小 <= 256KB 的段）；IDA 判定的 INT 21h 指令站點 %d 處\n" % (total, len(code_sites)))
        o.write("未被 IDA 認成 INT 21h 指令的 CD 21：%d 處\n" % len(unmatched))
        for ea, pre, post in unmatched:
            o.write("  %s  前8bytes=%s  後4bytes=%s  段類別=%s\n" % (
                sel_off(ea), pre, post, ida_segment.get_segm_class(ida_segment.getseg(ea))))
        o.write("前 8 bytes 含 B4 4E 或 B8 xx 4E 的 CD 21：%d 處\n" % len(hits4e))
        for ea, is_code, pre in hits4e:
            o.write("  %s  IDA指令=%s  前8bytes=%s\n" % (sel_off(ea), is_code, pre))


errs = []
for fn in (sec_segs, sec_names, sec_xrefs, sec_ops, sec_strs, sec_int21, sec_dosapi, sec_segusers, sec_rawcd21):
    try:
        fn()
    except Exception:
        errs.append(fn.__name__ + "\n" + traceback.format_exc())
with open(PFX + "-error.txt", "w", encoding="utf-8") as o:
    o.write("\n".join(errs) if errs else "no errors\n")
ida_pro.qexit(0)
