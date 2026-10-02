# 013 執行層、前端與發行包的驗收收據

日期：2026-10-03
範圍：`docs/spec/002-stack-size` 與 `docs/spec/003-runtime-and-frontend`（皆 READY）的實作與驗收；Linux、Windows、macOS 三種發行包的建置與驗收。不含聲音、`OP.EXE`、`END.EXE`、HD 疊層。
輸入：`MAIN.EXE`（SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`）與 `docs/re/source-inventory.tsv` 的必要檔案清單（77 個檔案）。
工具：`workplace/dosgolem` 分支 `hr`（`apps/hr/patch`、`apps/hr/runtime`、`apps/hr/cmd/hr-smoke`、`apps/hr/play`）；`tools/play.sh`、`tools/package.sh`、`tools/pkg/`。Go 1.26.7 與 ebiten 2.9.9（本機映像 `eob-remake-go:1.26.7-ebiten2.9.9`），macOS 用 `psychicwar-osxcross`（Go 1.24.13），AppImage 用 `psychicwar-appimage`。這些映像屬其他專案，只以 `docker run --rm` 使用。
推論等級：confirmed（可由指令重跑）、強推論、假說、未知。

## 1. 單元與整合測試（`tools/play.sh test`）

`apps/hr/patch` 5 個測試、`apps/hr/runtime` 9 個測試，全數通過。需要原版的測試在缺檔時 skip（不用替代檔）。

| 測試 | 驗證 | 對應規格 |
|---|---|---|
| `TestApplyChangesStartupStack` 等 5 項（patch） | 套用後啟動 `SP ＝ 0x8010`、未套用 `0x1010`；雜湊不符不改；原值不是 `0x1000` 回錯誤；已執行過指令回錯誤。突變檢查：拿掉 `Write16` 後第一項失敗 | 002 第 4、10 節 |
| `TestOpenRejectsWrongImage` | 非原版的 `MAIN.EXE` 拒絕啟動並顯示實際 SHA-256 | 003 第 2 節 |
| `TestRequiredFilesListsMissing`、`TestRequiredFilesDetectsSizeMismatch` | 缺檔與大小不符列出檔名並拒絕啟動；原版目錄通過 | 003 第 2 節 |
| `TestColdStartReceiptA` | 30,000,000 道指令的畫面 PNG SHA-256 ＝ `112cd52c…`（`docs/re/008` 收據 A），堆疊補丁開與關都相同 | 003 第 8 節、002 第 5 節 |
| `TestMouseClickReachesGameAndHoldsForPolls` | 經執行層的輸入佇列點標題選單的新遊戲，90,000,000 道指令的畫面 PNG SHA-256 ＝ `853a6953…`（收據 B）；按鍵在遊戲恢復輪詢後放開 | 003 第 7、8 節 |
| `TestKeyEventsGoToStdin` | 一般鍵送 ASCII，擴充鍵送 `00` 加掃描碼，進 `d.Stdin` | 003 第 7 節 |
| `TestRunProducesFrameAndStopsOnCancel` | `Run` 取消時回 nil，產生 `640x480` 快照 | 003 第 3 節 |
| `TestSaveGoesToScratchAndLeavesOriginalAlone` | 讀取槽 0、系統選單「檔案存入」、存入槽 2：暫存層出現 `GAMEFILE.002` 與 `fname.dat`，原版目錄的 `GAMEFILE.002` 與 `FNAME.DAT` 雜湊不變 | 003 第 5 節 |

無頭收據另可用 `tools/play.sh smoke` 重現（`hr-smoke`，不依賴 ebiten 與顯示環境）：收據 A 與 B 的 PNG SHA-256 與 `docs/re/008` 相同。

## 2. 長跑（計時器間隔 300,000）

`hrsoak -interval 300000`（與執行層同一條路徑：`IRQ0Base ＝ 間隔 × 17000 ÷ 65536` 加 `RecalcIRQ0`）、`-stklen 32768`、`-key-path stdin`（按鍵有效）、存檔槽 0 至 4 各一個種子（60 至 64）、50 億道指令（約 915 模擬秒）：

| 存檔槽 | 結束碼 1 的次數 | 停機 | 最低 SP | 最大深度（頂端 `0x8010`） |
|---:|---:|---|---|---:|
| 0 | 0 | 無 | `784C` | 1988 |
| 1 | 0 | 無 | `7824` | 2028 |
| 2 | 1 | 無 | `780E` | 2050 |
| 3 | 0 | 無 | `7824` | 2028 |
| 4 | 0 | 無 | `77D6` | 2106 |

沒有溢位、跳出記憶體或凍結。`docs/spec/003` 第 10 節的「間隔 300,000 不影響遊戲邏輯」由假說改為：五組各約 15 模擬分鐘的隨機輸入沒有觀察到差異（停機類別與資源統計）；不等於逐事件等價，這個比對沒有做。

## 3. 桌面前端（Xvfb 內的實際視窗）

`tools/play.sh gui`：Xvfb（`1280x800x24`）內啟動 `hr-play -scale 2`，`xdotool` 點標題選單的新遊戲，`import` 截圖。

| 觀察 | 結果 |
|---|---|
| 標題畫面 | 視窗顯示世界地圖加「片頭選單」，遊戲自己的游標可見 |
| 點新遊戲 | 進入遊戲地圖（顧問對話、債務與所持金面板，日期 `0632/04/16`）；與 `docs/re/008` 收據 B 的畫面一致 |
| F1 | 疊加統計：步數、tick、模擬秒、目前間隔、最低 SP 與頂端、開啟檔案數、TPS 與 FPS |
| 找不到原版 | `tools/play.sh gui-error`：視窗顯示 ASCII 說明（找不到原版，放在 `original/` 或用 `-orig`），終端機另印完整中文訊息 |
| 計時自動降速 | 本機負載高（load average 20 至 30，14 核）時，間隔由 300,000 逐步降到下限 150,000，紀錄寫出每次調降。降速不回調，所以暫時的負載會讓整段遊玩留在較慢的間隔 |

限制：Xvfb 使用軟體繪圖，FPS 約 21，不代表實機；自動降速的行為在負載低的機器上未量測；Linux 版是 cgo 建置（`CGO_ENABLED=0` 的 Linux 建置不被 ebiten 2.9.9 支援），執行時需要系統的 libX11 與 libGL。

## 4. 發行包

`tools/package.sh <appimage|windows|macos>` 全部在 Docker 內，產出放 `dist-all/`（gitignore），每個平台只留最新一份。包內不含原版檔案：`original/PUT_ORIGINAL_FILES_HERE.txt` 是空資料夾的說明，玩家自備原版。包內含 `README.txt`、`LICENSE`（RRSAL-1.0）、`THIRD_PARTY_NOTICES.txt`（ebiten、purego、hideconsole、xgb、x/sys、x/sync 與 Go 的授權全文，取自建置映像的模組快取）。圖示是純幾何圖形，不用原版美術。

| 平台 | 產物 | 建置 | 驗收 |
|---|---|---|---|
| Linux | `HighReward-<版本>-x86_64.AppImage` | cgo，動態連結 libX11 與 libGL；type2 runtime 加 squashfs | `tools/pkg/verify_appimage.sh`：Xvfb 內以 `APPIMAGE_EXTRACT_AND_RUN=1` 啟動，原版以唯讀掛在 AppImage 旁的 `original`，點新遊戲，截圖顯示遊戲地圖（confirmed） |
| Windows | `HighReward-<版本>-win64.zip` | `CGO_ENABLED=0`、`-H=windowsgui` | Wine（`psychicwar-wine`）加 Xvfb：視窗啟動並顯示標題畫面（confirmed）；Wine 與軟體繪圖下每 2 秒只有 1 至 3 個 tick，只能證明能啟動，不代表速度（未知：實機） |
| macOS | `HighReward-<版本>-macos.zip` | osxcross，arm64 與 x86_64，`lipo` 合成 universal，最低 macOS 11.0，未簽章 | `tools/pkg/verify_macos.sh`：`lipo -info` 含兩種架構、`Info.plist` 以 `plistlib` 解析成功、`.icns` 檔頭正確。**沒有實機驗證**，結構過關不等於功能正常 |

外洩掃描：`tools/pkg/leakscan.py` 依 `docs/re/source-inventory.tsv` 的檔名與 SHA-256 掃描三個包的暫存目錄，命中 0。

原版目錄的尋找順序：`-orig`、環境變數 `HR_ORIG`、`.AppImage` 旁的 `original`、執行檔旁的 `original`、macOS 的 `Contents/Resources/original`、目前目錄的 `original`、使用者資料目錄記住的上次路徑。

## 5. 未涵蓋與已知限制

- 沒有聲音：音樂路徑需要 `SOUND` 環境變數與 `ctmidi.drv`，音效需要 Sound Blaster 模擬（`docs/re/010`）。
- 只執行 `MAIN.EXE`：結束碼 0 時顯示結束並關閉視窗，不播片尾；不播片頭（`OP.EXE` 在 dosgolem 內可冷啟動，第一個畫面是角色介紹，但前進條件與結束碼尚未驗）。
- `go.sum` 由本機模組快取產生（`GOSUMDB=off`），沒有經校驗資料庫核對。
- 鍵盤：遊戲讀鍵盤的畫面與按鍵未普查；前端保留鍵（F1、F11、F12、Alt+Enter、Ctrl+Q）與遊戲按鍵的衝突未驗。
- 存檔：存入新槽、刪除與改名未驗；存檔後讀回並續玩的等價性未驗。
- DOS 日期在 play 模式取主機日期（存檔列顯示真日期）；無頭模式維持 1993-01-01。
- macOS 與 Windows 沒有實機驗證。
