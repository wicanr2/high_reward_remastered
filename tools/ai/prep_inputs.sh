#!/usr/bin/env bash
# AI theme 試作的輸入圖：原版解碼 PNG（workplace/re-img/out）最近鄰放大、透明處墊灰底（#808080），
# 輸出到 workplace/ai-hd/in/<名稱>.png。全部在 Docker 內（ImageMagick），原版目錄唯讀。
#   tools/ai/prep_inputs.sh
# 名稱、相對路徑與放大倍率的清單在本檔 LIST（試作的代表圖；全量時改由 hd/catalog.tsv 產生）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
test -d "$ROOT/workplace/re-img/out" || { echo "缺 workplace/re-img/out" >&2; exit 1; }
mkdir -p "$ROOT/workplace/ai-hd/in"
# 名稱 相對路徑 放大後尺寸
LIST='FACE000 MRG/FACE.MRG/FACE.MRG_000.png 768x960
ED0 GS/ED0.GS.png 1280x800
GMAP PXS/GMAP.PXS.png 1280x800
BSTAGE000 MRG/BSTAGE.MRG/BSTAGE.MRG_000.png 1440x440
BC32_000 MRG/BC32.MRG/BC32.MRG_000.png 1024x512
KOMA001 MRG/KOMA.MRG/KOMA.MRG_001.png 768x768
BUTTON000 MRG/BUTTON.MRG/BUTTON.MRG_000.png 768x768
SPOINT014 MRG/SPOINT.MRG/SPOINT.MRG_014.png 960x720
ITEM000 MRG/ITEM.MRG/ITEM.MRG_000.png 768x768'
exec timeout 5m docker run --rm --network none --memory 1g --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$ROOT/workplace/re-img/out:/src:ro" -v "$ROOT/workplace/ai-hd/in:/dst" -e HOME=/tmp -e LIST="$LIST" "$IMAGE" sh -c '
    echo "$LIST" | while read n p s; do
      convert "/src/$p" -background "#808080" -alpha remove -alpha off -filter point -resize "${s}!" "/dst/$n.png"
      echo "$n $(identify -format "%wx%h" /dst/$n.png)"
    done'
