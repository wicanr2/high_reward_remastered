"""《高報酬戰將》圖像容器解碼函式庫（純 Python 標準庫）。

格式依據見 REPORT.md。每個函式只實作反組譯或位元組可直接支持的規則。
"""
import struct
import zlib

# ---------------------------------------------------------------- PNG

def png_bytes(w, h, rows, palette, trns=None, bit_depth=8):
    """rows：每列一個 bytes（每像素一個索引）。palette：[(r,g,b),...]。trns：每個索引的 alpha。"""
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = bytearray()
    for r in rows:
        raw.append(0)
        raw += r
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, bit_depth, 3, 0, 0, 0))
    out += chunk(b'PLTE', b''.join(bytes(c) for c in palette))
    if trns is not None:
        out += chunk(b'tRNS', bytes(trns))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    return out


def write_png(path, w, h, pixels, palette, trns=None):
    rows = [bytes(pixels[y * w:(y + 1) * w]) for y in range(h)]
    with open(path, 'wb') as f:
        f.write(png_bytes(w, h, rows, palette, trns))


def write_png_rgb(path, w, h, rgb):
    """rgb：長度 w*h*3 的 bytes。color type 2。"""
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(out)

# ---------------------------------------------------------------- 調色盤

def dac6_from_nibble(v):
    """OP.EXE 1B56:00DD..00E2：al = (v & 0Fh) * 87h >> 5，寫入 VGA DAC（6 位元）。"""
    return ((v & 0x0F) * 0x87) >> 5


def dac6_to_8(d):
    return (d << 2) | (d >> 4)


def palette_from_rgb_file(data):
    """RGB 檔：16 色 × (R, G, B)，每分量低 4 位元有效（OP.EXE 18F3:0E11..0E44 `and ax, 0Fh`）。"""
    assert len(data) == 48, len(data)
    pal = []
    for i in range(16):
        r, g, b = data[3 * i], data[3 * i + 1], data[3 * i + 2]
        pal.append(tuple(dac6_to_8(dac6_from_nibble(c)) for c in (r, g, b)))
    return pal


# VGA 預設 16 色（模式 12h 開機值，屬性暫存器經 OP.EXE 1815:0D85.. 改成恆等映射後，
# DAC 0..15 的 BIOS 預設值）。只用於沒有已知調色盤來源的預覽，不代表遊戲畫面。
VGA_DEFAULT16 = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xAA), (0x00, 0xAA, 0x00), (0x00, 0xAA, 0xAA),
    (0xAA, 0x00, 0x00), (0xAA, 0x00, 0xAA), (0xAA, 0x55, 0x00), (0xAA, 0xAA, 0xAA),
    (0x55, 0x55, 0x55), (0x55, 0x55, 0xFF), (0x55, 0xFF, 0x55), (0x55, 0xFF, 0xFF),
    (0xFF, 0x55, 0x55), (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0x55), (0xFF, 0xFF, 0xFF),
]

# ---------------------------------------------------------------- LZSS

class LzssError(Exception):
    pass


def lzss_decompress(buf, off=0, check_end=None):
    """OP.EXE 1A75:0D32（sub_1B482，讀檔版）與 END.EXE 1BD0:040C（sub_1C10C，記憶體版）。

    u32 解壓後長度；環狀緩衝 1024 bytes 初值 0，寫入位置起點 0x3BE；
    旗標位元組 LSB 先，1 = 字面值；0 = 兩 bytes 的參照 (b1, b2)：
    位置 = b1 | (b2 & 0xC0) << 2，長度 = (b2 & 0x3F) + 3。
    回傳 (輸出 bytes, 消耗的輸入長度含 4 bytes 長度欄)。
    """
    if off + 4 > len(buf):
        raise LzssError('too short')
    total = struct.unpack_from('<I', buf, off)[0]
    if total > 4 * 1024 * 1024:
        raise LzssError('size %d implausible' % total)
    ring = bytearray(1024)
    r = 0x3BE
    out = bytearray()
    p = off + 4
    flags = 0
    nbits = 0
    remaining = total
    n = len(buf)
    while remaining > 0:
        if nbits == 0:
            if p >= n:
                raise LzssError('eof in flags at out=%d/%d' % (len(out), total))
            flags = buf[p]; p += 1
            nbits = 8
        bit = flags & 1
        flags >>= 1
        nbits -= 1
        if bit:
            if p >= n:
                raise LzssError('eof in literal')
            c = buf[p]; p += 1
            ring[r] = c; r = (r + 1) & 0x3FF
            out.append(c)
            remaining -= 1
        else:
            if p + 1 >= n:
                raise LzssError('eof in match at out=%d/%d' % (len(out), total))
            b1 = buf[p]; b2 = buf[p + 1]; p += 2
            pos = b1 | ((b2 & 0xC0) << 2)
            ln = (b2 & 0x3F) + 3
            remaining -= ln
            for _ in range(ln):
                c = ring[pos]; pos = (pos + 1) & 0x3FF
                ring[r] = c; r = (r + 1) & 0x3FF
                out.append(c)
    return bytes(out[:total]), p - off, len(out) - total

