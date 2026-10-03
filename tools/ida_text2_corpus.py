"""M10 證據探針（第二輪）：以 25DC:1676 的指令級模擬掃描原版文字，輸出位置與數量（不輸出原文）。

用法（經 tools/ida.sh，資料檔放在 <HR_IDA_WORK>/run/data/，容器內 /work/data）：
  ida_text2_corpus.py <輸出前綴>
輸出：
  -summary.txt  彙總（工具、輸入雜湊、各項計數與位置）
  -items.tsv    每個項目一列：檔 id 位元組數 手動行數 最長行 折行後行數(W248/W504/W536) 吞行 拆字…（只有數字與 id）
模擬依據（全部來自 MAIN.EXE 位元組，非猜測）：
  1000:966C(c,0)：tbl[c]&4 → 1（lead）；否則 ctype[c]&0xDE → 0；否則 tbl[c]&3 → 0；否則 -1。
  25DC:1676 迴圈頂端：*p!=0 且 *p!=0x0A 且 8*si<maxw 才進入；回傳值≠0 時走成對路徑（畫 p，si++，若 8*si>maxw 或 *p==0 即離開，
  否則無條件再畫一個位元組），＝0 時只畫一個位元組。離開後若 *p==0x0A 則 si++，傳回 *p==0 ? 0 : si。
tbl＝dseg:09D1 起 256 bytes（檔案位移 0x583C1），ctype＝dseg:040F 起 256 bytes（檔案位移 0x57DFF）。
"""
import hashlib
import struct
import sys
import traceback

import ida_auto
import ida_bytes
import ida_pro

ida_auto.auto_wait()
PFX = sys.argv[1]
D = "/work/data/"
EXE = open("/work/MAIN.EXE", "rb").read()
TBL_OFF, CT_OFF = 0x583C1, 0x57DFF
tbl = EXE[TBL_OFF:TBL_OFF + 256]
ct = EXE[CT_OFF:CT_OFF + 256]
LIN_DSEG = 0x62FF0
ida_tbl = ida_bytes.get_bytes(LIN_DSEG + 0x9D1, 256)
ida_ct = ida_bytes.get_bytes(LIN_DSEG + 0x40F, 256)


def cls(c):
    if tbl[c] & 4:
        return 1
    if ct[c] & 0xDE:
        return 0
    if tbl[c] & 3:
        return 0
    return -1


def sim_line(buf, p, maxw):
    """模擬 25DC:1676 一次呼叫。buf 後面要有足夠的 NUL 墊底。回傳 dict。"""
    si = 0
    swallowed = False
    split = False
    pair_entered = 0
    while True:
        b = buf[p + si]
        if b == 0 or b == 0x0A or not (8 * si < maxw):
            break
        if cls(b) != 0:
            pair_entered += 1
            si += 1
            if 8 * si > maxw or buf[p + si] == 0:
                break
            if buf[p + si] == 0x0A:
                swallowed = True
            si += 1
        else:
            si += 1
    nl = buf[p + si] == 0x0A
    ended_by_width = (not nl) and buf[p + si] != 0
    # 寬度離開時，最後畫出的位元組若是真正的 lead，且 buf[p+si] 是它的 trail，就是拆字
    if ended_by_width and si > 0:
        prev = buf[p + si - 1]
        # 真實 Big5 配對由呼叫端傳入的 true_lead 集合判定，這裡先記錄位置
        split = True
    if nl:
        si += 1
        ret = si
    else:
        ret = 0 if buf[p + si] == 0 else si
    return {"ret": ret, "si": si, "swallowed": swallowed, "ended_by_width": ended_by_width, "pair_entered": pair_entered}


def true_pairs(b):
    """依序解析，傳回 {lead 位置: trail 位置} 的集合（lead 0x81-0xFE 且下一位元組 0x40-0x7E 或 0x80-0xFE）。"""
    res = set()
    i = 0
    while i < len(b):
        c = b[i]
        if c >= 0x81 and i + 1 < len(b) and (0x40 <= b[i + 1] <= 0x7E or 0x80 <= b[i + 1] <= 0xFE):
            res.add(i)
            i += 2
        else:
            i += 1
    return res


