"""以 S=2 管線連續做兩次得到 S=4 的樣張（多倍率可行性評估的對照組）。

用法：python3 art_cascade.py <原圖根目錄> <S=2 成品根目錄> <輸出根目錄>
第二次的輸入是第一次的 HD 圖，只把 alpha ＝ 255 的像素當有效（第一次的羽化像素不參與），
不再做去抖色與雙邊濾波，只做模式搜尋上採樣、輪廓平滑與 alpha 處理。
輸出尺寸是原圖的 4 倍，用 validate.py 以 S ＝ 4 對原圖檢查。
"""
import os
import sys
import time

from PIL import Image

import art_lib
import art_samples


def main():
    src, hd2, dst = sys.argv[1:4]
    for rel in art_samples.SAMPLES:
        p = os.path.join(hd2, rel)
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        t = time.time()
        rgba = art_lib.process(p, 2, dict(per=0, beta=8, post=1, vt=255))
        Image.fromarray(rgba, "RGBA").save(out)
        print(rel, f"{time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
