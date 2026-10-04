#!/usr/bin/env bash
# 發行包（docs/spec/003 第 8 節）。一般包產出放 dist-all/，每個平台只留最新一份。
# HR_FULL_LOCAL=1 且 HR_VERSION 為正式版號時，另產出 dist-all/<版本>/full-local/；
# 原版逐檔核對 docs/re/source-inventory.tsv，僅供本機交付，絕不提交或上傳。
#
#   tools/package.sh appimage   Linux：HighReward-<版本>-x86_64.AppImage
#   tools/package.sh windows    HighReward-<版本>-win64.zip
#   tools/package.sh macos      HighReward-<版本>-macos.zip（universal：arm64 加 x86_64，未簽章）
#   tools/package.sh all
#
# 一般發行包不含原版素材（AGENTS.md 第 2 節）：玩家自備，放在執行檔旁的 original/。
# 產出前以 tools/pkg/leakscan.py 依 docs/re/source-inventory.tsv 的檔名與雜湊掃描，有命中就不出包。
# 建置一律在 Docker（--rm、目前 UID、--network none）。映像用本機已有的：
#   Go 與 ebiten 2.9.9：eob-remake-go:1.26.7-ebiten2.9.9      （HR_GO_IMAGE）
#   macOS 交叉編譯：    psychicwar-osxcross:latest              （HR_MAC_IMAGE）
#   AppImage：          psychicwar-appimage:latest              （HR_APPIMAGE_IMAGE）
# 這些映像屬於其他專案，這裡只 `docker run --rm`，不修改、不刪除。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
TARGET="${1:-all}"
DG="workplace/dosgolem"
WITH_HD="${HR_WITH_HD:-0}"   # 1 ＝ 把 hd/ 放進包內（含原版美術的衍生物，只供私人流通）
FULL_LOCAL="${HR_FULL_LOCAL:-0}" # 1 ＝ 本機完整版
RELEASE_PATCH="${HR_RELEASE_PATCH:-0}" # 1 ＝ 正式版號、不含原版的私人 Release 包
HRV="$(git describe --tags --always --dirty 2>/dev/null || echo dev)"
DGV="$(git -C "$DG" rev-parse --short HEAD 2>/dev/null || echo unknown)"
VER="${HR_VERSION:-$HRV-dg$DGV}"
if [ "$FULL_LOCAL" = 1 ] || [ "$RELEASE_PATCH" = 1 ]; then
  [[ "$VER" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]] || { echo "完整版需要 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD" >&2; exit 2; }
fi
if [ "$FULL_LOCAL" = 1 ] && [ "$RELEASE_PATCH" = 1 ]; then
  echo "HR_FULL_LOCAL 與 HR_RELEASE_PATCH 不能同時使用" >&2; exit 2
fi
if [ "$FULL_LOCAL" = 1 ]; then
  test -d workplace/orig || { echo "缺 workplace/orig" >&2; exit 2; }
  DIST="dist-all/$VER/full-local"
  STAGE="workplace/pkg-stage-full-local"
elif [ "$RELEASE_PATCH" = 1 ]; then
  DIST="dist-all/$VER/patch"
  STAGE="workplace/pkg-stage-release-patch"
else
  if [ "$WITH_HD" = 1 ]; then VER="$VER-hd"; fi
  DIST="dist-all"
  if [ "$WITH_HD" = 1 ]; then DIST="dist-all/with-hd"; fi
  STAGE="workplace/pkg-stage"
fi
GO_IMAGE="${HR_GO_IMAGE:-eob-remake-go:1.26.7-ebiten2.9.9}"
MAC_IMAGE="${HR_MAC_IMAGE:-psychicwar-osxcross:latest}"
APPIMAGE_IMAGE="${HR_APPIMAGE_IMAGE:-psychicwar-appimage:latest}"
INV="docs/re/source-inventory.tsv"
mkdir -p "$DIST" "$STAGE" workplace/gocache workplace/out

for img in "$GO_IMAGE"; do
  docker image inspect "$img" >/dev/null 2>&1 || { echo "缺映像 $img" >&2; exit 3; }
