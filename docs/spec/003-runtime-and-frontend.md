# 003 執行層與桌面前端

狀態：READY（2026-10-03）。第一輪審查有阻擋；第二輪的阻擋是 `IRQ0Base` 的標定分頻（17,000，不是 65,536）與驗收項不可執行、引用缺漏，已依原始碼與審查數據修正後升為 READY。第 1 版範圍只含 `MAIN.EXE`；聲音由 `docs/spec/007` 負責，鍵盤普查見 `docs/re/021`；`OP/END`、macOS 實機不在本規格內，列在第 11 節。
日期：2026-10-03
前置：`docs/spec/002-stack-size.md`、`docs/re/008-dosgolem-cold-start-receipts.md`、`docs/re/010-music-subsystem-DRAFT.md`、`docs/re/011-longrun-stack-overflow.md`、`AGENTS.md` 第 2、4、5、14 節。
實作位置：`workplace/dosgolem` 本地分支 `hr`。執行層 `apps/hr/runtime`；前端 `apps/hr/cmd/hr-play`。前端用 ebiten 2.9.9（離線建置映像：本機已有的 `eob-remake-go:1.26.7-ebiten2.9.9`，模組快取內含 ebiten；`go.sum` 由本機快取產生，未經校驗資料庫核對，列為已知限制）。dosgolem 的 `internal/*` 只能由同一個 Go 模組引用，所以 ebiten 依賴只加在 `hr` 分支的 `go.mod`。

## 1. 範圍與排除

範圍：讓玩家用自備的原版檔案，在 Linux、Windows、macOS 的視窗中玩《高報酬戰將》的主程式 `MAIN.EXE`（與 jsdos 版相同的範圍，`docs/re/001`）。
排除：Android；網路功能；HD 替換（`docs/spec/004`）；音樂與音效（`docs/spec/007`）；`OP.EXE`、`END.EXE`、`PSH.EXE`、`SIG.COM`（`HR.BAT` 的其餘步驟，第 3.2 節）。

## 2. 輸入的原版

玩家指定一個目錄，內含原版檔案。前端不內建、不下載、不重新散布任何原版檔案。啟動時檢查：

1. `MAIN.EXE` 存在且 SHA-256 為 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。不符就拒絕啟動並顯示實際雜湊（其他版本的位址與補丁不成立，`docs/spec/002` 第 4 節）。
2. 必要檔案存在且大小相符。清單是 `apps/hr/runtime/required.tsv`，由 `docs/re/source-inventory.tsv` 取 `in_jsdos ＝ 1` 的列、排除 `GAMEFILE.*` 與 `复件 *`，欄位為檔名、大小、SHA-256。缺檔或大小不符就列出檔名並拒絕啟動，不用替代檔。完整雜湊驗證只在 `-verify` 時做。語言包（`docs/spec/008`）有自己的 manifest，由 `Session.Open` 另驗，不併入這份清單。

## 3. 執行層（`apps/hr/runtime`）

`Session` 包住 `machine.Machine` 與 `dos.DOS`，不認識視窗。執行緒模型：一個模擬 goroutine 擁有 `Machine` 與 `DOS`，其他執行緒不直接碰它們。

