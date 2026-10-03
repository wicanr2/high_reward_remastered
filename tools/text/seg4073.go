// seg4073：把段 4073（存檔傾印範圍 4073:0008 起 31839 bytes）內的字串依記錄步幅分類。
//
//	seg4073
// 記錄：地名表 4073:01AB 起每 0x65 bytes（名稱欄 20 bytes）、國名表 4073:28BC 起每 0x49 bytes。
// 其餘依偏移區間列出數量。不輸出原文。
package main

import (
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func main() {
	b, _ := os.ReadFile("/idatext/str.tsv")
	cnt := map[string]int{}
	chars := map[string]int{}
	var others []int
	inSave := 0
	for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 || f[0][:4] != "4073" {
			continue
		}
		bc, _ := strconv.Atoi(f[4])
		if bc < 2 {
			continue
		}
		o64, _ := strconv.ParseInt(f[0][5:], 16, 32)
		off := int(o64)
		if off >= 8 && off < 0x7C67 {
			inSave++
		}
		var cls string
		switch {
		case off >= 0x1AB && off < 0x28BC && (off-0x1AB)%0x65 == 0:
			cls = "地名表(0x65 步幅)"
		case off >= 0x28BC && (off-0x28BC)%0x49 == 0:
			cls = "國名表(0x49 步幅)"
		default:
			cls = "其他"
			others = append(others, off)
		}
		cnt[cls]++
		chars[cls] += bc
	}
	for k, v := range cnt {
		fmt.Printf("%-18s 字串=%d 字=%d\n", k, v, chars[k])
	}
	fmt.Printf("段 4073 內且落在存檔範圍(4073:0008..7C66)的字串=%d\n", inSave)
	sort.Ints(others)
	if len(others) > 0 {
		fmt.Printf("其他類偏移範圍 %#x..%#x，共 %d 筆；前 40 筆偏移:", others[0], others[len(others)-1], len(others))
		for i := 0; i < len(others) && i < 40; i++ {
			fmt.Printf(" %#x", others[i])
		}
		fmt.Println()
	}
}
