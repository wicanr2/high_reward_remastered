#!/usr/bin/env bash
# AppImage 的啟動驗收：Xvfb 內啟動，原版目錄以唯讀掛在 .AppImage 旁的 original，
# xdotool 點新遊戲，截圖到 workplace/out/pkg-appimage-*.png。容器內沒有 FUSE，用 APPIMAGE_EXTRACT_AND_RUN=1。
#   tools/pkg/verify_appimage.sh dist-all/HighReward-<版本>-x86_64.AppImage
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AI="$(cd "$(dirname "${1:?AppImage 路徑}")" && pwd)/$(basename "$1")"
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
test -f "$AI" || { echo "缺 $AI" >&2; exit 1; }
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig" >&2; exit 1; }
mkdir -p "$ROOT/workplace/out"
timeout 10m docker run --rm --network none --memory 3g --cpus 2 --pids-limit 512 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$AI:/work/HR.AppImage:ro" -v "$ROOT/workplace/orig:/work/original:ro" -v "$ROOT/workplace/out:/out" \
  -e HOME=/tmp -w /work "$IMAGE" sh -c '
    set -e
    mkdir -p /tmp/.X11-unix
    Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
    XPID=$!
    sleep 2
    export DISPLAY=:99 APPIMAGE_EXTRACT_AND_RUN=1
    cp /work/HR.AppImage /tmp/HR.AppImage
    # APPIMAGE 指向 /work/HR.AppImage 旁邊的 original：用原位置執行
    ./HR.AppImage >/tmp/play.log 2>&1 &
    PID=$!
    sleep 15
    import -window root /out/pkg-appimage-title.png
    xdotool mousemove 640 342; sleep 1; xdotool click 1; sleep 25
    import -window root /out/pkg-appimage-newgame.png
    kill $PID 2>/dev/null || true; kill $XPID 2>/dev/null || true
    tail -4 /tmp/play.log'
