#!/usr/bin/env bash
# 實際錄影到 workplace/out/<名稱>，control.json 只提供正常按鍵／滑鼠操作。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${1:?請指定錄影工作名稱}"
[[ "$NAME" =~ ^[a-zA-Z0-9_-]+$ ]]
OUT="$ROOT/workplace/out/$NAME"
BIN="${HR_CAPTURE_BINARY_DIR:-$ROOT/workplace/out/bin}"
test -d "$ROOT/workplace/out" && test -d "$BIN" && test -f "$BIN/hr-play"
test -d "$ROOT/workplace/orig" && test -d "$ROOT/hd" && test -d "$ROOT/hd-ai" && test -d "$ROOT/l10n"
test -f "$ROOT/tools/capture_promo.py"
IMAGE="${HR_CAPTURE_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
docker image inspect "$IMAGE" >/dev/null
# 由容器建立輸出目錄，以最終 UID 寫入。
exec timeout 20m docker run --rm --name "hr-promo-live-$NAME" \
  --user "$(id -u):$(id -g)" --network none --memory 4g --cpus 4 --pids-limit 512 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT/workplace/out:/outputs" -v "$BIN:/binary:ro" \
  -v "$ROOT/workplace/orig:/orig:ro" -v "$ROOT/hd:/hd:ro" -v "$ROOT/hd-ai:/hd-ai:ro" \
  -v "$ROOT/l10n:/l10n:ro" -v "$ROOT/tools:/scripts:ro" \
  -e "HR_CAPTURE_NAME=$NAME" -e "HR_CAPTURE_LANG=${HR_CAPTURE_LANG:-zh-TW}" --entrypoint sh "$IMAGE" -c \
  'test ! -e "/outputs/$HR_CAPTURE_NAME"; mkdir "/outputs/$HR_CAPTURE_NAME"; exec python3 /scripts/capture_promo.py'
