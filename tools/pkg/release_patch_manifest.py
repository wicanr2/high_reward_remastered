"""Record checksums for the three private Release packages without original game files."""

import hashlib
import json
import os
import pathlib
import re
import sys


directory = pathlib.Path(sys.argv[1])
version, source_commit, dosgolem_commit = sys.argv[2:5]
if not re.fullmatch(r"v\.\d+\.\d+\.\d+-\d{8}", version):
    raise ValueError("invalid release version")
if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (source_commit, dosgolem_commit)):
    raise ValueError("invalid source commit")

names = (
    f"patch/HighReward-{version}-x86_64.AppImage",
    f"patch/HighReward-{version}-win64.zip",
    f"patch/HighReward-{version}-macos.zip",
)
files = []
for name in names:
    path = directory / name
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing package: {name}")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    files.append({"path": name, "bytes": path.stat().st_size, "sha256": digest.hexdigest()})

manifest = {
    "version": version,
    "visibility": "private",
    "rights": "Authorized HD and AI artwork and translations derive from the original game; pure Noto font data is under OFL. Original game files, music and compiled language packs are omitted. Private repository only.",
    "source_commit": source_commit,
    "dosgolem_commit": dosgolem_commit,
    "files": files,
}
temporary = directory / "patch/SHA256SUMS.json.tmp"
temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, directory / "patch/SHA256SUMS.json")
# 根清冊包含本機完整版與 private patch；Release 上傳 patch 內清冊。
root_manifest = directory / 'SHA256SUMS.json'
combined = json.loads(root_manifest.read_text()) if root_manifest.is_file() else dict(manifest)
previous = [entry for entry in combined.get('files', []) if not entry['path'].startswith('patch/')]
combined.update(source_commit=source_commit, dosgolem_commit=dosgolem_commit)
combined['files'] = previous + [dict(entry, distribution='private-repo') for entry in files]
temporary = directory / 'SHA256SUMS.json.tmp'
temporary.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
os.replace(temporary, root_manifest)
print(directory / "patch/SHA256SUMS.json")
