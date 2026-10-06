#!/usr/bin/env bash
# 在隔離容器內建置正式版號的三平台發行包，原版來源唯讀且不入包。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD}"
[[ "$VERSION" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]] || { echo "版號格式錯誤" >&2; exit 2; }
test -z "$(git -C "$ROOT" status --porcelain)" || { echo "正式發行包需要乾淨工作樹" >&2; exit 2; }
test -z "$(git -C "$ROOT/workplace/dosgolem" status --porcelain)" || { echo "dosgolem 副本需要乾淨工作樹" >&2; exit 2; }
TARGET="${1:-all}"
case "$TARGET" in all|appimage|windows|macos) ;; *) echo "目標需為 all、appimage、windows 或 macos" >&2; exit 2;; esac
IMAGE="eob-remake-release:1.26.7-ebiten2.9.9-audio"
test -d "$ROOT/workplace" && test -d "$ROOT/workplace/orig" && test -d "$ROOT/dist-all"
test -f "$ROOT/tools/package.sh" && test -f "$ROOT/workplace/orig/MAIN.EXE"
test -f /usr/bin/docker && test -S /var/run/docker.sock
docker image inspect "$IMAGE" >/dev/null
exec timeout "${HR_RELEASE_TIMEOUT:-3h}" docker run --rm --name hr-release-patch-build \
  --network none --memory 2g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" --group-add "$(stat -c %g /var/run/docker.sock)" \
  -e HR_RELEASE_PATCH=1 -e HR_WITH_HD=1 -e "HR_VERSION=$VERSION" \
  -e "HR_FULL_EXTRAS=${HR_FULL_EXTRAS:-1}" \
  -v /usr/bin/docker:/usr/local/bin/docker:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$ROOT:$ROOT:ro" \
  -v "$ROOT/workplace:$ROOT/workplace" \
  -v "$ROOT/workplace/orig:$ROOT/workplace/orig:ro" \
  -v "$ROOT/dist-all:$ROOT/dist-all" \
  -w "$ROOT" --entrypoint bash "$IMAGE" tools/package.sh "$TARGET"
