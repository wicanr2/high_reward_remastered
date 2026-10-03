// loose：以寬鬆規則（不要求 NUL 邊界）掃描 MAIN.EXE 資料段內的雙位元組連續字，與嚴格字串掃描比對，估計漏抓量。
//
//	loose
// 輸入：/idatext/str.seg（段起點線性位址、大小、類別、嚴格字串的字數）、/orig/MAIN.EXE。
// 只掃類別 UNK（資料段）。連續片段：雙位元組字、可印 ASCII、0x0A，含至少 2 個雙位元組字。
// 輸出：資料段合計（寬鬆字數、嚴格字數）與兩者差距最大的段。
package main

import (
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func isLead(b byte) bool  { return b >= 0xA1 && b <= 0xF9 }
func isTrail(b byte) bool { return (b >= 0x40 && b <= 0x7E) || (b >= 0xA1 && b <= 0xFE) }

func main() {
	exe, _ := os.ReadFile("/orig/MAIN.EXE")
	b, _ := os.ReadFile("/idatext/str.seg")
	type row struct {
		sel               string
		loose, strict, rs int
	}
	var rows []row
	tl, ts := 0, 0
	for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 8 || f[2] != "UNK" {
			continue
		}
		size, _ := strconv.Atoi(f[3])
		strictChars, _ := strconv.Atoi(f[5])
		start, _ := strconv.ParseInt(strings.TrimPrefix(f[7], "0x"), 16, 64)
		fo := int(start) - 0x10000 + 18944
		if fo < 0 || fo+size > 361856 {
			continue
		}
		seg := exe[fo : fo+size]
		loose, runs := 0, 0
		for i := 0; i < len(seg); {
			if !(isLead(seg[i]) && i+1 < len(seg) && isTrail(seg[i+1])) {
				i++
				continue
			}
			n := 0
			for i < len(seg) {
				if isLead(seg[i]) && i+1 < len(seg) && isTrail(seg[i+1]) {
					n++
					i += 2
				} else if (seg[i] >= 0x20 && seg[i] <= 0x7E) || seg[i] == 0x0A {
					i++
				} else {
					break
				}
			}
			if n >= 2 {
				loose += n
				runs++
			}
		}
		rows = append(rows, row{f[1], loose, strictChars, runs})
		tl += loose
		ts += strictChars
	}
	fmt.Printf("資料段(UNK)合計：寬鬆連續字(>=2字)=%d；嚴格字串字數(>=1字，含單字雜訊)=%d\n", tl, ts)
	sort.Slice(rows, func(i, j int) bool { return rows[i].loose-rows[i].strict > rows[j].loose-rows[j].strict })
	for i := 0; i < len(rows) && i < 12; i++ {
		fmt.Printf("  %s 寬鬆=%d 嚴格=%d 差=%d 片段數=%d\n", rows[i].sel, rows[i].loose, rows[i].strict, rows[i].loose-rows[i].strict, rows[i].rs)
	}
}
