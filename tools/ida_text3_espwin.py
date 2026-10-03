"""M10 證據探針（第三輪）：ESPMES 外層 id 換算、窗口類別表、`%` 普查、SHOPTAB 與外層表核對。

輸出只有位址、位元組、計數與 id，不含任何原文。

用法（經 tools/ida.sh，資料檔在 <HR_IDA_WORK>/run/data/，容器內 /work/data；espmap.txt 是 023 的輸出複本）：
  ida_text3_espwin.py <輸出前綴>
輸出：
  <前綴>-switch.txt        237B:0464 的 switch 解碼（位元組、檔案位移、id 到群組索引、邊界檢查）
  <前綴>-esp.txt           ESPMES 外層與內層結構、630 個呼叫點的統計（算式）
  <前綴>-esp-windows.tsv   1024 個項目：id、類別（只有兩欄）
  <前綴>-esp-detail.tsv    同上加 外層 id、呼叫點數、顯示函式組合、函式位址
  <前綴>-pct.txt           各檔含 % 的項目數、轉換規格個數、指定項目的 % 位置
  <前綴>-pct-items.tsv     每個含 % 的項目：id、0x25 個數、轉換規格（只有型別字母）、位置
  <前綴>-shoptab.txt       SHOPTAB.TBL 的 792 個欄位核對
"""
import collections
import hashlib
import re
import struct
import sys
import traceback

import ida_auto
import ida_bytes
import ida_pro
import idc

ida_auto.auto_wait()
PFX = sys.argv[1]
D = "/work/data/"


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def lin(seg, off):
    return (seg << 4) + off


def sha(b):
    return hashlib.sha256(b).hexdigest()


def foff(ea):
    try:
        v = idc.get_fileregion_offset(ea)
        return v
    except Exception:
        return -1


def fo_s(ea):
    v = foff(ea)
    return "%#x" % v if isinstance(v, int) and v >= 0 else "n/a（IDA 無檔案對應，由主機 grep 定位）"


# ---------------------------------------------------------------- 1. switch
def do_switch(out):
    w = out.write
    w("# 237B:0464 switch 解碼（IDA 資料庫位元組；檔案位移由 IDA 的 get_fileregion_offset 給出，主機另以 xxd 複核）\n")
    base_ea = lin(0x237B, 0x482)
    code = ida_bytes.get_bytes(base_ea, 16)
    w("237B:0482..0491 bytes: %s  file_off=%s\n" % (code.hex(" "), fo_s(base_ea)))
    ok = (code[0:2] == b"\x81\xeb" and code[4:6] == b"\x83\xfb" and code[7] == 0x77
          and code[9:11] == b"\x03\xdb" and code[11:14] == b"\x2e\xff\xa7")
    w("格式符合 `sub bx,imm16; cmp bx,imm8; ja rel8; add bx,bx; jmp cs:[bx+jpt]`：%s\n" % ok)
    if not ok:
        return None
    sub = u16(code, 2)
    maxcase = code[6]
    rel = code[8]
    default = 0x48B + rel
    jpt = u16(code, 14)
    n = maxcase + 1
    w("sub bx,%#x（%d）；cmp bx,%#x → 有效 case 數 %d（id %d 至 %d）；ja 目標 237B:%04X（預設）；跳表 237B:%04X\n"
      % (sub, sub, maxcase, n, sub, sub + maxcase, default, jpt))
    jea = lin(0x237B, jpt)
    jbytes = ida_bytes.get_bytes(jea, 2 * n)
    w("跳表 237B:%04X..%04X bytes: %s  file_off=%s\n" % (jpt, jpt + 2 * n - 1, jbytes.hex(" "), fo_s(jea)))
    # 進入點前導
    pea = lin(0x237B, 0x472)
    w("237B:0472 bytes: %s  (mov si,[bp+6] 即 si = 外層 id)\n" % ida_bytes.get_bytes(pea, 3).hex(" "))
    mapping = {}
    w("\n# id → 目標 → si（外層 id → 群組索引）\n")
    w("id\ttarget\ttarget_bytes\tsi\tgroup\n")
    for i in range(n):
        t = u16(jbytes, 2 * i)
        tb = ida_bytes.get_bytes(lin(0x237B, t), 5)
        if t == default:
            si = None
            desc = "預設（si 保持為 id）"
        elif tb[0] == 0xBE and tb[3] == 0xEB and (t + 5 + tb[4]) & 0xFFFF == default:
            si = u16(tb, 1)
            desc = "mov si,%#x; jmp 預設" % si
        elif tb[0] == 0xBE and t + 3 == default:
            si = u16(tb, 1)
            desc = "mov si,%#x; 直接落入預設（緊鄰）" % si
        else:
            si = None
            desc = "非預期格式"
        gid = sub + i
        grp = gid if si is None else si
        mapping[gid] = grp
        w("%d\t237B:%04X\t%s\t%s\t%d\n" % (gid, t, tb.hex(" "), desc, grp))
    # 預設路徑與邊界檢查
    dea = lin(0x237B, default)
    w("\n預設目標 237B:%04X bytes: %s（push ds; push offset \"ESPMES.MRG\"; call 2B14:0000 開檔）\n"
      % (default, ida_bytes.get_bytes(dea, 9).hex(" ")))
    bea = lin(0x237B, 0x4FE)
    bb = ida_bytes.get_bytes(bea, 5)
    w("邊界檢查 237B:04FE bytes: %s file_off=%s（3b 76 fe ＝ cmp si,[bp-2]（N）；76 12 ＝ jbe：無號 si <= N 通過）\n"
      % (bb.hex(" "), fo_s(bea)))
    cea = lin(0x237B, 0x557)
    cb = ida_bytes.get_bytes(cea, 8)
    w("子 id 邊界檢查 237B:0557 bytes: %s（8b 46 08 ＝ mov ax,[bp+8]（子 id）；3b 46 fc ＝ cmp ax,[bp-4]（N2）；76 12 ＝ jbe）\n" % cb.hex(" "))
    w("\n# 換算函式（由上表與 ja 預設推得）\n")
    w("  si = id            （id < %d 或 id > %d，或 id 在跳表指向預設的格：%s）\n"
      % (sub, sub + maxcase, ",".join(str(k) for k, v in sorted(mapping.items()) if v == k)))
    w("  si = 表值          （其餘格：%s）\n" % ", ".join("%d→%d" % (k, v) for k, v in sorted(mapping.items()) if v != k))
    w("  之後 si <= N 才讀，否則關檔並回傳空字串 4028:0081（開頭 237B:047A 已寫 0）\n")
    return mapping


