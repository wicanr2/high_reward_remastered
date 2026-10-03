#!/usr/bin/env bash
# 產生前端介面的內嵌字型子集（docs/spec/006 第 6 節）。全部在 Docker 內。
#
#   tools/gen_ui_fonts.sh
#
# 步驟：
#   1. play.sh 的 Go 容器跑 TestGenCharsets，把五份字元表寫到 apps/hr/play/fonts/charset-<語言>.txt；
#   2. 核對主機的 NotoSansCJK-Regular.ttc 的 SHA-256（不符即失敗），唯讀掛進 fontTools 容器；
#   3. pyftsubset 依字元表各切一份子集（zh-TW 與 en 用 TC 字面 3、zh-CN 用 SC 字面 2、ko 用 KR 字面 1、ja 用 JP 字面 0），
#      丟棄 GSUB／GPOS 與提示（x/image 沒有 shaping；--layout-features= 只清空特性，仍留空殼表，所以另加 --drop-tables+=GSUB,GPOS），
#      保留 .notdef 與 name ID 0、7、13、14（版權、商標、授權說明、授權網址）；
#   4. 核對 TTC 內指定字面的名稱（選到 Mono 字面會讓拉丁字母變等寬）；fontTools 版本不是 4.66.1 即失敗；
#      斷言每份子集沒有 GSUB、GPOS 表，且 name ID 0、7、13、14 都存在。
# 輸出 apps/hr/play/fonts/ui-<語言>.otf 與 fonts/SOURCE.txt（來源、雜湊、fontTools 版本、旗標）。授權全文在 fonts/OFL.txt
# （只取 OFL 1.1 一段，斷言不含 GPL 文字）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DG="$ROOT/workplace/dosgolem"
FONTDIR="$DG/apps/hr/play/fonts"
TTC="${HR_NOTO_TTC:-/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc}"
WANT_SHA="b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"
test -f "$TTC" || { echo "找不到 $TTC" >&2; exit 1; }
got="$(sha256sum "$TTC" | cut -d' ' -f1)"
[ "$got" = "$WANT_SHA" ] || { echo "TTC 的 SHA-256 是 $got，應為 $WANT_SHA" >&2; exit 1; }
mkdir -p "$FONTDIR"

# 映像：yuan-analysis:1 是另一個專案的映像（歸屬未驗證）；唯讀使用，但要鎖定映像 ID，換了就失敗
WANT_IMG="sha256:f9ea24396753f49d4c215763aa8726755041f0b523f93c9bdbffd76b8e358fca"
IMG="yuan-analysis:1"
gotimg="$(docker image inspect "$IMG" --format '{{.Id}}')" || { echo "找不到映像 $IMG" >&2; exit 1; }
[ "$gotimg" = "$WANT_IMG" ] || { echo "映像 $IMG 的 ID 是 $gotimg，應為 $WANT_IMG" >&2; exit 1; }

# 1. 字元表。play.sh 的容器指令以管線結尾（go test | tail），沒有 pipefail，測試失敗時整條仍回 0；
# 所以這裡檢查輸出含 PASS，並檢查五份字元表的時間戳比開始時間新，否則失敗（避免拿舊字元表切子集）。
START_TS="$(date +%s)"
sleep 1
GEN_LOG="$(HR_GEN_CHARSET=/src/apps/hr/play/fonts "$ROOT/tools/play.sh" gen-charset 2>&1)" || { echo "$GEN_LOG" >&2; echo "gen-charset 失敗" >&2; exit 1; }
echo "$GEN_LOG" | tail -12
echo "$GEN_LOG" | grep -q '^PASS' || { echo "gen-charset 的輸出沒有 PASS（TestGenCharsets 沒跑或失敗）" >&2; exit 1; }
for l in zh-TW zh-CN ko en ja; do
  ts="$(stat -c %Y "$FONTDIR/charset-$l.txt" 2>/dev/null || echo 0)"
  [ "$ts" -ge "$START_TS" ] || { echo "charset-$l.txt 的時間戳沒有更新（$ts < $START_TS）" >&2; exit 1; }
done

# fontTools 版本必須是 4.66.1（子集行為隨版本變）；SOURCE.txt 記錄它
WANT_FT="4.66.1"
FTV="$(timeout 2m docker run --rm --name "hr-ftver-$$" --network none --memory 256m --cpus 1 --pids-limit 32 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" -e HOME=/tmp \
  "$IMG" python3 -c 'import fontTools; print(fontTools.version)')"
[ "$FTV" = "$WANT_FT" ] || { echo "fontTools 是 $FTV，應為 $WANT_FT" >&2; exit 1; }

# 2 到 4. 子集
timeout 10m docker run --rm --name "hr-fonts-$$" --network none --memory 1g --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$(dirname "$TTC"):/fonts:ro" -v "$FONTDIR:/out" -e HOME=/tmp -e TTCNAME="$(basename "$TTC")" \
  "$IMG" sh -c '
