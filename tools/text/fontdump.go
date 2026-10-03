// fontdump：檢查字模來源（只讀，容器內執行）。
//
//	fontdump ascii           MAIN.EXE 內嵌 8x16 半形字模（IDA 段 361B 偏移 0x22 起，每字 16 bytes）轉 PNG 與文字統計
//	fontdump cfont           CFONT.15 依 MAIN.EXE 公式（287C:05A2）涵蓋統計：各 Big5 區的非空字模數
//	fontdump sheet <lead起> <lead迄>   把指定 lead 範圍的字模排成 PNG（每 lead 一列，trail 40-7E 與 A1-FE 共 157 格）
//
// 輸出在 /out/font-*.png 與標準輸出。內容是原版字模，只放 workplace。
package main

import (
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"
	"strconv"
)

// 與 docs/re/006 第 8 節、287C:05A2 相同的字號公式。
func glyphIndex(lead, trail int) int {
	t := trail - 0x62
	if trail <= 0x7E {
		t = trail - 0x40
	}
	switch {
	case lead <= 0xA3:
		return (lead-0xA1)*157 + t
	case (lead == 0xC6 && trail >= 0xA1) || (lead > 0xC6 && lead <= 0xC8):
		return (lead-0xC6)*157 + t - 0x3F + 0x198
	default:
		x := (lead-0xA4)*157 + t
		if lead >= 0xC9 {
			x -= 0x198
		}
		return x + 0x305
	}
}

func savePNG(path string, img image.Image) {
	f, err := os.Create(path)
	if err != nil {
		fmt.Println(err)
		return
	}
	defer f.Close()
	png.Encode(f, img)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "用法: fontdump ascii | cfont | sheet <lead起> <lead迄>")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ascii":
		exe, _ := os.ReadFile("/orig/MAIN.EXE")
		base := 0x361B0 - 0x10000 + 18944 + 0x22
		n := 85
		cols, scale := 17, 4
		img := image.NewGray(image.Rect(0, 0, cols*10*scale, ((n+cols-1)/cols)*18*scale))
		for y := range img.Pix {
			img.Pix[y] = 255
		}
		blank := 0
		for i := 0; i < n; i++ {
			g := exe[base+16*i : base+16*i+16]
			nz := false
			for _, b := range g {
				if b != 0 {
					nz = true
				}
			}
			if !nz {
				blank++
			}
			ox, oy := (i%cols)*10*scale, (i/cols)*18*scale
			for r := 0; r < 16; r++ {
				for c := 0; c < 8; c++ {
					if g[r]&(0x80>>c) != 0 {
						for dy := 0; dy < scale; dy++ {
							for dx := 0; dx < scale; dx++ {
								img.SetGray(ox+c*scale+dx, oy+r*scale+dy, color.Gray{0})
							}
						}
					}
				}
			}
		}
		savePNG("/out/font-ascii.png", img)
		fmt.Printf("內嵌半形字模：檔案位移 %#x，%d 格，全空 %d 格；PNG 每列 %d 格，格 i 對應字元碼 i+46（0x2E 起）\n", base, n, blank, cols)
		// 列出全空格的字元碼（可印範圍內）
		fmt.Print("全空格對應字元碼：")
		for i := 0; i < n; i++ {
			g := exe[base+16*i : base+16*i+16]
			z := true
			for _, b := range g {
				if b != 0 {
					z = false
				}
			}
			if z {
				fmt.Printf(" 0x%02X", i+46)
			}
		}
		fmt.Println()
	case "cfont":
		cf, _ := os.ReadFile("/orig/CFONT.15")
		type reg struct {
			name string
			f    func(l, t int) bool
		}
		regs := []reg{
			{"A1-A3 符號", func(l, t int) bool { return l >= 0xA1 && l <= 0xA3 }},
			{"A4-C5 常用字", func(l, t int) bool { return l >= 0xA4 && l <= 0xC5 }},
			{"C6 40-7E 常用字尾", func(l, t int) bool { return l == 0xC6 && t <= 0x7E }},
			{"C6A1-C8FE 擴充區", func(l, t int) bool { return (l == 0xC6 && t >= 0xA1) || l == 0xC7 || l == 0xC8 }},
			{"C9-F9 次常用字", func(l, t int) bool { return l >= 0xC9 && l <= 0xF9 }},
		}
		tot := make([]int, len(regs))
		nz := make([]int, len(regs))
		oob := 0
		for l := 0xA1; l <= 0xF9; l++ {
			for t := 0x40; t <= 0xFE; t++ {
				if t > 0x7E && t < 0xA1 {
					continue
				}
				i := glyphIndex(l, t)
				for k, r := range regs {
					if r.f(l, t) {
						tot[k]++
						if i < 0 || (i+1)*30 > len(cf) {
							oob++
							break
						}
						g := cf[i*30 : i*30+30]
						for _, b := range g {
							if b != 0 {
								nz[k]++
								break
							}
						}
					}
				}
			}
		}
		fmt.Printf("CFONT.15 大小=%d，字模數=%d（每字 30 bytes）\n", len(cf), len(cf)/30)
		for k, r := range regs {
			fmt.Printf("  %-18s 碼位 %5d，非空字模 %5d\n", r.name, tot[k], nz[k])
		}
		fmt.Printf("  公式算出超出檔案範圍的碼位=%d\n", oob)
		// lead 0x94 的情形（ESPMES 內出現的 94 FC）
		for _, tr := range []int{0xFC} {
			l := 0x94
			fmt.Printf("  lead=0x%02X trail=0x%02X 依 287C:05A2（lead<=A3 的分支）算出的字號=%d（負值＝檔案開頭之前）\n", l, tr, glyphIndex(l, tr))
		}
	case "sheet":
		a, _ := strconv.ParseInt(os.Args[2], 16, 32)
		b, _ := strconv.ParseInt(os.Args[3], 16, 32)
		cf, _ := os.ReadFile("/orig/CFONT.15")
		rows := int(b-a) + 1
		scale := 1
		img := image.NewGray(image.Rect(0, 0, 157*17*scale, rows*17*scale))
		for y := range img.Pix {
			img.Pix[y] = 255
		}
		for ri := 0; ri < rows; ri++ {
			l := int(a) + ri
			col := 0
			for t := 0x40; t <= 0xFE; t++ {
				if t > 0x7E && t < 0xA1 {
					continue
				}
				i := glyphIndex(l, t)
				if i >= 0 && (i+1)*30 <= len(cf) {
					g := cf[i*30 : i*30+30]
					for r := 0; r < 15; r++ {
						w := int(g[2*r])<<8 | int(g[2*r+1])
						for c := 0; c < 16; c++ {
							if w&(0x8000>>c) != 0 {
								img.SetGray(col*17*scale+c*scale, ri*17*scale+r*scale, color.Gray{0})
							}
						}
					}
				}
				col++
			}
		}
		out := fmt.Sprintf("/out/font-sheet-%02X-%02X.png", a, b)
		savePNG(out, img)
		fmt.Println("寫出", out)
	}
}
