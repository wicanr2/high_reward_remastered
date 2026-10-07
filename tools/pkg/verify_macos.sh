#!/usr/bin/env bash
# macOS bundle 的靜態驗收（Linux 上執行不了 macOS 執行檔，只能驗結構）。
#   tools/pkg/verify_macos.sh <HighReward.app 目錄>
# 檢查：Info.plist 是格式正確的 XML 且含必要鍵；執行檔是 universal Mach-O（arm64 與 x86_64）；
# 圖示存在；沒有指向 Linux 路徑的連結。⚠ 結構過關不等於功能正常，沒有在實機驗證。
set -euo pipefail
APP="${1:?bundle 目錄}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${HR_MAC_IMAGE:-hr-osxcross:1.26.7-15.5-r1}"
fail() { echo "[verify-macos] 失敗：$*" >&2; exit 1; }
test -f "$APP/Contents/Info.plist" || fail "缺 Info.plist"
test -x "$APP/Contents/MacOS/hr-play" || fail "缺執行檔或沒有執行位元"
test -s "$APP/Contents/Resources/hr-play.icns" || fail "缺圖示"
for k in CFBundleExecutable CFBundleIdentifier CFBundleIconFile CFBundlePackageType LSMinimumSystemVersion; do
  grep -q "<key>$k</key>" "$APP/Contents/Info.plist" || fail "Info.plist 缺 $k"
done
# 容器內檢查 Mach-O 與 plist 格式（--network none、唯讀掛載）
timeout 60s docker run --rm --network none --memory 512m --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$(cd "$APP" && pwd):/app:ro" "$IMAGE" bash -c '
    set -euo pipefail
    eval "$(osxcross-conf)"
    info=$(x86_64-apple-$OSXCROSS_TARGET-lipo -info /app/Contents/MacOS/hr-play)
    echo "$info"
    case "$info" in *arm64*) ;; *) echo "缺 arm64"; exit 1;; esac
    case "$info" in *x86_64*) ;; *) echo "缺 x86_64"; exit 1;; esac
    head -c 4 /app/Contents/Resources/hr-play.icns | grep -q icns || { echo "icns 檔頭錯誤"; exit 1; }
    if command -v xmllint >/dev/null; then xmllint --noout /app/Contents/Info.plist; else echo "（映像沒有 xmllint，略過 plist 格式檢查）"; fi
  ' || fail "容器內檢查"
echo "[verify-macos] 結構檢查通過（未在實機驗證）"
