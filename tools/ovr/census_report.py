#!/usr/bin/env python3
"""把 ida/out/all/ 的 IDA 普查 JSON 整理成文字檔 out/census_overlay.txt（標準庫，容器內執行）。"""
import json
import os
import sys

W = sys.argv[1] if len(sys.argv) > 1 else "/w"
A = os.path.join(W, "ida/out/all")
seg = json.load(open(os.path.join(A, "segments.json"), encoding="utf-8"))
c386 = json.load(open(os.path.join(A, "census386.json"), encoding="utf-8"))
ic = json.load(open(os.path.join(A, "int_census.json"), encoding="utf-8"))
ent = json.load(open(os.path.join(A, "entries_check.json"), encoding="utf-8"))
ov = json.load(open(os.path.join(W, "out/overlays.json"), encoding="utf-8"))
L = []
p = L.append
p("# MAIN.EXE overlay 區普查（IDA 9.4 DOS loader 預設載入，ida-pro-9.4-idapython:locked-v1）")
p(f"輸入 {ov['input']['path']} sha256 {ov['input']['sha256']}")
p("產生方式：./pipeline.sh（ida.sh run MAIN.EXE ovr_ida_all.py，再由本檔整理）")
p("")
p("## 1. 段落與覆蓋")
p(f"函式總數 {seg['functions_total']}")
p("類別       段落數   bytes   函式   code head   未定義 byte")
for k in ("resident", "stub", "ovr"):
    t = seg["by_class"].get(k, {})
    p(f"{k:9} {t.get('segments', 0):6} {t.get('bytes', 0):7} {t.get('funcs', 0):6} {t.get('code_heads', 0):10} {t.get('undef_bytes', 0):10}")
p("ovr 段落中未定義的 1 byte 是 ovr381（code size 0，IDA 仍建 1 byte 段落）。")
p(f"入口檢查：overlays.json 的 {ent['entries']} 個入口中，{ent['func_start']} 個是 IDA 函式起點；"
  f"資料庫內 stub 入口首位元組分佈 {ent['stub_db_bytes']}（IDA 載入時把 CD 3F 改寫成 EA jmp far）。")
p(f"指向 stub 入口的遠呼叫（9A）共 {ent['far_calls_to_stub_entries']}，依呼叫端類別 {ent.get('far_calls_by_caller_class')}；"
  f"其他 code ref {ent.get('other_code_refs')}")
p(f"offset 0 不是入口的段：{ent.get('offset0_not_entry')}")
p(f"「90 0E E8」：{ent.get('near_conv_90_0E_E8')}")
p("")
p("## 2. 386 形式（邏輯同 tools/ida_census_386.py，依類別分開）")
p(f"code head：{c386['code_heads']}")
for k in ("resident", "stub", "ovr"):
    forms = c386["forms"].get(k, {})
    p(f"### {k}：{sum(v['n'] for v in forms.values())} 條，{len(forms)} 種")
    for key, v in forms.items():
        ex = "；".join(f"{e['at']} {e['bytes']} {e['text']}" for e in v["ex"][:3])
        p(f"  {v['n']:4}  {key:10} {ex}")
p("")
p("## 3. int n（往前 8 道找 AH／AX 常數；結果是下限）")
p(f"總數：{ic['totals']}")
for k in ("resident", "stub", "ovr"):
    calls = ic["calls"].get(k, {})
    p(f"### {k}：{sum(v['n'] for v in calls.values())} 處，{len(calls)} 種")
    for key, v in calls.items():
        p(f"  {v['n']:4}  {key:28} {' '.join(v['ex'][:6])}")
p("")
p("## 4. 經由 C 執行期 _int86 的軟體中斷（int 指令普查看不到）")
p(open(os.path.join(A, "intwrap.txt"), encoding="utf-8").read().rstrip())
p("")
p("## 5. ovr 段落內的 in／out")
p(open(os.path.join(A, "ports.txt"), encoding="utf-8").read().rstrip())
p("")
p("指定中斷的前後文：ida/out/all/int_context.txt；overlay manager 反組譯與 _int86 呼叫端的 AX 設定：ida/out/ctx_dump.txt")
open(os.path.join(W, "out/census_overlay.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
