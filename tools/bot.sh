#!/usr/bin/env bash
# 遊玩機器人（workplace/dosgolem/apps/hr/cmd/hrbot）在 Docker 內執行，輸出到 workplace/out/bot/<名稱>/。
#   tools/bot.sh build                      建置 workplace/out/hrbot（容器內，離線）
#   tools/bot.sh run <名稱> [hrbot 參數…]    例：tools/bot.sh run p1 -game-hours 2 -seed 1
#   tools/bot.sh run <名稱> -no-stack-patch … 關掉堆疊補丁（對照）
# 容器名 hr-bot-<名稱>，--rm、1 核、2 GB、預設 --network none；原版唯讀掛為 /orig/orig。
# 輸出（截圖、狀態檔、存檔）是原版內容的衍生物，只放 workplace/，不進版控。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GO_IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
RUN_IMAGE="${HR_BOT_IMAGE:-golang:1.24-bookworm}"
case "${1:-}" in
  build)
    DOSGOLEM_GO_IMAGE="$GO_IMAGE" GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local \
      "$ROOT/tools/dosgolem.sh" go build -o /out/hrbot ./apps/hr/cmd/hrbot ;;
  run)
    shift
    NAME="${1:?名稱}"; shift
    OUT="$ROOT/workplace/out/bot/$NAME"
    mkdir -p "$OUT"
    test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig" >&2; exit 1; }
    test -x "$ROOT/workplace/out/hrbot" || { echo "先 tools/bot.sh build" >&2; exit 1; }
    exec timeout "${HR_BOT_TIMEOUT:-6h}" docker run --rm --name "hr-bot-$NAME" --network none \
      --memory "${HR_BOT_MEM:-2g}" --cpus "${HR_BOT_CPUS:-1}" --pids-limit 128 \
      --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
      -v "$ROOT/workplace/orig:/orig/orig:ro" -v "$OUT:/out/bot" -v "$ROOT/workplace/out/hrbot:/hrbot:ro" \
      -e HOME=/tmp "$RUN_IMAGE" /hrbot -orig /orig/orig -out /out/bot "$@" ;;
  *) sed -n 2,6p "$0" >&2; exit 2 ;;
esac
