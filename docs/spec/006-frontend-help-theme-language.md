# 006 前端：F1 功能說明、F2 切換 theme、F4 切換介面語言

狀態：DRAFT（2026-10-03）
範圍：`apps/hr/play`（前端）與 `apps/hr/hd`（`Composer` 換素材）。涵蓋 F1 說明的內容與語言、F2 在原版與各 HD theme 之間循環、F4 在五種語言之間循環（只切換前端介面文字）、偏好設定的保存、字型內嵌。不含：遊戲內文字（對白、選單、數值表）的多語系，那是里程碑 M10，另立規格；AI theme 的素材本身（M8）。
關聯：`docs/spec/003-runtime-and-frontend`（保留鍵第 7 節）、`docs/spec/004-hd-overlay`（Composer、catalog）、`docs/spec/005-hang-diagnostics`（Ctrl+D、F1 的最近診斷列）。
使用者決定（2026-10-03，`AGENTS.md` 第 12 節）：F1 說明列出功能；F2 切換 theme；F4 切換語言（繁體中文、簡體中文、韓文、英文、日文）。

## 1. 輸入與工具

| 項目 | 內容 |
|---|---|
| 程式基準 | dosgolem 分支 `hr` 的 `apps/hr/play`（獨立模組，ebiten 2.9.9）。目前 F1 說明是 `ebitenutil.DebugPrintAt`，只有 ASCII |
| 文字繪製 | `github.com/hajimehoshi/ebiten/v2/text`（v1）加 `golang.org/x/image/font/opentype`。`text/v2` 需要 `go-text/typesetting`，本機模組快取沒有（`workplace/gomodcache`），離線建置不可用 |
| 字型 | Noto Sans CJK（SIL OFL 1.1），主機 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`（Debian `fonts-noto-cjk`，授權檔 `/usr/share/doc/fonts-noto-cjk/copyright`）。以 `fontTools` 的 `pyftsubset`（容器 `yuan-analysis:1`，fontTools 4.66.1）依各語言的字元表做子集，嵌入程式（`go:embed`）。TTC 內的字面：JP、KR、SC、TC、HK |
| 建置與測試 | 一律在 Docker（`tools/play.sh test-play`、`gui-*`） |

## 2. 按鍵

| 鍵 | 功能 | 備註 |
|---|---|---|
| F1 | 開關功能說明（見第 3 節） | 沿用 |
| F2 | 切換到下一個 theme（見第 4 節） | **新增保留鍵**，原本 F2 送進遊戲（掃描碼 `0x3C`） |
| F4 | 切換到下一種介面語言（見第 5 節） | **新增保留鍵**，原本 F4 送進遊戲（掃描碼 `0x3E`） |
| F11、Alt+Enter | 全螢幕 | 沿用 |
| F12 | 存截圖 | 沿用 |
| Ctrl+D | 手動診斷（`docs/spec/005`） | 沿用 |
| Ctrl+Q | 結束 | 沿用 |

保留鍵不送進遊戲。這是對 `docs/spec/003` 第 7 節保留鍵表的修訂（同一提交一併修訂）。已知差異：遊戲是否讀 F2、F4 未普查（`docs/spec/003` 第 7 節），保留之後若遊戲有用到這兩個鍵，該功能在前端不可用；`docs/re/004` 列的讀鍵服務是 `int 21h` 的 `AH＝08`、`0B`、`0700`，沒有逐畫面的按鍵清單。

## 3. F1 功能說明

- 面板：半透明深色底加文字，位置在畫面左上。文字高度隨邏輯解析度的倍率縮放（倍率 1 用 16 像素，倍率 2 用 32 像素），任一倍率下整個面板在 640x400 遊戲區內放得下。
- 內容（每一行都有五種語言的翻譯，第 6 節）：
  1. 按鍵表：F1、F2、F4、F11 與 Alt+Enter、F12、Ctrl+D、Ctrl+Q，各一行（鍵名與功能）。
  2. 目前狀態：theme 名稱（含可用的 theme 清單）、介面語言、遊戲內文字語言（M10 之前一律「繁體中文（原版）」）。
  3. 統計：模擬步數、tick、遊戲秒、堆疊最低 SP、開啟檔案數、TPS 與 FPS（沿用現有統計，標籤翻譯，數字照舊）。
  4. 最近一份診斷的目錄名（`docs/spec/005`，目錄名是 ASCII）。
  5. 遊玩提示：滑鼠操作遊戲；存檔與截圖的位置（資料目錄的 `saves`、`screenshots`，路徑照實顯示）。
- F1 開著的期間，字元與特殊鍵不送進遊戲（沿用）。
- 字型載入失敗時退回 `DebugPrintAt` 的 ASCII 英文版（內容同第 1、2 項，英文），並在標準錯誤記一行；功能不得因字型缺失而不可用。

## 4. F2 與 theme

**theme 的定義**：一組 HD 素材目錄（`catalog.tsv`、`palettes.tsv`、`provenance.tsv`、`x2/`，`docs/spec/004` 第 4 節）加上顯示名稱。

| 代號 | 顯示名稱 | 目錄 | 內容 |
|---|---|---|---|
| `original` | 原版 | 無 | 不合成，直接顯示執行層的畫面（邏輯倍率 1） |
| `hd` | HD | `hd/` | 演算法 HD（`docs/re/015`），2 倍 |
| `ai` | AI 重繪 | `hd-ai/` | AI 重繪（M8，`docs/re/` 另記），2 倍 |

- 可用的 theme ＝ `original` 加上目錄存在且通過檢查的 HD theme。尋找順序與 `hd/` 相同（旗標、環境變數、AppImage 旁、執行檔旁、macOS 的 `Contents/Resources`、目前目錄），目錄名換成 `hd-ai`；旗標 `-hd-ai`、環境變數 `HR_HD_AI`。
- 檢查：HD theme 的 `catalog.tsv` 與第一個載入的 theme 的 `catalog.tsv` 在 `hash`、`id`、`w`、`h` 四欄必須相同（辨識以原版像素雜湊為準，各 theme 只換 HD 圖）；不同就拒絕該 theme，記一行錯誤，其餘 theme 照常。
- F2：依順序 `original → hd → ai → original`（略過不可用的）循環。只有 `original` 可用時，F2 顯示提示「沒有其他 theme」，不改變任何狀態。
- 啟動時的 theme：`-theme original|hd|ai`，其次是偏好設定（第 7 節），其次預設 `hd`（有 HD 目錄時），否則 `original`。舊旗標 `-no-hd` 等於 `-theme original`。
- 執行中換素材：
  - 只要有任何 HD theme 目錄，`Session` 一開始就開 `HDHooks`（目前的行為：有 HD 目錄就開），辨識用第一個載入的 theme 的 `catalog`，所以切到 `original` 也不需要重開 `Session`。沒有任何 HD 目錄時不開 `HDHooks`（與現況相同），F2 只有 `original`。
  - theme 的 `Assets` 在第一次切到它時於背景 goroutine 載入（`hd.LoadAssets`，約 27 MB 的 PNG），載入期間畫面照舊，顯示「載入中」提示，載入完成才切換；載入失敗留在原 theme 並記一行錯誤。
  - `hdView` 的 `Composer` 在合成 goroutine 內於兩個畫面之間換素材（`Composer.SetAssets`，以鎖保護；換素材不得造成同一幀用到兩套素材）。
  - 邏輯倍率：`original` ＝ 1，HD theme ＝ `hdScale`（2）。切換時重配 `g.img` 與 `g.rgba`，`Layout` 回傳新的邏輯尺寸，視窗與全螢幕狀態不變，滑鼠座標依新倍率換算（`x / g.scale`）。切換不得讓遊戲收到多餘的滑鼠事件。
- 提示：切換後左上角顯示 2 秒「Theme: HD」之類（該語言的文字）。

## 5. F4 與介面語言

- 語言：`zh-TW` 繁體中文、`zh-CN` 簡體中文、`ko` 한국어、`en` English、`ja` 日本語。顯示名稱用各語言自己的名稱。
- F4 依序循環 `zh-TW → zh-CN → ko → en → ja → zh-TW`。
- 啟動時的語言：`-lang <代號>`，其次偏好設定，其次 `zh-TW`。
- **範圍**：F4 切換的是前端介面文字（F1 說明、F2 與 F4 的提示、診斷提示、錯誤視窗與啟動錯誤訊息的文字、視窗標題）。遊戲內文字（對白、選單、數值表）由原版資料決定，M10 之前不隨 F4 改變，F1 的「遊戲內文字」一行如實標示。M10 完成後，F4 同時選擇遊戲內文字的語言包；沒有語言包的語言，遊戲內文字維持原版繁體中文並在 F1 標示。
- 提示：切換後左上角顯示 2 秒語言名稱（該語言的名稱）。

## 6. 字串與字型

- 字串表：`i18n.go`，鍵到五種語言的文字。測試要求每個鍵都有五種語言且非空。
- 字型子集：每個語言一份子集（`zh-TW` 用 TC 字面、`zh-CN` 用 SC、`ko` 用 KR、`ja` 用 JP，`en` 用 TC 的拉丁字母），字元表由該語言的全部字串加 ASCII 可印字元產生（`tools/gen_ui_fonts.sh`，容器內），輸出到 `apps/hr/play/fonts/`，附授權檔與來源版本。測試要求：每個語言的每個字元在該語言的字型有字形（`sfnt.GlyphIndex ≠ 0`）；子集大小記錄在收據。
- 授權：Noto Sans CJK 是 SIL OFL 1.1。發行包的 `THIRD_PARTY_NOTICES.txt` 加入版權與授權全文；子集是修改版，OFL 允許，名稱沿用且 Noto 沒有 Reserved Font Name。
- 效能：文字面板只在內容改變（F1 開關、語言、統計每秒更新）時重畫到快取影像，不是每幀重新排版。

## 7. 偏好設定

- 檔案 `<資料目錄>/prefs.json`：`{"theme":"hd","lang":"zh-TW"}`。F2、F4 切換時寫入（失敗只記一行，不影響遊戲）；啟動時讀取，格式錯誤、未知值一律忽略並用預設。
- 旗標優先於偏好設定。

## 8. 失敗模式

| 情形 | 預期 |
|---|---|
| HD theme 的 `catalog.tsv` 與第一個 theme 不一致 | 拒絕該 theme，其餘 theme 照常，F2 略過它 |
| 切換時素材載入失敗或逾時（載入 60 秒仍未完成） | 留在原 theme，提示失敗，記一行錯誤 |
| 字型缺字 | 該字以字型的 `.notdef` 顯示，不得崩潰；測試保證字串表內沒有缺字 |
| 字型載入失敗 | 退回 ASCII 英文的 F1，功能照常 |
| 偏好設定檔損壞 | 忽略，用預設 |
| 快速連按 F2 | 載入中再按 F2：忽略直到載入完成，不排隊 |

## 9. 玩家路徑與存檔影響

玩家路徑：啟動（可能帶偏好設定）、遊玩中按 F1 看說明、按 F2 換 theme、按 F4 換語言。不修改遊戲記憶體、存檔與原版檔案；偏好設定只寫 `prefs.json`。存檔格式與遊戲規則不變。

## 10. 測試

| 承諾 | 測試 |
|---|---|
| theme 循環順序與略過不可用者；只有 `original` 時 F2 不動作 | 單元（純函式） |
| 語言循環順序 | 單元 |
| 字串表五語言齊全、無空字串 | 單元 |
| 字型涵蓋：每個語言的每個字元都有字形 | 單元（解析內嵌字型） |
| 偏好設定讀寫、損壞與未知值 | 單元（暫存目錄） |
| 旗標優先於偏好設定；`-no-hd` 等於 `-theme original` | 單元 |
| `catalog` 不一致的 theme 被拒絕 | 單元（暫存目錄的假 theme，不含原版素材：只測 `catalog.tsv` 比對） |
| F2、F4 不送進遊戲；Ctrl 按住不送 | 單元（`sendKeysToGame` 與按鍵表） |
| `Composer.SetAssets` 與合成同時進行 | `go test -race`（需原版與 `hd/`，缺檔 skip） |
| 端對端：Xvfb 內啟動，按 F4 循環五次，F1 說明畫面對應各語言的文字（截圖存 `workplace/out/`，人工過目）；按 F2，畫面在原版與 HD 之間改變（雜湊不同）且切回去相同 | `tools/play.sh gui-lang`、`gui-theme` |
| 字型載入失敗時退回 ASCII 的 F1 | 單元（注入壞字型） |

## 11. 原版 oracle 與已知差異

沒有原版對應物。已知差異：F2、F4 不再送進遊戲；遊戲內文字不隨 F4 改變（M10）；AI theme 要等 M8 有成品才可選。

## 12. 停止線與權利邊界

- 內嵌字型是 OFL，可散布，授權檔隨發行包；不使用原版字型（`CFONT.15`）。
- HD 與 AI theme 的素材是原版美術的衍生物，發行包預設不含（`AGENTS.md` 第 2 節）；本規格不改變這個邊界。
- 截圖（F1 的五種語言、theme 切換）含原版畫面，只放 `workplace/` 或 `docs/images/`（`AGENTS.md` 第 2 節的截圖例外，新增前先問）。
