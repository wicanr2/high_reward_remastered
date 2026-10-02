#!/usr/bin/env bash
# 抓 SingleStepTests/8088 v2 全部測資到 workplace/dosgolem/testdata/8088/（dosgolem 副本內，已 gitignore）。
# 8088 語料是 dosgolem CPU 的既有驗收基準；缺檔時那些測試會 skip，等於沒驗到。
# 在容器內以 Python urllib 下載（需要網路，約 760 MB）。已存在且非空的檔案略過。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/workplace/dosgolem/testdata/8088"
mkdir -p "$OUT"
exec timeout 3000 docker run --rm -u "$(id -u):$(id -g)" --memory 512m --cpus 1 --pids-limit 32 \
  --log-opt max-size=10m --log-opt max-file=3 -v "$OUT:/out" python:3.13-alpine python -c '
import json, os, urllib.request
H = {"User-Agent": "Mozilla/5.0"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=120).read()
lst = json.loads(get("https://api.github.com/repos/SingleStepTests/8088/contents/v2"))
names = [x["name"] for x in lst if x["type"] == "file"]
base = "https://raw.githubusercontent.com/SingleStepTests/8088/main/v2/"
n = 0
for name in names:
    f = "/out/" + name
    if os.path.exists(f) and os.path.getsize(f) > 0: continue
    b = get(base + name); open(f + ".part", "wb").write(b); os.rename(f + ".part", f); n += 1
print("files", len(names), "downloaded", n)
'
