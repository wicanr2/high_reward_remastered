"""計算本機完整版的正式封包與推廣影片雜湊。"""

import hashlib
import json
import os
import pathlib
import re
import sys


root = pathlib.Path(sys.argv[1])
version = sys.argv[2]
if not re.fullmatch(r"v\.\d+\.\d+\.\d+-\d{8}", version):
    raise ValueError("版號格式錯誤")
names = [
    f"full-local/HighReward-{version}-x86_64.AppImage",
    f"full-local/HighReward-{version}-win64.zip",
    f"full-local/HighReward-{version}-macos.zip",
    f"promo/HighReward-{version}-promo.mp4",
]
files = []
for name in names:
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"缺封包或不是一般檔案：{name}")
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    files.append({"path": name, "bytes": path.stat().st_size, "sha256": digest.hexdigest()})

manifest = {
    "version": version,
    "visibility": "local-only",
    "rights": "Contains original game files, HD derivatives, or original music derivatives; no public distribution permission established.",
    "files": files,
}
dest = root / "SHA256SUMS.json"
temp = root / "SHA256SUMS.json.tmp"
temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temp, dest)
print(dest)
