"""依範圍輸出反組譯文字。參數：<輸出檔> <段:偏移:長度>...（十六進位，段為 IDA 選擇子）。

IDA 選擇子與 dosgolem 執行期段值的換算（MAIN.EXE，載入段 0x110）：IDA = 執行期 + 0xEF0。
"""
import sys

import ida_auto
import ida_bytes
import ida_pro
import idc

ida_auto.auto_wait()
out = open(sys.argv[1], "w", encoding="utf-8")
for spec in sys.argv[2:]:
    seg, off, ln = [int(x, 16) for x in spec.split(":")]
    ea = (seg << 4) + off
    end = ea + ln
    out.write(f"== {seg:04X}:{off:04X} len {ln:#x} (linear {ea:#x})\n")
    while ea < end:
        if ida_bytes.is_code(ida_bytes.get_flags(ea)):
            n = idc.get_item_size(ea)
            b = (ida_bytes.get_bytes(ea, n) or b"").hex(" ")
            name = idc.get_name(ea) or ""
            out.write(f"{seg:04X}:{ea - (seg << 4):04X}  {b:24} {idc.generate_disasm_line(ea, 0)}\n")
            ea += n
        else:
            out.write(f"{seg:04X}:{ea - (seg << 4):04X}  {ida_bytes.get_byte(ea):02x}                       db (非 code)\n")
            ea += 1
out.close()
ida_pro.qexit(0)