| 介面 | 作用 |
|---|---|
| `Open(root string, opt Options) (*Session, error)` | 驗證映像（第 2 節）、載入、套用 `docs/spec/002` 的堆疊補丁、`d.Install()`；`Options.SaveDir` 設為 `d.Scratch`（空字串為唯讀，第 5 節）；`Options.LangDir`、`LangDigest`、`SkipLangDigest` 設定語言層與預期輸入摘要（`docs/spec/008` 第 3.1、3.2 節）：語言包驗證失敗時 `Open` 不回錯，改以空 `LangDir` 開啟，並由 `Session.LangStatus()` 回報原因；`LangDir` 非空而 `LangDigest` 為空且未明示 `SkipLangDigest` 時回錯 |
| `Run(ctx)` | 模擬迴圈（第 4 節）。回傳停機原因（第 3.1 節） |
| `Frame() *Frame`、`RequestFrame()` | 最近一個快照：`640x480` 的像素值（`Machine.Planar`，0 至 15）、AC 到 DAC 的對應表、DAC 與模擬步數；`Frame.RGBA` 在使用者的執行緒轉成 RGBA。快照是拉取式：前端每次繪製前呼叫 `RequestFrame`，模擬 goroutine 在下一次滑鼠輪詢指令剛執行完時產生（審查實測 `PlanarRGB` 一次 1.8 至 3.3 ms，推送式每 8 ms 一次會吃掉兩到四成的單核）。快照由模擬 goroutine 逐指令檢查 `d.Mouse.Polls` 的長度，在輪詢指令剛執行完的那一刻產生（遊戲回到等輸入的迴圈）：批次邊界或 tick 邊界取樣時游標矩形完整繪出的比例只有 8% 至 9%（審查實測），輪詢指令剛執行完是 158／159。滑鼠 100 毫秒內沒有輪詢（動畫、載入）時，退回牆鐘 100 毫秒的快照。前端把 `RequestFrame` 的呼叫率限制在 60 Hz 以內（`docs/spec/004` 第 5.1 節）。前端執行緒取用快照，不碰機器 |
| `ScreenPNG() []byte` | 目前畫面的調色盤 PNG（`Machine.Planar` 與 `VGA.DACIndex`，標準庫 `image/png` 預設壓縮），與 `probe -dump-screen-png` 同編碼，供無頭驗收比對雜湊 |
| `Input(ev)` | 把輸入事件放進佇列（第 7 節）；由模擬 goroutine 在指令邊界取出，轉成對 `DOS` 的呼叫 |
| `Stats()` | 步數、`m.Ticks`、模擬秒數、`d.Stats()`、本次最低 `SP` |

`Trim`（清診斷紀錄，`apps/hr/cmd/hrsoak` 的 `trim`）由模擬 goroutine 在滑鼠沒有按住、鍵盤佇列為空時每 200 萬道指令執行一次。

### 3.1 停機條件

沿用 `docs/re/011`：CPU 錯誤；`CS:IP` 進入視訊記憶體位址範圍；堆疊溢位（`SS` 為堆疊段且 `SP` 大於頂端）；程式以結束碼 1 結束（玩家結束遊戲）；結束碼 0（進入片尾，`HR.BAT` 會接著跑 `END.EXE`）；其他結束碼。結束碼 1 關閉視窗。結束碼 0 在第 1 版顯示「遊戲結束」並關閉視窗，不跑 `END.EXE`（第 3.2 節）。其他停機顯示原因並存現場（狀態檔、最近輸入）到使用者資料目錄的 `crash/`。
停機現場（`CrashDump`）的 `info.txt` 內容由 `docs/spec/005` 擴充（2026-10-03）：第一行是固定標記，其後沿用原欄位，再加暫存器、呼叫鏈、最近呼叫、服務中斷等區段；簽章不變。疑似 hang（T2）與手動觸發（T3）的非致命診斷由 `Options.DiagDir`、`HangSeconds`、`OnDiag` 與 `RequestDiag` 控制，細節見 005。


### 3.2 啟動鏈

`HR.BAT` 的步驟：`PSH RAIN.PCX`、`PSH H-TXT.PCX`、`sig`、`OP`、`MAIN`、`END`、`sig /r`（`docs/re/004`）。第 1 版只跑 `MAIN`（與 jsdos 版相同）。`OP.EXE`、`END.EXE`、`SIG.COM` 在 dosgolem 的冷啟動收據尚未做（`docs/re/008` 第 5 節），做完並另立規格後才納入。

## 4. 計時

遊戲時間由計時器中斷次數決定（`machine.Machine.Ticks`）。PIT 通道 0 的 65536 分頻是 dosgolem 的開機預設，原版遊戲沒有寫 PIT 埠（`docs/re/010`）。dosgolem 以「每 `IRQ0Every` 道指令送一次中斷」模擬計時器，預設約 636,000（`docs/re/008` 第 1 節：30,000,000 道指令送 47 次）。