set -e
echo "fontTools $(python3 -c "import fontTools; print(fontTools.version)")"
sha256sum "/fonts/$TTCNAME"
for pair in zh-TW:3 zh-CN:2 ko:1 en:3 ja:0; do
  l=${pair%%:*}; n=${pair##*:}
  python3 - "$l" "$n" <<PY
import sys
from fontTools.ttLib import TTCollection
l, n = sys.argv[1], int(sys.argv[2])
f = TTCollection("/fonts/" + __import__("os").environ["TTCNAME"]).fonts[n]
name = f["name"].getDebugName(4)
want = {"zh-TW": "Noto Sans CJK TC", "en": "Noto Sans CJK TC", "zh-CN": "Noto Sans CJK SC", "ko": "Noto Sans CJK KR", "ja": "Noto Sans CJK JP"}[l]
assert name in (want, want + " Regular"), (l, n, name)
print("面", n, name)
PY
  pyftsubset "/fonts/$TTCNAME" --font-number=$n --text-file=/out/charset-$l.txt --output-file=/out/ui-$l.otf \
    --layout-features= --drop-tables+=GSUB,GPOS --no-hinting --notdef-outline --name-IDs=0,7,13,14 --legacy-kern --recalc-bounds
  ls -l /out/ui-$l.otf
  python3 - "$l" <<PY
import sys
from fontTools.ttLib import TTFont
l = sys.argv[1]
f = TTFont("/out/ui-%s.otf" % l)
tabs = sorted(f.keys())
assert "GSUB" not in tabs and "GPOS" not in tabs, (l, tabs)
for i in (0, 7, 13, 14):
    assert f["name"].getDebugName(i), (l, "name", i)
print("表", " ".join(t for t in tabs if t != "GlyphOrder"))
PY
done
'
{
  echo "來源：$(basename "$TTC")（Debian 套件 fonts-noto-cjk，Noto Sans CJK Regular，SIL Open Font License 1.1）"
  echo "SHA-256：$WANT_SHA"
  echo "字面：zh-TW 與 en ＝ 3（TC）、zh-CN ＝ 2（SC）、ko ＝ 1（KR）、ja ＝ 0（JP）"
  echo "工具：fontTools $FTV（容器映像 $IMG，ID $gotimg）pyftsubset，--layout-features= --drop-tables+=GSUB,GPOS --no-hinting --notdef-outline --name-IDs=0,7,13,14 --legacy-kern --recalc-bounds"
  echo "字元表：charset-<語言>.txt（由 apps/hr/play 的 TestGenCharsets 產生）"
} > "$FONTDIR/SOURCE.txt"
echo "完成：$(ls "$FONTDIR"/ui-*.otf | wc -l) 份子集，總大小 $(cat "$FONTDIR"/ui-*.otf | wc -c) bytes"

# 授權檔：字型內嵌的版權與授權說明（name ID 0、13、14，OFL 第 2 條要求每份複本帶著版權聲明與授權），加 OFL 1.1 全文。
# 全文取自 Debian 套件 fonts-noto-cjk 的 copyright 檔（"License: SIL-1.1" 段），不憑記憶寫。
DOC=/usr/share/doc/fonts-noto-cjk/copyright
test -f "$DOC" || { echo "找不到 $DOC" >&2; exit 1; }
start="$(grep -n '^License: SIL-1.1' "$DOC" | tail -1 | cut -d: -f1)"
[ -n "$start" ] || { echo "$DOC 找不到 License: SIL-1.1 段" >&2; exit 1; }
timeout 5m docker run -i --rm --name "hr-fontlic-$$" --network none --memory 256m --cpus 1 --pids-limit 32 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$FONTDIR:/out" -e HOME=/tmp "$IMG" python3 - <<'PY'
from fontTools.ttLib import TTFont
names = {}
for l in ("zh-TW", "zh-CN", "ko", "ja", "en"):
    n = TTFont("/out/ui-%s.otf" % l)["name"]
    for i in (0, 7, 13, 14):
        s = n.getDebugName(i)
        assert s, (l, i)
        names.setdefault(i, set()).add(s)
for i in (0, 7, 13, 14):
    assert len(names[i]) == 1, (i, names[i])
with open("/out/NOTICE-fonts.txt", "w", encoding="utf-8") as f:
    f.write("Noto Sans CJK 子集（內嵌於 hr-play 的介面字型）\n\n")
    f.write("版權（字型 name ID 0）：%s\n" % next(iter(names[0])))
    f.write("授權說明（name ID 13）：%s\n" % next(iter(names[13])))
    f.write("授權網址（name ID 14）：%s\n" % next(iter(names[14])))
    f.write("這些子集是修改版（只保留介面用到的字元），依 OFL 1.1 散布，授權全文如下。\n\n")
PY
test -s "$FONTDIR/NOTICE-fonts.txt" || { echo "沒有產生 NOTICE-fonts.txt" >&2; exit 1; }
{
  cat "$FONTDIR/NOTICE-fonts.txt"
  # 只取 "License: SIL-1.1" 這一段：Debian copyright 的段落以空白開頭的行延續，遇到不以空白開頭的行（下一段，
  # 例如 debian/* 的 License: GPL-3+）就停。" ." 是 Debian 的空行寫法。
  awk -v s="$start" 'NR > s { if ($0 ~ /^ /) print; else exit }' "$DOC" | sed 's/^ \.$//; s/^ //'
} > "$FONTDIR/OFL.txt"
rm -f "$FONTDIR/NOTICE-fonts.txt"
grep -q 'SIL OPEN FONT LICENSE Version 1.1' "$FONTDIR/OFL.txt" || { echo "OFL.txt 沒有 OFL 1.1 全文" >&2; exit 1; }
if grep -q 'GNU General Public License' "$FONTDIR/OFL.txt"; then echo "OFL.txt 夾帶了 GPL 文字" >&2; exit 1; fi
echo "授權檔：$(wc -l < "$FONTDIR/OFL.txt") 行（fonts/OFL.txt）"
