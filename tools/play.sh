#!/usr/bin/env bash
# 桌面前端 hr-play（workplace/dosgolem/apps/hr/play）的建置與驗收，一律在 Docker 內。
#
#   tools/play.sh build            建 Linux amd64 執行檔到 workplace/out/bin/hr-play
#   tools/play.sh test             跑 apps/hr 的測試（含 runtime、patch；原版以 /orig/orig 唯讀掛入）
#   tools/play.sh test-play        前端（apps/hr/play）的測試
#   tools/play.sh build-cross      前端在 windows/amd64 能編譯（CGO_ENABLED=0；macOS 要用 osxcross，見 package.sh），補 go.mod 的 oto
#   tools/play.sh test-diag        docs/spec/005 的診斷測試（HR_TEST_RUN 指定樣式，HR_RACE=1 加 -race）
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
EXTRA=()
run() { # $1 = 容器內的 sh 指令
  timeout "${HR_PLAY_TIMEOUT:-20m}" docker run --rm --network none \
    --memory "${HR_PLAY_MEM:-4g}" --cpus "${HR_PLAY_CPUS:-2}" --pids-limit 512 \
    --log-opt max-size=10m --log-opt max-file=3 \
    -u "$(id -u):$(id -g)" \
    -v "$DG:/src" -v "$OUT:/out" -v "$ROOT/workplace/orig:/orig/orig:ro" -v "$ROOT/workplace/gocache:/gocache" "${EXTRA[@]}" \
    -e HOME=/tmp -e GOCACHE=/gocache -e GOFLAGS=-mod=mod -e GOPROXY=off -e GOSUMDB=off -e CGO_ENABLED="${HR_CGO:-1}" \
    -e HR_VERSION="${HR_VERSION:-dev}" \
    -w /src "$IMAGE" sh -c "$1"
}
case "$CMD" in
  build)
    run 'cd apps/hr/play && go build -ldflags "-s -w -X main.version=$HR_VERSION" -o /out/bin/hr-play . && ls -la /out/bin/hr-play' ;;
  test)
    run 'cd /src && GOFLAGS=-mod=mod go test -count=1 ./apps/hr/patch/ ./apps/hr/runtime/' ;;
  test-diag)
    # docs/spec/005 的診斷測試。狀態檔場景：戰鬥佈陣前的狀態檔（HR_BENCH_STATE）與 docs/re/009 的取樣狀態檔（HR_SOAK_STATE），
    # 缺檔就 skip。HR_TEST_RUN 指定 -run 樣式，HR_RACE=1 加 -race（需 cgo）。
    SN="$OUT/explore2/nodes"; SK="$OUT/soak-s0"
    test -f "$SN/n00071.state" && EXTRA+=(-v "$SN:/state/explore:ro" -e HR_BENCH_STATE=/state/explore/n00071.state)
    test -f "$SK/ck-001500000000.state" && EXTRA+=(-v "$SK:/state/soak:ro" -e HR_SOAK_STATE=/state/soak/ck-001500000000.state)
    [ -n "${HR_BENCH_OVERHEAD:-}" ] && EXTRA+=(-e HR_BENCH_OVERHEAD=1)
    run "cd /src && GOFLAGS=-mod=mod go test -count=1 ${HR_RACE:+-race} -run '${HR_TEST_RUN:-.}' -v ./apps/hr/runtime/ 2>&1 | grep -E '^(=== RUN|--- |PASS|FAIL|ok|panic|\\s+[a-z_]+\\.go:[0-9]+:)' | grep -v '=== RUN'" ;;
  gen-charset)
    # 產生前端 UI 字型子集用的字元表（tools/gen_ui_fonts.sh 呼叫）；HR_GEN_CHARSET 是容器內的輸出目錄
    EXTRA+=(-e "HR_GEN_CHARSET=${HR_GEN_CHARSET:?HR_GEN_CHARSET}")
    run 'set -e; mkdir -p /tmp/.X11-unix; Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 & XPID=$!; sleep 2; export DISPLAY=:99; cd apps/hr/play; go test -count=1 -run TestGenCharsets -v . 2>&1 | tail -25; kill $XPID 2>/dev/null || true' ;;
  build-cross)
    # 前端在 Windows 目標上能編譯（docs/spec/007 第 5.3 節：非 Linux 後端用 oto）。macOS 需要 osxcross（tools/package.sh macos），這裡編不了。
    # -mod=mod 會把 oto 補進 go.mod 與 go.sum（離線，來自本機模組快取），補完要提交並重產 engine/patches/。
    run 'cd apps/hr/play && for t in windows/amd64; do os=${t%/*}; arch=${t#*/}; echo "== $t"; CGO_ENABLED=0 GOOS=$os GOARCH=$arch go vet . && CGO_ENABLED=0 GOOS=$os GOARCH=$arch go build -o /dev/null . && echo ok; done' ;;
  test-play)
    # 前端（apps/hr/play，獨立模組）的測試：保留鍵、診斷目錄顯示等純函式
    [ -n "${HR_RACE:-}" ] && EXTRA+=(-e HR_RACE=1)
    [ -n "${HR_VERBOSE:-}" ] && EXTRA+=(-e HR_VERBOSE=1)
    [ -n "${HR_TEST_RUN:-}" ] && EXTRA+=(-e "HR_TEST_RUN=${HR_TEST_RUN}")
    run 'set -e; mkdir -p /tmp/.X11-unix; Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 & XPID=$!; sleep 2; export DISPLAY=:99; cd apps/hr/play; go vet ./...; go test -count=1 ${HR_RACE:+-race} ${HR_VERBOSE:+-v} ${HR_TEST_RUN:+-run "$HR_TEST_RUN"} ./...; kill $XPID 2>/dev/null || true' ;;
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
  gui-diag)
    # docs/spec/005 第 8 節：Xvfb 內啟動視窗、點新遊戲、按 Ctrl+D，確認使用者資料目錄的 crash/ 出現 -manual 診斷
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
      xdotool mousemove 640 342
      sleep 1
      xdotool click 1
      sleep 20
      xdotool keydown ctrl; sleep 0.4; xdotool keydown d; sleep 0.6; xdotool keyup d; sleep 0.3; xdotool keyup ctrl
      sleep 6
      xdotool key F1
      sleep 1
      import -window root /out/gui-diag-help.png
      kill $PID 2>/dev/null || true
      kill $XPID 2>/dev/null || true
      echo "== crash 目錄"; ls -la /tmp/.config/high_reward/crash/ || true
      d=$(ls -d /tmp/.config/high_reward/crash/*-manual* 2>/dev/null | head -1)
      echo "== $d"; ls -la "$d" || true
      head -12 "$d/info.txt" || true
      echo "== play.log"; tail -3 /tmp/.config/high_reward/play.log || true
      echo "== stderr"; tail -5 /tmp/play.log' ;;
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
