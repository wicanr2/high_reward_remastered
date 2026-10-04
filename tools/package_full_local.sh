#!/usr/bin/env bash
# 在隔離容器內編排本機完整版；所有檔案處理、建置與封裝都在 Docker。
# 原版來源唯讀掛載；交付只寫到 dist-all/<版本>/full-local/。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD}"
IMAGE="eob-remake-release:1.26.7-ebiten2.9.9-audio"
test -d "$ROOT/workplace" && test -d "$ROOT/workplace/orig" && test -d "$ROOT/dist-all"
test -f "$ROOT/tools/package.sh" && test -f "$ROOT/workplace/orig/MAIN.EXE"
test -f /usr/bin/docker && test -S /var/run/docker.sock
docker image inspect "$IMAGE" >/dev/null
exec timeout "${HR_FULL_TIMEOUT:-3h}" docker run --rm --name hr-full-local-build \
  --network none --memory 2g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" --group-add "$(stat -c %g /var/run/docker.sock)" \
  -e HR_FULL_LOCAL=1 -e HR_WITH_HD=1 -e "HR_VERSION=$VERSION" \
  -v /usr/bin/docker:/usr/local/bin/docker:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$ROOT:$ROOT:ro" \
  -v "$ROOT/workplace:$ROOT/workplace" \
  -v "$ROOT/workplace/orig:$ROOT/workplace/orig:ro" \
  -v "$ROOT/dist-all:$ROOT/dist-all" \
  -w "$ROOT" --entrypoint bash "$IMAGE" tools/package.sh all
