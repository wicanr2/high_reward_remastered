"""包裝：執行 ovr_ida_body.py，例外時把 traceback 寫到 <輸出目錄>/error.txt，最後 qexit。

用法：./ida.sh run MAIN.EXE ovr_ida_all.py /work/out/all /data/overlays.json
說明見 ovr_ida_body.py 的 docstring。成功時輸出目錄有 done.txt，失敗時有 error.txt。
"""
import os
import sys
import traceback

import ida_pro

out = sys.argv[1] if len(sys.argv) > 1 else "/work/out/all"
os.makedirs(out, exist_ok=True)
try:
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ovr_ida_body.py"), encoding="utf-8").read()
    exec(compile(src, "ovr_ida_body.py", "exec"), {"__name__": "__main__"})
except Exception:
    with open(os.path.join(out, "error.txt"), "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
ida_pro.qexit(0)
