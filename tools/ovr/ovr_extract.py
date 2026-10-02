#!/usr/bin/env python3
"""Borland C++ FBOV overlay 抽取器（《高報酬戰將》MAIN.EXE）。只用標準庫。

用法：
  python3 ovr_extract.py MAIN.EXE --out OUT [--resident-base 1000] [--ovr-base HEX]
                         [--ovr-seg NNN=HEX ...] [--no-fp-fix] [--compare-ida DIR] [--any-input]

輸出（OUT 之下）：
  ovr/ovrNNN.raw.bin   未套重定位的程式碼（長度 = stub 的 code size）
  ovr/ovrNNN.bin       套用重定位後的程式碼
  ovr_all.bin          所有 overlay 依配置段值排好的合併映像，起點是 --ovr-base 段的位移 0
  overlays.json        區塊標頭、段落表、每段 overlay 的欄位與入口表、緩衝區推算
  relocs.tsv           每一筆重定位（overlay、位移、原值、段落表索引、bit0、套用後的值）
  verify.txt           驗證結果，每項 PASS 或 FAIL；任何 FAIL 時結束碼為 1

NNN 是 overlay 在段落表（segment table）的索引，與 IDA 9.4 DOS loader 的 ovrNNN／stubNNN 同號。

段值慣例：
  段落表 +0 是映像相對的段值（MZ 重定位前）。套用時加上 --resident-base：
  0x1000 是 IDA 慣例（IDA 段 = 映像段 + 0x1000），0x110 是 dosgolem 執行期（載入段 0x110）。
  overlay 的程式碼位元組在重定位之後與它自己的載入段無關：指向 overlay 段落（含自己）的段值
  一律是該段的 stub 段（段落表 +0），所以 --ovr-base／--ovr-seg 只影響 ovr_all.bin 的排列
  與 overlays.json 內 stub 入口改寫成 jmp far 之後的目標。

本工具綁定特定輸入：SHA-256 不符時拒絕執行（--any-input 可略過，驗證項仍會跑）。
"""
import argparse
import hashlib
import json
import os
import struct
import sys

EXPECT_SHA256 = "08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e"

# 以下常數取自 IDA 對常駐映像 overlay manager 的反組譯（IDA 段 3582 = 映像段 0x2582），
# 反組譯全文見 ida/out/ctx_dump.txt（pipeline.sh 產生）。只拿來做一致性檢查，抽取本身不依賴它們。
MGR_PARA = 0x2582          # overlay manager 程式段（映像相對）
MGR_DS_SLOT = 0x000A       # cs:[000A] = overlay manager 的資料段
SEGTAB_DS_OFF = 0x00C0     # mov si, 0C0h（3582:02F2）
SEGTAB_DS_END = 0x0D40     # cmp si, 0D40h（3582:0346）
DSEG_PARA = 0x52FF         # C 執行期資料段 dseg（IDA 62FF）
OVRBUFFER_OFF = 0x0AD6     # dseg:0AD6，3582:0941 與 [AA] 比較的變數
STUB_HDR = 0x20            # mov di, 20h（3582:06DA）
ENTRY_LEN = 5              # add di, 5（3582:04F4）


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def hexs(v, w=4):
    return "%0*X" % (w, v)


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail):
        self.rows.append(("PASS" if ok else "FAIL", name, detail))
        return ok

    def failed(self):
        return [r for r in self.rows if r[0] != "PASS"]


