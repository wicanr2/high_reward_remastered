"""掃描 MAIN.EXE 全部段，找出含 Big5 雙位元組字的 NUL 結尾字串，並列出指向它們的 xref。

用法（經 tools/ida.sh）：ida_text_strings.py <輸出檔前綴>
  <前綴>.tsv  每筆字串一列：selector:offset、線性位址、段類別、位元組數（不含 NUL）、雙位元組字數、
              ASCII 可印數、控制位元組數、xref 數、xref 來源（最多 6 個，格式 來源:所在函式起點）、內容 hex（最多 160 bytes）
  <前綴>.seg  每個段的彙總（字串數、雙位元組字數、xref 為 0 的字串數）
  <前綴>.asc  純 ASCII 字串（長度 >= 4、含空白或 % 或英文字母）的數量彙總與前 200 筆，只列位址與長度
嚴格判定：字串起點的前一位元組必須是 0（或段首），內容只能是 Big5 雙位元組（lead A1-F9、trail 40-7E、A1-FE）、
可印 ASCII、0x0A、0x0D、0x09，並以 NUL 結束。唯讀，不改資料庫。
"""
import sys

import ida_auto
import ida_bytes
import ida_funcs
import ida_pro
import ida_segment
import idautils

ida_auto.auto_wait()
prefix = sys.argv[1]


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return "????:%05X" % ea
    return "%04X:%04X" % (seg.sel, ea - (seg.sel << 4))


def is_lead(b):
    return 0xA1 <= b <= 0xF9


def is_trail(b):
    return 0x40 <= b <= 0x7E or 0xA1 <= b <= 0xFE


tsv = open(prefix + ".tsv", "w", encoding="utf-8")
tsv.write("sel_off\tlinear\tclass\tnbytes\tbig5\tascii\tctl\txrefs\txref_from(func)\thex\n")
segf = open(prefix + ".seg", "w", encoding="utf-8")
segf.write("segname\tsel\tclass\tsize\tbig5_strings\tbig5_chars\tstrings_without_xref\tstart_linear\n")
asc = open(prefix + ".asc", "w", encoding="utf-8")
asc_total = 0
asc_lines = []

for sea in idautils.Segments():
    seg = ida_segment.getseg(sea)
    start, end = seg.start_ea, seg.end_ea
    cls = ida_segment.get_segm_class(seg) or ""
    name = ida_segment.get_segm_name(seg)
    data = ida_bytes.get_bytes(start, end - start) or b""
    n_str = n_chars = n_noref = 0
    i = 0
    L = len(data)
    while i < L:
        if i > 0 and data[i - 1] != 0:
            i += 1
            continue
        if data[i] == 0:
            i += 1
            continue
        j = i
        big5 = asc_n = ctl = 0
        ok = True
        while j < L:
            c = data[j]
            if c == 0:
                break
            if is_lead(c) and j + 1 < L and is_trail(data[j + 1]):
                big5 += 1
                j += 2
            elif 0x20 <= c <= 0x7E:
                asc_n += 1
                j += 1
            elif c in (0x0A, 0x0D, 0x09):
                ctl += 1
                j += 1
            else:
                ok = False
                break
        terminated = j < L and data[j] == 0
        if ok and terminated:
            ea = start + i
            if big5 >= 1:
                refs = []
                for x in idautils.XrefsTo(ea, 0):
                    f = ida_funcs.get_func(x.frm)
                    refs.append("%s:%s" % (sel_off(x.frm), sel_off(f.start_ea) if f else "-"))
                tsv.write("%s\t%#x\t%s\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n" % (
                    sel_off(ea), ea, cls, j - i, big5, asc_n, ctl, len(refs), " ".join(refs[:6]), data[i:min(j, i + 160)].hex()))
                n_str += 1
                n_chars += big5
                if not refs:
                    n_noref += 1
            elif asc_n >= 4 and any(ch in data[i:j] for ch in b" %" + bytes(range(0x41, 0x5B)) + bytes(range(0x61, 0x7B))):
                asc_total += 1
                if len(asc_lines) < 200:
                    asc_lines.append("%s\t%d" % (sel_off(ea), j - i))
        i = j + 1 if ok else i + 1
    segf.write("%s\t%04X\t%s\t%d\t%d\t%d\t%d\t%#x\n" % (name, seg.sel, cls, end - start, n_str, n_chars, n_noref, start))

asc.write("純 ASCII 字串總數(>=4, 含空白、百分號或英文字母)：%d\n" % asc_total)
asc.write("\n".join(asc_lines) + "\n")
tsv.close()
segf.close()
asc.close()
ida_pro.qexit(0)
