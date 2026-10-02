"""搜尋與音樂、音效相關的字串，列出位址、完整字串與 IDA 已解出的資料參照。

用法（經 tools/ida.sh）：ida_music_strings.py <輸出檔> [額外關鍵字…]
方法：對每個段落的原始位元組做不分大小寫的子字串搜尋（不依賴 IDA 的字串清單），
把命中處向左右擴張到非可印字元為止，列出該字串與 DataRefsTo。
另列：以該字串偏移為立即值的 code 指令（IDA 沒建立 xref 時的後備，只在同一資料段內比對偏移）。
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
out_path = sys.argv[1]
extra = [a for a in sys.argv[2:]]
KEYS = [
    "ctmidi", ".drv", "drv", ".mid", "midi", "mpu", "adlib", "opl", "sound", "music", "blaster",
    ".pcm", ".voc", ".wav", "sblaster", "fm", "snd", "bgm", "cfg", "config", "ctmid", "gus",
    "roland", "mt-32", "mt32", "sb ", "pcm", "audio", "speaker", "volume", "tempo", "play",
] + extra

out = open(out_path, "w", encoding="utf-8")


def addr(ea):
    seg = ida_segment.getseg(ea)
    sel = seg.sel if seg else 0
    return "%04X:%04X" % (sel, ea - (sel << 4))


def fname(ea):
    f = ida_funcs.get_func(ea)
    if not f:
        return "-"
    return "%s@%s" % (idc.get_func_name(f.start_ea), addr(f.start_ea))


PRINT = set(range(0x20, 0x7F))
hits = {}
for sea in idautils.Segments():
    seg = ida_segment.getseg(sea)
    end = seg.end_ea
    size = end - sea
    if size <= 0:
        continue
    data = ida_bytes.get_bytes(sea, size) or b""
    low = data.lower()
    for k in KEYS:
        kb = k.lower().encode()
        for m in re.finditer(re.escape(kb), low):
            i = m.start()
            a = i
            while a > 0 and data[a - 1] in PRINT:
                a -= 1
            b = i + len(kb)
            while b < len(data) and data[b] in PRINT:
                b += 1
            if b - a < 4:
                continue
            hits.setdefault(sea + a, (b - a, data[a:b].decode("latin1")))

out.write("# 字串命中：位址 長度 字串 | 資料參照\n")
for ea in sorted(hits):
    ln, s = hits[ea]
    seg = ida_segment.getseg(ea)
    sel = seg.sel
    off = ea - (sel << 4)
    refs = list(idautils.DataRefsTo(ea))
    rs = "; ".join("%s(%s)" % (addr(r), fname(r)) for r in refs[:8])
    out.write("%s %3d %r | %s\n" % (addr(ea), ln, s, rs))

# 後備：code 內以 offset 為立即值
out.write("\n# 後備：code 指令的立即值等於字串偏移（同一個 dseg 6021 內的字串）\n")
targets = {}
for ea, (ln, s) in hits.items():
    seg = ida_segment.getseg(ea)
    if seg.sel == 0x6021 or True:
        targets.setdefault(ea - (seg.sel << 4), []).append((ea, s))
for ea in idautils.Heads():
    fl = ida_bytes.get_flags(ea)
    if not ida_bytes.is_code(fl):
        continue
    for opn in (0, 1):
        t = idc.get_operand_type(ea, opn)
        if t == idc.o_imm:
            v = idc.get_operand_value(ea, opn) & 0xFFFF
            if v in targets and v >= 0x100:
                for tea, s in targets[v]:
                    sel = ida_segment.getseg(tea).sel
                    if sel in (0x6021,):
                        out.write("%s (%s) %s  ->  %s %r\n" % (addr(ea), fname(ea), idc.generate_disasm_line(ea, 0), addr(tea), s))
out.write("== done\n")
out.close()
ida_pro.qexit(0)
