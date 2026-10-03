// textscan：原版資料檔的文字普查工具（只讀，容器內執行）。
//
//	textscan scanall                  掃描 /orig 內每個檔案，統計 Big5 雙位元組與 ASCII 字串
//	textscan table <檔名>...           解析 MES/MRG 的偏移表並做項目統計，解碼文字寫到 /out/dump-<檔名>.txt
//
// 輸出檔都在 /out（對應 workplace/out/re-text）。內容含原版文字，只放 workplace，不進版控。
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"golang.org/x/text/encoding/traditionalchinese"
)

func isLead(b byte) bool  { return b >= 0xA1 && b <= 0xF9 }
func isTrail(b byte) bool { return (b >= 0x40 && b <= 0x7E) || (b >= 0xA1 && b <= 0xFE) }

// segment 是一段文字內容的分類統計。
type stats struct {
	big5      int            // 雙位元組字數
	ascii     int            // 可印 ASCII
	ctl       map[byte]int   // 控制位元組（< 0x20，含 0x0A、0x00）
	high      int            // 無法配成雙位元組的高位元組
	uniq      map[uint16]int // 不重複雙位元組字
	asciiSet  map[byte]int
	badTrail  int
}

func newStats() *stats {
	return &stats{ctl: map[byte]int{}, uniq: map[uint16]int{}, asciiSet: map[byte]int{}}
}

func (s *stats) add(b []byte) {
	for i := 0; i < len(b); i++ {
		c := b[i]
		switch {
		case isLead(c) && i+1 < len(b) && isTrail(b[i+1]):
			s.big5++
			s.uniq[uint16(c)<<8|uint16(b[i+1])]++
			i++
		case c >= 0x20 && c <= 0x7E:
			s.ascii++
			s.asciiSet[c]++
		case c < 0x20:
			s.ctl[c]++
		default:
			s.high++
		}
	}
}

// run 找出至少 minChars 個連續雙位元組字的字串（容許夾雜 ASCII 可印字元與 0x0A）。
type run struct {
	off, n, big5 int
}

func findRuns(b []byte, minBig5 int) []run {
	var out []run
	i := 0
	for i < len(b) {
		// 起點要是雙位元組
		if !(isLead(b[i]) && i+1 < len(b) && isTrail(b[i+1])) {
			i++
			continue
		}
		start := i
		big5 := 0
		for i < len(b) {
			if isLead(b[i]) && i+1 < len(b) && isTrail(b[i+1]) {
				big5++
				i += 2
			} else if b[i] >= 0x20 && b[i] <= 0x7E || b[i] == 0x0A || b[i] == 0x0D {
				i++
			} else {
				break
			}
		}
		if big5 >= minBig5 {
			out = append(out, run{start, i - start, big5})
		}
	}
	return out
}

func parseTable(d []byte) (offs []uint32, form string) {
	if len(d) < 6 {
		return nil, "太短"
	}
	n := int(binary.LittleEndian.Uint16(d))
	for _, cnt := range []int{n, n - 1} {
		if cnt < 1 || 2+4*cnt > len(d) {
			continue
		}
		o := make([]uint32, cnt)
		for i := range o {
			o[i] = binary.LittleEndian.Uint32(d[2+4*i:])
		}
		if int(o[0]) == 2+4*cnt {
			form = fmt.Sprintf("N=%d, 偏移數=%d", n, cnt)
			if cnt == n {
				form += "(MES 型：偏移數＝N)"
			} else {
				form += "(MRG 型：偏移數＝N-1)"
			}
			return o, form
		}
	}
	return nil, fmt.Sprintf("N=%d 但首偏移不符合 2+4*cnt", n)
}

func big5ToUTF8(b []byte) string {
	r, _ := traditionalchinese.Big5.NewDecoder().Bytes(b)
	return string(r)
}

func render(b []byte) string {
	// 先把控制位元組換成 <XX>，再解碼雙位元組
	var sb strings.Builder
	i := 0
	for i < len(b) {
		c := b[i]
		switch {
		case isLead(c) && i+1 < len(b) && isTrail(b[i+1]):
			sb.WriteString(big5ToUTF8(b[i : i+2]))
			i += 2
		case c >= 0x20 && c <= 0x7E:
			sb.WriteByte(c)
			i++
		case c == 0x0A:
			sb.WriteString("<LF>")
			i++
		case c == 0x00:
			sb.WriteString("<NUL>")
			i++
		default:
			fmt.Fprintf(&sb, "<%02X>", c)
			i++
		}
	}
	return sb.String()
}

