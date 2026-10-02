"""原型實驗：對單張圖跑 v2 管線的各種變體，輸出到指定檔（診斷用）。

用法：python3 art_proto.py <原圖> <輸出前綴> <S> <變體> [<變體> ...]
變體字串：key=value 以逗號分隔（參數見 art_lib.process），name 為輸出檔名後綴。
"""
import sys
import time

from PIL import Image

import art_lib


def main():
    path, prefix, S = sys.argv[1], sys.argv[2], int(sys.argv[3])
    for v in sys.argv[4:]:
        opt = dict(kv.split("=") for kv in v.split(",") if kv)
        t = time.time()
        rgba = art_lib.process(path, S, opt)
        name = f"{prefix}_{opt.get('name', 'v')}.png"
        Image.fromarray(rgba, "RGBA").save(name)
        print(name, f"{time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
