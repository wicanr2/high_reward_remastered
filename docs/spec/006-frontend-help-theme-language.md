# 006 前端：F1 功能說明、F2 切換 theme、F3 聲音開關、F4 切換介面語言

狀態：DRAFT（2026-10-03，第二版）
審查：審查 A（唯讀，報告在 `workplace/spec-review/006-review-A.md`，不進版控）結論「修訂後可升 READY」，阻擋 B1 至 B5、建議 S1 至 S13。第一版的設計錯誤：載入模型與 `hd.LoadAssets` 不符（B1）、`Composer.SetAssets` 併發設計自相矛盾（B2）、倍率切換違反「不得多送滑鼠事件」（B3）、F1 面板行數與寬度放不下（B4）、缺 READY 最少記錄項目（B5）。本版處理全部阻擋項與建議項，建議項的取捨見第 13 節。尚待第二位審查者或同一位審查者重審。
範圍：`apps/hr/play`（前端）與 `apps/hr/hd`（素材預載與釋放）。涵蓋 F1 說明的內容與語言、F2 在原版與各 HD theme 之間循環、F3 聲音開關（功能見 `docs/spec/007`）、F4 在五種語言之間循環（只切換前端介面文字）、偏好設定、字型內嵌。不含：遊戲內文字（對白、選單、數值表）的多語系，那是里程碑 M10，另立規格；AI theme 的素材本身（M8）；音樂與音效的合成（`docs/spec/007`）。
關聯：`docs/spec/003-runtime-and-frontend`（保留鍵第 7 節，本規格同一提交修訂）、`docs/spec/004-hd-overlay`（Composer、清冊第 3.3 節、素材契約第 6 節）、`docs/spec/005-hang-diagnostics`（Ctrl+D、F1 的最近診斷列）、`docs/spec/007-music-sfx-playback`（F3）。
使用者決定（2026-10-03，`AGENTS.md` 第 12 節）：F1 說明列出功能；F2 切換 theme；F4 切換語言（繁體中文、簡體中文、韓文、英文、日文）。F3 是本專案為聲音開關選的鍵（使用者沒有指定，見第 13 節）。

推論等級用法：confirmed（讀原始碼、位元組或實跑可見）、強推論、假說、未知。沒有標的敘述是設計決定。

## 1. 輸入與工具

