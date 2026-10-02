"""統計程式內所有 `int n` 呼叫與前幾道指令中可解出的 AH／AX 常數。

用法（經 tools/ida.sh）：ida_int_census.py <輸出.json>
輸出：每個 (中斷號, AX 或 AH 常數) 的次數與前 6 個位址；解不出常數的呼叫另列前置指令。
只讀 IDA 已反組譯出的指令，不改資料庫。
"""
import json
import re
import sys

import ida_auto
import ida_bytes
import ida_pro
import idautils
import idc

ida_auto.auto_wait()
out_path = sys.argv[1] if len(sys.argv) > 1 else "/work/out/int_census.json"

MOV_AX = re.compile(r"^mov\s+ax,\s*([0-9A-Fa-f]+)h?$")
MOV_AH = re.compile(r"^mov\s+ah,\s*([0-9A-Fa-f]+)h?$")
MOV_AL = re.compile(r"^mov\s+al,\s*([0-9A-Fa-f]+)h?$")
XOR_AH = re.compile(r"^xor\s+ah,\s*ah$")
XOR_AX = re.compile(r"^xor\s+ax,\s*ax$")


def num(s):
    return int(s.rstrip("hH"), 16)


res = {}
unresolved = []
for ea in idautils.Heads():
    if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
        continue
    if idc.get_wide_byte(ea) != 0xCD:
        continue
    n = idc.get_wide_byte(ea + 1)
    ah = al = None
    ax = None
    p = ea
    trail = []
    for _ in range(8):
        p = idc.prev_head(p, 0)
        if p == idc.BADADDR:
            break
        t = idc.generate_disasm_line(p, 0).split(";")[0].strip()
        t = re.sub(r"\s+", " ", t)
        trail.append(t)
        m = MOV_AX.match(t)
        if m and ax is None and ah is None:
            ax = num(m.group(1)); break
        m = MOV_AH.match(t)
        if m and ah is None:
            ah = num(m.group(1))
        m = MOV_AL.match(t)
        if m and al is None:
            al = num(m.group(1))
        if XOR_AH.match(t) and ah is None:
            ah = 0
        if XOR_AX.match(t) and ax is None and ah is None:
            ax = 0; break
        if t.startswith(("retn", "retf", "jmp", "call")):
            break
    if ax is not None:
        key = f"int {n:02X}h AX={ax:04X}"
    elif ah is not None:
        key = f"int {n:02X}h AH={ah:02X}" + (f" AL={al:02X}" if al is not None else "")
    else:
        key = f"int {n:02X}h (AH 未解)"
        if len(unresolved) < 200:
            unresolved.append({"ea": "%X" % ea, "trail": list(reversed(trail))})
    e = res.setdefault(key, {"n": 0, "ex": []})
    e["n"] += 1
    if len(e["ex"]) < 6:
        e["ex"].append("%04X:%04X" % ((ea >> 4) & 0xFFFF if False else (ea - (ea & 0xF)) >> 4 & 0xFFFF, ea & 0xF))

json.dump({"calls": dict(sorted(res.items())), "unresolved_sample": unresolved[:60]}, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
ida_pro.qexit(0)
