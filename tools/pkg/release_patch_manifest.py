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
    "rights": "HD artwork derives from the original game; original game files are omitted.",
    "source_commit": source_commit,
    "dosgolem_commit": dosgolem_commit,
    "files": files,
}
temporary = directory / "SHA256SUMS.json.tmp"
temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, directory / "SHA256SUMS.json")
print(directory / "SHA256SUMS.json")