done
test -f "$DG/apps/hr/play/go.mod" || { echo "缺 $DG/apps/hr/play" >&2; exit 1; }
test -f "$INV" || { echo "缺 $INV" >&2; exit 1; }

# 共用的 docker run 前綴（唯讀的網路與資源限制寫在這裡，不在各處重複）。
drun() { # 用法：drun <映像> [額外 docker 參數…] -- <指令…>
  local image="$1"; shift
  local extra=()
  while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do extra+=("$1"); shift; done
  shift
  timeout "${HR_PKG_TIMEOUT:-30m}" docker run --rm --network none \
    --memory "${HR_PKG_MEM:-6g}" --cpus "${HR_PKG_CPUS:-4}" --pids-limit 512 \
    --log-opt max-size=10m --log-opt max-file=3 \
    -u "$(id -u):$(id -g)" "${extra[@]}" "$image" "$@"
}

keep_latest() { # $1 glob，$2 這次要留的檔
  { [ "$FULL_LOCAL" = 1 ] || [ "$RELEASE_PATCH" = 1 ]; } && return 0
  local f
  for f in $1; do
    [ -e "$f" ] || continue
    [ "$f" = "$2" ] || { echo "[package] 清掉舊的 $f"; rm -f "$f"; }
  done
}

# 第三方授權：從建置映像的模組快取與 Go 發行版讀授權全文（不是憑記憶寫）。
make_notices() { # $1 輸出檔
  drun "$GO_IMAGE" -v "$ROOT/workplace:/w:ro" -e HOME=/tmp -- sh -c '
    set -e
    M=/go/pkg/mod
    echo "本程式靜態連結下列第三方軟體。授權全文如下。"
    for d in github.com/hajimehoshi/ebiten/v2@v2.9.9 github.com/ebitengine/purego@v0.9.0 \
             github.com/ebitengine/hideconsole@v1.0.0 github.com/ebitengine/oto/v3@v3.4.0 github.com/jezek/xgb@v1.1.1 \
             golang.org/x/sys@v0.36.0 golang.org/x/sync@v0.17.0 golang.org/x/image@v0.31.0 golang.org/x/text@v0.29.0; do
      echo; echo "================================================================"; echo "$d"; echo "================================================================"
      cat "$M/$d/LICENSE"
    done
    # 介面字型子集（docs/spec/006 第 6 節）：字型內嵌的版權與授權說明加 OFL 全文，由 tools/gen_ui_fonts.sh 產生
    test -f /w/dosgolem/apps/hr/play/fonts/OFL.txt || { echo "缺字型授權檔 fonts/OFL.txt（docs/spec/006 第 6 節，缺檔即失敗）" >&2; exit 1; }
    echo; echo "================================================================"; echo "Noto Sans CJK 子集（介面字型）"; echo "================================================================"
    cat /w/dosgolem/apps/hr/play/fonts/OFL.txt
    echo; echo "================================================================"; echo "Go 標準函式庫與執行期"; echo "================================================================"
    cat "$(go env GOROOT)/LICENSE"
  ' > "$1"
  test -s "$1" || { echo "第三方授權檔是空的" >&2; exit 1; }
  # docs/spec/006 第 6 節的驗收：含 OFL 全文與字型版權人（Adobe），不含 GPL 文字；含 x/image 與 x/text 的授權
  grep -q "SIL OPEN FONT LICENSE" "$1" && grep -q "Adobe" "$1" || { echo "THIRD_PARTY_NOTICES 缺 OFL 全文或字型版權聲明" >&2; exit 1; }
  if grep -q "GNU General Public License" "$1"; then echo "THIRD_PARTY_NOTICES 夾帶了 GPL 文字" >&2; exit 1; fi
  grep -q "golang.org/x/image@" "$1" && grep -q "golang.org/x/text@" "$1" || { echo "THIRD_PARTY_NOTICES 缺 x/image 或 x/text" >&2; exit 1; }
}

