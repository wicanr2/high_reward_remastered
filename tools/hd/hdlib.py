"""HD 圖像處理的共用函式（docs/spec/004 第 4 節的素材契約）。

輸入是 tools/img 解碼出的 PNG（調色盤，索引 16 為透明）；輸出是 S 倍的 RGBA PNG：
- 原版不透明區域放大 S 倍後 alpha 必須是 255。
- 輪廓外最多 S 個 HD 像素的羽化，其餘 alpha 為 0。
- 原版沒有透明的圖，整張 alpha 為 255。
只用 PIL、numpy、scipy，在容器內執行（tools/hd/run.sh）。
"""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def load_rgba(path):
    """回傳 (rgba float32 [h,w,4], 是否有透明)。"""
    im = Image.open(path)
    arr = np.array(im.convert("RGBA")).astype(np.float32)
    has_alpha = bool((arr[..., 3] < 255).any())
    return arr, has_alpha


def dedither(rgb):
    """去掉棋盤式抖色：2x2 區塊 (a b / c d) 滿足 a==d、b==c、a!=b 時，
    把涵蓋該像素的所有這種區塊的平均色當成像素色。"""
    h, w, _ = rgb.shape
    if h < 2 or w < 2:
        return rgb
    acc = np.zeros_like(rgb)
    cnt = np.zeros((h, w, 1), np.float32)
    a, b, c, d = rgb[:-1, :-1], rgb[:-1, 1:], rgb[1:, :-1], rgb[1:, 1:]

    def same(p, q):
        return np.all(p == q, axis=2)

    chk = same(a, d) & same(b, c) & ~same(a, b)
    avg = (a + b + c + d) / 4.0
    for dy in (0, 1):
        for dx in (0, 1):
            sl = (slice(dy, h - 1 + dy), slice(dx, w - 1 + dx))
            acc[sl] += avg * chk[..., None]
            cnt[sl] += chk[..., None]
    out = rgb.copy()
    m = cnt[..., 0] > 0
    out[m] = acc[m] / cnt[m]
    return out


def _resize_f(x, size):
    return np.array(Image.fromarray(x.astype(np.float32), mode="F").resize(size, Image.LANCZOS))


def upscale(path, S=2, sharpen=60):
    """基準演算法 v1：去抖色、預乘 alpha 的 Lanczos、輪廓限制、輕度銳化。回傳 PIL RGBA。"""
    arr, has_alpha = load_rgba(path)
    rgb, alpha = arr[..., :3], arr[..., 3] / 255.0
    rgb = dedither(rgb)
    h, w = alpha.shape
    size = (w * S, h * S)
    if not has_alpha:
        chans = [np.clip(_resize_f(rgb[..., i], size), 0, 255) for i in range(3)]
        out = np.dstack(chans + [np.full((h * S, w * S), 255.0)])
        img = Image.fromarray(out.astype(np.uint8), "RGBA")
        base = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.0, percent=sharpen, threshold=2))
        return Image.merge("RGBA", (*base.split(), img.split()[3]))
    pm = rgb * alpha[..., None]
    chans = [_resize_f(pm[..., i], size) for i in range(3)]
    a_up = np.clip(_resize_f(alpha, size), 0, 1)
    a_nn = np.kron(alpha > 0.5, np.ones((S, S))).astype(bool)
    near = ndimage.binary_dilation(a_nn, iterations=S)
    a_out = np.where(a_nn, 1.0, np.where(near, a_up, 0.0))
    denom = np.maximum(a_up, 1e-3)
    out = np.zeros((h * S, w * S, 4), np.float32)
    for i in range(3):
        out[..., i] = np.where(a_out > 0, np.clip(chans[i] / denom, 0, 255), 0)
    out[..., 3] = a_out * 255
    img = Image.fromarray(np.round(out).astype(np.uint8), "RGBA")
    base = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.0, percent=sharpen, threshold=2))
    return Image.merge("RGBA", (*base.split(), img.split()[3]))


def check_contract(orig_path, hd_path, S=2):
    """回傳違反契約的描述清單（空 ＝ 通過）。"""
    errs = []
    arr, has_alpha = load_rgba(orig_path)
    h, w = arr.shape[:2]
    hd = np.array(Image.open(hd_path).convert("RGBA"))
    if hd.shape[0] != h * S or hd.shape[1] != w * S:
        return [f"尺寸 {hd.shape[1]}x{hd.shape[0]}，應為 {w * S}x{h * S}"]
    opaque = np.kron(arr[..., 3] > 127, np.ones((S, S))).astype(bool)
    if (hd[..., 3][opaque] != 255).any():
        errs.append(f"輪廓內有 {(hd[..., 3][opaque] != 255).sum()} 個像素 alpha 不是 255")
    if not has_alpha:
        return errs
    near = ndimage.binary_dilation(opaque, iterations=S)
    out_of_band = (~near) & (hd[..., 3] > 0)
    if out_of_band.any():
        errs.append(f"羽化帶之外有 {out_of_band.sum()} 個像素 alpha 大於 0")
    return errs
