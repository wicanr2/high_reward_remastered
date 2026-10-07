#!/usr/bin/env bash
# 恢復 HR 的固定 AppImage builder；主機只操作 Docker 與路徑檢查。
# runtime 優先使用已核對的本機前綴，缺少時從既有公開 patch 包恢復。
set -euo pipefail
HR_AI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HR_AI_IMAGE=hr-appimage:runtime-recovery-r1
HR_AI_PREP_IMAGE=hr-go-ebiten:1.26.7-2.9.9-r1
HR_AI_OUT="$HR_AI_ROOT/workplace/out/toolchain-context"
HR_AI_CONTEXT="$HR_AI_OUT/appimage/build"
test -d "$HR_AI_OUT"
test -f "$HR_AI_ROOT/tools/docker/Dockerfile.hr-appimage-r1"
test -f "$HR_AI_ROOT/tools/pkg/recover_appimage_runtime.py"
docker image inspect "$HR_AI_PREP_IMAGE" >/dev/null

timeout 60s docker run --rm --name "hr-appimage-recovery-context-$$" \
  --user 1000:1000 --network none --memory 512m --cpus 1 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$HR_AI_ROOT:/src:ro" -v "$HR_AI_OUT:/out" \
  "$HR_AI_PREP_IMAGE" python3 /src/tools/pkg/recover_appimage_runtime.py

timeout 30s docker run --rm --name "hr-appimage-recovery-copy-$$" \
  --user 1000:1000 --network none --memory 256m --cpus 1 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$HR_AI_ROOT/tools/docker:/source:ro" -v "$HR_AI_CONTEXT:/context" \
  "$HR_AI_PREP_IMAGE" python3 -c \
  'from pathlib import Path; import shutil; p=Path("/context"); assert not any(q.name not in {"Dockerfile", "runtime"} for q in p.iterdir()); assert (p.stat().st_uid,p.stat().st_gid)==(1000,1000); shutil.copyfile("/source/Dockerfile.hr-appimage-r1",p/"Dockerfile")'

if docker image inspect "$HR_AI_IMAGE" >/dev/null 2>&1; then
  timeout 30s docker run --rm --name "hr-appimage-recovery-existing-$$" \
    --user 1000:1000 --network none --memory 256m --cpus 1 --pids-limit 128 \
    --log-opt max-size=10m --log-opt max-file=3 "$HR_AI_IMAGE" sh -c \
    'set -eu; printf "%s  %s\n" 1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf /opt/runtime-x86_64 | sha256sum -c -; test "$(/opt/runtime-x86_64 --appimage-offset)" = 944632; mksquashfs -version'
  printf '沿用固定 AppImage image：%s\n' "$HR_AI_IMAGE"
  exit 0
fi

# 只為基底、apt 套件下載開網路，沒有 runtime 下載或原版資料。
timeout "${HR_APPIMAGE_BUILD_TIMEOUT:-15m}" docker build \
  --memory 2g --cpu-period 100000 --cpu-quota 100000 --network default \
  --tag "$HR_AI_IMAGE" "$HR_AI_CONTEXT" 2>&1 | tee "$HR_AI_OUT/appimage/build.log"
docker image inspect "$HR_AI_IMAGE" --format '{{.Id}}'