# ---------------------------------------------------------------- 點陣

def unpack_packed4(data, off, w, h):
    """旗標 0x80：每 byte 兩像素、高 4 位元在左（OP.EXE 1A4C:0040..00C0 的位元搬移）。"""
    bpr = w // 2
    px = bytearray(w * h)
    for y in range(h):
        row = data[off + y * bpr: off + (y + 1) * bpr]
        o = y * w
        for i, b in enumerate(row):
            px[o + 2 * i] = b >> 4
            px[o + 2 * i + 1] = b & 0x0F
    return px


def palette_from_words(data, off):
    """16 個 u16，格式 0x0RGB（MAIN.EXE 29C4:00E3..0101：[si+1]&0Fh 為 R，[si]>>4 為 G，[si]&0Fh 為 B）。"""
    pal = []
    for i in range(16):
        w = struct.unpack_from('<H', data, off + 2 * i)[0]
        r, g, b = (w >> 8) & 0x0F, (w >> 4) & 0x0F, w & 0x0F
        pal.append(tuple(dac6_to_8(dac6_from_nibble(c)) for c in (r, g, b)))
    return pal


def mz_file_offset(exe, linear):
    """IDA 線性位址（載入基底段 0x1000）轉檔案位移：線性 - 0x10000 + 標頭段落數 × 16。"""
    hdr = struct.unpack_from('<H', exe, 8)[0] * 16
    return linear - 0x10000 + hdr


def main_palette(main_exe):
    """MAIN.EXE 583A:002A（線性 0x583CA）的 16 色表。全部 12 個參照都是 push（讀）。"""
    return palette_from_words(main_exe, mz_file_offset(main_exe, 0x583CA))

# ---------------------------------------------------------------- 容器

def parse_mrg(d):
    """u16 N；N-1 個 u32 偏移；項目 i = [off[i], off[i+1])，共 N-2 項（MAIN.EXE 24FF:0B90、24FF:0C47）。
    最後一個偏移之後若還有資料，以 tail 回傳（主要載入器不讀）。"""
    n = struct.unpack_from('<H', d, 0)[0]
    offs = list(struct.unpack_from('<%dI' % (n - 1), d, 2))
    assert offs[0] == 2 + 4 * (n - 1)
    items = [d[offs[i]:offs[i + 1]] for i in range(n - 2)]
    return n, offs, items, d[offs[-1]:]