- 模擬 goroutine 每個回合計算牆鐘時間應有的 tick 數（18.2065 Hz），不足就執行，超前就睡眠。
- `IRQ0Every` 不能直接指定：`RecalcIRQ0` 依 `IRQ0Base` 與 PIT 分頻重算。`IRQ0Base` 的標定分頻是 17,000（`machine.go` 的 `recalcIRQ0`、`pit.go`），所以分頻 65536 時的間隔是 `IRQ0Base × 65536 ÷ 17000`：預設 `IRQ0Base ＝ 165,000` 對應 636,085。要在分頻 65536 得到間隔 `E`，設 `IRQ0Base ＝ E × 17000 ÷ 65536` 並呼叫 `RecalcIRQ0()`。之後聲音驅動若寫 PIT，重算仍依 `IRQ0Base` 按比例縮放。
- 預設間隔取 300,000（`IRQ0Base ≈ 77,820`），依據：審查實測 636,085 時單核約 0.85 至 1.34 倍速，沒有餘量；審查以 `hrsoak -tick 300000`（直接設 `IRQ0Every`）量到 `simSec` 與預設值成比例，短跑未見停機。這不是經 `IRQ0Base` 的路徑，兩者在分頻不變時等價，但經 `IRQ0Base` 的路徑未直接量測（第 10 節）。
- 跑不到 18.2 Hz 時降低間隔：每 2 秒檢查，落後超過 5% 就調為原值的 90%，下限 150,000（`IRQ0Base ≈ 38,910`），並寫進紀錄。一旦調降不再調回。
- 改變間隔不改變遊戲內時序的單位（動畫由 tick 驅動），但每個 tick 間可執行的指令數變少。這是模擬較慢的機器，不是改變遊戲邏輯；遊戲邏輯依賴指令數的證據：未發現，未證明沒有。閒置時約 84% 的指令用在游標的保存、貼圖、還原（取樣 100 萬道指令，`1C57` 60%、`1F69` 23%），所以間隔降低主要減少游標重繪的次數。

## 5. 存檔與檔案

原版把存檔寫在遊戲目錄的 `GAMEFILE.000` 至 `.004`，並更新 `FNAME.DAT`（遊戲以 `fopen "wt+"` 建立）。前端不寫原版目錄：`Options.SaveDir`（前端預設在使用者資料目錄的 `high_reward/saves`）是 dosgolem 的暫存層（`d.Scratch`，dosgolem `docs/spec/009-scratch-writes`），寫入時複製到暫存層再寫。已實測（`docs/re/012` 第 2 節）：讀取槽 0，開系統選單，存入槽 2，暫存層出現 `GAMEFILE.002`（31839 bytes）與 `fname.dat`（158 bytes），原版檔案 MD5 不變；重開後選單的槽 2 列顯示新日期。

限制與要求：

- 暫存層的檔名保留遊戲開檔時的大小寫（`fname.dat`），讀取時要大小寫不分地比對原版目錄與暫存層（實測成立）。
- 刪除（`AH=41`）與改名（`AH=56`）在暫存層沒有墓碑：原版目錄的檔案無法被「刪掉」。遊戲存檔流程是否用到：實測的存檔（覆寫既有槽）沒有用到；存入新槽與其他路徑未驗，驗收要涵蓋。
- DOS 日期在 dosgolem 固定為 1993-01-01（`int 21h AH=2A`），所以存檔列顯示該日期。執行器的 play 模式改用主機時間（需要 dosgolem 增加一個時鐘來源；`AH=2C` 已用 `d.clock()`）。執行器的 play 模式不要求決定性。
- 語言層（`docs/spec/008` 第 3.1 節）：`Options.LangDir` 非空時，檔案解析順序是暫存層、語言層、原版目錄，語言層缺檔回退原版；以寫入模式開語言層的檔回存取被拒，不複製進暫存層。`LangDir` 為空時行為與沒有語言層相同。

## 6. 畫面

