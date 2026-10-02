"""MAIN.EXE 的 overlay 區在 IDA 9.4 內的盤點與普查（單次執行，對同一資料庫的所有查詢合併在這裡）。

前提：IDA 9.4 的 DOS loader 已在預設載入時把 FBOV overlay 建成 stubNNN／ovrNNN 段落。
本腳本不新增段落，只讀取，最後存一份 .i64 供 GUI 開啟。

參數：<輸出目錄> [overlays.json 路徑]
輸出（都在輸出目錄）：
  segments.json          每個段落的類別、選擇子、範圍、函式數、code head 數、未定義 byte 數
  idaovr/ovrNNN.bin      每個 ovr 段落的位元組（給 ovr_extract.py --compare-ida 比對）
  census386.json         386 形式普查，依 resident／stub／ovr 分開計數
  int_census.json        int n 普查，依 resident／stub／ovr 分開；位址為 IDA 選擇子:偏移
  int_context.txt        指定中斷（10h、33h、16h、2Fh、81h、15h、67h）每一處的前 8 道指令
  intwrap.txt            名稱像 int86／intr／geninterrupt 的函式與它們的呼叫點（含 ovr 內）
  ports.txt              ovr 內 in／out 指令與前面最近的 mov dx, imm
  entries_check.json     overlays.json 的每個入口在 IDA 是否為函式起點，以及 stub 入口在資料庫內的位元組
  sample.txt             stub 與 ovr 段落開頭的反組譯
  done.txt               最後寫入，存在即表示腳本跑完
"""
import json
import os
import re
import sys

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import ida_pro
import ida_segment
import ida_ua
import idautils
import idc

ida_auto.auto_wait()
out = sys.argv[1] if len(sys.argv) > 1 else "/work/out/all"
ovj = sys.argv[2] if len(sys.argv) > 2 else "/data/overlays.json"
os.makedirs(out + "/idaovr", exist_ok=True)


def seg_class(name):
    if name.startswith("ovr"):
        return "ovr"
    if name.startswith("stub"):
        return "stub"
    return "resident"


SEGS = []
for s in idautils.Segments():
    seg = ida_segment.getseg(s)
    SEGS.append((seg.start_ea, seg.end_ea, ida_segment.get_segm_name(seg), seg.sel))


def where(ea):
    seg = ida_segment.getseg(ea)
    if not seg:
        return ("?", 0, "?")
    nm = ida_segment.get_segm_name(seg)
    return (nm, seg.sel, seg_class(nm))


def addr(ea):
    nm, sel, _ = where(ea)
    return "%04X:%04X" % (sel, ea - (sel << 4))


def text(ea):
    return re.sub(r"\s+", " ", idc.generate_disasm_line(ea, 0).split(";")[0].strip())


# ---------- 段落盤點 ----------
segs = []
for (st, en, nm, sel) in SEGS:
    nf = sum(1 for _ in idautils.Functions(st, en))
    heads = undef = 0
    ea = st
    while ea < en:
        fl = ida_bytes.get_flags(ea)
        if ida_bytes.is_code(fl):
            heads += 1
            ea += max(1, idc.get_item_size(ea))
        elif ida_bytes.is_unknown(fl):
            undef += 1
            ea += 1
        else:
            ea += max(1, idc.get_item_size(ea))
    segs.append({"name": nm, "class": seg_class(nm), "sel": sel, "start": st, "end": en,
                 "funcs": nf, "code_heads": heads, "undef_bytes": undef})
    if nm.startswith("ovr"):
        with open(f"{out}/idaovr/{nm}.bin", "wb") as f:
            f.write(ida_bytes.get_bytes(st, en - st) or b"")
tot = {}
for s in segs:
    t = tot.setdefault(s["class"], {"segments": 0, "bytes": 0, "funcs": 0, "code_heads": 0, "undef_bytes": 0})
    t["segments"] += 1
    t["bytes"] += s["end"] - s["start"]
    for k in ("funcs", "code_heads", "undef_bytes"):
        t[k] += s[k]
json.dump({"functions_total": len(list(idautils.Functions())), "by_class": tot, "segments": segs},
          open(out + "/segments.json", "w", encoding="utf-8"), indent=1)

