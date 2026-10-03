#!/usr/bin/env bash
# 在 docker 內執行 tools/text 下的單檔 Go 工具（標準庫加 golang.org/x/text，Big5 解碼用）。
#
#   tools/text/run.sh <工具名> <參數...>        原版目錄唯讀掛載為 /orig，輸出在容器內 /out
#
# 容器：--network none；原版唯讀；唯一可寫的主機路徑是 workplace/out/re-text（容器內 /out）。
# x/text 從 workplace/gomodcache 的下載快取以 file:// 代理唯讀取得，模組快取與建置快取放在 tmpfs，
# 不寫入主機。每次執行先把 /tools 複製到 /tmp/w，go.sum 在 tmpfs 內產生。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test -d "$ROOT/workplace/orig" || { echo "缺 workplace/orig" >&2; exit 1; }
test -d "$ROOT/workplace/gomodcache/cache/download/golang.org/x/text" || { echo "缺 x/text 快取" >&2; exit 1; }
mkdir -p "$ROOT/workplace/ida-text/out"
test -f "$ROOT/tools/text/${1:?工具名}.go" || { echo "沒有 tools/text/$1.go" >&2; exit 1; }
mkdir -p "$ROOT/workplace/out/re-text"
tool="$1"; shift
exec timeout 10m docker run --rm --name "hr-text-$$" --network none \
  --memory 2g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" \
  --tmpfs /tmp:rw,exec,size=1g \
  -v "$ROOT/tools/text:/tools:ro" \
  -v "$ROOT/workplace/orig:/orig:ro" \
  -v "$ROOT/workplace/out/re-text:/out" \
  -v "$ROOT/workplace/gomodcache/cache/download:/proxy:ro" \
  -v "$ROOT/workplace/ida-text/out:/idatext:ro" \
  -e GOCACHE=/tmp/gocache -e GOMODCACHE=/tmp/gomod -e GOPROXY=file:///proxy \
  -e GOSUMDB=off -e GOFLAGS=-mod=mod -e HOME=/tmp -e CGO_ENABLED=0 \
  -w /tmp golang:1.24-bookworm sh -c 'mkdir -p /tmp/w && cp /tools/*.go /tools/go.mod /tmp/w/ && cd /tmp/w && go run "$0.go" "$@"' "$tool" "$@"
