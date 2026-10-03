// espmes：解析 ESPMES.MRG 的兩層結構（237B:0464 的讀取方式：群組編號、子編號），輸出統計。
//
//	espmes
//
// 外層：u16 N，N-1 個 u32 偏移（N-2 個群組）。內層：每個非空群組是同形的表（u16 N2 與偏移，偏移相對群組起點）。
// 輸出每個非空群組：外層索引、群組長度、內層 N2 與偏移數的判定、子項目數、空子項目數、字數、最長子項目；
// 並把解碼文字寫到 /out/dump-ESPMES-groups.txt（含控制碼的十六進位標示）。
package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"sort"
	"strings"

	"golang.org/x/text/encoding/traditionalchinese"
)

func isLead(b byte) bool  { return b >= 0xA1 && b <= 0xF9 }
func isTrail(b byte) bool { return (b >= 0x40 && b <= 0x7E) || (b >= 0xA1 && b <= 0xFE) }

func render(b []byte) string {
	var sb strings.Builder
	dec := traditionalchinese.Big5.NewDecoder()
	for i := 0; i < len(b); {
		c := b[i]
		switch {
		case isLead(c) && i+1 < len(b) && isTrail(b[i+1]):
			t, _ := dec.Bytes(b[i : i+2])
			sb.Write(t)
			i += 2
		case c >= 0x20 && c <= 0x7E:
			sb.WriteByte(c)
			i++
		case c == 0x0A:
			sb.WriteString("<LF>")
			i++
		case c == 0:
			sb.WriteString("<NUL>")
			i++
		default:
			fmt.Fprintf(&sb, "<%02X>", c)
			i++
		}
	}
	return sb.String()
}

func count(b []byte) (big5, ascii int, ctl map[byte]int) {
	ctl = map[byte]int{}
	for i := 0; i < len(b); i++ {
		c := b[i]
		switch {
		case isLead(c) && i+1 < len(b) && isTrail(b[i+1]):
			big5++
			i++
		case c >= 0x20 && c <= 0x7E:
			ascii++
		default:
			ctl[c]++
		}
	}
	return
}

func main() {
	d, err := os.ReadFile("/orig/ESPMES.MRG")
	if err != nil {
		fmt.Println(err)
		return
	}
	n := int(binary.LittleEndian.Uint16(d))
	offs := make([]int, n-1)
	for i := range offs {
		offs[i] = int(binary.LittleEndian.Uint32(d[2+4*i:]))
	}
	offsLen := len(offs)
	offs = append(offs, len(d)) // 最後一個偏移是最後一個群組的起點，群組延伸到檔尾
	fmt.Printf("ESPMES.MRG size=%d N=%d 外層偏移數=%d 首偏移=%d 末偏移=%d（檔長-末偏移=%d）\n", len(d), n, offsLen, offs[0], offs[offsLen-1], len(d)-offs[offsLen-1])
	var dump strings.Builder
	totItems, totEmpty, totBig5, totAscii := 0, 0, 0, 0
	allCtl := map[byte]int{}
	uniq := map[uint16]bool{}
	maxLen := 0
	for g := 0; g+1 < len(offs); g++ {
		a, e := offs[g], offs[g+1]
		if a >= e {
			continue
		}
		grp := d[a:e]
		n2 := int(binary.LittleEndian.Uint16(grp))
		var o2 []int
		form := ""
		for _, cnt := range []int{n2 - 1, n2} {
			if cnt < 1 || 2+4*cnt > len(grp) {
				continue
			}
			t := make([]int, cnt)
			for i := range t {
				t[i] = int(binary.LittleEndian.Uint32(grp[2+4*i:]))
			}
			if t[0] == 2+4*cnt {
				o2, form = t, fmt.Sprintf("偏移數=%d", cnt)
				if cnt == n2-1 {
					form += "(N2-1)"
				} else {
					form += "(N2)"
				}
				break
			}
		}
		if o2 == nil {
			fmt.Printf("群組[%d] len=%d N2=%d：偏移表無法判定\n", g, len(grp), n2)
			continue
		}
		items, empty, b5, as, mx := 0, 0, 0, 0, 0
		for k := 0; k+1 < len(o2); k++ {
			s, t := o2[k], o2[k+1]
			items++
			if s >= t || t > len(grp) {
				empty++
				continue
			}
			it := grp[s:t]
			bb, aa, cc := count(it)
			b5 += bb
			as += aa
			for kk, v := range cc {
				allCtl[kk] += v
			}
			for i := 0; i+1 < len(it); i++ {
				if isLead(it[i]) && isTrail(it[i+1]) {
					uniq[uint16(it[i])<<8|uint16(it[i+1])] = true
					i++
				}
			}
			if len(it) > mx {
				mx = len(it)
			}
			fmt.Fprintf(&dump, "[%d.%d] len=%d %s\n", g, k, len(it), render(it))
		}
		fmt.Printf("群組[%d] len=%d N2=%d %s 末偏移=%d 子項目=%d 空=%d 字數=%d ASCII=%d 最長=%d\n", g, len(grp), n2, form, o2[len(o2)-1], items, empty, b5, as, mx)
		totItems += items
		totEmpty += empty
		totBig5 += b5
		totAscii += as
		if mx > maxLen {
			maxLen = mx
		}
	}
	var cs []int
	for k := range allCtl {
		cs = append(cs, int(k))
	}
	sort.Ints(cs)
	var parts []string
	for _, k := range cs {
		parts = append(parts, fmt.Sprintf("%02X:%d", k, allCtl[byte(k)]))
	}
	fmt.Printf("合計：子項目=%d 其中空=%d 雙位元組字=%d 不重複=%d ASCII=%d 最長=%d 控制位元組 %s\n", totItems, totEmpty, totBig5, len(uniq), totAscii, maxLen, strings.Join(parts, " "))
	os.WriteFile("/out/dump-ESPMES-groups.txt", []byte(dump.String()), 0o644)
}
