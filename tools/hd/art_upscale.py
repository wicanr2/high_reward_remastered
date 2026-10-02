"""批次產生 HD 圖（演算法 v2，art_lib 管線）。與 upscale.py（基準 v1）介面相同，另依圖像類別選參數。

用法：python3 art_upscale.py <輸入根目錄> <輸出根目錄> [S] [--only 子字串] [--list]
輸入根目錄是 tools/img 的輸出；輸出維持相同的相對路徑。類別由相對路徑決定（route），
類別參數表是 PRESETS；各類別的取捨見 workplace/hd-work/METHOD.md。
取代 upscale.py 的方式：把呼叫 upscale.py 的地方改成呼叫本檔，輸出根目錄改成新目錄，
再用 validate.py 檢查契約。
"""
import os
import sys
import time

from PIL import Image

import art_lib

PRESETS = {
    # 頭像：週期抖色 ＋ 低對比抖色的雙邊濾波 ＋ 模式搜尋上採樣 ＋ HD 輪廓平滑
    "face": dict(per=1, bil=30, beta=8, post=1),
    # 全畫面插圖：同頭像
    "portrait": dict(per=1, bil=30, beta=8, post=1),
    # 標題字樣（OP8：灰階格紋字，3x3 視窗會誤判字形，只用大視窗）
    "logo": dict(per=1, wins="big", beta=8, post=1),
    # 文字與點陣字：不做去抖色（字形的斜線在小視窗內像棋盤）
    "text": dict(per=0, beta=8, post=1),
    # 戰場地圖與世界地圖
    "map": dict(per=1, bil=30, beta=8, post=1),
    # 類照片的戰鬥畫面（VS、兵器圖）：反半色調（導引雙邊濾波）加夾限銳化
    "photo": dict(per=1, bil=35, gs=0.8, beta=6, sharp=0.6),
    # 戰鬥舞台地面：輕度雙邊濾波
    "stage": dict(per=1, bil=20, beta=8),
    # 棋盤格底圖加一條線
    "plain": dict(per=1, beta=8),
    # 小精靈、道具、按鈕、戰場單位：只做週期抖色，不做雙邊濾波（保留小細節）
    "sprite": dict(per=1, beta=8, post=1),
    # 256 色連續調（PCX）：Lanczos 加夾限銳化
    "cont": dict(per=0, up="lz", sharp=0.3),
}


def route(rel):
    """相對路徑 -> 類別名。"""
    parts = rel.replace("\\", "/").split("/")
    top = parts[0]
    name = parts[-1]
    if top == "MRG":
        grp = parts[1]
        if grp == "FACE.MRG":
            return "face"
        if grp in ("VS.MRG", "CANNON.MRG", "PANZER.MRG", "PLANE.MRG"):
            return "photo"
        if grp == "BSTAGE.MRG":
            return "stage"
        if grp == "NOWEAPON.MRG":
            return "plain"
        return "sprite"
    if top in ("GRP", "BIN"):
        return "sprite"
    if top == "GS":
        if name.startswith("OP8."):
            return "logo"
        if name.startswith("OP9.") or name.startswith("ROLL."):
            return "text"
        return "portrait"
    if top in ("PXZ", "PXS"):
        return "map"
    if top == "PCX":
        return "cont"
    if top == "FONT":
        return "text"
    return "sprite"


def options(rel):
    o = dict(PRESETS[route(rel)])
    if o.get("wins") == "big":
        o["wins"] = "big"
    return o


def main():
    args = sys.argv[1:]
    only = None
    lst = False
    if "--only" in args:
        i = args.index("--only")
        only = args[i + 1]
        del args[i:i + 2]
    if "--list" in args:
        lst = True
        args.remove("--list")
    src, dst = args[0], args[1]
    S = int(args[2]) if len(args) > 2 else 2
    n = 0
    t0 = time.time()
    for root, _, files in os.walk(src):
        for f in sorted(files):
            if not f.lower().endswith(".png"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, src)
            if only and not any(s in rel for s in only.split(",")):
                continue
            if lst:
                print(route(rel), rel)
                continue
            out = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            t = time.time()
            rgba = art_lib.process(p, S, options(rel))
            Image.fromarray(rgba, "RGBA").save(out)
            n += 1
            if time.time() - t > 20:
                print(f"{rel} {time.time() - t:.0f}s", flush=True)
    if not lst:
        print(f"完成 {n} 張，S={S}，{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
