// corpus：需翻譯字串的規模盤點（只讀，容器內執行）。
//
//	corpus            輸出總表到標準輸出與 /out/corpus-summary.txt
//
// 來源：
//   - /orig 內的檔案：COUNTRY.MES、SP.MES、SYSTEM.MES、UWASA.MES、POWERMES.MES（MES 表，以 NUL 切分）、
//     ESPMES.MRG（兩層表）、OP.TXT 與 OP0 至 OP5.TXT（CRLF 行）、SHOPTAB.TBL（200 bytes 記錄內的 20 bytes 欄位）。
//   - /idatext/str.tsv（MAIN.EXE，ida_text_strings.py 輸出）、str-OP.tsv、str-END.tsv。
//
// 統計欄位：字串數、不重複字串數（內容去除尾端半形空白後比對）、雙位元組字數、不重複雙位元組字數、
// 半形可印字數、最長位元組數。另輸出所有來源的不重複字集合，並以 CFONT.15 檢查是否都有非空字模。
// 只輸出統計，不輸出原文。
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"

	"golang.org/x/text/encoding/japanese"
	"golang.org/x/text/encoding/korean"
	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/encoding/traditionalchinese"
)

func isLead(b byte) bool  { return b >= 0xA1 && b <= 0xF9 }
func isTrail(b byte) bool { return (b >= 0x40 && b <= 0x7E) || (b >= 0xA1 && b <= 0xFE) }

type item struct {
	src, cat string
	raw      []byte
}

type agg struct {
	n, uniqStr, big5, ascii, maxLen, fmtN int
	uniqChars                             map[uint16]bool
	seen                                  map[string]bool
	chars                                 int
}

func newAgg() *agg { return &agg{uniqChars: map[uint16]bool{}, seen: map[string]bool{}} }

func (a *agg) add(raw []byte) {
	a.n++
	k := string(bytes.TrimRight(raw, " "))
	if !a.seen[k] {
		a.seen[k] = true
		a.uniqStr++
	}
	for i := 0; i < len(raw); i++ {
		c := raw[i]
		if isLead(c) && i+1 < len(raw) && isTrail(raw[i+1]) {
			a.big5++
			a.uniqChars[uint16(c)<<8|uint16(raw[i+1])] = true
			i++
		} else if c >= 0x21 && c <= 0x7E {
			a.ascii++
		}
	}
	if len(raw) > a.maxLen {
		a.maxLen = len(raw)
	}
	if bytes.IndexByte(raw, '%') >= 0 {
		a.fmtN++
	}
}

func hasBig5(b []byte) bool {
	for i := 0; i+1 < len(b); i++ {
		if isLead(b[i]) && isTrail(b[i+1]) {
			return true
		}
	}
	return false
}

func readFile(name string) []byte {
	b, err := os.ReadFile("/orig/" + name)
	if err != nil {
		fmt.Println("讀不到", name, err)
		os.Exit(1)
	}
	return b
}

// mesItems 以 NUL 切分，從第一個偏移開始，到 0xFF 結尾標記前。
func mesItems(d []byte) [][]byte {
	n := int(binary.LittleEndian.Uint16(d))
	pos := int(binary.LittleEndian.Uint32(d[2:]))
	var out [][]byte
	for len(out) < n-1 && pos < len(d) {
		j := bytes.IndexByte(d[pos:], 0)
		if j < 0 {
			break
		}
		out = append(out, d[pos:pos+j])
		pos += j + 1
	}
	return out
}

func espItems(d []byte) [][]byte {
	n := int(binary.LittleEndian.Uint16(d))
	offs := make([]int, n-1)
	for i := range offs {
		offs[i] = int(binary.LittleEndian.Uint32(d[2+4*i:]))
	}
	offs = append(offs, len(d)) // 最後一個偏移是最後一個群組的起點，延伸到檔尾
	var out [][]byte
	for g := 0; g+1 < len(offs); g++ {
		a, e := offs[g], offs[g+1]
		if a >= e {
			continue
		}
		grp := d[a:e]
		n2 := int(binary.LittleEndian.Uint16(grp))
		o2 := make([]int, n2)
		for i := range o2 {
			o2[i] = int(binary.LittleEndian.Uint32(grp[2+4*i:]))
		}
		for k := 0; k+1 < len(o2); k++ {
			if o2[k] < o2[k+1] && o2[k+1] <= len(grp) {
				it := grp[o2[k]:o2[k+1]]
				out = append(out, bytes.TrimRight(it, "\x00"))
			}
		}
	}
	return out
}

