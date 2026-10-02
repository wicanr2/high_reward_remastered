"""匯出函式表、呼叫圖與繪圖特徵，供 grep／awk 查詢（主機不跑 python）。

用法（經 tools/ida.sh）：ida_draw_db.py <輸出前綴>
輸出（皆 utf-8、TSV、第一行是欄名）：
  <前綴>-funcs.tsv  每個函式一列：selector:offset、線性位址、大小、段名、retn/retf 計數、
                    ret imm 參數位元組（最後一次看到的）、enter 的區域大小、特徵旗標
  <前綴>-calls.tsv  每個 call 指令與每個對函式起點的資料 xref 一列：
                    來源 selector:offset、來源函式、目標 selector:offset、目標函式、種類
特徵旗標（字串，逗號分隔）：
  v=A0C8/A000/A800 立即值載入視訊段、p=3C4/3CE/3C0/3C8/3C9/3DA 立即值載入埠號、
  out=out 指令數、movs/stos/lods=rep 串列指令數、int3f=是否含 int 3Fh
只讀 IDA 已反組譯結果，不改資料庫。
"""
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
prefix = sys.argv[1]


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return f"????:{ea:05X}"
    return f"{seg.sel:04X}:{ea - (seg.sel << 4):04X}"


VSEG = {0xA0C8: "A0C8", 0xA000: "A000", 0xA800: "A800", 0xA0C0: "A0C0", 0xA190: "A190"}
PORT = {0x3C4: "3C4", 0x3CE: "3CE", 0x3C0: "3C0", 0x3C8: "3C8", 0x3C9: "3C9", 0x3DA: "3DA", 0x3C2: "3C2", 0x3CF: "3CF", 0x3C5: "3C5"}

ff = open(prefix + "-funcs.tsv", "w", encoding="utf-8")
ff.write("addr\tlinear\tsize\tseg\tretn\tretf\tretimm\tenter_locals\tfeatures\n")
fc = open(prefix + "-calls.tsv", "w", encoding="utf-8")
fc.write("from\tfrom_func\tto\tto_func\tkind\n")

for fea in idautils.Functions():
    f = ida_funcs.get_func(fea)
    if not f:
        continue
    seg = ida_segment.getseg(fea)
    segname = ida_segment.get_segm_name(seg) if seg else ""
    retn = retf = 0
    retimm = ""
    enter_loc = ""
    feat = {}
    ea = f.start_ea
    while ea < f.end_ea:
        if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
            ea += 1
            continue
        sz = idc.get_item_size(ea)
        b0 = ida_bytes.get_byte(ea)
        mn = idc.print_insn_mnem(ea)
        if b0 == 0xC3:
            retn += 1
        elif b0 == 0xC2:
            retn += 1
            retimm = str(ida_bytes.get_word(ea + 1))
        elif b0 == 0xCB:
            retf += 1
        elif b0 == 0xCA:
            retf += 1
            retimm = str(ida_bytes.get_word(ea + 1))
        elif b0 == 0xC8 and ea == f.start_ea:
            enter_loc = str(ida_bytes.get_word(ea + 1))
        if mn == "mov" and idc.get_operand_type(ea, 1) == idc.o_imm:
            v = idc.get_operand_value(ea, 1) & 0xFFFF
            if v in VSEG and idc.get_operand_type(ea, 0) == idc.o_reg:
                feat["v=" + VSEG[v]] = 1
            if v in PORT and idc.get_operand_type(ea, 0) == idc.o_reg:
                feat["p=" + PORT[v]] = 1
        if mn in ("out", "outsb", "outsw"):
            feat["out"] = feat.get("out", 0) + 1
        line = idc.generate_disasm_line(ea, 0)
        if "movs" in mn and "rep" in line:
            feat["movs"] = feat.get("movs", 0) + 1
        elif "stos" in mn and "rep" in line:
            feat["stos"] = feat.get("stos", 0) + 1
        elif mn in ("lodsb", "lodsw"):
            feat["lods"] = feat.get("lods", 0) + 1
        if b0 == 0xCD and ida_bytes.get_byte(ea + 1) == 0x3F:
            feat["int3f"] = 1
        # call 指令
        if mn == "call":
            kinds = []
            for x in idautils.XrefsFrom(ea, 0):
                if x.type in (ida_xref.fl_CF, ida_xref.fl_CN):
                    tf = ida_funcs.get_func(x.to)
                    fc.write(
                        f"{sel_off(ea)}\t{sel_off(f.start_ea)}\t{sel_off(x.to)}\t"
                        f"{sel_off(tf.start_ea) if tf else '-'}\t{'far' if x.type == ida_xref.fl_CF else 'near'}\n"
                    )
                    kinds.append(1)
            if not kinds:
                fc.write(f"{sel_off(ea)}\t{sel_off(f.start_ea)}\t-\t-\tindirect:{line.split(';')[0].strip()}\n")
        ea += sz
    fl = ",".join(f"{k}" if v == 1 else f"{k}={v}" for k, v in sorted(feat.items()))
    ff.write(
        f"{sel_off(f.start_ea)}\t{f.start_ea:#x}\t{f.end_ea - f.start_ea}\t{segname}\t{retn}\t{retf}\t{retimm}\t{enter_loc}\t{fl}\n"
    )
    # 資料 xref 指到函式起點（遠指標表）
    for x in idautils.XrefsTo(f.start_ea, 0):
        if not x.iscode:
            cf = ida_funcs.get_func(x.frm)
            fc.write(f"{sel_off(x.frm)}\t{sel_off(cf.start_ea) if cf else '-'}\t{sel_off(f.start_ea)}\t{sel_off(f.start_ea)}\tdata\n")
ff.close()
fc.close()
ida_pro.qexit(0)
