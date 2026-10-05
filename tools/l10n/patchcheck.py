"""DRAFT five-file patch verifier. Does not create packs or modify CFONT files.

Evidence/contract: docs/re/032 and docs/spec/008 section 3.4.
The caller supplies the independently measured reserved file; a patch cannot
authorize its own reserved set. A successful check proves structure, not art.
"""
import argparse
import hashlib
import json
import re
import stat
import unicodedata
from pathlib import Path

FONT_SHA = 'b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a'
OFL_SHA = 'f47ac356aaafd53b53c6c784b3d63e265bf2dc9fe452d4ba5aee4b9b0bf51ca8'
CFONT_SHA = '60e55cf73ba2eb8e83018e8a9b585e22524e730e240732adb5e746b7ed54d8db'
RESERVED_SHA = '1c841eb8a768ec79051090f39371abc582da8c30a8f2811b26a3089ee015a1fe'
FACES = {'zh-CN': (2, 'SC'), 'ja': (0, 'JP'), 'ko': (1, 'KR'), 'en': (3, 'TC')}
PAIR = dict(source_canvas='12x15', source_anchor='ls', source_origin='0,11',
            source_clipping='canvas-before-getbbox', source_crop='0,0,bbox-right,15',
            shrink='width-gt7:BILINEAR:7x15', half_origin='0,0;8,0',
            blank_column='7', blank_scalar='U+0020')
BASE_KEYS = set('format language units_sha256 unicode_version font_file font_sha256 '
                'font_version face_index face_name pillow_version fonttools_version '
                'pixel_size cell threshold placement container_image_id unit_mode '
                'rasterizer_version rasterizer_sha256 glyphs_sha256 charmap_sha256 '
                'reserved_sha256 ofl_sha256'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path, limit):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_size <= limit,
            'not a bounded regular file: ' + path.name)
    data = path.read_bytes()
    require(len(data) <= limit, 'file grew beyond limit: ' + path.name)
    return data


def lines(data):
    text = data.decode('utf-8', errors='strict')
    require(not text.startswith('\ufeff') and '\r' not in text and
            '\x00' not in text and text.endswith('\n'), 'requires UTF-8 without BOM, LF terminal')
    return text[:-1].split('\n')


def code(text):
    require(re.fullmatch('[0-9A-F]{4}', text), 'noncanonical code')
    value = int(text, 16)
    lead, trail = value >> 8, value & 255
    require(0xE0 <= lead <= 0xF9 and (0x40 <= trail <= 0x7E or 0xA1 <= trail <= 0xDF),
            'code outside domain')
    return value


def scalar(text, language='en'):
    require(re.fullmatch(r'U\+[0-9A-F]{4,6}', text), 'noncanonical scalar')
    value = int(text[2:], 16)
    require(value <= 0x10FFFF and not 0xD800 <= value <= 0xDFFF and
            text == f'U+{value:04X}', 'invalid scalar')
    ch = chr(value)
    spaces = {' '} if language == 'en' else {' ', '\u3000'}
    require(not unicodedata.category(ch).startswith(('C', 'M')) and
            (not ch.isspace() or ch in spaces), 'unsupported scalar')
    return value


def index(value):
    lead, trail = value >> 8, value & 255
    tail = trail - (0x40 if trail <= 0x7E else 0x62)
    number = (lead - 0xA4) * 157 + tail - 0x198 + 0x305
    require(0 <= number < 13867 and number * 30 + 30 <= 416010, 'glyph index outside CFONT')
    return number


