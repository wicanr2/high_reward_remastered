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
names += [f'patch/HighReward-{version}-{suffix}' for suffix in ['x86_64.AppImage', 'win64.zip', 'macos.zip']
          if (root / f'patch/HighReward-{version}-{suffix}').is_file()]
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
    scope = 'private-repo' if name.startswith('patch/') else 'local-only'
    files.append({"path": name, "bytes": path.stat().st_size, "sha256": digest.hexdigest(), "distribution": scope})

manifest = {
    "version": version,
    "visibility": "local-full-and-private-patch",
    "rights": "full-local and promo contain original game or music and remain local. Private patch includes authorized HD, AI art, translations and pure Noto fonts; original game files and compiled language packs are omitted. No public distribution permission established.",
    "files": files,
}
for key, variable in [('source_commit', 'HR_SOURCE_COMMIT'), ('dosgolem_commit', 'HR_DOSGOLEM_COMMIT')]:
    value = os.environ.get(variable)
    if value:
        if not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError(f'{variable} 格式不符')
        manifest[key] = value
static = root / "smoke/full-static.json"
if static.is_file():
    receipt = json.loads(static.read_text())
    if receipt["version"] != version:
        raise ValueError("驗收收據版本不符")
    for key in ['build_source', 'fork_source', 'original_files_per_platform', 'adopted_seven_file_rows',
                'main_table_rows', 'full_text_activated', 'macos']:
        if key in receipt:
            manifest[key] = receipt[key]
    manifest['verification_scope'] = 'User requested language integration and switching only; no additional gameplay sampling or native macOS test.'
    manifest["verification_receipts_sha256"] = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [static, root / "smoke/linux/receipt.json", root / "smoke/windows/RESULTS.txt", root / "promo/ffprobe.json", root / "promo/rights.json"] if p.is_file()
    }
dest = root / "SHA256SUMS.json"
temp = root / "SHA256SUMS.json.tmp"
temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temp, dest)
print(dest)
