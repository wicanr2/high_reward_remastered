"""Local DRAFT patch checks; requires the independently prebaked OFL patch.

No font bytes or original data are stored in this test source.
Run in Docker with HR_PATCH_TESTDIR, HR_RESERVED_TESTFILE, HR_CFONT_TESTFILE.
"""
import os
import tempfile
import unittest
from pathlib import Path
import patchcheck as pc


class PatchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = os.environ.get('HR_PATCH_TESTDIR')
        reserved = os.environ.get('HR_RESERVED_TESTFILE')
        if not directory or not reserved:
            raise unittest.SkipTest('local prebaked patch and trusted reserved measurement required')
        cls.raw = {p.name: p.read_bytes() for p in Path(directory).iterdir()}
        cls.reserved = Path(reserved).read_bytes()

    def check(self, files=None):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            for name, data in (self.raw if files is None else files).items():
                (path / name).write_bytes(data)
            return pc.verify(path, 'en', self.reserved)

    def altered(self, name, fn, rehash=True):
        files = self.raw.copy()
        files[name] = fn(files[name])
        if rehash and name != 'SOURCE.txt':
            key = {'glyphs-en.bin':'glyphs_sha256', 'charmap-en.tsv':'charmap_sha256',
                   'reserved-codes.tsv':'reserved_sha256', 'OFL.txt':'ofl_sha256'}[name]
            source = dict(line.split('\t') for line in files['SOURCE.txt'].decode().splitlines())
            source[key] = pc.digest(files[name])
            files['SOURCE.txt'] = ''.join(k+'\t'+source[k]+'\n' for k in sorted(source)).encode()
        return files

    def reject(self, files, reason):
        with self.assertRaisesRegex(ValueError, reason):
            self.check(files)

    def test_real_patch_and_identity(self):
        patch = self.check()
        self.assertEqual(len(patch['glyphs']), 230)
        self.assertEqual(patch['patch_hash'], 'f604fc1f65098bc19b0f3ca2052e1c78a4f09df62f39fc65f275b0a6120184c8')
        original_file = os.environ.get('HR_CFONT_TESTFILE')
        if not original_file:
            self.skipTest('original CFONT absent')
        original = Path(original_file).read_bytes()
        self.assertIs(pc.apply(patch, original, 0), original)
        changed = pc.apply(patch, original, 1)
        self.assertEqual(pc.digest(changed), '58dc44cfc78876af26068f55f9b5a4eda65d64a9facb5cc2aed406f668498876')
        # Independent offset formula and full read-back, including untouched slots.
        expected = {}
        for value, glyph in patch['glyphs'].items():
            lead, trail = value >> 8, value & 255
            tail = trail - (64 if trail < 127 else 98)
            number = (lead - 164) * 157 + tail + 365
            expected[number] = glyph
        for number in range(13867):
            before = original[number*30:(number+1)*30]
            after = changed[number*30:(number+1)*30]
            self.assertEqual(after, expected.get(number, before))
        with self.assertRaisesRegex(ValueError, 'identity'):
            pc.apply(patch, bytes(len(original)), 1)
        with self.assertRaisesRegex(ValueError, 'adopted'):
            pc.apply(patch, original, -1)

    def test_file_set_and_raw_digests(self):
        files = self.raw.copy(); del files['OFL.txt']
        self.reject(files, 'five files')
        files = self.raw.copy(); files['extra'] = b''
        self.reject(files, 'five files')
        for name in ['glyphs-en.bin', 'charmap-en.tsv', 'OFL.txt']:
            with self.subTest(name=name):
                self.reject(self.altered(name, lambda b: b+b'x', False), 'SOURCE digest')
        self.reject(self.altered('reserved-codes.tsv', lambda b: b.replace(b'F9D8', b'F9D9')), 'trusted')
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            for name, data in self.raw.items():
                (path/name).write_bytes(data)
            altered_trust = self.reserved.replace(b'F9D8', b'F9D9')
            with self.assertRaisesRegex(ValueError, 'measurement version'):
                pc.verify(path, 'en', altered_trust)
        self.reject(self.altered('OFL.txt', lambda b: b+b'x'), 'license')
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            for name, data in self.raw.items():
                (path/name).write_bytes(data)
            (path/'OFL.txt').unlink()
            (path/'OFL.txt').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ValueError, 'regular file'):
                pc.verify(path, 'en', self.reserved)

    def test_structural_record_mutations(self):
        cases = [
            (lambda b: b[:-1], 'truncation'),
            (lambda b: b[32:64]+b[:32]+b[64:], 'code mismatch'),
            (lambda b: b[:32]+b[:32]+b[64:], 'code mismatch'),
            (lambda b: b[:3]+bytes([b[3]|1])+b[4:], 'bit zero'),
            (lambda b: b[:2]+bytes([b[2]|1])+b[3:], 'middle column'),
            (lambda b: b[:2]+bytes([b[2]|128])+b[3:], 'left space'),
        ]
        for fn, reason in cases:
            with self.subTest(reason=reason):
                self.reject(self.altered('glyphs-en.bin', fn), reason)

    def test_map_mutations(self):
        def duplicate_unit(b):
            lines = b.decode().splitlines()
            fields = lines[1].split('\t')[:-1]+[lines[2].split('\t')[-1]]
            lines[2] = '\t'.join(fields)
            return ('\n'.join(lines)+'\n').encode()
        cases = [
            (lambda b: b.replace(b'E040', b'E047', 1), 'allocation'),
            (lambda b: b.replace(b'E040', b'E080', 1), 'domain'),
            (lambda b: b.replace(b'U+0020', b'U+0009', 1), 'unsupported scalar'),
            (lambda b: b.replace(b'U+0020', b'U+0301', 1), 'unsupported scalar'),
            (lambda b: b.replace(b'U+0020', b'U+D800', 1), 'invalid scalar'),
            (lambda b: b.replace(b'U+0020', b'U+000020', 1), 'invalid scalar'),
            (duplicate_unit, 'unit order'),
            (lambda b: b.replace(b'\n', b'\r\n'), 'LF'),
        ]
        for fn, reason in cases:
            with self.subTest(reason=reason):
                self.reject(self.altered('charmap-en.tsv', fn), reason)

    def test_language_whitespace_contract(self):
        self.assertEqual(pc.scalar('U+3000', 'ja'), 0x3000)
        for language in pc.FACES:
            self.assertEqual(pc.scalar('U+0020', language), 0x20)
        with self.assertRaisesRegex(ValueError, 'unsupported scalar'):
            pc.scalar('U+3000', 'en')

    def test_source_mutations_and_hash_binding(self):
        cases = [
            (lambda b: b.replace(b'language\ten\n', b'language\tja\n'), 'parameters'),
            (lambda b: b.replace(b'threshold\t128', b'threshold\t127'), 'parameters'),
            (lambda b: b+b'language\ten\n', 'order'),
            (lambda b: b.replace(b'\n', b'\r\n'), 'LF'),
            (lambda b: b.replace(b'cell\t15x15\n', b''), 'key set'),
        ]
        for fn, reason in cases:
            with self.subTest(reason=reason):
                self.reject(self.altered('SOURCE.txt', fn), reason)
        changed = self.altered('SOURCE.txt', lambda b: b.replace(b'hr-l2-rasterizer-draft-v1', b'hr-l2-rasterizer-draft-v2'))
        self.assertNotEqual(self.check(changed)['patch_hash'], self.check()['patch_hash'])


if __name__ == '__main__':
    unittest.main()