func tsvItems(path, src string, minBig5 int, catFn func(sel string, raw []byte, nb int) string) []item {
	b, err := os.ReadFile(path)
	if err != nil {
		fmt.Println(err)
		return nil
	}
	var out []item
	for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 {
			continue
		}
		bc, _ := strconv.Atoi(f[4])
		nb, _ := strconv.Atoi(f[3])
		if bc < minBig5 {
			continue
		}
		raw, _ := hex.DecodeString(f[9])
		if len(raw) < nb { // hex 最多 160 bytes，長字串被截斷時以長度標記
			// 截斷只影響字集合，不影響字串數與 nb；補齊長度資訊
		}
		out = append(out, item{src: src, cat: catFn(f[0][:4], raw, nb), raw: raw})
	}
	return out
}

func main() {
	var items []item
	// 檔案
	for _, n := range []string{"COUNTRY.MES", "SP.MES", "SYSTEM.MES", "UWASA.MES", "POWERMES.MES"} {
		for _, it := range mesItems(readFile(n)) {
			items = append(items, item{n, "檔案:對白與敘述", it})
		}
	}
	for _, it := range espItems(readFile("ESPMES.MRG")) {
		items = append(items, item{"ESPMES.MRG", "檔案:對白與敘述", it})
	}
	for _, n := range []string{"OP.TXT", "OP0.TXT", "OP1.TXT", "OP2.TXT", "OP3.TXT", "OP4.TXT", "OP5.TXT"} {
		for _, ln := range bytes.Split(readFile(n), []byte("\r\n")) {
			t := bytes.TrimSpace(ln)
			if hasBig5(t) {
				items = append(items, item{n, "檔案:片頭文字", t})
			}
		}
	}
	// SHOPTAB.TBL：200 bytes 記錄，欄位以 NUL 或長度切分；取含雙位元組字的連續（雙位元組或空白）片段
	{
		d := readFile("SHOPTAB.TBL")
		i := 0
		for i < len(d) {
			if isLead(d[i]) && i+1 < len(d) && isTrail(d[i+1]) {
				s := i
				for i < len(d) {
					if isLead(d[i]) && i+1 < len(d) && isTrail(d[i+1]) {
						i += 2
					} else if d[i] == ' ' {
						i++
					} else {
						break
					}
				}
				items = append(items, item{"SHOPTAB.TBL", "檔案:商店表欄位", bytes.TrimRight(d[s:i], " ")})
			} else {
				i++
			}
		}
	}
	// MAIN.EXE 與 OP/END
	mainCat := func(sel string, raw []byte, nb int) string {
		switch {
		case bytes.IndexByte(raw, '%') >= 0:
			return "MAIN:格式字串(含%)"
		case nb == 20:
			return "MAIN:名稱表(固定20位元組)"
		default:
			return "MAIN:其他介面與敘述"
		}
	}
	items = append(items, tsvItems("/idatext/str.tsv", "MAIN.EXE", 2, mainCat)...)
	// OP/END 只取資料段（排除程式碼段雜訊）：204D（OP）與 21A8（END）
	filterSeg := func(items []item, path string, sel string) []item {
		b, _ := os.ReadFile(path)
		var out []item
		_ = items
		for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n")[1:] {
			f := strings.Split(ln, "\t")
			if len(f) < 10 || f[0][:4] != sel {
				continue
			}
			bc, _ := strconv.Atoi(f[4])
			if bc < 2 {
				continue
			}
			raw, _ := hex.DecodeString(f[9])
			out = append(out, item{"", "", raw})
		}
		return out
	}
	for _, it := range filterSeg(nil, "/idatext/str-OP.tsv", "204D") {
		it.src, it.cat = "OP.EXE", "OP.EXE:資料段字串"
		items = append(items, it)
	}
	for _, it := range filterSeg(nil, "/idatext/str-END.tsv", "21A8") {
		it.src, it.cat = "END.EXE", "END.EXE:資料段字串"
		items = append(items, it)
	}

	// 彙總
	byCat := map[string]*agg{}
	bySrc := map[string]*agg{}
	all := newAgg()
	var cats, srcs []string
	for _, it := range items {
		a := byCat[it.cat]
		if a == nil {
			a = newAgg()
			byCat[it.cat] = a
			cats = append(cats, it.cat)
		}
		a.add(it.raw)
		s := bySrc[it.src]
		if s == nil {
			s = newAgg()
			bySrc[it.src] = s
			srcs = append(srcs, it.src)
		}
		s.add(it.raw)
		all.add(it.raw)
	}
	var out strings.Builder
	w := func(format string, a ...any) {
		s := fmt.Sprintf(format, a...)
		out.WriteString(s)
		fmt.Print(s)
	}
	w("== 依來源\n來源\t字串數\t不重複字串\t雙位元組字\t不重複字\tASCII可印\t含%%\t最長bytes\n")
	for _, s := range srcs {
		a := bySrc[s]
		w("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", s, a.n, a.uniqStr, a.big5, len(a.uniqChars), a.ascii, a.fmtN, a.maxLen)
	}
	w("== 依類別\n類別\t字串數\t不重複字串\t雙位元組字\t不重複字\tASCII可印\t含%%\t最長bytes\n")
	sort.Strings(cats)
	for _, c := range cats {
		a := byCat[c]
		w("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", c, a.n, a.uniqStr, a.big5, len(a.uniqChars), a.ascii, a.fmtN, a.maxLen)
	}
	w("== 合計\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", all.n, all.uniqStr, all.big5, len(all.uniqChars), all.ascii, all.fmtN, all.maxLen)

	// 字集合與 CFONT.15 涵蓋
	cf := readFile("CFONT.15")
	idx := func(lead, trail int) int {
		t := trail - 0x62
		if trail <= 0x7E {
			t = trail - 0x40
		}
		switch {
		case lead <= 0xA3:
			return (lead-0xA1)*157 + t
		case (lead == 0xC6 && trail >= 0xA1) || (lead > 0xC6 && lead <= 0xC8):
			return (lead-0xC6)*157 + t - 0x3F + 0x198
		default:
			x := (lead-0xA4)*157 + t
			if lead >= 0xC9 {
				x -= 0x198
			}
			return x + 0x305
		}
	}
	blank := func(code uint16) (bool, bool) {
		i := idx(int(code>>8), int(code&0xff))
		if i < 0 || (i+1)*30 > len(cf) {
			return false, false
		}
		g := cf[i*30 : i*30+30]
		for _, b := range g {
			if b != 0 {
				return false, true
			}
		}
		return true, true
	}
	missing, blanks := 0, 0
	for c := range all.uniqChars {
		bl, ok := blank(c)
		if !ok {
			missing++
		} else if bl {
			blanks++
		}
	}
	w("== 字集合：全部來源不重複雙位元組字=%d；索引超出 CFONT.15=%d；字模全空=%d\n", len(all.uniqChars), missing, blanks)
	// 各來源之間的不重複字集合重疊：以「檔案」「MAIN」兩大類
	fileSet, mainSet := map[uint16]bool{}, map[uint16]bool{}
	for _, it := range items {
		set := fileSet
		if strings.HasPrefix(it.cat, "MAIN") {
			set = mainSet
		}
		for i := 0; i+1 < len(it.raw); i++ {
			if isLead(it.raw[i]) && isTrail(it.raw[i+1]) {
				set[uint16(it.raw[i])<<8|uint16(it.raw[i+1])] = true
				i++
			}
		}
	}
	both := 0
	for c := range mainSet {
		if fileSet[c] {
			both++
		}
	}
	w("== 字集合：檔案與 OP/END 以外=%d；MAIN=%d；兩者共有=%d\n", len(fileSet), len(mainSet), both)
	// 字集合對各語系字集的涵蓋（代理指標：能否用該語系的標準字集編碼；不等於字形相同）
	{
		dec := traditionalchinese.Big5.NewDecoder()
		gb := simplifiedchinese.HZGB2312.NewEncoder()
		sj := japanese.ShiftJIS.NewEncoder()
		ks := korean.EUCKR.NewEncoder()
		total, decErr, notGB, notJIS, notKS := 0, 0, 0, 0, 0
		for c := range all.uniqChars {
			u, err := dec.Bytes([]byte{byte(c >> 8), byte(c)})
			total++
			if err != nil || len(u) == 0 || []rune(string(u))[0] == 0xFFFD {
				decErr++
				continue
			}
			s := string(u)
			if _, err := gb.String(s); err != nil {
				notGB++
			}
			if _, err := sj.String(s); err != nil {
				notJIS++
			}
			if _, err := ks.String(s); err != nil {
				notKS++
			}
		}
		reg := map[string]int{}
		for c := range all.uniqChars {
			l, t := int(c>>8), int(c&0xff)
			switch {
			case l <= 0xA3:
				reg["A1-A3 符號"]++
			case l == 0xC6 && t >= 0xA1, l == 0xC7, l == 0xC8:
				reg["C6A1-C8FE 擴充(假名等)"]++
			case l >= 0xA4 && l <= 0xC6:
				reg["A4-C6 常用字"]++
			default:
				reg["C9-F9 次常用字"]++
			}
		}
		w("== 不重複字依字模區：%v\n", reg)
		w("== 字集代理指標：不重複字=%d；Big5 無法轉 Unicode=%d；不在 GB2312=%d；不在 Shift_JIS(JIS X 0208)=%d；不在 EUC-KR(KS X 1001，含漢字)=%d\n", total, decErr, notGB, notJIS, notKS)
	}
	os.WriteFile("/out/corpus-summary.txt", []byte(out.String()), 0o644)
}
