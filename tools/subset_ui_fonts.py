#!/usr/bin/env python3
"""在鎖版 fontTools 容器中更新已由 TestGenCharsets 產生的介面字型。"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import fontTools
from fontTools.ttLib import TTCollection, TTFont

assert fontTools.version == "4.66.1", fontTools.version
source, output = map(Path, sys.argv[1:3])
expected = "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
assert output.stat().st_uid == os.getuid()
faces = {"zh-TW": (3, "TC"), "zh-CN": (2, "SC"), "ko": (1, "KR"), "en": (3, "TC"), "ja": (0, "JP")}
for language, (index, region) in faces.items():
    full = TTCollection(source, lazy=True).fonts[index]
    assert full["name"].getDebugName(4) in (f"Noto Sans CJK {region}", f"Noto Sans CJK {region} Regular")
    target = output / f"ui-{language}.otf"
    assert not target.exists() or target.stat().st_uid == os.getuid()
    subprocess.run([sys.executable, "-m", "fontTools.subset", str(source),
                    f"--font-number={index}", f"--text-file={output / ('charset-' + language + '.txt')}",
                    f"--output-file={target}", "--layout-features=", "--drop-tables+=GSUB,GPOS",
                    "--no-hinting", "--notdef-outline", "--name-IDs=0,7,13,14", "--legacy-kern", "--recalc-bounds"], check=True)
    subset = TTFont(target)
    assert "GSUB" not in subset and "GPOS" not in subset
    for name_id in (0, 7, 13, 14):
        assert subset["name"].getDebugName(name_id)
    assert target.stat().st_uid == os.getuid()
    print(language, target.stat().st_size, hashlib.sha256(target.read_bytes()).hexdigest())
(output / "SOURCE.txt").write_text(
    f"來源：NotoSansCJK-Regular.ttc，Noto Sans CJK Regular，SIL Open Font License 1.1\nSHA-256：{expected}\n"
    "字面：zh-TW/en=TC 3、zh-CN=SC 2、ko=KR 1、ja=JP 0\n"
    "工具：fontTools 4.66.1；鎖版 wheel SHA-256 83572afe48733bad7a4a9c11721d3a726c2e976d82b063fc9bdd049d76955abd\n"
    "參數及重生入口：hr/tools/subset_ui_fonts.py；字元表由 apps/hr/play 的 TestGenCharsets 產生。\n"
    "授權全文及版權聲明：同目錄 OFL.txt，字型 name IDs 0/7/13/14 保留。\n", encoding="utf-8")