stage_common() { # $1 目的目錄
  mkdir -p "$1/original"
  if [ "$FULL_LOCAL" = 1 ]; then
    python3 tools/pkg/full_local.py "$INV" workplace/orig
    cp -R workplace/orig/. "$1/original/"
    python3 tools/pkg/full_local.py "$INV" "$1/original"
    cp packaging/README.full-local.txt "$1/README.txt"
  else
    cp packaging/README.dist.txt "$1/README.txt"
    cp packaging/PUT_ORIGINAL_FILES_HERE.txt "$1/original/PUT_ORIGINAL_FILES_HERE.txt"
  fi
  if [ "$WITH_HD" = 1 ]; then cat packaging/README.hd.txt >> "$1/README.txt"; fi
  cp LICENSE "$1/LICENSE"
  make_notices "$1/THIRD_PARTY_NOTICES.txt"
}

stage_hd() { # $1 包內放 hd 的位置（HR_WITH_HD=1 才做）
  [ "$WITH_HD" = 1 ] || return 0
  test -f hd/catalog.tsv && test -f hd/palettes.tsv && test -f hd/provenance.tsv && test -d hd/x2 || { echo "HR_WITH_HD=1 需要 hd/catalog.tsv、palettes.tsv、provenance.tsv 與 x2/" >&2; exit 1; }
  mkdir -p "$1/hd"
  cp hd/catalog.tsv hd/palettes.tsv hd/provenance.tsv "$1/hd/"
  cp -r hd/x2 "$1/hd/x2"
  cp packaging/HD_NOTICE.txt "$1/hd/NOTICE.txt"
  echo "[package] 含 HD 素材：$(find "$1/hd/x2" -name '*.png' | wc -l) 張（$1/hd）"
}

leak_scan() { # $1 要掃的目錄（workplace 內，repo 相對）
  if [ "$FULL_LOCAL" = 1 ]; then
    local original="$1/original"
    if [ -d "$1/usr/bin/original" ]; then original="$1/usr/bin/original"; fi
    if [ -d "$1/Contents/Resources/original" ]; then original="$1/Contents/Resources/original"; fi
    python3 tools/pkg/full_local.py "$INV" "$original"
    test ! -e "$1/l10n" && test ! -e "$1/l10n-packs" || { echo "完整版不得夾帶譯文表或語言包" >&2; exit 1; }
    return
  fi
  cp "$INV" "$STAGE/inventory.tsv"
  if ! tools/pkg/py.sh leakscan.py "/w/${STAGE#workplace/}/inventory.tsv" "/w/${1#workplace/}"; then
    echo "可散布的包夾帶原版檔，中止" >&2; exit 1
  fi
  # 內容判準（docs/spec/008 第 3.9 節）：原版資料檔與 OP*.TXT 的對白。原版缺席時失敗，不略過。
  test -f workplace/orig/MAIN.EXE || { echo "缺 workplace/orig/MAIN.EXE：內容判準無法執行，閘門失敗" >&2; exit 1; }
  if ! tools/l10n/leakscan.sh "$1"; then
    echo "可散布的包含原版文字（內容判準），中止" >&2; exit 1
  fi
  echo "[package] 外洩掃描通過：$1"
}

prepare_gomodcache() {
  [ -d workplace/gomodcache/github.com/hajimehoshi ] && return 0
  mkdir -p workplace/gomodcache
  drun "$GO_IMAGE" -v "$ROOT/workplace/gomodcache:/dst" -- sh -c 'cp -R /go/pkg/mod/. /dst/'
}

go_build() { # $1 GOOS $2 CGO $3 輸出（/out 內）$4 額外 ldflags
  prepare_gomodcache
  drun "$GO_IMAGE" -v "$ROOT/$DG:/src:ro" -v "$ROOT/workplace/out:/out" -v "$ROOT/workplace/gocache:/gocache" -v "$ROOT/workplace/gomodcache:/gomodcache" \
    -e HOME=/tmp -e GOCACHE=/gocache -e GOMODCACHE=/gomodcache -e GOFLAGS=-mod=readonly -e GOPROXY=off -e GOSUMDB=off \
    -e CGO_ENABLED="$2" -e GOOS="$1" -e GOARCH=amd64 \
    -e "HR_LDFLAGS=-s -w -X main.version=$VER $4" -e "HR_OUT=$3" -w /src/apps/hr/play -- \
    sh -c 'go build -trimpath -ldflags "$HR_LDFLAGS" -o "$HR_OUT" .'
}

