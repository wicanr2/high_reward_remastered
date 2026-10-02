"""解出《高報酬戰將》全部已知圖像容器為 PNG，並寫 inventory.tsv 與 out/decode_log.txt。

在 Docker 內執行（見 run.sh）：原版目錄唯讀掛在 /orig，本目錄掛在 /w。
格式規則與證據見 REPORT.md；每個分支只實作反組譯或位元組可支持的規則。
"""
import glob
import hashlib
import os
import struct
import sys
import traceback

sys.path.insert(0, '/w')
import hrimg

ORIG = '/orig'
OUT = '/w/out'
TRANSPARENT = 16  # 有遮罩或未覆蓋像素使用的索引

# GS 檔與調色盤的配對，以及配對的反組譯證據（scripts/pairing.py 的輸出）
GS_PAIRS = {
    'IMG.GS': ('IMG.RGB', 'OP.EXE 1815:0113 sub_195F2(IMG.GS); 1815:011F sub_19CF6(IMG.RGB)'),
    'OP0.GS': ('OP0.RGB', 'OP.EXE 1815:0540 sub_19C4F(OP0.RGB); 1815:054E sub_195F2(OP0.GS)'),
    'OP1.GS': ('OP1.RGB', 'OP.EXE 1815:0616 sub_19C4F(OP1.RGB); 1815:0624 sub_195F2(OP1.GS)'),
    'OP2.GS': ('OP2.RGB', 'OP.EXE 1815:06E8 sub_19C4F(OP2.RGB); 1815:06F6 sub_195F2(OP2.GS)'),
    'OP3.GS': ('OP3.RGB', 'OP.EXE 1815:0802 sub_19C4F(OP3.RGB); 1815:0810 sub_195F2(OP3.GS)'),
    'OP4.GS': ('OP4.RGB', 'OP.EXE 1815:08F5 sub_19C4F(OP4.RGB); 1815:0903 sub_195F2(OP4.GS)'),
    'OP5.GS': ('OP5.RGB', 'OP.EXE 1815:09CB sub_19C4F(OP5.RGB); 1815:09D9 sub_195F2(OP5.GS)'),
    'OP6.GS': ('OP6.RGB', 'OP.EXE 1815:0B17 sub_19443(OP6.GS); 1815:0B33 sub_19CF6(OP6.RGB)'),
    'OP7.GS': ('OP7.RGB', 'OP.EXE 1815:0BF8 sub_19C4F(OP7.RGB); 1815:0C06 sub_196BA(OP7.GS)'),
    'OP8.GS': ('OP8.RGB', 'OP.EXE 1815:014C sub_19443(OP8.GS); 1815:0158 sub_19CF6(OP8.RGB)'),
    'OP9.GS': ('OP9.RGB', '檔名對應；三個 EXE 都沒有 OP9 字串，無已知讀取端'),
    'OP10.GS': ('OP10.RGB', 'OP.EXE 1815:0C60 sub_19443(OP10.GS); 1815:0C6C sub_19CF6(OP10.RGB)'),
    'ROLL.GS': ('ROLL.RGB', 'END.EXE 182B:1B2C sub_1B206(ROLL.RGB); 182B:1B39 sub_19C1D(ROLL.GS)'),
}
_ED_SITES = ['1D10/1D2E', '1D9A/1DB8', '1E0C/1E2A', '1E7E/1E9C', '1EF0/1F0E', '1F62/1F80', '1FD4/1FF2', '2046/2064']
for _i, _s in enumerate(_ED_SITES):
    _a, _b = _s.split('/')
    GS_PAIRS['ED%d.GS' % _i] = ('ED%d.RGB' % _i, 'END.EXE 182B:%s sub_1B206(ED%d.RGB); 182B:%s sub_1ABA9(ED%d.GS)'
                                % (_a, _i, _b, _i))

