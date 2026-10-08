#!/usr/bin/env bash
# 實際錄影到 workplace/out/<名稱>，control.json 只提供正常按鍵／滑鼠操作。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${1:?請指定錄影工作名稱}"
[[ "$NAME" =~ ^[a-zA-Z0-9_-]+$ ]]
OUT="$ROOT/workplace/out/$NAME"
test -d "$ROOT/workplace/out"
test "$(stat -c %u:%g "$ROOT/workplace/out")" = "$(id -u):$(id -g)"
test -f "$ROOT/tools/capture_promo.py"
MOUNTS=(-v "$ROOT/workplace/out:/outputs" -v "$ROOT/tools:/scripts:ro")
OPTIONS=()
if [ -n "${HR_CAPTURE_BUNDLE_DIR:-}" ]; then
  BUNDLE="$HR_CAPTURE_BUNDLE_DIR"
  test -d "$BUNDLE" && test -f "$BUNDLE/AppRun" && test -x "$BUNDLE/AppRun"
  test -f "$BUNDLE/usr/bin/hr-play" && test -x "$BUNDLE/usr/bin/hr-play"
  for resource in original hd hd-ai l10n; do test -d "$BUNDLE/usr/bin/$resource"; done
  BUNDLE="$(cd "$BUNDLE" && pwd -P)"
  MOUNTS+=(-v "$BUNDLE:/bundle:ro")
  OPTIONS+=(-e HR_CAPTURE_BUNDLE_DIR=/bundle)
  ARTIFACT="${HR_CAPTURE_ARTIFACT:-$BUNDLE}"
else
  BIN="${HR_CAPTURE_BINARY_DIR:-$ROOT/workplace/out/bin}"
  test -d "$BIN" && test -f "$BIN/hr-play"
  BIN="$(cd "$BIN" && pwd -P)"
  test -d "$ROOT/workplace/orig" && test -d "$ROOT/hd" && test -d "$ROOT/hd-ai" && test -d "$ROOT/l10n"
  MOUNTS+=(-v "$BIN:/binary:ro" -v "$ROOT/workplace/orig:/orig:ro"
           -v "$ROOT/hd:/hd:ro" -v "$ROOT/hd-ai:/hd-ai:ro" -v "$ROOT/l10n:/l10n:ro")
  ARTIFACT="${HR_CAPTURE_ARTIFACT:-$BIN/hr-play}"
fi
if [ -n "${HR_CAPTURE_CONTROL_FILE:-}" ]; then
  test -f "$HR_CAPTURE_CONTROL_FILE" && test ! -L "$HR_CAPTURE_CONTROL_FILE"
  CONTROL="$(cd "$(dirname "$HR_CAPTURE_CONTROL_FILE")" && pwd -P)/$(basename "$HR_CAPTURE_CONTROL_FILE")"
  MOUNTS+=(-v "$CONTROL:/control.json:ro")
  OPTIONS+=(-e HR_CAPTURE_CONTROL_FILE=/control.json)
fi
THEME="${HR_CAPTURE_THEME:-original}"
case "$THEME" in original|hd|ai) ;; *) echo "HR_CAPTURE_THEME 需為 original、hd 或 ai" >&2; exit 2 ;; esac
IMAGE="${HR_CAPTURE_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
docker image inspect "$IMAGE" >/dev/null
# 由容器建立輸出目錄，以最終 UID 寫入。
exec timeout 20m docker run --rm --name "hr-promo-live-$NAME" \
  --user "$(id -u):$(id -g)" --network none --memory 4g --cpus 4 --pids-limit 512 \
  --log-opt max-size=10m --log-opt max-file=3 \
  "${MOUNTS[@]}" "${OPTIONS[@]}" \
  -e "HR_CAPTURE_NAME=$NAME" -e "HR_CAPTURE_LANG=${HR_CAPTURE_LANG:-zh-TW}" \
  -e "HR_CAPTURE_THEME=$THEME" -e "HR_CAPTURE_ARTIFACT=$ARTIFACT" --entrypoint sh "$IMAGE" -c \
  'test ! -e "/outputs/$HR_CAPTURE_NAME"; mkdir "/outputs/$HR_CAPTURE_NAME"; exec python3 /scripts/capture_promo.py'
