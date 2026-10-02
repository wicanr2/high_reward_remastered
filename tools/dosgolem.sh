#!/usr/bin/env bash
# 包裝 workplace/dosgolem（獨立副本）的 docker 建置與探針。
#
#   tools/dosgolem.sh build                    編譯 probe 與 hrsoak 到 workplace/out
#   tools/dosgolem.sh probe <probe 參數…>       在容器內跑 probe（原版唯讀掛載為 /orig，輸出 /out）
#   tools/dosgolem.sh soak <hrsoak 參數…>       在容器內跑長跑驅動（apps/hr/cmd/hrsoak，輸出到 /out/soak）
#   tools/dosgolem.sh go <go 參數…>             在容器內跑任意 go 指令（例如 test ./internal/cpu）
#
# 原版目錄在容器內是 /orig/orig（唯讀），例如：
#   tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 20000000
# 容器預設 --network none。可寫輸出只有 workplace/out（容器內 /out）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DG="$ROOT/workplace/dosgolem"
test -x "$DG/tools/go.sh" || { echo "缺 workplace/dosgolem" >&2; exit 1; }
test -d "$ROOT/workplace/orig" || { echo "缺 workplace/orig" >&2; exit 1; }
mkdir -p "$ROOT/workplace/out"
export DOSGOLEM_GO_IMAGE="${DOSGOLEM_GO_IMAGE:-golang:1.24-bookworm}"
export DOSGOLEM_ORIG="$ROOT/workplace"
export DOSGOLEM_EXTRA_MOUNT="$ROOT/workplace/out:/out"
export DOSGOLEM_TIMEOUT="${DOSGOLEM_TIMEOUT:-10m}" DOSGOLEM_CPUS="${DOSGOLEM_CPUS:-2}" DOSGOLEM_MEM="${DOSGOLEM_MEM:-2g}"
cd "$DG"
case "${1:-}" in
  build) tools/go.sh build -o /out/probe ./cmd/probe && tools/go.sh build -o /out/hrsoak ./apps/hr/cmd/hrsoak ;;
  soak)  shift; DOSGOLEM_GO_CMD=/out/hrsoak tools/go.sh -exe /orig/orig/MAIN.EXE -root /orig/orig "$@" ;;
  probe) shift; DOSGOLEM_GO_CMD=/out/probe tools/go.sh "$@" ;;
  go)    shift; tools/go.sh "$@" ;;
  *) sed -n 2,12p "$0" >&2; exit 2 ;;
esac
