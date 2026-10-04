// 產生 apps/hr/l10n/data/charmap-zh-TW.tsv（開發側，容器內執行，不進 fork）。
//
// 容器只掛載 workplace（唯讀，容器內 /orig）與 fork（容器內 /src），所以先把本檔複製到 workplace 再執行：
//
//	mkdir -p workplace/gencharmap && cp tools/l10n/gencharmap/main.go workplace/gencharmap/main.go
//	tools/dosgolem.sh go run /orig/gencharmap/main.go
//
// 輸入：/orig/orig（原版，唯讀）、/orig/ida-text/out/str*.tsv（IDA 嚴格掃描輸出，唯讀）。
// 輸出：/src/apps/hr/l10n/data/charmap-zh-TW.tsv、/out/l1-formats/gen-charmap.log（只含數字與碼位）。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"

	"github.com/wicanr2/dosgolem/apps/hr/l10n"
)

var logb bytes.Buffer

func logf(format string, a ...any) {
	s := fmt.Sprintf(format, a...)
	logb.WriteString(s)
	fmt.Print(s)
}

func rd(p string) []byte {
	b, err := os.ReadFile(p)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	return b
}

func sum(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// idaStrings 讀 IDA 的 str*.tsv：big5 欄（第 5 欄）>= minBig5，seg 非空時只取該段，回傳每筆的位元組。
func idaStrings(path, seg string, minBig5 int) [][]byte {
	var out [][]byte
	for _, ln := range strings.Split(strings.TrimSpace(string(rd(path))), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 {
			continue
		}
		if seg != "" && f[0][:4] != seg {
			continue
		}
		bc, _ := strconv.Atoi(f[4])
		if bc < minBig5 {
			continue
		}
		raw, err := hex.DecodeString(f[9])
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		out = append(out, raw)
	}
	return out
}

func isLead(b byte) bool  { return b >= 0xA1 && b <= 0xF9 }
func isTrail(b byte) bool { return (b >= 0x40 && b <= 0x7E) || (b >= 0xA1 && b <= 0xFE) }

// strictStrings 是 tools/ida_text_strings.py 的規則在整個檔案上的實作（參照用，不進套件）。
func strictStrings(d []byte, minBig5 int) [][]byte {
	var out [][]byte
	i, L := 0, len(d)
	for i < L {
		if d[i] == 0 {
			i++
			continue
		}
		j, ok, big5 := i, true, 0
		for j < L && d[j] != 0 {
			c := d[j]
			switch {
			case isLead(c) && j+1 < L && isTrail(d[j+1]):
				big5++
				j += 2
			case c >= 0x20 && c <= 0x7E, c == 0x0A, c == 0x0D, c == 0x09:
				j++
			default:
				ok = false
				j++
			}
		}
		if ok && j < L && big5 >= minBig5 {
			out = append(out, d[i:j])
		}
		i = j + 1
	}
	return out
}

func codesOf(tsv []byte) map[uint16]uint16 { // big5 -> unicode
	m := map[uint16]uint16{}
	for _, ln := range strings.Split(strings.TrimSpace(string(tsv)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		u, _ := strconv.ParseUint(f[0], 16, 32)
		b, _ := strconv.ParseUint(f[1], 16, 16)
		m[uint16(b)] = uint16(u)
	}
	return m
}

func main() {
	if err := os.MkdirAll("/out/l1-formats", 0o755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	names := []string{"COUNTRY.MES", "SP.MES", "SYSTEM.MES", "UWASA.MES", "POWERMES.MES", "ESPMES.MRG", "SHOPTAB.TBL",
		"OP.TXT", "OP0.TXT", "OP1.TXT", "OP2.TXT", "OP3.TXT", "OP4.TXT", "OP5.TXT"}
	files := map[string][]byte{}
	for _, n := range names {
		files[n] = rd("/orig/orig/" + n)
		logf("輸入 %-14s %7d bytes sha256=%s\n", n, len(files[n]), sum(files[n]))
	}
	for _, n := range []string{"MAIN.EXE", "OP.EXE", "END.EXE"} {
		b := rd("/orig/orig/" + n)
		logf("輸入 %-14s %7d bytes sha256=%s\n", n, len(b), sum(b))
	}
	for _, n := range []string{"str.tsv", "str-OP.tsv", "str-END.tsv"} {
		b := rd("/orig/ida-text/out/" + n)
		logf("輸入 IDA %-12s %7d bytes sha256=%s\n", n, len(b), sum(b))
	}
	var extra [][]byte
	mainS := idaStrings("/orig/ida-text/out/str.tsv", "", 2)
	opS := idaStrings("/orig/ida-text/out/str-OP.tsv", "204D", 2)
	endS := idaStrings("/orig/ida-text/out/str-END.tsv", "21A8", 2)
	logf("IDA 字串：MAIN.EXE 全段 %d 筆，OP.EXE 段 204D %d 筆，END.EXE 段 21A8 %d 筆\n", len(mainS), len(opS), len(endS))
	extra = append(extra, mainS...)
	extra = append(extra, opS...)
	extra = append(extra, endS...)

	out1, rep, err := l10n.GenerateCharmap(files, extra)
	logf("報告：Total=%d FromData=%d FromExtra=%d Shared=%d Undecodable=%X Collisions=%X err=%v\n",
		rep.Total, rep.FromData, rep.FromExtra, rep.Shared, rep.Undecodable, rep.Collisions, err)
	if err != nil {
		os.WriteFile("/out/l1-formats/gen-charmap.log", logb.Bytes(), 0o644)
		os.Exit(1)
	}
	out2, _, _ := l10n.GenerateCharmap(files, extra)
	logf("決定性：兩次產生逐位元相同=%v\n", bytes.Equal(out1, out2))
	logf("輸出 charmap-zh-TW.tsv %d bytes sha256=%s\n", len(out1), sum(out1))
	if err := os.WriteFile("/src/apps/hr/l10n/data/charmap-zh-TW.tsv", out1, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	// 參照：不用 IDA，EXE 以整檔嚴格掃描。
	var wholeExtra [][]byte
	for _, n := range []string{"MAIN.EXE", "OP.EXE", "END.EXE"} {
		wholeExtra = append(wholeExtra, strictStrings(rd("/orig/orig/"+n), 2)...)
	}
	out3, rep3, err3 := l10n.GenerateCharmap(files, wholeExtra)
	logf("參照（整檔嚴格掃描）：Total=%d FromExtra=%d Shared=%d Undecodable=%X Collisions=%X err=%v\n",
		rep3.Total, rep3.FromExtra, rep3.Shared, rep3.Undecodable, rep3.Collisions, err3)
	a, b := codesOf(out1), codesOf(out3)
	var onlyIDA, onlyWhole []int
	for c := range a {
		if _, ok := b[c]; !ok {
			onlyIDA = append(onlyIDA, int(c))
		}
	}
	for c := range b {
		if _, ok := a[c]; !ok {
			onlyWhole = append(onlyWhole, int(c))
		}
	}
	sort.Ints(onlyIDA)
	sort.Ints(onlyWhole)
	logf("只在 IDA 法：%X；只在整檔法：%X\n", onlyIDA, onlyWhole)

	// docs/re/020 第 5.3 節的分解：MAIN.EXE 757、MAIN.EXE 以外 1569、共有 610。
	_, rM, _ := l10n.GenerateCharmap(files, mainS)
	var opEnd [][]byte
	opEnd = append(opEnd, opS...)
	opEnd = append(opEnd, endS...)
	_, rNM, _ := l10n.GenerateCharmap(files, opEnd)
	logf("分解：MAIN.EXE 字串的不重複字=%d（020：757）；MAIN.EXE 以外（資料檔、OP*.TXT、OP.EXE、END.EXE）=%d（020：1569）；共有=%d（020：610）\n",
		rM.FromExtra, rNM.Total, rM.FromExtra+rNM.Total-rep.Total)
	// 只用資料檔與 OP*.TXT（不含 EXE）的字數。
	_, rep0, _ := l10n.GenerateCharmap(files, nil)
	logf("只含資料檔與 OP*.TXT：Total=%d\n", rep0.Total)
	os.WriteFile("/out/l1-formats/gen-charmap.log", logb.Bytes(), 0o644)
}
