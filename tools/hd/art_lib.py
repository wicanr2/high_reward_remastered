"""HD 圖像處理 v2：週期性抖色偵測、去抖色、類別式上採樣與透明邊緣處理。

輸入是 tools/img 解碼出的 PNG（調色盤，索引 16 為透明）；輸出是 S 倍的 RGBA PNG。
契約見 docs/spec/004 第 4 節，由 hdlib.check_contract / validate.py 檢查。
只用 PIL、numpy、scipy，在容器內執行（tools/hd/run.sh）。
本檔不修改、不取代 hdlib.py；art_upscale.py 以本檔為基礎產生 v2 成品。
"""
import numpy as np
from PIL import Image
from scipy import ndimage


# ---------------------------------------------------------------- 載入

def load(path, vt=128):
    """回傳 dict：rgb (h,w,3 float32)、valid (h,w bool，alpha>127)、idx (h,w int32，無效為 -1)、
    has_alpha。透明像素的 RGB 一律不參與任何計算（解碼器把索引 16 塗成洋紅 255,0,255）。"""
    im = Image.open(path)
    rgba = np.array(im.convert("RGBA"))
    valid = rgba[..., 3] >= vt
    rgb = rgba[..., :3].astype(np.float32)
    key = (rgba[..., 0].astype(np.int64) << 16) | (rgba[..., 1].astype(np.int64) << 8) | rgba[..., 2]
    key = np.where(valid, key, -1)
    uniq, inv = np.unique(key, return_inverse=True)
    idx = inv.reshape(key.shape).astype(np.int32)
    if uniq[0] == -1:
        idx = idx - 1  # 無效像素的 id 變成 -1
    has_alpha = bool((rgba[..., 3] < 255).any())
    rgb = np.where(valid[..., None], rgb, 0).astype(np.float32)
    return dict(rgb=rgb, valid=valid, idx=idx, has_alpha=has_alpha, alpha=rgba[..., 3])


# ---------------------------------------------------------------- 週期性抖色

def _win_all(a, h, w):
    """a 為 bool (H,W)；回傳 (H-h+1, W-w+1)，每格代表 a[y:y+h, x:x+w] 是否全真。h 或 w 為 0 時恆真。"""
    H, W = a.shape
    if h <= 0 or w <= 0:
        return np.ones((H - max(h, 1) + 1, W - max(w, 1) + 1), bool)
    out = a[:H - h + 1, :W - w + 1].copy()
    for dy in range(h):
        for dx in range(w):
            out &= a[dy:H - h + 1 + dy, dx:W - w + 1 + dx]
    return out


