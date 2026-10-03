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

### 4.1 乾淨工作樹的發行包（2026-10-03）

版本字串 `97c1b13-dg8118664`（本 repo 的 commit `97c1b13`，dosgolem 分支 `hr` 的 commit `8118664`；`git describe --dirty` 沒有 `dirty`）。含 HD 疊層的前端（`docs/re/014`）：找得到 `hd/` 目錄（`-hd`、`HR_HD`、AppImage 檔案旁、執行檔旁、macOS 的 `Contents/Resources/hd`、目前目錄）就啟用，找不到就顯示原版畫面；三個包都不含 HD 素材與原版素材。

| 產物 | 大小（bytes） | SHA-256 |
|---|---|---|
| `HighReward-97c1b13-dg8118664-x86_64.AppImage` | 4,340,216 | `1fc800e469d1e42dd4a24c2140c4270cafc104627539d1d922480d889115e290` |
| `HighReward-97c1b13-dg8118664-win64.zip` | 3,778,966 | `3bbd9d216371e58f4c0dfb527ea946678c10e1aa61dc95f47a5145d5be7704e3` |
| `HighReward-97c1b13-dg8118664-macos.zip` | 7,303,692 | `7454f466b3cb288ea0aa348b2facb8c78689950556bf844acb47a8d04a37e6cd` |

驗收（本次重建後重跑）：外洩掃描三個包命中 0；AppImage 在 Xvfb 內啟動並點新遊戲，原版目錄在 `.AppImage` 旁（`pkg-appimage-newgame.png`），另以 `HR_HD_DIR` 把 HD 目錄掛在 `.AppImage` 旁重跑，新遊戲畫面顯示 HD（`pkg-appimage-hd-newgame.png`）；Windows 以 `tools/pkg/verify_wine.sh` 在 Wine 加 Xvfb 內啟動，顯示標題畫面（`pkg-wine-title.png`，沒有 `hd/`，所以是原版畫面）；macOS 只驗結構（`lipo` 含 x86_64 與 arm64），沒有實機。HD 前端在 Windows 以 Wine 驗過標題畫面（`docs/re/014` 第 5 節），macOS 沒有驗過。

### 4.2 含 HD 素材的發行包（2026-10-03）

使用者 2026-10-03 授權發行含 HD 素材的版本，隨後表示「HD 我都接受」（`hd/provenance.tsv` 全部 `accepted`）。`HR_WITH_HD=1 tools/package.sh all` 把 `hd/`（清冊、調色盤表、`provenance.tsv`、595 張 `x2/` PNG）放進包內，產物在 `dist-all/with-hd/`，版本字串加 `-hd`，包內附 `hd/NOTICE.txt`（說明這些圖是原版美術的衍生物，只供私人流通）與 README 的 HD 段。版本 `9d4f0f0-dg8eb277d-hd`（本 repo commit `9d4f0f0`，dosgolem 分支 `hr` 的 commit `8eb277d`，工作樹乾淨）。位置：AppImage 的 `usr/bin/hd`、Windows zip 的 `hd/`、macOS 的 `Contents/Resources/hd`。

| 產物 | 大小（bytes） | SHA-256 |
|---|---|---|
| `HighReward-9d4f0f0-dg8eb277d-hd-x86_64.AppImage` | 30,472,696 | `816dcaa5373e26e4bbcb14bd7238c5608a8406d51b8ca38f8254074e0296002c` |
| `HighReward-9d4f0f0-dg8eb277d-hd-win64.zip` | 30,089,890 | `d581fc5569d278fc40f5b00c2e61d9ddff4347c886d3fd7409547968be4e415d` |
| `HighReward-9d4f0f0-dg8eb277d-hd-macos.zip` | 33,609,545 | `6ef4b1baa59ef276b1ec651b5b1c89c524de74a61871a7f5c8e4c0900da5462c` |

驗收：外洩掃描三個包命中 0（HD 的 PNG 不在原版清冊內，掃描對象是原版檔名與 SHA-256）；macOS 只驗結構（`lipo` 含 x86_64 與 arm64）。AppImage 在 Xvfb 內啟動，不另外掛 HD 目錄，內附的 `hd/` 被自動找到，新遊戲畫面顯示 HD（`pkg-appimage-withhd2-newgame.png`）；Windows zip 在 Wine 加 Xvfb 內啟動，不帶 `-hd`，標題畫面顯示 HD（`pkg-wine-withhd2-title.png`）。不含 HD 的包（4.1）不受影響。macOS 與兩個平台的實機沒有驗證。權利：含原版美術衍生物的包不得公開散布；轉公開、公開 Release 前要先處理 git 歷史並更新 `LICENSE` 第 2 條 (c)（`AGENTS.md` 第 2 節）。

外洩掃描：`tools/pkg/leakscan.py` 依 `docs/re/source-inventory.tsv` 的檔名與 SHA-256 掃描三個包的暫存目錄，命中 0。

原版目錄的尋找順序：`-orig`、環境變數 `HR_ORIG`、`.AppImage` 旁的 `original`、執行檔旁的 `original`、macOS 的 `Contents/Resources/original`、目前目錄的 `original`、使用者資料目錄記住的上次路徑。

