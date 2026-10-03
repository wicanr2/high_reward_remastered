// midiinfo 列出 MID 檔的結構摘要與 SOUND_E.PCM 的切片統計，只讀、只輸出文字。
// 證據用途：docs/re/018。不輸出任何檔案內容的副本，只輸出計數與統計。
//
//	tools/music/run.sh midiinfo /orig/*.MID
package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type track struct {
	events       int
	bytes        int
	notes        int
	lo, hi       int         // 音高範圍（ch10 以外）
	drums        map[int]int // ch10 的 note number 次數
	active       map[int]int // channel<<8|note -> 開啟數
	poly, maxPol int
	bends        int
	vels         map[int]int // 力度 -> 次數
	cc7          []int       // 控制器 7 的值（依序）
	texts        map[string]int // meta 04 樂器名與 meta 01 文字的次數
	endAbs       uint64
	channels     map[int]int
	programs     map[int][]int // channel -> program changes in order
	ccs          map[int]int
	metas        map[int]int
	sysex        []string
	tempos       []int
	name         string
	markers      []string
	runningStart int
}

func vlq(b []byte, p *int) (uint32, bool) {
	var v uint32
	for i := 0; i < 4; i++ {
		if *p >= len(b) {
			return 0, false
		}
		c := b[*p]
		*p++
		v = v<<7 | uint32(c&0x7f)
		if c&0x80 == 0 {
			return v, true
		}
	}
	return v, false
}

func analyze(path string) {
	b, err := os.ReadFile(path)
	name := filepath.Base(path)
	if err != nil {
		fmt.Printf("%s\tERR %v\n", name, err)
		return
	}
	if len(b) == 0 {
		fmt.Printf("%s\tsize=0\n", name)
		return
	}
	if len(b) < 14 || string(b[:4]) != "MThd" {
		fmt.Printf("%s\tsize=%d\t非 MThd 開頭：% x\n", name, len(b), b[:min(8, len(b))])
		return
	}
	hl := binary.BigEndian.Uint32(b[4:])
	format := binary.BigEndian.Uint16(b[8:])
	ntrk := binary.BigEndian.Uint16(b[10:])
	div := binary.BigEndian.Uint16(b[12:])
	fmt.Printf("%s\tsize=%d\tMThd len=%d format=%d tracks=%d division=%#04x(%d)\n", name, len(b), hl, format, ntrk, div, div)
	p := 8 + int(hl)
	ti := 0
	for p+8 <= len(b) {
		id := string(b[p : p+4])
		ln := int(binary.BigEndian.Uint32(b[p+4:]))
		body := b[p+8:]
		trunc := ""
		if ln > len(body) {
			trunc = fmt.Sprintf(" 截斷:宣告%d實有%d", ln, len(body))
			ln = len(body)
		}
		body = body[:ln]
		if id != "MTrk" {
			fmt.Printf("  chunk %q len=%d（非 MTrk）\n", id, ln)
			p += 8 + ln
			continue
		}
		t := &track{channels: map[int]int{}, programs: map[int][]int{}, ccs: map[int]int{}, metas: map[int]int{}, drums: map[int]int{}, active: map[int]int{}, vels: map[int]int{}, texts: map[string]int{}}
		q := 0
		var abs uint64
		var run byte
		ok := true
		for q < len(body) {
			dt, good := vlq(body, &q)
			if !good {
				ok = false
				break
			}
			abs += uint64(dt)
			if q >= len(body) {
				ok = false
				break
			}
			st := body[q]
			if st < 0x80 {
				if run == 0 {
					ok = false
					break
				}
				st = run
			} else {
				q++
				if st < 0xf0 {
					run = st
				}
			}
			t.events++
			switch {
			case st == 0xff:
				if q >= len(body) {
					ok = false
					break
				}
				mt := body[q]
				q++
				l, good := vlq(body, &q)
				if !good || q+int(l) > len(body) {
					ok = false
					break
				}
				d := body[q : q+int(l)]
				q += int(l)
				t.metas[int(mt)]++
				switch mt {
				case 0x51:
					if len(d) == 3 {
						t.tempos = append(t.tempos, int(d[0])<<16|int(d[1])<<8|int(d[2]))
					}
				case 0x01, 0x04:
					t.texts[fmt.Sprintf("meta%02X:%q", mt, string(d))]++
				case 0x03:
					t.name = string(d)
				case 0x06, 0x07:
					if len(t.markers) < 6 {
						t.markers = append(t.markers, fmt.Sprintf("%d:%q@%d", mt, string(d), abs))
					}
				}
				if mt == 0x2f {
					t.endAbs = abs
					q = len(body)
				}
			case st == 0xf0 || st == 0xf7:
				l, good := vlq(body, &q)
				if !good || q+int(l) > len(body) {
					ok = false
					break
				}
				d := body[q : q+int(l)]
				q += int(l)
				if len(t.sysex) < 4 {
					t.sysex = append(t.sysex, fmt.Sprintf("%d bytes % x", len(d), d[:min(len(d), 12)]))
				}
			default:
				ch := int(st & 15)
				switch st >> 4 {
				case 0x8, 0xa, 0xb, 0xe:
					if q+2 > len(body) {
						ok = false
						break
					}
					switch st >> 4 {
					case 0xb:
						t.ccs[int(body[q])]++
						if body[q] == 7 {
							t.cc7 = append(t.cc7, int(body[q+1]))
						}
					case 0xe:
						t.bends++
					case 0x8:
						k := ch<<8 | int(body[q])
						if t.active[k] > 0 {
							t.active[k]--
							t.poly--
						}
					}
					t.channels[ch]++
					q += 2
				case 0x9:
					if q+2 > len(body) {
						ok = false
						break
					}
					if body[q+1] != 0 {
						t.notes++
						t.vels[int(body[q+1])]++
						n := int(body[q])
						if ch == 9 {
							t.drums[n]++
						} else {
							if t.lo == 0 || n < t.lo {
								t.lo = n
							}
							if n > t.hi {
								t.hi = n
							}
						}
						t.active[ch<<8|n]++
						t.poly++
						if t.poly > t.maxPol {
							t.maxPol = t.poly
						}
					} else {
						k := ch<<8 | int(body[q])
						if t.active[k] > 0 {
							t.active[k]--
							t.poly--
						}
					}
					t.channels[ch]++
					q += 2
				case 0xc:
					if q+1 > len(body) {
						ok = false
						break
					}
					t.programs[ch] = append(t.programs[ch], int(body[q]))
					t.channels[ch]++
					q++
				case 0xd:
					if q+1 > len(body) {
						ok = false
						break
					}
					t.channels[ch]++
					q++
				default:
					ok = false
				}
			}
			if !ok {
				break
			}
		}
		fmt.Printf("  MTrk#%d len=%d events=%d notes=%d endTick=%d解析=%v%s name=%q\n", ti, ln, t.events, t.notes, t.endAbs, ok, trunc, t.name)
		var chs []int
		for c := range t.channels {
			chs = append(chs, c)
		}
		sort.Ints(chs)
		var parts []string
		for _, c := range chs {
			parts = append(parts, fmt.Sprintf("ch%d:%d事件 prog%v", c+1, t.channels[c], t.programs[c]))
		}
		fmt.Printf("    %s\n", strings.Join(parts, "  "))
		var ccl []int
		for c := range t.ccs {
			ccl = append(ccl, c)
		}
		sort.Ints(ccl)
		var cs []string
		for _, c := range ccl {
			cs = append(cs, fmt.Sprintf("CC%d×%d", c, t.ccs[c]))
		}
		var ml []int
		for c := range t.metas {
			ml = append(ml, c)
		}
		sort.Ints(ml)
		var ms []string
		for _, c := range ml {
			ms = append(ms, fmt.Sprintf("meta%02X×%d", c, t.metas[c]))
		}
		fmt.Printf("    控制器 %s | meta %s | 速度 %v | sysex %v | 標記 %v\n", strings.Join(cs, " "), strings.Join(ms, " "), t.tempos, t.sysex, t.markers)
		var dn []int
		for n := range t.drums {
			dn = append(dn, n)
		}
		sort.Ints(dn)
		var ds []string
		for _, n := range dn {
			ds = append(ds, fmt.Sprintf("%d×%d", n, t.drums[n]))
		}
		fmt.Printf("    音高 %d..%d 最大同時發聲 %d 彎音 %d 鼓 %s\n", t.lo, t.hi, t.maxPol, t.bends, strings.Join(ds, " "))
		var vk []int
		for v := range t.vels {
			vk = append(vk, v)
		}
		sort.Ints(vk)
		var vs []string
		for _, v := range vk {
			vs = append(vs, fmt.Sprintf("%d×%d", v, t.vels[v]))
		}
		var tk []string
		for k, n := range t.texts {
			tk = append(tk, fmt.Sprintf("%s×%d", k, n))
		}
		sort.Strings(tk)
		fmt.Printf("    力度 %s | CC7 值 %v | 文字 %s\n", strings.Join(vs, " "), t.cc7, strings.Join(tk, " "))
		p += 8 + ln
		ti++
	}
	if p != len(b) {
		fmt.Printf("  尾端剩 %d bytes（偏移 %d）\n", len(b)-p, p)
	}
}

