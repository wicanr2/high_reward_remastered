"""列出資料庫內所有長度不少於 N 的可印 ASCII 字串（位址、長度、字串）。

用法（經 tools/ida.sh）：ida_music_allstrings.py <輸出檔> [最短長度，預設 4]
直接掃各段原始位元組，不依賴 IDA 的字串清單。只讀，不改資料庫。
輸出為分析工作區內的檔案，內容含原版檔案的字串，不得複製進 docs/ 或 tools/。
"""
import sys

import ida_auto
import ida_bytes
import ida_pro
import ida_segment
import idautils

ida_auto.auto_wait()
out = open(sys.argv[1], "w", encoding="utf-8")
minlen = int(sys.argv[2]) if len(sys.argv) > 2 else 4
PRINT = set(range(0x20, 0x7F))
for sea in idautils.Segments():
    seg = ida_segment.getseg(sea)
    data = ida_bytes.get_bytes(sea, seg.end_ea - sea) or b""
    i = 0
    n = len(data)
    while i < n:
        if data[i] in PRINT:
            j = i
            while j < n and data[j] in PRINT:
                j += 1
            if j - i >= minlen:
                out.write("%04X:%04X %3d %r\n" % (seg.sel, i, j - i, data[i:j].decode("latin1")))
            i = j
        else:
            i += 1
out.write("== done\n")
out.close()
ida_pro.qexit(0)
