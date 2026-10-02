#!/usr/bin/env bash
# 在 Docker 內重跑全部圖像解碼：輸出 workplace/re-img/out/（PNG 與 decode_log.txt）與 inventory.tsv。
# 原版目錄 workplace/orig 唯讀掛載；只用 python:3.13-alpine 的標準庫。解出的 PNG 是原版美術的衍生物，
# 只留在 workplace/（已 gitignore），不進 repo。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
W="$ROOT/workplace/re-img"
test -f "$ROOT/workplace/orig/MAIN.EXE" || { echo "缺 workplace/orig/MAIN.EXE" >&2; exit 1; }
mkdir -p "$W"
cp -f "$ROOT/tools/img/hrimg.py" "$ROOT/tools/img/decode_all.py" "$W/"
rm -rf -- "$W/out"; mkdir -p "$W/out"
exec timeout 900 docker run --rm -u "$(id -u):$(id -g)" --network none \
  --memory 1g --cpus 2 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT/workplace/orig:/orig:ro" -v "$W:/w" -w /w \
  python:3.13-alpine python3 /w/decode_all.py
