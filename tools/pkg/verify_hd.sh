#!/usr/bin/env bash
# HD 疊層的前端驗收：Xvfb 內啟動 hr-play，載入指定的 HD 目錄，點新遊戲後截圖。
#   tools/pkg/verify_hd.sh <hr-play 執行檔（workplace/out 內）> <HD 目錄（workplace 內）> <輸出前綴>
# 例：tools/pkg/verify_hd.sh workplace/out/hr-play-hd workplace/hd-stage workplace/out/hd/gui
# 輸出的 PNG 是原版美術的衍生物，只放 workplace/。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="$(cd "$(dirname "${1:?hr-play 執行檔}")" && pwd)/$(basename "$1")"
HDD="$(cd "${2:?HD 目錄}" && pwd)"
PREFIX="${3:?輸出前綴}"
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
test -f "$BIN" || { echo "缺 $BIN" >&2; exit 1; }
test -f "$HDD/catalog.tsv" || { echo "缺 $HDD/catalog.tsv" >&2; exit 1; }
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig" >&2; exit 1; }
case "$HDD" in "$ROOT/workplace"/*) ;; *) echo "HD 目錄必須在 workplace 內" >&2; exit 1 ;; esac
case "$PREFIX" in /*) ;; *) PREFIX="$ROOT/$PREFIX" ;; esac
mkdir -p "$(dirname "$PREFIX")"
OUTDIR="$(dirname "$PREFIX")"; NAME="$(basename "$PREFIX")"
timeout 10m docker run --rm --network none --memory 3g --cpus 2 --pids-limit 512 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$BIN:/work/hr-play:ro" -v "$ROOT/workplace:/work/ws:ro" -v "$OUTDIR:/out" \
  -e HOME=/tmp -e NAME="$NAME" -e HDREL="${HDD#"$ROOT/workplace/"}" -w /work "$IMAGE" sh -c '
    set -e
    mkdir -p /tmp/.X11-unix /tmp/saves
    Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
    XPID=$!
    sleep 2
    export DISPLAY=:99
    /work/hr-play -orig /work/ws/orig -hd "/work/ws/$HDREL" -saves /tmp/saves >/tmp/play.log 2>&1 &
    PID=$!
    sleep 20
    import -window root "/out/${NAME}-title.png"
    xdotool mousemove 640 342; sleep 1; xdotool click 1; sleep 25
    import -window root "/out/${NAME}-newgame.png"
    kill $PID 2>/dev/null || true; kill $XPID 2>/dev/null || true
    tail -6 /tmp/play.log'
