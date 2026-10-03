#!/usr/bin/env bash
# Windows zip 的啟動驗收：在 Docker 內解開 zip，Wine 加 Xvfb 啟動 hr-play.exe，截圖標題畫面。
# Wine 與軟體繪圖下很慢，只證明能啟動並顯示標題，不代表速度。
#   tools/pkg/verify_wine.sh dist-all/HighReward-<版本>-win64.zip
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ZIP="$(cd "$(dirname "${1:?zip 路徑}")" && pwd)/$(basename "$1")"
WINE_IMAGE="${HR_WINE_IMAGE:-psychicwar-wine:latest}"
PY_IMAGE="${HR_HD_IMAGE:-yuan-analysis:1}"
test -f "$ZIP" || { echo "缺 $ZIP" >&2; exit 1; }
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig" >&2; exit 1; }
OUT="$ROOT/workplace/out"
HDMOUNT=(); HDARG=""
# HR_HD_DIR（workplace 內、不含符號連結的 HD 目錄）有設就掛到 /hd 並以 -hd 啟動，驗收 Windows 包的 HD 路徑
if [ -n "${HR_HD_DIR:-}" ]; then HDMOUNT=(-v "$(cd "$HR_HD_DIR" && pwd):/hd:ro"); HDARG="-hd Z:\\hd"; fi
SHOT="${HR_SHOT_PREFIX:-pkg-wine}"
rm -rf "$OUT/wine-pkg" && mkdir -p "$OUT/wine-pkg"
docker run --rm --network none --memory 1g --cpus 1 --pids-limit 64 --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" -v "$ZIP:/pkg.zip:ro" -v "$OUT/wine-pkg:/x" "$PY_IMAGE" python3 -m zipfile -e /pkg.zip /x
EXE="$(cd "$OUT/wine-pkg" && ls -d */hr-play.exe | head -1)"
test -n "$EXE" || { echo "zip 內找不到 hr-play.exe" >&2; exit 1; }
timeout 15m docker run --rm --network none --memory 3g --cpus 2 --pids-limit 512 --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" --tmpfs "/wine:rw,exec,uid=$(id -u),gid=$(id -g),size=1g" \
  -v "$OUT/wine-pkg:/pkg:ro" -v "$ROOT/workplace/orig:/orig:ro" -v "$OUT:/out" "${HDMOUNT[@]}" -e HDARG="$HDARG" -e SHOT="$SHOT" \
  -e HOME=/wine -e WINEPREFIX=/wine/prefix -e WINEDEBUG=-all -e EXE="$EXE" -w /pkg "$WINE_IMAGE" sh -c '
    mkdir -p /tmp/.X11-unix
    Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
    XPID=$!
    sleep 2
    export DISPLAY=:99
    wine "/pkg/$EXE" -orig Z:\\orig -saves Z:\\wine\\saves $HDARG >/tmp/wine.log 2>&1 &
    PID=$!
    sleep 90
    import -window root /out/${SHOT}-title.png
    kill $PID 2>/dev/null || true; kill $XPID 2>/dev/null || true
    tail -5 /tmp/wine.log'
echo "輸出 workplace/out/${SHOT}-title.png"
