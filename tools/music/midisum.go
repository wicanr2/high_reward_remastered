// midisum 輸出每個 MID 的摘要 TSV：名稱、大小、軌數、音符數、結束 tick、曲長秒數。
// 這是獨立於 apps/hr/sound 解析器的第二份實作，用來交叉驗證解析器與離線轉檔長度
// （docs/spec/007 第 8 節）。曲長依速度表逐段換算，不假設單一速度。
//
//	tools/music/run.sh midisum /orig/*.MID
package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type tempoEv struct {
	tick uint64
	us   uint64
}

func sum(path string) string {
	name := strings.TrimSuffix(strings.ToUpper(filepath.Base(path)), ".MID")
	b, err := os.ReadFile(path)
	if err != nil {
		return fmt.Sprintf("%s\tERR\t%v", name, err)
	}
	if len(b) == 0 {
		return fmt.Sprintf("%s\t0\t-\t-\t-\t-", name)
	}
	if len(b) < 14 || string(b[:4]) != "MThd" {
		return fmt.Sprintf("%s\t%d\tNOT-SMF", name, len(b))
	}
	div := uint64(binary.BigEndian.Uint16(b[12:]))
	ntrk := int(binary.BigEndian.Uint16(b[10:]))
	p := 8 + int(binary.BigEndian.Uint32(b[4:]))
	var tempos []tempoEv
	var endTick, notes uint64
	for t := 0; t < ntrk && p+8 <= len(b); t++ {
		ln := int(binary.BigEndian.Uint32(b[p+4:]))
		body := b[p+8 : p+8+ln]
		p += 8 + ln
		var tick uint64
		var run byte
		q := 0
		vl := func() uint64 {
			var v uint64
			for {
				c := body[q]
				q++
				v = v<<7 | uint64(c&0x7f)
				if c&0x80 == 0 {
					return v
				}
			}
		}
		for q < len(body) {
			tick += vl()
			st := body[q]
			if st < 0x80 {
				st = run
			} else {
				q++
				if st < 0xf0 {
					run = st
				}
			}
			switch {
			case st == 0xff:
				mt := body[q]
				q++
				l := int(vl())
				d := body[q : q+l]
				q += l
				if mt == 0x51 && l == 3 {
					tempos = append(tempos, tempoEv{tick, uint64(d[0])<<16 | uint64(d[1])<<8 | uint64(d[2])})
				}
				if mt == 0x2f {
					q = len(body)
				}
			case st == 0xf0 || st == 0xf7:
				q += int(vl())
			case st>>4 == 0xc || st>>4 == 0xd:
				q++
			default:
				if st>>4 == 0x9 && body[q+1] != 0 {
					notes++
				}
				q += 2
			}
		}
		if tick > endTick {
			endTick = tick
		}
	}
	sort.SliceStable(tempos, func(i, j int) bool { return tempos[i].tick < tempos[j].tick })
	// 逐段：每段 Δtick × 速度 ÷ division 微秒
	var us float64
	cur, last := uint64(500000), uint64(0)
	for _, tp := range tempos {
		us += float64(tp.tick-last) * float64(cur) / float64(div)
		last, cur = tp.tick, tp.us
	}
	us += float64(endTick-last) * float64(cur) / float64(div)
	return fmt.Sprintf("%s\t%d\t%d\t%d\t%d\t%.3f", name, len(b), ntrk, notes, endTick, us/1e6)
}

func main() {
	fmt.Println("name\tbytes\ttracks\tnotes\tend_tick\tseconds")
	files := os.Args[1:]
	sort.Strings(files)
	for _, f := range files {
		fmt.Println(sum(f))
	}
}
