#!/usr/bin/env bash
# 在容器內執行 tools/pkg 的 Python 腳本（PIL）。映像預設 yuan-analysis:1，用 HR_PKG_IMAGE 覆蓋。
#   tools/pkg/py.sh appicon.py /w/pkg-stage/icon 
# 掛載：workplace 讀寫為 /w，tools/pkg 唯讀為 /s。預設 --network none。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="${1:?腳本名}"; shift
test -f "$ROOT/tools/pkg/$SCRIPT" || { echo "缺腳本 tools/pkg/$SCRIPT" >&2; exit 1; }
mkdir -p "$ROOT/workplace"
orig_mount=()
if [ -d "$ROOT/workplace/orig" ]; then
  orig_mount=(-v "$ROOT/workplace/orig:/w/orig:ro")
fi
exec timeout "${HR_PKG_TIMEOUT:-10m}" docker run --rm --network none \
  --memory 1g --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" -e PYTHONPATH=/s \
  -v "$ROOT/workplace:/w" "${orig_mount[@]}" -v "$ROOT/tools/pkg:/s:ro" -w /w \
  "${HR_PKG_IMAGE:-yuan-analysis:1}" python3 "/s/$SCRIPT" "$@"
