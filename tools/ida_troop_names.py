"""匯出部隊名稱表、交叉參照及直接使用者，保留 IDA 原始定位。"""
import json
import sys
import traceback

import ida_auto
import ida_bytes
import ida_funcs
import ida_pro
import ida_segment
import idautils
import idc

ida_auto.auto_wait()


def loc(ea):
    s = ida_segment.getseg(ea)
    return "%04X:%04X" % (s.sel, ea - (s.sel << 4)) if s else hex(ea)


def function(ea):
    f = ida_funcs.get_func(ea)
    if not f:
        return None
    return {
        "name": idc.get_func_name(f.start_ea),
        "start": loc(f.start_ea),
        "instructions": [
            {"address": loc(a), "bytes": (ida_bytes.get_bytes(a, idc.get_item_size(a)) or b"").hex(),
             "asm": idc.generate_disasm_line(a, 0)}
            for a in idautils.FuncItems(f.start_ea)
        ],
    }


result = {"tool": "IDA " + ida_pro.IDA_SDK_VERSION.__str__(), "address_space": "IDA selector:offset and linear"}
try:
    rows, funcs = [], {}
    ranges = [(0x5F36, 0x3FB, 0x41F), (0x5ACF, 0xC70, 0xCC0), (0x5E43, 0, 0xC0)]
    for seg, start, end in ranges:
        for off in range(start, end):
            ea = seg * 16 + off
            xs = list(idautils.XrefsTo(ea))
            if xs:
                rows.append({"address": loc(ea), "linear": hex(ea),
                             "bytes": (ida_bytes.get_bytes(ea, 24) or b"").hex(),
                             "xrefs": [{"from": loc(x.frm), "type": x.type, "code": bool(x.iscode)} for x in xs]})
                for x in xs:
                    f = function(x.frm)
                    if f:
                        funcs[f["start"]] = f
                    else:
                        for y in idautils.XrefsTo(x.frm):
                            f = function(y.frm)
                            if f:
                                funcs[f["start"]] = f
    for query in sys.argv[2:]:
        seg, off = (int(v, 16) for v in query.split(":"))
        f = function(seg * 16 + off)
        if f:
            funcs[f["start"]] = f
    result.update(function_count=len(list(idautils.Functions())), references=rows, functions=list(funcs.values()))
except Exception:
    result["error"] = traceback.format_exc()
with open(sys.argv[1], "w", encoding="utf-8") as out:
    json.dump(result, out, ensure_ascii=False, indent=2)
ida_pro.qexit(0)
