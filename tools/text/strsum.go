// strsum：依段彙總 IDA 匯出的 str.tsv：字串數、雙位元組字數、無 xref 數、位元組長度分佈前三名、含 % 的字串數、前三筆樣本（解碼後 12 字）。
//
//	strsum <tsv> [最少雙位元組字數，預設 1]
//
// 只供研究者在終端機看，不進報告。
package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"

	"golang.org/x/text/encoding/traditionalchinese"
)

type seg struct {
	sel, cls          string
	n, chars, noref   int
	pct               int
	lens              map[int]int
	samples           []string
}

func main() {
	b, err := os.ReadFile("/idatext/" + os.Args[1])
	if err != nil {
		fmt.Println(err)
		return
	}
	minc := 1
	if len(os.Args) > 2 {
		minc, _ = strconv.Atoi(os.Args[2])
	}
	dec := traditionalchinese.Big5.NewDecoder()
	segs := map[string]*seg{}
	var order []string
	totS, totC := 0, 0
	for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n")[1:] {
		f := strings.Split(ln, "\t")
		if len(f) < 10 {
			continue
		}
		bc, _ := strconv.Atoi(f[4])
		if bc < minc {
			continue
		}
		sel := f[0][:4]
		s := segs[sel]
		if s == nil {
			s = &seg{sel: sel, cls: f[2], lens: map[int]int{}}
			segs[sel] = s
			order = append(order, sel)
		}
		nb, _ := strconv.Atoi(f[3])
		s.n++
		s.chars += bc
		totS++
		totC += bc
		if f[7] == "0" {
			s.noref++
		}
		s.lens[nb]++
		raw, _ := hex.DecodeString(f[9])
		if strings.Contains(string(raw), "%") {
			s.pct++
		}
		if len(s.samples) < 3 {
			t, _ := dec.Bytes(raw)
			r := []rune(strings.NewReplacer("\n", "/", "\r", "").Replace(string(t)))
			if len(r) > 12 {
				r = r[:12]
			}
			s.samples = append(s.samples, string(r))
		}
	}
	for _, sel := range order {
		s := segs[sel]
		type kv struct{ k, v int }
		var kvs []kv
		for k, v := range s.lens {
			kvs = append(kvs, kv{k, v})
		}
		sort.Slice(kvs, func(i, j int) bool { return kvs[i].v > kvs[j].v })
		var ls []string
		for i := 0; i < len(kvs) && i < 3; i++ {
			ls = append(ls, fmt.Sprintf("%d×%d", kvs[i].k, kvs[i].v))
		}
		fmt.Printf("%s %-8s 字串=%3d 字=%4d 無xref=%3d %%=%2d 長度[%s] | %s\n", s.sel, s.cls, s.n, s.chars, s.noref, s.pct, strings.Join(ls, ","), strings.Join(s.samples, " / "))
	}
	fmt.Printf("合計 字串=%d 雙位元組字=%d（最少字數門檻 %d）\n", totS, totC, minc)
}