def verify(directory, language, trusted_reserved):
    require(language in FACES, 'unknown language')
    names = {f'glyphs-{language}.bin', f'charmap-{language}.tsv',
             'reserved-codes.tsv', 'OFL.txt', 'SOURCE.txt'}
    require({p.name for p in directory.iterdir()} == names, 'patch must contain exactly five files')
    files = {name: read_regular(directory / name, 2 * 1024 * 1024) for name in names}
    require(digest(trusted_reserved) == RESERVED_SHA, 'trusted measurement version mismatch')
    require(files['reserved-codes.tsv'] == trusted_reserved, 'reserved set differs from trusted measurement')
    rlines = lines(trusted_reserved)
    require(rlines[0] == 'code_hex\tsources', 'reserved header')
    reserved = []
    for line in rlines[1:]:
        fields = line.split('\t')
        require(len(fields) == 2 and fields[1], 'reserved row')
        reserved.append(code(fields[0]))
    require(reserved == sorted(set(reserved)), 'reserved order or duplicates')
    slines = lines(files['SOURCE.txt'])
    source = {}
    keys = []
    for line in slines:
        fields = line.split('\t')
        require(len(fields) == 2 and fields[1], 'SOURCE row')
        keys.append(fields[0])
        source[fields[0]] = fields[1]
    require(keys == sorted(set(keys)), 'SOURCE order or duplicates')
    require(set(source) == BASE_KEYS | (set(PAIR) if language == 'en' else set()), 'SOURCE key set')
    face, suffix = FACES[language]
    expected = dict(format='hr-l2-source-v1', language=language, font_file='NotoSansCJK-Regular.ttc',
                    font_sha256=FONT_SHA,
                    font_version='Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603',
                    face_index=str(face), face_name='Noto Sans CJK ' + suffix,
                    pillow_version='12.3.0', fonttools_version='4.66.1', cell='15x15', threshold='128',
                    pixel_size='10' if language == 'en' else '13',
                    placement='pair2x7-baseline11' if language == 'en' else 'mask-center-floor',
                    unit_mode='pair2x7' if language == 'en' else 'scalar15', unicode_version='15.0.0')
    if language == 'en':
        expected.update(PAIR)
    require(all(source[k] == v for k, v in expected.items()), 'unsupported SOURCE parameters')
    require(re.fullmatch('sha256:[0-9a-f]{64}', source['container_image_id']), 'container identity')
    require(re.fullmatch('[A-Za-z0-9._-]+', source['rasterizer_version']), 'rasterizer version')
    for key in ('units_sha256', 'rasterizer_sha256'):
        require(re.fullmatch('[0-9a-f]{64}', source[key]), 'SOURCE hash: ' + key)
    for key, name in [('glyphs_sha256', f'glyphs-{language}.bin'),
                      ('charmap_sha256', f'charmap-{language}.tsv'),
                      ('reserved_sha256', 'reserved-codes.tsv'), ('ofl_sha256', 'OFL.txt')]:
        require(source[key] == digest(files[name]), 'SOURCE digest: ' + name)
    require(digest(files['OFL.txt']) == OFL_SHA, 'OFL differs from recorded font license')
    cmap = lines(files[f'charmap-{language}.tsv'])
    header = 'left_cp\tright_cp\tcode_hex' if language == 'en' else 'unicode\tcode_hex'
    require(cmap[0] == header, 'charmap header')
    units, codes = [], []
    for line in cmap[1:]:
        fields = line.split('\t')
        require(len(fields) == (3 if language == 'en' else 2), 'charmap row')
        units.append(tuple(scalar(v, language) for v in fields[:-1]))
        codes.append(code(fields[-1]))
    require(0 < len(units) <= 3276 and units == sorted(set(units)), 'unit order, duplicates or empty map')
    domain = [lead * 256 + trail for lead in range(0xE0, 0xFA)
              for trail in [*range(0x40, 0x7F), *range(0xA1, 0xE0)]
              if lead * 256 + trail not in reserved]
    require(codes == domain[:len(units)], 'noncanonical allocation or reserved collision')
    binary = files[f'glyphs-{language}.bin']
    require(len(binary) == 32 * len(units), 'glyph record count or truncation')
    glyphs = {}
    indices = set()
    for i, value in enumerate(codes):
        record = binary[i * 32:(i + 1) * 32]
        require(int.from_bytes(record[:2], 'big') == value, 'binary and charmap code mismatch')
        number = index(value)
        require(number not in indices, 'colliding glyph indices')
        indices.add(number)
        glyph = record[2:]
        for row in range(15):
            word = int.from_bytes(glyph[row * 2:row * 2 + 2], 'big')
            require(not word & 1, 'bit zero must be blank')
            require(language != 'en' or not word & 0x100, 'pair middle column must be blank')
            if language == 'en':
                require(units[i][0] != 0x20 or not word & 0xFE00, 'left space must be blank')
                require(units[i][1] != 0x20 or not word & 0x00FE, 'right space must be blank')
            else:
                require(units[i][0] not in (0x20, 0x3000) or word == 0, 'scalar space must be blank')
        glyphs[value] = glyph
    stream = b'hr-l2-patch-v1\n'
    for name in sorted(names, key=lambda s: s.encode()):
        data = files[name]
        stream += f'{name}\t{len(data)}\t{digest(data)}\n'.encode()
    return {'patch_hash': digest(stream), 'language': language, 'glyphs': glyphs,
            'charmap': dict(zip(units, codes)), 'source': source}


def apply(patch, original, adopted):
    require(type(adopted) is int and adopted >= 0, 'invalid adopted count')
    require(len(original) == 416010 and digest(original) == CFONT_SHA, 'original CFONT identity mismatch')
    if adopted == 0:
        return original
    out = bytearray(original)
    for value, glyph in patch['glyphs'].items():
        start = index(value) * 30
        out[start:start + 30] = glyph
    require(len(out) == len(original), 'CFONT size changed')
    return bytes(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('patch', type=Path)
    parser.add_argument('language', choices=FACES)
    parser.add_argument('trusted_reserved', type=Path)
    parser.add_argument('--cfont', type=Path)
    args = parser.parse_args()
    patch = verify(args.patch, args.language, read_regular(args.trusted_reserved, 2 * 1024 * 1024))
    report = {'scope': 'DRAFT research verifier; no language pack', 'patch_hash': patch['patch_hash'],
              'language': args.language, 'glyph_count': len(patch['glyphs'])}
    if args.cfont:
        original = read_regular(args.cfont, 416010)
        report['zero_adopt_cfont_sha256'] = digest(apply(patch, original, 0))
        report['positive_adopt_cfont_sha256'] = digest(apply(patch, original, 1))
    print(json.dumps(report, indent=2, sort_keys=True))
