#!/usr/bin/env bash
# IDA Pro 9.4 headless 包裝（image：ida-pro-9.4-idapython:locked-v1，非 root）。
#
#   tools/ida.sh run <原版檔名> <腳本.py> [腳本參數…]
#
# 每次對 workplace/ida/run/ 內的全新資料庫執行（原版檔從 workplace/orig/ 唯讀掛載後複製），
# 腳本結果一律寫到容器內 /work/out/，對應主機的 workplace/ida/out/。
# 工作目錄預設 workplace/ida，可用 HR_IDA_WORK 指到別處（多個工作同時跑時各用各的）。
# IDAPython 的 stdout 看不到、exit code 不可信：唯一的證據是輸出檔，
# 呼叫端要自己驗輸出檔存在、非空、時間戳更新。
# 腳本結尾要 ida_pro.qexit(0)。對同一資料庫的批次合併成單次執行。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${HR_IDA_IMAGE:-ida-pro-9.4-idapython:locked-v1}"
MODE="${1:-}"; EXE="${2:-}"; SCRIPT="${3:-}"
[[ "$MODE" == run && -n "$EXE" && -n "$SCRIPT" ]] || { sed -n 2,13p "$0" >&2; exit 2; }
shift 3
test -f "$ROOT/workplace/orig/$EXE" || { echo "缺原版檔: workplace/orig/$EXE" >&2; exit 1; }
test -f "$ROOT/tools/$SCRIPT" || { echo "缺腳本: tools/$SCRIPT" >&2; exit 1; }
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "缺 image: $IMAGE" >&2; exit 3; }
WORK="${HR_IDA_WORK:-$ROOT/workplace/ida}"; RUN="$WORK/run"; OUT="$WORK/out"
mkdir -p "$RUN" "$RUN/out" "$OUT"
cp -f "$ROOT/workplace/orig/$EXE" "$RUN/$EXE"
sha256sum "$RUN/$EXE" >&2
exec timeout "${HR_IDA_TIMEOUT:-20m}" docker run --rm --network none \
  --memory 4g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" \
  -v "$RUN:/work" -v "$OUT:/work/out" -v "$ROOT/tools:/tools:ro" -w /work \
  "$IMAGE" idat -A -c "-S/tools/$SCRIPT $*" "$EXE"
