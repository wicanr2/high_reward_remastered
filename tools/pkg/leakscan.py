"""可散布的包不得夾帶原版檔：依 docs/re/source-inventory.tsv 的檔名與 SHA-256 掃描目錄。

用法：python3 leakscan.py <清冊 tsv> <要掃的目錄>   有命中就回傳 1。
主判準是原版目錄裡實際有哪些檔名與雜湊。另加音訊的衍生物判準（docs/spec/007 第 8 節）：
發行包不含任何音訊檔，所以下列任一項都算洩漏，即使它是原版檔經過轉檔、雜湊已經不同：
  - 副檔名是 .wav .mid .midi .pcm .ogg .mp3 .flac .opus；
  - 檔頭是 RIFF…WAVE 或 MThd（改了副檔名也抓得到）；
  - 去掉副檔名後與清冊裡某個 .MID 或 .PCM 檔同名（例如 SCOUT.wav、sound_e.dat 這類轉出檔的命名）。
"""
import hashlib
import os
import sys

AUDIO_EXT = {".wav", ".mid", ".midi", ".pcm", ".ogg", ".mp3", ".flac", ".opus"}

inv, root = sys.argv[1], sys.argv[2]
names, hashes, audio_stems = set(), set(), set()
with open(inv, encoding="utf-8") as f:
    next(f)
    for ln in f:
        c = ln.rstrip("\n").split("\t")
        if len(c) >= 3:
            names.add(c[0].upper())
            if c[0].upper().endswith((".MID", ".PCM")):
                audio_stems.add(os.path.splitext(c[0])[0].upper())
            if c[1] != "0":
                hashes.add(c[2])
hit = []
# 譯文表與語言包的路徑不得出現在發行包內（docs/spec/008 第 3.9 節第 6 項；語言包含原版位元組，譯文表是衍生著作）。
L10N_DIRS = {"l10n", "l10n-packs"}
for r, dirs, files in os.walk(root):
    for d in dirs:
        if d.lower() in L10N_DIRS:
            hit.append(("譯文表或語言包路徑", os.path.join(r, d)))
    for n in files:
        p = os.path.join(r, n)
        if n.upper() in names:
            hit.append(("檔名", p))
        data = open(p, "rb").read()
        if hashlib.sha256(data).hexdigest() in hashes:
            hit.append(("雜湊", p))
        stem, ext = os.path.splitext(n)
        if ext.lower() in AUDIO_EXT:
            hit.append(("音訊副檔名", p))
        if data[:4] == b"MThd" or (data[:4] == b"RIFF" and data[8:12] == b"WAVE"):
            hit.append(("音訊檔頭", p))
        if stem.upper() in audio_stems and ext.lower() != ".exe":
            hit.append(("與原版音訊同名", p))
for kind, p in hit:
    print("洩漏", kind, p)
print("掃描完成，命中", len(hit))
sys.exit(1 if hit else 0)
