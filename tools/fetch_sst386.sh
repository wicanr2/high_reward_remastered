#!/usr/bin/env bash
# 抓 SingleStepTests/80386 的 real mode 測資到 workplace/testdata/80386/v1_ex_real_mode/（gitignore）。
#
#   tools/fetch_sst386.sh 668B 669C 66C1.5 0FA1
#
# 檔名對照語料的 `<名稱>.MOO.gz`；群組 opcode 以 `.<reg>` 結尾。語料授權是它自己的，不隨本 repo 散布。
# 在容器內以 Python urllib 下載（需要網路），已存在且非空的檔案略過。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/workplace/testdata/80386/v1_ex_real_mode"
mkdir -p "$OUT"
[[ $# -gt 0 ]] || { sed -n 2,6p "$0" >&2; exit 2; }
exec timeout 600 docker run --rm -u "$(id -u):$(id -g)" --memory 256m --cpus 1 --pids-limit 32 \
  --log-opt max-size=10m --log-opt max-file=3 -v "$OUT:/out" python:3.13-alpine python -c '
import os, sys, urllib.request
base = "https://raw.githubusercontent.com/SingleStepTests/80386/main/v1_ex_real_mode/"
for n in sys.argv[1:]:
    f = f"/out/{n}.MOO.gz"
    if os.path.exists(f) and os.path.getsize(f) > 0:
        print("skip", n); continue
    req = urllib.request.Request(base + n + ".MOO.gz", headers={"User-Agent": "Mozilla/5.0"})
    b = urllib.request.urlopen(req, timeout=120).read()
    open(f + ".part", "wb").write(b); os.rename(f + ".part", f); print("got", n, len(b))
' "$@"
