#!/usr/bin/env bash
# 洩漏判準掃描（docs/spec/008 第 3.9 節）：依原版七個資料檔與 OP*.TXT 的文字單位，
# 找出版控、docs、tools、fork 或發行包內夾帶的原版對白與敘述。輸出只有路徑與單位身分，不輸出內容。
#
#   tools/l10n/leakscan.sh                 工作樹：本 repo 的 git ls-files 加 fork 的 git ls-files
#   tools/l10n/leakscan.sh <路徑…>          只掃指定的檔案或目錄（repo 相對路徑，例如打包暫存目錄）
#   tools/l10n/leakscan.sh --history       全歷史：本 repo 與 fork 各自 git rev-list --all 的全部 blob
#   tools/l10n/leakscan.sh --check-allow   只驗證 tools/l10n/leakscan-allow.tsv
#
# 退出碼：0 無命中，1 有命中，2 閘門失敗或用法錯誤（原版缺席、雜湊不符、allowlist 無效、掃描範圍為空）。
# 原版缺席時失敗，不略過（AGENTS.md 第 10 節）。
# 全部在 Docker：--rm、目前 UID、--network none、repo 與原版唯讀。主機只跑 git 產生檔案清單與歷史串流。
# hrl10n 的原始碼在 fork（workplace/dosgolem 的 hr 分支，apps/hr/cmd/hrl10n）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
DG="workplace/dosgolem"
ALLOW="tools/l10n/leakscan-allow.tsv"
IMAGE="${HR_L10N_IMAGE:-${DOSGOLEM_GO_IMAGE:-golang:1.24-bookworm}}"
OUT="workplace/out"
BIN="$OUT/hrl10n"
ORIG="workplace/orig"

test -f "$DG/apps/hr/cmd/hrl10n/main.go" || { echo "缺 $DG/apps/hr/cmd/hrl10n（fork 的 hr 分支）" >&2; exit 2; }
test -f "$ORIG/MAIN.EXE" || { echo "缺 $ORIG/MAIN.EXE：原版缺席，閘門失敗（不略過）" >&2; exit 2; }
test -f "$ALLOW" || { echo "缺 $ALLOW" >&2; exit 2; }
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "缺映像 $IMAGE" >&2; exit 2; }
mkdir -p "$OUT" workplace/gocache workplace/gomodcache

# 共用的 docker run 前綴。$1 是額外 docker 參數的陣列名稱前綴由呼叫端展開，這裡只放不變的部分。
drun() { # 用法：drun [額外 docker 參數…] -- <指令…>
  local extra=()
  while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do extra+=("$1"); shift; done
  shift
  timeout "${HR_L10N_TIMEOUT:-20m}" docker run --rm --network none \
    --memory "${HR_L10N_MEM:-2g}" --cpus "${HR_L10N_CPUS:-2}" --pids-limit 256 \
    --log-opt max-size=10m --log-opt max-file=3 \
    --name "hr-leakscan-$$-$RANDOM" \
    -u "$(id -u):$(id -g)" "${extra[@]}" "$IMAGE" "$@"
}

# 建出 hrl10n（離線：module cache 在 workplace/gomodcache）。fork 唯讀掛載，go.mod 與 go.sum 必須已經完整。
build() {
  drun -v "$ROOT/$DG:/src:ro" -v "$ROOT/$OUT:/out" -v "$ROOT/workplace/gocache:/gocache" -v "$ROOT/workplace/gomodcache:/gomodcache" \
    -e GOCACHE=/gocache -e GOMODCACHE=/gomodcache -e GOFLAGS=-mod=readonly -e GOPROXY=off -e GOSUMDB=off \
    -e CGO_ENABLED=0 -w /src -- go build -trimpath -o /out/hrl10n ./apps/hr/cmd/hrl10n
}

