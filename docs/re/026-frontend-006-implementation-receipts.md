# 026 前端 F1 至 F4 與 theme 切換的實作收據（docs/spec/006 第七版）

日期：2026-10-04
狀態：收據（`docs/spec/006` 的實作驗證）。記錄目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱；未驗項目在第 6 節。
輸入：dosgolem 分支 `hr` 提交 `c9c8ec3`（hd 與 runtime）、`adeb3e4`（聲音）、`aaaf999`（play），基底 `223ed99`；補丁備份 `engine/patches/0026` 至 `0028`，已用 `git am` 套在 `223ed99` 並以 `git diff` 確認重現同一棵樹。原版輸入 `MAIN.EXE` SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。建置映像 `eob-remake-go:1.26.7-ebiten2.9.9`，`linux/amd64`（Windows 只編譯）。
實作者報告在 `workplace/impl-006-A-report.md`、`impl-006-B1-report.md`、`impl-006-B2-report.md`（gitignore）；本文只收主代理獨立重跑確認的數字與實作者的突變驗證與設計選擇。

## 1. 測試（主代理獨立重跑，日誌在 `workplace/out/verify006*.log`）

| 層 | 指令 | 結果 |
|---|---|---|
| `apps/hr/hd` | `HR_VERBOSE=1 tools/play.sh test-hd`（`go vet` 加 `-race`） | 40 項通過、2 項略過（`TestAllCatalogAssetsLoad`、`TestCatalogCrossCheck`，沒有 `/orig/hd-stage` 掛載，既有行為）、0 失敗 |
| `apps/hr/runtime` 的 holdGate 與 windowVerdict | `HR_RACE=1 HR_TEST_RUN='HoldGate|WindowVerdict' tools/play.sh test-diag` | 15 項通過、0 失敗，含需原版的 Run 接線整合 |
| `apps/hr/play`（B1 完成時） | `HR_RACE=1 HR_VERBOSE=1 tools/play.sh test-play` | 91 項通過、0 失敗 |
| `apps/hr/play`（B2 完成時） | 同上 | 132 項通過、1 項略過（`TestGenCharsets`，沒設 `HR_GEN_CHARSET`）、0 失敗、無 DATA RACE |
| Windows 編譯 | `tools/play.sh build-cross`（B2 回報） | `windows/amd64` 通過，`go.mod` 與 `go.sum` 前後逐位元相同 |

`test-diag` 的容器指令以 `grep -v` 管線結尾、沒有 `pipefail`，退出碼不可靠，所以 `runtime` 列以輸出中的 `PASS`／`FAIL` 行為準。

## 2. 突變驗證（每項改壞、測試必須失敗、還原後 SHA-256 與改前相同）

| 層 | 突變 | 結果 |
|---|---|---|
| hd | `Compose` 快照改逐戳記重讀（M1）；`ErrorStats` 不上鎖（M4）；`SetGetHook` 的鉤子在 `a.mu` 內呼叫（M5） | 決定性與統計式快照測試失敗（90／400 幀混合）；資料競爭；`TestSetGetHookOutsideLock` 逾時 |
| runtime | `release` 不設 `dirty`（M2）；`Preload` 的 `ctx` 檢查失效（M3）；非原子放開（先設 `dirty`、解鎖、之後才減計數，M6） | 案例 (1) 至 (6)、整合測試失敗；取消測試失敗；**案例 (1) 至 (6) 全部存活**，由新加的單持有者並行測試殺死（1489 次）。已寫回 `docs/spec/006` 第 10 節 |
| play 邏輯層 | `hdView` 發佈條件改 `if true`、不重設 `last`；`onResult` 的 `timerFired` 恆真與恆假；prefs 每次寫入判斷損壞；keys 加回 F2；Alt 不處理；`HoldAdapt` 取兩次；`Release` 先於 `ErrorStats`；`Close` 無逾時；計時器先於結果 | 各殺死對應 2 至 5 個測試；`TestHDViewNegativeControl` 逐子項各自失敗；M16 是無效突變（編譯錯誤），由 M16a 取代；M22（刪 `Close` 後最後一次 flush）存活，屬等價突變（`Submit` 的喚醒訊號保證迴圈退出前先 flush） |
| play 畫面層 | `lineWidth` 忽略前進量（只殺 `MeasureString` 量法的測試）；忽略墨跡右緣（只殺 `BoundString` 量法的測試）；toast 矩形與停機提示重疊；`ensureImages` 插入 `os.Exit(3)`；RunGame 失敗路徑改 `os.Exit(1)` | 15 項全部被殺死；兩種量法各自獨立；`os.Exit` 的 `go/ast` 靜態檢查帶 11 個合成原始碼的偵測器正反對照 |

## 3. 端對端（B2 回報，Xvfb、`--cpus 2`、截圖只在 `workplace/out/`）