def _shift(w, dy, dx):
    """o[y,x] ＝ w[y+dy, x+dx]，超出範圍為 False。"""
    o = np.zeros_like(w)
    ys0, ys1 = max(0, -dy), w.shape[0] - max(0, dy)
    xs0, xs1 = max(0, -dx), w.shape[1] - max(0, dx)
    o[ys0:ys1, xs0:xs1] = w[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return o


WINDOWS = ((4, 4), (2, 4), (4, 2), (3, 3))


def periodic_dedither(idx, rgb, windows=WINDOWS, grow_iter=4):
    """週期為 2 的有序抖色（棋盤、25%、75%）去抖色。

    視窗 (h,w) 內 P(x,y)==P(x+2,y) 且 P(x,y)==P(x,y+2) 成立（h 或 w 為 2 的方向沒有該方向的條件）時，
    視窗是週期圖樣，視窗內像素改為左上 2x2 圖樣的平均（一個週期的平均）。
    - 4x4 視窗：能涵蓋大面積抖色。1 像素寬的斜線在 2x2 看起來是棋盤，在 4x4 就不是週期的，所以不會被誤判。
      條紋型（橫條、直條）需要沿條紋方向連續 6 格才算，避免平行的細線被當成抖色。
    - 2x4、4x2、3x3 視窗：涵蓋寬度只有 2 到 3 像素、4x4 放不下的抖色帶（漸層過渡）與小精靈內的小塊抖色，只接受棋盤與稀疏點型，不接受條紋型，
      且圖樣內亮度差不超過 100（高對比的鋸齒線，例如睫毛，不當成抖色）。
    之後沿圖樣延伸：與已判定像素的圖樣相符、至少有 2 個相符的鄰居且沒有不相符鄰居的像素併入。
    回傳 C (h,w,3 float32)、dith (h,w bool，圖樣非單色的像素)。"""
    H, W = idx.shape
    C = rgb.copy()
    ok = idx >= 0
    eqx = np.zeros((H, W), bool)
    eqy = np.zeros((H, W), bool)
    eqx[:, :-2] = (idx[:, :-2] == idx[:, 2:]) & ok[:, :-2]
    eqy[:-2, :] = (idx[:-2, :] == idx[2:, :]) & ok[:-2, :]
    acc = np.zeros((H, W, 3), np.float32)
    cnt = np.zeros((H, W), np.float32)
    cnt_nf = np.zeros((H, W), np.float32)
    tile = np.full((4, H, W), -1, np.int32)
    for wh, ww in windows:
        if H < wh or W < ww:
            continue
        nh, nw = H - wh + 1, W - ww + 1
        wok = _win_all(eqy, wh - 2, ww)[:nh, :nw] & _win_all(eqx, wh, ww - 2)[:nh, :nw]
        # 區塊：每個 2x2 子區塊 (y..y+1, x..x+1) 的色 id，且 4 個像素都有效
        a, b = idx[:nh, :nw], idx[:nh, 1:nw + 1]
        c, d = idx[1:nh + 1, :nw], idx[1:nh + 1, 1:nw + 1]
        nonflat = ~((a == b) & (a == c) & (a == d))
        vstripe = (a == c) & (b == d) & (a != b)
        hstripe = (a == b) & (c == d) & (a != c)
        if (wh, ww) == (4, 4):
            wok = wok & ~(vstripe & ~(_shift(wok, 0, 2) | _shift(wok, 0, -2)))
            wok = wok & ~(hstripe & ~(_shift(wok, 2, 0) | _shift(wok, -2, 0)))
        else:
            lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
            l4 = np.stack([lum[:nh, :nw], lum[:nh, 1:nw + 1], lum[1:nh + 1, :nw], lum[1:nh + 1, 1:nw + 1]])
            wok = wok & ~vstripe & ~hstripe & nonflat & ((l4.max(0) - l4.min(0)) <= 100)
        mean = (rgb[:nh, :nw] + rgb[:nh, 1:nw + 1] + rgb[1:nh + 1, :nw] + rgb[1:nh + 1, 1:nw + 1]) / 4.0
        ys, xs = np.mgrid[0:nh, 0:nw]
        sel_nf = wok & nonflat
        for py in range(2):
            for px in range(2):
                ph = ((ys + py) % 2) * 2 + ((xs + px) % 2)
                col = idx[py:py + nh, px:px + nw]
                for q in range(4):
                    sel = sel_nf & (ph == q)
                    if not sel.any():
                        continue
                    for dy in range(wh):
                        for dx in range(ww):
                            sub = tile[q, dy:dy + nh, dx:dx + nw]
                            sub[sel] = col[sel]
        for dy in range(wh):
            for dx in range(ww):
                acc[dy:dy + nh, dx:dx + nw] += mean * wok[..., None]
                cnt[dy:dy + nh, dx:dx + nw] += wok
                cnt_nf[dy:dy + nh, dx:dx + nw] += sel_nf
    cov = cnt > 0
    C[cov] = acc[cov] / cnt[cov][:, None]
    R = cnt_nf > 0
    dith = R.copy()
    ph_full = (np.arange(H)[:, None] % 2) * 2 + (np.arange(W)[None, :] % 2)
    for _ in range(grow_iter):
        support = np.zeros((H, W), np.int32)
        against = np.zeros((H, W), np.int32)
        new_tile = np.full((4, H, W), -1, np.int32)
        new_mean = np.zeros((H, W, 3), np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nR = np.zeros((H, W), bool)
            nT = np.full((4, H, W), -1, np.int32)
            nM = np.zeros((H, W, 3), np.float32)
            ys0, ys1 = max(0, -dy), H - max(0, dy)
            xs0, xs1 = max(0, -dx), W - max(0, dx)
            nR[ys0:ys1, xs0:xs1] = R[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
            nT[:, ys0:ys1, xs0:xs1] = tile[:, ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
            nM[ys0:ys1, xs0:xs1] = C[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
            expect = np.take_along_axis(nT, ph_full[None], axis=0)[0]
            cons = nR & (expect == idx) & (idx >= 0)
            incons = nR & ~cons
            first = cons & (support == 0)
            for q in range(4):
                new_tile[q][first] = nT[q][first]
            new_mean[first] = nM[first]
            support += cons
            against += incons
        add = (~R) & (idx >= 0) & (support >= 2) & (against == 0)
        if not add.any():
            break
        for q in range(4):
            tile[q][add] = new_tile[q][add]
        C[add] = new_mean[add]
        R |= add
        dith |= add
    return C, dith


# ---------------------------------------------------------------- 低對比抖色與雜訊：聯合雙邊濾波

def gaussian_norm(x, valid, sigma):
    """只用有效像素的正規化高斯平滑。x (h,w,3)。"""
    v = valid.astype(np.float32)
    num = np.stack([ndimage.gaussian_filter(x[..., c] * v, sigma, mode="nearest") for c in range(3)], -1)
    den = ndimage.gaussian_filter(v, sigma, mode="nearest")
    return num / np.maximum(den, 1e-4)[..., None]


def bilateral_denoise(C, valid, sigma_s=1.5, sigma_r=25.0, guide_sigma=0.8, radius=3, passes=1):
    """以預先平滑的影像當導引的雙邊濾波。
    導引 G ＝ 高斯平滑的 C，所以相鄰像素是否算「同一色塊」由平滑後的色調判斷，
    不被抖色造成的高頻起伏影響；跨越高對比邊緣的鄰居權重趨近 0，線條與輪廓保留。"""
    H, W, _ = C.shape
    out = C
    for _ in range(passes):
        G = gaussian_norm(out, valid, guide_sigma) if guide_sigma > 0 else out
        r = radius
        Gp = np.pad(G, ((r, r), (r, r), (0, 0)), mode="edge")
        Cp = np.pad(out, ((r, r), (r, r), (0, 0)), mode="edge")
        Vp = np.pad(valid.astype(np.float32), r, mode="edge")
        acc = np.zeros_like(out)
        wsum = np.zeros((H, W), np.float32)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                gs = np.exp(-(dy * dy + dx * dx) / (2 * sigma_s * sigma_s))
                Gq = Gp[r + dy:r + dy + H, r + dx:r + dx + W]
                d2 = ((Gq - G) ** 2).sum(-1)
                w = (gs * np.exp(-d2 / (2 * sigma_r * sigma_r))).astype(np.float32) * Vp[r + dy:r + dy + H, r + dx:r + dx + W]
                acc += w[..., None] * Cp[r + dy:r + dy + H, r + dx:r + dx + W]
                wsum += w
        res = acc / np.maximum(wsum, 1e-6)[..., None]
        out = np.where(valid[..., None], res, out).astype(np.float32)
    return out


# ---------------------------------------------------------------- 類別式（模式搜尋）上採樣

def _ru_points(Cn, Vn, S, R, sigma_k, beta, center_boost, sim_sigma, vote_exp):
    """Cn (N,K,3)、Vn (N,K)：N 個原圖像素各自的 K ＝ (2R+1)^2 個鄰居（顏色與有效性）。
    回傳 (色 (N,S,S,3)，覆蓋率 (N,S,S))。"""
    N, K = Vn.shape
    offs = [(dy, dx) for dy in range(-R, R + 1) for dx in range(-R, R + 1)]
    f = [(a + 0.5) / S - 0.5 for a in range(S)]
    wy = np.array([[np.exp(-((d - f[a]) ** 2) / (2 * sigma_k ** 2)) for d in range(-R, R + 1)] for a in range(S)], np.float32)
    kap = np.zeros((S, S, K), np.float32)
    for a in range(S):
        for b in range(S):
            for k, (dy, dx) in enumerate(offs):
                kap[a, b, k] = wy[a][dy + R] * wy[b][dx + R] * (center_boost if (dy == 0 and dx == 0) else 1.0)
    Cv = [Cn[:, k] for k in range(K)]
    Vv = [Vn[:, k] for k in range(K)]
    Sacc = np.zeros((S, S, K, N), np.float32)
    inv2 = 1.0 / (2 * sim_sigma * sim_sigma)
    for m in range(K):
        for n in range(m, K):
            if m == n:
                sim = np.ones(N, np.float32)
            else:
                d = Cv[m] - Cv[n]
                sim = np.exp(-(d * d).sum(-1) * inv2).astype(np.float32)
            for a in range(S):
                for b in range(S):
                    Sacc[a, b, n] += (kap[a, b, m] * sim) * Vv[m]
                    if m != n:
                        Sacc[a, b, m] += (kap[a, b, n] * sim) * Vv[n]
    out = np.zeros((N, S, S, 3), np.float32)
    cov = np.zeros((N, S, S), np.float32)
    for a in range(S):
        for b in range(S):
            tot = np.zeros(N, np.float32)
            for k in range(K):
                tot += kap[a, b, k] * Vv[k]
            totk = float(kap[a, b].sum())
            num = np.zeros((N, 3), np.float32)
            den = np.zeros(N, np.float32)
            inv_tot = 1.0 / np.maximum(tot, 1e-6)
            for k in range(K):
                s = Sacc[a, b, k] * inv_tot
                om = kap[a, b, k] * Vv[k] * np.power(np.maximum(s, 1e-6), vote_exp * (beta - 1.0))
                num += om[:, None] * Cv[k]
                den += om
            out[:, a, b] = num / np.maximum(den, 1e-9)[:, None]
            cov[:, a, b] = tot / totk
    return out, cov


def robust_upscale(C, valid, S=2, sigma_k=0.5, beta=8.0, center_boost=1.15, sim_sigma=28.0,
                   R=2, chunk=40000, vote_exp=1.0):
    """模式搜尋式上採樣。每個 HD 像素從原圖 (2R+1)x(2R+1) 的鄰居取色：
    每個鄰居的票數 ＝ 以高斯距離加權、與它顏色相近（高斯相似度，sim_sigma）的鄰居質量；
    輸出 ＝ 以 (票數)^(beta-1) 再加權的顏色平均。顏色相近的鄰居合成同一群（漸層平滑內插），
    顏色差很多的群之間取質量較大者（邊緣銳利、輪廓圓化）；center_boost 提高最近像素的質量，
    使 1 像素寬的線與孤立點不被吃掉。
    整個 (2R+1)^2 鄰域顏色相同的像素直接複製，視窗內全是無效像素者略過（輸出 0），其餘才做投票。
    回傳 (色 (S*h,S*w,3)，覆蓋率 (S*h,S*w)：核質量落在有效像素的比例)。"""
    H, W, _ = C.shape
    Cp = np.pad(C, ((R, R), (R, R), (0, 0)), mode="edge")
    Vp = np.pad(valid.astype(np.float32), R, mode="edge")
    offs = [(dy, dx) for dy in range(-R, R + 1) for dx in range(-R, R + 1)]
    flat = valid.copy()
    for dy, dx in offs:
        flat &= (Vp[R + dy:R + dy + H, R + dx:R + dx + W] == 1) & \
                (Cp[R + dy:R + dy + H, R + dx:R + dx + W] == C).all(-1)
    anyv = ndimage.maximum_filter(valid.astype(np.uint8), size=2 * R + 1, mode="constant") > 0
    todo = ~flat & anyv
    out = np.repeat(np.repeat(np.where(valid[..., None], C, 0), S, 0), S, 1).astype(np.float32)
    cov = np.repeat(np.repeat(valid.astype(np.float32), S, 0), S, 1)
    ys, xs = np.nonzero(todo)
    for s0 in range(0, len(ys), chunk):
        yy, xx = ys[s0:s0 + chunk], xs[s0:s0 + chunk]
        Cn = np.stack([Cp[yy + R + dy, xx + R + dx] for dy, dx in offs], 1)
        Vn = np.stack([Vp[yy + R + dy, xx + R + dx] for dy, dx in offs], 1)
        res, cv = _ru_points(Cn, Vn, S, R, sigma_k, beta, center_boost, sim_sigma, vote_exp)
        for a in range(S):
            for b in range(S):
                out[yy * S + a, xx * S + b] = res[:, a, b]
                cov[yy * S + a, xx * S + b] = cv[:, a, b]
    return out, cov


# ---------------------------------------------------------------- 透明邊緣、銳化

def finish_alpha(color, cov, valid, S, a_gain=1.4, a_max=0.7):
    """組合 RGBA：輪廓內 alpha ＝ 255；輪廓外最多 S 個 HD 像素，alpha 由核覆蓋率決定（最大 a_max）。
    alpha ＝ 0 的像素把 RGB 填成最近有效像素的顏色（避免縮放時的暗邊或色污染）。"""
    H, W = valid.shape
    a_nn = np.kron(valid, np.ones((S, S))).astype(bool)
    if a_nn.all():
        rgb = np.clip(np.round(color), 0, 255).astype(np.uint8)
        return np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
    near = ndimage.binary_dilation(a_nn, iterations=S)
    soft = np.clip(cov * a_gain, 0, a_max)
    alpha = np.where(a_nn, 1.0, np.where(near, soft, 0.0))
    # 色彩外推：無有效資訊（覆蓋率極低）的像素取最近的 alpha > 0.25 像素色
    good = a_nn | (near & (cov > 0.02))
    idx = ndimage.distance_transform_edt(~good, return_distances=False, return_indices=True)
    col = color[idx[0], idx[1]]
    col = np.where(good[..., None], color, col)
    rgb = np.clip(np.round(col), 0, 255).astype(np.uint8)
    return np.dstack([rgb, np.round(alpha * 255).astype(np.uint8)])


def clamp_sharpen(rgba, amount=0.6, sigma=1.0, size=3):
    """限制範圍的銳化：unsharp 後夾在原像素 size x size 鄰域的最小與最大值之間（不產生光暈）。"""
    rgb = rgba[..., :3].astype(np.float32)
    bl = np.stack([ndimage.gaussian_filter(rgb[..., c], sigma, mode="nearest") for c in range(3)], -1)
    sh = rgb + amount * (rgb - bl)
    lo = np.stack([ndimage.minimum_filter(rgb[..., c], size, mode="nearest") for c in range(3)], -1)
    hi = np.stack([ndimage.maximum_filter(rgb[..., c], size, mode="nearest") for c in range(3)], -1)
    sh = np.clip(sh, lo, hi)
    out = rgba.copy()
    out[..., :3] = np.clip(np.round(sh), 0, 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------- 管線

def process(path, S, opt):
    """依參數字典 opt 產生 RGBA（uint8 陣列）。參數：
    per 週期性去抖色（0/1）；bil、bs、gs、br、bp 雙邊濾波的 sigma_r、sigma_s、導引 sigma、半徑、次數（bil ＝ 0 不做）；
    up 上採樣：ru（模式搜尋）、lz（Lanczos）；beta、sk、cb、ss 模式搜尋參數；
    post、psk、pbeta、pcb HD 解析度的輪廓平滑次數與參數；sharp 夾限銳化量。"""
    d = load(path, int(opt.get("vt", 128)))
    C = d["rgb"]
    if int(opt.get("per", 1)):
        wins = WINDOWS if opt.get("wins", "all") == "all" else WINDOWS[:3]
        C, _ = periodic_dedither(d["idx"], d["rgb"], windows=wins)
    if float(opt.get("bil", 0)) > 0:
        C = bilateral_denoise(C, d["valid"], sigma_s=float(opt.get("bs", 1.5)), sigma_r=float(opt["bil"]),
                              passes=int(opt.get("bp", 1)), guide_sigma=float(opt.get("gs", 0.0)),
                              radius=int(opt.get("br", 3)))
    valid = d["valid"]
    if opt.get("up", "ru") == "ru":
        col, cov = robust_upscale(C, valid, S=S, sigma_k=float(opt.get("sk", 0.5)), beta=float(opt.get("beta", 8)),
                                  center_boost=float(opt.get("cb", 1.15)), sim_sigma=float(opt.get("ss", 28)))
    else:
        from hdlib import _resize_f
        h, w = valid.shape
        v = valid.astype(np.float32)
        chans = [_resize_f(C[..., i] * v, (w * S, h * S)) for i in range(3)]
        a_up = np.clip(_resize_f(v, (w * S, h * S)), 0, 1)
        col = np.clip(np.stack([c / np.maximum(a_up, 1e-3) for c in chans], -1), 0, 255)
        cov = a_up
    a_nn = np.kron(valid, np.ones((S, S))).astype(bool)
    for _ in range(int(opt.get("post", 0))):
        col, _c = robust_upscale(col, a_nn, S=1, sigma_k=float(opt.get("psk", 0.7)), beta=float(opt.get("pbeta", 8)),
                                 center_boost=float(opt.get("pcb", 1.3)), sim_sigma=float(opt.get("ss", 28)))
    rgba = finish_alpha(col, cov, valid, S, a_gain=float(opt.get("ag", 1.4)), a_max=float(opt.get("am", 0.7)))
    if float(opt.get("sharp", 0)) > 0:
        rgba = clamp_sharpen(rgba, amount=float(opt["sharp"]))
    return rgba