# ---------- 386 形式普查（邏輯同 tools/ida_census_386.py，加上分類） ----------
PREFIX = {0x66, 0x67, 0xF2, 0xF3, 0x2E, 0x36, 0x3E, 0x26, 0x64, 0x65, 0xF0}
GROUP = (0x80, 0x81, 0x83, 0xC0, 0xC1, 0xD0, 0xD1, 0xD2, 0xD3, 0xF6, 0xF7, 0xFE, 0xFF, 0xC6, 0xC7, 0x8F)
c386 = {"resident": {}, "stub": {}, "ovr": {}}
heads_by = {"resident": 0, "stub": 0, "ovr": 0}
for (st, en, nm, sel) in SEGS:
    cl = seg_class(nm)
    ea = st
    while ea < en and ea != idc.BADADDR:
        if ida_bytes.is_code(ida_bytes.get_flags(ea)):
            size = idc.get_item_size(ea)
            b = ida_bytes.get_bytes(ea, size) or b""
            heads_by[cl] += 1
            i = 0
            pre = []
            while i < len(b) and b[i] in PREFIX:
                pre.append(b[i])
                i += 1
            op = b[i:i + 2]
            key = None
            if op:
                has66, has67 = 0x66 in pre, 0x67 in pre
                fs_gs = 0x64 in pre or 0x65 in pre
                if op[0] == 0x0F:
                    key = "0F %02X" % op[1] if len(op) > 1 else "0F"
                    if has66:
                        key = "66 " + key
                elif has66 or has67 or fs_gs:
                    key = ("66 " if has66 else "") + ("67 " if has67 else "") + ("FS/GS " if fs_gs else "") + "%02X" % op[0]
                    if op[0] in GROUP and len(op) > 1:
                        key += "/%d" % ((op[1] >> 3) & 7)
            if key:
                f = c386[cl].setdefault(key, {"n": 0, "ex": []})
                f["n"] += 1
                if len(f["ex"]) < 8:
                    f["ex"].append({"at": addr(ea), "seg": nm, "bytes": b.hex(" "), "text": text(ea)})
        ea = idc.next_head(ea, en)
