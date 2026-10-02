"""產生發行包的圖示：純幾何圖形（盾牌與金幣），不使用任何原版美術。

用法：python3 appicon.py <輸出目錄> [尺寸...]   輸出 icon_<尺寸>.png（預設 64 128 256 512 1024）
"""
import sys
from PIL import Image, ImageDraw


def draw(size):
    s = size * 4  # 4 倍超取樣
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(s * 0.08)
    # 底：圓角方塊
    d.rounded_rectangle((pad, pad, s - pad, s - pad), radius=int(s * 0.18), fill=(38, 52, 96, 255))
    # 盾牌
    cx, top, bot = s // 2, int(s * 0.2), int(s * 0.82)
    w = int(s * 0.27)
    pts = [(cx - w, top), (cx + w, top), (cx + w, int(s * 0.55)), (cx, bot), (cx - w, int(s * 0.55))]
    d.polygon(pts, fill=(196, 150, 54, 255))
    inner = int(w * 0.8)
    pts2 = [(cx - inner, top + int(s * 0.04)), (cx + inner, top + int(s * 0.04)), (cx + inner, int(s * 0.54)),
            (cx, bot - int(s * 0.07)), (cx - inner, int(s * 0.54))]
    d.polygon(pts2, fill=(122, 28, 36, 255))
    # 金幣
    r = int(s * 0.12)
    d.ellipse((cx - r, int(s * 0.42) - r, cx + r, int(s * 0.42) + r), fill=(245, 205, 80, 255), outline=(196, 150, 54, 255), width=max(2, s // 120))
    d.ellipse((cx - r // 2, int(s * 0.42) - r // 2, cx + r // 2, int(s * 0.42) + r // 2), outline=(196, 150, 54, 255), width=max(2, s // 150))
    return im.resize((size, size), Image.LANCZOS)


out = sys.argv[1]
sizes = [int(x) for x in sys.argv[2:]] or [64, 128, 256, 512, 1024]
import os
os.makedirs(out, exist_ok=True)
for z in sizes:
    draw(z).save(os.path.join(out, f"icon_{z}.png"))
print("icons", sizes)
