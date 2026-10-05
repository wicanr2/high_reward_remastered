"""Disposable L2 E0/A4 probe roots from earlier T0/T3a experiments."""
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path("/out/re-text2/roots")
START = 0x3D7A
SECOND = 0x3D90
receipt = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def create(name, source, offset, before, after):
    assert len(before) == len(after)
    dst = ROOT / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(ROOT / source, dst)
    path = dst / "ESPMES.MRG"
    blob = bytearray(path.read_bytes())
    assert blob[offset:offset + len(before)] == before, name
    source_hash = sha(blob)
    blob[offset:offset + len(after)] = after
    path.write_bytes(blob)
    receipt[name] = {
        "source": source, "source_sha256": source_hash,
        "output_sha256": sha(blob), "offset": hex(offset),
        "old_hex": before.hex(), "new_hex": after.hex(),
    }


# The first dialogue field has 22 bytes including its NUL. Use the existing
# A4 T1 as the negative control. The E0 path tests a P-class trailing E0.
t0 = (ROOT / "t0" / "ESPMES.MRG").read_bytes()
first_before = bytes.fromhex("a440a441a47e0aa442a443a444a445a446a447a44800")
assert t0[START:START + 22] == first_before
first_e0 = bytes.fromhex("e040e041e0e00ae042e043e044e045e046e047e04800")
create("l2-tail-e0", "t0", START, first_before, first_e0)

# The second dialogue field has 29 two-byte glyphs plus NUL. The 16th starts
# at si=30. E0 is P-class; A4 is the earlier S-class negative control.
t3 = (ROOT / "t3a" / "ESPMES.MRG").read_bytes()
second_before = t3[SECOND:SECOND + 59]
assert second_before == b"".join(bytes((0xA4, n)) for n in range(0x40, 0x5D)) + b"\x00"
second_e0 = b"".join(bytes((0xE0, n)) for n in range(0x40, 0x5D)) + b"\x00"
create("l2-boundary-e0", "t3a", SECOND, second_before, second_e0)

# One ASCII digit plus fourteen paired glyphs occupies 29 bytes, just short
# of the 31-byte window; then a newline and fourteen more glyphs.
for name, lead in (("l2-digit-a4", 0xA4), ("l2-digit-e0", 0xE0)):
    next_text = (b"1" + b"".join(bytes((lead, n)) for n in range(0x40, 0x4E))
                 + b"\x0a" + b"".join(bytes((lead, n)) for n in range(0x4E, 0x5C))
                 + b"\x00")
    assert len(next_text) == 59
    create(name, "t3a", SECOND, second_before, next_text)

out = pathlib.Path("/out/re-text2/l2-probe-inputs.json")
out.write_text(json.dumps(receipt, indent=2) + "\n")
print(out)
for name, item in receipt.items():
    print(name, item["output_sha256"])
