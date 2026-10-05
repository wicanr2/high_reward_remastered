"""DRAFT English source/wrap/subset model. Research only; no pack output.

Call prepare(text, original_specs, codebook, width, expanded_limit, max_rows).
width/expanded_limit/max_rows are the L1 budget's item-dependent values.
It never allocates glyph codes or falls back to the original translation.
"""
from functools import lru_cache
import math
import re
import unicodedata

SPEC = re.compile(r'%[-+#0]*([0-9]*)(?:\.([0-9]+))?(l?)([sd])')


class PairError(ValueError):
    pass


def tokens(text):
    result = []
    offset = 0
    while offset < len(text):
        char = text[offset]
        if char == '%':
            match = SPEC.match(text, offset)
            if not match or match[3] and match[4] != 'd':
                raise PairError(f'placeholder offset={offset}')
            raw = match[0]
            width = min(int(match[1] or '0'), 1 << 20)
            precision = min(int(match[2] or '0'), 1 << 20)
            bound = 20 if match[4] == 's' else 11 if match[3] else 6
            result.append(('spec', raw, max(bound, width, precision)))
            offset += len(raw)
            continue
        cp = ord(char)
        if char != '\n':
            if unicodedata.category(char) in {'Cc', 'Cf', 'Cs', 'Co', 'Cn', 'Mn', 'Mc', 'Me', 'Zl', 'Zp'}:
                raise PairError(f'unsupported-scalar offset={offset} U+{cp:04X}')
            if char.isspace() and char != ' ':
                raise PairError(f'unsupported-space offset={offset} U+{cp:04X}')
        result.append(('newline' if char == '\n' else 'char', char, 0))
        offset += 1
    return result


def segments(text):
    """Ordinary text segments end at every complete format specification."""
    plain = []
    result = []
    for kind, value, expansion in tokens(text):
        if kind == 'char':
            plain.append(value)
            continue
        if kind == 'newline':
            raise PairError('internal newline in line segment')
        if plain:
            result.append(('plain', ''.join(plain), 0))
            plain = []
        result.append((kind, value, expansion))
    if plain:
        result.append(('plain', ''.join(plain), 0))
    return result


def metrics(text):
    literal = expanded = 0
    for kind, value, expansion in segments(text):
        n = 2 * ((len(value)+1)//2) if kind == 'plain' else len(value)
        literal += n
        expanded += n if kind == 'plain' else expansion
    return literal, expanded


def pairs(text):
    result = []
    for kind, value, _ in segments(text):
        if kind == 'plain':
            result.extend((ord(value[i]), ord(value[i+1]) if i+1 < len(value) else 0x20)
                          for i in range(0, len(value), 2))
    return result


def wrap_line(text, width, expanded_limit):
    if not text:
        return ['']
    # Spaces inside specifications are rejected by tokens before this point.
    breaks = [i for i, c in enumerate(text) if c == ' ']
    ends = [*breaks, len(text)]

    @lru_cache(None)
    def solve(start):
        best = None
        for end in reversed(ends):
            if end < start or end == start and end != len(text):
                continue
            line = text[start:end]
            lit, exp = metrics(line)
            if lit > width or exp > expanded_limit:
                continue
            row_count = max(1, math.ceil(exp/width))
            if end == len(text):
                solution = ([line], row_count, lit, exp)
            else:
                tail = solve(end+1)
                if tail is None:
                    continue
                solution = ([line, *tail[0]], row_count+tail[1], lit+1+tail[2], exp+1+tail[3])
            # Prefer fewer rendered rows, fewer inserted line breaks, then
            # fewer bytes. Reversed candidate order fixes ties to longer lines.
            score = (solution[1], len(solution[0]), solution[2])
            if best is None or score < best[0]:
                best = (score, solution)
        return None if best is None else best[1]

    result = solve(0)
    if result is None:
        raise PairError('line-width no-word-boundary-solution')
    return result[0]


def prepare(text, original_specs, codebook, width, expanded_limit, max_rows):
    if len(text) > 4096:
        raise PairError('source-too-long for research model')
    if not isinstance(width, int) or width <= 0 or expanded_limit < width or max_rows <= 0:
        raise PairError('invalid item-dependent budget')
    source_tokens = tokens(text)
    if [value for kind, value, _ in source_tokens if kind == 'spec'] != list(original_specs):
        raise PairError('placeholder count/order/text differs')
    for unit, code in codebook.items():
        if len(unit) != 2 or any(not isinstance(cp, int) for cp in unit) or not isinstance(code, int):
            raise PairError('invalid fixed codebook')
        lead, trail = code >> 8, code & 255
        if not (0xE0 <= lead <= 0xF9 and (0x40 <= trail <= 0x7E or 0xA1 <= trail <= 0xDF)):
            raise PairError('codebook outside L2 domain')
    if len(set(codebook.values())) != len(codebook):
        raise PairError('duplicate fixed code')
    lines = [line for explicit in text.split('\n') for line in wrap_line(explicit, width, expanded_limit)]
    measures = [metrics(line) for line in lines]
    rendered = sum(max(1, math.ceil(exp/width)) for _, exp in measures)
    literal = sum(lit for lit, _ in measures) + len(lines)-1
    expanded = sum(exp for _, exp in measures) + len(lines)-1
    if rendered > max_rows:
        raise PairError(f'rows actual={rendered} limit={max_rows}')
    if literal > 511 or expanded > 511:
        raise PairError(f'length raw={literal} expanded={expanded}')
    required = {unit for line in lines for unit in pairs(line)}
    missing = sorted(required - set(codebook))
    if missing:
        detail = ','.join(f'U+{a:04X}+U+{b:04X}' for a, b in missing)
        raise PairError('missing-pair rebuild-glyph-patch: ' + detail)
    result = bytearray()
    for i, line in enumerate(lines):
        if i:
            result.append(0x0A)
        for kind, value, _ in segments(line):
            if kind == 'spec':
                result.extend(value.encode('ascii'))
            else:
                for offset in range(0, len(value), 2):
                    unit = (ord(value[offset]), ord(value[offset+1]) if offset+1 < len(value) else 0x20)
                    result.extend(codebook[unit].to_bytes(2, 'big'))
    assert len(result) == literal
    return {'lines': lines, 'encoded': bytes(result), 'required_pairs': required,
            'line_metrics': measures, 'rendered_rows': rendered}
