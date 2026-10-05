"""Export candidate Big5 codes from non-code bytes in MAIN FBOV overlay segments.

The JSON contains code values and IDA locations, never original strings or glyphs.
Run against a disposable database with IDA Pro 9.4.
"""
import hashlib
import json
import sys

import ida_auto
import ida_bytes
import ida_pro
import ida_segment
import idautils


EXPECTED = "08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e"
SOURCE = "/work/MAIN.EXE"
OUT = sys.argv[1]

ida_auto.auto_wait()
with open(SOURCE, "rb") as stream:
    source_hash = hashlib.sha256(stream.read()).hexdigest()
if source_hash != EXPECTED:
    raise RuntimeError("MAIN.EXE SHA-256 differs from the project inventory")


def is_lead(value):
    return 0xA1 <= value <= 0xF9


def is_trail(value):
    return 0x40 <= value <= 0x7E or 0xA1 <= value <= 0xFE


def is_custom(code):
    lead, trail = code >> 8, code & 0xFF
    return 0xE0 <= lead <= 0xF9 and (0x40 <= trail <= 0x7E or 0xA1 <= trail <= 0xDF)


codes = {}
segments = []
runs = []
for segment_ea in idautils.Segments():
    segment = ida_segment.getseg(segment_ea)
    name = ida_segment.get_segm_name(segment)
    if not name.startswith("ovr") or ida_segment.get_segm_class(segment) != "OVERLAY":
        continue
    data = ida_bytes.get_bytes(segment.start_ea, segment.end_ea - segment.start_ea)
    if data is None:
        raise RuntimeError("IDA did not provide bytes for " + name)
    # IDA marks instruction operands as tail bytes.  Classify each byte by
    # its containing item's head, or the operands look like unclassified data.
    flags = [ida_bytes.get_full_flags(ida_bytes.get_item_head(segment.start_ea + pos))
             for pos in range(len(data))]
    code_bytes = sum(ida_bytes.is_code(flag) for flag in flags)
    unknown_bytes = sum(ida_bytes.is_unknown(flag) for flag in flags)
    data_bytes = sum(ida_bytes.is_data(flag) for flag in flags)
    candidate_runs = 0
    noncode_runs = 0
    start = 0
    while start < len(data):
        if ida_bytes.is_code(flags[start]):
            start += 1
            continue
        stop = start + 1
        while stop < len(data) and not ida_bytes.is_code(flags[stop]):
            stop += 1
        noncode_runs += 1
        pos = start
        while pos < stop:
            if not (is_lead(data[pos]) and pos + 1 < stop and is_trail(data[pos + 1])):
                pos += 1
                continue
            run_start = pos
            pairs = []
            while pos < stop:
                if is_lead(data[pos]) and pos + 1 < stop and is_trail(data[pos + 1]):
                    pairs.append((pos, data[pos] << 8 | data[pos + 1]))
                    pos += 2
                elif 0x20 <= data[pos] <= 0x7E or data[pos] == 0x0A:
                    pos += 1
                else:
                    break
            if len(pairs) >= 2:
                candidate_runs += 1
                runs.append({
                    "segment": name,
                    "start_offset": "0x%X" % run_start,
                    "start_linear": "0x%X" % (segment.start_ea + run_start),
                    "bytes_hex": data[run_start:pos].hex(),
                    "pairs": ["%04X" % code for _, code in pairs],
                })
                for offset, code in pairs:
                    if not is_custom(code):
                        continue
                    linear = segment.start_ea + offset
                    locator = "%s:%04X@0x%X" % (name, offset, linear)
                    codes.setdefault("%04X" % code, []).append(locator)
            if pos == run_start:
                pos += 1
        start = stop
    segments.append({
        "name": name,
        "selector": "%04X" % segment.sel,
        "start_linear": "0x%X" % segment.start_ea,
        "size": len(data),
        "code_bytes": code_bytes,
        "data_bytes": data_bytes,
        "unknown_bytes": unknown_bytes,
        "noncode_runs": noncode_runs,
        "candidate_runs": candidate_runs,
    })

if len(segments) != 139:
    raise RuntimeError("expected 139 FBOV overlay segments, got %d" % len(segments))
result = {
    "status": "candidate codes from IDA non-code overlay bytes; review before reservation",
    "input": "MAIN.EXE",
    "input_sha256": source_hash,
    "address_space": "IDA 9.4 linear, with overlay segment name and segment-relative offset",
    "method": "contiguous non-code IDA bytes; Big5 aligned runs of at least two pairs; no flat file-offset assumption",
    "segments": segments,
    "runs": runs,
    "codes": {code: sorted(set(locators)) for code, locators in sorted(codes.items())},
}
with open(OUT, "w", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
ida_pro.qexit(0)