def wrap_lines(item, maxw):
    """模擬 18AC 的逐行呼叫，傳回 (行數, 吞行數, 拆字數, 吞行位置[(行號, 行內位移)], 拆字位置)。"""
    buf = item + b"\0" * 8
    tp = true_pairs(item)
    pos = 0
    lines = 0
    swallow = []
    splits = []
    guard = 0
    while buf[pos] != 0 and guard < 400:
        guard += 1
        r = sim_line(buf, pos, maxw)
        lines += 1
        if r["swallowed"]:
            swallow.append((lines - 1, r["si"]))
        if r["ended_by_width"]:
            last = pos + r["si"] - 1
            if last in tp:  # 最後畫出的位元組是真 lead，trail 被留到下一行
                splits.append((lines - 1, r["si"]))
        if r["ret"] == 0:
            break
        pos += r["ret"]
    return lines, swallow, splits


def parse_mes(d, name):
    k = struct.unpack_from("<H", d, 0)[0]
    offs = [struct.unpack_from("<I", d, 2 + 4 * i)[0] for i in range(k)]
    items = []
    for i in range(k - 1):
        a, b = offs[i], offs[i + 1]
        raw = d[a:b]
        s = raw.split(b"\0")[0]
        items.append(("%s#%d" % (name, i), s, len(raw)))
    return items


def parse_esp(d):
    n = struct.unpack_from("<H", d, 0)[0]
    offs = [struct.unpack_from("<I", d, 2 + 4 * i)[0] for i in range(n - 1)]
    offs.append(len(d))
    items = []
    for g in range(len(offs) - 1):
        a, e = offs[g], offs[g + 1]
        if a >= e:
            continue
        grp = d[a:e]
        n2 = struct.unpack_from("<H", grp, 0)[0]
        o2 = None
        for cnt in (n2 - 1, n2):
            if cnt < 1 or 2 + 4 * cnt > len(grp):
                continue
            t = [struct.unpack_from("<I", grp, 2 + 4 * i)[0] for i in range(cnt)]
            if t[0] == 2 + 4 * cnt:
                o2 = t
                break
        if o2 is None:
            continue
        for k in range(len(o2) - 1):
            s, t = o2[k], o2[k + 1]
            if s >= t or t > len(grp):
                items.append(("ESPMES#%d.%d" % (g, k), b"", 0))
                continue
            raw = grp[s:t]
            items.append(("ESPMES#%d.%d" % (g, k), raw.split(b"\0")[0], len(raw)))
    return items


