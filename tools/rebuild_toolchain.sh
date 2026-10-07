#!/usr/bin/env bash
# 恢復固定 Go 1.26.7 / Ebiten 2.9.9 的 Linux build/test/record image。
# 在主機只操作 Docker；最小 context 由 UID 1000 的 Python 容器建立。
# 來源與替代關係見 tools/docker/Dockerfile.hr-build-r1。
set -euo pipefail
HR_TOOL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HR_TOOL_IMAGE=hr-go-ebiten:1.26.7-2.9.9-r1
HR_TOOL_PREP_IMAGE=python:3.13-bookworm
HR_TOOL_DG="$HR_TOOL_ROOT/workplace/dosgolem"
HR_TOOL_OUT="$HR_TOOL_ROOT/workplace/out"
HR_TOOL_CONTEXT="$HR_TOOL_OUT/toolchain-context/build"
test -d "$HR_TOOL_OUT"
test -d "$HR_TOOL_DG/apps/hr/play"
test -f "$HR_TOOL_ROOT/tools/docker/Dockerfile.hr-build-r1"
test -f "$HR_TOOL_DG/go.mod" && test -f "$HR_TOOL_DG/go.sum"
test -f "$HR_TOOL_DG/apps/hr/play/go.mod" && test -f "$HR_TOOL_DG/apps/hr/play/go.sum"
docker image inspect "$HR_TOOL_PREP_IMAGE" >/dev/null

timeout 60s docker run -i --rm --name "hr-toolchain-context-$$" --user 1000:1000 \
  --network none --memory 512m --cpus 1 --pids-limit 128 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$HR_TOOL_ROOT:/src:ro" -v "$HR_TOOL_OUT:/out" "$HR_TOOL_PREP_IMAGE" python3 - <<'PY'
from pathlib import Path
import hashlib
import json
import re
import shutil

source = Path('/src/workplace/dosgolem')
target = Path('/out/toolchain-context')
build = target / 'build'
target.mkdir(exist_ok=True)
build.mkdir(exist_ok=True)
for folder in (target, build):
    if folder.stat().st_uid != 1000 or folder.stat().st_gid != 1000:
        raise SystemExit(f'輸出目錄擁有權不是 1000:1000：{folder}')
if any(p.name not in {'Dockerfile', 'go.mod', 'go.sum'} for p in build.iterdir()):
    raise SystemExit('build context 存在非 Dockerfile／go.mod／go.sum 的檔案')

inputs = [source/'go.mod', source/'go.sum', source/'apps/hr/play/go.mod', source/'apps/hr/play/go.sum', Path('/src/tools/docker/Dockerfile.hr-build-r1')]
for path in inputs:
    if not path.is_file():
        raise SystemExit(f'缺少來源：{path}')
versions = {}
for path in (source/'go.mod', source/'apps/hr/play/go.mod'):
    for line in path.read_text().splitlines():
        match = re.fullmatch(r'\s*([a-zA-Z0-9._/-]+)\s+(v[^\s]+)(?:\s+//.*)?\s*', line)
        if not match:
            continue
        module, version = match.groups()
        if module == 'github.com/wicanr2/dosgolem':
            continue  # 本機 replace，不下載另一份專案。
        if module in versions and versions[module] != version:
            raise SystemExit(f'模組版本衝突：{module}')
        versions[module] = version
if versions.get('github.com/hajimehoshi/ebiten/v2') != 'v2.9.9':
    raise SystemExit('來源 Ebiten 版本不是 v2.9.9')
sums = {}
for path in (source/'go.sum', source/'apps/hr/play/go.sum'):
    for line in path.read_text().splitlines():
        module, version, checksum = line.split()
        key = (module, version)
        if key in sums and sums[key] != checksum:
            raise SystemExit(f'模組 checksum 衝突：{module} {version}')
        sums[key] = checksum
for module, version in versions.items():
    for key in ((module, version), (module, version+'/go.mod')):
        if key not in sums:
            raise SystemExit(f'原鎖檔缺少 checksum：{key}')
mod = 'module hrtoolchain\n\ngo 1.24.0\n\nrequire (\n'
mod += ''.join(f'\t{module} {version}\n' for module, version in sorted(versions.items())) + ')\n'
(build/'go.mod').write_text(mod)
(build/'go.sum').write_text(''.join(f'{module} {version} {checksum}\n' for (module, version), checksum in sorted(sums.items())))
shutil.copyfile('/src/tools/docker/Dockerfile.hr-build-r1', build/'Dockerfile')
manifest = {'inputs': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}, 'context': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(build.iterdir())}, 'modules': versions, 'contains_original_data': False}
(target/'context-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({'context_files': sorted(p.name for p in build.iterdir()), 'modules': len(versions), 'owner': '1000:1000'}))
PY

if docker image inspect "$HR_TOOL_IMAGE" >/dev/null 2>&1; then
  timeout 30s docker run --rm --name "hr-toolchain-existing-$$" --user 1000:1000 \
    --network none --memory 512m --cpus 1 --pids-limit 128 \
    --log-opt max-size=10m --log-opt max-file=3 \
    -v "$HR_TOOL_CONTEXT:/expected:ro" "$HR_TOOL_IMAGE" bash -c \
    'set -eu; test "$(go env GOVERSION)" = go1.26.7; cd /opt/hr-toolchain; cmp go.mod /expected/go.mod; cmp go.sum /expected/go.sum; test "$(go list -m -f "{{.Version}}" github.com/hajimehoshi/ebiten/v2)" = v2.9.9; test "$(dpkg-query -W -f="\${Version}" ffmpeg)" = 7:5.1.9-0+deb12u1; go mod verify'
  printf '沿用既有 image：%s\n' "$HR_TOOL_IMAGE"
  exit 0
fi

# Docker build／套件下載明確需要網路。來源只限上方建立的三檔 context。
timeout "${HR_TOOLCHAIN_BUILD_TIMEOUT:-20m}" docker build \
  --memory 4g --cpu-period 100000 --cpu-quota 200000 \
  --network default --tag "$HR_TOOL_IMAGE" "$HR_TOOL_CONTEXT" 2>&1 | tee "$HR_TOOL_OUT/toolchain-context/build.log"
docker image inspect "$HR_TOOL_IMAGE" --format '{{.Id}}'