# 執行 hrl10n leakscan。repo 唯讀掛在 /repo（原版在 /repo/workplace/orig），工作目錄 /repo，路徑一律 repo 相對。
# 標準輸入要傳進容器，所以加 -i。
scan() {
  drun -i -v "$ROOT:/repo:ro" -w /repo -- "/repo/$BIN" leakscan -orig "/repo/$ORIG" "$@"
}

# 工作樹清單：NUL 分隔，repo 相對路徑。fork 的路徑加 workplace/dosgolem/ 前綴，與 allowlist 的路徑空間一致。
tracked_list() {
  # 使用者 2026-10-06 授權 private repo 收錄 l10n TSV 的原文欄。
  # 只排除正式表與純 Noto 碼表；其他路徑與所有編譯語言包照常掃描。
  git -c core.quotepath=off ls-files -z | while IFS= read -r -d '' p; do
    case "$p" in
      l10n/zh-TW/*.tsv|l10n/zh-CN/*.tsv|l10n/ja/*.tsv|l10n/ko/*.tsv|l10n/en/*.tsv) continue ;;
    esac
    printf '%s\0' "$p"
  done
  git -C "$DG" -c core.quotepath=off ls-files -z | while IFS= read -r -d '' p; do
    printf '%s/%s\0' "$DG" "$p"
  done
}

# 歷史串流：<commit>\t<路徑>\t<大小>\n<內容>\n …，以 END\t<記錄數>\n 結尾。
# 每個 (路徑, blob) 只記第一次出現的 commit。路徑含 Tab 或換行時失敗，不猜。
history_stream() { # $1 git 目錄（. 或 fork）$2 路徑前綴（空或 workplace/dosgolem/）
  local gdir="$1" prefix="$2" n=0 commit meta path oldmode newmode oldsha sha status
  declare -A seen=()
  while IFS= read -r commit; do
    while IFS= read -r -d '' meta && IFS= read -r -d '' path; do
      # meta：:<舊模式> <新模式> <舊 sha> <新 sha> <狀態>
      read -r oldmode newmode oldsha sha status <<<"${meta#:}"
      case "$newmode" in 160000) continue ;; esac         # submodule
      case "$sha" in 0000000000000000000000000000000000000000) continue ;; esac
      case "$path" in *$'\t'*|*$'\n'*) echo "歷史串流：路徑含 Tab 或換行，無法安全編碼：$commit" >&2; return 1 ;; esac
      [ -n "${seen[$sha:$path]:-}" ] && continue
      seen[$sha:$path]=1
      printf '%s\t%s%s\t%s\n' "$commit" "$prefix" "$path" "$(git -C "$gdir" cat-file -s "$sha")"
      git -C "$gdir" cat-file blob "$sha"
      printf '\n'
      n=$((n + 1))
    done < <(git -C "$gdir" -c core.quotepath=off diff-tree -r -z -m --root --no-renames --no-commit-id --diff-filter=AMT "$commit")
  done < <(git -C "$gdir" rev-list --all)
  printf 'END\t%d\n' "$n"
}

mode="tree"
case "${1:-}" in
  --history) mode="history"; shift ;;
  --check-allow) mode="check"; shift ;;
esac
if [ "$mode" != "tree" ] && [ "$#" -gt 0 ]; then
  echo "--history 與 --check-allow 不接受路徑參數" >&2; exit 2
fi

build >&2

rc=0
case "$mode" in
  check)
    scan -check-allow "$ALLOW" </dev/null || rc=$?
    ;;
  history)
    for g in "." "$DG"; do
      prefix=""; [ "$g" = "." ] || prefix="$DG/"
      echo "[leakscan] 歷史：$g" >&2
      r=0
      history_stream "$g" "$prefix" | scan -allow "$ALLOW" -history || r=$?
      if [ "$r" -gt "$rc" ]; then rc=$r; fi
    done
    ;;
  tree)
    if [ "$#" -gt 0 ]; then
      scan -allow "$ALLOW" "$@" </dev/null || rc=$?
    else
      tracked_list | scan -allow "$ALLOW" -files-from0 - -skip-missing || rc=$?
    fi
    ;;
esac
exit "$rc"