def parse_mz(b):
    if b[:2] != b"MZ":
        raise SystemExit("不是 MZ 執行檔")
    last, pages, nrel, hdrp, minal, maxal, ss, sp, csum, ip, cs, relo = struct.unpack_from("<12H", b, 2)
    end = (pages - 1) * 512 + last if last else pages * 512
    rels = [struct.unpack_from("<HH", b, relo + 4 * i) for i in range(nrel)]
    return {"last": last, "pages": pages, "nrel": nrel, "hdr_bytes": hdrp * 16, "image_end": end,
            "image_len": end - hdrp * 16, "ss": ss, "sp": sp, "cs": cs, "ip": ip, "minalloc": minal,
            "maxalloc": maxal, "reloc_table": relo, "relocs": rels}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exe")
    ap.add_argument("--out", default="out")
    ap.add_argument("--resident-base", default="1000", help="加到映像相對段值的基底（十六進位），IDA=1000，dosgolem=110")
    ap.add_argument("--ovr-base", default=None, help="第一段 overlay 的配置段（十六進位）；預設接在映像之後，與 IDA 9.4 相同")
    ap.add_argument("--ovr-seg", action="append", default=[], help="NNN=HEX，單獨指定某段 overlay 的配置段")
    ap.add_argument("--no-fp-fix", action="store_true", help="不做 bit0 的遠指標轉換（預設照 overlay manager 的行為做）")
    ap.add_argument("--compare-ida", default=None, help="IDA 匯出的 ovrNNN.bin 目錄，逐位元組比對")
    ap.add_argument("--any-input", action="store_true")
    a = ap.parse_args()

    b = open(a.exe, "rb").read()
    sha = hashlib.sha256(b).hexdigest()
    if sha != EXPECT_SHA256 and not a.any_input:
        raise SystemExit(f"輸入 SHA-256 {sha} 與預期 {EXPECT_SHA256} 不符；確定要跑請加 --any-input")
    rb = int(a.resident_base, 16)
    ck = Checks()
    mz = parse_mz(b)
    hdr, end = mz["hdr_bytes"], mz["image_end"]
    img = b[hdr:end]
    ck.add("MZ 標頭", hdr == 18944 and end == 361856 and mz["nrel"] == 4352,
           f"header {hdr} bytes，映像結束於 {end}（{end:#x}），映像 {mz['image_len']} bytes，重定位 {mz['nrel']} 項")
    relimg = {seg * 16 + off for off, seg in mz["relocs"]}

    # ---- FBOV 區塊標頭 ----
    blocks = []
    pos = end
    while pos + 16 <= len(b):
        magic = b[pos:pos + 4]
        blen = u32(b, pos + 4)
        blocks.append({"file_offset": pos, "magic": magic.decode("latin1"), "len_after_header": blen,
                       "u32_8": u32(b, pos + 8), "u32_12": u32(b, pos + 12)})
        pos += 16 + blen
    ck.add("區塊鏈涵蓋到檔尾", pos == len(b) and len(blocks) == 1 and blocks[0]["magic"] == "FBOV",
           f"自 {end} 起 {len(blocks)} 個區塊，最後結束於 {pos}，檔長 {len(b)}")
    fb = blocks[0]
    data0 = fb["file_offset"] + 16
    segtab_file = fb["u32_8"]
    nseg = fb["u32_12"]
    segtab_img = segtab_file - hdr

    # ---- 段落表 ----
    mgr_ds = u16(img, MGR_PARA * 16 + MGR_DS_SLOT)
    ck.add("FBOV +8 = 段落表的檔案位移", segtab_img == mgr_ds * 16 + SEGTAB_DS_OFF,
           f"+8 = {segtab_file:#x}，減標頭 = 映像 {segtab_img:#x}；overlay manager 資料段 cs:[000A] = 映像段 {mgr_ds:04X}，"
           f"{mgr_ds:04X}:{SEGTAB_DS_OFF:04X} = 映像 {mgr_ds * 16 + SEGTAB_DS_OFF:#x}")
    ck.add("FBOV +12 = 段落表筆數", nseg * 8 == SEGTAB_DS_END - SEGTAB_DS_OFF,
           f"+12 = {nseg}，{nseg} × 8 = {nseg * 8:#x}；迴圈範圍 {SEGTAB_DS_OFF:#x}..{SEGTAB_DS_END:#x} = {SEGTAB_DS_END - SEGTAB_DS_OFF:#x}")
    segtab = []
    for i in range(nseg):
        o = segtab_img + 8 * i
        para, size, flags, start = struct.unpack_from("<4H", img, o)
        segtab.append({"idx": i, "para": para, "maxoff": size, "flags": flags, "minoff": start,
                       "mz_reloc": o in relimg})
    ck.add("段落表每筆 +0 都是 MZ 重定位目標", all(s["mz_reloc"] for s in segtab),
           f"{sum(s['mz_reloc'] for s in segtab)} / {nseg}")
    fh = {}
    for s in segtab:
        fh[s["flags"]] = fh.get(s["flags"], 0) + 1
    ovs = [s for s in segtab if s["flags"] & 2]
    # +2 = maxoff、+6 = minoff 的解讀（強推論）：相鄰兩筆 para*16+maxoff 與下一筆 para*16+minoff 相接
    cont = {"eq": 0, "gap_lt16": 0, "other": 0, "ffff": 0}
    for k in range(nseg - 1):
        s, t = segtab[k], segtab[k + 1]
        if s["maxoff"] == 0xFFFF or t["maxoff"] == 0xFFFF:
            cont["ffff"] += 1
            continue
        g = t["para"] * 16 + t["minoff"] - (s["para"] * 16 + s["maxoff"])
        cont["eq" if g == 0 else ("gap_lt16" if 0 < g < 16 else "other")] += 1
    ck.add("段落表 +2／+6 解讀為 maxoff／minoff 時相鄰段相接（資訊）", cont["other"] <= 1,
           f"{cont}（other 那 1 筆是 dseg 391 的 maxoff 涵蓋 392 起的小段）")

    # ---- stub 與 overlay ----
    overlays = []
    stub_by_para = {}
    bad_stub = []
    for s in ovs:
        so = s["para"] * 16
        h = img[so:so + STUB_HDR]
        ov = {"idx": s["idx"], "name": "ovr%03d" % s["idx"], "stub_name": "stub%03d" % s["idx"],
              "stub_para": s["para"], "segtab_maxoff": s["maxoff"], "segtab_flags": s["flags"],
              "stub_hdr_hex": h.hex(" "),
              "rel_offset": u32(h, 4), "code_size": u16(h, 8), "reloc_size": u16(h, 0x0A),
              "entry_count": u16(h, 0x0C), "f02": u16(h, 2), "f0e": u16(h, 0x0E),
              "runtime_area_10_1f_zero": h[0x10:0x20] == bytes(16), "f1a": h[0x1A]}
        ov["file_offset"] = data0 + ov["rel_offset"]
        if h[:2] != b"\xcd\x3f":
            bad_stub.append((s["idx"], "magic"))
        ents = []
        for i in range(ov["entry_count"]):
            e = img[so + STUB_HDR + ENTRY_LEN * i: so + STUB_HDR + ENTRY_LEN * (i + 1)]
            ents.append({"i": i, "stub_off": STUB_HDR + ENTRY_LEN * i, "code_off": u16(e, 2), "byte4": e[4],
                         "magic_ok": e[:2] == b"\xcd\x3f"})
        ov["entries"] = ents
        overlays.append(ov)
        stub_by_para[s["para"]] = ov
    ck.add("overlay 段落數與旗標", len(ovs) == 139 and all(s["flags"] == 3 for s in ovs),
           f"旗標分佈 {dict(sorted(fh.items()))}；flags bit1 的 {len(ovs)} 筆全為 3：{all(s['flags'] == 3 for s in ovs)}")
    ck.add("stub 標頭 CD 3F", not bad_stub, f"不符 {bad_stub[:5]}")
    ck.add("段落表 maxoff = 20h + 5 × entry 數",
           all(o["segtab_maxoff"] == STUB_HDR + ENTRY_LEN * o["entry_count"] for o in overlays),
           "反例 " + str([o["idx"] for o in overlays if o["segtab_maxoff"] != STUB_HDR + ENTRY_LEN * o["entry_count"]][:5]))
    ck.add("stub +2、+0E、+10..+1F 在檔案內為 0",
           all(o["f02"] == 0 and o["f0e"] == 0 and o["runtime_area_10_1f_zero"] for o in overlays),
           "反例 " + str([o["idx"] for o in overlays if not (o["f02"] == 0 and o["f0e"] == 0 and o["runtime_area_10_1f_zero"])][:5]))
    allents = [e for o in overlays for e in o["entries"]]
    ck.add("入口 CD 3F、第 5 byte 為 0、位移落在程式碼內",
           all(e["magic_ok"] and e["byte4"] == 0 for e in allents)
           and all(e["code_off"] < o["code_size"] for o in overlays for e in o["entries"]),
           f"入口共 {len(allents)} 筆")
    dup = [o["name"] for o in overlays if len({e["code_off"] for e in o["entries"]}) != len(o["entries"])]
    ck.add("同一段內入口的程式碼位移不重複", not dup, f"重複的段 {dup}")
    # 映像內所有 CD 3F 的歸類：stub 標頭、入口、overlay manager 的 [00A0] 字組，其餘算巧合
    hdr_pos = {o["stub_para"] * 16 for o in overlays}
    ent_pos = {o["stub_para"] * 16 + STUB_HDR + ENTRY_LEN * e["i"] for o in overlays for e in o["entries"]}
    mgr_word = mgr_ds * 16 + 0xA0
    hits, i = [], 0
    while True:
        i = img.find(b"\xcd\x3f", i)
        if i < 0:
            break
        hits.append(i)
        i += 1
    other = [h for h in hits if h not in hdr_pos and h not in ent_pos and h != mgr_word]
    cd3f = {"hits": len(hits), "stub_headers": len(hdr_pos & set(hits)), "entries": len(ent_pos & set(hits)),
            "mgr_word_00A0": int(mgr_word in hits), "other": len(other), "other_image_offsets": [hexs(h, 5) for h in other[:20]]}
    ck.add("映像內 CD 3F 全數有歸屬（標頭 + 入口 + manager 的 [00A0]）", not other and len(hits) == len(hdr_pos) + len(ent_pos) + 1,
           f"{cd3f}")
    ck.add("stub 之間互不重疊且段落對齊",
           all(overlays[k]["stub_para"] * 16 + overlays[k]["segtab_maxoff"] <= overlays[k + 1]["stub_para"] * 16
               for k in range(len(overlays) - 1)),
           f"stub 段 {hexs(overlays[0]['stub_para'])}..{hexs(overlays[-1]['stub_para'])}（映像相對）")

    # ---- 檔案內的排列 ----
    fo = sorted(overlays, key=lambda o: o["rel_offset"])
    blen = fb["len_after_header"]
    aligned = all(o["rel_offset"] % 16 == 0 for o in fo)
    overlap, nonzero_gap, pad_rule_bad = [], [], []
    for k in range(len(fo)):
        o = fo[k]
        nxt = fo[k + 1]["rel_offset"] if k + 1 < len(fo) else blen
        o["span"] = nxt - o["rel_offset"]
        used = o["code_size"] + o["reloc_size"]
        o["pad"] = o["span"] - used
        if o["pad"] < 0:
            overlap.append(o["name"])
        g0 = o["file_offset"] + used
        if any(b[g0:g0 + max(0, o["pad"])]):
            nonzero_gap.append(o["name"])
        # 補白的來源（強推論）：TLINK 把同段遠呼叫改成 90 0E E8 後，空出的 reloc 項不回收
        code = b[o["file_offset"]:o["file_offset"] + o["code_size"]]
        n, i = 0, 0
        while True:
            i = code.find(b"\x90\x0e\xe8", i)
            if i < 0:
                break
            n, i = n + 1, i + 1
        o["near_conv_90_0E_E8"] = n
        pred = max(16, ((used + 2 * n + 15) // 16) * 16)
        if pred != o["span"]:
            pad_rule_bad.append((o["name"], o["span"], pred))
    ck.add("檔案內各段段落對齊、遞增、不重疊", fo[0]["rel_offset"] == 0 and aligned and not overlap,
           f"第一段相對位移 {fo[0]['rel_offset']}，全部 16 對齊：{aligned}，重疊 {overlap}")
    ck.add("段與段之間的補白全為 0", not nonzero_gap, f"補白非 0 的段 {nonzero_gap}")
    ck.add("長度加總 = FBOV +4",
           sum(o["code_size"] + o["reloc_size"] + o["pad"] for o in fo) == blen
           and fo[-1]["rel_offset"] + fo[-1]["code_size"] + fo[-1]["reloc_size"] <= blen,
           f"Σ code = {sum(o['code_size'] for o in fo)}，Σ reloc = {sum(o['reloc_size'] for o in fo)}，"
           f"Σ 補白 = {sum(o['pad'] for o in fo)}，合計 {sum(o['code_size'] + o['reloc_size'] + o['pad'] for o in fo)}；"
           f"FBOV +4 = {blen}；補白 ≥ 16 的段 {[o['name'] for o in fo if o['pad'] >= 16]}")
    ck.add("每段跨距 = max(16, align16(code + reloc + 2 × 「90 0E E8」數))", not pad_rule_bad,
           f"不符 {pad_rule_bad[:5]}（強推論：補白是 TLINK 改成近呼叫後空出的重定位項）")
    ck.add("段落表順序 = 檔案順序", [o["idx"] for o in fo] == [o["idx"] for o in overlays], "")
    ck.add("code + reloc 不超出區塊", all(o["file_offset"] + o["code_size"] + o["reloc_size"] <= len(b) for o in overlays), "")

    # ---- 配置段 ----
    img_paras = (mz["image_len"] + 15) // 16
    ovr_base = int(a.ovr_base, 16) if a.ovr_base else rb + img_paras
    override = {}
    for spec in a.ovr_seg:
        k, v = spec.split("=")
        override[int(k)] = int(v, 16)
    cur = ovr_base
    for o in overlays:
        o["load_seg"] = override.get(o["idx"], cur)
        # IDA 9.4 對 code size 0 的段仍建 1 byte 段落，佔一個段落；這裡照做，讓預設排列與 IDA 相同
        cur = max(cur, o["load_seg"] + max(1, (o["code_size"] + 15) // 16))
    for o in overlays:
        o["stub_seg"] = o["stub_para"] + rb
        for e in o["entries"]:
            e["patched"] = "EA %02X %02X %02X %02X" % (e["code_off"] & 0xFF, e["code_off"] >> 8,
                                                       o["load_seg"] & 0xFF, o["load_seg"] >> 8)

    # ---- 重定位 ----
    os.makedirs(os.path.join(a.out, "ovr"), exist_ok=True)
    rel_rows = []
    lowbits = {}
    tgt_kind = {"overlay": 0, "code": 0, "data": 0, "other": 0}
    fp_stats = {"bit0": 0, "pattern": 0, "converted": 0, "target_not_overlay": 0, "no_entry": 0}
    rel_bad = []
    for o in overlays:
        fo_ = o["file_offset"]
        raw = bytearray(b[fo_:fo_ + o["code_size"]])
        rtab = b[fo_ + o["code_size"]: fo_ + o["code_size"] + o["reloc_size"]]
        code = bytearray(raw)
        if o["reloc_size"] % 2:
            rel_bad.append((o["idx"], "odd reloc size"))
        offs = [u16(rtab, 2 * i) for i in range(o["reloc_size"] // 2)]
        o["reloc_count"] = len(offs)
        o["reloc_desc"] = all(offs[k] > offs[k + 1] for k in range(len(offs) - 1))
        so_ = sorted(offs)
        o["reloc_disjoint"] = all(so_[k + 1] - so_[k] >= 2 for k in range(len(so_) - 1))
        o["fp_fix"] = 0
        o["reloc_to_self"] = 0
        o["reloc_to_other_ovr"] = 0
        for r in offs:
            if r + 2 > o["code_size"]:
                rel_bad.append((o["idx"], "offset %04X 超出 code" % r))
                continue
            w = u16(code, r)
            lowbits[w & 7] = lowbits.get(w & 7, 0) + 1
            ti = (w & 0xFFF8) >> 3
            if ti >= nseg:
                rel_bad.append((o["idx"], "index %d 超出段落表" % ti))
                continue
            t = segtab[ti]
            if ti == o["idx"]:
                o["reloc_to_self"] += 1
            elif t["flags"] & 2:
                o["reloc_to_other_ovr"] += 1
            if t["flags"] & 2:
                tgt_kind["overlay"] += 1
            elif t["flags"] & 1:
                tgt_kind["code"] += 1
            elif t["flags"] & 4:
                tgt_kind["data"] += 1
            else:
                tgt_kind["other"] += 1
            val = (t["para"] + rb) & 0xFFFF
            struct.pack_into("<H", code, r, val)
            note = ""
            if w & 1:
                fp_stats["bit0"] += 1
                # 3582:04A3 起：B8+r <seg> 50+r B8+r <off> 50+r，把 <off> 換成目標 stub 的入口位移
                ok = (r >= 1 and r + 7 <= len(code)
                      and (code[r - 1] & 0xF8) == 0xB8 and (code[r + 2] & 0xF8) == 0x50
                      and (code[r - 1] & 7) == (code[r + 2] & 7)
                      and code[r + 3] == code[r - 1] and code[r + 6] == code[r + 2])
                if ok:
                    fp_stats["pattern"] += 1
                    if not (t["flags"] & 2):
                        fp_stats["target_not_overlay"] += 1
                        note = "bit0：目標不是 overlay，未轉換"
                    else:
                        tov = stub_by_para[t["para"]]
                        off = u16(code, r + 4)
                        hit = [e for e in tov["entries"] if e["code_off"] == off]
                        if hit:
                            fp_stats["converted"] += 1
                            o["fp_fix"] += 1
                            note = "bit0：off %04X → stub 入口 %04X" % (off, hit[0]["stub_off"])
                            if not a.no_fp_fix:
                                struct.pack_into("<H", code, r + 4, hit[0]["stub_off"])
                        else:
                            fp_stats["no_entry"] += 1
                            note = "bit0：off %04X 不是目標的入口，未轉換" % off
                else:
                    note = "bit0：前後指令不符樣式，未轉換"
            rel_rows.append((o["name"], r, w, ti, w & 1, val, note))
        o["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        o["bin_sha256"] = hashlib.sha256(code).hexdigest()
        open(os.path.join(a.out, "ovr", o["name"] + ".raw.bin"), "wb").write(raw)
        open(os.path.join(a.out, "ovr", o["name"] + ".bin"), "wb").write(code)
        o["_code"] = bytes(code)
    ck.add("重定位表：長度偶數、位移落在程式碼內、索引在段落表內", not rel_bad, f"問題 {rel_bad[:5]}")
    ck.add("重定位位移不重複、修補的字組互不重疊", all(o["reloc_disjoint"] for o in overlays),
           "反例 " + str([o["idx"] for o in overlays if not o["reloc_disjoint"]][:5])
           + f"；表內順序不影響結果（各筆獨立），嚴格遞減的段 {sum(o['reloc_desc'] for o in overlays)} / {len(overlays)}")
    ck.add("重定位原值低 3 位元只用到 bit0", set(lowbits) <= {0, 1}, f"低 3 位元分佈 {dict(sorted(lowbits.items()))}")
    ck.add("bit0 全部符合 push 遠指標樣式且可轉換",
           fp_stats["bit0"] == fp_stats["pattern"] == fp_stats["converted"], f"{fp_stats}")
    with open(os.path.join(a.out, "relocs.tsv"), "w", encoding="utf-8") as f:
        f.write("overlay\toffset\traw\tsegtab_idx\tbit0\tvalue\tnote\n")
        for n, r, w, ti, b0, val, note in rel_rows:
            f.write(f"{n}\t{r:04X}\t{w:04X}\t{ti}\t{b0}\t{val:04X}\t{note}\n")

    # ---- 合併映像 ----
    top = max(o["load_seg"] * 16 + o["code_size"] for o in overlays)
    allb = bytearray(top - ovr_base * 16)
    for o in overlays:
        p = o["load_seg"] * 16 - ovr_base * 16
        if p < 0:
            raise SystemExit(f"{o['name']} 的配置段 {o['load_seg']:04X} 低於 --ovr-base")
        allb[p:p + o["code_size"]] = o["_code"]
    open(os.path.join(a.out, "ovr_all.bin"), "wb").write(allb)

    # ---- 緩衝區推算（3582:07EA、3582:0350、3582:0928、3582:0358）----
    P = [((o["code_size"] + 0x11) >> 4) + ((o["reloc_size"] + 0xF) >> 4) for o in overlays]
    AA = max(P) + 2
    big = overlays[P.index(max(P))]
    ovrbuf = u16(img, DSEG_PARA * 16 + OVRBUFFER_OFF)
    if AA >= ovrbuf:
        bx = 2 * AA + 1
    else:
        bx = ovrbuf + 1
    usable = bx - 1
    linked = [o for o in overlays if o["segtab_maxoff"] != 0 and o["f1a"] != 0xFF]
    si = 0
    pre = []
    for k, o in enumerate(linked):
        if k + 1 >= len(linked):
            break
        span = (linked[k + 1]["rel_offset"] - o["rel_offset"]) // 16
        if si + span > usable:
            break
        pre.append(o["name"])
        si += span
    buf = {"max_paras_per_overlay": max(P), "max_overlay": big["name"], "AA_min_buffer_paras": AA,
           "ovrbuffer_var_dseg_0AD6": ovrbuf, "alloc_paras": bx, "usable_paras": usable,
           "usable_bytes": usable * 16, "preload_overlays": pre, "preload_paras": si, "preload_bytes": si * 16,
           "runtime_buffer_start_probe": "55C3", "runtime_buffer_end_calc": hexs(0x55C3 + usable)}
    ck.add("預載讀取長度 = 探針收據 50896（0xC6D0）", si * 16 == 50896,
           f"[AA] = {AA} 段落（最大 {big['name']} 需 {max(P)}），_ovrbuffer = {ovrbuf}，配置 {bx} 段落，可用 {usable}；"
           f"預載 {len(pre)} 段（{pre[0]}..{pre[-1] if pre else ''}）共 {si} 段落 = {si * 16} bytes")
    ck.add("緩衝區落在 AH=4A 之後的記憶體塊內（PSP 0100 + 6200 = 6300）", 0x55C3 + usable <= 0x6300,
           f"55C3 + {usable:#x} = {0x55C3 + usable:04X}")

    # ---- 與 IDA 比對 ----
    ida = None
    if a.compare_ida:
        same, diff, miss, empty = 0, [], [], []
        for o in overlays:
            p = os.path.join(a.compare_ida, o["name"] + ".bin")
            if not os.path.exists(p):
                miss.append(o["name"])
                continue
            ib = open(p, "rb").read()
            if ib == o["_code"]:
                same += 1
            elif o["code_size"] == 0 and len(ib) == 1:
                empty.append(f"{o['name']}（code size 0，IDA 建 1 byte 段，內容 {ib.hex()}）")
                same += 1
            else:
                d = [i for i in range(min(len(ib), len(o["_code"]))) if ib[i] != o["_code"][i]]
                diff.append({"name": o["name"], "ida_len": len(ib), "len": len(o["_code"]), "ndiff": len(d),
                             "first": ["%04X:%02X/%02X" % (i, o["_code"][i], ib[i]) for i in d[:6]]})
        ida = {"same": same, "diff": diff, "missing": miss, "empty_segments": empty}
        ck.add("與 IDA 9.4 DOS loader 載入的 ovr 段落逐位元組相同", same == len(overlays),
               f"相同 {same}，不同 {len(diff)}，缺 {len(miss)}；特例 {empty}；不同的前幾段 {diff[:3]}")
        sj = os.path.join(os.path.dirname(os.path.normpath(a.compare_ida)), "segments.json")
        if os.path.exists(sj):
            isegs = {s["name"]: s for s in json.load(open(sj))["segments"]}
            bad_sel = [o["name"] for o in overlays if isegs.get(o["name"], {}).get("sel") != o["load_seg"]]
            bad_stub = [o["name"] for o in overlays if isegs.get(o["stub_name"], {}).get("sel") != o["stub_seg"]]
            ida["sel_mismatch"] = bad_sel
            ida["stub_sel_mismatch"] = bad_stub
            ck.add("配置段與 IDA 的 ovrNNN／stubNNN 選擇子相同（resident_base=1000、預設 ovr_base 時）",
                   not bad_sel and not bad_stub,
                   f"ovr 不符 {bad_sel[:5]}，stub 不符 {bad_stub[:5]}")

    # ---- 輸出 ----
    for o in overlays:
        del o["_code"]
    res = {
        "tool": "ovr_extract.py", "input": {"path": os.path.basename(a.exe), "size": len(b), "sha256": sha},
        "conventions": {"resident_base": hexs(rb), "ovr_base": hexs(ovr_base), "fp_fix": not a.no_fp_fix,
                        "seg_note": "段值 = 映像相對段 + resident_base；IDA 慣例 resident_base=1000"},
        "mz": {k: v for k, v in mz.items() if k != "relocs"},
        "fbov": {"file_offset": fb["file_offset"], "magic": fb["magic"], "len_after_header": fb["len_after_header"],
                 "segtab_file_offset": segtab_file, "segtab_count": nseg, "data_file_offset": data0,
                 "header_hex": b[fb["file_offset"]:fb["file_offset"] + 16].hex(" ")},
        "segtab": {"image_offset": segtab_img, "flags_hist": {hexs(k): v for k, v in sorted(fh.items())},
                   "entries": [[s["idx"], hexs(s["para"]), hexs(s["maxoff"]), s["flags"], hexs(s["minoff"])] for s in segtab],
                   "entries_columns": ["idx", "para(映像相對)", "maxoff", "flags", "minoff"]},
        "overlays": [{
            "idx": o["idx"], "name": o["name"], "stub_name": o["stub_name"],
            "stub_para": hexs(o["stub_para"]), "stub_seg": hexs(o["stub_seg"]), "load_seg": hexs(o["load_seg"]),
            "file_offset": o["file_offset"], "rel_offset": o["rel_offset"], "code_size": o["code_size"],
            "reloc_size": o["reloc_size"], "reloc_count": o["reloc_count"], "span": o["span"], "pad": o["pad"],
            "near_conv_90_0E_E8": o["near_conv_90_0E_E8"], "fp_fix": o["fp_fix"],
            "reloc_to_self": o["reloc_to_self"], "reloc_to_other_ovr": o["reloc_to_other_ovr"],
            "stub_seg_dosgolem": hexs(o["stub_para"] + 0x110), "entry_count": o["entry_count"],
            "entries": [[e["i"], hexs(e["stub_off"]), hexs(e["code_off"])] for e in o["entries"]],
            "raw_sha256": o["raw_sha256"], "bin_sha256": o["bin_sha256"]} for o in overlays],
        "overlays_entries_columns": ["i", "stub_off", "code_off"],
        "reloc_summary": {"total": len(rel_rows), "low3_hist": {str(k): v for k, v in sorted(lowbits.items())},
                          "target_kind": tgt_kind, "fp_fix": fp_stats,
                          "to_self": sum(o["reloc_to_self"] for o in overlays),
                          "to_other_ovr": sum(o["reloc_to_other_ovr"] for o in overlays),
                          "near_conv_90_0E_E8": sum(o["near_conv_90_0E_E8"] for o in overlays)},
        "cd3f_scan": cd3f,
        "buffer": buf, "ida_compare": ida,
        "totals": {"overlays": len(overlays), "code_bytes": sum(o["code_size"] for o in overlays),
                   "reloc_bytes": sum(o["reloc_size"] for o in overlays), "entries": len(allents)},
    }
    with open(os.path.join(a.out, "overlays.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, "verify.txt"), "w", encoding="utf-8") as f:
        f.write(f"input {os.path.basename(a.exe)} sha256 {sha}\n")
        f.write(f"resident_base {hexs(rb)} ovr_base {hexs(ovr_base)} fp_fix {not a.no_fp_fix}\n")
        for st, n, d in ck.rows:
            f.write(f"[{st}] {n}：{d}\n")
        f.write(f"總計 {len(ck.rows)} 項，FAIL {len(ck.failed())} 項\n")
    sys.exit(1 if ck.failed() else 0)


if __name__ == "__main__":
    main()
