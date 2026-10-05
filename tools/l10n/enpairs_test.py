"""Meaningful DRAFT gates: source rejection, segment padding, fixed-code reuse."""
import unittest

from enpairs import PairError, metrics, prepare


class EnglishPairs(unittest.TestCase):
    def test_odd_segments_do_not_pair_across_format_spec(self):
        book = {(ord('A'), 0x20): 0xE040, (ord('B'), 0x20): 0xE041}
        result = prepare('A%sB', ['%s'], book, 30, 30, 4)
        self.assertEqual(result['encoded'], b'\xe0\x40%s\xe0\x41')
        self.assertEqual(result['line_metrics'], [(6, 24)])
        self.assertEqual(metrics('ABC%03dDEF'), (12, 14))
        self.assertEqual(metrics('A%10ldB'), (9, 15))

    def test_reordering_reuses_fixed_codes(self):
        book = {(ord('A'), ord('B')): 0xE050, (ord('C'), ord('D')): 0xE0A1}
        a = prepare('AB CD', [], book, 4, 4, 2)
        b = prepare('CD AB', [], book, 4, 4, 2)
        self.assertEqual(a['encoded'], b'\xe0\x50\n\xe0\xa1')
        self.assertEqual(b['encoded'], b'\xe0\xa1\n\xe0\x50')
        self.assertEqual(a['required_pairs'], b['required_pairs'])
        with self.assertRaisesRegex(PairError, 'missing-pair rebuild-glyph-patch'):
            prepare('EF', [], book, 4, 4, 2)

    def test_source_is_checked_before_encoding(self):
        for text in ['A\tB', 'A\rB', 'A\0B', 'A\u0301', 'A\u200dB', '\ud800', 'A\u3000B']:
            with self.subTest(text=repr(text)), self.assertRaises(PairError):
                prepare(text, [], {}, 30, 30, 4)
        for text in ['%%', '%*d', '% d', '%ls', '%f', '%1.d', '%']:
            with self.subTest(text=text), self.assertRaisesRegex(PairError, 'placeholder'):
                prepare(text, [], {}, 30, 30, 4)
        with self.assertRaisesRegex(PairError, 'placeholder count/order/text'):
            prepare('%d%s', ['%s', '%d'], {}, 30, 30, 4)

    def test_expansion_rows_and_length_remain_bounded(self):
        result = prepare('%s%s', ['%s', '%s'], {}, 30, 40, 2)
        self.assertEqual(result['encoded'], b'%s%s')
        self.assertEqual(result['line_metrics'], [(4, 40)])
        self.assertEqual(result['rendered_rows'], 2)
        with self.assertRaisesRegex(PairError, 'rows'):
            prepare('%s%s', ['%s', '%s'], {}, 30, 40, 1)
        with self.assertRaisesRegex(PairError, 'no-word-boundary-solution'):
            prepare('ABCDEFG', [], {}, 4, 4, 4)
        with self.assertRaisesRegex(PairError, 'length'):
            prepare('AB '*180, [], {}, 70, 70, 20)

    def test_explicit_empty_lines_and_interior_spaces_are_preserved(self):
        result = prepare('AB\n', [], {(65, 66): 0xE050}, 30, 30, 4)
        self.assertEqual(result['encoded'], b'\xe0\x50\n')
        self.assertEqual(result['rendered_rows'], 2)
        book = {(65, 66): 0xE050, (0x20, 0x20): 0xE051, (67, 68): 0xE052}
        result = prepare('AB  CD', [], book, 30, 30, 4)
        self.assertEqual(result['encoded'], b'\xe0\x50\xe0\x51\xe0\x52')


if __name__ == '__main__':
    unittest.main()
