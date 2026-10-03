"""由指定函式往上走呼叫者（含 overlay 樁的資料參考），輸出呼叫樹。唯讀。

用法（經 tools/ida.sh）：ida_text2_updown.py <輸出檔> <深度> <段:偏移>...
每個節點一列：縮排 ＋ 函式位址 ＋ [段名/類別] ＋ 直接呼叫者數 ＋ 標記（函式內是否呼叫文字載入或顯示函式）。
IDA 對 overlay 的樁（stub）有的有 code xref，有的只有 data xref（dd），兩者都走。
單一節點最多展開 14 個呼叫者，總節點上限 600。
"""
import re
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

MARKS = {
    "24B2:0111": "MES取字",
    "24B2:0030": "MES取字+vsprintf",
    "237B:0464": "ESPMES取字",
    "237B:01A3": "對話框A",
    "237B:06CF": "對話框B",
    "237B:07FE": "對話框C",
    "25DC:18AC": "文字物件顯示",
    "25DC:1676": "一行折行",
    "25DC:15E7": "一行不折",
    "25DC:0180": "建文字物件",
}


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return "????:%05X" % ea
    return "%04X:%04X" % (seg.sel, ea - (seg.sel << 4))


def lin(spec):
    s, o = [int(x, 16) for x in spec.split(":")]
    return (s << 4) + o


MARK_EA = {lin(k): v for k, v in MARKS.items()}


def func_start(ea):
    f = ida_funcs.get_func(ea)
    return f.start_ea if f else ea


def marks_in(fstart):
    f = ida_funcs.get_func(fstart)
    if not f:
        return ""
    got = set()
    for h in idautils.FuncItems(fstart):
        for x in idautils.XrefsFrom(h, 0):
            if x.iscode and x.to in MARK_EA:
                got.add(MARK_EA[x.to])
    return ",".join(sorted(got))


def callers(fstart):
    res = {}
    for x in idautils.XrefsTo(fstart, 0):
        key = func_start(x.frm)
        res.setdefault(key, set()).add((x.frm, "code" if x.iscode else "data"))
    return res


def main():
    out = open(sys.argv[1], "w", encoding="utf-8")
    depth = int(sys.argv[2])
    count = [0]

    def walk(f, d, path, indent):
        count[0] += 1
        if count[0] > 600:
            return
        seg = ida_segment.getseg(f)
        cs = callers(f)
        nm = idc.get_name(f)
        out.write("%s%s  [%s/%s] 呼叫者%d %s %s\n" % (
            "  " * indent, sel_off(f), ida_segment.get_segm_name(seg) if seg else "?",
            ida_segment.get_segm_class(seg) if seg else "?", len(cs), marks_in(f),
            ("" if nm.startswith("sub_") else nm)))
        if d == 0:
            return
        n = 0
        for c in sorted(cs):
            if c in path or c == f:
                continue
            n += 1
            if n > 14:
                out.write("%s...（其餘 %d 個略）\n" % ("  " * (indent + 1), len(cs) - 14))
                break
            kinds = ",".join(sorted(set(k for _, k in cs[c])))
            out.write("%s<- %s via %s\n" % ("  " * (indent + 1), sel_off(sorted(cs[c])[0][0]), kinds))
            walk(c, d - 1, path | {f}, indent + 1)

    for spec in sys.argv[3:]:
        out.write("== 起點 %s\n" % spec)
        walk(lin(spec), depth, set(), 0)
    out.write("== done\n")
    out.close()


try:
    main()
except Exception:
    with open(sys.argv[1] + ".error", "w", encoding="utf-8") as e:
        e.write(traceback.format_exc())
ida_pro.qexit(0)
