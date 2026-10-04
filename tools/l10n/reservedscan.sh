#!/usr/bin/env bash
# M10 L2 靜態保留碼初測。結果只寫 workplace/out/re-text/。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
for path in "$ROOT/workplace/dosgolem" "$ROOT/workplace/orig" "$ROOT/workplace/ida-text/out" "$ROOT/workplace/out/re-text" "$ROOT/docs/re" "$ROOT/tools/l10n"; do
  test -d "$path" || { echo "缺少目錄：$path" >&2; exit 1; }
done
test -f "$ROOT/docs/re/source-inventory.tsv" || { echo "缺原版 SHA-256 清冊" >&2; exit 1; }
test -f "$ROOT/tools/l10n/reservedscan.go" || { echo "缺掃描程式" >&2; exit 1; }
IMAGE_ID="$(docker image inspect "$IMAGE" --format '{{.Id}}')"

exec timeout 5m docker run --rm --network none --memory 2g --cpus 2 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$ROOT/workplace/dosgolem:/fork:ro" \
  -v "$ROOT/workplace/orig:/orig:ro" \
  -v "$ROOT/workplace/ida-text/out:/ida:ro" \
  -v "$ROOT/docs/re:/inventory:ro" \
  -v "$ROOT/tools/l10n:/tools:ro" \
  -v "$ROOT/workplace/out/re-text:/out" \
  -w /fork -e HOME=/tmp -e GOCACHE=/tmp/go-cache -e GOPROXY=off -e GOFLAGS=-mod=mod -e HR_IMAGE_ID="$IMAGE_ID" \
  --entrypoint go "$IMAGE" run /tools/reservedscan.go
