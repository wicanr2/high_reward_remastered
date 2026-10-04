"""本機完整版的原版檔案閘門。

用法：python3 tools/pkg/full_local.py docs/re/source-inventory.tsv <original 目錄>
只接受清冊中的平面檔案；逐檔核對大小與 SHA-256，不輸出原版內容。
"""

import csv
import hashlib
import pathlib
import sys


def main() -> None:
    inventory = pathlib.Path(sys.argv[1])
    source = pathlib.Path(sys.argv[2])
    with inventory.open(newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    expected = {row["path"] for row in rows}
    if len(expected) != len(rows):
        raise ValueError("清冊有重複檔名")
    actual = {p.name for p in source.iterdir()}
    if actual != expected:
        raise ValueError(
            f"原版檔名不符：缺 {sorted(expected - actual)}；多 {sorted(actual - expected)}"
        )
    for row in rows:
        name = row["path"]
        if pathlib.Path(name).name != name:
            raise ValueError(f"清冊不是平面檔名：{name}")
        path = source / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"不是一般檔案：{name}")
        if path.stat().st_size != int(row["size"]):
            raise ValueError(f"大小不符：{name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            raise ValueError(f"SHA-256 不符：{name}")
    print(f"[full-local] 原版 {len(rows)} 檔，大小與 SHA-256 全部符合清冊：{source}")


if __name__ == "__main__":
    main()
