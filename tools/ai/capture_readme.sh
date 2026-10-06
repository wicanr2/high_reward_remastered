#!/usr/bin/env bash
# 新版完整 AI 圖層的 README 畫面。來源唯讀，截圖先留本機供核對。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LABEL="${1:?請指定未使用的輸出標籤}"
[[ "$LABEL" =~ ^[a-z0-9-]{1,40}$ ]] || exit 2
for path in workplace/orig workplace/out/bin workplace/out workplace/ai-hd/technical/full-theme tools/ai; do
  test -d "$ROOT/$path" || { echo "缺少目錄：$path" >&2; exit 2; }
done
test -f "$ROOT/workplace/out/bin/hr-play"
test -f "$ROOT/tools/ai/capture_readme.py"
test ! -e "$ROOT/workplace/out/$LABEL"
test "$(stat -c %u:%g "$ROOT/workplace/out")" = "$(id -u):$(id -g)"
CONTAINER="hr-ai-readme-$$"
if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "容器名稱已存在：$CONTAINER" >&2
  exit 2
fi
cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
timeout 300s docker run --rm --name "$CONTAINER" --user "$(id -u):$(id -g)" \
  --network none --memory 4g --cpus 2 --pids-limit 256 --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT/workplace/orig:/orig:ro" -v "$ROOT/workplace/out/bin:/binary:ro" \
  -v "$ROOT/workplace/ai-hd/technical/full-theme:/theme:ro" \
  -v "$ROOT/tools/ai:/tools:ro" -v "$ROOT/workplace/out:/out" \
  --entrypoint python3 eob-remake-go:1.26.7-ebiten2.9.9 /tools/capture_readme.py "$LABEL"
