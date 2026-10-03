# 006 前端：F1 功能說明、F2 切換 theme、F3 聲音開關、F4 切換介面語言

狀態：DRAFT（2026-10-03，第三版）
審查：審查 A（唯讀）審第一版（報告 `workplace/spec-review/006-review-A.md`，不進版控）：阻擋 B1 至 B5、建議 S1 至 S13。重審（報告 `006-rereview.md`）審第二版：第一版的 B3、B4 已解決，B1、B2、B5 部分解決，另有 2 個新阻擋與 R1 至 R10。第三版處理全部：基底 theme 的處理（重審 B1）、測試表兩列無法執行與 `Compose` 快照缺鑑別力（重審 B2）、偏好設定、預載殘留與記憶體、繪製統一、字型旗標與授權檔、保留鍵措辭、錯誤視窗範圍、輸入雜湊與端對端細節。處理對照見第 14 節。修正後需要第三輪重審才能升 READY。
流程：工作樹已有本規格部分功能的實作草稿（`hd/theme.go`、`play/prefs.go`、`i18n.go`、字型子集與產生腳本，與 `docs/spec/007` 的聲音接線）。這些檔案是草稿，未提交到 fork 的 `hr` 分支；升 READY 時以本規格為準重審，不符之處改程式。
範圍：`apps/hr/play`（前端）與 `apps/hr/hd`（素材預載、釋放、檢查）。涵蓋 F1 說明的內容與語言、F2 在原版與各 HD theme 之間循環、F3 聲音開關（功能見 `docs/spec/007`）、F4 在五種語言之間循環（只切換前端介面文字）、偏好設定、字型內嵌。不含：遊戲內文字（對白、選單、數值表）的多語系，那是里程碑 M10；AI theme 的素材本身（M8）；音樂與音效的合成（`docs/spec/007`）。
關聯：`docs/spec/003-runtime-and-frontend`（保留鍵第 7 節，本規格同一提交修訂）、`docs/spec/004-hd-overlay`（Composer、清冊第 3.3 節、素材契約第 6 節）、`docs/spec/005-hang-diagnostics`（Ctrl+D、F1 的最近診斷列）、`docs/spec/007-music-sfx-playback`（F3、`-mute`）。
使用者決定（2026-10-03，`AGENTS.md` 第 12 節）：F1 說明列出功能；F2 切換 theme；F4 切換語言（繁體中文、簡體中文、韓文、英文、日文）。F3 是本專案為聲音開關選的鍵（使用者沒有指定，見第 14 節）。

推論等級用法：confirmed（讀原始碼、位元組或實跑可見）、強推論、假說、未知。沒有標的敘述是設計決定。

## 1. 輸入與工具

