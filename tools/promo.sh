#!/usr/bin/env bash
# 以真實操作錄影製作本機推廣片。輸出只放 dist-all/<版本>/promo/。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定正式版號}"
[[ "$VERSION" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
LIVE="${HR_PROMO_LIVE:-$ROOT/workplace/out/live-f1-v101}"
ENGLISH="${HR_PROMO_ENGLISH:-$ROOT/workplace/out/live-en-debt-v101}"
DELIVERY="$ROOT/dist-all/$VERSION"
FONTDIR=/usr/share/fonts/opentype/noto
test -d "$DELIVERY" && test -d "$LIVE" && test -d "$ENGLISH"
test -f "$LIVE/receipt.json" && test -f "$ENGLISH/receipt.json"
test -f "$FONTDIR/NotoSansCJK-Bold.ttc" && test -f "$ROOT/workplace/out/music/wav/MAP2.wav"
IMAGE=eob-remake-go:1.26.7-ebiten2.9.9-video-ime1
docker image inspect "$IMAGE" >/dev/null
exec timeout "${HR_PROMO_TIMEOUT:-25m}" docker run --rm --name hr-promo-render \
  --network none --memory 4g --cpus 3 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 --user "$(id -u):$(id -g)" \
  -e "HR_VERSION=$VERSION" -v "$DELIVERY:/delivery" -v "$LIVE:/live:ro" -v "$ENGLISH:/english:ro" \
  -v "$FONTDIR:/fonts:ro" -v "$ROOT/tools/render_promo.py:/render.py:ro" \
  -v "$ROOT/workplace/out/music/wav/MAP2.wav:/music.wav:ro" \
  "$IMAGE" python3 /render.py
