#!/usr/bin/env bash
# 驗證實際 AppImage 的可調視窗；所有執行與解包都在 Docker。
# 用法：bash tools/pkg/verify_resize.sh <AppImage> <已存在的輸出目錄>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT="$(realpath "${1:?AppImage 路徑}")"
OUT="$(realpath "${2:?已存在的輸出目錄}")"
test -f "$ARTIFACT" && test -d "$OUT"
test -f "$ROOT/tools/pkg/verify_resize.py"
IMAGE="${HR_GO_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
docker image inspect "$IMAGE" >/dev/null
exec timeout 8m docker run --rm --name hr-resize-verify \
  --network none --memory 3g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e LIBGL_ALWAYS_SOFTWARE=1 -e LP_NUM_THREADS=2 \
  -v "$ARTIFACT:/input/HighReward.AppImage:ro" \
  -v "$ROOT/tools/pkg/verify_resize.py:/verify_resize.py:ro" \
  -v "$OUT:/out" "$IMAGE" python3 /verify_resize.py
