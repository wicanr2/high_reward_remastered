"""25DC:18AC 的每個呼叫點：傳回值（AX）在後續路徑上有沒有被讀。唯讀。

用法（經 tools/ida.sh）：ida_text2_18ac_ret.py <輸出檔> [目標 段:偏移 ...，預設 25DC:18AC]
做法（文字層，保守）：從呼叫點的下一道指令起做深度優先探索，每條路徑最多 40 道指令；
  - 遇 call 停；遇 retf／retn 記為 propagates（若 AX 尚未被覆寫）；
  - `mov|lea|les|lds|pop ax|al|ah, <來源不含 ax|al|ah>`、`xor ax,ax` ＝ 覆寫，該路徑停；
  - 出現 ax|al|ah 的其他指令，或 cwd／cbw／mul／div 等隱含使用 AX 者 ＝ 疑似使用，立即回報 used；
  - jmp 與條件跳躍都跟進目標（條件跳躍兩邊都走）；間接跳躍或查不到目標記 unknown-jump。
結果分類：used（任一路徑先讀 AX）、propagates（有路徑 AX 未被覆寫就 ret，傳回值轉交給外層呼叫者）、clean（所有路徑都在讀之前覆寫或遇 call，沒有讀也沒有轉交）、unknown-jump、limit（步數用盡仍未判定）。
輸出每個呼叫點一列：呼叫點 所在函式 結果 命中指令。
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


def sel_off(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return "????:%05X" % ea
    return "%04X:%04X" % (seg.sel, ea - (seg.sel << 4))


def ct(ea):
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0).split(";")[0]).strip()


AXRE = re.compile(r"\b(ax|al|ah)\b")
IMPL = ("cwd", "cbw", "mul", "div", "idiv", "xlat", "stosb", "stosw", "sahf", "lahf", "aam", "aad", "out", "in")
MAXD = 40


def explore(site):
    stack = [(idc.next_head(site, idc.BADADDR), 0)]
    seen = set()
    unknown = ""
    limit = False
    propagates = []
    while stack:
        ea, d = stack.pop()
        if ea == idc.BADADDR or ea in seen:
            continue
        seen.add(ea)
        if d >= MAXD:
            limit = True
            continue
        t = ct(ea)
        mn = idc.print_insn_mnem(ea)
        if mn in ("retf", "retn"):
            propagates.append("%s %s" % (sel_off(ea), t))  # AX 未被覆寫就返回：傳回值轉交給呼叫者
            continue
        if mn == "call":
            continue
        m = re.match(r"^(mov|lea|les|lds|pop) (ax|al|ah)\b,?(.*)$", t)
        if m and not AXRE.search(m.group(3)):
            continue
        if t in ("xor ax, ax", "xor al, al"):
            continue
        if AXRE.search(t) or mn in IMPL:
            return "used", "%s %s" % (sel_off(ea), t)
        if mn == "jmp" or mn.startswith("j") or mn.startswith("loop"):
            tg = [x for x in idautils.CodeRefsFrom(ea, False)]
            if not tg:
                unknown = "%s %s" % (sel_off(ea), t)
            for x in tg:
                stack.append((x, d + 1))
            if mn != "jmp":
                stack.append((idc.next_head(ea, idc.BADADDR), d + 1))
            continue
        stack.append((idc.next_head(ea, idc.BADADDR), d + 1))
    if unknown:
        return "unknown-jump", unknown
    if limit:
        return "limit", ""
    if propagates:
        return "propagates", propagates[0]
    return "clean", ""


def main():
    out = open(sys.argv[1], "w", encoding="utf-8")
    specs = sys.argv[2:] or ["25DC:18AC"]
    for spec in specs:
        raw = spec.startswith("raw:")
        s, o = [int(x, 16) for x in spec[4:].split(":")] if raw else [int(x, 16) for x in spec.split(":")]
        tgt = (s << 4) + o
        cnt = {}
        out.write("== 目標 %s\n" % spec)
        if raw:
            # 原始位元組層搜尋遠呼叫 9A off seg（IDA 沒有為 overlay 樁建 xref 時用）
            pat = b"\x9a" + o.to_bytes(2, "little") + s.to_bytes(2, "little")
            cand = []
            for i in range(ida_segment.get_segm_qty()):
                sg = ida_segment.getnseg(i)
                sz = sg.end_ea - sg.start_ea
                if sz <= 0 or sz > 0x40000:
                    continue
                data = ida_bytes.get_bytes(sg.start_ea, sz)
                k = 0
                while data:
                    k = data.find(pat, k)
                    if k < 0:
                        break
                    cand.append(sg.start_ea + k)
                    k += 1
            sites = []
            for ea in sorted(cand):
                if ida_bytes.is_code(ida_bytes.get_flags(ea)):
                    sites.append(ea)
                else:
                    out.write("%s\t-\tnot-code\t\n" % sel_off(ea))
        else:
            sites = sorted(set(x.frm for x in idautils.XrefsTo(tgt, 0) if x.iscode))
        for site in sites:
            f = ida_funcs.get_func(site)
            res, hit = explore(site)
            cnt[res] = cnt.get(res, 0) + 1
            out.write("%s\t%s\t%s\t%s\n" % (sel_off(site), sel_off(f.start_ea) if f else "-", res, hit))
        out.write("== 合計 %d：%s\n" % (sum(cnt.values()), "，".join("%s %d" % kv for kv in sorted(cnt.items()))))
    out.close()


try:
    main()
except Exception:
    with open(sys.argv[1] + ".error", "w", encoding="utf-8") as e:
        e.write(traceback.format_exc())
ida_pro.qexit(0)