json.dump({"code_heads": heads_by, "forms": {k: dict(sorted(v.items(), key=lambda kv: -kv[1]["n"])) for k, v in c386.items()}},
          open(out + "/census386.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ---------- int 普查（往前最多 8 道指令找 AH／AX 常數，用運算元型別判讀，不解析字串） ----------


def imm_of(p, reg):
    if idc.print_insn_mnem(p) == "mov" and idc.print_operand(p, 0) == reg and idc.get_operand_type(p, 1) == idc.o_imm:
        return idc.get_operand_value(p, 1) & 0xFFFF
    return None


calls = {"resident": {}, "stub": {}, "ovr": {}}
sites = []
for (st, en, nm, sel) in SEGS:
    cl = seg_class(nm)
    for ea in idautils.Heads(st, en):
        if not ida_bytes.is_code(ida_bytes.get_flags(ea)) or idc.get_wide_byte(ea) != 0xCD:
            continue
        n = idc.get_wide_byte(ea + 1)
        ah = al = ax = None
        trail = []
        p = ea
        for _ in range(8):
            p = idc.prev_head(p, st)
            if p == idc.BADADDR:
                break
            t = text(p)
            trail.append("%s  %s" % (addr(p), t))
            mn = idc.print_insn_mnem(p)
            v = imm_of(p, "ax")
            if v is not None and ax is None and ah is None:
                ax = v
                break
            v = imm_of(p, "ah")
            if v is not None and ah is None:
                ah = v
            v = imm_of(p, "al")
            if v is not None and al is None:
                al = v
            if mn == "xor" and idc.print_operand(p, 0) == "ah" and idc.print_operand(p, 1) == "ah" and ah is None:
                ah = 0
            if mn == "xor" and idc.print_operand(p, 0) == "ax" and idc.print_operand(p, 1) == "ax" and ax is None and ah is None:
                ax = 0
                break
            if mn in ("retn", "retf", "jmp", "call", "iret"):
                break
        if ax is not None:
            key = "int %02Xh AX=%04X" % (n, ax)
        elif ah is not None:
            key = "int %02Xh AH=%02X" % (n, ah) + (" AL=%02X" % al if al is not None else "")
        else:
            key = "int %02Xh (AH 未解)" % n
        e = calls[cl].setdefault(key, {"n": 0, "ex": []})
        e["n"] += 1
        if len(e["ex"]) < 8:
            e["ex"].append(addr(ea))
        sites.append((n, cl, nm, addr(ea), key, list(reversed(trail)), text(ea)))
json.dump({"calls": {k: dict(sorted(v.items())) for k, v in calls.items()},
           "totals": {k: sum(x["n"] for x in v.values()) for k, v in calls.items()}},
          open(out + "/int_census.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
with open(out + "/int_context.txt", "w", encoding="utf-8") as fh:
    for want in (0x10, 0x33, 0x16, 0x2F, 0x81, 0x15, 0x67):
        hit = [s for s in sites if s[0] == want]
        fh.write("== int %02Xh：%d 處（resident %d、ovr %d、stub %d）\n" % (
            want, len(hit), sum(1 for s in hit if s[1] == "resident"), sum(1 for s in hit if s[1] == "ovr"),
            sum(1 for s in hit if s[1] == "stub")))
        for (n, cl, nm, at, key, trail, t) in hit:
            fh.write("-- %s [%s %s] %s\n" % (at, cl, nm, key))
            for line in trail:
                fh.write("     %s\n" % line)
            fh.write("  => %s  %s\n" % (at, t))

# ---------- 軟體中斷包裝函式與呼叫點 ----------
WRAP = re.compile(r"int86|intr|intdos|geninterrupt|bioskey|biosequip|_bios", re.I)
with open(out + "/intwrap.txt", "w", encoding="utf-8") as fh:
    for f in idautils.Functions():
        name = idc.get_func_name(f)
        if not WRAP.search(name or ""):
            continue
        xs = list(idautils.CodeRefsTo(f, 0))
        fh.write("== %s %s（%s）呼叫點 %d\n" % (addr(f), name, where(f)[0], len(xs)))
        for x in xs:
            cl = where(x)[2]
            pre = []
            p = x
            for _ in range(6):
                p = idc.prev_head(p, 0)
                if p == idc.BADADDR:
                    break
                pre.append(text(p))
            fh.write("   %s [%s] 前 6 道（近到遠）：%s\n" % (addr(x), cl, " | ".join(pre)))

# ---------- ovr 內的 I/O 埠 ----------
with open(out + "/ports.txt", "w", encoding="utf-8") as fh:
    cnt = {}
    for (st, en, nm, sel) in SEGS:
        if seg_class(nm) != "ovr":
            continue
        for ea in idautils.Heads(st, en):
            if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
                continue
            mn = idc.print_insn_mnem(ea)
            if mn not in ("in", "out", "ins", "outs", "insb", "outsb", "insw", "outsw"):
                continue
            port = None
            if idc.get_operand_type(ea, 0 if mn == "out" else 1) == idc.o_imm:
                port = idc.get_operand_value(ea, 0 if mn == "out" else 1)
            else:
                p = ea
                for _ in range(6):
                    p = idc.prev_head(p, st)
                    if p == idc.BADADDR:
                        break
                    if idc.print_insn_mnem(p) == "mov" and idc.print_operand(p, 0) == "dx" and idc.get_operand_type(p, 1) == idc.o_imm:
                        port = idc.get_operand_value(p, 1)
                        break
            k = "%s %s" % (mn, "%04Xh" % port if port is not None else "dx(未解)")
            cnt[k] = cnt.get(k, 0) + 1
            fh.write("%s [%s] %s\n" % (addr(ea), nm, text(ea)))
    fh.write("== 統計\n")
    for k, v in sorted(cnt.items()):
        fh.write("%5d %s\n" % (v, k))

# ---------- 入口檢查 ----------
chk = {"entries": 0, "func_start": 0, "not_func_start": [], "stub_db_bytes": {}, "far_calls_to_stub_entries": 0}
if os.path.exists(ovj):
    d = json.load(open(ovj, encoding="utf-8"))
    for o in d["overlays"]:
        ls = int(o["load_seg"], 16)
        ss = int(o["stub_seg"], 16)
        for (i, soff, coff) in o["entries"]:
            chk["entries"] += 1
            ea = (ls << 4) + int(coff, 16)
            f = ida_funcs.get_func(ea)
            if f and f.start_ea == ea:
                chk["func_start"] += 1
            else:
                chk["not_func_start"].append("%s#%d %04X:%s" % (o["name"], i, ls, coff))
            sea = (ss << 4) + int(soff, 16)
            k = "%02X" % idc.get_wide_byte(sea)
            chk["stub_db_bytes"][k] = chk["stub_db_bytes"].get(k, 0) + 1
            for x in idautils.CodeRefsTo(sea, 0):
                if idc.get_wide_byte(x) == 0x9A:
                    chk["far_calls_to_stub_entries"] += 1
                    cl = where(x)[2]
                    own = where(x)[0] == o["name"]
                    k = cl + ("（呼叫自己的 stub）" if own else "")
                    chk.setdefault("far_calls_by_caller_class", {})
                    chk["far_calls_by_caller_class"][k] = chk["far_calls_by_caller_class"].get(k, 0) + 1
                else:
                    k = "%s 非 9A：%s" % (where(x)[2], idc.print_insn_mnem(x))
                    chk.setdefault("other_code_refs", {})
                    chk["other_code_refs"][k] = chk["other_code_refs"].get(k, 0) + 1
    # 對 offset 0 不是入口的段，看 offset 0 是否有函式
    zero = []
    for o in d["overlays"]:
        if o["code_size"] == 0:
            continue
        if not any(int(c, 16) == 0 for (_, _, c) in o["entries"]):
            ea = int(o["load_seg"], 16) << 4
            f = ida_funcs.get_func(ea)
            zero.append({"name": o["name"], "func_at_0": bool(f and f.start_ea == ea)})
    chk["offset0_not_entry"] = zero
# 「90 0E E8」（nop／push cs／call near）在 ovr 段落中：原始位元組次數與 IDA 解成三道指令的次数
raw_n = insn_n = 0
for (st, en, nm, sel) in SEGS:
    if seg_class(nm) != "ovr":
        continue
    blob = ida_bytes.get_bytes(st, en - st) or b""
    i = 0
    while True:
        i = blob.find(b"\x90\x0e\xe8", i)
        if i < 0:
            break
        raw_n += 1
        ea = st + i
        if all(ida_bytes.is_code(ida_bytes.get_flags(ea + k)) and idc.get_item_head(ea + k) == ea + k for k in (0, 1, 2)) \
                and idc.print_insn_mnem(ea + 2) == "call":
            insn_n += 1
        i += 1
chk["near_conv_90_0E_E8"] = {"raw_bytes": raw_n, "decoded_as_nop_pushcs_call": insn_n}
json.dump(chk, open(out + "/entries_check.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ---------- 範例反組譯 ----------
with open(out + "/sample.txt", "w", encoding="utf-8") as fh:
    for nm in ("stub252", "ovr252", "stub374", "ovr374", "stub390", "ovr390"):
        seg = ida_segment.get_segm_by_name(nm)
        if not seg:
            fh.write("== %s 不存在\n" % nm)
            continue
        fh.write("== %s sel=%04X %X-%X\n" % (nm, seg.sel, seg.start_ea, seg.end_ea))
        ea = seg.start_ea
        for _ in range(24):
            if ea == idc.BADADDR or ea >= seg.end_ea:
                break
            sz = max(1, idc.get_item_size(ea))
            fh.write("%s  %-24s %s\n" % (addr(ea), (ida_bytes.get_bytes(ea, min(sz, 8)) or b"").hex(" "), idc.generate_disasm_line(ea, 0)))
            ea = idc.next_head(ea, seg.end_ea)

ida_loader.save_database(ida_loader.get_path(ida_loader.PATH_TYPE_IDB), 0)
open(out + "/done.txt", "w").write("ok\n")
