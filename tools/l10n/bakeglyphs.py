"""DRAFT L2 developer rasterizer. Produces local OFL glyphs, never CFONT bytes.

Input TSV: unicode (scalar languages), or left_cp/right_cp (English), U+XXXX.
The caller supplies units after source validation and final line wrapping.
This tool does not adopt translations or authorize a production language pack.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import unicodedata

import PIL
from PIL import Image, ImageDraw, ImageFont
import fontTools
from fontTools.ttLib import TTCollection

FONT_SHA = 'b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a'
OFL_SHA = 'f47ac356aaafd53b53c6c784b3d63e265bf2dc9fe452d4ba5aee4b9b0bf51ca8'
FACES = {'zh-CN': (2, 'Noto Sans CJK SC'), 'ja': (0, 'Noto Sans CJK JP'),
         'ko': (1, 'Noto Sans CJK KR'), 'en': (3, 'Noto Sans CJK TC')}
VERSION = 'hr-l2-rasterizer-draft-v1'
FONT_VERSION = 'Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def scalar(value):
    if not re.fullmatch(r'U\+[0-9A-F]{4,6}', value):
        raise ValueError('noncanonical Unicode value: ' + value)
    cp = int(value[2:], 16)
    if cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF or value != f'U+{cp:04X}':
        raise ValueError('invalid Unicode scalar: ' + value)
    char = chr(cp)
    if unicodedata.category(char) in {'Cc', 'Cf', 'Cs', 'Co', 'Cn', 'Mn', 'Mc', 'Me', 'Zl', 'Zp'}:
        raise ValueError('unsupported scalar category: ' + value)
    if char.isspace() and char not in {' ', '\u3000'}:
        raise ValueError('unsupported whitespace: ' + value)
    return cp


def units(path, language):
    text = path.read_bytes().decode('utf-8')
    if '\r' in text or '\ufeff' in text or not text.endswith('\n'):
        raise ValueError('units must be UTF-8 without BOM, LF terminated')
    reader = csv.DictReader(io.StringIO(text), delimiter='\t')
    header = ['left_cp', 'right_cp'] if language == 'en' else ['unicode']
    if reader.fieldnames != header:
        raise ValueError('units header differs: ' + str(reader.fieldnames))
    rows = []
    for row in reader:
        if set(row) != set(header) or any(v is None for v in row.values()):
            raise ValueError('invalid units row')
        unit = tuple(scalar(row[key]) for key in header)
        if language == 'en' and any(chr(cp).isspace() and cp != 0x20 for cp in unit):
            raise ValueError('English pairs only support U+0020 whitespace')
        rows.append(unit)
    if len(set(rows)) != len(rows) or not rows:
        raise ValueError('empty or duplicate unit list')
    return sorted(rows)


def codes(data):
    text = data.decode('utf-8')
    if '\r' in text or '\ufeff' in text or not text.endswith('\n'):
        raise ValueError('reserved list must be canonical UTF-8 LF')
    reader = csv.DictReader(io.StringIO(text), delimiter='\t')
    if reader.fieldnames != ['code_hex', 'sources']:
        raise ValueError('reserved header differs')
    result = []
    for row in reader:
        if set(row) != {'code_hex', 'sources'} or not row['sources'] or not re.fullmatch('[0-9A-F]{4}', row['code_hex']):
            raise ValueError('invalid reserved row')
        code = int(row['code_hex'], 16)
        lead, trail = code >> 8, code & 255
        if not (0xE0 <= lead <= 0xF9 and (0x40 <= trail <= 0x7E or 0xA1 <= trail <= 0xDF)):
            raise ValueError('reserved code outside L2 domain')
        result.append(code)
    if result != sorted(set(result)):
        raise ValueError('reserved codes not unique and ascending')
    return set(result)


def pack(cell, allow_blank=False):
    rows = bytearray()
    for y in range(15):
        word = sum(1 << (15-x) for x in range(15) if cell.getpixel((x, y)) >= 128)
        rows.extend(word.to_bytes(2, 'big'))
    if not any(rows) and not allow_blank:
        raise ValueError('glyph has no thresholded ink')
    return bytes(rows)


def scalar_cell(font, cp):
    char = chr(cp)
    if char in {' ', '\u3000'}:
        return Image.new('L', (15, 15), 0)
    mask = font.getmask(char, mode='L')
    width, height = mask.size
    if width > 15 or height > 15 or not width or not height:
        raise ValueError(f'overlarge/empty mask U+{cp:04X}: {mask.size}')
    cell = Image.new('L', (15, 15), 0)
    cell.paste(Image.frombytes('L', mask.size, bytes(mask)), ((15-width)//2, (15-height)//2))
    return cell


def half_cell(font, cp):
    if cp == 0x20:
        return Image.new('L', (7, 15), 0)
    source = Image.new('L', (12, 15), 0)
    ImageDraw.Draw(source).text((0, 11), chr(cp), fill=255, font=font, anchor='ls')
    box = source.getbbox()
    if box is None:
        raise ValueError(f'empty English source U+{cp:04X}')
    # This reproduces the displayed prototype: left bearing and baseline stay
    # fixed; source drawing clips to the 12x15 canvas before bbox inspection.
    part = source.crop((0, 0, box[2], 15))
    if box[2] > 7:
        part = part.resize((7, 15), Image.Resampling.BILINEAR)
    result = Image.new('L', (7, 15), 0)
    result.paste(part, (0, 0))
    return result


def bake(args):
    if args.output.exists():
        raise ValueError('refusing existing output directory')
    if sha(args.font.read_bytes()) != FONT_SHA or sha(args.ofl.read_bytes()) != OFL_SHA:
        raise ValueError('font or isolated OFL hash differs')
    if PIL.__version__ != '12.3.0' or fontTools.__version__ != '4.66.1':
        raise ValueError('rasterizer dependency versions differ')
    image_id = os.environ.get('HR_IMAGE_ID', '')
    if image_id != 'sha256:f9ea24396753f49d4c215763aa8726755041f0b523f93c9bdbffd76b8e358fca':
        raise ValueError('rasterizer container image differs')
    requested = units(args.units, args.language)
    reserved_data = args.reserved.read_bytes()
    reserved = codes(reserved_data)
    available = [a*256+b for a in range(0xE0, 0xFA) for b in [*range(0x40, 0x7F), *range(0xA1, 0xE0)] if a*256+b not in reserved]
    if len(requested) > len(available):
        raise ValueError('unit set exceeds available code count')
    index, name = FACES[args.language]
    collection = TTCollection(str(args.font), lazy=True)
    face = collection.fonts[index]
    if face['name'].getDebugName(4) != name or face['name'].getDebugName(5) != FONT_VERSION:
        raise ValueError('font face/version differs')
    cmap = face.getBestCmap()
    if any(cp not in cmap for unit in requested for cp in unit):
        raise ValueError('requested scalar missing from font cmap')
    size = 10 if args.language == 'en' else 13
    font = ImageFont.truetype(str(args.font), size, index=index)
    records = bytearray()
    header = 'left_cp\tright_cp\tcode_hex\n' if args.language == 'en' else 'unicode\tcode_hex\n'
    charmap = [header]
    for unit, code in zip(requested, available):
        if args.language == 'en':
            cell = Image.new('L', (15, 15), 0)
            cell.paste(half_cell(font, unit[0]), (0, 0))
            cell.paste(half_cell(font, unit[1]), (8, 0))
            blank = unit == (0x20, 0x20)
        else:
            cell = scalar_cell(font, unit[0])
            blank = unit[0] in {0x20, 0x3000}
        records.extend(code.to_bytes(2, 'big') + pack(cell, blank))
        charmap.append('\t'.join([*(f'U+{cp:04X}' for cp in unit), f'{code:04X}']) + '\n')
    files = {f'glyphs-{args.language}.bin': bytes(records),
             f'charmap-{args.language}.tsv': ''.join(charmap).encode(),
             'reserved-codes.tsv': reserved_data, 'OFL.txt': args.ofl.read_bytes()}
    source = {'format': 'hr-l2-source-v1', 'language': args.language, 'font_file': args.font.name,
              'font_sha256': FONT_SHA, 'font_version': FONT_VERSION, 'face_index': str(index), 'face_name': name,
              'pillow_version': PIL.__version__, 'fonttools_version': fontTools.__version__,
              'pixel_size': str(size), 'cell': '15x15', 'threshold': '128',
              'placement': 'pair2x7-baseline11' if args.language == 'en' else 'mask-center-floor',
              'container_image_id': image_id, 'unit_mode': 'pair2x7' if args.language == 'en' else 'scalar15',
              'rasterizer_version': VERSION, 'rasterizer_sha256': sha(Path(__file__).read_bytes()),
              'units_sha256': sha(args.units.read_bytes()), 'unicode_version': unicodedata.unidata_version,
              'glyphs_sha256': sha(files[f'glyphs-{args.language}.bin']),
              'charmap_sha256': sha(files[f'charmap-{args.language}.tsv']),
              'reserved_sha256': sha(reserved_data), 'ofl_sha256': OFL_SHA}
    if args.language == 'en':
        source.update(source_canvas='12x15', source_anchor='ls', source_origin='0,11',
                      source_clipping='canvas-before-getbbox', source_crop='0,0,bbox-right,15',
                      shrink='width-gt7:BILINEAR:7x15', half_origin='0,0;8,0', blank_column='7',
                      blank_scalar='U+0020')
    files['SOURCE.txt'] = ''.join(k+'\t'+source[k]+'\n' for k in sorted(source)).encode()
    args.output.mkdir()
    try:
        for name, data in files.items():
            (args.output / name).write_bytes(data)
    except BaseException:
        # mkdir above was exclusive. Remove only this invocation's output.
        shutil.rmtree(args.output)
        raise
    lines = b'hr-l2-patch-v1\n' + b''.join((name+'\t'+str(len(files[name]))+'\t'+sha(files[name])+'\n').encode() for name in sorted(files))
    print(json.dumps({'status': 'DRAFT local glyph patch only', 'language': args.language,
                      'units': len(requested), 'patch_sha256': sha(lines),
                      'files': {name: sha(data) for name, data in files.items()}}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=FACES, required=True)
    for name in ['font', 'ofl', 'units', 'reserved', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    bake(parser.parse_args())
