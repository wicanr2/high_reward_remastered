// Research-only independent L1 budget/1676 check of DRAFT English output.
// Input and receipts stay in workplace; this never serializes a language pack.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wicanr2/dosgolem/apps/hr/l10n"
	"github.com/wicanr2/dosgolem/apps/hr/l10n/budget"
)

type entry struct {
	ID        string `json:"id"`
	File      string `json:"file"`
	Synthetic bool   `json:"synthetic"`
	OrigHex   string `json:"orig_hex"`
	TransHex  string `json:"trans_hex"`
}

func main() {
	if len(os.Args) != 4 {
		panic("enpair_budgetcheck <orig-dir> <cases.json> <receipt.json>")
	}
	input, err := os.ReadFile(os.Args[2])
	if err != nil {
		panic(err)
	}
	var entries []entry
	if err := json.Unmarshal(input, &entries); err != nil {
		panic(err)
	}
	if len(entries) == 0 {
		panic("empty cases")
	}
	expected := map[string]string{
		"ESPMES.MRG": "e7cd0398746fafe9a0ba8b4c07de16662983b5071fa88595a48700fed22994d3",
		"SP.MES":     "f88fed9bbd525c5fb0972b2ef58718a59615b6fc92721c2ab83c5bd1cdd24b0c",
	}
	files := map[string]*l10n.File{}
	for name, want := range expected {
		data, err := os.ReadFile(filepath.Join(os.Args[1], name))
		if err != nil {
			panic(err)
		}
		if fmt.Sprintf("%x", sha256.Sum256(data)) != want {
			panic("original hash mismatch: " + name)
		}
		f, err := l10n.Parse(name, data)
		if err != nil {
			panic(err)
		}
		files[name] = f
	}
	reports := []map[string]any{}
	failed := 0
	seen := map[string]bool{}
	for _, e := range entries {
		if seen[e.ID] {
			panic("duplicate case id")
		}
		seen[e.ID] = true
		trans, err := hex.DecodeString(e.TransHex)
		if err != nil {
			panic(err)
		}
		var orig []byte
		class := "none"
		if e.Synthetic {
			orig, err = hex.DecodeString(e.OrigHex)
			if err != nil {
				panic(err)
			}
		} else {
			if e.OrigHex != "" {
				panic("real case cannot supply replacement original")
			}
			f := files[e.File]
			if f == nil {
				panic("unsupported original file")
			}
			item, ok := f.Lookup(e.ID)
			if !ok {
				panic("unknown original item")
			}
			orig = item.Orig
			if e.File == "ESPMES.MRG" {
				class, ok = l10n.ESPWindowClass(e.ID)
				if !ok {
					panic("missing original window class")
				}
			}
		}
		vs := budget.Check(budget.Input{ID: e.ID, File: e.File, Class: class, Orig: orig, Trans: trans})
		if len(vs) > 0 {
			failed++
		}
		reports = append(reports, map[string]any{"id": e.ID, "synthetic": e.Synthetic, "bytes": len(trans), "violations": vs})
	}
	receipt := map[string]any{"status": "DRAFT independent L1 budget and 1676 check; not a pack", "go_version": runtime.Version(),
		"original_sha256": expected, "fixture_sha256": fmt.Sprintf("%x", sha256.Sum256(input)),
		"cases": len(entries), "failed": failed, "results": reports}
	data, err := json.MarshalIndent(receipt, "", "  ")
	if err != nil {
		panic(err)
	}
	if err := os.WriteFile(os.Args[3], append(data, '\n'), 0644); err != nil {
		panic(err)
	}
	fmt.Printf("cases=%d failed=%d\n", len(entries), failed)
	if failed != 0 {
		os.Exit(1)
	}
}
