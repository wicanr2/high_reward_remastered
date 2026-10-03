"""以指定參數處理指定的幾張圖，輸出到輸出根目錄的相同相對路徑（實驗用）。

用法：python3 art_batch.py <原圖根目錄> <輸出根目錄> <S> <參數字串> <相對路徑> [...]
參數字串同 art_proto（key=value 逗號分隔）；若為 preset，則改用 art_upscale.options 的類別參數再覆蓋。
"""
import os
import sys

from PIL import Image

import art_lib
import art_upscale

src, dst, S, spec = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
over = dict(kv.split("=") for kv in spec.split(",") if kv)
for rel in sys.argv[5:]:
    opt = art_upscale.options(rel)
    opt.update(over)
    out = os.path.join(dst, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.fromarray(art_lib.process(os.path.join(src, rel), S, opt), "RGBA").save(out)
    print(rel)
