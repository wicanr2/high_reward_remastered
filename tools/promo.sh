#!/usr/bin/env bash
# 以真實操作錄影製作本機推廣片。輸出只放 dist-all/<版本>/promo/。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定正式版號}"
[[ "$VERSION" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
LIVE="${HR_PROMO_LIVE:?請指定本版實際完整版的繁中錄影目錄}"
ENGLISH="${HR_PROMO_ENGLISH:?請指定本版實際完整版的英文錄影目錄}"
AUDIO_MODE="${HR_PROMO_AUDIO_MODE:-pending}" # 原版錄音來源確定前先做無配樂預覽
[[ "$AUDIO_MODE" = pending || "$AUDIO_MODE" = original-recording || "$AUDIO_MODE" = none ]]
DELIVERY="$ROOT/dist-all/$VERSION"
FONTDIR=/usr/share/fonts/opentype/noto
test -d "$DELIVERY" && test -d "$LIVE" && test -d "$ENGLISH"
test -f "$LIVE/receipt.json" && test -f "$ENGLISH/receipt.json"
test -f "$FONTDIR/NotoSansCJK-Bold.ttc"
AUDIO_MOUNTS=()
if [ "$AUDIO_MODE" = original-recording ]; then
  AUDIO_FILE="${HR_PROMO_AUDIO_FILE:?請指定經原版執行錄製的 WAV}"
  AUDIO_RECEIPT="${HR_PROMO_AUDIO_RECEIPT:?請指定原版錄音來源收據}"
  test -f "$AUDIO_FILE" && test -f "$AUDIO_RECEIPT"
  AUDIO_FILE="$(cd "$(dirname "$AUDIO_FILE")" && pwd -P)/$(basename "$AUDIO_FILE")"
  AUDIO_RECEIPT="$(cd "$(dirname "$AUDIO_RECEIPT")" && pwd -P)/$(basename "$AUDIO_RECEIPT")"
  AUDIO_MOUNTS=(-v "$AUDIO_FILE:/music.wav:ro" -v "$AUDIO_RECEIPT:/audio-provenance.json:ro")
fi
IMAGE="${HR_CAPTURE_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
docker image inspect "$IMAGE" >/dev/null
exec timeout "${HR_PROMO_TIMEOUT:-25m}" docker run --rm --name hr-promo-render \
  --network none --memory 4g --cpus 3 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 --user "$(id -u):$(id -g)" \
  -e "HR_VERSION=$VERSION" -e "HR_PROMO_AUDIO_MODE=$AUDIO_MODE" -v "$DELIVERY:/delivery" -v "$LIVE:/live:ro" -v "$ENGLISH:/english:ro" \
  -v "$FONTDIR:/fonts:ro" -v "$ROOT/tools/render_promo.py:/render.py:ro" \
  "${AUDIO_MOUNTS[@]}" \
  "$IMAGE" python3 /render.py
