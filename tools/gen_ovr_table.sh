#!/usr/bin/env bash
# 產生 workplace/dosgolem/apps/hr/runtime/ovrtab.go（docs/spec/005 第 5.1 節）。全部在容器內。
#   tools/gen_ovr_table.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
J="$ROOT/workplace/re-ovr/out/overlays.json"
D="$ROOT/workplace/dosgolem/apps/hr/runtime"
test -f "$J" || { echo "缺 $J" >&2; exit 1; }
test -d "$D" || { echo "缺 $D" >&2; exit 1; }
exec timeout 5m docker run --rm --network none --memory 512m --cpus 1 --pids-limit 32 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$J:/in/overlays.json:ro" -v "$ROOT/tools:/s:ro" -v "$D:/out" -w /tmp \
  "${HR_PKG_IMAGE:-yuan-analysis:1}" python3 /s/gen_ovr_table.py /in/overlays.json /out/ovrtab.go
