// xrefstat：把 MAIN.EXE 的字串（str.tsv，雙位元組字 >= 2）依「怎麼被引用」分類並統計。
//
//	xrefstat
// 類別：code（至少一個 xref 來自函式內的指令）、table（xref 只來自資料，func 欄為 -，例如同段的近指標表）、none（沒有 xref：
// 欄位陣列或記錄內的固定寬度欄位，由程式以「基底＋索引×步幅」存取）。另列固定 20 位元組欄位（長度恰為 20）占 none 的比例。
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	b, _ := os.ReadFile("/idatext/str.tsv")
	type c struct{ n, chars, n20 int }
	m := map[string]*c{"code": {}, "table": {}, "none": {}}
	for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 {
			continue
		}
		bc, _ := strconv.Atoi(f[4])
		nb, _ := strconv.Atoi(f[3])
		if bc < 2 {
			continue
		}
		cls := "none"
		if f[7] != "0" {
			cls = "table"
			for _, x := range strings.Fields(f[8]) {
				p := strings.Split(x, ":")
				// 格式 來源段:來源偏移:函式段:函式偏移 ；函式欄為 "-" 表示來源不在函式內
				if len(p) == 3 && p[2] != "-" || len(p) == 4 && p[3] != "-" {
					cls = "code"
				}
			}
		}
		e := m[cls]
		e.n++
		e.chars += bc
		if nb == 20 {
			e.n20++
		}
	}
	for _, k := range []string{"code", "table", "none"} {
		fmt.Printf("%-6s 字串=%4d 雙位元組字=%5d 其中長度恰為20=%d\n", k, m[k].n, m[k].chars, m[k].n20)
	}
}
