#!/usr/bin/env bash
# 在容器內產生原版壓縮檔清冊（docs/re/source-inventory.tsv）。
# 原版輸入唯讀掛載，輸出只寫 docs/re。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for f in "$ROOT/workplace/dl/hr_src.jsdos.zip" "$ROOT/workplace/dl/hr_src.zip" "$ROOT/tools/inventory.py"; do
  test -f "$f" || { echo "缺檔: $f" >&2; exit 1; }
done
test -d "$ROOT/docs/re" || { echo "缺目錄: docs/re" >&2; exit 1; }
timeout 120 docker run --rm -u "$(id -u):$(id -g)" --network none \
  --memory 512m --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT/workplace/dl:/in:ro" -v "$ROOT/tools:/tools:ro" -v "$ROOT/docs/re:/out" \
  python:3.13-alpine \
  python /tools/inventory.py /in/hr_src.jsdos.zip /in/hr_src.zip /out/source-inventory.tsv
