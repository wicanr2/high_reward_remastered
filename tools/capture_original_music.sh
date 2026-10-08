#!/usr/bin/env bash
# 本機原版錄音。driver 必須已由使用者取得；不下載、不修改來源、不覆寫既有輸出。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
NAME="${1:-original-music}"
[[ "$NAME" =~ ^[a-zA-Z0-9_-]+$ ]]
ORIGINAL="${HR_AUDIO_ORIGINAL_DIR:-$ROOT/workplace/orig}"
DRIVER="${HR_AUDIO_DRIVER_FILE:?請設定已取得的 CTMIDI-S.DRV 檔案路徑}"
INVENTORY="$ROOT/docs/re/source-inventory.tsv"
test -d "$ORIGINAL" && test -f "$ORIGINAL/MAIN.EXE"
test -f "$DRIVER" && test ! -L "$DRIVER"
test -f "$INVENTORY" && test -f "$ROOT/tools/capture_original_music.py"
test -d "$ROOT/workplace/out" && test "$(stat -c %u:%g "$ROOT/workplace/out")" = 1000:1000
ORIGINAL="$(cd "$ORIGINAL" && pwd -P)"
DRIVER="$(cd "$(dirname "$DRIVER")" && pwd -P)/$(basename "$DRIVER")"
DISABLED="${HR_AUDIO_DISABLE_DRIVER:-0}"
case "$DISABLED" in 0|1) ;; *) echo "HR_AUDIO_DISABLE_DRIVER 需為 0 或 1" >&2; exit 2 ;; esac
MOUNTS=(-v "$ORIGINAL:/orig:ro" -v "$DRIVER:/driver/CTMIDI-S.DRV:ro"
        -v "$INVENTORY:/source-inventory.tsv:ro" -v "$ROOT/tools:/scripts:ro"
        -v "$ROOT/workplace/out:/outputs")
OPTIONS=()
if [ -n "${HR_AUDIO_CONTROL_DIR:-}" ]; then
  test "$DISABLED" = 0
  CONTROL="$HR_AUDIO_CONTROL_DIR"
  test -d "$CONTROL" && test -f "$CONTROL/receipt.json" && test -f "$CONTROL/native.conf" && test -d "$CONTROL/capture"
  CONTROL="$(cd "$CONTROL" && pwd -P)"
  MOUNTS+=(-v "$CONTROL:/control:ro")
  OPTIONS+=(-e HR_AUDIO_CONTROL_DIR=/control)
fi
IMAGE=psychicwar-dosboxx:source-5fcf624b-r1
docker image inspect "$IMAGE" >/dev/null
exec timeout 3m docker run --rm --name "hr-original-music-$NAME" \
  --user 1000:1000 --network none --memory 2g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  "${MOUNTS[@]}" "${OPTIONS[@]}" \
  -e "HR_AUDIO_NAME=$NAME" -e "HR_AUDIO_RECORD_SECONDS=${HR_AUDIO_RECORD_SECONDS:-65}" \
  -e "HR_AUDIO_DISABLE_DRIVER=$DISABLED" --entrypoint python3 "$IMAGE" \
  /scripts/capture_original_music.py
