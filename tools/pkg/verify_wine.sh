#!/usr/bin/env bash
# Windows zip 的啟動驗收：在 Docker 內解開 zip，Wine 加 Xvfb 啟動 hr-play.exe，
# 冷建置 identity 語言包，保存 manifest，並截取有內容的畫面。
# Wine 與軟體繪圖下很慢；此驗收不代表速度。
#   tools/pkg/verify_wine.sh dist-all/HighReward-<版本>-win64.zip
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ZIP="$(cd "$(dirname "${1:?zip 路徑}")" && pwd)/$(basename "$1")"
WINE_IMAGE="${HR_WINE_IMAGE:-psychicwar-wine:latest}"
PY_IMAGE="${HR_HD_IMAGE:-yuan-analysis:1}"
test -f "$ZIP" || { echo "缺 $ZIP" >&2; exit 1; }
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig" >&2; exit 1; }
OUT="$ROOT/workplace/out"
test -d "$OUT" || { echo "缺 $OUT" >&2; exit 1; }
HDMOUNT=(); HDARG=""
# HR_HD_DIR（workplace 內、不含符號連結的 HD 目錄）有設就掛到 /hd 並以 -hd 啟動，驗收 Windows 包的 HD 路徑
if [ -n "${HR_HD_DIR:-}" ]; then
  test -d "$HR_HD_DIR" || { echo "缺 HD 目錄 $HR_HD_DIR" >&2; exit 1; }
  HDMOUNT=(-v "$(cd "$HR_HD_DIR" && pwd):/hd:ro"); HDARG="-hd Z:\\hd"
fi
SHOT="${HR_SHOT_PREFIX:-pkg-wine}"
WORK="$OUT/wine-pkg-$$"
test ! -e "$WORK" || { echo "輸出目錄已存在：$WORK" >&2; exit 1; }
timeout 3m docker run --rm --name "hr-wine-unpack-$$" --network none --memory 1g --cpus 1 --pids-limit 64 --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" -v "$ZIP:/pkg.zip:ro" -v "$OUT:/out" -e WORKDIR="$(basename "$WORK")" "$PY_IMAGE" \
  sh -c 'mkdir "/out/$WORKDIR" && python3 -m zipfile -e /pkg.zip "/out/$WORKDIR"'
timeout 15m docker run --rm --name "hr-wine-verify-$$" --network none --memory 3g --cpus 2 --pids-limit 512 --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" --tmpfs "/wine:rw,exec,uid=$(id -u),gid=$(id -g),size=1g" \
  -v "$WORK:/pkg:ro" -v "$ROOT/workplace/orig:/orig:ro" -v "$OUT:/out" "${HDMOUNT[@]}" -e HDARG="$HDARG" -e SHOT="$SHOT" \
  -e HOME=/wine -e WINEPREFIX=/wine/prefix -e WINEDEBUG=-all -w /pkg "$WINE_IMAGE" sh -c '
    EXE=$(find /pkg -mindepth 2 -maxdepth 2 -type f -name hr-play.exe -print -quit)
    test -n "$EXE" || { echo "zip 內找不到 hr-play.exe" >&2; exit 1; }
    mkdir -p /tmp/.X11-unix
    Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
    XPID=$!
    sleep 2
    export DISPLAY=:99
    wine "$EXE" -orig Z:\\orig -saves Z:\\wine\\saves -scale 1 -ingame-lang identity $HDARG >/tmp/wine.log 2>&1 &
    PID=$!
    trap "kill $PID $XPID 2>/dev/null || true" EXIT
    i=0; visible=0
    while [ "$i" -lt 40 ]; do
      sleep 3
      if grep -q "ingame: pack-active" /tmp/wine.log; then
        wid=$(xwininfo -root -tree | grep -E "hr-play.exe.*[0-9]{3,4}x[0-9]{3,4}" | sed -nE "s/^[[:space:]]*(0x[0-9a-fA-F]+).*/\\1/p" | head -1)
        if [ -n "$wid" ] && import -window "$wid" "/out/${SHOT}-title.png" 2>/dev/null; then
          colors=$(identify -format %k "/out/${SHOT}-title.png")
          geometry=$(identify -format %wx%h "/out/${SHOT}-title.png")
          if [ "$geometry" = 640x400 ] && [ "$colors" -gt 1 ]; then visible=1; break; fi
        fi
      fi
      kill -0 "$PID" 2>/dev/null || break
      i=$((i + 1))
    done
    cp /tmp/wine.log "/out/${SHOT}-identity.log"
    grep "ingame:" /tmp/wine.log || true
    grep -q "ingame: pack-ready .*reused=false mode=identity code=identity adopted=0" /tmp/wine.log
    grep -q "ingame: pack-active" /tmp/wine.log
    test "$visible" -eq 1
    mf=$(find "$WINEPREFIX" -type f -name manifest.json -print -quit)
    test -f "$mf"
    cp "$mf" "/out/${SHOT}-identity-manifest.json"
    sha256sum "/out/${SHOT}-identity-manifest.json"'
echo "輸出 workplace/out/${SHOT}-title.png、${SHOT}-identity-manifest.json"
