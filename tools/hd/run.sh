#!/usr/bin/env bash
# 在容器內執行 tools/hd 的 Python 腳本（PIL、numpy、scipy）。
#   tools/hd/run.sh upscale.py /w/re-img/out /w/hd-work/x2 2
#   tools/hd/run.sh validate.py /w/re-img/out /w/hd-work/x2 2
# 映像預設 yuan-analysis:1（本機已有，含 PIL、numpy、scipy），用 HR_HD_IMAGE 覆蓋。
# 掛載：workplace 讀寫為 /w，tools/hd 唯讀為 /s。預設 --network none。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="${1:?腳本名}"; shift
test -f "$ROOT/tools/hd/$SCRIPT" || { echo "缺腳本 tools/hd/$SCRIPT" >&2; exit 1; }
test -d "$ROOT/workplace" || { echo "缺 workplace" >&2; exit 1; }
exec timeout "${HR_HD_TIMEOUT:-30m}" docker run --rm --network none \
  --memory "${HR_HD_MEM:-4g}" --cpus "${HR_HD_CPUS:-2}" --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" -e PYTHONPATH=/s \
  -v "$ROOT/workplace:/w" -v "$ROOT/tools/hd:/s:ro" -w /w \
  "${HR_HD_IMAGE:-yuan-analysis:1}" python3 "/s/$SCRIPT" "$@"
