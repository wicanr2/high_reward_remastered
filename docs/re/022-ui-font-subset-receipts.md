# 022 前端介面字型子集的收據

日期：2026-10-03
狀態：收據（`docs/spec/006` 第 6 節與第 10 節的實跑證據）。規格仍是 DRAFT；這裡只記錄實際量到的結果。
輸入：`NotoSansCJK-Regular.ttc` SHA-256 `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`，19,484,784 bytes，Debian 套件 `fonts-noto-cjk 1:20230817+repack1-3`，授權 SIL OFL 1.1。

## 1. 子集產生（`tools/gen_ui_fonts.sh`）

重跑：`tools/gen_ui_fonts.sh`（容器內；約 1 分鐘）。腳本前置檢查全部通過：TTC 的 SHA-256、映像 ID、fontTools 版本、`gen-charset` 輸出含 `PASS`、五份字元表時間戳更新、五份子集無 GSUB／GPOS 且 name ID 0、7、13、14 存在、`OFL.txt` 含 "SIL OPEN FONT LICENSE Version 1.1" 且不含 "GNU General Public License"。連跑兩次，產物雜湊相同（可重現）。

| 項目 | 值 |
|---|---|
| 容器映像 | `yuan-analysis:1`，ID `sha256:f9ea24396753f49d4c215763aa8726755041f0b523f93c9bdbffd76b8e358fca`（另一個專案的映像，歸屬未驗證，唯讀使用，腳本鎖定 ID） |
| fontTools | 4.66.1 |
| 旗標 | `--layout-features= --drop-tables+=GSUB,GPOS --no-hinting --notdef-outline --name-IDs=0,7,13,14 --legacy-kern --recalc-bounds` |
| 子集的表（五份相同） | BASE、CFF、OS/2、VORG、cmap、head、hhea、hmtx、maxp、name、post、vhea、vmtx（13 張，沒有 GSUB、GPOS、kern） |
| 字元數 | zh-TW 205、zh-CN 206、ko 212、en 101、ja 232 |

| 檔案 | 大小（bytes） | SHA-256 |
|---|---:|---|
| `ui-zh-TW.otf` | 32,696 | `d16146487d2eadeec55d120d12d2157d40a51e00d50b40c088e1ab9e377f0d0f` |
| `ui-zh-CN.otf` | 28,684 | `2c9caa25fcf3525c45a1a03ba18aaee1b3ee70c8a6aed6297146b9c78aa63d88` |
| `ui-ko.otf` | 21,184 | `7e028b59f17b04c504e1186c2e50d3b98acd986b8f0d40361e21652788a7694f` |
| `ui-en.otf` | 9,884 | `b5e55701b906b7b0ad0b52fe82edc71d2d07a55f0e71c5effb6aacdfc7995dbf` |
| `ui-ja.otf` | 30,076 | `bba2aa5d55a1b8dc1c573ae0d36a51ac355a76e466a3abfcd71fcd9cf4cf132b` |
| `OFL.txt`（97 行） | | `f47ac356aaafd53b53c6c784b3d63e265bf2dc9fe452d4ba5aee4b9b0bf51ca8` |
| `SOURCE.txt` | | `be3d1f86d3aedff8485efdaa1b6ccfadc876e06e93fcb01cc29907da69c5eae0` |

總大小 122,524 bytes。`OFL.txt` 只含 OFL 1.1 段（97 行），不含 Debian `copyright` 檔 `debian/*` 的 GPL-3+ 段。字型內嵌的版權行是 name ID 0「© 2014-2021 Adobe」。

## 2. 字形墨跡測試（`x/image` 能否畫出 CID 型 CFF 子集）

重跑：`HR_VERBOSE=1 HR_TEST_RUN='Fonts' tools/play.sh test-play`（`apps/hr/play/fonts_test.go`；日誌 `workplace/out/test-fonts.log`）。

| 測試 | 結果 |
|---|---|
| `TestFontsEveryCharHasInk` | 通過：五份子集的每個非空白字元（205、206、212、101、232 個）`face.Glyph` 回 ok 且遮罩有墨跡；控制組：空白（含 U+3000）ok 但沒有墨跡。第一次執行只有 U+3000 沒有墨跡，是測試的空白例外漏了它，不是字型問題 |
| `TestFontsMissingGlyphIsDetected` | 通過：不在子集內的 U+9F98 在五份子集都是 `GlyphIndex ＝ 0`、`Glyph` 回 `ok＝false` |
| `TestFontsProportionalLatinAndMetrics` | 通過：五份子集的 `GlyphAdvance('i')` 不等於 `GlyphAdvance('W')`；`Metrics().Height` 在 31.7 至 32.0 之間（約 31.86） |
| `TestFontsNoLayoutTablesAndKernZero` | 通過：檔頭 `OTTO`、表目錄（測試自己解析）沒有 GSUB、GPOS、kern，必要的表都在；`Kern` 對 AV、To、Wa、fi 恆為 0 |
| `TestFontsNameIDsPresent` | 通過：name ID 0、7、13、14 都存在 |

結論（confirmed）：`golang.org/x/image` v0.31.0 的 `opentype` 能實際畫出這五份 Noto Sans CJK 子集的全部字元，字型方案成立。`apps/hr/play/go.mod`、`go.sum` 因此新增 `golang.org/x/image`（離線自建置映像的模組快取補入）。

## 3. 建置映像內的模組與授權檔

`eob-remake-go:1.26.7-ebiten2.9.9` 的 `/go/pkg/mod`：`golang.org/x/image@v0.31.0`、`golang.org/x/text@v0.29.0`（各有 `LICENSE`），`cache/download` 下有對應的 `.mod`、`.zip`、`.ziphash`。`go env`：`GOMODCACHE=/go/pkg/mod`、`GOPROXY=https://proxy.golang.org,direct`（測試時以 `GOPROXY=off` 離線）。`workplace/gomodcache` 也有同版本。

## 4. 上游授權

上游 `notofonts/noto-cjk` 的 `Sans/LICENSE`（2026-10-03，WebFetch 讀取，是摘要結果，原檔未保存）：首句 "This Font Software is licensed under the SIL Open Font License, Version 1.1"，沒有宣告 Reserved Font Name。與 Debian `copyright` 檔、TTC 全檔（ASCII 與 UTF-16BE 都找過）的結果一致。等級：強推論；發行前以原檔再核對一次。
