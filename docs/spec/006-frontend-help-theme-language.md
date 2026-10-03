# 006 前端：F1 功能說明、F2 切換 theme、F3 聲音開關、F4 切換介面語言

狀態：READY（2026-10-04，第七版）
審查：審查 A（唯讀）審第一版（報告 `workplace/spec-review/006-review-A.md`，不進版控）：阻擋 B1 至 B5、建議 S1 至 S13。重審（`006-rereview.md`）審第二版：新阻擋 2 個與 R1 至 R10。第三輪（`006-rereview2.md`）審第三版：阻擋 B1（字型腳本斷言與產物不符、授權檔夾帶 GPL 段）與 B2（`Compose` 快照測試仍可能空轉）、建議 R1 至 R13。第四版處理全部。第四輪（`006-rereview3.md`）審第四版：阻擋 B1（`HoldAdapt` 的計數式語意擋不住降頻，需視窗規則）與 B2（`hdView` 世代測試沒有決定性控制點與負對照）、建議 R1 至 R13。第五版處理全部。第五輪（`006-rereview4.md`）審第五版：阻擋 B1（`hdView` 世代測試的順序測試與負對照寫不出來）與 B2（切換序列沒有恢復暫停中的 `hdView`）、建議 R1 至 R8。第六版處理全部。第六輪（`006-rereview5.md`）審第六版：阻擋 B1（`hdView` 測試分辨不出素材 A、B，負對照無法用 `t.Run` 表達，負向斷言沒有同步點）、B2（逾時計數在計時器路徑上不會加一）、B3（離開列沒有放開 `HoldAdapt`，`original` 目標沒有完整路徑）、B4（生命週期鎖不保證 `Release` 先於新 `Preload`）、建議 R1 至 R7。第七版處理全部：B3、B4 的根源是切走時背景 `Release`，第七版改為已套用的 HD theme 常駐，整套背景 `Release` 狀態不再存在。對照見第 14 節。第七輪（`006-rereview6.md`，窄範圍）審第七版：設計面沒有阻擋，阻擋 B1（`holdGate` 案例 (6) 的不變式字面為假）與 B2（`hdView` 負對照要逐子項獨立）都在測試列文字，建議 R1 至 R7。同一版內處理全部，對照見第 14 節末；審查者表示不需要再做設計層重審，主代理對照 B1、B2、R1 至 R4 做 diff 核對後，與 `docs/spec/007` 在同一提交升 READY（該提交同時修訂 `003`、`004`、`005` 的對應句）。
流程：工作樹已有本規格部分功能的實作草稿（`hd/theme.go`、`play/prefs.go`、`i18n.go`、字型子集與產生腳本，與 `docs/spec/007` 的聲音接線）。這些檔案是草稿，未提交到 fork 的 `hr` 分支，部分行為落後於本規格（偏好設定的補丁式合併、`updatePrefs`、`hdView` 的世代、`Composer.A` 原子指標等）。升 READY 後以本規格為準改程式，測試也要改成斷言規格的行為。
範圍：`apps/hr/play`（前端）與 `apps/hr/hd`（素材預載、釋放、檢查）。涵蓋 F1 說明的內容與語言、F2 在原版與各 HD theme 之間循環、F3 聲音開關（功能見 `docs/spec/007`）、F4 在五種語言之間循環（只切換前端介面文字）、偏好設定、字型內嵌。不含：遊戲內文字（對白、選單、數值表）的多語系，那是里程碑 M10（`docs/spec/008`）；AI theme 的素材本身（M8）；音樂與音效的合成（`docs/spec/007`）。
關聯：`docs/spec/003-runtime-and-frontend`（保留鍵第 7 節、縮放第 6 節）、`docs/spec/004-hd-overlay`（Composer、清冊第 3.3 節、素材契約第 6 節）、`docs/spec/005-hang-diagnostics`（Ctrl+D、F1 的最近診斷列）、`docs/spec/007-music-sfx-playback`（F3、`-mute`）、`docs/spec/008-ingame-text-localization`（F4 與遊戲內語言，第 3.8 節）、`docs/re/021-mainexe-keyboard-census.md`（遊戲是否讀 F2、F3、F4）。
使用者決定（2026-10-03，`AGENTS.md` 第 12 節）：F1 說明列出功能；F2 切換 theme；F4 切換語言（繁體中文、簡體中文、韓文、英文、日文）。F3 是本專案為聲音開關選的鍵（使用者沒有指定，見第 14 節）。

推論等級用法：confirmed（讀原始碼、位元組或實跑可見）、強推論、假說、未知。沒有標的敘述是設計決定。

## 1. 輸入與工具