- `Frame` 是 `640x480`（模式 12h），遊戲區是 `640x400`，位於第 40 至 439 列（`docs/re/006` 第 2 節）。上下各 40 列黑邊不顯示。
- 顏色用 `Machine.PlanarRGB`（已含 EGA 屬性暫存器到 DAC 的對應，遊戲呼叫 `AX=1000` 共 9 處）。不直接用 `Indexed` 加 `Palette`。
- 前端以整數倍放大優先，視窗尺寸不是整數倍時等比縮放並置中，其餘填黑。`Composer` 的基底層恆為最近鄰；`-linear` 只影響 `original` theme 的 2 倍放大步驟（`docs/spec/006` 第 4 節）。

## 7. 輸入

| 來源 | 轉換 |
|---|---|
| 滑鼠位置 | 視窗座標扣掉黑邊與縮放，得遊戲區座標，夾在 `[0, 639]`、`[0, 399]`；送入 dosgolem 時加 40 列（`d.MoveMouse` 吃 `640x480` 畫面座標；`-clicks` 與 `hrsoak` 的座標也是這個系統） |
| 滑鼠左右鍵 | 按下後至少維持到遊戲輪詢 3 次才放開（`d.Mouse.Polls`），避免遊戲來不及讀到短按 |
| 鍵盤 | 遊戲只用 `int 21h` 的 `AH=08`、`0B`、`0700`（`docs/re/004`）讀鍵盤，dosgolem 這幾個服務只讀 `d.Stdin`。所以鍵盤事件寫進 `d.Stdin`：一般鍵送 ASCII，擴充鍵（方向鍵、功能鍵）先送 `00` 再送掃描碼。`d.PushKey`（BDA 緩衝）遊戲不讀，不用。`NonBlockingKeys` 維持預設（遊戲在 `AH=08` 等鍵時阻塞，與真 DOS 相同；滑鼠與計時器照常運作） |
| 前端保留鍵 | 完整清單與修飾鍵組合見 `docs/spec/006` 第 2 節：F1 說明、F2 切換 theme、F3 聲音開關（`docs/spec/007`）、F4 切換介面語言、F11 與 Alt+Enter 全螢幕、F12 存截圖、Ctrl+D 手動診斷（`docs/spec/005`）、Ctrl+Q 結束。保留鍵不送進遊戲；Ctrl 按住的那一幀字元與特殊鍵都不送 |

遊戲實際讀鍵盤的畫面與按鍵：已靜態普查（`docs/re/021`，2026-10-03）。`MAIN.EXE` 讀鍵的指令只有 4 個，三個函式的 7 個呼叫點都不使用鍵值（5 個錯誤等待、2 個結束序列的清緩衝），正常遊玩路徑上遊戲不讀鍵盤（強推論），所以前端保留鍵與遊戲按鍵沒有衝突。動態計數旁證與 `OP.EXE`、`END.EXE` 的用法未做。

## 8. 驗收

