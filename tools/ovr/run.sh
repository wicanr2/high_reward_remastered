#!/usr/bin/env bash
# 在 Docker 內抽取 MAIN.EXE 的 FBOV overlay 並做 28 項驗證：輸出 workplace/re-ovr/out/（verify.txt 等）。
#   tools/ovr/run.sh [ovr_extract.py 的其他參數…]
# 結束碼 0 ＝ 全部 PASS。抽出的 overlay 二進位是原版程式碼，只留在 workplace/（已 gitignore）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
W="$ROOT/workplace/re-ovr"
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig/MAIN.EXE" >&2; exit 1; }
mkdir -p "$W/out"
cp -f "$ROOT/tools/ovr/ovr_extract.py" "$W/"
EXTRA=(); [[ -d "$W/ida/out/all/idaovr" ]] && EXTRA=(--compare-ida /w/ida/out/all/idaovr)
exec timeout 300 docker run --rm -u "$(id -u):$(id -g)" --network none --memory 1g --cpus 2 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT/workplace/orig:/orig:ro" -v "$W:/w" -w /w python:3.13-alpine \
  python3 /w/ovr_extract.py /orig/MAIN.EXE --out /w/out "${EXTRA[@]}" "$@"