func pcm(path string, offs []int) {
	b, err := os.ReadFile(path)
	if err != nil {
		fmt.Println("ERR", err)
		return
	}
	fmt.Printf("%s size=%d 前 8 bytes % x\n", filepath.Base(path), len(b), b[:8])
	if len(b) >= 4 {
		fmt.Printf("前 4 bytes 當 uint32 LE = %d(%#x)，當 uint16 LE = %d\n", binary.LittleEndian.Uint32(b), binary.LittleEndian.Uint32(b), binary.LittleEndian.Uint16(b))
	}
	for i := 0; i+1 < len(offs); i++ {
		s, e := offs[i], offs[i+1]
		seg := b[min(s, len(b)):min(e, len(b))]
		var lo, hi, sum int = 255, 0, 0
		for _, v := range seg {
			if int(v) < lo {
				lo = int(v)
			}
			if int(v) > hi {
				hi = int(v)
			}
			sum += int(v)
		}
		mean := 0.0
		if len(seg) > 0 {
			mean = float64(sum) / float64(len(seg))
		}
		fmt.Printf("  切片%d [%d,%d) len=%d min=%d max=%d mean=%.1f 首尾 % x … % x\n", i, s, e, len(seg), lo, hi, mean, seg[:min(4, len(seg))], seg[max(0, len(seg)-4):])
	}
	// 最後一個位移之後
	if n := len(offs); n > 0 && offs[n-1] < len(b) {
		seg := b[offs[n-1]:]
		fmt.Printf("  最後位移 %d 之後 %d bytes：% x\n", offs[n-1], len(seg), seg[:min(16, len(seg))])
	}
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "usage: midiinfo midi <files...> | pcm <file> <offsets...>")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "midi":
		for _, f := range os.Args[2:] {
			analyze(f)
		}
	case "pcm":
		var offs []int
		for _, s := range os.Args[3:] {
			var v int
			fmt.Sscanf(s, "%d", &v)
			offs = append(offs, v)
		}
		pcm(os.Args[2], offs)
	}
}