| 項目 | 方法 | 預期 |
|---|---|---|
| 映像驗證 | 目錄中的 `MAIN.EXE` 改一個位元組 | 拒絕啟動，顯示實際雜湊 |
| 必要檔 | 移走一個必要檔、改一個大小 | 列出檔名並拒絕啟動 |
| 無頭執行 | `Session` 以步數為單位（`Stats` 回報步數）跑冷啟動到標題與新遊戲，輸入等價於 `probe -clicks "35000000:312:211"`（步數與 `640x480` 畫面座標，含 40 列黑邊）；`Session` 另提供 `ScreenPNG()`，用與 `probe -dump-screen-png` 相同的編碼（調色盤 PNG，`VGA.DACIndex` 對應，標準庫預設壓縮） | PNG 的 SHA-256 與 `docs/re/008` 收據 A、B 相同（`112cd52c…`、`853a6953…`）；`IRQ0Base` 取預設值時 |
| 計時 | 實機一個核心上量 60 秒內的 `Ticks` | 與 `60 × 18.2065` 差在 5% 內，或間隔調降紀錄存在 |
| 輸入映射 | 腳本化視窗座標，點標題選單的新遊戲與讀取遊戲 | 與無頭路徑得到同一畫面（座標扣黑邊與縮放後相同） |
| 鍵盤 | 普查結果（`docs/re/021`）顯示正常遊玩路徑上遊戲不讀鍵盤，此項改為驗證「送鍵不改變遊戲狀態」：在新遊戲畫面送一般鍵與方向鍵（`00` 加掃描碼），同狀態 A/B 畫面與記憶體雜湊不變 | 遊戲狀態不變；錯誤等待畫面（不易到達）才會因任何鍵而繼續 |
| 存檔 | 新遊戲、存檔（覆寫既有槽與新槽）、重開、讀檔 | 回到存檔當下；原版目錄內 `GAMEFILE.*`、`FNAME.DAT` 的雜湊不變 |
| 堆疊補丁 | `docs/spec/002` 第 6 節 | 全數通過 |
| 結束 | 系統選單選「終了」 | 結束碼 1，視窗關閉；存檔不遺失 |
| 三平台建置 | `tools/package.sh`（M7 另立規格） | 各平台產物啟動後在 10 秒內到標題畫面（Linux 以 Xvfb 驗證，Windows 以 Wine，macOS 只驗證建置與 Mach-O 結構，無實機） |
| 外洩掃描 | 發行包內容比對 `docs/re/source-inventory.tsv` 的檔名與雜湊；另跑內容判準 `tools/l10n/leakscan.sh <包目錄>`（原版資料檔與 `OP*.TXT` 的對白，`docs/spec/008` 第 3.9 節）。路徑規則含 `l10n`、`l10n-packs`。閘門失敗關閉：原版缺席、雜湊不符、掃描範圍為空都失敗，不略過 | 沒有任何原版檔案或其衍生物 |

## 9. 聲音（`docs/spec/007`）

音樂需要 `SOUND` 環境變數、`ctmidi.drv` 與 EMS 頁框內的驅動程式碼（`docs/re/010` 第 1 節）。dosgolem 現況沒有設 `SOUND`，音樂路徑整個關閉，音效（Sound Blaster 的 PCM）也不播。音樂與音效的攔截、合成與播放由 `docs/spec/007` 負責：遊戲旗標 `3E24:01B8` 維持 0，在聲音常式的進入點觀察，不需要 `ctmidi.drv`（原版沒附）。本規格的執行層仍不設 `SOUND`。

## 10. 推論等級與已知差異

| 項目 | 等級 |
|---|---|
| 存檔流程在暫存層可行（槽 2 存入、重讀） | confirmed（`docs/re/012` 第 2 節） |
| 鍵盤路徑只讀 `d.Stdin` | confirmed（審查讀 `internal/dos/int21.go`）；遊戲讀鍵的畫面：`MAIN.EXE` 的讀鍵呼叫點都不使用鍵值（`docs/re/021`，靜態普查，強推論） |
| 間隔 300,000（`IRQ0Base ≈ 77,820`）不影響遊戲邏輯 | 假說（`-tick 300000` 的短跑未見差異；經 `IRQ0Base` 的路徑與長跑對照未做） |
| 刪除與改名的暫存層語意 | 未知 |
| 玩家垂直路徑 | 新遊戲、讀檔、存檔、結束四條已有收據（標題、系統選單）；戰鬥、商店等未驗 |
| 與原版 DOS 的差異 | 日期（play 模式用主機時間）、計時（間隔可能調降）、聲音（`docs/spec/007`，無音訊裝置時靜音運行）、存檔位置（暫存層）、鍵盤保留鍵 |

## 11. 未解與停止線

- 間隔 300,000 的等價性：經 `IRQ0Base` 與 `RecalcIRQ0` 的路徑、長跑對照（同種子，300,000 與預設的停機與資源統計）。
- 音樂與音效：見 `docs/spec/007`。
- 鍵盤路徑的普查：靜態普查已完成（`docs/re/021`），剩動態計數旁證（`docs/spec/006` 第 10 節）與 `OP.EXE`、`END.EXE` 的用法。
- `OP.EXE`、`END.EXE`、`SIG.COM` 的冷啟動收據與啟動鏈。
- macOS 無實機驗證。
- 停止線：任何會改變遊戲邏輯、存檔格式或需要散布原版內容的作法，退回 DRAFT 並問使用者。