| 項目 | 結果 |
|---|---|
| `tools/play.sh gui-lang` | 通過：F1 面板區域五張（F4 x 0 至 4）像素簽章兩兩不同，第六次回到與第一張相同；Ctrl+Q 結束碼 0；`prefs.json` 為 `{"version":1,"lang":"zh-TW"}`；階段 2（不凍結）F4 後 toast 出現、2 秒後消失 |
| `tools/play.sh gui-theme` | 通過：以 `-theme original` 啟動取基準，F2 後以 stderr 的 `theme ready: hd` 為完成訊號（Xvfb 內 9 至 11 秒），**HD 差異像素 899077／1024000 ＝ 87.8%，門檻定 50%**（腳本 `HD_MIN_PERCENT=50`）；F2 回 original 與基準 0 像素差異 |
| 原版標題畫面靜態 | 間隔 5 秒的兩張整張截圖差異 0 像素，不需裁動態區 |
| `tools/play.sh gui`（既有） | 正常啟動；ALSA 無裝置、前端靜音運行、降頻訊息；F1 面板在新遊戲畫面顯示真實統計 |
| `Lowered` 斷言 | **在這個容器內無效**：對照組（`-theme hd` 啟動、不按 F2、同長度）已降頻到下限（`lowered=true`，6 至 7 行日誌），按 F2 之前就已降頻（5 行）；Xvfb 軟體繪圖加 `--cpus 2` 的環境本身跑不到 18.2 Hz。腳本照規格印「Lowered 斷言無效」，不當通過或失敗。真實雙核降頻收據沒有取得 |

## 4. 實作者的設計選擇與規格缺案（細節在實作者報告）

- hd：「鉤子自帶 once」讀成每次安裝只在第一次 `Get` 觸發；`windowVerdict` 的參數型別規格沒寫（`time.Time`、`uint64`，回傳 `skip`／`ok`／`lower`）；`want <= 0` 在 `windowVerdict` 與 `adapt` 包裝兩處都處理；`Preload`、`CheckTheme` 改為依雜湊排序處理（測試與錯誤訊息決定性）；`writeTheme` 原本寫 alpha 0 的 PNG（規格已預告），加 `fill` 欄。
- play 邏輯層：`onResult(res loadResult, timerFired bool)` 簽名；`-theme` 不可用時「退回預設」讀成當作沒給（往下找偏好設定、第一個可用 HD theme、original）；`.prefs-*.tmp` 清理加了檔齡條件（1 分鐘）避免誤刪另一個執行個體正在寫的暫存檔；`inputSink` 只含 `Input`；第 267 行子項 (2) 的 skip 模式實際失敗點是屏障等待逾時，測試接受兩種失敗步驟；`TestPrefsCloseTimesOut` 的牆鐘窗口 [0.9 秒, 3 秒] 在極端負載下可能誤判（連跑 5 次皆綠）。
- play 畫面層：基線取 `Ascent.Floor()`（25），取 26 時 `'|'` 墨跡下緣超出 32 像素格；`fitLine` 取前進量與墨跡右緣較大者（`'f'` 右側外溢 43／64 像素）；加了 `panelCache`（面板文字每秒至多組裝一次，`panelLines` 一般 0.7 至 4 毫秒，三條 1700 字元路徑 13 至 36 毫秒）；`os.Exit` 靜態檢查用 `go/ast`（規格寫 grep）；`dataDir` 失敗改走 `fail(...)`；停機種類名稱仍是英文 `stopKindName`（新增 i18n 鍵要重產字型）；F1 關閉的那一幀就開始轉送按鍵。
- 字型子集字元數隨新字串改變：zh-TW 210、zh-CN 211、ko 217、en 101、ja 239（規格第 93 行寫 205、206、212、101、232，已過期）；`fonts_test.go` 全部通過。

## 5. 規格要同步的事

- `docs/spec/006` 第 93 行的字元數過期（現值見第 4 節）；第 357 行（R8）要求的 `workplace/out/test-fonts.log` 與 `docs/re/022` 的字型 SHA-256 要在最後一次重產後補。
- 第 273 行的 `Lowered` 斷言在容器內無效，第 13 節第 5 項的雙核收據仍待取得（需要非軟體繪圖的雙核環境）。

## 6. 沒做完或沒驗

macOS 與 Windows 的執行（只有 `windows/amd64` 編譯與 vet）；真實雙核容器內的 `Lowered`；預載時間分布與 RSS 收據（規格第 13 節第 5 項）；`text.Draw` 字形快取大小與 GPU 繪製成本；ASCII 退回版與停機提示的實際繪製（只驗文字與寬度）；`-scale 1`、`-linear`、全螢幕；`TestGenCharsets` 與 `tools/gen_ui_fonts.sh` 在 B2 階段沒有重跑（沒有新增 i18n 鍵）；`THIRD_PARTY_NOTICES.txt` 的字型授權驗收（`tools/package.sh` 的 `make_notices`、`tools/pkg/verify_*.sh`，規格第 6 節末項，尚未做）。