### 4.3 合併 Buck Rogers 與修正長跑記憶體成長之後的發行包（2026-10-03）

版本字串 `034771b-dg49d5eed`（本 repo 的 commit `034771b`，dosgolem 分支 `hr` 的 commit `49d5eed`；兩邊工作樹皆乾淨，沒有 `dirty`）。與 4.1、4.2 相比，`hr` 分支多了：

- 合併兄弟分支 `buck-rogers-cht-output-overlay`（merge `50ffc62`，使用者 2026-10-03 授權）。
- 修正診斷紀錄在鍵盤佇列非空時不修剪的缺陷：`Session.idleForTrim()` 改成只看滑鼠按鍵是否按住。舊版在畫面上有未消化按鍵時，`Machine.PortLog` 等紀錄無上限成長，遊玩機器人長跑時行程被 OOM 殺掉（exit 137，pprof 指向 `Machine.Out8`）。這個缺陷也在已發行的 `v0.1.0-hd` 裡。測試 `TestIdleForTrimIgnoresPendingKeys`。
- 前端在異常停機時把現場存到使用者資料目錄的 `crash/<時間>/`（`info.txt`、`screen.png`、`state.state`），並每分鐘在 `play.log` 追加一行遙測（步數、tick、最低 SP、降速紀錄）。
- `Session.RunToPoll`、`Session.SnapshotNow`、`CrashDump` 與遊玩機器人 `apps/hr/cmd/hrbot`（`tools/bot.sh`，見 `docs/re/016`）。

不含 HD 的包（`dist-all/`）：

| 產物 | 大小（bytes） | SHA-256 |
|---|---|---|
| `HighReward-034771b-dg49d5eed-x86_64.AppImage` | 4,364,792 | `684197f52c39ddce4ce115e8280b06e232be2419cd87334f3ecb7950587c14a9` |
| `HighReward-034771b-dg49d5eed-win64.zip` | 3,799,523 | `b992855fbdadee578e46ddeeb25dbfaea8e50ce7cd958bc1150e6fdc245713fb` |
| `HighReward-034771b-dg49d5eed-macos.zip` | 7,336,513 | `4cb4ee225240f3d8a885586cc46a4ccbbe3cfada34f2b668d345d757c47a67b5` |

含 HD 的包（`dist-all/with-hd/`，`HR_WITH_HD=1`）：

| 產物 | 大小（bytes） | SHA-256 |
|---|---|---|
| `HighReward-034771b-dg49d5eed-hd-x86_64.AppImage` | 30,497,272 | `45d4ddfb11b73608c6d2f20410fb9bdee56f3fced04be0068df34d06c78c96b2` |
| `HighReward-034771b-dg49d5eed-hd-win64.zip` | 30,110,423 | `1900b677d54c83d70dc66239827c4099c79d1c84dd8725393aef7820257e1f47` |
| `HighReward-034771b-dg49d5eed-hd-macos.zip` | 33,642,377 | `28aafb83c9e8bb33083127321432dc97091ae46a1457a661f50791c884c9d732` |

驗收：兩組各三個包的外洩掃描命中 0；macOS 只驗結構。AppImage 在 Xvfb 內啟動並點新遊戲，不帶 `HR_HD_DIR`：含 HD 的包新遊戲畫面為 HD（`pkg-hd-v011-appimage-newgame.png`），不含 HD 的包為原版畫面（`pkg-v011-appimage-newgame.png`）。Windows zip 在 Wine 加 Xvfb 內啟動，不帶 `-hd`：兩個包都顯示標題畫面，含 HD 的包 zip 內有 `hd/` 檔案 627 個，不含的 0 個（`pkg-hd-v011-wine-title.png`、`pkg-v011-wine-title.png`）。驗收時主機負載平均約 30 至 46（14 核，另有其他專案的行程），dosgolem 的速度守門把計時器間隔降到 150000，所以只證明能啟動並顯示畫面，不代表速度。

## 5. 未涵蓋與已知限制

- 沒有聲音：音樂路徑需要 `SOUND` 環境變數與 `ctmidi.drv`，音效需要 Sound Blaster 模擬（`docs/re/010`）。
- 只執行 `MAIN.EXE`：結束碼 0 時顯示結束並關閉視窗，不播片尾；不播片頭（`OP.EXE` 在 dosgolem 內可冷啟動，第一個畫面是角色介紹，但前進條件與結束碼尚未驗）。
- `go.sum` 由本機模組快取產生（`GOSUMDB=off`），沒有經校驗資料庫核對。
- 鍵盤：遊戲讀鍵盤的畫面與按鍵未普查；前端保留鍵（F1、F11、F12、Alt+Enter、Ctrl+Q）與遊戲按鍵的衝突未驗。
- 存檔：存入新槽、刪除與改名未驗；存檔後讀回並續玩的等價性未驗。
- DOS 日期在 play 模式取主機日期（存檔列顯示真日期）；無頭模式維持 1993-01-01。
- macOS 與 Windows 沒有實機驗證。