icons() { # $1 icon 目錄（workplace 內，repo 相對）
  tools/pkg/py.sh appicon.py "/w/${1#workplace/}" >/dev/null
}

do_appimage() {
  local app="$STAGE/HighReward.AppDir" out="$DIST/HighReward-$VER-x86_64.AppImage"
  rm -rf "$app"; mkdir -p "$app/usr/bin"
  go_build linux 1 /out/pkg-hr-play-linux ""
  cp workplace/out/pkg-hr-play-linux "$app/usr/bin/hr-play"; chmod +x "$app/usr/bin/hr-play"
  stage_common "$app/usr/bin"
  stage_hd "$app/usr/bin"
  icons "$STAGE/icons"
  cp "$STAGE/icons/icon_256.png" "$app/hr-play.png"
  cat > "$app/AppRun" <<'SH'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/hr-play" "$@"
SH
  chmod +x "$app/AppRun"
  cat > "$app/hr-play.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=高報酬戰將 hr-play
Comment=《高報酬戰將》（DOS 版）的桌面執行器，需自備原版檔案
Exec=hr-play
Icon=hr-play
Categories=Game;
Terminal=false
DESKTOP
  leak_scan "$app"
  docker image inspect "$APPIMAGE_IMAGE" >/dev/null 2>&1 || { echo "缺映像 $APPIMAGE_IMAGE" >&2; exit 3; }
  keep_latest "$DIST/HighReward-*-x86_64.AppImage" "$out"
  drun "$APPIMAGE_IMAGE" -e HOME=/tmp -v "$ROOT/$STAGE:/stage:ro" -v "$ROOT/$DIST:/out" -- sh -c "
    set -eu
    mksquashfs /stage/HighReward.AppDir /tmp/app.squashfs -root-owned -noappend -no-progress -comp zstd -Xcompression-level 19
    cat /opt/runtime-x86_64 /tmp/app.squashfs > '/out/$(basename "$out")'
    chmod +x '/out/$(basename "$out")'
    file '/out/$(basename "$out")'"
  rm -rf "$app" "$STAGE/icons"
  echo "$out"
}

do_windows() {
  local dir="$STAGE/win/HighReward-$VER-win64" out="$DIST/HighReward-$VER-win64.zip"
  rm -rf "$STAGE/win"; mkdir -p "$dir"
  go_build windows 0 /out/pkg-hr-play.exe "-H=windowsgui"
  cp workplace/out/pkg-hr-play.exe "$dir/hr-play.exe"
  stage_common "$dir"
  stage_hd "$dir"
  leak_scan "$dir"
  keep_latest "$DIST/HighReward-*-win64.zip" "$out"
  rm -f "$out"
  tools/pkg/py.sh zipdir.py "/w/${dir#workplace/}" "/w/${STAGE#workplace/}/out.zip" "HighReward-$VER-win64" >/dev/null
  mv "$STAGE/out.zip" "$out"
  rm -rf "$STAGE/win"
  echo "$out"
}

