#!/usr/bin/env bash
# L2 DRAFT 本機預烘器。輸入須是已定稿折行後的碼位／字組清冊。
# bash tools/l10n/bakeglyphs.sh en <units.tsv> <輸出名稱>
# 只輸出 workplace/l3-visual-20261005/patches/<名稱>/，不改原版檔。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LANGUAGE="${1:?語言}"; UNITS="${2:?字組清冊}"; NAME="${3:?輸出名稱}"
[[ "$LANGUAGE" = en || "$LANGUAGE" = zh-CN || "$LANGUAGE" = ja || "$LANGUAGE" = ko ]]
[[ "$NAME" =~ ^[a-zA-Z0-9-]+$ ]]
FONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
OFL="$ROOT/workplace/out/re-text2/OFL-prototype.txt"
RESERVED="$ROOT/workplace/out/re-text/m10-reserved-codes.tsv"
OUT="$ROOT/workplace/l3-visual-20261005/patches"
for path in "$UNITS" "$FONT" "$OFL" "$RESERVED"; do
  test -f "$path" || { echo "缺少檔案：$path" >&2; exit 1; }
done
for path in "$ROOT/workplace/l3-visual-20261005" "$ROOT/tools/l10n"; do
  test -d "$path" || { echo "缺少目錄：$path" >&2; exit 1; }
done
mkdir -p "$OUT"
test "$(stat -c %u:%g "$OUT")" = "$(id -u):$(id -g)" || { echo "輸出目錄擁有權不符" >&2; exit 1; }
test ! -e "$OUT/$NAME" || { echo "不覆寫既有補丁" >&2; exit 1; }
IMAGE="yuan-analysis:1"
IMAGE_ID="$(docker image inspect "$IMAGE" --format '{{.Id}}')"
UNITS_DIR="$(cd "$(dirname "$UNITS")" && pwd)"
UNITS_FILE="$(basename "$UNITS")"
exec timeout 2m docker run --rm --name hr-l2-bakeglyphs --network none --memory 1g --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 --user "$(id -u):$(id -g)" \
  -v "$ROOT/tools/l10n:/tools:ro" -v "$(dirname "$FONT"):/font:ro" \
  -v "$(dirname "$OFL"):/ofl:ro" -v "$(dirname "$RESERVED"):/reserved:ro" \
  -v "$UNITS_DIR:/units:ro" -v "$OUT:/out" -e HR_IMAGE_ID="$IMAGE_ID" \
  --entrypoint python3 "$IMAGE" /tools/bakeglyphs.py --language "$LANGUAGE" \
  --font /font/NotoSansCJK-Regular.ttc --ofl /ofl/OFL-prototype.txt \
  --units "/units/$UNITS_FILE" --reserved /reserved/m10-reserved-codes.tsv --output "/out/$NAME"
