"""Recover only the ELF/type-2 runtime prefix of one fixed public HR AppImage."""
from pathlib import Path
import hashlib
import json
import mmap
import struct

SOURCE = Path('/src/dist-all/v.1.0.1-20261006/patch/HighReward-v.1.0.1-20261006-x86_64.AppImage')
SOURCE_SHA = '475ac6abe5617a352d82c68862e829805a584f6dce5f905af6f11137b1b8edc9'
RUNTIME_SHA = '1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf'
RUNTIME_BYTES = 944632
OUT = Path('/out/appimage')
U64_NONE = 0xffffffffffffffff
SB_FMT = '<5I6H8Q'
SB_NAMES = ('magic', 'inodes', 'mkfs_time', 'block_size', 'fragments', 'compression',
            'block_log', 'flags', 'no_ids', 'major', 'minor', 'root_inode', 'bytes_used',
            'id_table_start', 'xattr_id_table_start', 'inode_table_start',
            'directory_table_start', 'fragment_table_start', 'lookup_table_start')


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def elf_extent(data):
    if len(data) < 64 or data[:4] != b'\x7fELF' or data[4:7] != b'\x02\x01\x01':
        raise ValueError('source is not ELF64 little-endian version 1')
    if data[8:11] != b'AI\x02':
        raise ValueError('missing AI type-2 marker at ELF offset 8')
    values = struct.unpack_from('<HHIQQQIHHHHHH', data, 16)
    names = ('type', 'machine', 'version', 'entry', 'phoff', 'shoff', 'flags',
             'ehsize', 'phentsize', 'phnum', 'shentsize', 'shnum', 'shstrndx')
    header = dict(zip(names, values))
    if header['type'] not in (2, 3) or header['machine'] != 62 or header['version'] != 1:
        raise ValueError('unsupported ELF type/architecture/version')
    if header['ehsize'] != 64 or header['phentsize'] != 56 or not 1 <= header['phnum'] < 65535:
        raise ValueError('invalid/extended ELF program-header geometry')
    if header['shnum'] == 0 and header['shoff'] != 0:
        raise ValueError('extended ELF section count is unsupported')
    if header['shnum'] and header['shentsize'] != 64:
        raise ValueError('invalid ELF section-header size')
    end = max(64, header['phoff'] + header['phnum'] * 56,
              header['shoff'] + header['shnum'] * header['shentsize'])
    if end > len(data):
        raise ValueError('ELF header table exceeds source')
    segments = []
    for i in range(header['phnum']):
        ph = struct.unpack_from('<IIQQQQQQ', data, header['phoff'] + i * 56)
        if ph[0] == 1 and ph[5] > ph[6]:
            raise ValueError('ELF PT_LOAD filesz exceeds memsz')
        end = max(end, ph[2] + ph[5])
        segments.append({'type': ph[0], 'offset': ph[2], 'file_size': ph[5]})
    for i in range(header['shnum']):
        sh = struct.unpack_from('<IIQQQQIIQQ', data, header['shoff'] + i * 64)
        if sh[1] != 8:  # SHT_NOBITS has no file bytes.
            end = max(end, sh[4] + sh[5])
    if end > len(data):
        raise ValueError('ELF segments/sections exceed source')
    return end, {'header': header, 'extent': end, 'segments': segments}


