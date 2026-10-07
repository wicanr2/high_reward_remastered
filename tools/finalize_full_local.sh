#!/usr/bin/env bash
# 本機完整版驗收後寫入 SHA256SUMS.json；本輪另有推廣片時一併登錄。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD}"
DELIVERY="$ROOT/dist-all/$VERSION"
SOURCE_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
DOSGOLEM_COMMIT="$(git -C "$ROOT/workplace/dosgolem" rev-parse HEAD)"
test -d "$DELIVERY" && test -f "$ROOT/tools/pkg/full_local_manifest.py" && test -f "$ROOT/LICENSE"
IMAGE="${HR_GO_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
docker image inspect "$IMAGE" >/dev/null
exec timeout 3m docker run --rm --name hr-full-local-manifest \
  --network none --memory 512m --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" \
  -e "HR_SOURCE_COMMIT=$SOURCE_COMMIT" -e "HR_DOSGOLEM_COMMIT=$DOSGOLEM_COMMIT" \
  -v "$DELIVERY:/delivery" \
  -v "$ROOT/tools/pkg/full_local_manifest.py:/manifest.py:ro" \
  -v "$ROOT/LICENSE:/license:ro" \
  "$IMAGE" \
  python3 /manifest.py /delivery "$VERSION"
