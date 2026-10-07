#!/usr/bin/env bash
# AppImage 的啟動驗收：Xvfb 內啟動，原版目錄以唯讀掛在 .AppImage 旁的 original，
# 冷建置 identity 語言包並保存 manifest，xdotool 點新遊戲，截圖到 workplace/out/。
# 容器內沒有 FUSE，用 APPIMAGE_EXTRACT_AND_RUN=1。
#   tools/pkg/verify_appimage.sh dist-all/HighReward-<版本>-x86_64.AppImage
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AI="$(cd "$(dirname "${1:?AppImage 路徑}")" && pwd)/$(basename "$1")"
IMAGE="${HR_GO_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
test -f "$AI" || { echo "缺 $AI" >&2; exit 1; }
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig" >&2; exit 1; }
test -d "$ROOT/workplace/out" || { echo "缺 workplace/out" >&2; exit 1; }
HDMOUNT=()
# HR_HD_DIR（workplace 內、不含符號連結的 HD 目錄）有設就掛到 .AppImage 旁的 hd，驗收 HD 疊層
if [ -n "${HR_HD_DIR:-}" ]; then
  test -d "$HR_HD_DIR" || { echo "缺 HD 目錄 $HR_HD_DIR" >&2; exit 1; }
  HDMOUNT=(-v "$(cd "$HR_HD_DIR" && pwd):/work/hd:ro")
fi
SHOT="${HR_SHOT_PREFIX:-pkg-appimage}"
timeout 10m docker run --rm --name "hr-appimage-verify-$$" --network none --memory 3g --cpus 2 --pids-limit 512 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$AI:/work/HR.AppImage:ro" -v "$ROOT/workplace/orig:/work/original:ro" -v "$ROOT/workplace/out:/out" "${HDMOUNT[@]}" -e SHOT="$SHOT" \
  -e HOME=/tmp -w /work "$IMAGE" sh -c '
    set -e
    mkdir -p /tmp/.X11-unix
    Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
    XPID=$!
    sleep 2
    export DISPLAY=:99 APPIMAGE_EXTRACT_AND_RUN=1
    # APPIMAGE 指向 /work/HR.AppImage 旁邊的 original：用原位置執行
    ./HR.AppImage -ingame-lang identity >/tmp/play.log 2>&1 &
    PID=$!
    trap "kill $PID $XPID 2>/dev/null || true" EXIT
    i=0
    until grep -q "ingame: pack-active" /tmp/play.log; do
      kill -0 "$PID" 2>/dev/null || { cat /tmp/play.log; exit 1; }
      test "$i" -lt 60 || { cat /tmp/play.log; exit 1; }
      sleep 2; i=$((i + 1))
    done
    grep -q "ingame: pack-ready .*reused=false mode=identity code=identity adopted=0" /tmp/play.log
    mf=$(find /tmp -type f -name manifest.json -print -quit)
    test -f "$mf"
    cp "$mf" "/out/${SHOT}-identity-manifest.json"
    cp /tmp/play.log "/out/${SHOT}-identity.log"
    i=0; visible=0
    while [ "$i" -lt 30 ]; do
      import -window root "/out/${SHOT}-title.png"
      colors=$(identify -format %k "/out/${SHOT}-title.png")
      if [ "$colors" -gt 1 ]; then visible=1; break; fi
      kill -0 "$PID" 2>/dev/null || break
      sleep 1; i=$((i + 1))
    done
    test "$visible" -eq 1
    xdotool mousemove 640 342; sleep 1; xdotool click 1; sleep 25
    import -window root /out/${SHOT}-newgame.png
    grep "ingame:" /tmp/play.log || true
    sha256sum "/out/${SHOT}-identity-manifest.json"'
