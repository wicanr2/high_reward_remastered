#!/usr/bin/env bash
# 本機完整版封包與影片均驗收後，在 Docker 內寫入 SHA256SUMS.json。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD}"
DELIVERY="$ROOT/dist-all/$VERSION"
test -d "$DELIVERY" && test -f "$ROOT/tools/pkg/full_local_manifest.py" && test -f "$ROOT/LICENSE"
docker image inspect eob-remake-release:1.26.7-ebiten2.9.9-audio >/dev/null
exec timeout 3m docker run --rm --name hr-full-local-manifest \
  --network none --memory 512m --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" \
  -v "$DELIVERY:/delivery" \
  -v "$ROOT/tools/pkg/full_local_manifest.py:/manifest.py:ro" \
  -v "$ROOT/LICENSE:/license:ro" \
  eob-remake-release:1.26.7-ebiten2.9.9-audio \
  python3 /manifest.py /delivery "$VERSION"
