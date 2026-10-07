#!/usr/bin/env bash
# 桌面前端 hr-play（workplace/dosgolem/apps/hr/play）的建置與驗收，一律在 Docker 內。
#
#   tools/play.sh build            建 Linux amd64 執行檔到 workplace/out/bin/hr-play
#   tools/play.sh test             跑 apps/hr 的測試（含 runtime、patch；原版以 /orig/orig 唯讀掛入）
#   tools/play.sh test-play        前端（apps/hr/play）的測試
#   tools/play.sh test-hd          apps/hr/hd 的 vet 與測試（-race，需 cgo；docs/spec/006 第 10 節；HR_TEST_RUN 指定 -run，HR_VERBOSE=1 加 -v）
#   tools/play.sh build-cross      前端在 windows/amd64 能編譯（CGO_ENABLED=0；macOS 要用 osxcross，見 package.sh），補 go.mod 的 oto
#   tools/play.sh test-diag        docs/spec/005 的診斷測試（HR_TEST_RUN 指定樣式，HR_RACE=1 加 -race）
#   tools/play.sh smoke            不開視窗（hr-smoke）重現 docs/re/008 的收據 A、B，輸出 workplace/out/smoke-{a,b}.png 與其 SHA-256
#   tools/play.sh gui              Xvfb 內啟動視窗、xdotool 點標題選單的新遊戲、截圖（workplace/out/gui-*.png）
#   tools/play.sh gui-error        找不到原版時的錯誤視窗（workplace/out/gui-error.png）
#   tools/play.sh gui-lang         docs/spec/006 第 10 節端對端：F4 循環五種語言的 F1 面板截圖（workplace/out/gui-lang-*.png，含原版畫面，不進 docs/）
#   tools/play.sh gui-theme        docs/spec/006 第 10 節端對端：F2 切換 original 與 HD（需要 hd/；掛 -v hd:/hd:ro；workplace/out/gui-theme-*.png）
#   tools/play.sh gui-ingame       docs/spec/008 第 3.8 節端對端：F1「遊戲內文字」一行與 F4 提示（預設、-ingame-lang identity、F4 一圈、竄改包、違規譯文表；
#                                  合法的 accepted 譯文表；workplace/out/l1-wire2/gui-ingame-*.png，含原版畫面，不進 docs/；資料目錄在 /out/l1-wire2/home，不寫 ~）
#   tools/play.sh gui-lang-cmp     比對兩組 gui-lang 截圖（HR_CMP_OLD、HR_CMP_NEW：/out 之下的目錄）的 F1 面板，逐行列出差異
#
# 映像：本機已有的 eob-remake-go:1.26.7-ebiten2.9.9（Go、ebiten 2.9.9 模組快取、X11／GL 標頭檔、Xvfb、xdotool、import）。
# 用 HR_GO_IMAGE 覆蓋。預設 --network none；go.sum 由本機模組快取產生（GOSUMDB=off，未經校驗資料庫核對）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${HR_GO_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
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
  test-hd)
    # apps/hr/hd（根模組，不需 Xvfb、原版與 hd/ 素材）的 vet 與 -race 測試：Compose 快照、Release 與 Compose 並行、
    # CheckTheme、ErrorStats、Preload 取消等（docs/spec/006 第 10 節）。-race 需要 cgo（HR_CGO 預設 1）。
    [ -n "${HR_VERBOSE:-}" ] && EXTRA+=(-e HR_VERBOSE=1)
    [ -n "${HR_TEST_RUN:-}" ] && EXTRA+=(-e "HR_TEST_RUN=${HR_TEST_RUN}")
    run 'set -e; cd /src; go vet ./apps/hr/hd/; go test -count=1 -race ${HR_VERBOSE:+-v} ${HR_TEST_RUN:+-run "$HR_TEST_RUN"} ./apps/hr/hd/' ;;
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
  gui-lang)
    # docs/spec/006 第 10 節的端對端：Xvfb、--cpus 2（預設）。HR_TEST_FREEZE_UI=1：統計欄位固定、toast 與載入進度不繪製、面板底色不透明。
    # 先量原版標題畫面間隔數秒的兩張截圖是否相同（游標與動畫），再按 F1 開面板、按 F4 循環：五張 F1 截圖只比對面板區域，
    # 兩兩不同，第六次（第五次 F4 之後）回到起點與第一張相同。比對像素簽章（convert 的 %#），不比檔案雜湊（PNG 帶 date 中繼資料）。
    GUI_BODY=$(cat <<'EOS'
set -e
for c in convert compare identify xdotool import Xvfb; do command -v "$c" >/dev/null 2>&1 || { echo "缺工具：$c" >&2; exit 1; }; done
cd /src/apps/hr/play
go build -o /out/bin/hr-play .
mkdir -p /tmp/.X11-unix
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
XPID=$!
sleep 2
export DISPLAY=:99 HR_TEST_FREEZE_UI=1
shot() { import -window root "$1"; }
sig() { convert "$1" -crop "$2" +repage -depth 8 -format "%#" info:; }
ae() { compare -metric AE "$1" "$2" null: 2>&1 | cut -d" " -f1 || true; }
press() { xdotool keydown "$1"; sleep 0.15; xdotool keyup "$1"; sleep "${2:-1}"; }
quitgame() {
  xdotool keydown ctrl; sleep 0.3; xdotool keydown q; sleep 0.3; xdotool keyup q; xdotool keyup ctrl
  i=0; while kill -0 "$1" 2>/dev/null && [ $i -lt 20 ]; do sleep 1; i=$((i+1)); done
  if kill -0 "$1" 2>/dev/null; then echo "Ctrl+Q 後 20 秒仍未結束，強制結束" >&2; kill "$1"; fi
  rc=0; wait "$1" || rc=$?; echo "結束碼：$rc"
}
FAIL=0
P=1248x672+16+16
/out/bin/hr-play -orig /orig/orig -saves /out/gui-saves -scale 2 -lang zh-TW >/tmp/play.log 2>&1 &
PID=$!
sleep 15
shot /out/gui-lang-title-a.png
sleep 5
shot /out/gui-lang-title-b.png
echo "== 原版標題畫面靜態性（間隔 5 秒的兩張截圖，整張 1280x800）"
echo "差異像素：$(ae /out/gui-lang-title-a.png /out/gui-lang-title-b.png)"
echo "簽章 A：$(sig /out/gui-lang-title-a.png 1280x800+0+0)"
echo "簽章 B：$(sig /out/gui-lang-title-b.png 1280x800+0+0)"
echo "面板區域簽章 A：$(sig /out/gui-lang-title-a.png $P)  B：$(sig /out/gui-lang-title-b.png $P)"
press F1 1
shot /out/gui-lang-0.png
i=1; while [ $i -le 5 ]; do press F4 1; shot /out/gui-lang-$i.png; i=$((i+1)); done
echo "== F1 面板區域（$P）的像素簽章"
: >/tmp/sigs04
i=0; while [ $i -le 5 ]; do s=$(sig /out/gui-lang-$i.png $P); echo "F4 x $i：$s"; echo "$s" >/tmp/sig$i; [ $i -le 4 ] && echo "$s" >>/tmp/sigs04; i=$((i+1)); done
dups=$(sort /tmp/sigs04 | uniq -d | wc -l)
if [ "$dups" -ne 0 ]; then echo "失敗：F4 前五張面板有 $dups 組相同簽章" >&2; FAIL=1; fi
if [ "$(cat /tmp/sig5)" != "$(cat /tmp/sig0)" ]; then echo "失敗：第六次（五次 F4 之後）沒有回到起點" >&2; FAIL=1; fi
if [ "$(sig /out/gui-lang-title-b.png $P)" = "$(cat /tmp/sig0)" ]; then echo "失敗：開 F1 前後面板區域相同，面板沒有畫出來" >&2; FAIL=1; fi
quitgame $PID
echo "== prefs.json（五次 F4 後的語言補丁）"
cat /tmp/.config/high_reward/prefs.json || { echo "失敗：沒有 prefs.json" >&2; FAIL=1; }
echo
echo "== play.log"; tail -3 /tmp/.config/high_reward/play.log || true
echo "== stderr（hr-play）"; grep -vE "^ALSA lib" /tmp/play.log | tail -15

echo "######## 階段 2：不設 HR_TEST_FREEZE_UI，F4 的 toast（左下最後一行，1248x32+16+752）：出現後 2 秒消失"
unset HR_TEST_FREEZE_UI
T=1248x32+16+752
XDG_CONFIG_HOME=/tmp/cfg2 /out/bin/hr-play -orig /orig/orig -saves /out/gui-saves -scale 2 -lang zh-TW >/tmp/play2.log 2>&1 &
PID=$!
sleep 15
shot /out/gui-lang-toast-0.png
press F4 0.5
shot /out/gui-lang-toast-1.png
sleep 3
shot /out/gui-lang-toast-2.png
t0=$(sig /out/gui-lang-toast-0.png $T); t1=$(sig /out/gui-lang-toast-1.png $T); t2=$(sig /out/gui-lang-toast-2.png $T)
echo "toast 區域簽章：F4 前 $t0；F4 後 0.5 秒 $t1；3.5 秒後 $t2"
if [ "$t0" = "$t1" ]; then echo "失敗：F4 之後 toast 區域沒有變化，toast 沒有畫出來" >&2; FAIL=1; fi
if [ "$t0" != "$t2" ]; then echo "失敗：toast 沒有在 2 秒後消失" >&2; FAIL=1; fi
quitgame $PID
kill $XPID 2>/dev/null || true
if [ $FAIL -eq 0 ]; then echo "gui-lang：通過"; else echo "gui-lang：失敗"; fi
exit $FAIL
EOS
)
    run "$GUI_BODY" ;;
  gui-theme)
    # docs/spec/006 第 10 節的端對端（theme）：另掛 -v hd:/hd:ro 與 -hd /hd。以 -theme original 啟動取基準標題截圖，按 F2 後以標準錯誤的
    # 日誌 theme ready: hd 為完成訊號（不用固定等待）再截圖；正向檢查 HD 與原版（最近鄰放大）的差異像素比例；再按 F2 回 original，與基準相同。
    # Lowered 的觀察來源：標準錯誤的降頻日誌與 play.log 的 lowered= 欄；對照組：同一容器、同樣時間長度以 -theme hd 啟動、不按 F2。
    test -f "$ROOT/hd/catalog.tsv" || { echo "缺 $ROOT/hd/catalog.tsv" >&2; exit 1; }
    test -d "$ROOT/hd/x2" || { echo "缺 $ROOT/hd/x2" >&2; exit 1; }
    EXTRA+=(-v "$ROOT/hd:/hd:ro")
    GUI_BODY=$(cat <<'EOS'
set -e
for c in convert compare identify xdotool import Xvfb; do command -v "$c" >/dev/null 2>&1 || { echo "缺工具：$c" >&2; exit 1; }; done
test -f /hd/catalog.tsv
cd /src/apps/hr/play
go build -o /out/bin/hr-play .
mkdir -p /tmp/.X11-unix
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
XPID=$!
sleep 2
export DISPLAY=:99 HR_TEST_FREEZE_UI=1
shot() { import -window root "$1"; }
sig() { convert "$1" -crop "$2" +repage -depth 8 -format "%#" info:; }
ae() { compare -metric AE "$1" "$2" null: 2>&1 | cut -d" " -f1 || true; }
press() { xdotool keydown "$1"; sleep 0.15; xdotool keyup "$1"; sleep "${2:-0.3}"; }
quitgame() {
  xdotool keydown ctrl; sleep 0.3; xdotool keydown q; sleep 0.3; xdotool keyup q; xdotool keyup ctrl
  i=0; while kill -0 "$1" 2>/dev/null && [ $i -lt 20 ]; do sleep 1; i=$((i+1)); done
  if kill -0 "$1" 2>/dev/null; then echo "Ctrl+Q 後 20 秒仍未結束，強制結束" >&2; kill "$1"; fi
  rc=0; wait "$1" || rc=$?; echo "結束碼：$rc"
}
# waitlog <檔> <樣式> <次數> <逾時秒>：標準錯誤日誌出現指定次數（不用固定等待當完成訊號）
waitlog() {
  i=0
  while [ $i -lt $4 ]; do
    n=$(grep -c "$2" "$1" || true)
    if [ "${n:-0}" -ge "$3" ]; then echo "$2 已出現 $n 次（$i 秒）"; return 0; fi
    sleep 1; i=$((i+1))
  done
  echo "逾時：$2（$4 秒內未出現 $3 次）" >&2; return 1
}
FAIL=0
W=1280x800+0+0
TOTAL=$((1280*800))

echo "######## 階段 B：-theme original 啟動，F2 切 HD，再 F2 回 original"
T0=$(date +%s)
XDG_CONFIG_HOME=/tmp/cfgB /out/bin/hr-play -orig /orig/orig -saves /out/gui-saves-theme -scale 2 -hd /hd -theme original >/tmp/playB.log 2>&1 &
PID=$!
sleep 15
shot /out/gui-theme-orig-a.png
sleep 5
shot /out/gui-theme-orig-b.png
echo "== 原版標題畫面靜態性（間隔 5 秒）：差異像素 $(ae /out/gui-theme-orig-a.png /out/gui-theme-orig-b.png)"
echo "   簽章 A：$(sig /out/gui-theme-orig-a.png $W)"
echo "   簽章 B：$(sig /out/gui-theme-orig-b.png $W)"
echo "   啟動日誌："; grep -vE "^ALSA lib" /tmp/playB.log | head -8
press F2 0.2
T1=$(date +%s)
waitlog /tmp/playB.log "theme ready: hd" 1 180 || FAIL=1
echo "F2 到 theme ready: hd：$(( $(date +%s) - T1 )) 秒（含輪詢粒度）"
sleep 1
shot /out/gui-theme-hd.png
D=$(ae /out/gui-theme-orig-b.png /out/gui-theme-hd.png)
echo "== 正向檢查：HD 與最近鄰放大的原版相比，差異像素 $D／$TOTAL ＝ $(( D*10000/TOTAL ))／10000"
echo "$D $TOTAL" >/out/gui-theme-diff-ratio.txt
# 門檻：2026-10-04 在本容器量到 899077／1024000（約 87.8%）；定為 50%。HD 沒有顯示（切換成空操作）時比例為 0。
HD_MIN_PERCENT=50
if [ $(( D*100/TOTAL )) -lt $HD_MIN_PERCENT ]; then echo "失敗：HD 與原版的差異像素比例低於 $HD_MIN_PERCENT%，HD 可能沒有顯示" >&2; FAIL=1; fi
press F2 0.2
waitlog /tmp/playB.log "theme ready: original" 1 30 || FAIL=1
sleep 1
shot /out/gui-theme-back.png
echo "== 回 original 與基準相比：差異像素 $(ae /out/gui-theme-orig-b.png /out/gui-theme-back.png)（基準 A 對 B 是 $(ae /out/gui-theme-orig-a.png /out/gui-theme-orig-b.png)）"
echo "   簽章 基準 B：$(sig /out/gui-theme-orig-b.png $W)"
echo "   簽章 回 original：$(sig /out/gui-theme-back.png $W)"
# 基準標題畫面是靜態的（A 對 B 差異 0）時，回 original 的截圖必須與基準逐像素相同；標題畫面若有動態區，這個比對無效（要先裁掉動態區）
if [ "$(ae /out/gui-theme-orig-a.png /out/gui-theme-orig-b.png)" != "0" ]; then
  echo "失敗：基準標題畫面不是靜態的，回 original 的逐像素比對無效（要先裁掉動態區）" >&2; FAIL=1
elif [ "$(ae /out/gui-theme-orig-b.png /out/gui-theme-back.png)" != "0" ]; then
  echo "失敗：回 original 的畫面與基準不同" >&2; FAIL=1
fi
quitgame $PID
T2=$(date +%s)
DUR=$((T2-T0))
echo "階段 B 全長 $DUR 秒"
echo "== stderr（階段 B）"; grep -vE "^ALSA lib" /tmp/playB.log | tail -20
echo "== play.log（階段 B）"; cat /tmp/cfgB/high_reward/play.log || true
echo "== prefs.json（階段 B）"; cat /tmp/cfgB/high_reward/prefs.json || true; echo
echo "== 降頻日誌（階段 B）：$(grep -c '跑不到' /tmp/playB.log || true) 行"
grep '跑不到' /tmp/playB.log || true

echo "######## 階段 A（對照）：-theme hd 啟動、不按 F2，同樣長度 $DUR 秒"
XDG_CONFIG_HOME=/tmp/cfgA /out/bin/hr-play -orig /orig/orig -saves /out/gui-saves-theme -scale 2 -hd /hd -theme hd >/tmp/playA.log 2>&1 &
PID=$!
sleep $DUR
shot /out/gui-theme-control-hd.png
quitgame $PID
echo "== stderr（階段 A）"; grep -vE "^ALSA lib" /tmp/playA.log | tail -12
echo "== play.log（階段 A）"; cat /tmp/cfgA/high_reward/play.log || true
echo "== 降頻日誌（階段 A）：$(grep -c '跑不到' /tmp/playA.log || true) 行"
grep '跑不到' /tmp/playA.log || true
kill $XPID 2>/dev/null || true
echo "== 收據：HD 差異比例 $D／$TOTAL；階段 A（-theme hd 不按 F2）降頻日誌 $(grep -c '跑不到' /tmp/playA.log || true) 行；階段 B 降頻日誌 $(grep -c '跑不到' /tmp/playB.log || true) 行"
# Lowered：階段 B 在「theme hd：開始預載」之前與整段的降頻日誌行數；對照組（階段 A）已降頻，或 F2 之前就已降頻，F2 前後不變的斷言無效（環境本身降頻）
PRE=$(sed -n "1,/開始預載/p" /tmp/playB.log | grep -c "跑不到" || true)
ALLB=$(grep -c "跑不到" /tmp/playB.log || true)
ALLA=$(grep -c "跑不到" /tmp/playA.log || true)
echo "== Lowered：階段 B F2 之前 $PRE 行、整段 $ALLB 行；對照組（階段 A）$ALLA 行"
if [ "$ALLA" -gt 0 ] || [ "$PRE" -gt 0 ]; then
  echo "Lowered 斷言無效：對照組或 F2 之前就已降頻（Xvfb 軟體繪圖加 --cpus ${HR_PLAY_CPUS:-2} 的環境本身跑不到 18.2 Hz），不作為通過或失敗的依據"
elif [ "$ALLB" -ne "$PRE" ]; then
  echo "失敗：對照組沒有降頻，但階段 B 在 F2 之後降頻（整段 $ALLB 行，F2 之前 $PRE 行）" >&2; FAIL=1
fi
if [ $FAIL -eq 0 ]; then echo "gui-theme：通過"; else echo "gui-theme：失敗"; fi
exit $FAIL
EOS
)
    run "$GUI_BODY" ;;
  gui-ingame)
    # docs/spec/008 第 3.2、3.8 節的前端端對端：F1「遊戲內文字」一行與 F4 提示。資料目錄用 XDG_CONFIG_HOME 指到 /out/l1-wire2/home/<階段>/.config
    # （語言包含原版位元組，只放 workplace/out；不寫 ~）。截圖與日誌在 /out/l1-wire2/gui-ingame-*。
    #   (a) 預設啟動（沒有 l10n/）：F1 是 (1) 原版，且沒有建置（不出現 l10n-packs）；
    #   (b) -ingame-lang identity：冷建置 identity 包，F1 是 (2) 驗證用；第二次啟動重用；
    #   (c) F4 一圈（不設 HR_TEST_FREEZE_UI，toast 才會畫）：ko、ja 的 toast 是「尚無語言包」、F1 是 (4) no-table；
    #       之後放入資料目錄的 l10n/zh-TW/，F4 回 zh-TW：F1 是 (3)、toast 是「下次啟動生效」（真值表列 20）；
    #   (d1) 竄改包：預先放一個同名而竄改一個位元組的 identity 包，不被搬動，前端改建 -2，F1 是 (2)；
    #   (d2) -ingame-lang zh-TW 而譯文表有一列違規（accepted、字集外的字）：建置失敗，F1 是 (4) 建置失敗，遊戲仍啟動；
    #   (e)  -l10n 指向 zh-TW 譯文表有一列合法的 accepted：table 模式、採用列數 1，F1 是 (2) 部分翻譯；F4 到 zh-CN（沒有表）是 (4) no-table（列 6、7）。
    GUI_BODY=$(cat <<'EOS'
set -e
for c in convert identify xdotool import Xvfb sha256sum cmp dd stat; do command -v "$c" >/dev/null 2>&1 || { echo "缺工具：$c" >&2; exit 1; }; done
O=/out/l1-wire2
# (d2)、(e) 的譯文表要綁定 ESPMES#121.0 的原項目雜湊（src_sha256 前 16 碼）。它是原版衍生值，不進版控：
# 由 workplace/out/l1-wire2/src-sha-esp121-0.txt 讀入（產生方法見 tools/l10n/srcsha/main.go 檔頭）。
SRCSHA_FILE="$O/src-sha-esp121-0.txt"
[ -s "$SRCSHA_FILE" ] || { echo "缺 workplace/out/l1-wire2/src-sha-esp121-0.txt（ESPMES#121.0 的 src_sha256 前 16 碼；產生方法見 tools/l10n/srcsha/main.go）" >&2; exit 1; }
SRCSHA=$(head -c 16 "$SRCSHA_FILE")
cd /src/apps/hr/play
go build -o /out/bin/hr-play .
mkdir -p /tmp/.X11-unix "$O"
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
XPID=$!
sleep 2
export DISPLAY=:99
shot() { import -window root "$1"; }
crop() { convert "$1" -crop "$2" +repage "$3"; }
sigfile() { convert "$1" -depth 8 -format "%#" info:; }
press() { xdotool keydown "$1"; sleep 0.15; xdotool keyup "$1"; sleep "${2:-1}"; }
quitgame() {
  xdotool keydown ctrl; sleep 0.3; xdotool keydown q; sleep 0.3; xdotool keyup q; xdotool keyup ctrl
  i=0; while kill -0 "$1" 2>/dev/null && [ $i -lt 20 ]; do sleep 1; i=$((i+1)); done
  if kill -0 "$1" 2>/dev/null; then echo "Ctrl+Q 後 20 秒仍未結束，強制結束" >&2; kill "$1"; fi
  rc=0; wait "$1" || rc=$?; echo "結束碼：$rc"
}
waitlog() {
  i=0
  while [ $i -lt $4 ]; do
    n=$(grep -c "$2" "$1" || true)
    if [ "${n:-0}" -ge "$3" ]; then echo "$2 已出現 $n 次（$i 秒）"; return 0; fi
    sleep 1; i=$((i+1))
  done
  echo "逾時：$2（$4 秒內未出現 $3 次）" >&2; return 1
}
newhome() { rm -rf "$O/home/$1"; mkdir -p "$O/home/$1/.config"; }
# start <階段名稱> <日誌檔> [hr-play 旗標…]：背景啟動，PID 放在 $PID
start() {
  sname=$1; slog=$2; shift 2
  XDG_CONFIG_HOME="$O/home/$sname/.config" /out/bin/hr-play -orig /orig/orig -saves "$O/saves" -scale 2 -lang zh-TW "$@" >"$slog" 2>&1 &
  PID=$!
}
FAIL=0
F1LINE=1248x32+16+368   # 面板第 rowStatus + 2 ＝ 11 行：y ＝ 16 + 11 x 32
TOAST=1248x32+16+752
HD=high_reward
export HR_TEST_FREEZE_UI=1

echo "######## (a) 預設啟動：沒有 l10n/"
newhome a
start a "$O/gui-ingame-a.log"
sleep 15
press F1 1
shot "$O/gui-ingame-a.png"; crop "$O/gui-ingame-a.png" $F1LINE "$O/gui-ingame-a-f1line.png"
echo "== 日誌（ingame:）"; grep 'ingame:' "$O/gui-ingame-a.log" || true
grep -q 'ingame: C=zh-TW explicit=false table=false plan=none' "$O/gui-ingame-a.log" || { echo "失敗：(a) 日誌沒有預期的計畫行" >&2; FAIL=1; }
if [ -d "$O/home/a/.config/$HD/l10n-packs" ]; then echo "失敗：(a) 預設路徑不該建置（出現了 l10n-packs）" >&2; FAIL=1; else echo "(a) 沒有 l10n-packs 目錄：預設路徑沒有建置"; fi
quitgame $PID

echo "######## (b) -ingame-lang identity：冷建置"
newhome b
start b "$O/gui-ingame-b.log" -ingame-lang identity
waitlog "$O/gui-ingame-b.log" "ingame: pack-active" 1 90 || FAIL=1
sleep 3
press F1 1
shot "$O/gui-ingame-b.png"; crop "$O/gui-ingame-b.png" $F1LINE "$O/gui-ingame-b-f1line.png"
echo "== 日誌（ingame:）"; grep 'ingame:' "$O/gui-ingame-b.log" || true
echo "== play.log（時間 與 內容）"; grep 'ingame:' "$O/home/b/.config/$HD/play.log" | cut -f1,3 || true
echo "== l10n-packs"; ls -la "$O/home/b/.config/$HD/l10n-packs/" || true
for p in "$O"/home/b/.config/$HD/l10n-packs/identity-*; do ls "$p" "$p/files"; done
grep -q 'ingame: pack-ready' "$O/gui-ingame-b.log" || { echo "失敗：(b) 沒有建置完成的日誌" >&2; FAIL=1; }
grep -q 'ingame: pack-active' "$O/gui-ingame-b.log" || { echo "失敗：(b) LangStatus 沒有生效的日誌" >&2; FAIL=1; }
grep -q 'reused=false' "$O/gui-ingame-b.log" || { echo "失敗：(b) 第一次應是冷建置（reused=false）" >&2; FAIL=1; }
if [ "$(sigfile "$O/gui-ingame-a-f1line.png")" = "$(sigfile "$O/gui-ingame-b-f1line.png")" ]; then echo "失敗：(b) F1 的遊戲內文字一行與 (a) 相同" >&2; FAIL=1; fi
quitgame $PID
echo "== (b2) 第二次啟動：重用同一個包"
start b "$O/gui-ingame-b2.log" -ingame-lang identity
waitlog "$O/gui-ingame-b2.log" "ingame: pack-active" 1 90 || FAIL=1
grep 'ingame:' "$O/gui-ingame-b2.log" || true
grep -q 'reused=true' "$O/gui-ingame-b2.log" || { echo "失敗：(b2) 第二次啟動應重用（reused=true）" >&2; FAIL=1; }
quitgame $PID

echo "######## (c) F4 一圈（不設 HR_TEST_FREEZE_UI）"
unset HR_TEST_FREEZE_UI
newhome c
start c "$O/gui-ingame-c.log"
sleep 15
press F1 1
shot "$O/gui-ingame-c-0.png"
for n in 1 2 3 4; do
  press F4 0.6
  shot "$O/gui-ingame-c-$n.png"
  crop "$O/gui-ingame-c-$n.png" $F1LINE "$O/gui-ingame-c-$n-f1line.png"
  crop "$O/gui-ingame-c-$n.png" $TOAST "$O/gui-ingame-c-$n-toast.png"
done
crop "$O/gui-ingame-c-0.png" $TOAST "$O/gui-ingame-c-0-toast.png"
echo "toast 區域簽章：F4 前 $(sigfile "$O/gui-ingame-c-0-toast.png")；ko（第 2 次）$(sigfile "$O/gui-ingame-c-2-toast.png")；ja（第 4 次）$(sigfile "$O/gui-ingame-c-4-toast.png")"
if [ "$(sigfile "$O/gui-ingame-c-0-toast.png")" = "$(sigfile "$O/gui-ingame-c-2-toast.png")" ]; then echo "失敗：(c) F4 到 ko 之後 toast 區域沒有變化" >&2; FAIL=1; fi
if [ "$(sigfile "$O/gui-ingame-c-2-toast.png")" = "$(sigfile "$O/gui-ingame-c-4-toast.png")" ]; then echo "失敗：(c) ko 與 ja 的 toast 相同" >&2; FAIL=1; fi
echo "== 列 20：放入 l10n/zh-TW/（資料目錄；只放一個佔位的譯文表檔，這次啟動不建置），F4 回 zh-TW"
mkdir -p "$O/home/c/.config/$HD/l10n/zh-TW"
printf 'id\n' > "$O/home/c/.config/$HD/l10n/zh-TW/SP.MES.tsv"
press F4 0.6
shot "$O/gui-ingame-c-5.png"
crop "$O/gui-ingame-c-5.png" $F1LINE "$O/gui-ingame-c-5-f1line.png"
crop "$O/gui-ingame-c-5.png" $TOAST "$O/gui-ingame-c-5-toast.png"
quitgame $PID
echo "== 日誌（ingame:）"; grep 'ingame:' "$O/gui-ingame-c.log" || true
if [ -d "$O/home/c/.config/$HD/l10n-packs" ]; then echo "失敗：(c) 預設路徑 F4 不該建置（出現了 l10n-packs）" >&2; FAIL=1; fi

echo "######## (d1) 竄改包：同名的 identity 包被竄改一個位元組"
export HR_TEST_FREEZE_UI=1
newhome d1
BP="$O/home/b/.config/$HD/l10n-packs"
D1="$O/home/d1/.config/$HD/l10n-packs"
P=$(ls "$BP" | grep '^identity-' | head -1)
echo "包名：$P"
mkdir -p "$D1"
cp -a "$BP/$P" "$D1/$P"
printf '\377' | dd of="$D1/$P/files/SP.MES" bs=1 seek=100 conv=notrunc 2>/dev/null
nd=$(cmp -l "$BP/$P/files/SP.MES" "$D1/$P/files/SP.MES" | wc -l)
if [ "$nd" -eq 0 ]; then printf '\000' | dd of="$D1/$P/files/SP.MES" bs=1 seek=100 conv=notrunc 2>/dev/null; nd=$(cmp -l "$BP/$P/files/SP.MES" "$D1/$P/files/SP.MES" | wc -l); fi
echo "竄改後與原包不同的位元組數：$nd（應為 1）"
[ "$nd" -eq 1 ] || { echo "失敗：(d1) 竄改的位元組數不是 1" >&2; FAIL=1; }
before=$(cd "$D1/$P" && find . -type f | sort | xargs sha256sum | sha256sum)
ino=$(stat -c %i "$D1/$P")
start d1 "$O/gui-ingame-d1.log" -ingame-lang identity
waitlog "$O/gui-ingame-d1.log" "ingame: pack-active" 1 90 || FAIL=1
sleep 3
press F1 1
shot "$O/gui-ingame-d1.png"; crop "$O/gui-ingame-d1.png" $F1LINE "$O/gui-ingame-d1-f1line.png"
quitgame $PID
echo "== 日誌（ingame:）"; grep 'ingame:' "$O/gui-ingame-d1.log" || true
echo "== l10n-packs"; ls -la "$D1" || true
after=$(cd "$D1/$P" && find . -type f | sort | xargs sha256sum | sha256sum)
ino2=$(stat -c %i "$D1/$P")
[ "$before" = "$after" ] && [ "$ino" = "$ino2" ] || { echo "失敗：(d1) 被竄改的舊目錄被搬動或改動（inode $ino → $ino2）" >&2; FAIL=1; }
test -d "$D1/$P-2" || { echo "失敗：(d1) 沒有改建 $P-2" >&2; FAIL=1; }
grep -q "pack-ready dir=$D1/$P-2 " "$O/gui-ingame-d1.log" || { echo "失敗：(d1) 日誌的 dir 不是 $P-2" >&2; FAIL=1; }

echo "######## (d2) -ingame-lang zh-TW，譯文表有一列違規"
newhome d2
BAD="$O/l10n-bad"
rm -rf "$BAD"; mkdir -p "$BAD/zh-TW"
TXT='简简简'
ACC=$(printf '%s' "$TXT" | sha256sum | cut -c1-16)
printf 'id\tsrc_sha256\ttext\tstatus\tacc_sha\tby\tbatch\tdate\tnote\nESPMES#121.0\t%s\t%s\taccepted\t%s\tgui\tgui-ingame\t2026-10-04\t\n' "$SRCSHA" "$TXT" "$ACC" > "$BAD/zh-TW/ESPMES.MRG.tsv"
start d2 "$O/gui-ingame-d2.log" -ingame-lang zh-TW -l10n "$BAD"
sleep 15
press F1 1
shot "$O/gui-ingame-d2.png"; crop "$O/gui-ingame-d2.png" $F1LINE "$O/gui-ingame-d2-f1line.png"
echo "== 日誌（ingame:）"; grep 'ingame:' "$O/gui-ingame-d2.log" || true
grep -q 'ingame: violation' "$O/gui-ingame-d2.log" || { echo "失敗：(d2) 沒有違規項目的日誌" >&2; FAIL=1; }
grep -q 'ingame: build-failed' "$O/gui-ingame-d2.log" || { echo "失敗：(d2) 沒有 build-failed 的日誌" >&2; FAIL=1; }
if grep -q 'ingame: pack-active' "$O/gui-ingame-d2.log"; then echo "失敗：(d2) 建置失敗卻啟用了語言包" >&2; FAIL=1; fi
kill -0 $PID 2>/dev/null || { echo "失敗：(d2) 建置失敗後遊戲沒有啟動" >&2; FAIL=1; }
quitgame $PID
if grep -qE 'panic|goroutine ' "$O/gui-ingame-d2.log"; then echo "失敗：(d2) 日誌有 panic" >&2; FAIL=1; fi

echo "######## (e) -l10n：zh-TW 譯文表有一列 accepted 且合法（table 模式，採用列數 1；沒有 -ingame-lang，啟用規則 3），F4 到 zh-CN（真值表列 6、7）"
unset HR_TEST_FREEZE_UI
newhome e
GOOD="$O/l10n-good"
rm -rf "$GOOD"; mkdir -p "$GOOD/zh-TW"
GT='一二三四六八十大'
GACC=$(printf '%s' "$GT" | sha256sum | cut -c1-16)
printf 'id\tsrc_sha256\ttext\tstatus\tacc_sha\tby\tbatch\tdate\tnote\nESPMES#121.0\t%s\t%s\taccepted\t%s\tgui\tgui-ingame\t2026-10-04\t\n' "$SRCSHA" "$GT" "$GACC" > "$GOOD/zh-TW/ESPMES.MRG.tsv"
start e "$O/gui-ingame-e.log" -l10n "$GOOD"
waitlog "$O/gui-ingame-e.log" "ingame: pack-active" 1 90 || FAIL=1
sleep 3
press F1 1
shot "$O/gui-ingame-e-0.png"; crop "$O/gui-ingame-e-0.png" $F1LINE "$O/gui-ingame-e-0-f1line.png"
press F4 0.6
shot "$O/gui-ingame-e-1.png"; crop "$O/gui-ingame-e-1.png" $F1LINE "$O/gui-ingame-e-1-f1line.png"; crop "$O/gui-ingame-e-1.png" $TOAST "$O/gui-ingame-e-1-toast.png"
quitgame $PID
echo "== 日誌（ingame:）"; grep 'ingame:' "$O/gui-ingame-e.log" || true
grep -q 'ingame: C=zh-TW explicit=false table=true plan=table' "$O/gui-ingame-e.log" || { echo "失敗：(e) 計畫行不是 (zh-TW, 非明示, 有表, table)" >&2; FAIL=1; }
grep -q 'ingame: pack-ready .* mode=table code=zh-TW adopted=1 ' "$O/gui-ingame-e.log" || { echo "失敗：(e) 建置結果不是 table 模式、採用列數 1" >&2; FAIL=1; }
grep -q 'ingame: pack-active' "$O/gui-ingame-e.log" || { echo "失敗：(e) LangStatus 沒有生效的日誌" >&2; FAIL=1; }

kill $XPID 2>/dev/null || true
if [ $FAIL -eq 0 ]; then echo "gui-ingame：通過"; else echo "gui-ingame：失敗"; fi
exit $FAIL
EOS
)
    run "$GUI_BODY" ;;
  gui-lang-cmp)
    # 比對兩組 gui-lang 截圖（舊：HR_CMP_OLD，新：HR_CMP_NEW，都是 /out 之下的目錄，內含 gui-lang-0.png 至 gui-lang-5.png）的 F1 面板：
    # 21 行逐行比差異像素，列出有差異的行（面板在邏輯畫面 x ＝ 16、y ＝ 16 起，每行 1248x32）。不啟動遊戲，只用映像內的 ImageMagick。
    EXTRA+=(-e "HR_CMP_OLD=${HR_CMP_OLD:?HR_CMP_OLD（/out 之下的舊截圖目錄）}" -e "HR_CMP_NEW=${HR_CMP_NEW:?HR_CMP_NEW（/out 之下的新截圖目錄）}")
    run 'set -e
      command -v compare >/dev/null 2>&1 || { echo "缺工具：compare" >&2; exit 1; }
      OLD=/out/$HR_CMP_OLD; NEW=/out/$HR_CMP_NEW
      for n in 0 1 2 3 4 5; do
        test -f "$OLD/gui-lang-$n.png" && test -f "$NEW/gui-lang-$n.png" || { echo "缺 gui-lang-$n.png" >&2; exit 1; }
        diffs=""; total=0; i=0
        while [ $i -lt 21 ]; do
          y=$((16 + i*32))
          d=$(compare -metric AE "$OLD/gui-lang-$n.png[1248x32+16+$y]" "$NEW/gui-lang-$n.png[1248x32+16+$y]" null: 2>&1 | cut -d" " -f1 || true)
          if [ "${d:-0}" != "0" ]; then diffs="$diffs 第${i}行($d)"; total=$((total+1)); fi
          i=$((i+1))
        done
        echo "gui-lang-$n：有差異的面板行 $total 行：${diffs:-（無）}"
      done' ;;
  *) sed -n 2,9p "$0" >&2; exit 2 ;;
esac