| 項目 | 內容 |
|---|---|
| 程式基準 | dosgolem 分支 `hr`，基準提交 `223ed99`；`apps/hr/play`（獨立模組，ebiten v2.9.9）。目前 F1 說明是 `ebitenutil.DebugPrintAt`，只有 ASCII（confirmed，`game.go`） |
| 文字繪製 | `github.com/hajimehoshi/ebiten/v2/text`（v1，已標 Deprecated 但 v2.9.9 仍在）加 `golang.org/x/image/font/opentype`（x/image v0.31.0，`ziphash` `h1:mLChjE2MV6g1S7oqbXC0/UcKijjm5fnJLUYKIYrLESA=`；其相依 x/text v0.29.0，`h1:1neNs90w9YzJ9BocxfsQNHKuAT4pkghyXc4nhZ6sJvk=`，兩者的 `.mod`、`.zip`、`.ziphash` 在 `workplace/gomodcache`，離線可補進 `go.mod`／`go.sum`，補後提交並重產 `engine/patches/`）。`text/v2` 需要 `go-text/typesetting`，不在 `workplace/gomodcache`，離線不可建置（confirmed，審查讀快取）。`x/image` 的 sfnt 可載入 CID 型 CFF（子集檔以第 10 節測試驗證） |
| 字型 | Noto Sans CJK Regular。檔案 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`，SHA-256 `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`，19,484,784 bytes，Debian 套件 `fonts-noto-cjk 1:20230817+repack1-3`，字型內部版本 2.004，授權 SIL OFL 1.1（confirmed，審查實測）。TTC 內 10 個字面，全部是 CFF（`OTTO`）：0 ＝ Sans JP、1 ＝ Sans KR、2 ＝ Sans SC、3 ＝ Sans TC、4 ＝ Sans HK、5 到 9 ＝ Sans Mono CJK（JP、KR、SC、TC、HK），Mono 不使用 |
| 子集工具 | `tools/gen_ui_fonts.sh`（第 6 節）；fontTools 4.66.1 的 `pyftsubset`（容器 `yuan-analysis:1`，映像識別 `sha256:f9ea24396753f49d…`）；腳本核對 TTC 的 SHA-256，核對面名稱，fontTools 版本不符就失敗 |
| 輸入雜湊 | `hd/catalog.tsv` SHA-256 `34d076c868717aab71dfdc0124aad9c5fa1d1a22d46c333445ffa1c8cf964033`，`hd/palettes.tsv` `7eb992cbc6823b57510f41f3d5267c507f243c7d132c8ef1b965fbd0368983d5`（第 4 節的檢查依賴它們；現有 `hd/` 通過新規則：595 列的 PNG 檔都存在且尺寸為 2w x 2h，24 個調色盤名稱都在 `palettes.tsv`，審查實測） |
| 建置與測試 | 一律在 Docker（`tools/play.sh`，映像 `eob-remake-go:1.26.7-ebiten2.9.9`，識別 `sha256:39d6e05c9abc60a5…`；`tools/dosgolem.sh` 的 `golang:1.24-bookworm` 跑不依賴 ebiten 的 `apps/hr/hd`）。`go.mod`／`go.sum` 用 `-mod=mod` 加 `GOPROXY=off` 離線補上 |

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

- 保留鍵不送進遊戲，也不重複觸發：F1 至 F4 一律用 `inpututil.IsKeyJustPressed`，不放進 `specialKeys` 的按住重複規則。修飾鍵邏輯寫成純函式 `reservedKeyAction(key, ctrl, alt) action`（可單元測試）：Alt 按住時 F4 不處理（Windows 與多數 Linux 視窗管理員以 Alt+F4 關閉視窗）；Ctrl 按住時 F1 至 F4 都不處理。**Ctrl 按住時 F1 不處理是行為變更**：現行 F1 沒有任何 Ctrl 判斷（`game.go`），本規格新增這條，與 F2 至 F4 一致（Ctrl 組合留給將來的功能）。
- `keys.go` 移除 F2、F3、F4 三列，更新檔頭註解；同一提交修訂 `docs/spec/003` 第 7 節的保留鍵表與差異表、`README.md` 的按鍵說明、`packaging/README.dist.txt` 的按鍵行。macOS 筆電的 F1 至 F4 預設是亮度與系統功能，要按 Fn；發行包說明要提。
- 已知差異（等級：未知）：遊戲是否讀 F2、F3、F4 沒有普查（`docs/spec/003` 第 7 節；`docs/re/004` 只列出讀鍵服務是 `int 21h` 的 `AH＝08`、`0B`、`0700`，審查從 `workplace/ida/out/int_MAIN.EXE.json` 看到讀鍵呼叫點只有四處）。保留之後若遊戲有用到這幾個鍵，該功能在前端不可用。**停止線**：升為 READY 之前的靜態普查（`29BB:000F`、`29BB:0007`、`1966:0005`、`1964:0008` 的呼叫者，找對 `0x3C`、`0x3D`、`0x3E` 的比較；任務 #13）若發現遊戲使用，改選別的鍵並回到 DRAFT。

## 3. F1 功能說明

- 繪製在邏輯畫面（第 4 節固定 1280x800）上，半透明深色底，位置左上，邊距 16 像素。字面 em ＝ 22 像素；**每一行各自呼叫 `text.Draw`，基線由呼叫端算**：第 i 行基線 ＝ 上緣 ＋ `Metrics().Ascent`（取整）＋ 32 × i。不使用 `\n`：`text.Draw` 的換行用 `Metrics().Height`（非整數，多行基線會逐行漂移）。em 22 時字面的自然行高是 (1160 ＋ 288) ÷ 1000 × 22 ＝ 31.86 像素（`hhea`：ascender 1160、descender −288、unitsPerEm 1000，審查讀字面），與 32 幾乎相同，所以固定行距 32 不是為了放得下，而是為了基線整齊。
- 預算：垂直可用 768 像素，最多 24 行；寬度可用 1248 像素。內容：

  | 區塊 | 行 | 內容 |
  |---|---:|---|
  | 標題 | 1 | 名稱與版本 |
  | 按鍵表 | 8 | F1、F2、F3、F4、F11 與 Alt+Enter、F12、Ctrl+D、Ctrl+Q，各一行（鍵名與功能） |
  | 狀態 | 4 | theme（含可用清單）、介面語言、遊戲內文字語言（M10 之前一律「繁體中文（原版）」）、聲音開或關 |
  | 統計 | 3 | 步數、tick、遊戲秒、間隔、是否降頻（`interval`、`lowered`）；堆疊最低 SP、堆疊頂端、開啟檔案數；TPS、FPS。欄位沿用現行 `Session.Stats` 與 `ebiten.ActualTPS/FPS` |
  | 診斷 | 1 | 最近一份診斷的目錄名（ASCII，`docs/spec/005`） |
  | 提示 | 4 | 滑鼠操作遊戲；存檔路徑（1 行）；截圖路徑（1 行）；資料目錄 |
  | 合計 | 21 | 21 行 ＝ 672 像素，在 768 內 |

- 超長處理：路徑與任何超出寬度的行，用 `font.MeasureString` 量，過寬時中間以「…」省略到放得下，不換行；停機提示（含現場存檔目錄路徑）與 F2、F3、F4 的提示（含 theme 名稱、載入進度）套用同一規則，寬度預算同為 1248 像素。路徑中的字元若不在目前語言的子集內（`GlyphIndex ＝ 0`，例如使用者名稱含罕見漢字），該字以 `?` 取代，不顯示 `.notdef`。`font.MeasureString` 與 `text.Draw` 的前進量同源（`GlyphAdvance` 加 `Kern`；丟棄 GPOS 後 `Kern` 走 `kern` 表或回 0），量測與繪製一致（confirmed，審查讀 `x/image/font/font.go` 與 `sfnt.go`）。
- 字面不是並行安全的（`opentype.Face`，審查讀原始碼）：字面只在 UI 執行緒使用，測試的 `MeasureString` 不與繪製並行。字面建立後長期保留，每個語言一個，不在每次切換時重建。
- F1 開著的期間，字元與特殊鍵不送進遊戲（沿用）。`g.stop` 的停機提示屬診斷提示，用目前語言（第 5 節）。
- 字型載入失敗時退回 `DebugPrintAt` 的 ASCII 英文版（按鍵表與狀態，英文），標準錯誤記一行；功能不得因字型缺失而不可用。回退字型畫在 1280x800 的邏輯畫面上，`original` theme 的螢幕大小比舊版小一半（已知差異）。
- 效能：面板內容的靜態部分（標題、按鍵表、狀態）只在 F1 開關、語言、theme、聲音狀態、診斷變化時重畫到快取影像；統計部分另一層，至多每秒重畫一次。`text.Draw` 的字形快取軟上限 512 個（以字元與四分之一像素 x 偏移為鍵，超過後只清 60 個 tick 沒用過的，審查讀 `text/text.go`），F1 約 250 至 400 個不同字元（估計）。實作時量測重畫成本並記在收據。
- `-scale 1`（視窗 640x400）時 F1 的 22 像素字縮成約 11 像素，CJK 難辨，列為已知差異；旗標說明建議 `-scale 2` 以上。

## 4. F2 與 theme

**邏輯畫面固定為 1280x800（遊戲區 640x400 的 2 倍）**，不隨 theme 改變（同時消除倍率切換造成的滑鼠換算與重配，第一版 B3）。`Layout` 永遠回傳 1280x800，游標換算永遠是 `x/2`、`y/2`。視窗倍率旗標 `-scale` 只決定視窗大小。

**繪製的統一**：兩種來源各一張影像，切換時只換來源，不重配邏輯畫面。
- `original`：`imgOrig`（640x480，執行層快照的 RGBA）畫成 `GeoM.Scale(2, 2)`，濾鏡由 `-linear` 決定（預設最近鄰）。
- HD theme：`imgHD`（1280x960，`hdView` 合成的畫面）1:1。
- `g.scale` 欄位、toast 位置（`g.scale*gameH-20`）、`Layout`、`newGame` 全部改用常數。
- ebiten 把邏輯畫面放到視窗的最後一步與 `-linear` 無關：整數倍用最近鄰、小於 1 用線性、其他非整數倍用 `FilterPixelated`（confirmed，審查讀 `gameforui.go`）。所以 `-linear` 只影響 `original` 的 2 倍步驟。`-scale 2` 時 `original` 與舊版的畫面內容相同（最近鄰兩次整數放大）；`-scale 1`、`3` 的最後一步濾鏡路徑與舊版不同，畫面內容近似（強推論，依 `gameforui.go` 三個分支，未實跑）。
- 切換時 `lastSq` 歸零（否則新影像在下一張快照到之前是黑的）。截圖路徑依「目前 theme」選（`original` 存 640x400，HD 存 1280x800），不依 `hv != nil`。

| 代號 | 顯示名稱 | 目錄 | 內容與畫法 |
|---|---|---|---|
| `original` | 原版 | 無 | 直接顯示執行層快照的遊戲區；不經 `Composer`，`hdView` 暫停 |
| `hd` | HD | `hd/` | 演算法 HD（`docs/re/015`），經 `Composer`（`docs/spec/004`） |
| `ai` | AI 重繪 | `hd-ai/` | AI 重繪（M8），經 `Composer`；缺漏的圖回退原圖（基底層） |

- 可用的 theme ＝ `original` 加上目錄存在且通過檢查的 HD theme。尋找順序與 `hd/` 相同（旗標、環境變數、AppImage 旁、執行檔旁、macOS 的 `Contents/Resources`、目前目錄），目錄名換成 `hd-ai`；旗標 `-hd-ai`、環境變數 `HR_HD_AI`。`-hd` 只決定 `hd/` 目錄，不選 theme。
- **基底 theme 與檢查**（重審 B1）：
  - 基底 theme ＝ 第一個載入成功的 HD theme（`hd/` 優先；只有 `hd-ai/` 時它就是基底，沒有可比對的對象）。`Session` 的 `HDAssets` 是基底 theme 的 `Assets`（`Overlay` 只用它的清冊做統計，`capture.go` 的 `Lookup`）；沒有任何 HD 目錄時 `HDAssets` 為 nil、不建立 `hdView`、F2 只有 `original`。
  - **基底 theme 只在 TSV 層錯誤時拒絕**（`LoadAssets`：清冊或調色盤缺檔、格式錯誤）。逐圖問題（PNG 缺檔、尺寸不符、調色盤缺名）維持現行行為：該圖退回基底層（原版像素放大），記一行，其餘圖照常。理由：現行 `Assets.Get` 對這些問題逐圖降級；改成「一張壞就整個 HD 關閉」是未經決定的行為變更。
  - **衍生 theme**（`hd-ai/`，以及將來其他）用嚴格的 `hd.CheckTheme(base, dir, S)`：每列的 `hash` 必須存在於基底清冊且 `w`、`h` 相同；引用的 `pal` 名稱必須存在於該 theme 自己的 `palettes.tsv`；`hd` 欄非空的列，PNG 必須存在且尺寸 S×w 乘 S×h（只讀檔頭，內容契約由發行前的驗收工具 `tools/hd` 負責）。**`hd` 欄為空的列略過**（`tools/hd/catalog.py` 產生的清冊列出全部雜湊，沒有 HD 圖的列 `hd` 欄為空，`docs/spec/004` 第 3.3 節）。允許只涵蓋部分雜湊；有任何一項不符就拒絕整個衍生 theme，記一行錯誤，其餘 theme 照常。比對以 `hash` 為鍵的集合，不依列序，也不比 `id`、`kind`、`pal` 欄的內容（`id` 是以分號合併的清單，列序不同時會不同）。`palettes.tsv` 不需與基底一致，合成用該 theme 自己的調色盤。
- 辨識（`Overlay`）與 theme 無關：`Overlay` 以像素雜湊建立戳記，清冊只用於統計，所以 `Session` 只開一次 `HDHooks`，切換 theme 不需重開 `Session`。
- F2：依序 `original → hd → ai → original`（略過不可用的）循環。只有 `original` 可用時 F2 顯示提示「沒有其他 theme」，不改變狀態。
- 啟動時的 theme：`-theme original|hd|ai`，其次偏好設定（第 7 節），其次預設 `hd`（有 HD 目錄時），否則 `original`。`-theme` 的值未知或該 theme 不可用：退回預設並記一行，不致命。`-no-hd` 是「不開 HD 掛鉤」：`HDHooks` 關、不建立 `hdView`、F2 沒有其他 theme，與 `-theme original` 不同（後者保留掛鉤與 `hdView`，F2 仍可切）。
- **素材載入與釋放**：
  - `hd.LoadAssets` 只讀兩個 TSV（毫秒級）；PNG 在 `Assets.Get` 內延遲解碼，失敗只寫入 `Errors` 並退回基底層（confirmed，`assets.go`）。啟動時的預設 theme 沿用延遲解碼（現況，首批戳記逐張解碼）。
  - **切換到任何 HD theme 時**（含從 `original` 切到 `hd`），先在背景 goroutine 對目標 `Assets` 執行 `Assets.Preload(ctx, progress)`（逐筆解碼 `hd` 欄非空的列，回報成功與失敗數；失敗數由 `Preload` 回傳，不讀 `Errors`），完成才切換；載入期間畫面照舊，左上角顯示「載入中」與進度。`docs/re/014` 實測全部載入約 1.65 秒（強推論，目標機器未量，量測見第 10 節）。`Get` 持鎖解碼，所以預載只對「目前沒有被合成使用」的 `Assets` 進行：從 `original` 切到 `hd` 時，`hd` 的 `Assets` 同時是 `Session` 的 `HDAssets`，但 `Overlay` 只讀清冊（`cat`）、不碰解碼快取，預載它安全。
  - 逾時 60 秒：以世代計數丟棄逾時後才完成的結果，`ctx` 取消 `Preload`。逾時後再按 F2 重新開始載入（續用已解碼的圖：`Assets.cache` 保留，這是預期的）。載入中再按 F2：忽略，不排隊。解碼成功數為 0 時拒絕切換並提示失敗；有部分失敗時照常切換（失敗的圖退回基底層，數量記一行）。**取消、逾時、全失敗時，等載入 goroutine 結束後對目標 `Assets` 呼叫 `Release`**，部分解碼的快取（最多約 194 MiB）不留著。
  - 記憶體預算：每個 HD theme 解碼後約 194 MiB（595 張，原版像素合計 12,709,184 乘 4 位元組乘 4 ＝ 203,346,944 bytes ＝ 193.9 MiB，審查重算；`docs/re/014` 另記全部載入約 262 MB 含不在清冊的字型圖）。`Assets.cache` 原本沒有淘汰，新增 `Assets.Release()` 清空解碼快取；切走的 theme 在新 theme 套用之後釋放，所以常駐只有目前 theme，換手瞬間最多兩份（約 388 MiB）。`Release` 之後在背景呼叫 `runtime.GC()` 與 `debug.FreeOSMemory()`（Go 的堆積目標約為上次 GC 後存活量的兩倍，只丟參照不會立刻還給系統；強推論，未量測），收據量 RSS。切回已釋放的 theme 要重新預載。
- **換素材的併發**（重審 B2）：`Composer.A` 改為 `atomic.Pointer[Assets]`，提供 `SetAssets(*Assets)`；`Compose` 開頭載入一次，整幀只用這個快照。換素材可由任何執行緒呼叫 `SetAssets`，不需請求通道與確認機制。`Release` 即使在還有一次 `Compose` 持有舊素材時呼叫也安全（`Get` 會重新延遲解碼，只是讓記憶體短暫回來），所以不需要等合成 goroutine 確認。選到 `original` 時設 `hdView` 的暫停旗標（`atomic.Bool`），`run` 迴圈在暫停時不合成，並**清掉 `ready`／`readySeq`**，恢復後第一張新畫面之前 F12 與 `upload` 不會取到舊 HD 畫面。`hdView` 對畫面來源只依賴介面 `frameSource{ Frame() *hrrt.Frame }`（`*hrrt.Session` 實作），測試用假來源，不需原版。
- 提示：切換後左上角顯示 2 秒「Theme: HD」之類（該語言的文字）。

## 5. F4 與介面語言

- 語言：`zh-TW` 繁體中文、`zh-CN` 簡體中文、`ko` 한국어、`en` English、`ja` 日本語。顯示名稱用各語言自己的名稱。
- F4 依序循環 `zh-TW → zh-CN → ko → en → ja → zh-TW`。
- 啟動時的語言：`-lang <代號>`，其次偏好設定，其次 `zh-TW`。`-lang` 的值未知：退回預設並記一行，不致命。
- **範圍**：F4 切換的是前端介面文字（F1 說明、F2、F3、F4 的提示、診斷提示與停機提示、視窗標題）。遊戲內文字（對白、選單、數值表）由原版資料決定，M10 之前不隨 F4 改變，F1 的「遊戲內文字」一行如實標示。M10 完成後，F4 同時選擇遊戲內文字的語言包；沒有語言包的語言，遊戲內文字維持原版繁體中文並在 F1 標示。
- **啟動順序與錯誤視窗**：解析旗標、讀偏好設定、決定語言、載入字型、找原版目錄。**啟動錯誤視窗（`errwin.go`）不在 F4 的範圍內**：它的內文固定 ASCII 英文、`Layout` 640x400、沒有按鍵處理，維持現狀；要翻譯它需要另定 `Layout` 與換行規則，不在本規格。
- 提示：切換後左上角顯示 2 秒語言名稱（用目標語言的字面與名稱）。
- 翻譯內容：五種語言的字串是 AI 草稿，未經母語者審閱（字串表檔頭註記）。這是翻譯品質的已知限制，不是規格的錯誤。

## 6. 字串與字型

- 字串表：`i18n.go`，鍵到五種語言的文字。測試要求每個鍵都有五種語言、非空，且格式動詞（`%d`、`%s`、`%.0f`）的順序與個數在五種語言一致。
- 字型子集：每個語言一份（`zh-TW` 用 TC 字面（`--font-number=3`）、`zh-CN` 用 SC（2）、`ko` 用 KR（1）、`ja` 用 JP（0）、`en` 用 TC 的拉丁字母）。字元表由字串表產生：`apps/hr/play` 的 `TestGenCharsets`（`HR_GEN_CHARSET=<目錄>`）把每個語言的字元倒成 `fonts/charset-<lang>.txt` 入版控，加 ASCII 可印字元、`…`、`?`；不用正規式從 Go 原始碼抓字串。
- **`pyftsubset` 旗標**：`--layout-features=`（丟棄 GSUB／GPOS；`x/image` 沒有 shaping，用不到）、`--no-hinting`、`--notdef-outline`（保留 `.notdef` 的輪廓）、`--name-IDs=0,7,13,14`（**取代**預設集合 0 至 6：保留版權、商標、授權說明、授權網址；`x/image` 的 `initialize` 不解析 `name` 表，丟掉 1 至 6 可行，這是決定）、`--legacy-kern`、`--recalc-bounds`。預設 `name_IDs` 不含 13、14，不加旗標會被丟掉（審查讀 fontTools 4.46.0 原始碼）。輸出 OTF。腳本末端斷言：輸出不含 GSUB、GPOS 表；name ID 0、7、13、14 都存在。
- **產生腳本 `tools/gen_ui_fonts.sh`**（容器內，掛載前確認來源存在，不符即失敗，因為來源不存在時 dockerd 會以 root 建空目錄）：核對 TTC 的 SHA-256；核對指定字面的 name table 名稱（選到 Mono 字面會讓拉丁字母變等寬）；fontTools 版本不是 4.66.1 就失敗；收據印出版本、子集大小、字元數。輸出入版控並以 `go:embed` 內嵌：`apps/hr/play/fonts/ui-<lang>.otf`、`charset-<lang>.txt`、`SOURCE.txt`（來源、雜湊、版本、旗標）、`OFL.txt`（授權檔）。字元表改了而字型沒有重產（字型過期）時，第 10 節的「每個字元都有字形」測試會失敗。
- 測試：每個語言的字串表字元（排除 `\n`、`\t` 等控制字元）在該語言的字型有字形（`sfnt.GlyphIndex ≠ 0`）；子集檔由 `opentype.Parse` 直接載入成功（不只信旗標）；name ID 0、7、13、14 存在（`sfnt.Font.Name`）；`Metrics().Height` 約 31.86（守住第 3 節的前提）；子集大小記在收據。動態字串（路徑、診斷目錄名）的缺字退回見第 3 節。
- 授權（OFL 1.1，第 2 條要求每份複本帶版權聲明與授權）：`OFL.txt` 的通知文字取自字型內嵌的 name ID 0（「© 2014-2021 Adobe」，審查實測，與 Debian 彙總檔的「Google 2010-2012」不同，以字型內嵌為準）、13、14，加 OFL 全文（取自 Debian 套件 `fonts-noto-cjk` 的 `copyright` 檔 `License: SIL-1.1` 段，不憑記憶寫）；子集是修改版，OFL 允許。「Noto 沒有 Reserved Font Name」的等級是強推論：Debian 的 `copyright` 與 TTC 全檔（ASCII 與 UTF-16BE 都找過）沒有出現 "Reserved" 字串，上游 `LICENSE` 離線無法查；升 READY 前查上游（停止線）。`tools/package.sh` 的 `make_notices`（掛 `$ROOT/workplace:/w`）加入 `oto`、`x/image`、`x/text` 與字型授權檔 `/w/dosgolem/apps/hr/play/fonts/OFL.txt`；發行包的 `THIRD_PARTY_NOTICES.txt` 因此更新。驗收：`tools/pkg/verify_*.sh` 加一項，斷言包內的 `THIRD_PARTY_NOTICES.txt` 含 "SIL OPEN FONT LICENSE" 與 "Adobe"。

## 7. 偏好設定

- 檔案 `<資料目錄>/prefs.json`：`{"version":1,"theme":"hd","lang":"zh-TW","sound":true}`。
- **只寫被切換的欄位**：F2 改 `theme`、F3 改 `sound`、F4 改 `lang`。寫入的流程是讀目前的檔案、只改該欄位、寫回（不是把整個執行中狀態存進去）。所以以旗標或環境變數啟動（例如 `-theme original`、`-mute`、`HR_MUTE`）不會把旗標值寫進檔案，兩個執行個體各自切換不同欄位時也不會互相蓋掉舊值。
- 讀取：逐欄位寬鬆解析（每個欄位單獨解碼，型別錯誤只讓該欄位用預設，不讓整份失敗）；檔案不存在、格式錯誤、`version` 不是 1 一律當作沒有偏好。未知欄位忽略，寫回時**保留**（先前的設計是丟棄，會讓新版寫的欄位被舊版丟掉）。值已知但目前不可用（例如 `"ai"` 而沒有 `hd-ai/`）：用預設，不覆寫檔案內容。
- 優先序（theme、lang、sound 一致）：命令列旗標、環境變數（目前只有 `HR_MUTE`，`docs/spec/007` 第 5.4 節）、偏好設定、預設。
- 寫入：`os.CreateTemp` 建唯一的暫存檔再 `os.Rename`；在背景 goroutine 寫、合併連續請求（快速連按 F2 只寫最後一次），不阻塞 UI 執行緒；失敗只記一行。**結束時 flush**：程式結束（Ctrl+Q、視窗關閉、停機）前等最後一次寫完，最多等 1 秒（F2 後立刻 Ctrl+Q 不漏寫）。`dataDir()` 在 `UserConfigDir` 失敗時退到 `os.TempDir()`，此時偏好設定不跨次保留（已知差異）。

## 8. 失敗模式

| 情形 | 預期 |
|---|---|
| 基底 theme 的清冊或調色盤 TSV 缺檔或格式錯誤 | 該 theme 不可用，記一行；沒有其他 theme 時 `HDAssets` 為 nil，F2 只有 `original` |
| 基底 theme 的個別 PNG 缺檔、尺寸不符、調色盤缺名 | 該圖退回基底層，記一行，其餘照常（現行行為，不變） |
| 衍生 theme 的檢查不符（雜湊不在基底、尺寸不符、調色盤缺名、圖檔缺） | 拒絕該 theme，其餘照常，F2 略過它，記一行 |
| 預載全部解碼失敗 | 拒絕切換，提示失敗，留在原 theme，`Release` 目標素材 |
| 預載逾時（60 秒）或取消 | 丟棄結果，留在原 theme，提示逾時，記一行，`Release` 目標素材 |
| 預載部分失敗 | 照常切換，失敗的圖退回基底層，記一行（失敗數） |
| 字型缺字 | 字串表內不得有缺字（測試保證）；動態字串以 `?` 取代 |
| 字型載入失敗 | 退回 ASCII 英文的 F1，功能照常 |
| 偏好設定檔損壞或值不可用 | 該欄位用預設，不覆寫檔案內容 |
| 快速連按 F2 | 載入中再按：忽略，不排隊 |
| 載入 theme 期間切換語言或聲音 | 照常生效（兩者與素材載入無關），載入進度提示改用新語言 |
| 旗標值未知（`-theme`、`-lang`） | 退回預設，記一行，不致命 |

## 9. 玩家路徑與存檔影響

玩家路徑：啟動（可能帶偏好設定）、遊玩中按 F1 看說明、按 F2 換 theme、按 F3 開關聲音、按 F4 換語言。不修改遊戲記憶體、存檔與原版檔案；偏好設定只寫 `prefs.json`。切換 theme、聲音與語言不送任何輸入事件給遊戲（第 10 節以純函式測試：F2、F3、F4 的處理結果不含 `Session.Input`）。存檔格式與遊戲規則不變。

## 10. 測試

純函式清單（讓測試不依賴 ebiten 與 GPU）：`nextTheme(cur, avail)`、`nextLang`、`resolveStartup(flags, env, prefs, available)`、`reservedKeyAction(key, ctrl, alt)`、`panelLines(lang, face, info)`（行組裝與省略）、`updatePrefs(path, func(*prefs))`。

| 承諾 | 測試 |
|---|---|
| theme 循環順序、略過不可用者；只有 `original` 時 F2 不動作 | 單元：`nextTheme` |
| 語言循環順序與解析 | 單元（已有） |
| 字串表五語言齊全、無空字串、格式動詞一致 | 單元（已有） |
| 字型涵蓋：每個語言的每個字元都有字形；子集由 `opentype.Parse` 載入；name ID 0、7、13、14 存在；`Metrics().Height` 約 31.86 | 單元（解析內嵌字型） |
| F1 面板邊界：五種語言各自量全部行（`font.MeasureString`、固定行距），斷言行數乘行距不超過 768、每行寬度不超過 1248（路徑、停機提示、theme 載入提示用極端長度輸入） | 單元：`panelLines`（不需 GPU） |
| 偏好設定：往返、損壞、版本不明、逐欄位型別錯誤、未知欄位保留、不可用值不覆寫、只改被切換的欄位（旗標值不被持久化）、原子寫入無暫存檔殘留、合併、結束時 flush | 單元（暫存目錄，部分已有） |
| 優先序與旗標：旗標、環境變數、偏好設定、預設；`-no-hd` 與 `-theme original` 的差別；`-hd` 不選 theme；未知旗標值退回預設 | 單元：`resolveStartup` |
| `CheckTheme`：雜湊不在基底、尺寸不符、調色盤缺名、PNG 缺檔、尺寸不符被拒絕；部分涵蓋與空 `hd` 欄被接受；以 `hash` 為鍵不依列序 | 單元（暫存目錄的假 theme，不含原版素材；已有） |
| 基底 theme 逐圖缺漏：維持逐圖退回基底層，不整個拒絕；TSV 層錯誤才拒絕 | 單元（假素材） |
| F2、F3、F4 不在 `specialKeys` 表內；Ctrl、Alt 的組合不觸發 | 單元：表本身加 `reservedKeyAction` |
| 邏輯畫面固定：`Layout` 在每個 theme 狀態下恆為 1280x800，`game` 不再有倍率欄位 | 單元 |
| `Compose` 快照：另一 goroutine 持續呼叫 `SetAssets` 在 A 與 B 之間切換，同時合成固定的假畫面（假戳記、顏色不同的假素材）N 幀，每幀輸出必須逐位元等於只用 A 或只用 B 的結果；負對照：把 `Compose` 改成每個戳記重讀 `c.A` 時此測試失敗（`go test -race`） | `go test -race`，假素材，不需原版與 `hd/`，不 skip |
| `hdView` 暫停與換素材：假 `frameSource`；暫停後不合成，`ready`／`readySeq` 清空；恢復後第一張才上傳 | 單元 |
| `Preload`：成功、部分失敗、全部失敗、取消、逾時世代丟棄（注入慢速載入與時鐘）、`Release` 後 `len(cache) ＝ 0`；失敗後目標素材被 `Release`；`hd` 欄空的列不計入分母 | 單元（假素材，已有大部分） |
| 記憶體：預載前後與 `Release` 後的 RSS | 收據量測（單元只能斷言快取為空），記在 `docs/re` |
| F2、F3、F4 不產生遊戲輸入事件 | 單元：處理函式的輸出不含 `Session.Input` 呼叫（用注入的記錄器） |
| 端對端：Xvfb 內啟動，以 `HR_TEST_FREEZE_UI=1`（統計欄位固定為常數，toast 與載入進度不計）啟動；按 F4 循環，五張 F1 截圖（只比對靜態層區域）兩兩雜湊不同，第六次回到起點與第一張相同；以 `-theme original` 啟動取得基準標題截圖，按 F2 後標題畫面（等 toast 消失）在 HD 區域與基準雜湊不同，再按 F2 回 `original`，與基準相同。先量原版標題畫面兩張間隔數秒的截圖雜湊是否相同（游標與動畫），不同就裁掉動態區 | `tools/play.sh gui-lang`、`gui-theme`（`gui-theme` 另掛 `-v hd:/hd:ro` 與 `-hd /hd`，先 `test -f hd/catalog.tsv`；Xvfb 軟體繪圖下 HD 較慢，等待時間要夠） |
| 字型載入失敗時退回 ASCII 的 F1 | 單元（字型載入以函式變數注入壞字型） |
| `THIRD_PARTY_NOTICES.txt` 含 OFL 與 Adobe 版權 | `tools/pkg/verify_*.sh` |
| 新增 `tools/play.sh test-hd`（或 `DOSGOLEM_GO_IMAGE=eob-remake-go:1.26.7-ebiten2.9.9 tools/dosgolem.sh go test -race ./apps/hr/hd/`），讓 `apps/hr/hd` 的測試有入口 | 工具 |

## 11. 原版 oracle 與已知差異

沒有原版對應物。已知差異：F2、F3、F4 不再送進遊戲（遊戲是否使用：未知，停止線見第 2 節）；Ctrl 按住時 F1 不再處理（行為變更）；遊戲內文字不隨 F4 改變（M10）；AI theme 要等 M8 有成品才可選；`original` theme 改由前端放大 2 倍，濾鏡由 `-linear` 控制（預設最近鄰）；`-scale 1` 時介面文字縮小難辨；回退字型在 1280x800 邏輯畫面上顯示得比舊版小；啟動錯誤視窗不翻譯；五種語言翻譯未經母語者審閱。

## 12. 停止線與權利邊界

- 停止線：任何一語言的字串表有缺字（測試失敗）；遊戲被證實使用 F2、F3 或 F4；需要把 HD 或 AI 素材放進發行包（先問使用者，`AGENTS.md` 第 2 節）；衍生 theme 的檢查規則需要放寬到第 4 節之外；上游查出 Noto 有 Reserved Font Name 且子集改名義務成立。
- 內嵌字型是 OFL，可散布，授權檔隨發行包；不使用原版字型（`CFONT.15`）。
- HD 與 AI theme 的素材是原版美術的衍生物，發行包預設不含（`AGENTS.md` 第 2 節）；本規格不改變這個邊界。
- 截圖（F1 的五種語言、theme 切換）含原版畫面，只放 `workplace/`；放 `docs/images/` 要先問（`AGENTS.md` 第 2 節的截圖例外，新增前先問）。

## 13. 升 READY 前的待辦

1. 靜態普查遊戲是否使用 F2、F3、F4（任務 #13）。
2. 第三輪重審。
3. 收據：預載時間在本機的分布、預載前後 RSS、F1 重畫成本與字形快取、原版標題畫面靜態性。
4. 查上游 Noto 的 Reserved Font Name。

## 14. 審查意見的取捨

| 項 | 處理 |
|---|---|
| 第一版 B1 載入模型 | 預載方案（`Assets.Preload`、`Assets.Release`、世代計數、記憶體預算），啟動時的預設 theme 沿用延遲解碼；重審補：任何 HD theme 切換都預載、逾時殘留釋放、GC、阻塞語意 |
| 第一版 B2 併發 | `Composer.A` 改原子指標，`Compose` 載入一次（重審 B2：原先的測試沒有鑑別力），不需請求通道；`original` 時 `hdView` 暫停並清畫面 |
| 第一版 B3 倍率切換 | 邏輯畫面固定 1280x800，倍率切換不存在；重審 R3：兩張影像各自統一繪製，`-linear` 語意更正 |
| 第一版 B4 F1 面板 | 固定行距 32 與預算；重審 R4：每行單獨繪製、基線公式，理由更正 |
| 第一版 B5、重審 R8 | 補推論等級、基準提交、字型雜湊、面數、`hd/catalog.tsv` 與 `palettes.tsv` 雜湊、映像識別、`ziphash`、停止線 |
| 重審 B1 基底 theme | 基底只在 TSV 層錯誤時拒絕，逐圖降級不變；嚴格檢查只對衍生 theme；寫明基底選法、缺席與空 `hd` 欄 |
| 重審 B2 測試表 | 端對端凍結統計並裁靜態區；`hdView` 介面 `frameSource`；快照測試改為另一 goroutine 持續切換，並有負對照；空測改為純函式與 `Layout` 常數 |
| 重審 R1 偏好設定 | 只寫被切換的欄位、旗標值不持久化、逐欄位寬鬆解析、保留未知欄位、唯一暫存檔、結束時 flush、優先序統一 |
| 重審 R5 字型 | 旗標串、`name ID` 取代預設、斷言輸出無 GSUB／GPOS、版本不符失敗、產物入版控與內嵌、授權檔路徑、`THIRD_PARTY_NOTICES` 驗收 |
| 重審 R6 | Ctrl 按住時 F1 不處理列為行為變更；修飾鍵邏輯純函式 |
| 重審 R7 | 啟動錯誤視窗不在 F4 範圍；停機提示套用省略規則；回退字型大小為已知差異 |
| 重審 R9 | 端對端先量基準穩定性、以 `-theme original` 取基準、等 toast 消失 |
| 重審 R10 流程 | 實作草稿未提交，升 READY 時以規格為準重審 |
| 第一版 S8 | 列為停止線與升 READY 前的靜態普查（任務 #13） |
| F3 | 使用者沒有指定聲音開關的鍵，選 F3 因為 F1、F2、F4 已定、相鄰；使用者可改，改了只動第 2 節與 `docs/spec/007` 第 5.4 節 |
