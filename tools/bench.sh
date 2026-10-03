#!/usr/bin/env bash
# 執行層熱迴圈的 A/B 速度比對（docs/spec/005 第 9 節）：兩個 test 執行檔交錯跑 N 次，
# 每個場景印使用者 CPU 時間（user-ns/op）的中位數與 B/A。
#   tools/bench.sh <A> [<B> [次數，預設 5]]
# A、B 是 workplace/out/ 內的檔名，由 `tools/dosgolem.sh go test -c -o /out/<名稱>.test ./apps/hr/runtime/` 建出。
# 戰鬥狀態場景用 workplace/out/explore2/nodes/n00071.state（HR_BENCH_STATE_DIR 與 HR_BENCH_STATE_FILE 可改，缺檔就 skip）。
# 容器：--rm、1 核、2 GB、--network none，原版與狀態檔唯讀掛入。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
A="${1:?test 執行檔 A（workplace/out/ 內的檔名）}"; B="${2:-}"; N="${3:-5}"
SDIR="${HR_BENCH_STATE_DIR:-$ROOT/workplace/out/explore2/nodes}"
SFILE="${HR_BENCH_STATE_FILE:-n00071.state}"
test -x "$ROOT/workplace/out/$A" || { echo "缺 workplace/out/$A" >&2; exit 1; }
test -d "$ROOT/workplace/orig" || { echo "缺 workplace/orig" >&2; exit 1; }
SMOUNT=(); SENV=()
if [ -f "$SDIR/$SFILE" ]; then SMOUNT=(-v "$SDIR:/state:ro"); SENV=(-e "HR_BENCH_STATE=/state/$SFILE"); fi
one() { # $1 = 檔名；印「場景 user-ns/op」
  timeout 30m docker run --rm --network none --memory 2g --cpus 1 --pids-limit 256 \
    --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
    -v "$ROOT/workplace/out:/out:ro" -v "$ROOT/workplace/orig:/orig/orig:ro" "${SMOUNT[@]}" "${SENV[@]}" -e HOME=/tmp -w /tmp "$IMAGE" \
    "/out/$1" -test.run XXX -test.bench RunSteps -test.benchtime 1x -test.count 1 \
    | awk '/^BenchmarkRunSteps/ { for (i = 1; i <= NF; i++) if ($i == "user-ns/op") { n = $1; sub(/^BenchmarkRunSteps\//, "", n); sub(/-[0-9]+$/, "", n); print n, $(i-1) } }'
}
OUT="$(mktemp)"; trap 'rm -f "$OUT"' EXIT
for i in $(seq 1 "$N"); do
  one "$A" | sed "s/^/A /" | tee -a "$OUT" >&2
  if [ -n "$B" ]; then one "$B" | sed "s/^/B /" | tee -a "$OUT" >&2; fi
done
awk '
  { k = $1 " " $2; v[k] = v[k] " " $3; sc[$2] = 1 }
  function med(s,   a, n, i, j, t) { n = split(s, a, " "); for (i = 1; i <= n; i++) for (j = i + 1; j <= n; j++) if (a[j] + 0 < a[i] + 0) { t = a[i]; a[i] = a[j]; a[j] = t } return a[int((n + 1) / 2)] }
  END {
    for (s in sc) {
      ma = med(v["A " s]); line = sprintf("%-14s A %.3f s", s, ma / 1e9)
      if (("B " s) in v) { mb = med(v["B " s]); line = line sprintf("  B %.3f s  B/A %.3f", mb / 1e9, mb / ma) }
      print line
    }
  }' "$OUT"
