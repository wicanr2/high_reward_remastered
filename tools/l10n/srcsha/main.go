// 開發側小工具：從原版 ESPMES.MRG 取指定項目，只輸出 src_sha256（前 16 碼）與位元組數，不輸出內容。
// 譯文表與 tools/play.sh gui-ingame 的負對照要綁定原項目雜湊；它是原版衍生值，不進版控，
// 所以由本工具在使用者的機器上算出，寫進 workplace/out/l1-wire2/src-sha-esp121-0.txt（只有 16 碼）。
//
// 容器只掛載 workplace（唯讀，容器內 /orig）與 fork（容器內 /src），所以先把本檔複製到 workplace 再執行：
//
//	mkdir -p workplace/srcsha && cp tools/l10n/srcsha/main.go workplace/srcsha/main.go
//	tools/dosgolem.sh go run /orig/srcsha/main.go ESPMES#121.0
package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/wicanr2/dosgolem/apps/hr/l10n"
)

func main() {
	dir := "/orig/orig"
	ents, err := os.ReadDir(dir)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	name := ""
	for _, e := range ents {
		if strings.EqualFold(e.Name(), "ESPMES.MRG") {
			name = e.Name()
		}
	}
	if name == "" {
		fmt.Fprintln(os.Stderr, "原版目錄沒有 ESPMES.MRG")
		os.Exit(1)
	}
	b, err := os.ReadFile(dir + "/" + name)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	f, err := l10n.Parse("ESPMES.MRG", b)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("ESPMES 項目總數 %d\n", len(f.Items))
	for _, id := range os.Args[1:] {
		it, ok := f.Lookup(id)
		if !ok {
			fmt.Printf("%s 不存在\n", id)
			continue
		}
		fmt.Printf("%s src_sha256=%s len=%d\n", id, l10n.SrcSHA(it.Orig), len(it.Orig))
	}
}