do_macos() {
  local app="$STAGE/mac/HighReward.app" out="$DIST/HighReward-$VER-macos.zip" min="${HR_MACOS_MIN:-11.0}"
  docker image inspect "$MAC_IMAGE" >/dev/null 2>&1 || { echo "缺映像 $MAC_IMAGE" >&2; exit 3; }
  rm -rf "$STAGE/mac"; mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources" "$STAGE/mac-icons"
  # osxcross 映像沒有 ebiten：沿用 go_build 準備的離線模組快取。
  prepare_gomodcache
  stage_common "$app/Contents/Resources"
  stage_hd "$app/Contents/Resources"
  icons "$STAGE/mac-icons"
  tools/pkg/py.sh icns.py "/w/${STAGE#workplace/}/mac-icons" "/w/${STAGE#workplace/}/mac/HighReward.app/Contents/Resources/hr-play.icns" >/dev/null
  drun "$MAC_IMAGE" -e HOME=/tmp -e "HR_VER=$VER" -e "HR_MIN=$min" -e HR_OUT=/src-out/hr-play-mac \
    -v "$ROOT/$DG:/src:ro" -v "$ROOT/workplace/out:/src-out" -v "$ROOT/workplace/gocache:/gocache" -v "$ROOT/workplace/gomodcache:/gomodcache" \
    --tmpfs "/tmp:exec,uid=$(id -u),gid=$(id -g),size=2g" -w /src/apps/hr/play -- bash -c '
      set -euo pipefail
      eval "$(osxcross-conf)"
      export GOCACHE=/gocache GOMODCACHE=/gomodcache GOPATH=/tmp/gopath
      export GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOWORK=off GOFLAGS=-mod=mod
      export CGO_ENABLED=1 GOOS=darwin MACOSX_DEPLOYMENT_TARGET=$HR_MIN
      for arch in arm64 amd64; do
        case $arch in
          arm64) pre=arm64-apple-$OSXCROSS_TARGET ;;
          amd64) pre=x86_64-apple-$OSXCROSS_TARGET ;;
        esac
        echo "[macos] $arch（$pre）"
        env GOARCH=$arch CC=$pre-clang CXX=$pre-clang++ \
            CGO_CFLAGS="-mmacosx-version-min=$HR_MIN" CGO_LDFLAGS="-mmacosx-version-min=$HR_MIN" \
          go build -trimpath -ldflags "-s -w -X main.version=$HR_VER" -o /tmp/hr-play-$arch .
      done
      x86_64-apple-$OSXCROSS_TARGET-lipo -create /tmp/hr-play-arm64 /tmp/hr-play-amd64 -output "$HR_OUT"
      x86_64-apple-$OSXCROSS_TARGET-lipo -info "$HR_OUT"'
  cp workplace/out/hr-play-mac "$app/Contents/MacOS/hr-play"; chmod +x "$app/Contents/MacOS/hr-play"
  local short
  if [[ "$VER" =~ ^v\.([0-9]+\.[0-9]+\.[0-9]+)- ]]; then
    short="${BASH_REMATCH[1]}"
  else
    short="$(printf '%s' "$VER" | sed -n 's/^v\{0,1\}\([0-9][0-9.]*\).*/\1/p')"
    [ -n "$short" ] || short="0.0.0"
  fi
  cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key><string>zh_TW</string>
	<key>CFBundleDisplayName</key><string>高報酬戰將</string>
	<key>CFBundleExecutable</key><string>hr-play</string>
	<key>CFBundleIconFile</key><string>hr-play</string>
	<key>CFBundleIdentifier</key><string>io.github.wicanr2.highreward</string>
	<key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
	<key>CFBundleName</key><string>HighReward</string>
	<key>CFBundlePackageType</key><string>APPL</string>
	<key>CFBundleShortVersionString</key><string>$short</string>
	<key>CFBundleVersion</key><string>$VER</string>
	<key>LSApplicationCategoryType</key><string>public.app-category.role-playing-games</string>
	<key>LSMinimumSystemVersion</key><string>$min</string>
	<key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST
  tools/pkg/verify_macos.sh "$app"
  leak_scan "$app"
  keep_latest "$DIST/HighReward-*-macos.zip" "$out"
  rm -f "$out"
  # zip 的頂層是 HighReward.app：從 mac 目錄壓，不加額外資料夾。
  tools/pkg/py.sh zipdir.py "/w/${STAGE#workplace/}/mac" "/w/${STAGE#workplace/}/out.zip" "" >/dev/null
  mv "$STAGE/out.zip" "$out"
  rm -rf "$STAGE/mac" "$STAGE/mac-icons"
  echo "$out"
}

case "$TARGET" in
  appimage) do_appimage ;;
  windows) do_windows ;;
  macos) do_macos ;;
  all) do_appimage; do_windows; do_macos ;;
  *) echo "目標要是 appimage、windows、macos 或 all" >&2; exit 2 ;;
esac
echo "== $DIST"
ls -la "$DIST"
