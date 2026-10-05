"""Local L2 font proof. Never ship the patched CFONT.15 or dialogue file."""

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil

import PIL
from PIL import Image, ImageFont
from fontTools import version as fonttools_version
from fontTools.ttLib import TTCollection


FONT = Path("/font/NotoSansCJK-Regular.ttc")
SOURCE = Path("/base/t0")
OUT = Path("/out")
RESERVED = Path("/evidence/m10-reserved-codes.tsv")
OFL = Path("/ofl/OFL.txt")
EXPECTED_FONT = "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"
EXPECTED_CF = "60e55cf73ba2eb8e83018e8a9b585e22524e730e240732adb5e746b7ed54d8db"
ASSIGNMENTS = (("简", 0xE040), ("体", 0xE041))
FACE = 2  # Noto Sans CJK SC
SIZE = 13
THRESHOLD = 128


def digest(data):
    return hashlib.sha256(data).hexdigest()


def glyph_index(code):
    lead, trail = code >> 8, code & 0xFF
    tail = trail - (0x40 if trail <= 0x7E else 0x62)
    if lead <= 0xA3:
        return (lead - 0xA1) * 157 + tail
    if (lead == 0xC6 and trail >= 0xA1) or 0xC6 < lead <= 0xC8:
        return (lead - 0xC6) * 157 + tail - 0x3F + 0x198
    return (lead - 0xA4) * 157 + tail - (0x198 if lead >= 0xC9 else 0) + 0x305


def raster(font, char):
    mask = font.getmask(char, mode="L")
    width, height = mask.size
    if width > 15 or height > 15:
        raise ValueError(f"glyph overflows 15x15: U+{ord(char):04X} {mask.size}")
    cell = Image.new("L", (15, 15), 0)
    cell.paste(Image.frombytes("L", mask.size, bytes(mask)),
               ((15 - width) // 2, (15 - height) // 2))
    rows = bytearray()
    ink = 0
    for y in range(15):
        word = 0
        for x in range(15):
            if cell.getpixel((x, y)) >= THRESHOLD:
                word |= 1 << (15 - x)
                ink += 1
        rows.extend(word.to_bytes(2, "big"))
    if not ink:
        raise ValueError(f"glyph has no ink: U+{ord(char):04X}")
    return bytes(rows), [width, height], ink


def main():
    if digest(FONT.read_bytes()) != EXPECTED_FONT:
        raise ValueError("font hash differs")
    if fonttools_version != "4.66.1" or PIL.__version__ != "12.3.0":
        raise ValueError("rasterizer version differs")
    font_collection = TTCollection(str(FONT), lazy=True)
    face_name = font_collection.fonts[FACE]["name"].getDebugName(4)
    cmap = font_collection.fonts[FACE].getBestCmap()
    if face_name != "Noto Sans CJK SC":
        raise ValueError("wrong Noto face")
    forbidden = {int(row["code_hex"], 16) for row in
                 csv.DictReader(RESERVED.open(), delimiter="\t")}
    for char, code in ASSIGNMENTS:
        if code in forbidden or ord(char) not in cmap:
            raise ValueError(f"reserved code or missing glyph: {char} {code:04X}")
    license_data = OFL.read_bytes()
    if b"SIL OPEN FONT LICENSE Version 1.1" not in license_data or b"GNU General Public License" in license_data:
        raise ValueError("OFL input is not the isolated license")
    image_id = os.environ.get("HR_IMAGE_ID", "")
    if not image_id.startswith("sha256:"):
        raise ValueError("missing container image ID")

    root = OUT / "l2-font-sc-root"
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(SOURCE, root)
    cf_path = root / "CFONT.15"
    cf = bytearray(cf_path.read_bytes())
    if digest(cf) != EXPECTED_CF or len(cf) != 13867 * 30:
        raise ValueError("CFONT source differs")
    face = ImageFont.truetype(str(FONT), SIZE, index=FACE)
    records = bytearray()
    rows = []
    for char, code in ASSIGNMENTS:
        glyph, mask_size, ink = raster(face, char)
        index = glyph_index(code)
        assert 0 <= index < 13867
        cf[index * 30:(index + 1) * 30] = glyph
        records.extend(code.to_bytes(2, "big"))
        records.extend(glyph)
        rows.append({"codepoint": f"U+{ord(char):04X}", "code_hex": f"{code:04X}",
                     "glyph_index": index, "mask_size": mask_size, "ink_pixels": ink})
    cf_path.write_bytes(cf)

    esp = root / "ESPMES.MRG"
    content = bytearray(esp.read_bytes())
    first = bytes.fromhex("a440a441a47e0aa442a443a444a445a446a447a44800")
    if content[0x3D7A:0x3D7A + 22] != first:
        raise ValueError("ESPMES source variant differs")
    sample = bytes.fromhex("e040e0410a") + bytes.fromhex("e040e041") * 4 + b"\x00"
    assert len(sample) == 22
    content[0x3D7A:0x3D7A + 22] = sample
    esp.write_bytes(content)

    (OUT / "glyphs-zh-CN-prototype.bin").write_bytes(records)
    (OUT / "charmap-zh-CN-prototype.tsv").write_text(
        "codepoint\tcode_hex\n" + "".join(f"{r['codepoint']}\t{r['code_hex']}\n" for r in rows))
    shutil.copyfile(OFL, OUT / "OFL-prototype.txt")
    report = {
        "status": "disposable L2 visual prototype, not a production language pack",
        "source_font": FONT.name, "source_font_sha256": EXPECTED_FONT,
        "source_cfont_sha256": EXPECTED_CF, "ofl_sha256": digest(license_data),
        "source_variant": "re-text2/roots/t0", "face_index": FACE,
        "face_name": face_name, "pillow": PIL.__version__, "fonttools": fonttools_version,
        "parameters": {"pixel_size": SIZE, "cell": [15, 15], "threshold": THRESHOLD,
                       "placement": "center mask without scaling; 16th column blank"},
        "container_image_id": image_id, "glyphs": rows,
        "glyphs_sha256": digest(records), "patched_cfont_sha256": digest(cf),
        "patched_espmes_sha256": digest(content),
    }
    (OUT / "SOURCE-prototype.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("face_name", "glyphs_sha256", "patched_cfont_sha256", "patched_espmes_sha256")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
