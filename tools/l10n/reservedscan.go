// Local L2 evidence prototype. Outputs code values and source IDs, never text.
package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"

	"github.com/wicanr2/dosgolem/apps/hr/l10n"
)

var dataNames = []string{"COUNTRY.MES", "SP.MES", "SYSTEM.MES", "UWASA.MES", "POWERMES.MES", "ESPMES.MRG", "SHOPTAB.TBL"}
var exeNames = []string{"MAIN.EXE", "OP.EXE", "END.EXE"}

type sourceStats struct {
	SHA256          string `json:"sha256"`
	Items           int    `json:"items,omitempty"`
	StringRows      int    `json:"string_rows,omitempty"`
	LooseRuns       int    `json:"loose_runs,omitempty"`
	ScannedSegments int    `json:"scanned_segments,omitempty"`
	SkippedSegments int    `json:"skipped_segments,omitempty"`
	Pairs           int    `json:"pairs"`
}

type inventoryItem struct {
	size   int
	sha256 string
}

type overlayAudit struct {
	InputSHA256 string              `json:"input_sha256"`
	Segments    []json.RawMessage   `json:"segments"`
	Codes       map[string][]string `json:"codes"`
}

func loadInventory(path string) map[string]inventoryItem {
	rows, err := readTSV(path)
	must(err)
	if len(rows) == 0 || len(rows[0]) < 3 || rows[0][0] != "path" || rows[0][2] != "sha256" {
		panic("bad source inventory")
	}
	out := make(map[string]inventoryItem)
	for _, row := range rows[1:] {
		if len(row) < 3 {
			panic("short inventory row")
		}
		size, err := strconv.Atoi(row[1])
		must(err)
		out[row[0]] = inventoryItem{size, row[2]}
	}
	return out
}

func checkInput(name string, b []byte, inventory map[string]inventoryItem) string {
	item, ok := inventory[name]
	if !ok {
		panic("missing inventory entry: " + name)
	}
	digest := fmt.Sprintf("%x", sha256.Sum256(b))
	if len(b) != item.size || digest != item.sha256 {
		panic("input differs from source inventory: " + name)
	}
	return digest
}

func isLead(b byte) bool  { return b >= 0xA1 && b <= 0xF9 }
func isTrail(b byte) bool { return b >= 0x40 && b <= 0x7E || b >= 0xA1 && b <= 0xFE }
func inCustomRange(code uint16) bool {
	a, b := byte(code>>8), byte(code)
	return a >= 0xE0 && a <= 0xF9 && (b >= 0x40 && b <= 0x7E || b >= 0xA1 && b <= 0xDF)
}

func add(set map[uint16]map[string]bool, code uint16, source string) {
	if !inCustomRange(code) {
		return
	}
	if set[code] == nil {
		set[code] = make(map[string]bool)
	}
	set[code][source] = true
}

// Always advance by two after an accepted Big5 pair. This preserves alignment.
func alignedPairs(b []byte, source string, set map[uint16]map[string]bool) int {
	n := 0
	for i := 0; i < len(b); {
		if isLead(b[i]) && i+1 < len(b) && isTrail(b[i+1]) {
			add(set, uint16(b[i])<<8|uint16(b[i+1]), source)
			n++
			i += 2
		} else {
			i++
		}
	}
	return n
}

func readTSV(path string) ([][]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	r.Comma = '\t'
	r.FieldsPerRecord = -1
	return r.ReadAll()
}

// Mirror tools/text/loose.go: only UNK data segments and runs with >=2 pairs.
func loosePairs(b []byte, source string, set map[uint16]map[string]bool) (int, int) {
	count, runs := 0, 0
	for i := 0; i < len(b); {
		if !(isLead(b[i]) && i+1 < len(b) && isTrail(b[i+1])) {
			i++
			continue
		}
		start := i
		pairs := make([]uint16, 0, 8)
		for i < len(b) {
			if isLead(b[i]) && i+1 < len(b) && isTrail(b[i+1]) {
				pairs = append(pairs, uint16(b[i])<<8|uint16(b[i+1]))
				i += 2
			} else if b[i] >= 0x20 && b[i] <= 0x7E || b[i] == 0x0A {
				i++
			} else {
				break
			}
		}
		if len(pairs) >= 2 {
			for _, code := range pairs {
				add(set, code, source)
			}
			count += len(pairs)
			runs++
		}
		if i == start {
			i++
		}
	}
	return count, runs
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}

