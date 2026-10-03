#!/usr/bin/env bash
# 產生前端介面的內嵌字型子集（docs/spec/006 第 6 節）。全部在 Docker 內。
#
#   tools/gen_ui_fonts.sh
#
# 步驟：
#   1. play.sh 的 Go 容器跑 TestGenCharsets，把五份字元表寫到 apps/hr/play/fonts/charset-<語言>.txt；
#   2. 核對主機的 NotoSansCJK-Regular.ttc 的 SHA-256（不符即失敗），唯讀掛進 fontTools 容器；
#   3. pyftsubset 依字元表各切一份子集（zh-TW 與 en 用 TC 字面 3、zh-CN 用 SC 字面 2、ko 用 KR 字面 1、ja 用 JP 字面 0），
#      丟棄 GSUB／GPOS 與提示（x/image 沒有 shaping），保留 .notdef 與 name ID 0、7、13、14（版權、商標、授權說明、授權網址）；
#   4. 核對 TTC 內指定字面的名稱（選到 Mono 字面會讓拉丁字母變等寬），印出 fontTools 版本與各檔大小。
# 輸出 apps/hr/play/fonts/ui-<語言>.otf 與 fonts/SOURCE.txt（來源、雜湊、版本）。授權全文在 fonts/OFL.txt。
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

# 1. 字元表
HR_GEN_CHARSET=/src/apps/hr/play/fonts "$ROOT/tools/play.sh" gen-charset

# 2 到 4. 子集
timeout 10m docker run --rm --name "hr-fonts-$$" --network none --memory 1g --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$(dirname "$TTC"):/fonts:ro" -v "$FONTDIR:/out" -e HOME=/tmp -e TTCNAME="$(basename "$TTC")" \
  yuan-analysis:1 sh -c '
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
    --layout-features= --no-hinting --notdef-outline --name-IDs=0,7,13,14 --legacy-kern --recalc-bounds
  ls -l /out/ui-$l.otf
done
'
{
  echo "來源：$(basename "$TTC")（Debian 套件 fonts-noto-cjk，Noto Sans CJK Regular，SIL Open Font License 1.1）"
  echo "SHA-256：$WANT_SHA"
  echo "字面：zh-TW 與 en ＝ 3（TC）、zh-CN ＝ 2（SC）、ko ＝ 1（KR）、ja ＝ 0（JP）"
  echo "工具：fontTools（容器 yuan-analysis:1）pyftsubset，--layout-features= --no-hinting --notdef-outline --name-IDs=0,7,13,14"
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
  -v "$FONTDIR:/out" -e HOME=/tmp yuan-analysis:1 python3 - <<'PY'
from fontTools.ttLib import TTFont
names = {}
for l in ("zh-TW", "zh-CN", "ko", "ja", "en"):
    n = TTFont("/out/ui-%s.otf" % l)["name"]
    for i in (0, 13, 14):
        s = n.getDebugName(i)
        assert s, (l, i)
        names.setdefault(i, set()).add(s)
for i in (0, 13, 14):
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
  tail -n +"$((start+1))" "$DOC" | sed 's/^ \.$//; s/^ //'
} > "$FONTDIR/OFL.txt"
rm -f "$FONTDIR/NOTICE-fonts.txt"
echo "授權檔：$(wc -l < "$FONTDIR/OFL.txt") 行（fonts/OFL.txt）"