def group_of(mapping, gid):
    return mapping.get(gid, gid)


# ---------------------------------------------------------------- 2. ESPMES
def parse_esp(esp):
    N = u16(esp, 0)
    first = u32(esp, 2)
    n_off = (first - 2) // 4
    offs = [u32(esp, 2 + 4 * i) for i in range(n_off)]
    info = {"N": N, "n_off": n_off, "first": first, "table_end": 2 + 4 * n_off, "offs": offs}
    groups = {}
    for g in range(n_off):
        s = offs[g]
        e = offs[g + 1] if g + 1 < n_off else len(esp)
        if s >= e:
            continue
        grp = esp[s:e]
        n2 = u16(grp, 0)
        o2 = [u32(grp, 2 + 4 * i) for i in range(n2)]
        items = []
        for k in range(n2 - 1):
            a, b = o2[k], o2[k + 1]
            raw = grp[a:b]
            items.append({"k": k, "file_off": s + a, "rawlen": b - a, "body": raw.split(b"\0")[0]})
        groups[g] = {"start": s, "end": e, "n2": n2, "o2": o2, "items": items, "len": e - s}
    info["groups"] = groups
    return info


def do_esp(out, esp, mapping):
    w = out.write
    info = parse_esp(esp)
    offs = info["offs"]
    w("# ESPMES.MRG 結構（SHA-256 %s，%d bytes）\n" % (sha(esp), len(esp)))
    w("外層 N（u16@0）= %d；表起點 2；第一個偏移值 %d (%#x)；若表緊接資料，偏移個數 = (第一個偏移 - 2) / 4 = %d；表尾 = 2 + 4 x %d = %d\n"
      % (info["N"], info["first"], info["first"], info["n_off"], info["n_off"], info["table_end"]))
    w("表尾 == 第一個偏移：%s；N - 偏移個數 = %d\n" % (info["table_end"] == info["first"], info["N"] - info["n_off"]))
    # 偏移值的連續相同段
    w("\n# 偏移值的連續相同段（群組索引區間、值、區間長）\n")
    runs = []
    for i, v in enumerate(offs):
        if runs and runs[-1][2] == v:
            runs[-1][1] = i
        else:
            runs.append([i, i, v])
    for a, b, v in runs:
        w("  群組 %d 至 %d：偏移 %d (%#x)，%d 個\n" % (a, b, v, v, b - a + 1))
    # 空群組：start == 下一個 start（最後一個群組的終點是檔尾）
    empty = [g for g in range(info["n_off"]) if g not in info["groups"]]
    nonempty = sorted(info["groups"])
    w("\n空群組（start == 下一個群組的 start）共 %d 個：" % len(empty))
    rng = []
    for g in empty:
        if rng and rng[-1][1] == g - 1:
            rng[-1][1] = g
        else:
            rng.append([g, g])
    w(", ".join("%d-%d" % (a, b) if a != b else "%d" % a for a, b in rng) + "\n")
    w("非空群組 %d 個：%s\n" % (len(nonempty), ", ".join(str(g) for g in nonempty)))
    w("驗證規格第 2 節：群組 45 至 115 的偏移都等於群組 116 的起點 → %s（值 %s）；群組 0 至 43 的偏移都等於群組 44 的起點 → %s（值 %s）\n"
      % (all(offs[g] == offs[116] for g in range(45, 116)), offs[116],
         all(offs[g] == offs[44] for g in range(0, 44)), offs[44]))
    w("群組 44 的起點 %d；群組 45 的起點 %d；群組 116 的起點 %d；群組 117 的起點 %d\n" % (offs[44], offs[45], offs[116], offs[117]))
    # 內層
    w("\n# 非空群組內層：N2、第一個內層偏移（== 2 + 4 x N2 表示表緊接資料）、項目數 = N2 - 1、終止偏移 vs 群組長\n")
    w("group\tstart\tend\tlen\tN2\to2[0]\t2+4*N2\titems\to2[N2-1]\tend-start\n")
    total = 0
    for g in nonempty:
        G = info["groups"][g]
        total += len(G["items"])
        w("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"
          % (g, G["start"], G["end"], G["len"], G["n2"], G["o2"][0], 2 + 4 * G["n2"], len(G["items"]),
             G["o2"][G["n2"] - 1], G["end"] - G["start"]))
    w("項目總數 = %d\n" % total)
    # 檔尾
    w("檔尾位元組：%s\n" % esp[-4:].hex(" "))
    # 載入端邊界：si <= N 通過
    w("\n載入端 237B:04FE `cmp si,N; jbe`（無號）：si = 0..%d 通過，%d 起失敗。群組 %d 至 %d 通過檢查但表只有 %d 個偏移（0..%d）：\n"
      % (info["N"], info["N"] + 1, info["n_off"], info["N"], info["n_off"], info["n_off"] - 1))
    for g in range(info["n_off"], info["N"] + 1):
        pos = 2 + 4 * g
        w("  si=%d：lseek(%d) 讀 8 bytes → %s（落在檔案內：%s）\n"
          % (g, pos, esp[pos:pos + 8].hex(" ") if pos + 8 <= len(esp) else "超出檔尾", pos + 8 <= len(esp)))
    # espmap
    sites = []
    cur = None
    for line in open(D + "espmap.txt", encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("== 目標"):
            cur = line.split()[-1]
            continue
        if line.startswith("==") or not line:
            continue
        if cur != "237B:0464":
            continue
        p = line.split("\t")
        m = re.match(r"^(\d+) \| (\d+)$", p[3])
        if not m:
            w("非立即值呼叫點：%s\n" % line)
            continue
        sites.append({"site": p[1], "func": p[2], "id": int(m.group(1)), "sub": int(m.group(2)),
                      "disp": p[4] if len(p) > 4 else ""})
    w("\n# espmap.txt（023 輸出，SHA-256 %s）：237B:0464 的呼叫點 %d 個，全部為立即值\n"
      % (sha(open(D + "espmap.txt", "rb").read()), len(sites)))
    byid = collections.Counter(s["id"] for s in sites)
    w("各外層 id 呼叫點數與換算後群組：" + "；".join("%d→%d（%d 處）" % (k, group_of(mapping, k), v) for k, v in sorted(byid.items())) + "\n")
    pairs = collections.OrderedDict()
    bad = []
    for s in sites:
        g = group_of(mapping, s["id"])
        key = (g, s["sub"])
        if g not in info["groups"] or s["sub"] >= len(info["groups"][g]["items"]):
            bad.append((s, g))
            continue
        pairs.setdefault(key, []).append(s)
    w("呼叫點 %d；不在任何有效項目的呼叫點 %d；去重後有效 (群組,子) 對 %d；有多個呼叫點的對 %d\n"
      % (len(sites), len(bad), len(pairs), sum(1 for v in pairs.values() if len(v) > 1)))
    for s, g in bad:
        w("  無效：%s id=%d→群組 %d 子 %d\n" % (s["site"], s["id"], g, s["sub"]))
    for k, v in pairs.items():
        if len(v) > 1:
            w("  重複：#%d.%d 於 %s\n" % (k[0], k[1], ", ".join(x["site"] for x in v)))

    def tokens(sl):
        t = set()
        for s in sl:
            for x in s["disp"].split(","):
                if x:
                    t.add(x)
        return t

    # 讀碼覆寫（掃描找不到顯示函式的三項，由反組譯確認；依據見報告 3.3）
    OVERRIDE = {
        (122, 165): ("win29x4", "read:6EE9:252F->_sprintf->62F0:0093(jmp 88A1:1DDC)->25F40(240x64)"),
        (122, 166): ("win29x4", "read:6EE9:2562->_sprintf->62F0:0093(jmp 88A1:1DDC)->25F40(240x64)"),
        (122, 168): ("win31x4", "read:6EE9:2706->_sprintf->237B:0052/01A3(6EE9:286F)"),
    }
    cls = {}
    detail = []
    n_a = n_c = n_unk = n_conf = 0
    n_ov = 0
    for g in nonempty:
        for it in info["groups"][g]["items"]:
            key = (g, it["k"])
            sl = pairs.get(key)
            basis = "scan"
            if not sl:
                c = "none"
                via = "-"
                outer = "-"
                nsite = 0
                funcs = "-"
            else:
                tk = tokens(sl)
                has_c = "dlgC(07FE)" in tk
                has_ab = ("dlgA(01A3)" in tk) or ("dlgB(06CF)" in tk)
                if has_c and has_ab:
                    c = "conflict"
                    n_conf += 1
                elif has_c:
                    c = "win63x8"
                    n_c += 1
                elif has_ab:
                    c = "win31x4"
                    n_a += 1
                else:
                    c = "unknown"
                    n_unk += 1
                via = "+".join(sorted({x[x.index("(") + 1:-1] for x in tk if x.startswith("dlg")})) or "-"
                outer = ",".join(sorted({str(s["id"]) for s in sl}))
                nsite = len(sl)
                funcs = ",".join(sorted({s["func"] for s in sl}))
            scan_cls = c
            if key in OVERRIDE:
                if c != "unknown":
                    raise RuntimeError("覆寫對象不是 unknown：%s" % (key,))
                c, basis = OVERRIDE[key]
                n_ov += 1
            cls[key] = c
            detail.append((g, it["k"], c, outer, nsite, via, funcs, basis, scan_cls))
    w("\n# 類別統計（espmap 的顯示函式標記；win31x4 ＝ 01A3 或 06CF；win63x8 ＝ 07FE；win29x4 ＝ 240x64 的 VS 畫面窗口；unknown ＝ 有呼叫點但掃描沒找到顯示函式；none ＝ 沒有靜態呼叫點）\n")
    w("掃描結果（覆寫前）：win31x4 %d；win63x8 %d；unknown %d；conflict %d；none %d；合計 %d\n"
      % (n_a, n_c, n_unk, n_conf, total - len(pairs), total))
    w("算式：1024 項目 - 有效靜態對 %d = %d 項無靜態呼叫點（none）；有靜態對 %d = win31x4 %d + win63x8 %d + unknown %d + conflict %d\n"
      % (len(pairs), total - len(pairs), len(pairs), n_a, n_c, n_unk, n_conf))
    w("掃描 unknown 的項目：%s\n" % ", ".join("#%d.%d" % k for k in OVERRIDE))
    w("覆寫（讀碼）%d 項；覆寫後各類：%s\n" % (n_ov, ", ".join("%s %d" % kv for kv in sorted(collections.Counter(cls.values()).items()))))
    w("conflict 的項目：%s\n" % ", ".join("#%d.%d" % k for k, c in cls.items() if c == "conflict"))
    # 各群組分布
    w("\n各群組類別分布：\n")
    for g in nonempty:
        cc = collections.Counter(cls[(g, it["k"])] for it in info["groups"][g]["items"])
        w("  群組 %d（%d 項）：%s\n" % (g, len(info["groups"][g]["items"]), ", ".join("%s %d" % kv for kv in sorted(cc.items()))))
    with open(PFX + "-esp-windows.tsv", "w", encoding="utf-8") as f:
        f.write("id\tclass\n")
        for g, k, c, outer, nsite, via, funcs, basis, scan_cls in detail:
            f.write("ESPMES#%d.%d\t%s\n" % (g, k, c))
    with open(PFX + "-esp-detail.tsv", "w", encoding="utf-8") as f:
        f.write("id\tclass\touter_id\tsites\tvia\tfuncs\tbasis\tscan_class\n")
        for g, k, c, outer, nsite, via, funcs, basis, scan_cls in detail:
            f.write("ESPMES#%d.%d\t%s\t%s\t%d\t%s\t%s\t%s\t%s\n" % (g, k, c, outer, nsite, via, funcs, basis, scan_cls))
    return info


# ---------------------------------------------------------------- 3. % 普查
FLAGS = b"-+ #0"
TYPES = b"diouxXeEfgGcsp%n"


def specs(b):
    res = []
    i = 0
    while i < len(b):
        if b[i] != 0x25:
            i += 1
            continue
        j = i + 1
        while j < len(b) and b[j] in FLAGS:
            j += 1
        while j < len(b) and (0x30 <= b[j] <= 0x39 or b[j] == 0x2A):
            j += 1
        if j < len(b) and b[j] == 0x2E:
            j += 1
            while j < len(b) and (0x30 <= b[j] <= 0x39 or b[j] == 0x2A):
                j += 1
        while j < len(b) and b[j] in b"hlLNF":
            j += 1
        if j < len(b) and b[j] in TYPES:
            res.append((i, "%" + b[i + 1:j + 1].decode("ascii"), j))
            i = j + 1
        else:
            res.append((i, "%?", i))
            i += 1
    return res


def parse_mes(d):
    k = u16(d, 0)
    offs = [u32(d, 2 + 4 * i) for i in range(k)]
    items = []
    for i in range(k - 1):
        a, b = offs[i], offs[i + 1]
        raw = d[a:b]
        items.append((i, a, len(raw), raw.split(b"\0")[0]))
    return items


def do_pct(out, tsv, esp, info, mapping):
    w = out.write
    w("# `%` 普查（只有計數、型別字母與位置）\n")
    allitems = []  # (id, file, file_off, rawlen, body)
    for name in ("COUNTRY.MES", "SP.MES", "SYSTEM.MES", "UWASA.MES", "POWERMES.MES"):
        d = open(D + name, "rb").read()
        for i, a, rl, body in parse_mes(d):
            allitems.append(("%s#%d" % (name, i), name, a, rl, body))
    for g in sorted(info["groups"]):
        for it in info["groups"][g]["items"]:
            allitems.append(("ESPMES#%d.%d" % (g, it["k"]), "ESPMES.MRG", it["file_off"], it["rawlen"], it["body"]))
    w("項目總數 %d\n" % len(allitems))
    tsv.write("id\tn25\tspecs\tpositions\tpct_s_before_0A_or_end\n")
    perfile = collections.OrderedDict()
    pct_s_nl = collections.Counter()
    pct_s_end = collections.Counter()
    pct_s_tot = collections.Counter()
    for iid, fn, fo, rl, body in allitems:
        sp = specs(body)
        n25 = body.count(b"\x25")
        st = perfile.setdefault(fn, {"items": 0, "with_pct": 0, "n25": 0, "types": collections.Counter()})
        st["items"] += 1
        if n25:
            st["with_pct"] += 1
            st["n25"] += n25
            for _, s, _ in sp:
                st["types"][s] += 1
            nl = 0
            for pos, s, j in sp:
                if s == "%s":
                    pct_s_tot[fn] += 1
                    nxt = body[j + 1:j + 2]
                    if nxt == b"\n":
                        nl += 1
                        pct_s_nl[fn] += 1
                    elif nxt == b"":
                        nl += 1
                        pct_s_end[fn] += 1
            tsv.write("%s\t%d\t%s\t%s\t%d\n" % (iid, n25, ",".join(s for _, s, _ in sp),
                                                 ",".join(str(p) for p, _, _ in sp), nl))
    for fn, st in perfile.items():
        w("%-14s 項目 %4d；含 0x25 的項目 %3d；0x25 總數 %3d；轉換規格：%s；%%s 共 %d 處，其中直接接 0A %d 處、緊接項目結尾 %d 處\n"
          % (fn, st["items"], st["with_pct"], st["n25"],
             ", ".join("%s x%d" % kv for kv in sorted(st["types"].items())) or "無",
             pct_s_tot[fn], pct_s_nl[fn], pct_s_end[fn]))
    return {i[0]: i for i in allitems}


def report_items(out, itemmap, keys):
    w = out.write
    w("\n# 指定項目\n")
    w("id\tfile_off\trawlen\tn25\tspecs（型別，含位置）\n")
    for k in keys:
        it = itemmap.get(k)
        if not it:
            w("%s\t（不存在）\n" % k)
            continue
        iid, fn, fo, rl, body = it
        sp = specs(body)
        w("%s\t%#x\t%d\t%d\t%s\n" % (iid, fo, rl, body.count(b"\x25"),
                                    ", ".join("%s@%d" % (s, p) for p, s, _ in sp) or "無"))


# ---------------------------------------------------------------- 4. SHOPTAB
def do_shoptab(out):
    w = out.write
    sh = open(D + "SHOPTAB.TBL", "rb").read()
    w("# SHOPTAB.TBL（SHA-256 %s，%d bytes）\n" % (sha(sh), len(sh)))
    nrec = len(sh) // 200
    w("長度 %d = %d x 200（餘 %d）；每筆 8 個 25-byte 欄位 → %d 欄\n" % (len(sh), nrec, len(sh) % 200, nrec * 8))
    fields = [sh[i * 25:(i + 1) * 25] for i in range(len(sh) // 25)]
    c20 = collections.Counter(f[20] for f in fields)
    w("每欄第 21 個位元組（索引 20）的分布：%s\n" % ", ".join("%02x x%d" % kv for kv in sorted(c20.items())))
    c19 = collections.Counter(f[19] for f in fields)
    w("每欄第 20 個位元組（索引 19，名稱最後一格）的分布：%s\n" % ", ".join("%02x x%d" % kv for kv in sorted(c19.items())))
    tails = collections.Counter(f[21:25] for f in fields)
    w("索引 21 至 24（其餘 4 bytes）不同樣式 %d 種；最多的 5 種：%s\n"
      % (len(tails), "; ".join("%s x%d" % (k.hex(" "), v) for k, v in tails.most_common(5))))
    blank = [f for f in fields if f[:20] == b"\x20" * 20]
    w("名稱 20 bytes 全為 0x20 的欄 %d 個；其中索引 20 為 00 的 %d 個\n" % (len(blank), sum(1 for f in blank if f[20] == 0)))
    # 名稱內是否出現 0x00
    w("名稱 20 bytes 內含 0x00 的欄 %d 個\n" % sum(1 for f in fields if 0 in f[:20]))
    # 每筆第 1 欄、第 8 欄的位置（確認欄位對齊）
    w("對齊檢查：每筆記錄 8 欄的索引 20 位元組全為 00：%s\n"
      % all(all(sh[r * 200 + c * 25 + 20] == 0 for c in range(8)) for r in range(nrec)))


def main():
    sw = open(PFX + "-switch.txt", "w", encoding="utf-8")
    mapping = do_switch(sw)
    sw.close()
    if mapping is None:
        raise RuntimeError("switch 格式不符")
    esp = open(D + "ESPMES.MRG", "rb").read()
    eo = open(PFX + "-esp.txt", "w", encoding="utf-8")
    info = do_esp(eo, esp, mapping)
    eo.close()
    po = open(PFX + "-pct.txt", "w", encoding="utf-8")
    tsv = open(PFX + "-pct-items.tsv", "w", encoding="utf-8")
    itemmap = do_pct(po, tsv, esp, info, mapping)
    tsv.close()
    report_items(po, itemmap, ["ESPMES#121.0", "ESPMES#121.1", "SP.MES#56", "ESPMES#122.165", "ESPMES#122.166",
                               "ESPMES#122.168", "ESPMES#120.70", "ESPMES#44.1"])
    po.close()
    so = open(PFX + "-shoptab.txt", "w", encoding="utf-8")
    do_shoptab(so)
    so.close()


try:
    main()
except Exception:
    with open(PFX + ".error", "w", encoding="utf-8") as e:
        e.write(traceback.format_exc())
ida_pro.qexit(0)
