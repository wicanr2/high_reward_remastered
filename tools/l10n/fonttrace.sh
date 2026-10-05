#!/usr/bin/env bash
# L2 原版連續字模觀測，研究副本不進正式 runtime。證據入口 docs/re/032。
#   bash tools/l10n/fonttrace.sh build
#   bash tools/l10n/fonttrace.sh run NAME plain|traced [hrbot 參數]
#   bash tools/l10n/fonttrace.sh audit NAME
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GO_IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
OUT="$ROOT/workplace/out/re-text/fonttrace"
for path in "$ROOT/workplace/dosgolem" "$ROOT/workplace/orig" "$ROOT/tools/l10n" "$ROOT/docs/re" "$ROOT/workplace/out/re-text"; do
  test -d "$path" || { echo "缺少目錄：$path" >&2; exit 1; }
done
test -f "$ROOT/tools/l10n/fonttrace.py"
test -f "$ROOT/docs/re/source-inventory.tsv"
test -f "$ROOT/workplace/out/re-text/m10-reserved-codes.tsv"
mkdir -p "$OUT"
test "$(stat -c %u:%g "$OUT")" = "$(id -u):$(id -g)" || { echo "輸出目錄擁有權不符" >&2; exit 1; }
COMMON=(--rm --network none --memory 2g --cpus 1 --pids-limit 128 --log-opt max-size=10m --log-opt max-file=3 --user "$(id -u):$(id -g)"
  -v "$ROOT/workplace/orig:/orig:ro" -v "$ROOT/docs/re:/inventory:ro" -v "$ROOT/tools/l10n:/tools:ro" -v "$OUT:/out")
case "${1:-}" in
  build)
    IMAGE_ID="$(docker image inspect "$GO_IMAGE" --format '{{.Id}}')"
    timeout 5m docker run "${COMMON[@]}" --name hr-fonttrace-build -v "$ROOT/workplace/dosgolem:/fork:ro" -e HR_IMAGE_ID="$IMAGE_ID" \
      -e GOCACHE=/tmp/go-cache -e GOPROXY=off -e GOSUMDB=off -e GOTOOLCHAIN=local --entrypoint sh "$GO_IMAGE" -c \
      'set -eu; python3 /tools/fonttrace.py prepare; cd /out/plain; go build -o /out/hrbot-plain ./apps/hr/cmd/hrbot; cd /out/traced; go build -o /out/hrbot-traced ./apps/hr/cmd/hrbot; go version > /out/go-version.txt; sha256sum /out/hrbot-* > /out/binary-sha256.txt'
    ;;
  run)
    NAME="${2:?名稱}"; MODE="${3:?plain 或 traced}"; shift 3
    [[ "$NAME" =~ ^[a-z0-9-]+$ ]] && [[ "$MODE" = plain || "$MODE" = traced ]]
    test -x "$OUT/hrbot-$MODE"
    test ! -e "$OUT/$NAME" || { echo "不覆寫既有收據" >&2; exit 1; }
    timeout "${HR_FONTTRACE_TIMEOUT:-3h}" docker run "${COMMON[@]}" --name "hr-fonttrace-$NAME" -e HOME=/tmp -e HR_FONT_TRACE="/out/$NAME/font-calls.tsv" \
      --entrypoint python3 "$GO_IMAGE" /tools/fonttrace.py run "$NAME" "$MODE" "$@"
    ;;
  audit)
    NAME="${2:?名稱}"; [[ "$NAME" =~ ^[a-z0-9-]+$ ]]
    timeout 1m docker run "${COMMON[@]}" --name hr-fonttrace-audit -v "$ROOT/workplace/out/re-text:/reserved:ro" \
      --entrypoint python3 "$GO_IMAGE" /tools/fonttrace.py audit "$NAME"
    ;;
  *) echo "build | run NAME plain|traced [hrbot 參數] | audit NAME" >&2; exit 2 ;;
esac
