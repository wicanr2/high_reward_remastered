// mescheck：比對 MES 偏移表與「依 NUL 切分」的項目起點。
//
//	mescheck <檔名>...
//
// 唯讀。輸出每個檔案：表偏移與 NUL 切分起點不一致的項目數、第一個不一致的項目與差值。
package main

import (
	"encoding/binary"
	"fmt"
	"os"
)

func main() {
	for _, name := range os.Args[1:] {
		d, err := os.ReadFile("/orig/" + name)
		if err != nil {
			fmt.Println(name, err)
			continue
		}
		n := int(binary.LittleEndian.Uint16(d))
		offs := make([]int, n)
		for i := range offs {
			offs[i] = int(binary.LittleEndian.Uint32(d[2+4*i:]))
		}
		// NUL 切分
		var starts []int
		pos := offs[0]
		starts = append(starts, pos)
		for pos < len(d) {
			j := pos
			for j < len(d) && d[j] != 0 {
				j++
			}
			if j >= len(d) {
				break
			}
			pos = j + 1
			if pos < len(d) && d[pos] != 0xFF {
				starts = append(starts, pos)
			} else {
				starts = append(starts, pos) // 結尾標記位置
				break
			}
		}
		mism := 0
		first := -1
		firstDelta := 0
		maxd, mind := 0, 0
		cmp := n
		if len(starts) < cmp {
			cmp = len(starts)
		}
		for i := 0; i < cmp; i++ {
			dlt := offs[i] - starts[i]
			if dlt != 0 {
				mism++
				if first < 0 {
					first = i
					firstDelta = dlt
				}
				if dlt > maxd {
					maxd = dlt
				}
				if dlt < mind {
					mind = dlt
				}
			}
		}
		fmt.Printf("%s: 表偏移數=%d NUL切分起點數=%d 不一致=%d 首個不一致項目=%d 差值=%d 差值範圍[%d,%d] 檔尾位元組=%02X 檔長=%d\n",
			name, n, len(starts), mism, first, firstDelta, mind, maxd, d[len(d)-1], len(d))
	}
}
