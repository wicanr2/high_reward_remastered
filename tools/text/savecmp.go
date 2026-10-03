// savecmp：比對存檔 GAMEFILE.00x 與 MAIN.EXE 內 IDA 段 4073 的初始資料。
//
//	savecmp
// 段 4073 線性位址 0x40730，檔案位移 ＝ 線性 － 0x10000 ＋ 18944（docs/re/006、007）。
// 對每個存檔輸出：存檔長度、最佳對齊位移（0 或 ±1）下相同的位元組比例、不同區段的數量與範圍摘要。
package main

import (
	"fmt"
	"os"
)

func main() {
	main, err := os.ReadFile("/orig/MAIN.EXE")
	if err != nil {
		fmt.Println(err)
		return
	}
	base := 0x40730 - 0x10000 + 18944
	segLen := 31840
	img := main[base : base+segLen]
	for _, name := range []string{"GAMEFILE.000", "GAMEFILE.001", "GAMEFILE.002", "GAMEFILE.003", "GAMEFILE.004", "复件 GAMEFILE.001"} {
		s, err := os.ReadFile("/orig/" + name)
		if err != nil {
			fmt.Println(name, err)
			continue
		}
		for _, shift := range []int{0, 8} {
			same, tot := 0, 0
			for i := 0; i < len(s); i++ {
				j := i + shift
				if j < 0 || j >= len(img) {
					continue
				}
				tot++
				if s[i] == img[j] {
					same++
				}
			}
			fmt.Printf("%s len=%d shift=%+d 相同=%d/%d (%.1f%%)\n", name, len(s), shift, same, tot, 100*float64(same)/float64(tot))
		}
	}
	// 以 shift=0 列出 GAMEFILE.000 與初始映像不同的區段（合併相距 <= 8 的差異）
	s, _ := os.ReadFile("/orig/GAMEFILE.000")
	type rg struct{ a, b int }
	var rs []rg
	for i := 0; i < len(s) && i+8 < len(img); i++ {
		if i+8 < len(img) && s[i] != img[i+8] {
			if len(rs) > 0 && i-rs[len(rs)-1].b <= 8 {
				rs[len(rs)-1].b = i + 1
			} else {
				rs = append(rs, rg{i, i + 1})
			}
		}
	}
	fmt.Printf("GAMEFILE.000 與段 4073 初始映像不同的區段數=%d（shift=0）\n", len(rs))
	for k, r := range rs {
		if k >= 40 {
			break
		}
		fmt.Printf("  [%04X,%04X) len=%d\n", r.a, r.b, r.b-r.a)
	}
	fmt.Printf("段 4073 最後 4 bytes=% X；GAMEFILE.000 最後 4 bytes=% X\n", img[len(img)-4:], s[len(s)-4:])
}
