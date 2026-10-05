#!/usr/bin/env bash
# READY 008 3.2.2：正常前端英文冷建包、玩家輸入、重用及回退。
# 本機表／補丁唯讀，畫面與含原版內容的包只在 workplace/out/re-text/。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LABEL="${1:-en-gui}"
[[ "$LABEL" =~ ^[a-z0-9-]{1,40}$ ]] || { echo '輸出標籤不合法' >&2; exit 2; }
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
for path in workplace/dosgolem/apps/hr/play workplace/orig l10n/en workplace/l3-visual-20261005/patches/en-bake5 workplace/out/re-text; do
  test -d "$ROOT/$path" || { echo "缺目錄：$path" >&2; exit 2; }
done
test -f "$ROOT/tools/l10n/verify_en_gui.py" || exit 2
CONTAINER_NAME="hr-en-gui-$$"
CID_FILE="$ROOT/workplace/out/re-text/$LABEL.container-id"
test ! -e "$CID_FILE" && test ! -L "$CID_FILE" || { echo '容器識別檔已存在' >&2; exit 2; }
cleanup() {
  if test -f "$CID_FILE"; then
    local created_id
    IFS= read -r created_id < "$CID_FILE" || true
    if [[ "$created_id" =~ ^[a-f0-9]{64}$ ]]; then
      docker container rm -f "$created_id" >/dev/null 2>&1 || true
    fi
  fi
}
trap cleanup EXIT INT TERM
timeout "${HR_EN_GUI_TIMEOUT:-600s}" docker run --rm --name "$CONTAINER_NAME" --cidfile "$CID_FILE" \
  --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 256 --network none \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT/workplace/dosgolem:/fork:ro" -v "$ROOT/workplace/orig:/orig:ro" \
  -v "$ROOT/l10n:/tables:ro" -v "$ROOT/workplace/l3-visual-20261005/patches/en-bake5:/patch:ro" \
  -v "$ROOT/tools/l10n:/tools:ro" -v "$ROOT/workplace/out/re-text:/out" \
  -e GOCACHE=/tmp/go-cache -e GOPROXY=off -e GOSUMDB=off -e GOFLAGS=-mod=readonly \
  -e GOTOOLCHAIN=local -w /fork/apps/hr/play "$IMAGE" sh -c \
  'set -e; cp -a /go/pkg/mod /tmp/go-mod; export GOMODCACHE=/tmp/go-mod; go build -trimpath -o /tmp/hr-play .; python3 /tools/verify_en_gui.py "$1"' sh "$LABEL"
