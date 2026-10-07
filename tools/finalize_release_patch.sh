#!/usr/bin/env bash
# 三平台 Release 包驗收後，於 Docker 內產生發行資產的 SHA-256 清冊。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD}"
DELIVERY="$ROOT/dist-all/$VERSION"
test -d "$DELIVERY/patch" && test -f "$DELIVERY/LICENSE" && test -f "$ROOT/tools/pkg/release_patch_manifest.py"
SOURCE_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
DOSGOLEM_COMMIT="$(git -C "$ROOT/workplace/dosgolem" rev-parse HEAD)"
IMAGE="${HR_GO_IMAGE:-hr-go-ebiten:1.26.7-2.9.9-r1}"
docker image inspect "$IMAGE" >/dev/null
exec timeout 3m docker run --rm --name hr-release-patch-manifest \
  --network none --memory 512m --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" \
  -v "$DELIVERY:/delivery" \
  -v "$ROOT/tools/pkg/release_patch_manifest.py:/manifest.py:ro" \
  "$IMAGE" \
  python3 /manifest.py /delivery "$VERSION" "$SOURCE_COMMIT" "$DOSGOLEM_COMMIT"