| 項目 | 內容 |
|---|---|
| 程式基準 | dosgolem 分支 `hr`，基準提交 `223ed99`；`apps/hr/play`（獨立模組，ebiten v2.9.9）。目前 F1 說明是 `ebitenutil.DebugPrintAt`，只有 ASCII（confirmed，`game.go`） |
| 文字繪製 | `github.com/hajimehoshi/ebiten/v2/text`（v1，已標 Deprecated 但 v2.9.9 仍在）加 `golang.org/x/image/font/opentype`（x/image v0.31.0）。`text/v2` 需要 `go-text/typesetting`，不在 `workplace/gomodcache`，離線不可建置（confirmed，審查 A 讀快取）。`x/image` 的 sfnt 可載入 CID 型 CFF（強推論，讀原始碼，實際子集檔以第 10 節測試驗證） |
| 字型 | Noto Sans CJK Regular。檔案 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`，SHA-256 `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`，19,484,784 bytes，Debian 套件 `fonts-noto-cjk 1:20230817+repack1-3`，字型內部版本 2.004，授權 SIL OFL 1.1（confirmed，審查 A 實測）。TTC 內 10 個字面，全部是 CFF（`OTTO`）：0 ＝ Sans JP、1 ＝ Sans KR、2 ＝ Sans SC、3 ＝ Sans TC、4 ＝ Sans HK、5 到 9 ＝ Sans Mono CJK（JP、KR、SC、TC、HK），Mono 不使用 |
| 子集工具 | fontTools 的 `pyftsubset`（容器 `yuan-analysis:1`）。產生腳本在收據印出 fontTools 版本與 TTC SHA-256，輸入不符就失敗 |
| 建置與測試 | 一律在 Docker（`tools/play.sh`）。`go.mod` 與 `go.sum` 用 `-mod=mod` 加 `GOPROXY=off` 離線補上 x/image 與 x/text（強推論，兩者的 zip 與 ziphash 都在快取，審查 A 讀快取），補上後在 `hr` 分支提交並重產 `engine/patches/` |

## 2. 按鍵

| 鍵 | 功能 | 備註 |
|---|---|---|
| F1 | 開關功能說明（第 3 節） | 沿用 |
| F2 | 切換到下一個 theme（第 4 節） | 新增保留鍵，原本送進遊戲（掃描碼 `0x3C`，confirmed，`keys.go`） |
| F3 | 聲音開關（`docs/spec/007`） | 新增保留鍵，原本送進遊戲（掃描碼 `0x3D`，confirmed，`keys.go`） |
| F4 | 切換到下一種介面語言（第 5 節） | 新增保留鍵，原本送進遊戲（掃描碼 `0x3E`，confirmed） |
| F11、Alt+Enter | 全螢幕 | 沿用 |
| F12 | 存截圖 | 沿用 |
| Ctrl+D | 手動診斷（`docs/spec/005`） | 沿用 |
| Ctrl+Q | 結束 | 沿用 |

- 保留鍵不送進遊戲，也不重複觸發：F1、F2、F3、F4 一律用 `inpututil.IsKeyJustPressed`，不放進 `specialKeys` 的按住重複規則。Alt 按住時 F4 不處理（Windows 與多數 Linux 視窗管理員以 Alt+F4 關閉視窗）。Ctrl 按住時的 F1 至 F4 不處理（同現有 F1 的規則）。
- `keys.go` 移除 F2、F3、F4 三列，更新檔頭註解；同一提交修訂 `docs/spec/003` 第 7 節的保留鍵表與差異表、`README.md` 的按鍵說明、`packaging/README.dist.txt` 的按鍵行。macOS 筆電的 F1 至 F4 預設是亮度與系統功能，要按 Fn；發行包說明要提。
- 已知差異（等級：未知）：遊戲是否讀 F2、F3、F4 沒有普查（`docs/spec/003` 第 7 節；`docs/re/004` 只列出讀鍵服務是 `int 21h` 的 `AH＝08`、`0B`、`0700`，審查 A 從 `workplace/ida/out/int_MAIN.EXE.json` 看到讀鍵呼叫點只有四處）。保留之後若遊戲有用到這幾個鍵，該功能在前端不可用。停止線：升為 READY 之前的靜態普查（`29BB:000F`、`29BB:0007`、`1966:0005`、`1964:0008` 的呼叫者，找對 `0x3C`、`0x3D`、`0x3E` 的比較）若發現遊戲使用，改選別的鍵並回到 DRAFT。

## 3. F1 功能說明

- 繪製在邏輯畫面（第 4 節固定 1280x800）上，半透明深色底，位置左上，邊距 16 像素。字面 em ＝ 22 像素，行距固定 32 像素（`x/image` 以 `hhea` 算出的自然行高是 1.448 em，審查 A 讀字面：ascender 1160、descender -288、unitsPerEm 1000；固定行距避免用自然行高時放不下）。
- 預算：垂直可用 768 像素，最多 24 行；寬度可用 1248 像素。內容：

  | 區塊 | 行 | 內容 |
  |---|---:|---|
  | 標題 | 1 | 名稱與版本 |
  | 按鍵表 | 8 | F1、F2、F3、F4、F11 與 Alt+Enter、F12、Ctrl+D、Ctrl+Q，各一行（鍵名與功能） |
  | 狀態 | 4 | theme（含可用清單）、介面語言、遊戲內文字語言（M10 之前一律「繁體中文（原版）」）、聲音開或關 |
  | 統計 | 3 | 步數、tick、遊戲秒、間隔、是否降頻（`interval`、`lowered`）；堆疊最低 SP、堆疊頂端、開啟檔案數；TPS、FPS。欄位沿用現行 `Session.Stats` 與 `ebiten.ActualTPS/FPS`，標籤翻譯，數字照舊 |
  | 診斷 | 1 | 最近一份診斷的目錄名（ASCII，`docs/spec/005`） |
  | 提示 | 4 | 滑鼠操作遊戲；存檔路徑（1 行）；截圖路徑（1 行）；資料目錄 |
  | 合計 | 21 | 21 行 ＝ 672 像素，在 768 內 |

- 超長處理：路徑與任何超出寬度的行，用 `font.MeasureString` 量，過寬時中間以「…」省略到放得下，不換行。路徑中的字元若不在目前語言的子集內（`GlyphIndex ＝ 0`，例如使用者名稱含罕見漢字），該字以 `?` 取代，不顯示 `.notdef`。
- F1 開著的期間，字元與特殊鍵不送進遊戲（沿用）。`g.stop` 的停機提示與錯誤視窗訊息屬診斷提示，同樣用目前語言（第 5 節）。
- 字型載入失敗時退回 `DebugPrintAt` 的 ASCII 英文版（內容同按鍵表與狀態，英文），標準錯誤記一行；功能不得因字型缺失而不可用。
- 效能：面板內容的靜態部分（標題、按鍵表、狀態）只在 F1 開關、語言、theme、聲音狀態、診斷變化時重畫到快取影像；統計部分另一層，至多每秒重畫一次。`text.Draw` 的字形快取軟上限 512 個，F1 約 250 至 400 個不同字元（強推論，估計），實作時量測重畫成本並記在收據。字面（每個語言一個）建立後長期保留，不在每次切換時重建。

## 4. F2 與 theme

**邏輯畫面固定為 1280x800（遊戲區 640x400 的 2 倍）**，不隨 theme 改變（審查 A 的 S12，同時消除倍率切換造成的滑鼠換算與重配問題，B3）。`Layout` 永遠回傳 1280x800，游標換算永遠是 `x/2`、`y/2`。視窗倍率旗標 `-scale` 只決定視窗大小。

| 代號 | 顯示名稱 | 目錄 | 內容與畫法 |
|---|---|---|---|
| `original` | 原版 | 無 | 直接顯示執行層快照的遊戲區，由前端以最近鄰（`-linear` 時線性）放大 2 倍；不經 `Composer`，`hdView` 暫停 |
| `hd` | HD | `hd/` | 演算法 HD（`docs/re/015`），經 `Composer`（`docs/spec/004`） |
| `ai` | AI 重繪 | `hd-ai/` | AI 重繪（M8），經 `Composer`；缺漏的圖回退原圖（基底層） |

- 可用的 theme ＝ `original` 加上目錄存在且通過檢查的 HD theme。尋找順序與 `hd/` 相同（旗標、環境變數、AppImage 旁、執行檔旁、macOS 的 `Contents/Resources`、目前目錄），目錄名換成 `hd-ai`；旗標 `-hd-ai`、環境變數 `HR_HD_AI`。`-hd` 只決定 `hd/` 目錄，不選 theme。
- **檢查**（`hd.CheckTheme`，載入前執行）：theme 的 `catalog.tsv` 每一列的 `hash` 必須存在於基底清冊（第一個載入的 theme，即 `hd`），且 `w`、`h` 相同；`catalog` 引用的 `pal` 名稱必須存在於該 theme 的 `palettes.tsv`；`hd` 圖檔存在且尺寸為 `2w x 2h`（`docs/spec/004` 第 6 節的契約，逐檔驗證沿用現有 `tools/hd` 的規則，執行時只驗存在與尺寸，內容契約由發行前的驗收工具負責）。允許只涵蓋部分雜湊（AI theme 可以只做一部分，缺的回退原圖）；有任何一項不符就拒絕整個 theme，記一行錯誤，其餘 theme 照常。比對以 `hash` 為鍵的集合，不依列序，不比 `id`、`kind`、`pal` 欄的內容（`id` 是以分號合併的清單，列序不同時會不同，`docs/spec/004` 第 3.3 節）。`palettes.tsv` 不需與基底一致，合成用該 theme 自己的調色盤。
- 辨識（`Overlay`）與 theme 無關：`Overlay` 以像素雜湊建立戳記，清冊只用於統計（confirmed，`capture.go` 的 `Lookup`），所以 `Session` 只開一次 `HDHooks`，用基底清冊，切換 theme 不需重開 `Session`。
- F2：依序 `original → hd → ai → original`（略過不可用的）循環。只有 `original` 可用時 F2 顯示提示「沒有其他 theme」，不改變狀態。
- 啟動時的 theme：`-theme original|hd|ai`，其次偏好設定（第 7 節），其次預設 `hd`（有 HD 目錄時），否則 `original`。`-theme` 的值未知或該 theme 不可用：退回預設並記一行，不致命。`-no-hd` 是「不開 HD 掛鉤」：`HDHooks` 關、不建立 `hdView`、F2 沒有其他 theme，與 `-theme original` 不同（後者保留掛鉤與 `hdView`，F2 仍可切）。
- **素材載入與釋放**（B1）：
  - `hd.LoadAssets` 只讀兩個 TSV（毫秒級）；PNG 在 `Assets.Get` 內延遲解碼，失敗只寫入 `Errors` 並退回基底層（confirmed，`assets.go`）。啟動時的預設 theme 沿用這個延遲解碼（現況，首批戳記會逐張解碼）。
  - 切換到另一個 HD theme 時，先在背景 goroutine 執行新增的 `Assets.Preload(ctx, progress)`（逐筆解碼，回報已解碼與失敗數），完成才切換；載入期間畫面照舊，左上角顯示「載入中」與進度。`docs/re/014` 實測全部載入約 1.65 秒（強推論，目標機器未量）。
  - 逾時 60 秒：以世代計數丟棄逾時後才完成的結果，`ctx` 取消 `Preload`；逾時後再按 F2 重新開始載入（不續用）。載入中再按 F2：忽略，不排隊。解碼成功數為 0 時拒絕切換並提示失敗；有部分失敗時照常切換（失敗的圖退回基底層，數量記一行）。
  - 記憶體預算：每個 HD theme 解碼後約 194 MiB（595 張，原版像素合計 12,709,184 乘 4 位元組乘 4，強推論，審查 A 算出；`docs/re/014` 另記全部載入約 262 MB 含不在清冊的字型圖）。`Assets.cache` 原本沒有淘汰，新增 `Assets.Release()` 清空解碼快取；切走的 theme 在新 theme 套用完成後釋放，所以常駐只有目前 theme，換手瞬間最多兩份（約 390 MiB）。切回已釋放的 theme 要重新預載。
- **換素材的併發**（B2）：`Composer.Compose` 開頭取一次 `A` 快照，之後整幀只用快照。換素材走請求通道：UI 執行緒投遞 `swapReq{assets}`，合成 goroutine 在兩幀之間套用並回覆確認；不使用鎖，不由別的 goroutine 直接呼叫 `SetAssets`。選到 `original` 時投遞「暫停」請求，`hdView` 不再合成，直到再選 HD theme。
- 圖像與截圖：`g.img` 依目前 theme 取來源（原版的 640x480 快照，或 HD 的 1280x960 合成），切換時 `lastSq` 歸零（否則新影像在下一張快照到之前是黑的，審查 A 指出）。截圖路徑依「目前 theme」選（`original` 存 640x400，HD 存 1280x800），不依 `hv != nil`。
- 提示：切換後左上角顯示 2 秒「Theme: HD」之類（該語言的文字）。

## 5. F4 與介面語言

- 語言：`zh-TW` 繁體中文、`zh-CN` 簡體中文、`ko` 한국어、`en` English、`ja` 日本語。顯示名稱用各語言自己的名稱。
- F4 依序循環 `zh-TW → zh-CN → ko → en → ja → zh-TW`。
- 啟動時的語言：`-lang <代號>`，其次偏好設定，其次 `zh-TW`。`-lang` 的值未知：退回預設並記一行，不致命。
- **範圍**：F4 切換的是前端介面文字（F1 說明、F2、F3、F4 的提示、診斷提示與停機提示、錯誤視窗與啟動錯誤訊息、視窗標題）。遊戲內文字（對白、選單、數值表）由原版資料決定，M10 之前不隨 F4 改變，F1 的「遊戲內文字」一行如實標示。M10 完成後，F4 同時選擇遊戲內文字的語言包；沒有語言包的語言，遊戲內文字維持原版繁體中文並在 F1 標示。
- **啟動順序**：解析旗標、讀偏好設定、決定語言、載入字型、找原版目錄。因此啟動錯誤與錯誤視窗用旗標與偏好設定決定的語言，不支援 F4（錯誤視窗沒有按鍵處理）；字型載入失敗時錯誤視窗退回 ASCII 英文（現行的 `errwin.go` 內文本來就只用 ASCII）。
- 提示：切換後左上角顯示 2 秒語言名稱（用目標語言的字面與名稱）。
- 翻譯內容：五種語言的字串是 AI 草稿，未經母語者審閱（字串表檔頭註記）。這是翻譯品質的已知限制，不是規格的錯誤。

## 6. 字串與字型

- 字串表：`i18n.go`，鍵到五種語言的文字。測試要求每個鍵都有五種語言且非空。
- 字型子集：每個語言一份（`zh-TW` 用 TC 字面（`--font-number=3`）、`zh-CN` 用 SC（2）、`ko` 用 KR（1）、`ja` 用 JP（0）、`en` 用 TC 的拉丁字母）。字元表由字串表產生：Go 小程式（或測試）把每個語言的字串倒成 `apps/hr/play/fonts/charset-<lang>.txt` 入版控，加上 ASCII 可印字元、`…`、`?`；不用正規式從 Go 原始碼抓字串（跳脫字元與 `%d` 容易漏）。`pyftsubset` 讀字元表，保留 `.notdef`，丟棄 GSUB、GPOS 與提示（`x/image` 沒有 shaping，用不到），輸出 OTF，保留 name ID 0、7、13、14（版權、商標、授權說明、授權網址）。
- 產生腳本 `tools/gen_ui_fonts.sh`（容器內）：掛載前確認 TTC 存在並核對 SHA-256（第 1 節），不符即失敗（來源不存在時 dockerd 會以 root 建空目錄）；核對 TTC 內指定字面的 name table 名稱（`--font-number` 選到 Mono 會讓拉丁字母變等寬）；收據印出 fontTools 版本、子集大小、字元數。
- 測試：每個語言的字串表字元（排除 `\n`、`\t` 等控制字元）在該語言的字型有字形（`sfnt.GlyphIndex ≠ 0`）；子集檔由 `opentype.Parse` 直接載入成功（不只信旗標）；子集大小記在收據。動態字串（路徑、診斷目錄名）的缺字退回見第 3 節。
- 授權（OFL 1.1，第 2 條要求每份複本帶版權聲明與授權）：通知文字取自字型內嵌的 name ID 0（「© 2014-2021 Adobe」，審查 A 實測，與 Debian 彙總檔的「Google 2010-2012」不同，以字型內嵌為準）、13、14，加 OFL 全文；子集是修改版，OFL 允許。「Noto 沒有 Reserved Font Name」的等級是強推論：Debian 的 `copyright` 與 TTC 全檔沒有出現 "Reserved Font" 字串，上游 `LICENSE` 沒查；升 READY 前查上游。`tools/package.sh` 的 `make_notices`（目前只列 ebiten、purego、hideconsole、xgb、x/sys、x/sync）加入 `golang.org/x/image`、`golang.org/x/text`（`sfnt` 引入 `x/text/encoding/charmap`）與字型授權；發行包的 `THIRD_PARTY_NOTICES.txt` 因此更新。

## 7. 偏好設定

- 檔案 `<資料目錄>/prefs.json`：`{"version":1,"theme":"hd","lang":"zh-TW","sound":true}`。F2、F3、F4 切換時寫入；啟動時讀取。未知欄位忽略（不保留），格式錯誤、未知值一律忽略並用預設；已知值但目前不可用（例如 `"ai"` 而沒有 `hd-ai/`）用預設但不覆寫檔案內容。
- 寫入：先寫暫存檔再 `os.Rename`（兩個執行個體同時寫或中斷時不留下損壞檔）；在背景 goroutine 寫、合併連續請求（快速連按 F2 只寫最後一次），不阻塞 UI 執行緒；失敗只記一行。`dataDir()` 在 `UserConfigDir` 失敗時退到 `os.TempDir()`，此時偏好設定不跨次保留（已知差異）。
- 旗標優先於偏好設定；旗標不寫入偏好設定。

## 8. 失敗模式

| 情形 | 預期 |
|---|---|
| HD theme 的檢查不符（雜湊不在基底、尺寸不符、調色盤缺名、圖檔缺） | 拒絕該 theme，其餘照常，F2 略過它，記一行 |
| 預載全部解碼失敗 | 拒絕切換，提示失敗，留在原 theme |
| 預載逾時（60 秒） | 丟棄結果，留在原 theme，提示逾時，記一行 |
| 預載部分失敗 | 照常切換，失敗的圖退回基底層，記一行（失敗數） |
| 字型缺字 | 字串表內不得有缺字（測試保證）；動態字串以 `?` 取代 |
| 字型載入失敗 | 退回 ASCII 英文的 F1 與錯誤視窗，功能照常 |
| 偏好設定檔損壞或值不可用 | 忽略，用預設 |
| 快速連按 F2 | 載入中再按：忽略，不排隊 |
| 旗標值未知（`-theme`、`-lang`） | 退回預設，記一行，不致命 |

## 9. 玩家路徑與存檔影響

玩家路徑：啟動（可能帶偏好設定）、遊玩中按 F1 看說明、按 F2 換 theme、按 F3 開關聲音、按 F4 換語言。不修改遊戲記憶體、存檔與原版檔案；偏好設定只寫 `prefs.json`。切換 theme 與語言不送任何輸入事件給遊戲，同一輸入下按 F2、F3、F4 前後的 `Session` 狀態雜湊相同（第 10 節測試）。存檔格式與遊戲規則不變。

## 10. 測試

| 承諾 | 測試 |
|---|---|
| theme 循環順序、略過不可用者；只有 `original` 時 F2 不動作 | 單元（純函式） |
| 語言循環順序 | 單元 |
| 字串表五語言齊全、無空字串 | 單元 |
| 字型涵蓋：每個語言的每個字元都有字形；子集由 `opentype.Parse` 載入 | 單元（解析內嵌字型） |
| F1 面板邊界：五種語言各自量全部行（`font.MeasureString`、固定行距），斷言行數乘行距不超過 768、每行寬度不超過 1248（路徑用極端長度輸入） | 單元（不需 GPU） |
| 偏好設定讀寫、損壞、未知值、不可用值、原子寫入與合併 | 單元（暫存目錄） |
| 旗標優先於偏好設定；`-no-hd` 與 `-theme original` 的差別；`-hd` 不選 theme；未知旗標值退回預設 | 單元 |
| `CheckTheme`：雜湊不在基底、尺寸不符、調色盤缺名被拒絕；部分涵蓋被接受；以 `hash` 為鍵不依列序 | 單元（暫存目錄的假 theme，不含原版素材） |
| F2、F3、F4 不在 `specialKeys` 表內，且不被 `sendKeysToGame` 帶進遊戲；Ctrl、Alt 的組合不觸發 | 單元（`keys_test.go` 針對表本身） |
| 游標換算是純函式 `cursorToGame(x, y)`（固定 2 倍）：theme 切換不改變它 | 單元 |
| `Compose` 開頭取素材快照：合成 N 幀並在中途請求換素材，每幀輸出逐位元等於只用 A 或只用 B 的結果；`original` 時 `hdView` 不合成 | `go test -race`，用假素材（`hd/compose_test.go` 的 `TestLoadAssets` 作法），不需原版與 `hd/`，不 skip |
| `Preload`：成功、部分失敗、全部失敗、取消、逾時世代丟棄、`Release` 後記憶體釋放 | 單元（假素材） |
| 同一輸入下按 F2、F3、F4 前後 `Session` 狀態雜湊相同 | runtime 測試（原版缺失時 skip） |
| 端對端：Xvfb 內啟動，按 F4 循環，五張 F1 截圖兩兩雜湊不同，第六次回到起點與第一張相同；按 F2，標題畫面在原版與 HD 之間雜湊改變，切回 `original` 與切換前的原版截圖雜湊相同（用靜態的標題畫面）。截圖存 `workplace/out/`，文字內容人工過目 | `tools/play.sh gui-lang`、`gui-theme`（`gui-theme` 另掛 `-v hd:/hd:ro` 與 `-hd /hd`，先 `test -f hd/catalog.tsv`；Xvfb 軟體繪圖下 HD 較慢，等待時間要夠） |
| 字型載入失敗時退回 ASCII 的 F1 與錯誤視窗 | 單元（注入壞字型） |
| 新增 `tools/play.sh test-hd`（或 `DOSGOLEM_GO_IMAGE=eob-remake-go:1.26.7-ebiten2.9.9 tools/dosgolem.sh go test -race ./apps/hr/hd/`），讓 `apps/hr/hd` 的測試有入口 | 工具 |

## 11. 原版 oracle 與已知差異

沒有原版對應物。已知差異：F2、F3、F4 不再送進遊戲（遊戲是否使用：未知，停止線見第 2 節）；遊戲內文字不隨 F4 改變（M10）；AI theme 要等 M8 有成品才可選；`original` theme 改由前端放大 2 倍而非 1 倍顯示再由 ebiten 放大（畫面內容相同，視窗內縮放濾鏡由 `-linear` 控制）；五種語言翻譯未經母語者審閱。

## 12. 停止線與權利邊界

- 停止線：任何一語言的字串表有缺字（測試失敗）；遊戲被證實使用 F2、F3 或 F4；需要把 HD 或 AI 素材放進發行包（先問使用者，`AGENTS.md` 第 2 節）；`catalog` 比對規則需要放寬到第 4 節之外；上游查出 Noto 有 Reserved Font Name 且子集改名義務成立。
- 內嵌字型是 OFL，可散布，授權檔隨發行包；不使用原版字型（`CFONT.15`）。
- HD 與 AI theme 的素材是原版美術的衍生物，發行包預設不含（`AGENTS.md` 第 2 節）；本規格不改變這個邊界。
- 截圖（F1 的五種語言、theme 切換）含原版畫面，只放 `workplace/`；放 `docs/images/` 要先問（`AGENTS.md` 第 2 節的截圖例外，新增前先問）。

## 13. 審查意見的取捨

| 項 | 處理 |
|---|---|
| B1 | 採預載方案（`Assets.Preload`、`Assets.Release`、世代計數、記憶體預算），啟動時的預設 theme 沿用延遲解碼 |
| B2 | `Compose` 取快照，換素材走請求通道，`original` 時 `hdView` 暫停 |
| B3 | 邏輯畫面固定 1280x800（審查 A 的 S12），倍率切換整個不存在 |
| B4 | 固定行距 32、行與寬度預算、省略規則、邊界單元測試 |
| B5 | 補推論等級、程式基準、字型雜湊與字面編號、停止線 |
| S1 至 S3 | 採納：字型通知取自內嵌 name ID、`make_notices` 擴充、子集產生流程寫完整、動態字串退回 `?` |
| S4、S5 | 採納：`-no-hd` 與 `-theme original` 的差別、未知旗標值、啟動順序與錯誤視窗語言 |
| S6 | 採納並放寬：允許部分涵蓋，以 `hash` 集合比對，調色盤名必須存在；第 4 節引用改為 3.3 與第 6 節 |
| S7 | 採納：`IsKeyJustPressed`、Alt 與 Ctrl 的組合、同步文件 |
| S8 | 列為停止線觸發條件與升 READY 前的靜態普查（本規格不能自己證明，等級標未知） |
| S9 至 S11 | 採納：原子寫入、背景合併、字面長期保留、F1 靜態層與統計層分開 |
| S12 | 採納（見 B3） |
| S13 | 採納：F1 欄位逐項列出；翻譯標註為 AI 草稿 |
| F3 | 使用者沒有指定聲音開關的鍵，選 F3 因為 F1、F2、F4 已定、相鄰；使用者可改，改了只動第 2 節與 `docs/spec/007` 第 5 節 |