func selfCheck() {
	set := make(map[uint16]map[string]bool)
	alignedPairs([]byte{0xA1, 0xE0, 0x40, 0xE0, 0xA1}, "fixture", set)
	if set[0xE040] != nil || set[0xE0A1] == nil {
		panic("misaligned Big5 pair")
	}
	set = make(map[uint16]map[string]bool)
	loosePairs([]byte{0xE0, 0x40}, "fixture", set)
	if len(set) != 0 {
		panic("isolated pair accepted as loose run")
	}
	loosePairs([]byte{0xE0, 0x40, 'A', 0xE0, 0xA1}, "fixture", set)
	if set[0xE040] == nil || set[0xE0A1] == nil {
		panic("valid loose run missed")
	}
}

func main() {
	selfCheck()
	const orig = "/orig"
	const ida = "/ida"
	const out = "/out"
	imageID := os.Getenv("HR_IMAGE_ID")
	if imageID == "" {
		panic("missing Docker image ID; use reservedscan.sh")
	}
	inventory := loadInventory("/inventory/source-inventory.tsv")
	reserved := make(map[uint16]map[string]bool)
	stats := make(map[string]*sourceStats)
	idaExports := make(map[string]string)
	for _, name := range dataNames {
		b, err := os.ReadFile(filepath.Join(orig, name))
		must(err)
		digest := checkInput(name, b, inventory)
		f, err := l10n.Parse(name, b)
		must(err)
		s := &sourceStats{SHA256: digest, Items: len(f.Items)}
		for _, item := range f.Items {
			s.Pairs += alignedPairs(item.Orig, "data:"+name, reserved)
		}
		stats[name] = s
	}
	for _, name := range exeNames {
		b, err := os.ReadFile(filepath.Join(orig, name))
		must(err)
		digest := checkInput(name, b, inventory)
		if len(b) < 0x1C || string(b[:2]) != "MZ" {
			panic("not MZ: " + name)
		}
		header := int(binary.LittleEndian.Uint16(b[8:10])) * 16
		limit := len(b)
		if name == "MAIN.EXE" {
			limit = 361856
		} // FBOV starts here; its IDA linear address is not a flat file offset.
		prefix := "str"
		if name == "OP.EXE" {
			prefix = "str-OP"
		}
		if name == "END.EXE" {
			prefix = "str-END"
		}
		for _, suffix := range []string{".tsv", ".seg"} {
			path := filepath.Join(ida, prefix+suffix)
			export, err := os.ReadFile(path)
			must(err)
			idaExports[prefix+suffix] = fmt.Sprintf("%x", sha256.Sum256(export))
		}
		s := &sourceStats{SHA256: digest}
		rows, err := readTSV(filepath.Join(ida, prefix+".tsv"))
		must(err)
		for _, row := range rows[1:] {
			if len(row) < 10 {
				panic("short string row")
			}
			decoded, err := hex.DecodeString(row[9])
			must(err)
			s.Pairs += alignedPairs(decoded, "strict:"+name, reserved)
			s.StringRows++
		}
		segments, err := readTSV(filepath.Join(ida, prefix+".seg"))
		must(err)
		for _, row := range segments[1:] {
			if len(row) < 8 || row[2] != "UNK" {
				continue
			}
			size, err := strconv.Atoi(row[3])
			must(err)
			start, err := strconv.ParseInt(strings.TrimPrefix(row[7], "0x"), 16, 64)
			must(err)
			fo := int(start) - 0x10000 + header
			if fo < header || fo+size > limit {
				s.SkippedSegments++
				continue
			}
			count, runs := loosePairs(b[fo:fo+size], "loose:"+name, reserved)
			s.Pairs += count
			s.LooseRuns += runs
			s.ScannedSegments++
		}
		stats[name] = s
	}
	// IDA maps FBOV overlays into separate address spaces.  Their bytes cannot
	// be scanned at a flat MZ offset.  Include all aligned non-code candidates
	// conservatively; the recorded five runs look like 5-byte-stride pointers.
	overlayBytes, err := os.ReadFile("/overlay/ida-l2-overlay-codes-v3.json")
	must(err)
	var overlay overlayAudit
	must(json.Unmarshal(overlayBytes, &overlay))
	if overlay.InputSHA256 != stats["MAIN.EXE"].SHA256 || len(overlay.Segments) != 139 {
		panic("overlay evidence does not match MAIN.EXE or 139 overlay segments")
	}
	overlayNovel := 0
	for codeHex, locators := range overlay.Codes {
		value, err := strconv.ParseUint(codeHex, 16, 16)
		must(err)
		if len(locators) == 0 || !inCustomRange(uint16(value)) {
			panic("invalid overlay code candidate: " + codeHex)
		}
		if reserved[uint16(value)] == nil {
			overlayNovel++
		}
		for _, locator := range locators {
			add(reserved, uint16(value), "overlay-candidate:MAIN.EXE:"+locator)
		}
	}
	codes := make([]int, 0, len(reserved))
	for code := range reserved {
		codes = append(codes, int(code))
	}
	sort.Ints(codes)
	var tsv strings.Builder
	tsv.WriteString("code_hex\tsources\n")
	for _, n := range codes {
		var sources []string
		for source := range reserved[uint16(n)] {
			sources = append(sources, source)
		}
		sort.Strings(sources)
		fmt.Fprintf(&tsv, "%04X\t%s\n", n, strings.Join(sources, ","))
	}
	must(os.WriteFile(filepath.Join(out, "m10-reserved-codes.tsv"), []byte(tsv.String()), 0644))
	report := struct {
		Status              string                  `json:"status"`
		Method              string                  `json:"method"`
		Capacity            int                     `json:"capacity"`
		Reserved            int                     `json:"reserved"`
		Available           int                     `json:"available"`
		GoVersion           string                  `json:"go_version"`
		DockerImage         string                  `json:"docker_image"`
		IDA                 string                  `json:"ida_version_and_address_space"`
		IDAExports          map[string]string       `json:"ida_export_sha256"`
		OverlayExportSHA256 string                  `json:"overlay_export_sha256"`
		OverlayCandidates   int                     `json:"overlay_candidate_codes"`
		OverlayNovel        int                     `json:"overlay_novel_codes"`
		Inputs              map[string]*sourceStats `json:"inputs"`
	}{"local conservative static prototype; FBOV pointer-like candidates retained", "L1 parsed items + IDA strict aligned strings + UNK loose aligned runs + FBOV non-code candidates", 3276, len(codes), 3276 - len(codes), runtime.Version(), imageID, "IDA Pro 9.4 linear addresses; MZ file offsets only for UNK segments before MAIN FBOV", idaExports, fmt.Sprintf("%x", sha256.Sum256(overlayBytes)), len(overlay.Codes), overlayNovel, stats}
	j, err := json.MarshalIndent(report, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(out, "m10-reserved-audit.json"), append(j, '\n'), 0644))
	fmt.Printf("reserved=%d available=%d of 3276\n", report.Reserved, report.Available)
	for _, name := range append(append([]string{}, dataNames...), exeNames...) {
		fmt.Printf("%s items=%d rows=%d segments=%d skipped=%d pairs=%d\n", name, stats[name].Items, stats[name].StringRows, stats[name].ScannedSegments, stats[name].SkippedSegments, stats[name].Pairs)
	}
}