MAIN_PAL_NAME = 'MAIN.EXE 583A:002A(file 0x4CDCA)'

inventory = []
log = []
counts = {}


def count(fam, key):
    counts.setdefault(fam, {}).setdefault(key, 0)
    counts[fam][key] += 1


def pal17(pal):
    return list(pal) + [(255, 0, 255)]


def trns17():
    return [255] * 16 + [0]


def save(fam, src, idx, w, h, px, pal, palname, fmt, flag, mask=None, note=''):
    """寫 PNG（有遮罩時用 17 色調色盤，索引 16 透明）並登錄清冊。"""
    d = os.path.join(OUT, fam)
    os.makedirs(d, exist_ok=True)
    name = src if idx is None else '%s_%s' % (src, idx if isinstance(idx, str) else '%03d' % idx)
    path = os.path.join(d, name + '.png')
    if mask is not None:
        q = bytearray(px)
        for i, m in enumerate(mask):
            if not m:
                q[i] = TRANSPARENT
        hrimg.write_png(path, w, h, q, pal17(pal), trns17())
        transp = 'index16=transparent'
    else:
        hrimg.write_png(path, w, h, px, pal)
        transp = 'none'
    inventory.append([src, '-' if idx is None else str(idx), str(w), str(h), palname,
                      os.path.relpath(path, '/w'), fmt, '' if flag is None else '0x%02X' % flag, transp, note])
    count(fam, 'png')


def run(fam, label, fn):
    try:
        fn()
    except Exception as e:  # 不吞掉：記錄完整原因並計數
        count(fam, 'error')
        log.append('ERROR %s %s: %s' % (fam, label, ''.join(traceback.format_exception_only(type(e), e)).strip()))
        log.append(traceback.format_exc())


def rgb_palette(name):
    p = os.path.join(ORIG, name)
    data = open(p, 'rb').read()
    return hrimg.palette_from_rgb_file(data)


