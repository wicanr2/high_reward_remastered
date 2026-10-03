"""驗收用對照總表：原版解碼圖（最近鄰放大 S 倍）與 HD 圖並排，依群組分頁。

用法：python3 art_review_sheets.py <原版 PNG 根目錄> <HD 根目錄> <輸出目錄> [S]
輸入根目錄的相對路徑相同（tools/img 的輸出與 art_upscale.py 的輸出）。
每格：左＝原版放大 S 倍，右＝HD 圖，圖名在下方；透明處顯示淺灰棋盤。
群組：第一層目錄，MRG 與 PXZ 以下再分到檔名。大圖（寬或高 ≥ 256）一格一列並縮成一半。
輸出是原版美術的衍生物，只放 workplace/。
"""
import os
import sys

from PIL import Image, ImageDraw

orig_root, hd_root, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
S = int(sys.argv[4]) if len(sys.argv) > 4 else 2
os.makedirs(out_dir, exist_ok=True)


def checker(w, h):
    im = Image.new("RGB", (w, h), (214, 214, 214))
    d = ImageDraw.Draw(im)
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            if (x // 8 + y // 8) % 2:
                d.rectangle([x, y, x + 7, y + 7], fill=(176, 176, 176))
    return im


def on_checker(im):
    im = im.convert("RGBA")
    bg = checker(*im.size)
    bg.paste(im, (0, 0), im)
    return bg


groups = {}
for dp, _, fs in os.walk(hd_root):
    for f in fs:
        if not f.endswith(".png"):
            continue
        rel = os.path.relpath(os.path.join(dp, f), hd_root)
        parts = rel.split(os.sep)
        key = parts[0] if parts[0] not in ("MRG", "PXZ", "PXS") or len(parts) < 3 else parts[0] + "_" + parts[1]
        groups.setdefault(key, []).append(rel)

index = []
for key in sorted(groups):
    rels = sorted(groups[key])
    # 原版對照圖不存在（例如游標，執行期才產生）時，改用 HD 圖縮回原尺寸的最近鄰當左圖
    tiles = []
    for rel in rels:
        hp = os.path.join(hd_root, rel)
        op = os.path.join(orig_root, rel)
        hd = Image.open(hp).convert("RGBA")
        if os.path.exists(op):
            o = Image.open(op).convert("RGBA")
            o = o.resize((o.size[0] * S, o.size[1] * S), Image.NEAREST)
        else:
            o = Image.new("RGBA", hd.size, (0, 0, 0, 0))
        big = max(hd.size) >= 256 * S
        if big:
            o = o.resize((o.size[0] // 2, o.size[1] // 2), Image.BOX)
            hd = hd.resize((hd.size[0] // 2, hd.size[1] // 2), Image.BOX)
        w = o.size[0] + hd.size[0] + 12
        h = max(o.size[1], hd.size[1]) + 14
        tile = Image.new("RGB", (w, h), (255, 255, 255))
        tile.paste(on_checker(o), (0, 0))
        tile.paste(on_checker(hd), (o.size[0] + 12, 0))
        ImageDraw.Draw(tile).text((2, h - 12), os.path.basename(rel)[:60], fill=(0, 0, 0))
        tiles.append((tile, big))
    # 分頁：寬度上限 2400
    page, row, rows, x, rh, n = 0, [], [], 0, 0, 0
    pages = []
    cur_rows, cur_x, cur_h, cur_row = [], 0, 0, []
    for tile, big in tiles:
        if cur_x + tile.size[0] > 2400 or (big and cur_row):
            if cur_row:
                cur_rows.append((cur_row, cur_h))
            cur_row, cur_x, cur_h = [], 0, 0
        cur_row.append(tile)
        cur_x += tile.size[0] + 8
        cur_h = max(cur_h, tile.size[1])
        total_h = sum(h for _, h in cur_rows) + cur_h
        if total_h > 2400 or big:
            cur_rows.append((cur_row, cur_h))
            cur_row, cur_x, cur_h = [], 0, 0
            if sum(h for _, h in cur_rows) > 2000:
                pages.append(cur_rows)
                cur_rows = []
    if cur_row:
        cur_rows.append((cur_row, cur_h))
    if cur_rows:
        pages.append(cur_rows)
    for pi, rows_ in enumerate(pages):
        W = max(sum(t.size[0] + 8 for t in r) for r, _ in rows_)
        H = sum(h + 8 for _, h in rows_)
        sheet = Image.new("RGB", (W, H), (255, 255, 255))
        y = 0
        for r, h in rows_:
            x = 0
            for t in r:
                sheet.paste(t, (x, y))
                x += t.size[0] + 8
            y += h + 8
        name = "%s_%02d.png" % (key, pi + 1)
        sheet.save(os.path.join(out_dir, name))
        index.append((name, sum(len(r) for r, _ in rows_)))
with open(os.path.join(out_dir, "index.tsv"), "w", encoding="utf-8") as f:
    for name, n in index:
        f.write("%s\t%d\n" % (name, n))
print("群組 %d，總表 %d 張，圖 %d 張" % (len(groups), len(index), sum(n for _, n in index)))
