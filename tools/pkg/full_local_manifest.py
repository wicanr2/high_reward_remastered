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
license_source = pathlib.Path("/license")
if license_source.is_file():
    (root / "LICENSE").write_bytes(license_source.read_bytes())
    names.append("LICENSE")
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
    "rights": "Contains original game files, HD or AI art, translation and original music derivatives; no public distribution permission established.",
    "files": files,
}
static = root / "smoke/full-static.json"
if static.is_file():
    receipt = json.loads(static.read_text())
    if receipt["version"] != version:
        raise ValueError("驗收收據版本不符")
    manifest.update(build_source=receipt["build_source"], fork_source=receipt["fork_source"],
                    original_files_per_platform=receipt["original_files_per_platform"],
                    pilot_per_language=receipt["pilot_per_language"],
                    accepted_full_per_new_language=receipt["accepted_full_per_new_language"],
                    full_text_activated=receipt["full_text_activated"],
                    verification={"linux": "Xvfb normal new-game path; AI and Korean pilot; F1/F2/F4", "windows": "Wine title boot and English pilot; no real-device test", "macos": receipt["macos"]})
    manifest["verification_receipts_sha256"] = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [static, root / "smoke/linux/receipt.json", root / "smoke/windows/RESULTS.txt", root / "promo/ffprobe.json", root / "promo/rights.json"]
    }
dest = root / "SHA256SUMS.json"
temp = root / "SHA256SUMS.json.tmp"
temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temp, dest)
print(dest)