| 項目 | 內容 |
|---|---|
| 程式基準 | dosgolem 分支 `hr`，基準提交 `223ed99`；`apps/hr/play`（獨立模組，ebiten v2.9.9）。目前 F1 說明是 `ebitenutil.DebugPrintAt`，只有 ASCII（confirmed，`game.go`） |
| 文字繪製 | `github.com/hajimehoshi/ebiten/v2/text`（v1，已標 Deprecated 但 v2.9.9 仍在）加 `golang.org/x/image/font/opentype`（x/image v0.31.0，`ziphash` `h1:mLChjE2MV6g1S7oqbXC0/UcKijjm5fnJLUYKIYrLESA=`；其相依 x/text v0.29.0，`h1:1neNs90w9YzJ9BocxfsQNHKuAT4pkghyXc4nhZ6sJvk=`）。兩者的 `.mod`、`.zip`、`.ziphash` 與 `LICENSE` 都在建置映像 `eob-remake-go:1.26.7-ebiten2.9.9` 的 `/go/pkg/mod`（`golang.org/x/image@v0.31.0`、`golang.org/x/text@v0.29.0`，2026-10-03 在容器內 `ls` 確認），也在 `workplace/gomodcache`。`tools/play.sh` 用映像內的模組快取（`GOFLAGS=-mod=mod GOPROXY=off`），不掛 `workplace/gomodcache`；補進 `go.mod`／`go.sum` 後提交並重產 `engine/patches/`。`text/v2` 需要 `go-text/typesetting`，不在任何快取，離線不可建置（confirmed）。`x/image` 的 sfnt 能實際畫出五份子集的 CID 型 CFF 字形：字形墨跡測試（`apps/hr/play/fonts_test.go`，2026-10-03）對 205、206、212、101、232 個字元全部 `Glyph` 回 ok 且有墨跡，缺字回 `ok＝false`（`docs/re/022`） |
| 字型 | Noto Sans CJK Regular。檔案 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`，SHA-256 `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`，19,484,784 bytes，Debian 套件 `fonts-noto-cjk 1:20230817+repack1-3`，字型內部版本 2.004，授權 SIL OFL 1.1（confirmed）。TTC 內 10 個字面，全部是 CFF（`OTTO`）：0 ＝ Sans JP、1 ＝ Sans KR、2 ＝ Sans SC、3 ＝ Sans TC、4 ＝ Sans HK、5 到 9 ＝ Sans Mono CJK，Mono 不使用。10 個字面的 `hhea` 都是 ascender 1160、descender −288、unitsPerEm 1000，所以 `Metrics().Height` 不能用來辨認選對面（見第 10 節） |
| 子集工具 | `tools/gen_ui_fonts.sh`（第 6 節）；fontTools 4.66.1 的 `pyftsubset`（容器 `yuan-analysis:1`，映像識別 `sha256:f9ea24396753f49d…`）。腳本核對 TTC 的 SHA-256 與字面名稱，fontTools 版本不是 4.66.1 即失敗 |
| 輸入雜湊 | `hd/catalog.tsv` SHA-256 `34d076c868717aab71dfdc0124aad9c5fa1d1a22d46c333445ffa1c8cf964033`，`hd/palettes.tsv` `7eb992cbc6823b57510f41f3d5267c507f243c7d132c8ef1b965fbd0368983d5`。現有 `hd/` 通過新規則：595 列、595 個 PNG 都存在且尺寸為 2w x 2h，24 個調色盤名稱都在 `palettes.tsv`，沒有重複雜湊，沒有空 `hd` 欄的列 |
| 建置與測試 | 一律在 Docker（`tools/play.sh`，映像 `eob-remake-go:1.26.7-ebiten2.9.9`，識別 `sha256:39d6e05c9abc60a5…`）。`apps/hr/hd` 的測試入口新增 `tools/play.sh test-hd`（`-race`，需 cgo）。`go.mod`／`go.sum` 用 `-mod=mod` 加 `GOPROXY=off` 離線補上 |

## 2. 按鍵

| 鍵 | 功能 | 備註 |
|---|---|---|
| F1 | 開關功能說明（第 3 節） | 沿用 |
| F2 | 切換到下一個 theme（第 4 節） | 新增保留鍵，原本送進遊戲（掃描碼 `0x3C`，confirmed，`keys.go`） |
| F3 | 聲音開關（`docs/spec/007`） | 新增保留鍵，原本送進遊戲（掃描碼 `0x3D`，confirmed，`keys.go`） |
| F4 | 切換到下一種介面語言（第 5 節） | 新增保留鍵，原本送進遊戲（掃描碼 `0x3E`，confirmed，`keys.go`） |
| F11、Alt+Enter | 全螢幕 | 沿用 |
| F12 | 存截圖 | 沿用 |
| Ctrl+D | 手動診斷（`docs/spec/005`） | 沿用 |
| Ctrl+Q | 結束 | 沿用 |

- F1 至 F4 一律用 `inpututil.IsKeyJustPressed`（confirmed：必須在 `Update` 內呼叫），不放進 `specialKeys` 的按住重複規則。F1 至 F4 與修飾鍵的組合由純函式 `reservedKeyAction(key, ctrl, alt) action` 決定：

  | 組合 | 前端動作 | 送進遊戲 |
  |---|---|---|
  | F1、F2、F3、F4（無修飾鍵） | 各自的功能 | 否 |
  | Ctrl 加 F1 至 F4（含 Ctrl 加 Alt） | 不處理（留給將來的功能） | 否 |
  | Alt 加 F1、F2、F3 | 不處理 | 否 |
  | Alt 加 F4 | 不處理（Windows 與多數 Linux 視窗管理員以此關閉視窗） | 否 |

  **Ctrl 按住時 F1 不處理是行為變更**：現行 F1 沒有 Ctrl 判斷（`game.go`），與 F2 至 F4 一致化。F3 排除 Alt 是 `docs/spec/007` 草稿原有的行為，本表統一定案，`docs/spec/007` 第 5.4 節引用本表。
- Shift 或 Meta 按住時，F1 至 F4 視為無修飾鍵（`reservedKeyAction` 只有 `ctrl`、`alt` 兩個參數）。
- `keys.go` 移除 F2、F3、F4 三列，更新檔頭註解。**跨規格修訂清單與分工**（**本規格與 `docs/spec/007` 在同一個提交升 READY**，該提交同時修訂 `003`，不留下一個 READY 規格與另一份規格不一致的區間；同一格內依詞語分工，先後無關）：

  | 位置 | 修訂 | 負責 |
  |---|---|---|
  | `docs/spec/003` 第 6 節縮放句 | 「縮放模式預設最近鄰，可改為線性」改為 `-linear` 只影響 `original` 的 2 倍步驟 | 006 |
  | `docs/spec/003` 第 7 節保留鍵表 | 列出完整保留鍵：F1 至 F4、F11、F12、Alt+Enter、Ctrl+Q、Ctrl+D，加修飾鍵組合表的引用 | 006 |
  | `docs/spec/003` 第 10 節差異表（「與原版 DOS 的差異」一格） | 「鍵盤保留鍵」改為指向本規格第 2 節 | 006 |
  | `docs/spec/003` 第 9 節與同一格的「聲音（無）」 | 聲音由 `docs/spec/007` 負責 | 007 |
  | `docs/spec/004` 第 91 行（戳記欄位列的「是否有 HD」）與第 104 行（`Frame` 戳記含 HD 圖指標） | 實際 `Stamp` 沒有素材資訊（`stamp.go`），素材在合成時以雜湊取得，這也是 theme 能在合成時切換的前提；兩處一併改 | 006 |
  | `docs/spec/005` 第 176 行（F1 說明用 `DebugPrint`、字串必須是 ASCII） | 改為使用內嵌字型，不再限 ASCII | 006 |
  | `docs/spec/005` 第 177 行（保留鍵集合列舉） | 改為引用本規格第 2 節的完整清單 | 006 |
  | `docs/spec/003` 第 11 節「鍵盤路徑的普查與保留鍵衝突」 | 該條已被 `docs/re/021` 取代，只剩動態旁證與 `OP.EXE`、`END.EXE`；改為指向 021 | 006 |
  | `docs/spec/004` 第 108 行（「整數倍放大（最近鄰，或選用的平滑濾鏡）」） | `Composer` 的基底層恆為最近鄰；`-linear` 只影響 `original` 的 2 倍步驟（第 4 節） | 006 |
  | `README.md` 的按鍵說明、`packaging/README.dist.txt` 的按鍵行 | **實作合併進 `hr` 並重建發行包的提交時**同步（兩者描述現況，實作未合併前保持原句，READY 提交不改） | 006 |

  macOS 筆電的 F1 至 F4 預設是亮度與系統功能，要按 Fn；發行包說明要提。
- **遊戲是否讀 F2、F3、F4**（`docs/re/021-mainexe-keyboard-census.md`，靜態普查，2026-10-03）：`MAIN.EXE` 全部 77 個 `int 21h` 中讀鍵的只有 4 個（confirmed），分屬 getch、`_kbhit`、清鍵盤緩衝三個函式；沒有 `int 16h`、INT 09h 掛接、埠 60h 讀取（confirmed，限已解碼指令與原始位元組樣式）；三個函式的呼叫點共 7 處（getch 5 處、清緩衝 2 處、`_kbhit` 0 處），沒有任何一處使用鍵值（confirmed）；這 7 處的情境是 5 個錯誤等待與 2 個結束序列的清緩衝（強推論，其中兩個錯誤訊息字串沒有解碼）。結論：F2、F3、F4 不會改變 `MAIN.EXE` 的行為，遊戲在正常遊玩路徑上不讀鍵盤（強推論，旁證 `docs/re/016` 記錄遊戲在不讀鍵盤的畫面不取走按鍵）。保留這三個鍵的唯一可觀察差異是 5 個錯誤等待畫面少了三個可關閉畫面的鍵。涵蓋限制：純靜態、無動態收據（可在 dosgolem 對四個 `int 21h` 位址計數驗證，遊玩中預期為 0）；`OP.EXE`、`END.EXE` 的用法未分析（目前不跑，若日後跑完整 `HR.BAT`，影響：未知）。**停止線**：動態計數在遊玩中命中非零，或日後納入 `OP.EXE`、`END.EXE` 時發現它們使用這三個鍵，改選別的鍵並回到 DRAFT。

## 3. F1 功能說明

- 繪製在邏輯畫面（第 4 節固定 1280x800）上，深色底。**面板底色為半透明**；測試模式（`HR_TEST_FREEZE_UI`，第 10 節）改為不透明。位置左上，邊距 16 像素。字面 em ＝ 22 像素；**每一行各自呼叫 `text.Draw`，基線由呼叫端算**：第 i 行基線 ＝ 上緣 ＋ `Metrics().Ascent`（取整）＋ 32 × i。不使用 `\n`：`text.Draw` 的換行用 `Metrics().Height`（非整數，多行基線會逐行漂移；confirmed，`text.go`）。em 22 時字面的自然行高是 (1160 ＋ 288) ÷ 1000 × 22 ＝ 31.86 像素，與 32 幾乎相同，所以固定行距 32 的理由是基線整齊。
- 預算：垂直可用 768 像素（800 減上下邊距各 16），最多 21 行（面板 y ＝ 16 至 688 ＝ 672 像素，再多一行就與停機提示重疊）；寬度可用 1248 像素。內容：

  | 區塊 | 行 | 內容 |
  |---|---:|---|
  | 標題 | 1 | 名稱與版本 |
  | 按鍵表 | 8 | F1、F2、F3、F4、F11 與 Alt+Enter、F12、Ctrl+D、Ctrl+Q，各一行（鍵名與功能） |
  | 狀態 | 4 | theme（含可用清單）、介面語言、遊戲內文字語言（M10 之前一律「繁體中文（原版）」）、聲音開或關 |
  | 統計 | 3 | 步數、tick、遊戲秒、間隔、是否降頻（`interval`、`lowered`）；堆疊最低 SP、堆疊頂端、開啟檔案數；TPS、FPS。欄位沿用現行 `Session.Stats` 與 `ebiten.ActualTPS/FPS` |
  | 診斷 | 1 | 最近一份診斷的目錄名（ASCII，`docs/spec/005`） |
  | 提示 | 4 | 滑鼠操作遊戲；存檔路徑（1 行）；截圖路徑（1 行）；資料目錄 |
  | 合計 | 21 | 21 行 ＝ 672 像素，在 768 內 |

- **疊加層的位置與順序**（每個位置只有一種說法）：

  | 層 | 位置 | 說明 |
  |---|---|---|
  | F1 面板 | 左上，y ＝ 16 至 688 | 開著才畫 |
  | 停機提示 | 左下，y ＝ 688 至 752（2 行） | 停機後一直顯示，不論 F1 開關；用目前語言；舊版畫在 (4,4)，改到此處（已知差異） |
  | toast 與載入進度 | 左下最後一行，y ＝ 752 至 784 | 同一時間只有一則，新的取代舊的（例外：使用者操作的提示壓過載入進度 2 秒）；toast 2 秒，載入進度到結束 |

  三者不重疊（688 ＋ 64 ＋ 32 ＝ 784 ≤ 800 － 16）。toast 與載入進度同為一行，套用下面的省略規則。
- 超長處理：路徑與任何超出寬度的行，用 `font.MeasureString` 量，過寬時中間以「…」省略到放得下，不換行；停機提示（含現場存檔目錄路徑）與 F2、F3、F4 的提示套用同一規則，寬度預算同為 1248 像素。路徑中的字元若不在目前語言的子集內（`GlyphIndex ＝ 0`），該字以 `?` 取代，不顯示 `.notdef`（缺字時量測與繪製都用 `.notdef` 的前進量，所以仍一致，但畫出方框；confirmed，`sfnt.go`）。`font.MeasureString` 與 `text.Draw` 的前進量同源（`GlyphAdvance` 加 `Kern`；子集沒有 GPOS 也沒有 `kern` 表，`Kern` 恆為 0，第 6 節與第 10 節有測試守住）。
- 字面不是並行安全的（`opentype.Face`）：字面只在 UI 執行緒使用，測試的 `MeasureString` 不與繪製並行。字面建立後長期保留，每個語言一個，不在每次切換時重建。
- F1 開著的期間，字元與特殊鍵不送進遊戲（沿用）。
- 字型載入失敗時退回 `DebugPrintAt` 的 ASCII 英文版（按鍵表與狀態，英文），標準錯誤記一行；功能不得因字型缺失而不可用。回退字型畫在 1280x800 的邏輯畫面上，`original` theme 的螢幕大小比舊版小一半（已知差異）。
- 效能：面板內容的靜態部分（標題、按鍵表、狀態）只在 F1 開關、語言、theme、聲音狀態、診斷變化時重畫到快取影像；統計部分另一層，至多每秒重畫一次。`text.Draw` 的字形快取軟上限 512 個（以字元與四分之一像素 x 偏移為鍵，超過後只清 60 個 tick 沒用過的，confirmed，`text.go`）。各語言的字元表為 205（zh-TW）、206（zh-CN）、212（ko）、101（en）、232（ja）個字元（`TestGenCharsets` 實測），F1 同時用到的不同字元數低於此；快取鍵含四種 x 偏移，最壞約為字元數乘 4，超過軟上限時只是不清除仍在使用的項目。實作時量測重畫成本與快取大小並記在收據。
- `-scale 1`（視窗 640x400）時 F1 的 22 像素字縮成約 11 像素，CJK 難辨，列為已知差異；旗標說明建議 `-scale 2` 以上。

## 4. F2 與 theme

**邏輯畫面固定為 1280x800（遊戲區 640x400 的 2 倍）**，不隨 theme 改變（同時消除倍率切換造成的滑鼠換算與重配）。`Layout` 永遠回傳 1280x800，游標換算永遠是 `x/2`、`y/2`。視窗倍率旗標 `-scale` 只決定視窗大小。

**繪製的統一**：兩種來源各一張影像，切換時只換來源，不重配邏輯畫面。
- `original`：`imgOrig`（640x480，執行層快照的 RGBA）畫成 `GeoM.Scale(2, 2)`，濾鏡由 `-linear` 決定（預設最近鄰）。
- HD theme：`imgHD`（1280x960，`hdView` 合成的畫面）1:1。
- `g.scale` 欄位、toast 位置、`Layout`、`newGame` 全部改用常數。
- ebiten 把邏輯畫面放到視窗的最後一步與 `-linear` 無關：整數倍用最近鄰、小於 1 用線性、其他非整數倍用 `FilterPixelated`（confirmed，`gameforui.go`）。所以 `-linear` 只影響 `original` 的 2 倍步驟。`-scale 2` 時 `original` 與舊版的畫面內容相同（最近鄰兩次整數放大）；`-scale 1`、`3` 的最後一步濾鏡路徑與舊版不同，畫面內容近似（強推論，依 `gameforui.go` 三個分支，未實跑）。
- 顯示來源與上傳：`original` 的 `imgOrig` 以遊戲 `Seq` 比對（`lastSq`）；HD 影像以 `hdView` 的發佈計數比對（第 4 節），不再用遊戲 `Seq`。截圖路徑依「目前 theme」選（`original` 存 640x400，HD 存 1280x800），不依 `hv != nil`。

| 代號 | 顯示名稱 | 目錄 | 內容與畫法 |
|---|---|---|---|
| `original` | 原版 | 無 | 直接顯示執行層快照的遊戲區；不經 `Composer`，`hdView` 暫停 |
| `hd` | HD | `hd/` | 演算法 HD（`docs/re/015`），經 `Composer`（`docs/spec/004`） |
| `ai` | AI 重繪 | `hd-ai/` | AI 重繪（M8），經 `Composer`；缺漏的圖回退原圖（基底層） |

- 可用的 theme ＝ `original` 加上目錄存在且通過檢查的 HD theme。尋找順序與 `hd/` 相同（旗標、環境變數、AppImage 旁、執行檔旁、macOS 的 `Contents/Resources`、目前目錄），目錄名換成 `hd-ai`；旗標 `-hd-ai`、環境變數 `HR_HD_AI`。`-hd` 只決定 `hd/` 目錄，不選 theme。
- **載入的順序與基底 theme**（純函式 `pickThemes(avail)`，進第 10 節測試表）：
  1. 依序 `hd`、`ai` 呼叫 `hd.LoadAssets`（只讀兩個 TSV）。失敗（清冊或調色盤缺檔、格式錯誤）的 theme 不可用，記一行。
  2. **基底 theme ＝ 第一個載入成功的 HD theme**（`hd/` 優先）。`Session` 的 `HDAssets` 是基底 theme 的 `Assets`（`Overlay` 只用它的清冊做統計，`capture.go` 的 `Lookup`）；沒有任何 HD 目錄載入成功時 `HDAssets` 為 nil、不建立 `hdView`、F2 只有 `original`。
  3. 基底 theme 之外的 theme 是**衍生 theme**，用嚴格檢查 `hd.CheckTheme(base, dir, S)`（簽名見下）。`base` 為 nil 時回明確錯誤，基底 theme 本身不經 `CheckTheme`。
  4. **已知差異**：`hd/` 的 TSV 壞掉時，`hd-ai/` 成為基底而只過 `LoadAssets`（寬鬆），嚴格程度隨 `hd/` 的健康與否而變；此時沒有可比對的對象。
  5. 啟動預設：`-theme`，其次偏好設定，其次**第一個可用的 HD theme**（有 `hd/` 時是 `hd`，只有 `hd-ai/` 時是 `ai`），都沒有時 `original`。
- **檢查的內容**：
  - 基底 theme 只在 TSV 層錯誤時拒絕。逐圖問題（PNG 缺檔、尺寸不符、調色盤缺名）維持現行行為：該圖退回基底層（原版像素放大），其餘圖照常。理由：現行 `Assets.Get` 對這些問題逐圖降級；改成「一張壞就整個 HD 關閉」是未經決定的行為變更。
  - 衍生 theme 用 `hd.CheckTheme(base *Assets, dir string, s int) (*Assets, error)`（簽名與草稿 `theme.go` 一致：內部 `LoadAssets(dir)` 並回傳載入好的 `*Assets`，避免對衍生 theme 解析兩次 TSV；`base` 為 nil 時回明確錯誤，不 panic）。它對**每一列**檢查：`hash` 存在於基底清冊且 `w`、`h` 相同；引用的 `pal` 名稱存在於該 theme 自己的 `palettes.tsv`。`hd` 欄**非空**的列另檢查 PNG 存在且尺寸 S×w 乘 S×h（只讀檔頭，內容契約由發行前的驗收工具 `tools/hd` 負責）；`hd` 欄**為空**的列只略過 PNG 檢查（`tools/hd/catalog.py` 產生的清冊列出全部雜湊，沒有 HD 圖的列 `hd` 欄為空，`docs/spec/004` 第 3.3 節；草稿 `theme.go` 的行為與此一致）。允許只涵蓋部分雜湊；有任何一項不符就拒絕整個衍生 theme，記一行錯誤，其餘 theme 照常。比對以 `hash` 為鍵的集合，不依列序，也不比 `id`、`kind`、`pal` 欄的內容。`palettes.tsv` 不需與基底一致，合成用該 theme 自己的調色盤。
  - **兩條路徑的嚴格度不同是決定**：啟動時的預設 HD theme 沿用延遲解碼、不預載（開啟快）；切換（F2）時的預載若解碼成功數為 0 就拒絕切換。啟動後若全部 PNG 都缺，畫面是基底層（原版放大），由下面的錯誤輸出規則通報。
  - **逐圖錯誤的輸出**：`Assets.Errors`（每雜湊最多一筆，上限 595 筆）目前只有 `cmd/hrhd` 讀取，前端不讀，所以現行逐圖降級沒有任何輸出。`Errors` 由合成執行緒在 `a.mu` 下 `append`，`Release` 會把它設為 nil，因此前端**不直接讀欄位**，改用帶鎖的 `Assets.ErrorStats() (n int, first string)`。規定：預載結果的失敗由載入 goroutine 在 `Release` 之前讀取並隨結果回傳（`Release` 會清掉原因，所以必須先讀），UI 在 `onResult` 記一行；已套用 theme 的逐圖錯誤，前端在遊戲執行中每 60 秒檢查一次，`n` 比基準增加時記一行（新增筆數，與整個 `Assets` 的第一筆原因，`first` 不是新增的第一筆），不逐筆記，**記錄後基準設為當時的 `n`**（否則每 60 秒重複記同一行）。基準 `n` 每個 `Assets` 一份，只由 UI 執行緒讀寫：啟動 theme 為 0；預載成功的 theme 在進入 applying 時設為當時的 `n`（預載階段的失敗已在 `onResult` 記過）；再次切回已常駐的 theme 時基準不重設（切走期間沒有 `Get`，`n` 不變）。已套用的 `Assets` 不 `Release`，所以 `n` 單調不減，不需要世代欄位。
- 辨識（`Overlay`）與 theme 無關，所以切換 theme 不需重開 `Session`。
- `status` 欄：執行期的 theme 載入不看 `hd/provenance.tsv` 的 `status`（`AGENTS.md` 第 8 節規定新素材先是 `candidate`）。AI theme 的候選圖在 F2 會直接顯示，這是**決定**：它是使用者過目新素材的方式；發行包不含 `hd-ai/`（`tools/package.sh` 的 `stage_hd` 只複製 `hd/`，confirmed）。
- F2：依序 `original → hd → ai → original`（略過不可用的）循環。只有 `original` 可用時 F2 顯示提示「沒有其他 theme」，不改變狀態。**被拒的 theme 不再卡住循環**：預載被拒（解碼成功數為 0，含全部失敗與 `Preload` 回 `(0, 0)`，例如清冊的 `hd` 欄全空）時，該 theme 在本次執行標為不可用並記一行，`nextTheme` 略過它；逾時的 theme 不立即標記，允許再試一次，連續第二次逾時才標為不可用。
- `-theme original|hd|ai`、`-no-hd`：`-theme` 的值未知或該 theme 不可用，退回預設並記一行，不致命。`-no-hd` 是「不開 HD 掛鉤」：`HDHooks` 關、不建立 `hdView`、F2 沒有其他 theme，與 `-theme original` 不同（後者保留掛鉤與 `hdView`，F2 仍可切）。

**常駐策略**：已載入並套用過的 HD theme 一律常駐，切走時**不 `Release`**。HD theme 最多兩個（`hd/`、`hd-ai/`），常駐上限約 base 加兩份，每份約 194 MiB（595 張，原版像素合計 12,709,184 乘 4 位元組乘 4 ＝ 203,346,944 bytes ＝ 193.9 MiB；`docs/re/014` 另記全部載入約 262 MB 含不在清冊的字型圖），也就是約 400 MiB 加基底與遊戲。切回已載入的 theme 是即時的；若日後記憶體成為問題，另立規格加 `Release` 策略。`Assets.Release()`（清空解碼快取與 `Errors`，保留清冊與調色盤）只用在**尚未套用的預載被丟棄或被拒**時，由載入 goroutine 在回報結果之前同步呼叫，此時沒有其他使用者。**量測與通過標準**（收據量測後可調整，調整要記在 `docs/re`）：兩個 theme 都載入後，分別記兩個時點的 RSS 與 `HeapInuse`：預載剛完成時，以及 `runtime.GC()` 後等 5 秒。通過標準只設在 GC 之後：RSS 不高於載入前加 2 × 194 MiB 加 64 MiB。預載剛完成時的值只記錄不設門檻（`GOGC` 預設 100，解碼的暫時物件在回收前仍計入 RSS，強推論，未量測）。預載被丟棄後的 RSS 只記錄：被拒（`ok ＝ 0`）沒有解碼任何東西，只有逾時才有部分解碼。

**切換狀態機**（純邏輯，注入載入器、時鐘、`holder` 與 `viewControl` 縫隙即可測試）：

| 狀態 | 進入 | 離開 |
|---|---|---|
| idle | 初始；任何交易結束 | F2 且目標是 `original` → 即時切換（下面「回 original」）；F2 且目標是已常駐的 HD theme → 取得 `HoldAdapt`，進入 applying；F2 且目標是未常駐的 HD theme → 取得 `HoldAdapt`，啟動 goroutine，進入 loading |
| loading | goroutine 對目標 `Assets` 執行 `Assets.Preload(ctx, progress)`，進度顯示在 toast 行；計時器 60 秒；**進入 loading 時清除 `timerFired`** | 結果到達 → `onResult`（下）；計時器觸發 → 記 `timerFired`、取消 `ctx`、進入 cancelling（只是「已請求取消」的顯示狀態）；程式結束 → 取消 `ctx`（`timerFired` 維持為假）、進入 cancelling |
| cancelling | 計時器觸發或程式結束，`ctx` 已取消，goroutine 尚未回來 | 結果到達 → `onResult`（下） |
| applying | 目標素材就緒，`hdView.SetAssets(target)` 已呼叫，目前 theme 已更新為目標；等該世代第一張新畫面或 2 秒 | 第一張新畫面已發佈（`ready` 由空變非空），或 2 秒到期 → 完成：顯示來源與上傳更新、toast、記 `theme ready: <代號>`、提交 `theme` 偏好補丁、放開 `HoldAdapt` → idle |

**`onResult` 是唯一的結果處理函式**（結果由 goroutine 傳回 UI，UI 在 `Update` 內處理；同一次 `Update` 內計時器與結果同時到達時**結果優先**）。`Preload` 回傳 `(ok, failed, err)`，`err != nil` 表示 `ctx` 在迴圈頭被取消，`ok` 可大於 0；迴圈跑完回傳 `err ＝ nil`（即使 `ctx` 在之後才被取消）：
1. `err != nil`（取消，已有部分解碼的快取）：goroutine 已在回報前 `Release` 目標。**`timerFired` 為真就是計時器逾時，為假就是程式結束**（取消來源只有這兩個）：逾時時該 theme 的逾時計數加一，計數達 2 標為不可用，toast 提示逾時並記一行；程式結束時不計數、不提示。放開 `HoldAdapt` → idle。
2. `err ＝ nil` 且 `ok ＝ 0`（含清冊 `hd` 欄全空的 `(0, 0)`）：goroutine 已在回報前讀取 `ErrorStats()` 並 `Release` 目標。標為不可用並記一行：`failed > 0` 時含首筆原因，`(0, 0)` 時用固定文字（清冊沒有 HD 圖）。放開 `HoldAdapt` → idle。
3. `err ＝ nil` 且 `ok > 0`：預載是完整的，**即使計時器已經觸發也接受**（不丟棄一份已完整的預載），逾時計數歸零，目標成為常駐 → applying。有部分失敗照常，失敗的圖退回基底層，數量記一行。

- **逾時計數**：每個 theme 一個計數，只算連續逾時（`onResult` 的第 1 條且 `timerFired`），第 3 條成功時歸零；連續第二次逾時才標為不可用。「不可用」的標記只在本次執行有效，不持久化。
- loading、cancelling、applying 期間再按 F2：忽略，不排隊，toast 顯示「載入中」。取消沒有使用者動作，只有計時器與程式結束兩個來源。
- **回 original**（`original` 為目標，全在 UI 執行緒，不需要 `HoldAdapt`）：顯示來源立刻換成 `imgOrig`；`hdView.SetAssets(nil)`（暫停）；提交 `theme: original` 偏好補丁；toast 與記 `theme ready: original`；回 idle。目前 HD theme 的 `Assets` 保留常駐。
- **回報順序與一取一放**：每個 HD 目標的交易恰好取得一次、放開一次 `HoldAdapt`：成功與常駐目標在 applying 完成時放開；被拒、丟棄在 `onResult` 內放開。`original` 目標不取得。
- `Preload` 的 `progress` 回呼在 goroutine 內執行；toast 與進度欄位用 atomic 或鎖，不得由 goroutine 直接改 UI 欄位。
- 時間：`docs/re/014` 實測全部載入約 1.65 秒（強推論，目標機器未量，量測見第 10 節）。`Get` 持鎖解碼，所以預載只對「目前沒有被合成使用」的 `Assets` 進行（目標未常駐，不在顯示中）。從 `original` 切到 `hd` 時，`hd` 的 `Assets` 同時是 `Session` 的 `HDAssets`，但 `Overlay` 只讀清冊、不碰解碼快取，預載它安全。啟動時就使用的 HD theme 沿用延遲解碼、不預載，視為已常駐。
- **預載與模擬降頻**：`Session.Run` 每 2 秒呼叫一次 `adapt`，隨後無條件把視窗基準（`lastCheck`、`checkTicks`）重設為現在；`adapt` 判斷整個視窗內的 tick 數，落後 5% 以上就把間隔降為 90% 且 `lowered` 永久為真（confirmed，`session.go`）。預載是單核解碼，與模擬、合成、UI、音訊同時進行，雙核機器（`tools/play.sh` 預設 `--cpus 2`）上可能觸發永久降頻，改變遊戲相對於計時器的速度。只讓 `adapt` 在持有時返回不夠（預載在視窗中途結束時，評估點落在持有之後，視窗仍含競爭期）。規定：
  - 持有狀態是獨立型別 `holdGate{mu, held, dirty}`，方法 `hold() (release func())` 與 `take() (held int, dirty bool)`；`release` 在鎖內同時減計數並設 `dirty`，且冪等（第二次呼叫不再減，計數不得變負）。`Session.HoldAdapt()` 是它的薄包裝。
  - **視窗規則**：任何與持有時間相交的視窗（含放開當下所在的視窗）只重設基準、不評估：`Run` 只在視窗已滿 2 秒的檢查點呼叫 `take()`（否則會提早清掉 `dirty`，下面案例的算術依賴這點），若 `held > 0` 或 `dirty`（讀取後清除）就跳過。
  - 決策拆成純函式 `windowVerdict(now, lastCheck, ticks, held, dirty) → skip | ok | lower`，`lower` 只表示「落後 5% 以上」；`adapt` 的下限判斷（`want <= 0`、`interval <= MinInterval` 時直接返回，不改 `lowered`、不記日誌）留在 `Session` 的薄包裝層。`lastCheck`、`checkTicks` 目前是 `Run` 的區域變數，搬到 `Session` 欄位。靜態檢查：`adapt(` 在 `session.go` 只出現定義與包裝的一次呼叫。
  - **持有範圍**：從受理 F2 到 applying 完成或被拒、丟棄為止（涵蓋預載與 `hdView` 的首次整幅合成）。最長約 62 秒（60 秒逾時加 2 秒等待新畫面）；這段期間真正的落後也不降頻（已知差異）。
  - 收據量測雙核下 F2 前後的 `Lowered` 與 `interval`；另有對照：同一容器、同樣時間長度，以 `-theme hd` 啟動、不按 F2，若 `Lowered` 為真，代表 `hdView` 的持續合成本身就會降頻，F2 前後不變的斷言無效（`hdView` 的 `Workers` 預設 `min(GOMAXPROCS, 8)`）。

**切換的序列與畫面**：
1. 目標是 HD theme（進入 applying 後）：呼叫 `hdView.SetAssets(target)`（下面：單一臨界區內設素材、遞增 `epoch`、清 `ready`）。目前 theme 在此刻就更新為目標，之後顯示來源換成 `imgHD` 只是呈現。**等 `ready` 由空變非空（該世代第一張新畫面，最多 2 秒）**才更新顯示：從 `original` 切來時此時才把顯示來源換成 `imgHD`；HD 到 HD 時顯示來源本來就是 `imgHD`，舊內容一直保留到新畫面上傳，不會閃出黑色。停機時 `SetAssets` 仍讓 `run` 用目前 `Frame` 重合成，新畫面照樣出現；2 秒到期只會發生在 `Frame()` 為 nil（`Session` 尚無畫面）或 `Compose` 超過 2 秒。逾時仍切換，此時 `imgHD` 可能是黑色或舊 theme 的內容，列為已知差異。
2. 回 original：見上。
3. 從 HD theme 切到另一個 HD theme：同序列 1，舊 theme 保持常駐，切回時是即時的（目標已常駐，直接進入 applying）。

**換素材與暫停的併發**：
- `Composer.A` 改為 `atomic.Pointer[Assets]`，提供 `SetAssets(*Assets)`；`Compose` 在**取任何素材之前**載入一次，整幀只用這個快照（草稿的快照在 `compose_draw.go` 的基底放大與驗證之後，實質相同，因為 `Composer.A` 在 `Compose` 內只有這一處讀取）。第 10 節有 `-race` 的快照測試。
- `hdView` 對畫面來源只依賴介面 `frameSource{ Frame() *hrrt.Frame }`（`*hrrt.Session` 實作），測試用假來源，不需原版。
- **`hdView` 只有一個狀態轉移 `SetAssets(a *Assets)`**：`a` 為 nil 表示暫停，非 nil 表示恢復並使用該素材。它在 `mu` 下的**單一臨界區**內同時改 `assets`、遞增 `epoch`、清 `ready`。素材與世代永遠一起改變，沒有順序問題。暫停就是 `assets ＝ nil`，沒有另外的旗標。
- **`run` 的一輪**（`run` 是唯一擁有 `last` 與 `seenEpoch` 的 goroutine）：在 `mu` 下一起讀 `(epoch, assets)`；若 `epoch` 與 `seenEpoch` 不同就把 `last` 歸零並更新 `seenEpoch`（`assets` 為 nil 的輪次也更新）；`assets` 為 nil 就等待；否則自己呼叫 `Composer.SetAssets(assets)`，再 `Compose`；完成後持 `mu` 檢查 `epoch` 未變才發佈（設 `ready`、遞增發佈計數 `pub`、記 `pubFrom ＝ assets`），否則丟棄（遞增 `discards`）。丟棄後下一輪會用目前 `Frame` 重新合成，這也涵蓋「`Session` 沒有新 `Seq`、靜態畫面」的情形。暫停時 `Composer` 仍指向舊 `Assets`（影響小：清冊與調色盤保留），`run` 在等待時可呼叫 `Composer.SetAssets(nil)`。
- **`upload` 與 `writePNG` 在 `ready` 為空時**：`upload` 回 false（不論 `pub` 是否與上次相同；否則 HD 到 HD 時剛發佈的舊畫面在同一幀被 `SetAssets` 清空，`Draw` 會上傳清空的緩衝區而閃出黑色）；`writePNG` 回哨兵錯誤 `errNoFrame`，不複製。`upload` 以發佈計數比對，不用遊戲 `Seq`（遊戲停機時 HD 到 HD 的新畫面仍能進入 `imgHD`）；`lastSq` 只留給 `original` 的 `imgOrig` 更新。
- **F12**：HD theme 下 `writePNG` 回 `errNoFrame` 時，`game.screenshot` 退回存原版快照（640x400）並記一行，不寫舊畫面或全黑 PNG。
- **測試控制點與可觀察手段**：`Assets` 提供匯出的測試輔助 `SetGetHook(f func(hash string))`，欄位用 `atomic.Pointer`；鉤子在 `Get` 進入時、查快取之前、**`a.mu` 之外**呼叫（否則停在鉤子的 `Compose` 持有 `a.mu`，測試同時呼叫 `ErrorStats()` 或 `Release()` 會卡死）；鉤子自帶 once。觸發前提：素材非 nil、`len(stamps) > 0`、至少一個戳記通過驗證（`compose_draw.go`）。`hdView` 提供未匯出的測試欄位與方法：`pubFrom`（最近一次發佈用的素材）、`discards`、`pub`；`skipEpochCheck` 與 `Composer` 的 `rereadPerStamp` 是**建構選項**（建立時設定，`newHDView` 一建立 `run` 就在跑，之後才設會與 `run` 的讀取競爭）。`play` 套件取不到 `hd` 的測試輔助（`_test.go` 不能跨套件），所以 `hdView` 測試用 `hd.LoadAssets` 指向只有表頭的兩個 TSV 暫存目錄，戳記用匯出欄位建立，雜湊不在清冊也會觸發鉤子；此時 `Get` 回 nil、輸出與素材無關，所以 A 與 B 的區分**用 `pubFrom` 的指標比對，不用像素**（`Composer` 是否真的使用該素材由 `hd` 套件的快照測試負責）。
- 提示：切換完成（applying 結束或回 original）後在 toast 行顯示 2 秒「Theme: HD」之類（該語言的文字），並記一行日誌 `theme ready: <代號>`（測試用的完成訊號；HD 到 HD 沒有換顯示來源，仍在 applying 結束時記）。toast 與載入進度同一行：使用者操作的提示（切換、語言、聲音）優先，壓過進度 2 秒（例外於「新的取代舊的」），之後進度恢復顯示。

## 5. F4 與介面語言

- 語言：`zh-TW` 繁體中文、`zh-CN` 簡體中文、`ko` 한국어、`en` English、`ja` 日本語。顯示名稱用各語言自己的名稱。
- F4 依序循環 `zh-TW → zh-CN → ko → en → ja → zh-TW`。
- 啟動時的語言：`-lang <代號>`，其次偏好設定，其次 `zh-TW`。`-lang` 的值未知：退回預設並記一行，不致命。
- **範圍**：F4 切換的是前端介面文字（F1 說明、F2、F3、F4 的提示、診斷提示與停機提示、視窗標題）。遊戲內文字（對白、選單、數值表）由原版資料決定，M10 之前不隨 F4 改變，F1 的「遊戲內文字」一行如實標示。M10 的 L1 實作後，F4 同時設定遊戲內語言包（`docs/spec/008` 第 3.8 節）；沒有語言包的語言，遊戲內文字維持原版繁體中文並在 F1 標示。
- **啟動錯誤視窗（`errwin.go`）不在 F4 的範圍內**：它的內文固定 ASCII 英文、`Layout` 640x400、沒有按鍵處理，維持現狀。
- 提示：切換後在 toast 行顯示 2 秒語言名稱（用目標語言的字面與名稱）。
- 翻譯內容：五種語言的字串是 AI 草稿，未經母語者審閱（字串表檔頭註記）。這是翻譯品質的已知限制。

## 6. 字串與字型

- 字串表：`i18n.go`，鍵到五種語言的文字。測試要求每個鍵都有五種語言、非空，且格式動詞（`%d`、`%s`、`%.0f`）的順序與個數在五種語言一致。
- 字型子集：每個語言一份（`zh-TW` 用 TC 字面（`--font-number=3`）、`zh-CN` 用 SC（2）、`ko` 用 KR（1）、`ja` 用 JP（0）、`en` 用 TC 的拉丁字母）。字元表由字串表產生：`apps/hr/play` 的 `TestGenCharsets`（`HR_GEN_CHARSET=<目錄>`）把每個語言的字元倒成 `fonts/charset-<lang>.txt` 入版控，加 ASCII 可印字元、`…`、`?`；不用正規式從 Go 原始碼抓字串。
- **`pyftsubset` 旗標**（fontTools 4.66.1，2026-10-03 在容器內實跑確認）：`--layout-features=`（清空字形替換與定位特性）、`--drop-tables+=GSUB,GPOS`（只用前一旗標，輸出仍留下空殼的 GSUB 72 bytes 與 GPOS 32 bytes；加上此旗標後兩表不存在；`x/image` 沒有 shaping，用不到）、`--no-hinting`、`--notdef-outline`、`--name-IDs=0,7,13,14`（**取代**預設集合 0 至 6：保留版權、商標、授權說明、授權網址；`x/image` 的 `initialize` 不解析 `name` 表，丟掉 1 至 6 可行，這是決定）、`--legacy-kern`、`--recalc-bounds`。預設 `name_IDs` 不含 13、14，不加旗標會被丟掉。輸出 OTF。實測子集的表為 BASE、CFF、OS/2、VORG、cmap、head、hhea、hmtx、maxp、name、post、vhea、vmtx（沒有 GSUB、GPOS、kern）。
- **產生腳本 `tools/gen_ui_fonts.sh`**（容器內，掛載前確認來源存在，因為來源不存在時 dockerd 會以 root 建空目錄）：核對 TTC 的 SHA-256；核對指定字面的 name table 名稱（選到 Mono 字面會讓拉丁字母變等寬）；**fontTools 版本不是 4.66.1 即失敗**；每份子集斷言沒有 GSUB、GPOS 表，name ID 0、7、13、14 都存在；`SOURCE.txt` 記錄來源、雜湊、fontTools 版本、旗標。**穩健度**：`play.sh gen-charset` 的容器指令以管線結尾（`go test … | tail`），沒有 pipefail，測試失敗時管線仍回 0；腳本因此要檢查輸出含 `PASS`，並檢查五份 `charset-*.txt` 的時間戳比腳本開始時間新，否則失敗（避免拿舊字元表切子集）。`yuan-analysis:1` 是另一個專案的映像（歸屬未驗證），唯讀的 `docker run` 不改映像，但可重現性依賴本專案管不到的映像：腳本比對映像 ID（`sha256:f9ea24396753f49d…` 的完整值寫在腳本與 `SOURCE.txt`），不符即失敗。`play.sh` 的前置檢查要求 `workplace/orig` 存在，與字型產生無關（已知限制，沒有原版時整條腳本不能跑，除非 `play.sh` 的檢查改為只對需要原版的子命令生效）。輸出入版控並以 `go:embed` 內嵌：`apps/hr/play/fonts/ui-<lang>.otf`、`charset-<lang>.txt`、`SOURCE.txt`、`OFL.txt`。字元表改了而字型沒有重產（字型過期）時，第 10 節的「每個字元都有字形」測試會失敗。
- **`OFL.txt`**：字型內嵌的版權與授權說明（name ID 0、13、14，OFL 第 2 條要求每份複本帶版權聲明與授權），加 OFL 1.1 全文。全文取自 Debian 套件 `fonts-noto-cjk` 的 `copyright` 檔 `License: SIL-1.1` 段，**只取該段**：Debian 的段落以空白開頭的行延續，遇到不以空白開頭的行（下一段，例如 `debian/*` 的 `License: GPL-3+`）即停；腳本末端斷言 `OFL.txt` 含 "SIL OPEN FONT LICENSE Version 1.1" 且不含 "GNU General Public License"（第三輪審查發現前一版夾帶 GPL-3+ 段共 12 行；修正後 `OFL.txt` 為 97 行，2026-10-03 實跑確認）。通知文字取自字型內嵌的 name ID 0（「© 2014-2021 Adobe」，與 Debian 彙總檔的「Google 2010-2012」不同，以字型內嵌為準）；子集是修改版，OFL 允許。「Noto 沒有 Reserved Font Name」的等級是強推論：Debian 的 `copyright` 與 TTC 全檔（ASCII 與 UTF-16BE 都找過）沒有宣告 Reserved Font Name（"reserved" 只出現在 OFL 全文內）；上游 `notofonts/noto-cjk` 的 `Sans/LICENSE` 首句是 "This Font Software is licensed under the SIL Open Font License, Version 1.1"，沒有宣告 Reserved Font Name（2026-10-03 以 WebFetch 讀取，是摘要結果，原檔未保存）。發行前以原檔再核對一次（停止線）。
- **證據留存**：字型方案的容器實跑結果（fontTools 版本、五份子集的表清單與 SHA-256、`OFL.txt` 的行數與 SHA-256、建置映像內 `x/image` 與 `x/text` 的 `ls`、字形墨跡測試結果）記在 `docs/re/022-ui-font-subset-receipts.md`。
- **發行包的授權聲明**：`tools/package.sh` 的 `make_notices` 已含 `oto`，現在沒有 `x/image`、`x/text`，字型授權檔用 `if [ -f … ]` 包住（缺檔會靜默略過）。本規格實作時：加入 `x/image`、`x/text` 與 `/w/dosgolem/apps/hr/play/fonts/OFL.txt`（掛 `$ROOT/workplace:/w`），字型授權檔缺檔改為失敗。驗收（`tools/pkg/verify_*.sh` 目前沒有任何 "SIL"、"Adobe" 或 `THIRD_PARTY` 的斷言，是全新的工作）：包內的 `THIRD_PARTY_NOTICES.txt` 含 "SIL OPEN FONT LICENSE" 與 "Adobe"，且不含 "GNU General Public License"。

## 7. 偏好設定

- 檔案 `<資料目錄>/prefs.json`：`{"version":1,"theme":"hd","lang":"zh-TW","sound":true}`。
- **只寫被切換的欄位，以補丁合併**：F2 改 `theme`、F3 改 `sound`、F4 改 `lang`。每次切換提交一個欄位補丁；背景寫入者合併**待套用的補丁**（同欄位後者覆蓋、不同欄位保留，所以 F2 後立刻 F4 兩個欄位都會寫入），然後讀目前的檔案、套用補丁、原子寫回。旗標與環境變數啟動（例如 `-theme original`、`-mute`、`HR_MUTE`）的值不進補丁，不會被持久化。兩個執行個體同時運行時，讀檔、改欄位、改名之間沒有檔案鎖，窗口縮小到一次寫入，但不是零：列為已知差異。
- 讀取：逐欄位寬鬆解析（每個欄位單獨解碼，型別錯誤只讓該欄位用預設，不讓整份失敗）。未知欄位忽略，寫回時**保留**。值已知但目前不可用（例如 `"ai"` 而沒有 `hd-ai/`）：用預設，不覆寫檔案內容。
- **補丁的提交時機**：切換完成（顯示來源已換、語言與聲音狀態已生效）才提交，不在按鍵當下。預載被拒或逾時時不得寫入 `theme`。
- **版本與損壞**：頂層不是 JSON 物件（陣列、`null`、字串）、不是合法 JSON，或 `version` 缺或不是數字，視為損壞：**每次寫入時**對剛讀到的位元組判斷（不是啟動時留下的旗標；否則兩個執行個體時，晚到的那個會把對方剛寫好的有效檔改名成 `.bad`），損壞就先把原檔改名為 `prefs.json.bad`（覆蓋舊的 `.bad`），再寫新檔，記一行。`version` 是數字但不是 1（例如新版寫的 2）：已知欄位照常讀取；寫回時**原樣保留 `version` 的值與所有未知欄位**，只改被切換的欄位。
- 優先序（theme、lang、sound 一致）：命令列旗標、環境變數（目前只有 `HR_MUTE`，`docs/spec/007` 第 5.4 節）、偏好設定、預設。
- 寫入：`os.CreateTemp` 建唯一的暫存檔再 `os.Rename`；在背景 goroutine 寫，不阻塞 UI 執行緒；失敗只記一行。**結束時 flush**：所有結束路徑（Ctrl+Q、視窗關閉、停機後離開、`os.Exit(1)` 的錯誤路徑）都經同一個 `quit()`，它等最後一次寫完，最多 1 秒（`Close()` 內部帶逾時，草稿的無上限等待要改）。信號終止不保證（已知差異）。啟動時清理自己留下的 `.prefs-*.tmp`（崩潰殘留，盡力而為）。`dataDir()` 在 `UserConfigDir` 失敗時退到 `os.TempDir()`，此時偏好設定不跨次保留（已知差異）。

## 8. 失敗模式

| 情形 | 預期 |
|---|---|
| 基底 theme 的清冊或調色盤 TSV 缺檔或格式錯誤 | 該 theme 不可用，記一行；沒有其他 theme 時 `HDAssets` 為 nil，F2 只有 `original` |
| 基底 theme 的個別 PNG 缺檔、尺寸不符、調色盤缺名 | 該圖退回基底層，其餘照常（現行行為，不變）；`Errors` 筆數增加時依第 4 節規則記一行 |
| 衍生 theme 的檢查不符（雜湊不在基底、尺寸不符、調色盤缺名、非空 `hd` 欄的圖檔缺或尺寸不符） | 拒絕該 theme，其餘照常，F2 略過它，記一行 |
| 預載解碼成功數為 0（`err ＝ nil` 且 `ok ＝ 0`，含 `Preload` 回 `(0, 0)`，例如清冊 `hd` 欄全空） | 拒絕切換，提示失敗，留在原 theme；載入 goroutine 在回報前讀取 `ErrorStats()` 並 `Release` 目標素材（未套用、無其他使用者），記一行（含首筆原因）；該 theme 在本次執行標為不可用，`nextTheme` 略過它；放開 `HoldAdapt` |
| 預載被取消（計時器 60 秒逾時或程式結束，`Preload` 回 `err != nil`，`ok` 可大於 0） | 丟棄結果，留在原 theme，goroutine 在回報前 `Release` 目標素材；計時器造成的取消，逾時計數加一，連續第二次逾時才標為不可用（本次執行有效，不持久化），程式結束造成的取消不計數；放開 `HoldAdapt` |
| 「跑完全部後計時器才觸發」（`err ＝ nil` 且 `ok > 0`） | 接受這份完整的預載（`onResult` 第 3 條，結果優先於計時器），逾時計數歸零，進入 applying |
| 切換等不到新畫面（2 秒，`Frame()` 為 nil 或 `Compose` 過慢） | 仍把顯示來源換成目標；`imgHD` 可能是黑色或舊內容（已知差異） |
| loading、cancelling、applying 時按 F2 | 忽略，不排隊，toast 顯示「載入中」 |
| 預載部分失敗 | 照常切換，失敗的圖退回基底層，記一行（失敗數） |
| 切換交易期間 `Session` 落後 | `HoldAdapt` 涵蓋 HD 目標的整個交易（受理 F2 到 applying 完成、被拒或丟棄）；含放開所在視窗不評估，下一個完整視窗恢復原判斷。`original` 目標不取得 `HoldAdapt`（全在 UI 執行緒，沒有預載） |
| 字型缺字 | 字串表內不得有缺字（測試保證）；動態字串以 `?` 取代 |
| 字型載入失敗 | 退回 ASCII 英文的 F1，功能照常 |
| 偏好設定檔損壞 | 改名為 `prefs.json.bad`，用預設，寫新檔 |
| 偏好設定的值不可用 | 該欄位用預設，不覆寫檔案內容 |
| 載入 theme 期間切換語言或聲音 | 照常生效，載入進度提示改用新語言 |
| HD theme 下 F12 而 `ready` 為空 | 存原版快照，記一行 |
| 旗標值未知（`-theme`、`-lang`） | 退回預設，記一行，不致命 |
| 偏好設定寫入失敗 | 記一行，行程內狀態不受影響，下次啟動回到先前的值 |
| F2 時 `Session` 已停機 | `SetAssets` 仍用目前 `Frame` 重合成，畫面照常更新；停機提示不受影響 |

## 9. 玩家路徑與存檔影響

玩家路徑：啟動（可能帶偏好設定）、遊玩中按 F1 看說明、按 F2 換 theme、按 F3 開關聲音、按 F4 換語言。不修改遊戲記憶體、存檔與原版檔案；偏好設定只寫 `prefs.json`。切換 theme、聲音與語言不送任何輸入事件給遊戲（第 10 節以枚舉測試守住）。存檔格式與遊戲規則不變。預載降頻的風險由 `HoldAdapt` 處理（第 4 節）。

## 10. 測試

測試縫隙（命名的介面與函式變數，讓測試不依賴 ebiten、GPU 與原版）：
- `frameSource`（`Frame()`）；`inputSink`（記錄對遊戲的 `Input`／`AppendInputChars` 呼叫）；`pressDuration func(ebiten.Key) int`（取代 `inpututil.KeyPressDuration`，ebiten 全域狀態在單元測試設不了按鍵）；
- `gameSession`：`game` 依賴的最小介面（`Stats`、`RequestFrame`、`RequestDiag`、`CrashDump`、`Input`、`Frame`），`*hrrt.Session` 實作，讓 `Layout` 與按鍵處理的測試不需要真的 `Session`，`newGame` 不在建構時啟動 `Run`；
- `assetLoader`（`Preload(ctx, progress)`、`Release()`，可注入慢速載入）；`clock`（時間來源）；
- `savePrefs` 寫入函式變數（可注入卡住的寫入）；字型載入函式變數（可注入壞字型）；
- `Assets.SetGetHook`（`hd` 套件匯出的測試輔助，`atomic.Pointer` 欄位；`Get` 進入時、查快取之前、`a.mu` 之外呼叫；鉤子自帶 once）；`Composer` 的 `rereadPerStamp` 與 `hdView` 的 `skipEpochCheck`（負對照用，兩者都是**建構選項**，建立時設定，因為 `newHDView` 一建立 `run` 就在跑）；`hdView` 的未匯出觀察欄位 `pub`、`pubFrom`、`discards`（第 4 節）；
- `viewControl`：前端對 `hdView` 的介面（`SetAssets(*Assets)`、`ready` 是否非空、發佈計數），讓狀態機測試能驗證呼叫順序；`holder`：`HoldAdapt` 的介面（取得與放開，記錄次數），併入 `gameSession` 或獨立，真實實作是 `holdGate`。

純函式：`pickThemes(avail)`、`nextTheme(cur, avail, rejected)`、`nextLang`、`resolveStartup(flags, env, prefs, available)`、`reservedKeyAction(key, ctrl, alt)`、`panelLines(lang, face, info)`、`applyPrefsPatch(old, patches)`、`windowVerdict`（`Session` 的降頻決策，可注入時鐘，見下）。

| 承諾 | 測試 |
|---|---|
| theme 循環順序、略過不可用者與被拒者；只有 `original` 時 F2 不動作 | 單元：`nextTheme` |
| 基底選法：`hd/` 優先；只有 `hd-ai/` 時它是基底且不經 `CheckTheme`；`hd/` TSV 壞時 `hd-ai/` 成為基底；啟動預設為第一個可用 HD theme | 單元：`pickThemes`、`resolveStartup` |
| 語言循環順序與解析 | 單元（已有） |
| 字串表五語言齊全、無空字串、格式動詞一致 | 單元（已有） |
| 字型涵蓋：每個語言的每個字元都有字形（`GlyphIndex` 不為 0）；子集由 `opentype.Parse` 載入；name ID 0、7、13、14 存在；子集沒有 GSUB、GPOS、kern（測試自己解析檔頭的表目錄：`numTables` 在偏移 4，每筆 16 位元組從偏移 12 起，因為 `sfnt.Font` 沒有公開表目錄） | 單元（已有，`fonts_test.go`） |
| **字形墨跡**：對字元表每個非空白字元，`face.Glyph` 回 ok 且遮罩有墨跡（解析與 `GlyphIndex` 不會執行 CFF charstring，只有 `Glyph` 會）。控制組：空白（含 U+3000）ok 但沒有墨跡；不在子集內的字元 `GlyphIndex ＝ 0` 且 `Glyph` 回 `ok＝false` | 單元（已有，五份子集全部通過，2026-10-03） |
| **選對字面**：`GlyphAdvance('i')` 不等於 `GlyphAdvance('W')`（選到 Mono 面會相等）。`Metrics().Height` 約 31.86 只守住 `hhea` 沒被改壞（10 個面的 `hhea` 全相同，不能用來辨認字面） | 單元（已有） |
| `Kern` 對常見字對恆為 0（子集沒有 GPOS 與 kern 表） | 單元（已有） |
| F1 面板邊界：五種語言各自量全部行，斷言行數乘行距不超過 768；每行寬度不超過 1248，**以兩種獨立方法**：`font.MeasureString` 與 `font.BoundString` 的墨跡右緣（路徑、停機提示、theme 載入提示用極端長度輸入） | 單元：`panelLines`（不需 GPU） |
| 疊加層位置：F1 面板、停機提示、toast 行的矩形互不相交；使用者提示壓過載入進度 2 秒 | 單元 |
| 偏好設定：往返、損壞（含頂層不是物件）改名 `.bad` 且判斷用每次寫入時剛讀到的位元組（兩個執行個體的晚到者不覆蓋對方剛寫的有效檔）、`version` 不是 1（原樣保留 version 與未知欄位）、逐欄位型別錯誤、不可用值不覆寫、補丁合併（F2 補丁後接 F4 補丁，兩欄位都寫入；同欄位後者覆蓋）、旗標值不被持久化、預載被拒時不提交 `theme` 補丁、原子寫入無暫存檔殘留、啟動清理殘留、`Close()` 逾時（經 `savePrefs` 注入卡住的寫入，最多等 1 秒） | 單元（暫存目錄；草稿的測試斷言舊行為，升 READY 後反過來） |
| 所有結束路徑都經 `quit()` | 靜態檢查（`grep`）：`os.Exit` 只出現在 `quit()` 與偏好設定尚未建立前的 `fail` 路徑（單元測試驗不了這件事） |
| 優先序與旗標：旗標、環境變數、偏好設定、預設；`-no-hd` 與 `-theme original` 的差別；`-hd` 不選 theme；未知旗標值退回預設。`sound` 欄位的優先序由 `docs/spec/007` 的 `resolveMute` 13 種組合承擔 | 單元：`resolveStartup` |
| `CheckTheme(base *Assets, dir string, s int) (*Assets, error)`：雜湊不在基底、尺寸不符、調色盤缺名、非空 `hd` 欄的 PNG 缺檔或尺寸不符被拒絕；部分涵蓋與列序不同被接受；**空 `hd` 欄的列**：`pal` 存在時接受、`pal` 不存在時拒絕（只略過 PNG 檢查）；`base` 為 nil 回明確錯誤，不 panic；成功時回傳載入好的 `*Assets` | 單元（暫存目錄的假 theme，不含原版素材） |
| 基底 theme 逐圖缺漏：維持逐圖退回基底層，不整個拒絕；TSV 層錯誤才拒絕 | 單元（假素材） |
| `Assets.ErrorStats() (n, first)` 帶鎖：並行 `Get`（合成執行緒 `append`）與讀取在 `-race` 下無競爭；`n` 單調不減（已套用的 `Assets` 不 `Release`）；前端 60 秒檢查只在 `n` 比基準增加時記一行（注入記錄器，不逐筆），記錄後基準前進，`n` 不變時第二次檢查不記；進入 applying 時基準設為當時的 `n`（預載階段的失敗不重複記）；被拒路徑在 `Release` 之前讀取（用 `failed > 0` 的案例證明，日誌含首筆原因；`(0, 0)` 沒有 `Errors` 項目，用固定文字） | 單元（`-race`，假素材；指令 `tools/play.sh test-hd`） |
| 保留鍵：F2、F3、F4 不在 `specialKeys` 表內；F1 至 F4 與無修飾、Ctrl、Alt、Ctrl 加 Alt 的組合逐一斷言 `reservedKeyAction` 的結果；Shift、Meta 視為無修飾 | 單元 |
| **F1 至 F12 的枚舉**：經注入的 `pressDuration` 逐鍵模擬按下，列出「會被轉成遊戲事件」的集合（`inputSink` 記錄），斷言不含 F1 至 F4；控制組：模擬按下 Enter 或方向鍵時集合非空（偵測器不是恆空） | 單元（比 `Input` 呼叫計數有鑑別力：計數為零恆成立） |
| 邏輯畫面固定：`Layout` 在每個 theme 狀態下恆為 1280x800，游標換算恆為 `x/2`、`y/2` | 單元（用 `gameSession` 假實作，不用反射檢查欄位不存在） |
| **`Compose` 快照（決定性）**：假畫面至少兩個戳記，假素材 A、B 的顏色不同，素材以 `writeTheme` 這類暫存目錄函式建出（真 PNG，不含原版）。`Assets.SetGetHook` 在第一個戳記的第一次 `Get` 時（進入 `Get`、查快取之前）同步呼叫 `Composer.SetAssets(B)`；斷言整幀輸出逐位元等於只用 A 的結果。**負對照**：`rereadPerStamp` 模式讓 `Compose` 每個戳記以 `c.A.Load()` 重讀，此時第二個戳記取到 B，輸出必須不同，否則判測試無效（`c.A.Load()` 是合法的原子讀取，所以 `-race` 不會先報競爭而掩蓋鑑別力）。統計式輔助：`GOMAXPROCS` 至少 2，固定 N 不小於 200 幀，切換者每幀與合成者以通道交握（不跑自由競速），每幀輸出必須逐位元等於全 A 或全 B，且兩種都至少出現一次，否則判無效 | `go test -race`（`tools/play.sh test-hd`），不需原版與 `hd/`，不 skip |
| **`Release` 與 `Compose` 並行**：一個 goroutine 連續 `Compose` 假畫面，另一個連續 `Release`（素材是真 PNG，讓 `Get` 能重新解碼），每幀輸出逐位元等於參考輸出 | `-race` 單元 |
| **`hdView` 世代與暫停（決定性）**：假 `frameSource`，`Seq` 必須從 1 起（`last` 歸零的哨兵是 0，`Seq ＝ 0` 的畫面永遠不會被合成；真實 `Session` 從 1 起）；可設為「不提供新 `Seq`」的靜態畫面；畫面含至少一個通過驗證的戳記（用匯出欄位建立，`hd.LoadAssets` 指向只有表頭的暫存 TSV，不需真 PNG）。**區分 A、B 用 `pubFrom`（最近一次發佈用的素材指標），不用像素**：雜湊不在清冊時 `Get` 回 nil，輸出與素材無關，`writeTheme` 的 PNG 又是 alpha 全 0（`drawStamp` 直接略過），兩者都分辨不出 A、B；`Composer` 是否真的用該素材由第 261 列旁的 `hd` 套件快照測試負責。控制點：`SetGetHook`（A 與 B 各裝一次性阻塞鉤子，進入 `Get` 時送出 `inCompose` 訊號並阻塞到測試放行）。**負向斷言的同步點是屏障**：`run` 是單一 goroutine，B 的 `Compose` 開始時，A 那一輪的發佈決定必然已做完，所以等 B 的 `inCompose` 之後才斷言。子項：(1) 卡住 A，`SetAssets(nil)`，放行 A，等 `discards ＝ 1`（丟棄路徑在 `mu` 下遞增），此刻斷言 `pub ＝ 0` 且 `ready` 為空；(2) 卡住 A，`SetAssets(B)`，放行 A，等 B 的 `inCompose`，此刻斷言 `pub ＝ 0` 且 `ready` 為空，放行 B，等 `pub ＝ 1`，斷言 `pubFrom ＝ B`，在**不提供新 `Seq`** 的來源上進行（涵蓋 `last` 重設與素材世代一起改變）；(3) 起點寫死：A 已發佈（`pub ＝ 1`）→ `SetAssets(nil)` → 等 `run` 看到 `nil`（`seenEpoch` 更新，以 `run` 的輪次計數為訊號）→ 靜態畫面（不提供新 `Seq`）→ `SetAssets(B)`，等 `pub ＝ 2`，斷言 `pubFrom ＝ B`（恢復路徑，涵蓋暫停輪次的 `seenEpoch` 更新與 `last` 重設；起點若是以 `nil` 建立的 `hdView`，`last` 本來就是 0，沒有鑑別力；起點若不先發佈 A，「等 `pub ＝ 1`」立刻成立）；(4) `ready` 為空時 `writePNG` 回哨兵 `errNoFrame` 且不複製，`upload` 回 false；退回原版快照並記一行的邏輯在 `game.screenshot`，用 `gameSession` 假實作另測；`writePNG` 假設 640x480 幾何，測試用滿尺寸的假畫面；(5) HD 到 HD 在停機（`Seq` 不再增加）時，`upload` 在 `ready` 為空期間回 false、新畫面發佈後把它放進 `imgHD`（以發佈計數比對）。**負對照逐子項獨立**：子項 (1)、(2)、(3) 各寫成 `func scenarioN(t, mode) error`（不呼叫 `t.Fatal`），正常模式回 nil；`skipEpochCheck` 模式繞過 `epoch` 的兩個用途（發佈條件與 `last` 重設）；`TestHDViewNegativeControl` 對每個子項**分別**斷言 skip 模式回 non-nil，任一子項在 skip 模式回 nil 即判負對照無效（Go 沒有「預期失敗」的子測試）。不可合併成單一 `scenario`：skip 模式會在 (1) 就回 error，(2)、(3) 從未執行，鑑別力沒有各自證明。skip 模式下各子項的預期：(1) A 被發佈，`discards` 恆為 0，等 `discards ＝ 1` 逾時；(2) 屏障處 `pub ＝ 1`，斷言失敗；(3) 靜態畫面不重合成，等 `pub ＝ 2` 逾時。主體內所有等待帶逾時並回 error（skip 模式下屏障可能永遠等不到）。每個測試用 `t.Cleanup` 先放行所有鉤子再 `close()`（`close()` 的 `wg.Wait()` 會在阻塞的鉤子上永遠不回） | `-race` 單元（`tools/play.sh test-play`，`HR_RACE=1`） |
| **切換狀態機與 `onResult`**（假 `assetLoader`、`viewControl`、`holder`、注入 `clock`）。`onResult` 三條路徑各一：(1) `err != nil`：丟棄，目標在回報前 `Release`；(2) `err ＝ nil` 且 `ok ＝ 0`：`failed > 0` 的案例標為不可用並記一行，日誌含首筆原因（證明 `ErrorStats()` 在 `Release` 之前讀取，載入器的呼叫日誌順序為 `ErrorStats`、`Release`、回報）；`(0, 0)` 案例用固定文字；`nextTheme` 略過；(3) `err ＝ nil` 且 `ok > 0`：接受，進入 applying。**計時器路徑的逾時計數**：注入永遠不回報的載入器，計時器觸發後取消 `ctx`，載入器回 `err != nil`，`timerFired` 為真，逾時計數加一並 toast 提示；連續第二次逾時才標為不可用；中間一次成功則歸零；進入 loading 時 `timerFired` 清除（上一個交易以「完整預載被接受」結束時它可能仍為真，下一個交易不得誤算）。**程式結束的取消**：`err != nil` 且 `timerFired` 為假，不計數、不提示；程式結束後 UI 迴圈已停止、`onResult` 不會被呼叫，所以測試直接呼叫 `onResult(err != nil, timerFired ＝ false)` 驗證計數不變，不模擬 UI 迴圈，也不斷言放開 `HoldAdapt` 有實際意義（行程在結束）。**結果優先**：同一次 `Update` 內計時器與結果同時到達，結果優先；載入器「跑完全部後計時器才觸發」（`err ＝ nil`、`ok > 0`）→ 接受，沒有被丟棄的完整預載，逾時計數歸零。loading、cancelling、applying 時 F2 被忽略（不排隊，toast「載入中」）。**呼叫順序**（`viewControl` 與顯示來源的記錄）：HD 目標：`SetAssets(target)` 先於顯示來源變更，顯示來源在 `ready` 非空或 2 秒之後才換，HD 到 HD 顯示來源不變，2 秒逾時仍切換；回 original：顯示來源立刻換成 `imgOrig`，`SetAssets(nil)`，提交 `theme: original` 補丁一次，記 `theme ready: original`，不取得 `HoldAdapt`。**偏好補丁**：applying 結束提交一次 `theme` 補丁（正向）；被拒、丟棄不提交；程式結束時取消。**`holder` 逐路徑一取一放**：成功、部分失敗、被拒、逾時、跑完才計時器觸發、程式結束、HD 到 HD、回 original（不取得，取放次數都是 0）；假實作記錄取放次數，斷言恰好一取一放，且放開在 `onResult` 或 applying 完成之後。`progress` 回呼不直接改 UI 欄位（`-race`）。**`Preload` 與 `Release` 的順序**：`Release` 只由載入 goroutine 在回報前同步呼叫（假載入器記錄呼叫日誌：`Preload`、`ErrorStats`、`Release`、回報的先後），UI 在收到結果前不會啟動第二次預載（狀態機在 loading 與 cancelling 時忽略 F2），所以不存在新 `Preload` 搶在舊 `Release` 前的路徑；常駐 theme 不 `Release`（斷言從 `hd` 切到 `original` 再切回，`Release` 與 `Preload` 呼叫次數都是 0，切回直接 applying） | 單元（`tools/play.sh test-play`，`HR_RACE=1`） |
| **`Preload` 的 `ctx` 取消與 `progress`**（真的 `*Assets`，`hd` 套件）：以 `progress` 回呼當阻塞點，`ctx` 在迴圈頭取消時回 `err != nil` 且 `ok` 可大於 0；迴圈跑完回 `err ＝ nil`（即使 `ctx` 在之後才取消）；清冊 `hd` 欄全空回 `(0, 0, nil)`；`progress` 阻塞期間，另一個 goroutine 對任意雜湊的 `Get` 與 `ErrorStats()` 不被擋、無競爭（防禦性測試：預載只對沒有被合成使用的 `Assets` 進行，正常路徑不會有並行的 `Get`） | `-race` 單元（`tools/play.sh test-hd`） |
| **`HoldAdapt` 視窗規則**：持有狀態是型別 `holdGate{mu, held, dirty}`（`hold() (release func())`、`take() (held int, dirty bool)`，`take` 讀取後清 `dirty`），決策是純函式 `windowVerdict(now, lastCheck, ticks, held, dirty) → skip｜ok｜lower`，兩者都以注入時鐘驅動，不需原版、不需 `Session`。案例（視窗 2 秒，每個視窗的 tick 都落後 5% 以上）：(1) 持有 [0.5, 2.15]：[0, 2.0] skip、[2.0, 4.0] skip（放開設 `dirty`）、[4.0, 6.0] lower（正對照）；(2) 持有完全落在一個視窗內 [0.5, 1.5]（只走 `dirty` 路徑）：[0, 2.0] skip，[2.0, 4.0] lower；(3) 持有跨三個檢查點 [0.5, 4.5]：[0,2]、[2,4]、[4,6] 都 skip，[6,8] lower；(4) 兩個持有重疊（A [0.5, 1.0]、B [0.8, 2.15]）：[0, 2.0] skip（B 仍持有，A 設過 `dirty`），[2.0, 4.0] skip（B 放開設 `dirty`），[4.0, 6.0] lower；(5) `release` 呼叫兩次，計數不得變負，也不吃掉另一個持有者的保護；(6) 持有結束與 `take` 的並行交錯在 `-race` 下正確，不變式：對每次 `release()` 回傳，緊接其後開始的第一次 `take()`（其間沒有別的 `take()` 回傳）必回 `held > 0` 或 `dirty`（不能寫成「放開之後開始的每次 `take()`」：中間另一次 `take()` 已清掉 `dirty` 時，後面的 `take()` 合法地回 `(0, false)`）。`lower` 只表示落後 5% 以上；`adapt` 的下限判斷（`want <= 0`、`interval <= MinInterval` 時直接返回，不改 `lowered`、不記日誌）留在 `Session` 薄包裝，另測一次（`machine.New()` 加 `Session` 字面值，`interval` 要大於 `MinInterval`、`logf` 非 nil，因為 `adapt` 會呼叫 `setInterval` 改 `IRQ0Base`）。靜態檢查：`adapt(` 在 `session.go` 只出現定義與包裝的一次呼叫（`grep -n 'adapt('` 命中的非註解行只有定義與包裝呼叫兩處）。只在持有時直接呼叫 `adapt` 的測試抓不到視窗跨界，不夠 | `apps/hr/runtime`：`HR_RACE=1 HR_TEST_RUN='HoldGate|WindowVerdict' tools/play.sh test-diag`（容器指令以 `grep -v` 管線結尾、沒有 `pipefail`，退出碼不可靠，收據以輸出中的 `PASS`／`FAIL` 行為準）；前端的包裝呼叫在 `test-play` |
| 記憶體：兩個 HD theme 都載入後，預載剛完成與 `runtime.GC()` 後等 5 秒兩個時點的 RSS 與 `HeapInuse`；預載被丟棄後的 RSS（只記錄）；對第 4 節「常駐策略」的通過標準（只設在 GC 之後） | 收據量測，記在 `docs/re` |
| **遊戲不讀 F2、F3、F4 的動態旁證**：dosgolem 在讀鍵函式入口（`0110:9623` getch、`0110:964F` `_kbhit`、`1ACA:000B` 清緩衝，位址見 `docs/re/021` 第 4.1 節）計數；冷啟動到新遊戲與機器人遊玩期間預期為 0。**正對照**：另跑一次走到遊戲結束序列，清緩衝入口的命中必須大於 0（否則判計數方法無效）。`OnCall` 掛函式入口是既有用法，掛 `int 21h` 所在的函式中段位址是否支援未驗證，所以掛入口 | `probe` 的 `-call-args` 或 `OnCall` 計數；需原版，缺檔 skip |
| **端對端**：Xvfb、`--cpus 2` 的容器。以環境變數 `HR_TEST_FREEZE_UI=1` 啟動：統計欄位固定為常數、toast 與載入進度不繪製、F1 面板底色不透明（這只影響測試時的畫面，一般使用不設定，不進文件）。先量原版標題畫面兩張間隔數秒的截圖雜湊是否相同（游標與動畫），不同就裁掉動態區。按 F4 循環，五張 F1 截圖（只比對面板區域）兩兩雜湊不同，第六次回到起點與第一張相同。以 `-theme original` 啟動取得基準標題截圖；按 F2 後以標準錯誤的日誌 `theme ready: hd` 為完成訊號（第 4 節定義：顯示來源換成目標之後才記；不用固定等待），再截圖；**正向檢查**：HD 區域與最近鄰放大的原版相比，差異像素比例超過收據量到的門檻（先記錄比例，門檻在收據定案）；再按 F2 回 `original`，與基準相同。`Lowered` 的觀察來源：標準錯誤的降頻日誌（`session.go` 的「跑不到」字樣）與 `play.log` 的 `lowered=` 欄（每分鐘一行），不讀 F1 面板（凍結後讀不到）。斷言 `Lowered` 在 F2 前後不變，**並有對照**：同一容器、同樣時間長度，以 `-theme hd` 啟動、不按 F2，若 `Lowered` 為真，代表 `hdView` 的持續合成本身會降頻，F2 前後不變的斷言無效 | `tools/play.sh gui-lang`、`gui-theme`（`gui-theme` 另掛 `-v hd:/hd:ro` 與 `-hd /hd`，先 `test -f hd/catalog.tsv`；Xvfb 軟體繪圖下 HD 較慢） |
| 字型載入失敗時退回 ASCII 的 F1 | 單元（字型載入函式變數注入壞字型） |
| `THIRD_PARTY_NOTICES.txt` 含 OFL 與 Adobe 版權，且不含 GNU General Public License；字型授權檔缺檔時 `package.sh` 失敗 | `tools/pkg/verify_*.sh` |
| `OFL.txt` 產生腳本的斷言（版本、映像 ID、無 GSUB／GPOS、name ID、無 GPL 文字、字元表時間戳與 `PASS`） | `tools/gen_ui_fonts.sh` 的實跑收據（`docs/re/022`） |
| `apps/hr/hd` 的測試入口 | 新增 `tools/play.sh test-hd`（`-race`，需 cgo） |

## 11. 原版 oracle 與已知差異

沒有原版對應物。已知差異：F2、F3、F4 不再送進遊戲（`MAIN.EXE` 靜態普查未發現使用，見第 2 節；5 個錯誤等待畫面少了三個可關閉畫面的鍵）；Ctrl 或 Alt 按住時 F1 不再處理（行為變更，現行 F1 沒有任何修飾判斷）；Shift 或 Meta 按住時 F1 至 F4 視為無修飾；`-scale 3` 的最後濾鏡步驟與舊版不同（第 4 節）；toast 與載入進度同一行，使用者提示壓過進度 2 秒；切換等不到新畫面（2 秒）時顯示來源仍會換；HD 目標的切換交易期間（最長約 62 秒：預載逾時 60 秒加等待新畫面 2 秒）真正的落後也不降頻；已套用的 HD theme 常駐，兩個 theme 都載入後記憶體約 400 MiB 加基底與遊戲；被拒與逾時的標記只在本次執行有效、不持久化；遊戲內文字不隨 F4 改變（M10）；AI theme 要等 M8 有成品才可選，且候選圖會直接顯示（決定）；`original` theme 改由前端放大 2 倍，濾鏡由 `-linear` 控制（預設最近鄰）；`-scale 1` 時介面文字縮小難辨；回退字型在 1280x800 邏輯畫面上顯示得比舊版小；停機提示從 (4,4) 移到左下；啟動錯誤視窗不翻譯；`hd/` 的 TSV 壞掉時 `hd-ai/` 成為基底而只過寬鬆載入；啟動預設的 HD theme 不預載，切換時才預載（兩者嚴格度不同）；兩個執行個體同時改偏好設定仍有小窗口；信號終止不保證偏好設定 flush；五種語言翻譯未經母語者審閱。

## 12. 停止線與權利邊界

- 停止線：任何一語言的字串表有缺字（測試失敗）；兩個 HD theme 常駐的 RSS 在 GC 之後超過第 4 節通過標準而無法接受（回到 DRAFT，另立 `Release` 策略）；動態計數發現遊戲讀 F2、F3 或 F4，或日後納入 `OP.EXE`、`END.EXE` 時發現它們使用這三個鍵；需要把 HD 或 AI 素材放進發行包（先問使用者，`AGENTS.md` 第 2 節）；衍生 theme 的檢查規則需要放寬到第 4 節之外；發行前以原檔核對時發現 Noto 有 Reserved Font Name 且子集改名義務成立；預載在雙核容器內仍造成 `Lowered`（對照組 `-theme hd` 不按 F2 的 `Lowered` 為假時才成立）；字形墨跡測試失敗（字型方案要換）。
- 內嵌字型是 OFL，可散布，授權檔隨發行包；不使用原版字型（`CFONT.15`）。
- HD 與 AI theme 的素材是原版美術的衍生物，發行包預設不含（`AGENTS.md` 第 2 節）；本規格不改變這個邊界。
- 截圖（F1 的五種語言、theme 切換）含原版畫面，只放 `workplace/`；放 `docs/images/` 要先問（`AGENTS.md` 第 2 節的截圖例外，新增前先問）。

## 13. 升 READY 前的待辦

1. ~~靜態普查遊戲是否使用 F2、F3、F4~~：已完成（第 2 節，`docs/re/021`）。剩動態計數旁證（第 10 節，含正對照）。
2. ~~字形墨跡雛形~~：已完成（五份子集全部字元畫得出，`docs/re/022`）。
3. ~~查上游 Noto 的 Reserved Font Name~~：上游 `LICENSE` 未宣告（WebFetch 摘要，第 6 節）；發行前以原檔核對一次。
4. 第七輪重審（窄範圍：第 4 節的常駐策略、轉移表、`onResult`、`holdGate`、`hdView` 單一轉移與 `run`，第 10 節對應的 `hdView`、狀態機、`Preload`、`HoldAdapt` 列）。
5. 收據：預載時間在本機的分布、預載前後與峰值 RSS、雙核容器內 F2 前後的 `Lowered`（含 `-theme hd` 不按 F2 的對照）、F1 重畫成本與字形快取、原版標題畫面靜態性、差異像素門檻。

## 14. 審查意見的取捨

| 項 | 處理 |
|---|---|
| 第一版 B1 載入模型 | 預載方案（`Assets.Preload`、`Assets.Release`、世代計數、記憶體預算），啟動時的預設 theme 沿用延遲解碼；第三輪補：狀態機、`Release` 的時機與執行緒、記憶體通過標準 |
| 第一版 B2 併發 | `Composer.A` 改原子指標，取任何素材之前載入一次；第三輪 B2 補：決定性注入測試與 `rereadPerStamp` 負對照，統計式輔助加有效性閘門 |
| 第一版 B3 倍率切換 | 邏輯畫面固定 1280x800；兩張影像各自統一繪製，`-linear` 語意更正 |
| 第一版 B4 F1 面板 | 固定行距 32 與預算；每行單獨繪製、基線公式；第三輪 R3 補：疊加層位置與順序 |
| 第一版 B5、重審 R8 | 推論等級、基準提交、字型雜湊、面數、輸入雜湊、映像識別、`ziphash`、停止線；第三輪補：映像內模組與 LICENSE 實測 |
| 重審 B1 基底 theme | 基底只在 TSV 層錯誤時拒絕、逐圖降級不變、衍生 theme 嚴格檢查；第三輪 R6 補：`pickThemes` 純函式、空 `hd` 欄只略過 PNG 檢查、`CheckTheme` 的 `base` 不可為 nil、`hd/` 壞時的已知差異、啟動預設、`Errors` 輸出規則、兩條路徑嚴格度不同為決定 |
| 重審 B2 測試表 | 端對端凍結統計；`frameSource`；快照測試；第三輪補：縫隙全部命名、枚舉測試取代計數測試 |
| 重審 R1 偏好設定 | 第三輪 R5 補：補丁式合併、`version` 不是 1 時原樣保留、損壞檔改名 `.bad`、結束路徑經 `quit()`、`Close()` 逾時、啟動清理殘留、兩個執行個體改為已知差異 |
| 重審 R5 字型 | 第三輪 B1 補：`--drop-tables+=GSUB,GPOS`（原旗標只留空殼表）、fontTools 版本硬失敗、name ID 7 斷言、`SOURCE.txt` 記版本、`OFL.txt` 只取 OFL 段並斷言無 GPL、`THIRD_PARTY_NOTICES` 驗收加無 GPL；已在容器內實跑確認 |
| 重審 R6 修飾鍵 | 第三輪 R7 補：組合表定案（含 Alt 加 F3），003、004、005 對應句由本規格同一提交修訂，007 不另改 |
| 重審 R7 錯誤視窗與回退 | 啟動錯誤視窗排除、停機提示套用省略規則並移到左下 |
| 第三輪 R1 | `hdView` 世代、同一把鎖、恢復與換素材重設 `last`、F12 的退回、切換時等第一張新畫面（最多 2 秒） |
| 第三輪 R2 | `Session.HoldAdapt` 與測試、收據量測、停止線 |
| 第三輪 R4 | 刪除「續用已解碼的圖」句，狀態機與 `Release` 時機 |
| 第三輪 R8 | 字形墨跡測試、`GlyphAdvance` 辨認字面、`BoundString` 獨立量測、字元數實測（205、206、212、101、232） |
| 第三輪 R9 | `HR_TEST_FREEZE_UI` 定義（測試用、不進文件）、不透明底、完成訊號、正向檢查、`Lowered` 斷言 |
| 第三輪 R10 | 記憶體通過標準（暫定 64 MiB 與 600 MiB，收據後可調整並記錄） |
| 第三輪 R11 | 映像內模組與 LICENSE 實測；`make_notices` 與 `verify_*.sh` 標明哪些已有、哪些未做 |
| 第三輪 R12 | 測試縫隙全部命名，第 164 列改枚舉，第 159 列只用 `Layout` |
| 第一版 S8 | 靜態普查已完成（`docs/re/021`）；動態計數旁證列入測試表與停止線 |
| F3 | 使用者沒有指定聲音開關的鍵，選 F3 因為 F1、F2、F4 已定、相鄰；使用者可改，改了只動第 2 節與 `docs/spec/007` 第 5.4 節 |

### 第四輪重審（第四版）的處理

| 項 | 處理 |
|---|---|
| B1 `HoldAdapt` 擋不住降頻 | 採納：改為視窗規則（與持有時間相交的視窗只重設基準、不評估），決策抽成可注入時鐘的函式 `adaptWindow`（已被第六輪改名為 `windowVerdict`），第 10 節以時間序列測試（跨界案例與正對照）；計數 atomic、`release` 冪等 |
| B2 `hdView` 世代測試無控制點 | 採納：`Assets.SetGetHook`（`Get` 進入時、查快取之前）當決定性控制點，`skipEpochCheck` 負對照，`SetAssets` 與 `epoch` 的順序測試（順序測試已被第五輪取代，`SetAssets` 是單一臨界區） |
| R1 被拒 theme 卡住 F2 循環、`(0, 0)` | 採納：成功數為 0（含 `(0, 0)`）標為不可用，`nextTheme` 略過；逾時可再試一次；失敗模式表補列 |
| R2 切換序列的狀態與順序 | 採納：新增 applying 狀態；`hdView.SetAssets` 先設素材再遞增 `epoch`（已被第五輪取代為單一臨界區）；2 秒逾時的理由改寫並列為已知差異 |
| R3 `Errors` 的併發與基準 | 採納（基準「`Release` 時重設」已被第七版取代：已套用的 `Assets` 不 `Release`，沒有重設）：帶鎖的 `ErrorCount()`、`FirstError()`（已被第五輪取代為 `ErrorStats`，第七版再簡化為 `(n, first)`），基準每個 `Assets` 一份，`Release` 時重設；`-race` 測試 |
| R4 `Release` 與 `Compose` 並行 | 採納：測試列與措辭修正 |
| R5 狀態機與真正的並行 | 採納（四態與串行化已被第七版取代：已套用的 theme 常駐，不再有背景 `Release`）：每個 `Assets` 四態常駐狀態並串行化 `Preload` 與 `Release`；取消只有逾時與程式結束兩個來源 |
| R6 降頻的其他來源、記憶體收斂副作用 | 採納（`SetMemoryLimit` 與下限規則已被第七版取代：不再有 GC 控制）：`-theme hd` 不按 F2 的對照；`SetMemoryLimit` 預設不設，下限規則 |
| R7 端對端 | 採納：`Lowered` 的觀察來源、`theme ready` 的定義 |
| R8 測試縫隙 | 採納：`pressDuration`、`gameSession`、`savePrefs`、表目錄自行解析、墨跡測試控制組（已實作）、`CheckTheme` 簽名與 nil、`SetGetHook` 觸發點、N 不小於 200 與通道交握 |
| R9 偏好設定細節 | 採納：補丁在切換完成後提交、損壞判斷用每次寫入時剛讀到的位元組、頂層非物件視為損壞 |
| R10 跨規格修訂 | 採納：第 2 節改為分工表（006 與 007 同一格內依詞語分工（兩份規格各改不同詞語，升 READY 的先後順序無關））；`003` 第 10 節與第 107 行已先改 |
| R11 證據留存與腳本 | 採納：`docs/re/022` 收據、腳本 pipefail 與 `PASS` 與時間戳檢查、映像 ID 比對、`oto` 已含 |
| R12 已知差異與失敗模式 | 採納：第 11 節與第 8 節補列 |
| R13 | 字形墨跡雛形與 Noto 上游已做；其餘收據在實作後 |

### 第五輪重審（第五版）的處理

| 項 | 處理 |
|---|---|
| B1 `hdView` 世代測試的順序測試與負對照 | 採納：`assets` 與 `epoch` 在同一臨界區一起改（`SetAssets` 是唯一狀態轉移），順序問題不存在，順序測試刪除；`skipEpochCheck` 繞過整個發佈條件，負對照是同一測試函式的 skip 模式子測試（預期失敗）；子測試 (2) 在「不提供新 `Seq`」的 `frameSource` 上驗證 `last` 重設與素材世代一起改變 |
| B2 切換序列沒有恢復暫停中的 `hdView` | 採納：`SetAssets(non-nil)` 即恢復，`SetAssets(nil)` 即暫停並放掉參照；序列 2 用 `SetAssets(nil)`；測試子項 (3) 驗證暫停中恢復的路徑 |
| R1 `HoldAdapt` 細節 | 採納：mutex 保護 `{held, dirty}`、`release` 在鎖內減計數並設 `dirty`；純函式 `windowVerdict` 與薄包裝、`lastCheck` 與 `checkTicks` 搬到 `Session` 欄位、靜態檢查；補四個案例；持有範圍擴大到整個切換交易；`holder` 縫隙；60 秒內不降頻列為已知差異 |
| R2 狀態機 | 採納（守衛優先序與生命週期鎖已被第七版取代：`onResult` 三條，完整的預載即使計時器已觸發也接受；不再有鎖）：守衛優先序（取消先於成功數，`ok > 0` 的取消仍丟棄並 `Release`）；cancelling 收到任何結果一律丟棄並 `Release`；刪除不可達的「目標已常駐」轉移與 applying 目標改變測試；逾時計數連續累計、成功歸零；啟動 theme 視為 resident；生命週期鎖與 `a.mu` 分開；`viewControl` 縫隙；`progress` 回呼的執行緒；`theme` 補丁提交的正向測試 |
| R3 `hdView` 與前端交界 | 採納：上傳以發佈計數比對，不再用遊戲 `Seq`；`run` 以 `epoch` 變化重設 `last`；`SetGetHook` 在 `a.mu` 之外、once、前提與 `atomic.Pointer`；`play` 套件的測試建法（表頭 TSV 加匯出欄位的戳記） |
| R4 `CheckTheme` 簽名 | 採納：`(*Assets, error)` |
| R5 跨規格分工表 | 採納：補 `003` 第 11 節與 `004` 第 108 行兩列；「同一格內依詞語分工」 |
| R6 內部一致性 | 採納：面板最多 21 行、toast 優先序例外、`theme ready` 在 applying 結束時記、失敗模式與已知差異補列 |
| R7 `ErrorStats` 基準 | 採納：`ErrorStats() (gen, n, first)`，基準只由 UI 執行緒讀寫，`gen` 不同視為 `n ＝ 0`（已被第七版簡化為 `(n, first)`，沒有 `gen`） |
| R8 字型證據配對 | 採納：最後一次產生後重跑 `Fonts` 測試，日誌附被測檔案的 SHA-256（`workplace/out/test-fonts.log`，與測試前相同） |

### 第六輪重審（第六版）的處理

| 項 | 處理 |
|---|---|
| B1 `hdView` 測試分辨不出 A、B，負對照無法用 `t.Run` 表達，負向斷言沒有同步點 | 採納：用 `pubFrom`（發佈用的素材指標）區分 A、B，不用像素；負向斷言以 B 的阻塞鉤子當屏障，丟棄路徑加 `discards` 計數；測試主體寫成 `scenario(t, mode) error`，skip 模式回 non-nil，由獨立測試函式驗證，等待帶逾時；`skipEpochCheck` 與 `rereadPerStamp` 改為建構選項；`t.Cleanup` 先放行再 `close()`；假來源 `Seq` 從 1 起 |
| B2 逾時計數在計時器路徑上不會加一 | 採納：守衛集中成單一函式 `onResult`（三條，計時器造成的取消才計數，程式結束不計），結果優先於計時器；cancelling 只是「已請求取消」的顯示狀態；測試列補計時器路徑 |
| B3 離開列沒有放開 `HoldAdapt`，`original` 目標沒有完整路徑 | 採納，且不新增 `releasing` 狀態：根源是切走時背景 `Release`，第七版改為已套用的 HD theme 常駐，沒有背景 `Release`；`Release` 只用在尚未套用的預載被丟棄或被拒，由載入 goroutine 在回報前同步呼叫；每個 HD 目標交易恰好一取一放（被拒、丟棄在 `onResult` 內放開，成功在 applying 完成時放開）；`original` 目標全在 UI 執行緒，即時切換、提交 `theme: original` 補丁、toast 與完成日誌，不取得 `HoldAdapt`（沒有預載，與「持有涵蓋切換交易」不矛盾，因為此路徑沒有可能落後的新工作）；`holder` 逐路徑一取一放測試 |
| B4 生命週期鎖不保證 `Release` 先於新 `Preload` | 採納，由結構消除：`Release` 與新預載之間不再有競爭路徑（見 B3）；`Release` 在回報前同步執行，UI 在收到結果前處於 loading 或 cancelling，忽略 F2；測試以呼叫日誌斷言先後；生命週期鎖與 `Assets` 層級的四態刪除 |
| R1 `ready` 為空的語意、`upload` 與「第一張新畫面」判準 | 採納：判準是 `ready` 非空；`upload` 在 `ready` 為空時回 false；`writePNG` 回哨兵 `errNoFrame` |
| R2 `last`、暫停旗標與 `Composer` 的參照 | 採納：`run` 是 `last` 與 `seenEpoch` 的唯一擁有者，`assets ＝ nil` 即暫停，刪除旗標 |
| R3 序列斷言與測試層次、`ErrorStats` 在 `Release` 前讀取、結果優先、可取消 | 採納：序列斷言併入狀態機測試列；`Preload` 的 `ctx` 取消與 `progress` 阻塞點改在 `hd` 套件測；`ErrorStats` 在 `Release` 前讀取；結果優先；不再有鎖，不需要可取消的鎖等待 |
| R4 四態與逾時上限 | 採納：刪除 `Assets` 層級四態；上限改為約 62 秒 |
| R5 `windowVerdict` 的下限判斷、`holdGate`、案例預期、並行不變式、靜態檢查、指令 | 採納：`lower` 只表示落後 5% 以上，下限判斷留在薄包裝；`holdGate` 型別；案例 (1) 至 (4) 補預期；案例 (6) 補不變式；靜態檢查寫明期望；測試指令逐列寫出 |
| R6 `hdView` 測試細節 | 採納：建構選項、`t.Cleanup` 先放行、`Seq` 從 1 起、子項 (3) 用不提供新 `Seq` 的來源、`game.screenshot` 的退回邏輯用 `gameSession` 假實作另測 |
| R7 措辭與歷史表 | 採納：「連續第二次逾時」統一；第四、五輪表內被取代的項標註；失敗模式表合併 F2 被忽略兩列 |

### 第七輪重審（第七版）的處理

| 項 | 處理 |
|---|---|
| B1 `holdGate` 案例 (6) 的不變式字面為假 | 採納：限定為「緊接 `release()` 之後開始的第一次 `take()`」，並註明不能寫成「每次 `take()`」的原因 |
| B2 `hdView` 負對照併在同一個 `scenario` | 採納：(1)、(2)、(3) 各自一個 `scenarioN`，`TestHDViewNegativeControl` 逐子項斷言 skip 模式回 non-nil；`skipEpochCheck` 同時繞過發佈條件與 `last` 重設，列出各子項在 skip 模式下的預期 |
| R1 子項 (3) 沒有起點 | 採納：A 已發佈 → `SetAssets(nil)` → 等 `run` 看到 nil → `SetAssets(B)`，等 `pub ＝ 2` |
| R2 `ErrorStats` 基準前進與 `first` 語意 | 採納：記錄後基準前進；日誌寫新增筆數與整個 `Assets` 的第一筆原因；切回常駐 theme 基準不重設 |
| R3 記憶體量測時點 | 採納：兩個時點（預載剛完成、GC 後等 5 秒）記 RSS 與 `HeapInuse`，門檻只設在 GC 之後；丟棄後只記錄 |
| R4 `timerFired` 生命週期與程式結束判定 | 採納：進入 loading 時清除；`timerFired` 為假的 `err != nil` 就是程式結束；loading 列補程式結束離開；第 1 條補「計數達 2 標為不可用」；測試直接呼叫 `onResult` |
| R5 `(0, 0)` 的原因、逾時 toast、`Get` 測試措辭 | 採納：`(0, 0)` 用固定文字，`failed > 0` 案例證明讀取順序；逾時 toast；`Get` 測試改為防禦性並行測試 |
| R6 正文殘留舊名詞、第 14 節三列未標被取代 | 採納：刪除正文括號與「取代先前的 `Pause()`、`Resume()`」；三列加標註 |
| R7 `take()` 只在滿 2 秒檢查點呼叫、`test-diag` 退出碼不可靠 | 採納：寫入視窗規則與測試列指令 |
