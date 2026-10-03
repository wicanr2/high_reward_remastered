// strview：讀 IDA 匯出的 str.tsv（ida_text_strings.py），依條件列出解碼後的字串（只給研究者在終端機看，不進報告）。
//
//	strview <tsv> seg <段選擇子> [最大列數]      列出該段的字串（內容截斷到 24 字）
//	strview <tsv> summary                       依段彙總：字串數、字數、無 xref 數
//	strview <tsv> noref <段選擇子> [最大列數]    列出沒有 xref 的字串
package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"strconv"
	"strings"

	"golang.org/x/text/encoding/traditionalchinese"
)

func main() {
	b, err := os.ReadFile("/idatext/" + os.Args[1])
	if err != nil {
		fmt.Println(err)
		return
	}
	lines := strings.Split(strings.TrimSpace(string(b)), "\n")[1:]
	mode := os.Args[2]
	max := 40
	minc := 1
	if len(os.Args) > 5 {
		minc, _ = strconv.Atoi(os.Args[5])
	}
	if len(os.Args) > 4 {
		max, _ = strconv.Atoi(os.Args[4])
	}
	dec := traditionalchinese.Big5.NewDecoder()
	n := 0
	for _, ln := range lines {
		f := strings.Split(ln, "\t")
		if len(f) < 10 {
			continue
		}
		sel := f[0][:4]
		switch mode {
		case "seg", "noref":
			if !strings.Contains(","+strings.ToUpper(os.Args[3])+",", ","+sel+",") {
				continue
			}
			if mode == "noref" && f[7] != "0" {
				continue
			}
		default:
			continue
		}
		if bc, _ := strconv.Atoi(f[4]); bc < minc {
			continue
		}
		raw, _ := hex.DecodeString(f[9])
		t, _ := dec.Bytes(raw)
		s := strings.NewReplacer("\n", "<LF>", "\r", "<CR>").Replace(string(t))
		r := []rune(strings.TrimSpace(s))
		if len(r) > 24 {
			r = append(r[:24], '…')
		}
		fmt.Printf("%s n=%s big5=%s xr=%s %s | %s\n", f[0], f[3], f[4], f[7], f[8], string(r))
		n++
		if n >= max {
			break
		}
	}
}
