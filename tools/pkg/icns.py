"""把 icon_<尺寸>.png 組成 .icns（PNG 內嵌型別碼 icp6、ic07、ic08、ic09、ic10 ＝ 64、128、256、512、1024）。

用法：python3 icns.py <icon 目錄> <輸出 .icns>
"""
import pathlib
import struct
import sys

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
types = {64: b"icp6", 128: b"ic07", 256: b"ic08", 512: b"ic09", 1024: b"ic10"}
body = b""
for size, tag in sorted(types.items()):
    png = (src / f"icon_{size}.png").read_bytes()
    body += tag + struct.pack(">I", len(png) + 8) + png
out.write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)
print(out, len(body) + 8)
