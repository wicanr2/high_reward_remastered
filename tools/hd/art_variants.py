"""各類別候選方法的保真度比較（每類別取代表樣張，跑 v1 與數個 v2 變體，算 art_fidelity 的指標）。

用法：python3 art_variants.py <原圖根目錄> <基準 v1 根目錄> <輸出 tsv>
輸出：每列 類別、變體、樣張數、各指標平均、平均秒數（v1 的秒數為空）。
"""
import os
import sys
import time

import numpy as np
from PIL import Image

import art_fidelity
import art_lib

CASES = {
    "face": (["MRG/FACE.MRG/FACE.MRG_000.png", "MRG/FACE.MRG/FACE.MRG_010.png", "MRG/FACE.MRG/FACE.MRG_050.png"], {
        "per": "per=1,beta=8,post=1",
        "per+bil30": "per=1,bil=30,beta=8,post=1",
        "per+bil30,lz": "per=1,bil=30,up=lz,sharp=0.5",
        "per+bil60,gs1": "per=1,bil=60,gs=1.0,beta=8,post=1",
    }),
    "sprite": (["MRG/ITEM.MRG/ITEM.MRG_005.png", "MRG/KOMA.MRG/KOMA.MRG_012.png", "MRG/SPOINT.MRG/SPOINT.MRG_004.png",
                "MRG/BC32.MRG/BC32.MRG_019.png", "MRG/FCHAR.MRG/FCHAR.MRG_002.png", "MRG/BUTTON.MRG/BUTTON.MRG_005.png"], {
        "per4": "per=1,wins=big,beta=8",
        "per5": "per=1,beta=8",
        "per5+post": "per=1,beta=8,post=1",
        "per5,lz": "per=1,up=lz,sharp=0.5",
        "per5+bil20": "per=1,bil=20,beta=8,post=1",
    }),
    "photo": (["MRG/VS.MRG/VS.MRG_003.png", "MRG/CANNON.MRG/CANNON.MRG_000.png", "MRG/PANZER.MRG/PANZER.MRG_002.png"], {
        "per": "per=1,beta=6",
        "bil40": "per=1,bil=40,gs=0.8,beta=6",
        "bil45,gs1": "per=1,bil=45,gs=1.0,beta=6",
        "bil60,gs1,2p": "per=1,bil=60,gs=1.0,bp=2,bs=2,br=4,beta=6",
        "bil35+sharp": "per=1,bil=35,gs=0.8,beta=6,sharp=0.6",
        "bil45,lz": "per=1,bil=45,gs=1.0,up=lz,sharp=0.4",
    }),
    "stage": (["MRG/BSTAGE.MRG/BSTAGE.MRG_000.png", "MRG/BSTAGE.MRG/BSTAGE.MRG_003.png"], {
        "per": "per=1,beta=8",
        "per+bil20": "per=1,bil=20,beta=8",
        "bil40,gs1": "per=1,bil=40,gs=1.0,beta=6",
    }),
    "map": (["PXZ/MAP01.PXZ.png", "PXS/GMAP.PXS.png"], {
        "per": "per=1,beta=8",
        "per+bil30": "per=1,bil=30,beta=8,post=1",
        "bil45,gs1": "per=1,bil=45,gs=1.0,beta=6",
    }),
    "portrait": (["GS/ED0.GS.png", "GS/OP4.GS.png"], {
        "per0": "per=0,beta=8,post=1",
        "per": "per=1,beta=8,post=1",
        "per+bil30": "per=1,bil=30,beta=8,post=1",
        "per+bil30,lz": "per=1,bil=30,up=lz,sharp=0.5",
    }),
    "text": (["GS/OP9.GS.png", "FONT/CFONT.15_sample.png"], {
        "per0": "per=0,beta=8,post=1",
        "per": "per=1,beta=8,post=1",
        "per0,lz": "per=0,up=lz,sharp=0.4",
    }),
    "cont": (["PCX/H-TXT.PCX.png"], {
        "ru": "per=0,beta=6",
        "ru+post": "per=1,beta=8,post=1",
        "lz+sharp": "per=0,up=lz,sharp=0.3",
    }),
}

KEYS = ["mae_raw", "mae_lp", "max_lp", "edge_mis", "overshoot", "hfe_o", "hfe_h", "band_bad"]


def avg(ms, k):
    arr = np.array([m[k] for m in ms], float)
    return float(np.nanmean(arr)) if np.isfinite(arr).any() else float("nan")


def main():
    src, base, out = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    tmp = "/w/hd-work/proto2/variants"
    os.makedirs(tmp, exist_ok=True)
    rows = []
    for cat, (imgs, variants) in CASES.items():
        if only and cat not in only:
            continue
        ms = [art_fidelity.metrics(f"{src}/{r}", f"{base}/{r}", 2) for r in imgs]
        rows.append((cat, "v1 基準", len(imgs), {k: avg(ms, k) for k in KEYS}, None))
        for name, spec in variants.items():
            opt = dict(kv.split("=") for kv in spec.split(",") if kv)
            ms, t0 = [], time.time()
            for r in imgs:
                rgba = art_lib.process(f"{src}/{r}", 2, opt)
                name_s = name.replace(',', '_').replace('+', 'p').replace(' ', '')
                p = f"{tmp}/{cat}__{name_s}__{os.path.basename(r)}"
                Image.fromarray(rgba, "RGBA").save(p)
                ms.append(art_fidelity.metrics(f"{src}/{r}", p, 2))
            rows.append((cat, name, len(imgs), {k: avg(ms, k) for k in KEYS}, (time.time() - t0) / len(imgs)))
            print(cat, name, flush=True)
    with open(out, "w") as fh:
        fh.write("cat\tvariant\tn\t" + "\t".join(KEYS) + "\tsec\n")
        for cat, name, n, m, t in rows:
            fh.write(f"{cat}\t{name}\t{n}\t" + "\t".join(f"{m[k]:.4g}" for k in KEYS) + f"\t{'' if t is None else f'{t:.1f}'}\n")


if __name__ == "__main__":
    main()