def superblock(data, offset, minimum):
    if offset < minimum:
        raise ValueError('magic is inside ELF body')
    if offset + 96 > len(data):
        raise ValueError('truncated superblock')
    sb = dict(zip(SB_NAMES, struct.unpack_from(SB_FMT, data, offset)))
    if sb['magic'] != 0x73717368 or (sb['major'], sb['minor']) != (4, 0):
        raise ValueError('not Squashfs 4.0')
    if (sb['compression'], sb['block_size'], sb['block_log']) != (6, 131072, 17):
        raise ValueError('wrong compression/block geometry')
    if not sb['inodes'] or not sb['no_ids'] or sb['flags'] & ~0x0fff:
        raise ValueError('invalid inode/id count or unknown flags')
    used = sb['bytes_used']
    if not 96 <= used <= len(data) - offset:
        raise ValueError('bytes_used exceeds source or header')
    padding = len(data) - offset - used
    if padding >= 4096 or any(data[offset + used:]):
        raise ValueError('trailing bytes are not Squashfs 4K zero padding')
    required = ('inode_table_start', 'directory_table_start', 'id_table_start')
    for name in required:
        if not 96 <= sb[name] < used:
            raise ValueError(f'{name} is outside filesystem')
    if not sb['inode_table_start'] < sb['directory_table_start']:
        raise ValueError('inode/directory metadata order is invalid')
    for name in ('xattr_id_table_start', 'fragment_table_start', 'lookup_table_start'):
        if sb[name] != U64_NONE and not 96 <= sb[name] < used:
            raise ValueError(f'{name} is outside filesystem')
    if sb['fragments'] and sb['fragment_table_start'] == U64_NONE:
        raise ValueError('fragments exist without table')
    if sb['flags'] & (1 << 7) and sb['lookup_table_start'] == U64_NONE:
        raise ValueError('export flag exists without lookup table')
    index_sizes = {'id_table_start': ((sb['no_ids'] * 4 + 8191) // 8192) * 8,
                   'fragment_table_start': ((sb['fragments'] * 16 + 8191) // 8192) * 8,
                   'lookup_table_start': ((sb['inodes'] * 8 + 8191) // 8192) * 8}
    for name, size in index_sizes.items():
        if sb[name] != U64_NONE and sb[name] + size > used:
            raise ValueError(f'{name} index array exceeds bytes_used')
    if sb['root_inode'] & 0xffff >= 8192:
        raise ValueError('root inode offset exceeds metadata block')
    if sb['inode_table_start'] + (sb['root_inode'] >> 16) >= sb['directory_table_start']:
        raise ValueError('root inode block is outside inode metadata')
    return sb


def select_offset(data):
    minimum, elf = elf_extent(data)
    valid, rejected = [], []
    at = 0
    while True:
        at = data.find(b'hsqs', at)
        if at < 0:
            break
        if len(valid) + len(rejected) >= 10000:
            raise ValueError('too many magic candidates')
        try:
            valid.append((at, superblock(data, at, minimum)))
        except ValueError as error:
            rejected.append({'offset': at, 'reason': str(error)})
        at += 1
    if len(valid) != 1:
        raise ValueError(f'expected exactly one validated superblock, found {len(valid)}')
    return valid[0][0], valid[0][1], elf, rejected


def main():
    OUT.mkdir(exist_ok=True)
    build = OUT / 'build'
    build.mkdir(exist_ok=True)
    for folder in (OUT, build):
        if (folder.stat().st_uid, folder.stat().st_gid) != (1000, 1000):
            raise ValueError(f'wrong owner: {folder}')
    path = build / 'runtime'
    if path.is_file():
        if (path.stat().st_uid, path.stat().st_gid) != (1000, 1000):
            raise ValueError('existing fixed runtime has wrong owner')
        if sha_file(path) != RUNTIME_SHA or path.stat().st_size != RUNTIME_BYTES:
            raise ValueError('existing fixed runtime has wrong SHA-256 or length')
        data = path.read_bytes()
        extent, _ = elf_extent(data)
        if extent != len(data):
            raise ValueError('fixed runtime contains bytes after ELF extent')
        result = {'runtime_bytes': len(data), 'runtime_sha256': RUNTIME_SHA,
                  'reused_fixed_runtime': True, 'payload_exported': False,
                  'method': 'verified fixed cached prefix; no source AppImage needed'}
        (OUT / 'runtime-reuse.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        return
    if sha_file(SOURCE) != SOURCE_SHA:
        raise ValueError('source AppImage does not match public release SHA-256')
    with SOURCE.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        offset, sb, elf, rejected = select_offset(data)
        runtime = bytes(data[:offset])
    digest = hashlib.sha256(runtime).hexdigest()
    if digest != RUNTIME_SHA or offset != RUNTIME_BYTES or offset != elf['extent']:
        raise ValueError('recovered prefix does not match fixed runtime or exact ELF extent')
    existing = path.is_file()
    if existing:
        if (path.stat().st_uid, path.stat().st_gid) != (1000, 1000):
            raise ValueError('existing fixed runtime has wrong owner')
        if sha_file(path) != digest or path.stat().st_size != offset:
            raise ValueError('existing fixed runtime differs from public release prefix')
    else:
        path.write_bytes(runtime)
        path.chmod(0o755)
    result = {'source': str(SOURCE), 'source_sha256': SOURCE_SHA, 'source_bytes': SOURCE.stat().st_size,
              'runtime_sha256': digest, 'runtime_bytes': offset, 'reused_fixed_runtime': existing,
              'elf': elf, 'squashfs_superblock': sb, 'rejected_magic_candidates': rejected,
              'payload_exported': False, 'method': 'ELF64/AI2 plus unique validated Squashfs 4.0 Zstandard(6) header; only bytes before superblock exported'}
    (OUT / 'runtime-recovery.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('runtime_bytes', 'runtime_sha256', 'reused_fixed_runtime', 'payload_exported')}))


if __name__ == '__main__':
    main()
