"""原版壓縮檔清冊：逐檔大小、SHA-256、檔頭 8 bytes，並比對兩份壓縮檔。

只讀 zip 內容，不解壓、不寫原版內容。輸出 TSV 與摘要。
用法（容器內）：python inventory.py <jsdos.zip> <plain.zip> <out.tsv>
"""
import hashlib
import sys
import zipfile


def entries(path):
    out = {}
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            if i.is_dir() or i.filename.startswith(".jsdos/"):
                continue
            data = z.read(i)
            out[i.filename] = (len(data), hashlib.sha256(data).hexdigest(), data[:8].hex())
    return out


def main():
    jsdos_zip, plain_zip, out_tsv = sys.argv[1:4]
    a, b = entries(jsdos_zip), entries(plain_zip)
    names = sorted(set(a) | set(b))
    with open(out_tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("path\tsize\tsha256\tin_jsdos\tin_plain\thead8\n")
        for n in names:
            e = a.get(n) or b.get(n)
            f.write(f"{n}\t{e[0]}\t{e[1]}\t{int(n in a)}\t{int(n in b)}\t{e[2]}\n")
    print("files", len(names), "jsdos", len(a), "plain", len(b))
    print("only_in_jsdos", sorted(set(a) - set(b)))
    print("only_in_plain", sorted(set(b) - set(a)))
    diff = [n for n in set(a) & set(b) if a[n][:2] != b[n][:2]]
    print("same_name_different_content", sorted(diff))
    print("zero_byte", [n for n in names if (a.get(n) or b.get(n))[0] == 0])
    fam = {}
    for n in names:
        ext = n.rsplit(".", 1)[-1].upper() if "." in n else "(none)"
        e = a.get(n) or b.get(n)
        fam.setdefault(ext, []).append((n, e[0], e[2]))
    for ext in sorted(fam):
        heads = sorted({h[:8] for _, s, h in fam[ext] if s})
        print(f"{ext:8} n={len(fam[ext]):3} head4_set={heads[:6]}")


main()
