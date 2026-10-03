#!/usr/bin/env bash
# 在 docker 內執行 tools/music 下的單檔 Go 工具（只用標準庫）。
#
#   tools/music/run.sh midiinfo midi /orig/MAP1.MID ...     原版目錄唯讀掛載為 /orig
#   tools/music/run.sh midiinfo pcm /orig/SOUND_E.PCM 0 500 ...
#
# 容器：--network none、唯讀掛載原版、唯一可寫處是 workplace/out/music（容器內 /out）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test -d "$ROOT/workplace/orig" || { echo "缺 workplace/orig" >&2; exit 1; }
test -f "$ROOT/tools/music/${1:?工具名}.go" || { echo "沒有 tools/music/$1.go" >&2; exit 1; }
mkdir -p "$ROOT/workplace/out/music" "$ROOT/workplace/gocache"
tool="$1"; shift
exec timeout 10m docker run --rm --name "hr-music-$$" --network none \
  --memory 2g --cpus 2 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" \
  -v "$ROOT/tools/music:/tools:ro" \
  -v "$ROOT/workplace/orig:/orig:ro" \
  -v "$ROOT/workplace/out/music:/out" \
  -v "$ROOT/workplace/gocache:/gocache" \
  -e GOCACHE=/gocache -e HOME=/tmp \
  -w /tools golang:1.24-bookworm go run "/tools/$tool.go" "$@"
