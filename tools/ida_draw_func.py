"""依種子位址輸出所在函式的反組譯、near/far 判定與呼叫者（xref）。

用法（經 tools/ida.sh）：ida_draw_func.py <輸出檔> <選項>... <段:偏移>...
  段:偏移 是 IDA 選擇子（十六進位）；dosgolem 執行期段 + 0xEF0 = IDA 段（MAIN.EXE 常駐映像）。
  選項 -n：只列函式標頭與 xref，不印反組譯。
唯讀，不改資料庫。輸出檔 utf-8。
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


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return f"????:{ea:05X}"
    return f"{seg.sel:04X}:{ea - (seg.sel << 4):04X}"


def func_kind(f):
    """near/far：看函式內的 ret 指令種類（retn=0xC3/0xC2、retf=0xCB/0xCA）。"""
    near = far = 0
    ea = f.start_ea
    while ea < f.end_ea:
        if ida_bytes.is_code(ida_bytes.get_flags(ea)):
            b = ida_bytes.get_byte(ea)
            if b in (0xC3, 0xC2):
                near += 1
            elif b in (0xCB, 0xCA):
                far += 1
            ea += idc.get_item_size(ea)
        else:
            ea += 1
    return near, far


out_path = sys.argv[1]
args = sys.argv[2:]
brief = "-n" in args
specs = [a for a in args if a != "-n"]
out = open(out_path, "w", encoding="utf-8")
done = set()
for spec in specs:
    seg, off = [int(x, 16) for x in spec.split(":")]
    ea = (seg << 4) + off
    f = ida_funcs.get_func(ea)
    out.write("=" * 78 + "\n")
    out.write(f"種子 {spec.upper()} (linear {ea:#x})\n")
    if not f:
        out.write("  不屬於任何函式\n")
        continue
    if f.start_ea in done:
        out.write(f"  已在前面輸出：函式 {sel_off(f.start_ea)}\n")
        continue
    done.add(f.start_ea)
    near, far = func_kind(f)
    out.write(
        f"函式 {sel_off(f.start_ea)}-{sel_off(f.end_ea)} 大小 {f.end_ea - f.start_ea:#x} "
        f"名稱 {idc.get_func_name(f.start_ea)} retn={near} retf={far} "
        f"FUNC_FAR旗標={bool(f.flags & ida_funcs.FUNC_FAR)}\n"
    )
    out.write("呼叫者（對函式起點的 xref）：\n")
    n = 0
    for x in idautils.XrefsTo(f.start_ea, 0):
        cf = ida_funcs.get_func(x.frm)
        cname = sel_off(cf.start_ea) if cf else "無函式"
        out.write(f"  {sel_off(x.frm)}  type={ida_xref.get_xref_type_name(x.type) if hasattr(ida_xref, 'get_xref_type_name') else x.type}  code={x.iscode}  所在函式 {cname}\n")
        n += 1
    out.write(f"  共 {n} 筆\n")
    if brief:
        continue
    out.write("反組譯：\n")
    p = f.start_ea
    while p < f.end_ea:
        if ida_bytes.is_code(ida_bytes.get_flags(p)):
            sz = idc.get_item_size(p)
            b = (ida_bytes.get_bytes(p, sz) or b"").hex(" ")
            out.write(f"{sel_off(p)}  {b:24} {idc.generate_disasm_line(p, 0)}\n")
            p += sz
        else:
            out.write(f"{sel_off(p)}  {ida_bytes.get_byte(p):02x}                       db\n")
            p += 1
out.close()
ida_pro.qexit(0)