def end_trigger(line):
    """行尾字（真 Big5 配對）的 lead 在 A1-DF 且 trail 在 E0-FC。"""
    if len(line) < 2:
        return False
    tp = true_pairs(line)
    if (len(line) - 2) in tp:
        L, T = line[-2], line[-1]
        return 0xA1 <= L <= 0xDF and 0xE0 <= T <= 0xFC
    return False


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    files = {}
    for n in ("COUNTRY.MES", "SP.MES", "SYSTEM.MES", "UWASA.MES", "POWERMES.MES"):
        files[n] = open(D + n, "rb").read()
    esp = open(D + "ESPMES.MRG", "rb").read()
    allitems = []
    for n, d in files.items():
        allitems += parse_mes(d, n)
    allitems += parse_esp(esp)

    out = open(PFX + "-summary.txt", "w", encoding="utf-8")
    tsv = open(PFX + "-items.tsv", "w", encoding="utf-8")
    out.write("# ida_text2_corpus.py 輸出（不含原文）\n")
    out.write("MAIN.EXE sha256 %s\n" % sha(EXE))
    for n, d in list(files.items()) + [("ESPMES.MRG", esp)]:
        out.write("%s %d bytes sha256 %s\n" % (n, len(d), sha(d)))
    out.write("表 dseg:09D1（IDA 資料庫）與檔案位移 %#x 是否相同：%s；ctype dseg:040F 與檔案位移 %#x：%s\n" % (
        TBL_OFF, ida_tbl == tbl, CT_OFF, ida_ct == ct))
    out.write("表 09D1 sha256 %s；ctype 040F sha256 %s\n" % (sha(tbl), sha(ct)))
    # 表的位元分布
    lead = [c for c in range(256) if tbl[c] & 4]
    trail = [c for c in range(256) if tbl[c] & 8]
    b1 = [c for c in range(256) if tbl[c] & 1]
    b2 = [c for c in range(256) if tbl[c] & 2]

    def ranges(xs):
        rs = []
        for x in xs:
            if rs and rs[-1][1] == x - 1:
                rs[-1][1] = x
            else:
                rs.append([x, x])
        return ",".join("%02X-%02X" % (a, b) if a != b else "%02X" % a for a, b in rs)

    out.write("tbl bit4(lead)：%s\n" % ranges(lead))
    out.write("tbl bit8(trail)：%s\n" % ranges(trail))
    out.write("tbl bit1：%s\n" % ranges(b1))
    out.write("tbl bit2：%s\n" % ranges(b2))
    for v in sorted(set(tbl)):
        out.write("tbl 值 %02X：%s\n" % (v, ranges([c for c in range(256) if tbl[c] == v])))
    c0 = [c for c in range(256) if cls(c) == 0]
    c1 = [c for c in range(256) if cls(c) == 1]
    cm = [c for c in range(256) if cls(c) == -1]
    out.write("966C(c,0) 分類：單位元組(0)＝%s\n  lead(1)＝%s\n  其他(-1，1676 當成對路徑)＝%s\n" % (ranges(c0), ranges(c1), ranges(cm)))

    tsv.write("item\tbytes_incl_nul\ttext_bytes\tmanual_lines\tmax_line\tn_over31\tn_over63\tw248_lines\tw504_lines\tw536_lines\tw320_lines\tswallow_inf\tswallow_248\tsplit_248\tsplit_504\tend_trigger\tmax_trail_e0fc_pairs\n")
    stats = {}
    swall_inf_pos = []
    swall_248_pos = []
    trig_pos = []
    trig_uniq = {}
    over4_248, over8_504, over5_536, over4_manual = [], [], [], []
    over4_568, split568 = [], []
    for iid, s, rawlen in allitems:
        f = iid.split("#")[0]
        st = stats.setdefault(f, {"items": 0, "empty": 0, "maxlen": 0, "maxid": "", "trig_lines": 0, "trig_items": 0,
                                   "swall_inf_items": 0, "swall_inf_lines": 0, "swall_248_items": 0,
                                   "split248_items": 0, "split504_items": 0, "over4_248": 0, "over8_504": 0,
                                   "over5_536": 0, "ge31": 0, "ge63": 0, "len_ge_200": 0, "lens": []})
        st["items"] += 1
        if not s:
            st["empty"] += 1
            tsv.write("%s\t%d\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\n" % (iid, rawlen))
            continue
        st["lens"].append((len(s), iid))
        if len(s) > st["maxlen"]:
            st["maxlen"], st["maxid"] = len(s), iid
        lines = s.split(b"\n")
        linf, swinf, _ = wrap_lines(s, 100000)
        ml = linf  # 手動換行的行數（尾端的 0x0A 之後不算一行）
        mx = max(len(x) for x in lines)
        n31 = sum(1 for x in lines if len(x) > 31)
        n63 = sum(1 for x in lines if len(x) > 63)
        if n31:
            st["ge31"] += 1
        if n63:
            st["ge63"] += 1
        # 注意：split 的最後一段是以 NUL 結尾的行，後面沒有 0x0A，不會吞到換行，不計入
        trig = [(i, len(ln)) for i, ln in enumerate(lines[:-1]) if end_trigger(ln)]
        if trig:
            st["trig_items"] += 1
            st["trig_lines"] += len(trig)
            for i, ln in trig:
                trig_pos.append("%s:L%d" % (iid, i))
                trig_uniq.setdefault(hashlib.sha256(lines[i]).hexdigest()[:8], []).append(iid)
        l248, sw248, sp248 = wrap_lines(s, 248)
        l504, sw504, sp504 = wrap_lines(s, 504)
        l536, _, _ = wrap_lines(s, 536)
        l320, _, _ = wrap_lines(s, 320)
        l568, sw568, sp568 = wrap_lines(s, 568)
        if l568 > 4:
            over4_568.append((iid, l568))
        if sp568:
            split568.append(iid)
        if swinf:
            st["swall_inf_items"] += 1
            st["swall_inf_lines"] += len(swinf)
            for ln, off in swinf:
                swall_inf_pos.append("%s:L%d@%d" % (iid, ln, off))
        if sw248:
            st["swall_248_items"] += 1
            for ln, off in sw248:
                swall_248_pos.append("%s:L%d@%d" % (iid, ln, off))
        if sp248:
            st["split248_items"] += 1
        if sp504:
            st["split504_items"] += 1
        if l248 > 4:
            st["over4_248"] += 1
            over4_248.append((iid, l248))
        if l504 > 8:
            st["over8_504"] += 1
            over8_504.append((iid, l504))
        if l536 > 5:
            st["over5_536"] += 1
            over5_536.append((iid, l536))
        if ml > 4:
            over4_manual.append((iid, ml))
        if len(s) + 1 >= 0x200:
            st["len_ge_200"] += 1
        tsv.write("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" % (
            iid, rawlen, len(s), ml, mx, n31, n63, l248, l504, l536, l320, len(swinf), len(sw248), len(sp248),
            len(sp504), len(trig), 0))
    tsv.close()

    out.write("\n== 各檔統計\n")
    for f, st in stats.items():
        top = sorted(st["lens"], reverse=True)[:5]
        out.write("%s：項目%d（空%d）最長 %d bytes（%s）；含 >31 bytes 行的項目 %d；含 >63 bytes 行的項目 %d；"
                  "行尾觸發（lead A1-DF、trail E0-FC，且該行後接 0x0A）項目 %d／行 %d；"
                  "無限寬模擬吞行 項目%d／行%d；W248 吞行項目 %d；W248 拆字項目 %d；W504 拆字項目 %d；"
                  "W248 折後>4行 %d；W504 折後>8行 %d；W536 折後>5行 %d；長度≥0x200 %d\n" % (
                      f, st["items"], st["empty"], st["maxlen"], st["maxid"], st["ge31"], st["ge63"], st["trig_items"],
                      st["trig_lines"], st["swall_inf_items"], st["swall_inf_lines"], st["swall_248_items"],
                      st["split248_items"], st["split504_items"], st["over4_248"], st["over8_504"], st["over5_536"],
                      st["len_ge_200"]))
        out.write("   最長 5 項：%s\n" % "; ".join("%s=%d" % (i, l) for l, i in top))
    out.write("\n行尾觸發位置（'項目:L行號'，行號從 0 起，限後接 0x0A 的行）共 %d：\n%s\n" % (len(trig_pos), " ".join(trig_pos)))
    out.write("\n行尾觸發的不重複行（以行位元組 SHA-256 前 8 碼分組）共 %d 種：\n" % len(trig_uniq))
    for h, ids in sorted(trig_uniq.items(), key=lambda kv: kv[1][0]):
        out.write("  %s ×%d：%s\n" % (h, len(ids), " ".join(ids)))
    out.write("\n無限寬模擬中換行被吞的位置（'項目:L行號@行內位移'）共 %d：\n%s\n" % (len(swall_inf_pos), " ".join(swall_inf_pos)))
    out.write("\nW248 模擬中換行被吞的位置共 %d：\n%s\n" % (len(swall_248_pos), " ".join(swall_248_pos)))
    out.write("\n手動換行行數 >4 的項目共 %d：%s\n" % (len(over4_manual), " ".join("%s=%d" % x for x in over4_manual)))
    out.write("\nW248（31 bytes/行）折後 >4 行的項目共 %d：%s\n" % (len(over4_248), " ".join("%s=%d" % x for x in over4_248)))
    out.write("\nW504（63 bytes/行）折後 >8 行的項目共 %d：%s\n" % (len(over8_504), " ".join("%s=%d" % x for x in over8_504)))
    out.write("\nW536（67 bytes/行）折後 >5 行的項目共 %d：%s\n" % (len(over5_536), " ".join("%s=%d" % x for x in over5_536)))
    out.write("\nW568（71 bytes/行，SP.MES 視窗 576x64＝4 行）折後 >4 行的項目共 %d：%s\n" % (
        len(over4_568), " ".join("%s=%d" % x for x in over4_568)))
    out.write("\nW568 行尾拆字（真 lead 留在行尾、trail 落到下一行）的項目共 %d：%s\n" % (len(split568), " ".join(split568)))
    out.close()


try:
    main()
except Exception:
    with open(PFX + "-error.txt", "w", encoding="utf-8") as e:
        e.write(traceback.format_exc())
ida_pro.qexit(0)
