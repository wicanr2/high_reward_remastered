#!/usr/bin/env bash
# 桌面前端 hr-play（workplace/dosgolem/apps/hr/play）的建置與驗收，一律在 Docker 內。
#
#   tools/play.sh build            建 Linux amd64 執行檔到 workplace/out/bin/hr-play
#   tools/play.sh test             跑 apps/hr 的測試（含 runtime、patch；原版以 /orig/orig 唯讀掛入）
#   tools/play.sh smoke            不開視窗（hr-smoke）重現 docs/re/008 的收據 A、B，輸出 workplace/out/smoke-{a,b}.png 與其 SHA-256
#   tools/play.sh gui              Xvfb 內啟動視窗、xdotool 點標題選單的新遊戲、截圖（workplace/out/gui-*.png）
#   tools/play.sh gui-error        找不到原版時的錯誤視窗（workplace/out/gui-error.png）
#
# 映像：本機已有的 eob-remake-go:1.26.7-ebiten2.9.9（Go、ebiten 2.9.9 模組快取、X11／GL 標頭檔、Xvfb、xdotool、import）。
# 用 HR_GO_IMAGE 覆蓋。預設 --network none；go.sum 由本機模組快取產生（GOSUMDB=off，未經校驗資料庫核對）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
DG="$ROOT/workplace/dosgolem"
OUT="$ROOT/workplace/out"
test -d "$DG/apps/hr/play" || { echo "缺 workplace/dosgolem/apps/hr/play" >&2; exit 1; }
test -d "$ROOT/workplace/orig" || { echo "缺 workplace/orig" >&2; exit 1; }
mkdir -p "$OUT/bin" "$ROOT/workplace/gocache"
CMD="${1:-}"
run() { # $1 = 容器內的 sh 指令
  timeout "${HR_PLAY_TIMEOUT:-20m}" docker run --rm --network none \
    --memory "${HR_PLAY_MEM:-4g}" --cpus "${HR_PLAY_CPUS:-2}" --pids-limit 512 \
    --log-opt max-size=10m --log-opt max-file=3 \
    -u "$(id -u):$(id -g)" \
    -v "$DG:/src" -v "$OUT:/out" -v "$ROOT/workplace/orig:/orig/orig:ro" -v "$ROOT/workplace/gocache:/gocache" \
    -e HOME=/tmp -e GOCACHE=/gocache -e GOFLAGS=-mod=mod -e GOPROXY=off -e GOSUMDB=off -e CGO_ENABLED="${HR_CGO:-1}" \
    -e HR_VERSION="${HR_VERSION:-dev}" \
    -w /src "$IMAGE" sh -c "$1"
}
case "$CMD" in
  build)
    run 'cd apps/hr/play && go build -ldflags "-s -w -X main.version=$HR_VERSION" -o /out/bin/hr-play . && ls -la /out/bin/hr-play' ;;
  test)
    run 'cd /src && GOFLAGS=-mod=mod go test -count=1 ./apps/hr/patch/ ./apps/hr/runtime/' ;;
  smoke)
    run 'cd /src && go run ./apps/hr/cmd/hr-smoke -orig /orig/orig -steps 30000000 -png /out/smoke-a.png && go run ./apps/hr/cmd/hr-smoke -orig /orig/orig -steps 90000000 -click 35000000:312:211 -png /out/smoke-b.png' ;;
  gui)
    run 'set -e
      cd apps/hr/play
      go build -o /out/bin/hr-play .
      mkdir -p /tmp/.X11-unix
      Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
      XPID=$!
      sleep 2
      export DISPLAY=:99
      /out/bin/hr-play -orig /orig/orig -saves /out/gui-saves -scale 2 >/tmp/play.log 2>&1 &
      PID=$!
      sleep 15
      import -window root /out/gui-title.png
      xdotool mousemove 640 342
      sleep 1
      xdotool click 1
      sleep 20
      import -window root /out/gui-newgame.png
      xdotool key F1
      sleep 1
      import -window root /out/gui-help.png
      kill $PID 2>/dev/null || true
      kill $XPID 2>/dev/null || true
      tail -5 /tmp/play.log' ;;
  gui-error)
    run 'set -e
      cd apps/hr/play
      go build -o /out/bin/hr-play .
      mkdir -p /tmp/.X11-unix
      Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
      XPID=$!
      sleep 2
      export DISPLAY=:99
      /out/bin/hr-play -orig /nonexistent >/tmp/play.log 2>&1 &
      PID=$!
      sleep 6
      import -window root /out/gui-error.png
      kill $PID 2>/dev/null || true
      kill $XPID 2>/dev/null || true
      cat /tmp/play.log' ;;
  *) sed -n 2,9p "$0" >&2; exit 2 ;;
esac
