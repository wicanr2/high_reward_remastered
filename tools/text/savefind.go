// savefind：把 MAIN.EXE 段 4073 內的字串（str.tsv）拿到存檔裡找位置，看存檔與初始映像的位移關係。
//
//	savefind <存檔檔名> [段選擇子]
// 輸出：找得到的字串數、位移差（存檔位移 － 段內偏移）的分佈、找不到的字串數。
package main

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func main() {
	save, err := os.ReadFile("/orig/" + os.Args[1])
	if err != nil {
		fmt.Println(err)
		return
	}
	sel := "4073"
	if len(os.Args) > 2 {
		sel = strings.ToUpper(os.Args[2])
	}
	tsv, _ := os.ReadFile("/idatext/str.tsv")
	found, miss, multi := 0, 0, 0
	delta := map[int]int{}
	for _, ln := range strings.Split(strings.TrimSpace(string(tsv)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 || f[0][:4] != sel {
			continue
		}
		nb, _ := strconv.Atoi(f[3])
		bc, _ := strconv.Atoi(f[4])
		if bc < 3 || nb > 80 {
			continue
		}
		raw, _ := hex.DecodeString(f[9])
		if len(raw) < 6 {
			continue
		}
		off64, _ := strconv.ParseInt(f[0][5:], 16, 32)
		off := int(off64)
		idx := bytes.Index(save, raw)
		if idx < 0 {
			miss++
			continue
		}
		if bytes.Count(save, raw) > 1 {
			multi++
			continue
		}
		found++
		delta[idx-off]++
	}
	fmt.Printf("%s 段 %s：唯一找到=%d 多處命中(略過)=%d 找不到=%d\n", os.Args[1], sel, found, multi, miss)
	var ks []int
	for k := range delta {
		ks = append(ks, k)
	}
	sort.Ints(ks)
	for _, k := range ks {
		fmt.Printf("  位移差 %+d（0x%X）: %d 筆\n", k, k&0xffff, delta[k])
	}
}
