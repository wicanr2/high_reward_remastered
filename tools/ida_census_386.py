"""統計 16 位元 DOS 程式內所有指令的 386 形式（前綴與雙位元組 opcode）。

用法（經 tools/ida.sh）：ida_census_386.py <輸出.json>
輸出：段落清單、函式數、各 386 形式的次數與前 40 個位址（segment:offset、線性位址、bytes）。
只讀 IDA 已反組譯出的指令，不改資料庫。
形式包含：帶 66、67、64、65 前綴的指令、`0F` 雙位元組 opcode，以及無前綴但只存在於 386 的
`8C`／`8E`（reg 欄位為 4、5，即 FS、GS 的段暫存器移動）。
"""
import json
import sys

import ida_auto
import ida_bytes
import ida_funcs
import ida_pro
import ida_segment
import idautils
import idc

PREFIX = {0x66, 0x67, 0xF2, 0xF3, 0x2E, 0x36, 0x3E, 0x26, 0x64, 0x65, 0xF0}

ida_auto.auto_wait()
out_path = sys.argv[1] if len(sys.argv) > 1 else "/work/out/census386.json"

segs = []
for s in idautils.Segments():
    seg = ida_segment.getseg(s)
    segs.append({"name": ida_segment.get_segm_name(seg), "start": seg.start_ea,
                 "end": seg.end_ea, "bitness": seg.bitness, "sel": seg.sel})

forms = {}
total = 0
for s in idautils.Segments():
    seg = ida_segment.getseg(s)
    ea = seg.start_ea
    while ea < seg.end_ea and ea != idc.BADADDR:
        if ida_bytes.is_code(ida_bytes.get_flags(ea)):
            size = idc.get_item_size(ea)
            b = ida_bytes.get_bytes(ea, size) or b""
            total += 1
            i = 0
            pre = []
            while i < len(b) and b[i] in PREFIX:
                pre.append(b[i]); i += 1
            op = b[i:i + 2]
            if not op:
                ea = idc.next_head(ea, seg.end_ea); continue
            key = None
            has66, has67 = 0x66 in pre, 0x67 in pre
            fs_gs = 0x64 in pre or 0x65 in pre
            if op[0] == 0x0F:
                key = "0F %02X" % op[1] if len(op) > 1 else "0F"
                if has66: key = "66 " + key
            elif op[0] in (0x8C, 0x8E) and len(op) > 1 and ((op[1] >> 3) & 7) in (4, 5):
                key = "%02X /%d (FS/GS 段暫存器移動)" % (op[0], (op[1] >> 3) & 7)
            elif has66 or has67 or fs_gs:
                key = ("66 " if has66 else "") + ("67 " if has67 else "") + ("FS/GS " if fs_gs else "") + "%02X" % op[0]
                # 群組 opcode 再依 modrm.reg 拆
                if op[0] in (0x80, 0x81, 0x83, 0xC0, 0xC1, 0xD0, 0xD1, 0xD2, 0xD3, 0xF6, 0xF7, 0xFE, 0xFF, 0xC6, 0xC7, 0x8F) and len(op) > 1:
                    key += "/%d" % ((op[1] >> 3) & 7)
            if key:
                f = forms.setdefault(key, {"n": 0, "ex": []})
                f["n"] += 1
                if len(f["ex"]) < 40:
                    f["ex"].append({"ea": ea, "sel_off": "%04X:%04X" % (seg.sel, ea - (seg.sel << 4)),
                                    "bytes": b.hex(" "), "text": idc.generate_disasm_line(ea, 0)})
        ea = idc.next_head(ea, seg.end_ea)

res = {"segments": segs, "functions": len(list(idautils.Functions())), "code_heads": total,
       "forms": dict(sorted(forms.items(), key=lambda kv: -kv[1]["n"]))}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
ida_pro.qexit(0)
