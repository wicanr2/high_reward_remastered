// savefind2：把 MAIN.EXE 各資料段的字串（str.tsv，雙位元組字 >= 2）去掉尾端空白後，到存檔裡找出現位置。
//
//	savefind2 <存檔檔名> <段選擇子，逗號分隔>
// 每段輸出：字串數、在存檔內找得到（至少一處）的字串數、唯一命中數，以及命中位置換成 4073 偏移（存檔位移 ＋ 8）的範圍與前幾筆。
// 找得到不代表是該段的資料被複製進存檔：短名稱可能剛好出現在別的欄位，只是上限證據。
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

func trimSp(b []byte) []byte {
	for {
		switch {
		case len(b) > 0 && b[len(b)-1] == ' ':
			b = b[:len(b)-1]
		case len(b) >= 2 && b[len(b)-2] == 0xA1 && b[len(b)-1] == 0x40:
			b = b[:len(b)-2]
		default:
			return b
		}
	}
}

func main() {
	save, err := os.ReadFile("/orig/" + os.Args[1])
	if err != nil {
		fmt.Println(err)
		return
	}
	segs := strings.Split(strings.ToUpper(os.Args[2]), ",")
	tsv, _ := os.ReadFile("/idatext/str.tsv")
	type st struct {
		n, any, uniq int
		offs         []int
	}
	m := map[string]*st{}
	for _, s := range segs {
		m[s] = &st{}
	}
	for _, ln := range strings.Split(strings.TrimSpace(string(tsv)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 {
			continue
		}
		s := m[f[0][:4]]
		if s == nil {
			continue
		}
		bc, _ := strconv.Atoi(f[4])
		if bc < 2 {
			continue
		}
		raw, _ := hex.DecodeString(f[9])
		raw = trimSp(raw)
		if len(raw) < 4 {
			continue
		}
		s.n++
		c := bytes.Count(save, raw)
		if c > 0 {
			s.any++
			if c == 1 {
				s.uniq++
			}
			s.offs = append(s.offs, bytes.Index(save, raw)+8)
		}
	}
	for _, k := range segs {
		s := m[k]
		sort.Ints(s.offs)
		fmt.Printf("段 %s：字串=%d 存檔內找得到=%d（唯一=%d）", k, s.n, s.any, s.uniq)
		if len(s.offs) > 0 {
			fmt.Printf(" 4073 偏移範圍 %#x..%#x；前 6 筆 ", s.offs[0], s.offs[len(s.offs)-1])
			for i := 0; i < len(s.offs) && i < 6; i++ {
				fmt.Printf("%#x ", s.offs[i])
			}
		}
		fmt.Println()
	}
}
