"""HD 圖保真度檢查：把 HD 箱形縮回原尺寸，和原圖與去抖色後的原圖比較。

用法：python3 art_fidelity.py <原圖根目錄> <HD 根目錄> <S> <輸出 tsv> [--top N] [--only 子字串]

每張圖的欄位（顏色單位 0 至 255，只算原版不透明的像素）：
  mae_raw / max_raw   箱形縮回後與原圖（未去抖色）的平均與最大絕對差（通道最大值）
  mae_C / max_C       與去抖色後的原圖（art_lib.periodic_dedither，不含雙邊濾波）的差
  mae_lp / max_lp     兩邊都先做 sigma=1.5 的高斯低通再比：與去抖色演算法無關的色調保真度
  edge_mis            強邊緣像素（與 8 鄰居色距 >= 90，且不在週期抖色範圍）縮回後
                      最近調色盤色不等於原色的比例：線條被吃掉、變灰或斷裂時上升
  overshoot           HD 像素任一通道超出對應原圖 5x5 鄰域 [min-3, max+3] 的比例：光暈與振鈴
  hfe_o / hfe_h      非強邊緣處的高頻能量（拉普拉斯絕對值平均）：原圖與 HD 縮回後；hfe_h 遠低於 hfe_o 代表抖色去得多
  band_bad            alpha 在 1 到 254 的像素中，顏色與最近不透明像素色距 > 60 的個數：色彩污染
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import art_lib


def box_down(a, S):
    h, w = a.shape[0] // S, a.shape[1] // S
    return a[:h * S, :w * S].reshape(h, S, w, S, -1).mean(axis=(1, 3))


def lowpass(x, valid, sigma=1.5):
    return art_lib.gaussian_norm(x, valid, sigma)


def laplace_abs(x):
    k = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], np.float32)
    return np.abs(np.stack([ndimage.convolve(x[..., c], k, mode="nearest") for c in range(3)], -1)).mean(-1)


def metrics(orig_path, hd_path, S):
    d = art_lib.load(orig_path)
    valid = d["valid"]
    raw = d["rgb"]
    hd = np.array(Image.open(hd_path).convert("RGBA"))
    H, W = valid.shape
    if hd.shape[0] != H * S or hd.shape[1] != W * S:
        return None
    hrgb = hd[..., :3].astype(np.float32)
    down = box_down(hrgb, S)
    C, dith = art_lib.periodic_dedither(d["idx"], d["rgb"])
    v = valid
    nv = max(int(v.sum()), 1)
    res = {}
    diff = np.abs(down - raw).max(-1)
    res["mae_raw"] = float((np.abs(down - raw).mean(-1))[v].sum() / nv)
    res["max_raw"] = float(diff[v].max()) if v.any() else 0.0
    diffC = np.abs(down - C).max(-1)
    res["mae_C"] = float((np.abs(down - C).mean(-1))[v].sum() / nv)
    res["max_C"] = float(diffC[v].max()) if v.any() else 0.0
    lp_o, lp_h = lowpass(raw, v), lowpass(down, v)
    dl = np.abs(lp_o - lp_h)
    res["mae_lp"] = float(dl.mean(-1)[v].sum() / nv)
    res["max_lp"] = float(dl.max(-1)[v].max()) if v.any() else 0.0
    # 強邊緣與線條保留
    pad = np.pad(raw, ((1, 1), (1, 1), (0, 0)), mode="edge")
    padv = np.pad(valid, 1, mode="edge")
    mx = np.zeros((H, W), np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            q = pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
            qv = padv[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
            dd = np.sqrt(((q - raw) ** 2).sum(-1)) * qv
            mx = np.maximum(mx, dd)
    strong = (mx >= 90) & v
    near_dith = ndimage.binary_dilation(dith, iterations=1)
    E = strong & ~near_dith
    if E.any():
        cols = np.unique(raw[v].reshape(-1, 3), axis=0)
        sub = down[E]
        orig_c = raw[E]
        bad = 0
        for s0 in range(0, len(sub), 20000):
            ch = sub[s0:s0 + 20000]
            dd = ((ch[:, None, :] - cols[None, :, :]) ** 2).sum(-1)
            snapped = cols[dd.argmin(1)]
            bad += int((np.abs(snapped - orig_c[s0:s0 + 20000]).max(-1) > 0.5).sum())
        res["edge_mis"] = bad / len(sub)
    else:
        res["edge_mis"] = 0.0
    # 光暈
    mn = np.stack([ndimage.minimum_filter(np.where(v, raw[..., c], 255), 5, mode="nearest") for c in range(3)], -1)
    mxx = np.stack([ndimage.maximum_filter(np.where(v, raw[..., c], 0), 5, mode="nearest") for c in range(3)], -1)
    mn_up = np.kron(mn, np.ones((S, S, 1)))
    mx_up = np.kron(mxx, np.ones((S, S, 1)))
    inside = np.kron(v, np.ones((S, S))).astype(bool)
    over = ((hrgb < mn_up - 3) | (hrgb > mx_up + 3)).any(-1) & inside
    res["overshoot"] = float(over.sum() / max(inside.sum(), 1))
    # 高頻能量
    smooth = v & ~ndimage.binary_dilation(strong, iterations=2)
    smooth = ndimage.binary_erosion(smooth, iterations=1)
    if smooth.sum() > 20:
        eo = laplace_abs(raw)[smooth].mean()
        eh = laplace_abs(down)[smooth].mean()
        res["hfe_o"], res["hfe_h"] = float(eo), float(eh)
    else:
        res["hfe_o"], res["hfe_h"] = float("nan"), float("nan")
    # 透明邊緣色彩污染
    a = hd[..., 3]
    band = (a > 0) & (a < 255)
    if band.any():
        opaque = a == 255
        idx = ndimage.distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        near = hrgb[idx[0], idx[1]]
        dist = np.sqrt(((hrgb - near) ** 2).sum(-1))
        res["band_bad"] = int((dist[band] > 60).sum())
    else:
        res["band_bad"] = 0
    return res


def group_of(rel):
    parts = rel.split(os.sep)
    if parts[0] in ("MRG", "GRP", "BIN") and len(parts) > 2:
        return parts[1]
    return parts[0]


def main():
    args = [a for a in sys.argv[1:]]
    top = 20
    only = None
    if "--top" in args:
        i = args.index("--top")
        top = int(args[i + 1])
        del args[i:i + 2]
    if "--only" in args:
        i = args.index("--only")
        only = args[i + 1]
        del args[i:i + 2]
    src, dst, S, out = args[0], args[1], int(args[2]), args[3]
    keys = ["mae_raw", "max_raw", "mae_C", "max_C", "mae_lp", "max_lp", "edge_mis", "overshoot", "hfe_o", "hfe_h", "band_bad"]
    rows = []
    for root, _, files in os.walk(dst):
        for f in sorted(files):
            if not f.lower().endswith(".png"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, dst)
            if only and only not in rel:
                continue
            o = os.path.join(src, rel)
            if not os.path.exists(o):
                continue
            m = metrics(o, p, S)
            if m is None:
                print("尺寸不符", rel)
                continue
            rows.append((rel, m))
    rows.sort(key=lambda r: r[0])
    with open(out, "w") as fh:
        fh.write("file\tgroup\t" + "\t".join(keys) + "\n")
        for rel, m in rows:
            fh.write(f"{rel}\t{group_of(rel)}\t" + "\t".join(f"{m[k]:.4g}" for k in keys) + "\n")
    # 類別摘要
    groups = {}
    for rel, m in rows:
        groups.setdefault(group_of(rel), []).append(m)
    print("group\tn\t" + "\t".join(keys))
    for g in sorted(groups):
        ms = groups[g]
        vals = []
        for k in keys:
            arr = np.array([x[k] for x in ms], float)
            if k.startswith("max_") or k == "band_bad":
                vals.append(f"{np.nanmax(arr):.4g}")
            else:
                vals.append(f"{np.nanmean(arr):.4g}")
        print(f"{g}\t{len(ms)}\t" + "\t".join(vals))
    print("-- 偏差最大的 %d 張（依 mae_lp）" % top)
    for rel, m in sorted(rows, key=lambda r: -r[1]["mae_lp"])[:top]:
        print(rel, " ".join(f"{k}={m[k]:.4g}" for k in ("mae_raw", "mae_lp", "max_lp", "edge_mis", "overshoot")))


if __name__ == "__main__":
    main()