func scanAll() {
	ents, _ := os.ReadDir("/orig")
	var rows []string
	rows = append(rows, "file\tsize\tbig5chars\tbig5runs>=2\tascii_runs>=4\tctl_bytes")
	for _, e := range ents {
		if e.IsDir() {
			continue
		}
		b, err := os.ReadFile(filepath.Join("/orig", e.Name()))
		if err != nil {
			continue
		}
		s := newStats()
		s.add(b)
		runs := findRuns(b, 2)
		// ASCII 連續可印字串 >= 4
		a := 0
		cur := 0
		for _, c := range b {
			if c >= 0x20 && c <= 0x7E {
				cur++
			} else {
				if cur >= 4 {
					a++
				}
				cur = 0
			}
		}
		if cur >= 4 {
			a++
		}
		ct := 0
		for _, v := range s.ctl {
			ct += v
		}
		rows = append(rows, fmt.Sprintf("%s\t%d\t%d\t%d\t%d\t%d", e.Name(), len(b), s.big5, len(runs), a, ct))
	}
	out := strings.Join(rows, "\n") + "\n"
	os.WriteFile("/out/scanall.tsv", []byte(out), 0o644)
	fmt.Print(out)
}

func table(name string) {
	d, err := os.ReadFile("/orig/" + name)
	if err != nil {
		fmt.Println(name, err)
		return
	}
	offs, form := parseTable(d)
	fmt.Printf("== %s size=%d %s\n", name, len(d), form)
	if offs == nil {
		return
	}
	cnt := len(offs)
	mono := true
	for i := 1; i < cnt; i++ {
		if offs[i] < offs[i-1] {
			mono = false
		}
	}
	fmt.Printf("  偏移單調=%v 最後偏移=%d 與檔長差=%d 項目數=%d\n", mono, offs[cnt-1], int(offs[cnt-1])-len(d), cnt-1)
	var dump strings.Builder
	tot := newStats()
	empty, nonEmpty, nested := 0, 0, 0
	maxLen, minLen := 0, 1<<30
	var lens []int
	endNul := 0
	for i := 0; i < cnt-1; i++ {
		a, e := int(offs[i]), int(offs[i+1])
		if e > len(d) {
			e = len(d)
		}
		if a >= e {
			empty++
			continue
		}
		nonEmpty++
		it := d[a:e]
		if n2, _ := parseTable(it); n2 != nil {
			nested++
			fmt.Fprintf(&dump, "[%d] 巢狀表 len=%d\n", i, len(it))
			continue
		}
		if it[len(it)-1] == 0 {
			endNul++
		}
		tot.add(it)
		l := len(it)
		lens = append(lens, l)
		if l > maxLen {
			maxLen = l
		}
		if l < minLen {
			minLen = l
		}
		fmt.Fprintf(&dump, "[%d] len=%d %s\n", i, l, render(it))
	}
	fmt.Printf("  空項目=%d 非空=%d 巢狀=%d 以NUL結尾=%d 最短=%d 最長=%d\n", empty, nonEmpty, nested, endNul, minLen, maxLen)
	fmt.Printf("  雙位元組字=%d 不重複=%d ASCII可印=%d 無法配對高位元組=%d\n", tot.big5, len(tot.uniq), tot.ascii, tot.high)
	var cs []int
	for k := range tot.ctl {
		cs = append(cs, int(k))
	}
	sort.Ints(cs)
	var parts []string
	for _, k := range cs {
		parts = append(parts, fmt.Sprintf("%02X:%d", k, tot.ctl[byte(k)]))
	}
	fmt.Printf("  控制位元組 %s\n", strings.Join(parts, " "))
	os.WriteFile("/out/dump-"+strings.ReplaceAll(name, "/", "_")+".txt", []byte(dump.String()), 0o644)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "用法: textscan scanall | table <檔名>...")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "scanall":
		scanAll()
	case "table":
		for _, n := range os.Args[2:] {
			table(n)
		}
	default:
		fmt.Fprintln(os.Stderr, "未知子命令")
		os.Exit(2)
	}
	_ = bytes.MinRead
}