def raw_sprite_size(w, h, flag):
    return 5 + (w // 8) * h * (5 if flag & 1 else 4)


def decode_raw_sprite(b, off=0):
    """未壓縮精靈（MAIN.EXE 2B47:0022 sub_2B492）：u16 w、u16 h、u8 flag；
    flag bit0 = 0：每列 平面0..3；bit0 = 1：每列 平面0..3 + 遮罩（2B47:02A5 先跳過 4 個平面讀遮罩）。"""
    w, h, fl = struct.unpack_from('<HHB', b, off)
    if fl & 1:
        px, mask = unpack_rowplanar(b, off + 5, w, h, 5, [0, 1, 2, 3, 'mask'])
        layout = 'raw planar p0-p3+mask'
    else:
        px, mask = unpack_rowplanar(b, off + 5, w, h, 4, [0, 1, 2, 3])
        layout = 'raw planar p0-p3'
    return w, h, fl, px, mask, layout


def decode_unpacked_sprite(out):
    """LZSS 解壓後的精靈：flag 0x80 = packed 4bpp（OP 1A4C:0011、MAIN 348F:0005、MAIN 2FB2:25A1）；
    flag 0 = 每列 平面0..3（MAIN 2E92:0414）；其他 = 每列 遮罩 + 平面0..3（MAIN 2E92:066A）。"""
    w, h, fl = struct.unpack_from('<HHB', out, 0)
    if fl == 0x80:
        if 5 + w * h // 2 != len(out):
            raise ValueError('packed size mismatch')
        return w, h, fl, unpack_packed4(out, 5, w, h), None, 'lzss packed4'
    np_ = 4 if fl == 0 else 5
    if 5 + (w // 8) * h * np_ != len(out):
        raise ValueError('planar size mismatch')
    if fl == 0:
        px, mask = unpack_rowplanar(out, 5, w, h, 4, [0, 1, 2, 3])
        return w, h, fl, px, None, 'lzss planar p0-p3'
    px, mask = unpack_rowplanar(out, 5, w, h, 5, ['mask', 0, 1, 2, 3])
    return w, h, fl, px, mask, 'lzss planar mask+p0-p3'


def decode_pxz(d):
    """PXZ（MAIN.EXE 323A:000A sub_323AA）：u32 A、A bytes 的 u16 span 表、u32 解壓長度、LZSS。
    span：di += s + 2（di >= 32000 結束），之後 (c >> 1) + 1 組，每組 8 bytes packed = 16 像素。"""
    a = struct.unpack_from('<I', d, 0)[0]
    words = struct.unpack_from('<%dH' % (a // 2), d, 4)
    out, used, over = lzss_decompress(d, 4 + a)
    W, H = 640, 400
    px = bytearray(W * H)
    cov = bytearray(W * H)
    di = 0
    i = 0
    p = 0
    groups = 0
    while True:
        di += words[i] + 2
        if di >= 0x7D00:
            break
        g = (words[i + 1] >> 1) + 1
        i += 2
        for _ in range(g):
            base = di * 8
            for k in range(8):
                b = out[p + k]
                for j, v in ((2 * k, b >> 4), (2 * k + 1, b & 0x0F)):
                    lin = base + j
                    if lin < W * H:
                        px[lin] = v
                        cov[lin] = 1
            p += 8
            di += 2
            groups += 1
    info = dict(table_bytes=a, words=len(words), words_used=i + 1, groups=groups,
                lzss_len=len(out), lzss_consumed_to_eof=(4 + a + used == len(d)), overshoot=over,
                data_used=p)
    return W, H, px, cov, info


def decode_pcx(d):
    """標準 PCX：此遊戲兩檔皆 ver 5、RLE、8 bpp、1 plane，調色盤在檔尾 0x0C 之後 768 bytes。"""
    bpp, planes = d[3], d[65]
    xmin, ymin, xmax, ymax = struct.unpack_from('<4H', d, 4)
    bpl = struct.unpack_from('<H', d, 66)[0]
    if not (bpp == 8 and planes == 1 and d[-769] == 0x0C):
        raise ValueError('unsupported PCX variant')
    w, h = xmax - xmin + 1, ymax - ymin + 1
    p = 128
    rows = []
    for y in range(h):
        row = bytearray()
        while len(row) < bpl:
            c = d[p]; p += 1
            if c >= 0xC0:
                n = c & 0x3F
                v = d[p]; p += 1
                row += bytes([v]) * n
            else:
                row.append(c)
        rows.append(bytes(row[:w]))
    pal = [tuple(d[len(d) - 768 + 3 * i: len(d) - 768 + 3 * i + 3]) for i in range(256)]
    return w, h, rows, pal, p


def cfont_index(lead, trail):
    """OP.EXE 1C8F:05A3（sub_1CE93）與 1C8F:065C..06F7：Big5 → CFONT.15 字號。檔案位移 = 字號 × 30。"""
    t = trail - 0x40 if trail <= 0x7E else trail - 0x62
    if lead <= 0xA3:
        return (lead - 0xA1) * 157 + t
    if (lead == 0xC6 and trail >= 0xA1) or (0xC6 < lead <= 0xC8):
        return (lead - 0xC6) * 157 + t - 0x3F + 0x198
    return (lead - 0xA4) * 157 + t - (0x198 if lead >= 0xC9 else 0) + 0x305


def unpack_rowplanar(data, off, w, h, nplanes, plane_bits):
    """逐列平面：每列依序 nplanes 個平面，每平面 w/8 bytes，MSB 在左。
    plane_bits[k] = 第 k 個平面對應的像素位元（或 'mask'）。回傳 (像素, 遮罩或 None)。"""
    bpp = w // 8
    px = bytearray(w * h)
    mask = bytearray(w * h) if 'mask' in plane_bits else None
    stride = bpp * nplanes
    for y in range(h):
        base = off + y * stride
        for k in range(nplanes):
            pb = plane_bits[k]
            seg = data[base + k * bpp: base + (k + 1) * bpp]
            for xb, b in enumerate(seg):
                if not b:
                    continue
                for bit in range(8):
                    if b & (0x80 >> bit):
                        i = y * w + xb * 8 + bit
                        if pb == 'mask':
                            mask[i] = 1
                        else:
                            px[i] |= 1 << pb
    return px, mask