def main():
    os.makedirs(OUT, exist_ok=True)
    main_exe = open(os.path.join(ORIG, 'MAIN.EXE'), 'rb').read()
    mpal = hrimg.main_palette(main_exe)

    # ---- GS
    for p in sorted(glob.glob(os.path.join(ORIG, '*.GS'))):
        src = os.path.basename(p)

        def do(src=src, p=p):
            d = open(p, 'rb').read()
            out, used, over = hrimg.lzss_decompress(d)
            rgb, ev = GS_PAIRS[src]
            pal = rgb_palette(rgb)
            if used != len(d) or over:
                raise ValueError('LZSS used=%d len=%d over=%d' % (used, len(d), over))
            if src == 'ROLL.GS':
                h = len(out) // 160
                px, _ = hrimg.unpack_rowplanar(out, 0, 320, h, 4, [0, 1, 2, 3])
                save('GS', src, None, 320, h, px, pal, rgb, 'lzss headerless planar p0-p3 (END 182B:1A5D)', None,
                     note=ev)
            else:
                w, h, fl, px, mask, layout = hrimg.decode_unpacked_sprite(out)
                save('GS', src, None, w, h, px, pal, rgb, layout, fl, mask, note=ev)
        run('GS', src, do)

    # ---- PXS
    def do_pxs():
        d = open(os.path.join(ORIG, 'GMAP.PXS'), 'rb').read()
        out, used, over = hrimg.lzss_decompress(d)
        if used != len(d) or over:
            raise ValueError('LZSS used=%d len=%d' % (used, len(d)))
        w, h, fl, px, mask, layout = hrimg.decode_unpacked_sprite(out)
        save('PXS', 'GMAP.PXS', None, w, h, px, mpal, MAIN_PAL_NAME, layout, fl, mask,
             note='MAIN 297D:0012 GMAP.PXS -> 2FB2:25A1 sub_320C1(cmp byte_2FB62,80h)')
    run('PXS', 'GMAP.PXS', do_pxs)

    # ---- MRG
    for p in sorted(glob.glob(os.path.join(ORIG, '*.MRG'))):
        src = os.path.basename(p)
        d = open(p, 'rb').read()
        n, offs, items, tail = hrimg.parse_mrg(d)
        if src == 'ESPMES.MRG':
            count('MRG', 'skipped_text_items')
            log.append('SKIP ESPMES.MRG: 巢狀 MRG 內為 Big5 文字（scripts/probe_misc.py），非圖像')
            continue
        entries = [(i, it, '') for i, it in enumerate(items)]
        if tail:
            entries.append(('tail', tail, '表外資料：位於最後一個偏移之後，24FF:0B38 與 24FF:0A0B 兩條載入路徑都讀不到'))
        for idx, it, note in entries:
            def do(idx=idx, it=it, note=note, src=src):
                if not it:
                    count('MRG', 'empty_item')
                    log.append('EMPTY %s[%s]: 長度 0' % (src, idx))
                    return
                w, h, fl = struct.unpack_from('<HHB', it, 0)
                if w and h and w % 8 == 0 and hrimg.raw_sprite_size(w, h, fl) == len(it):
                    w, h, fl, px, mask, layout = hrimg.decode_raw_sprite(it)
                else:
                    out, used, over = hrimg.lzss_decompress(it)
                    if used != len(it) or over:
                        raise ValueError('LZSS used=%d len=%d over=%d' % (used, len(it), over))
                    w, h, fl, px, mask, layout = hrimg.decode_unpacked_sprite(out)
                save('MRG/' + src, src, idx, w, h, px, mpal, MAIN_PAL_NAME, layout, fl, mask, note=note)
                count('MRG', 'png_' + layout.split()[0])
            run('MRG', '%s[%s]' % (src, idx), do)

    # ---- GRP / BIN（5 bytes 標頭的精靈串接，步幅 = 單格大小）
    for src, fam, palname, pal, ev in (
            ('ARROW.GRP', 'GRP', MAIN_PAL_NAME, mpal, 'MAIN 2404:0097 讀 0x1428 bytes；2404:00F1 imul ax,285h'),
            ('COIN.BIN', 'BIN', 'OP7.RGB', rgb_palette('OP7.RGB'),
             'OP 1A0E:00E3 讀 0x2850 bytes；1A0E:004C imul ax,285h；調色盤：OP 1815:0C35 sub_19C4F(OP7.RGB) 後 1815:0C3D 呼叫')):
        def do(src=src, fam=fam, palname=palname, pal=pal, ev=ev):
            d = open(os.path.join(ORIG, src), 'rb').read()
            off = 0
            i = 0
            while off < len(d):
                w, h, fl = struct.unpack_from('<HHB', d, off)
                size = hrimg.raw_sprite_size(w, h, fl)
                w, h, fl, px, mask, layout = hrimg.decode_raw_sprite(d, off)
                save(fam, src, i, w, h, px, pal, palname, layout, fl, mask, note=ev)
                off += size
                i += 1
            if off != len(d):
                raise ValueError('trailing %d bytes' % (len(d) - off))
        run(fam, src, do)

    # ---- PXZ
    for p in sorted(glob.glob(os.path.join(ORIG, '*.PXZ'))):
        src = os.path.basename(p)

        def do(src=src, p=p):
            d = open(p, 'rb').read()
            w, h, px, cov, info = hrimg.decode_pxz(d)
            if not (info['lzss_consumed_to_eof'] and info['overshoot'] == 0 and info['data_used'] == info['lzss_len']):
                raise ValueError('PXZ check failed %r' % info)
            covered = sum(cov)
            save('PXZ', src, None, w, h, px, mpal, MAIN_PAL_NAME, 'pxz spans + lzss packed4', None, cov,
                 note='MAIN 323A:000A；groups=%d covered_px=%d words=%d' % (info['groups'], covered, info['words']))
        run('PXZ', src, do)

    # ---- PCX
    for src in ('RAIN.PCX', 'H-TXT.PCX'):
        def do(src=src):
            d = open(os.path.join(ORIG, src), 'rb').read()
            w, h, rows, pal, end = hrimg.decode_pcx(d)
            px = b''.join(rows)
            if end != len(d) - 769:
                log.append('NOTE %s: RLE 結束於 %d，調色盤標記於 %d' % (src, end, len(d) - 769))
            save('PCX', src, None, w, h, px, pal, src + ' 檔尾 768 bytes', 'pcx v5 rle 8bpp', None,
                 note='HR.BAT: PSH %s' % src)
        run('PCX', src, do)

    # ---- CFONT.15
    def do_font():
        d = open(os.path.join(ORIG, 'CFONT.15'), 'rb').read()
        n = len(d) // 30
        cols = 157
        rows_ = (n + cols - 1) // cols
        W, H = cols * 16, rows_ * 15
        px = bytearray(W * H)
        for g in range(n):
            gx, gy = (g % cols) * 16, (g // cols) * 15
            for r in range(15):
                v = (d[30 * g + 2 * r] << 8) | d[30 * g + 2 * r + 1]
                for c in range(16):
                    if v & (0x8000 >> c):
                        px[(gy + r) * W + gx + c] = 1
        pal = [(0, 0, 0), (255, 255, 255)]
        save('FONT', 'CFONT.15', 'sheet', W, H, px, pal, 'none(1bpp)', '30 bytes/glyph, 15 rows x u16be', None,
             note='字號順序；每列 157 字；共 %d 字' % n)
        text = '高報酬戰將迪南多傭兵團'
        b5 = text.encode('big5')
        glyphs = [hrimg.cfont_index(b5[i], b5[i + 1]) for i in range(0, len(b5), 2)]
        W2, H2 = 16 * len(glyphs), 15
        px2 = bytearray(W2 * H2)
        for k, g in enumerate(glyphs):
            for r in range(15):
                v = (d[30 * g + 2 * r] << 8) | d[30 * g + 2 * r + 1]
                for c in range(16):
                    if v & (0x8000 >> c):
                        px2[r * W2 + 16 * k + c] = 1
        save('FONT', 'CFONT.15', 'sample', W2, H2, px2, pal, 'none(1bpp)', 'Big5 -> index (OP 1C8F:05A3)', None,
             note='字串 %s；字號 %s' % (text, ','.join(map(str, glyphs))))
    run('FONT', 'CFONT.15', do_font)

    # ---- 輸出清冊與日誌
    with open('/w/inventory.tsv', 'w', encoding='utf-8') as f:
        f.write('src\tindex\twidth\theight\tpalette_source\tpng\tformat\tflag\ttransparency\tnote\n')
        for row in inventory:
            f.write('\t'.join(row) + '\n')
    with open(os.path.join(OUT, 'decode_log.txt'), 'w', encoding='utf-8') as f:
        f.write('decode_all.py 執行結果\n')
        for name in sorted(os.listdir(ORIG)):
            if name.upper().endswith(('.GS', '.RGB', '.MRG', '.PXZ', '.PXS', '.GRP', '.BIN', '.PCX', '.15', '.EXE')):
                h = hashlib.sha256(open(os.path.join(ORIG, name), 'rb').read()).hexdigest()
                f.write('input %s %s\n' % (name, h))
        for fam in sorted(counts):
            f.write('count %s %s\n' % (fam, ' '.join('%s=%d' % kv for kv in sorted(counts[fam].items()))))
        f.write('inventory_rows %d\n' % len(inventory))
        for line in log:
            f.write(line + '\n')
    errors = sum(c.get('error', 0) for c in counts.values())
    print('inventory rows:', len(inventory), 'errors:', errors)
    for fam in sorted(counts):
        print(fam, counts[fam])
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
