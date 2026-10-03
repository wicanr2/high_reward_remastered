"""印出原圖一個區域的色 id（診斷用）：python3 art_dump.py <png> x y w h"""
import sys
import art_lib

path, x, y, w, h = sys.argv[1], *[int(v) for v in sys.argv[2:6]]
d = art_lib.load(path)
sym = "0123456789abcdefghijklmnopqrstuvwxyz"
for row in d["idx"][y:y + h, x:x + w]:
    print("".join("." if v < 0 else sym[v] for v in row))
