# 027 L0 語言層的實作收據（docs/spec/008 第八版）

日期：2026-10-04
狀態：收據（實作驗證）。記錄目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱；只涵蓋 L0（dosgolem 語言層），L1 尚未實作。
輸入：fork `workplace/dosgolem` 分支 `hr`，基底 `aaaf999`，L0 提交 `fabe4f2`；補丁備份 `engine/patches/0029-apps-hr-lang-layer-l0-008.patch`，已用 `git am` 套在 `aaaf999` 並確認重現同一棵樹（`7befbf5a…`）。原版輸入 `MAIN.EXE` SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。
來源：實作者報告（`workplace/l0-report.md`，不進版控）經主代理審閱後搬入，並經一位唯讀審查者對照規格逐項審查（`workplace/l0-review.md`，不進版控；無阻擋，應改 A1、A2 與建議 S1 至 S9 都已處理，第 9 節）。下文的行號與路徑是審查當時的狀態；記錄含主代理在審查後做的澄清（已併入 `docs/spec/008` 第 3.1 節）。


日期：2026-10-04。範圍：只做 L0。fork：`/home/anr2/cht/hr/workplace/dosgolem`，分支 `hr`，HEAD `aaaf999bc4a5fec4e3d647fdd57d79116a43cac9`，實作前工作樹乾淨。實作者沒有 commit、add、checkout、stash、reset；主代理審閱後以 `fabe4f2` 提交。

## 1. 改動檔案

`git diff --numstat`（已追蹤檔，新增 / 刪除行）：

| 檔案 | +/- | 內容 |
|---|---|---|
| `internal/dos/files.go` | 69 / 8 | `resolve` 回 `(path, Layer)`；`Layer` 型別與常數；`OpenedLayer`；`noteOpenLayer`；`open` 的語言層寫入拒絕與層報告（copy-up 後層記 `scratch`，第 9 節 A2）；`fileAttr` |
| `internal/dos/dos.go` | 26 / 1 | `DOS.LangDir`、`LangManifest`、`OpenedLayers`、`OnOpenLayer`；`AllowFileWrites` 不收語言層的檔 |
| `internal/dos/find.go` | 3 / 2 | `searchFor` 目錄順序 `Root`、`LangDir`、`Scratch` |
| `internal/dos/fileops.go` | 7 / 4 | `renameFile` 改層別判斷；`createNew` 呼叫點 |
| `internal/dos/state.go` | 53 / 5 | `dosState.LangDir`、`LangManifest`（`json:",omitempty"`）；`decodeState`、`checkLang`、`(*DOS).PreflightState`；`LoadState` 開頭預檢 |
| `internal/dos/exec.go`、`dosinfo.go`、`font.go` | 2/2、3/2、1/1 | 其餘 `resolve` 呼叫者改成接兩個回傳值 |
| `internal/dos/state_test.go` | 1 / 1 | 既有測試改接兩個回傳值（唯一的既有測試呼叫者） |
| `internal/state/state.go` | 21 / 7 | `Load` 先把兩段讀進記憶體，對 DOS 段 `PreflightState`，再套用機器段與 DOS 段 |
| `apps/hr/runtime/session.go` | 8 / 0 | `Options.LangDir`；`Open` 在 `dos.Install` 之前呼叫 `bindLang` |
| `apps/hr/runtime/diag.go` | 1 / 0 | `diagSections` 結尾加語言層區段（T1、T2、T3 共用） |
| `apps/hr/runtime/crash.go` | 3 / 1 | 只改 `CrashDump` 的註解：語言包 Session 的狀態檔要用 `probe -lang-dir` 或同一語言層的 Session 載入（第 9 節 S4） |
| `apps/hr/runtime/diag_test.go` | 12 / 5 | `hasInfoSections` 的基本清單加語言層區段與三個標籤；`newHang` 拆出 `newHangWith` |
| `cmd/probe/main.go` | 13 / 0 | 旗標 `-lang-dir`；報告印語言層與命中層 |
| `apps/hr/cmd/hrsoak/main.go` | 11 / 0 | 旗標 `-lang-dir`；report.tsv 記一行 |
| `apps/hr/cmd/hrbot/main.go` | 6 / 0 | 旗標 `-lang-dir` 傳給 `Options.LangDir`；`hrrt.Open` 之後呼叫 `checkLangBound`（第 9 節 A1） |

新增檔（未追蹤，行數；本表為審查後修正後的數字，檔案共 10 個）：

| 檔案 | 行數 | 內容 |
|---|---|---|
| `apps/hr/runtime/lang.go` | 96 | `bindLang`（含層重疊防呆）、`normDir`、`langDataFiles`、`langSection` |
| `cmd/probe/langdir.go` | 82 | `bindLangDir`（不存在回錯、層重疊防呆）、`normDir`、`reportLangLayers` |
| `apps/hr/cmd/hrsoak/langdir.go` | 63 | `bindLangDir`、`normDir` |
| `apps/hr/cmd/hrbot/lang.go` | 16 | `checkLangBound`（暫時防護） |
| `internal/dos/lang_test.go` | 1030 | 語言層單元測試（見第 3 節與第 9 節） |
| `internal/state/lang_test.go` | 132 | `state.Load` 預檢測試 |
| `apps/hr/runtime/lang_test.go` | 433 | `bindLang`、層重疊、診斷區段、冷啟動開檔層、狀態檔綁定 |
| `cmd/probe/langdir_test.go`、`apps/hr/cmd/hrsoak/langdir_test.go` | 112、111 | `bindLangDir` 單元測試 |
| `apps/hr/cmd/hrbot/lang_test.go` | 20 | `checkLangBound` 測試 |

已追蹤的改動檔 17 個、新增檔 10 個，合計 27 個。

fork 之外只寫了 `workplace/out/l0/`（日誌與基準）與 `workplace/l0-tmp/`（`l0drv.go` 驅動、突變前後雜湊清單、diff）。

## 2. 基準與 A/B 收據

綁定：fork HEAD `aaaf999bc4a5fec4e3d647fdd57d79116a43cac9`，`git status` 乾淨，repo 的 `user.email` 為 `wicanr2@gmail.com`。基準在改任何檔之前錄下；LangDir 為空；Interval 為 `NativeInterval`；輸入為冷啟動、第 35,000,000 步在 (312, 211) 點左鍵、跑到 90,000,000 步（即 `docs/re/008` 收據 B）。

### 2.1 Session 層（hrrt.Open，堆疊補丁開）

現有工具拿不到暫存器與 `machine.StateDigest`（`tools/play.sh smoke` 只印畫面 PNG 雜湊），所以寫了 `workplace/l0-tmp/l0drv.go`：與 `apps/hr/cmd/hr-smoke` 同一條路（`hrrt.Open`、`NativeInterval`、同樣的點擊），多印 CPU 暫存器，並呼叫 `Session.CrashDump` 存 `state.state`，再用 `cmd/state-compare` 對 `state.state` 算 `machine.StateDigest` 與 `dos.StateDigest`。驅動不改產品程式，也不 import `internal`。

指令（主機上執行，cwd 為 `/home/anr2/cht/hr`）：

```
tools/dosgolem.sh go run /orig/l0-tmp/l0drv.go -orig /orig/orig -out /out/l0/baseline/sess-1
tools/dosgolem.sh go run /orig/l0-tmp/l0drv.go -orig /orig/orig -out /out/l0/baseline/sess-2
tools/dosgolem.sh go run ./cmd/state-compare -left /out/l0/baseline/sess-1/state.state -right /out/l0/baseline/sess-2/state.state
```

基準輸出（兩次相同，`state-compare` 回 `equal:true`，退出碼 0）：

| 項目 | 值 |
|---|---|
| 步數 | 90000000 |
| 畫面 PNG SHA-256 | `853a695340271b1e2540702d6d5f1e78f3807e230c666a181e3985097879adaf`（與 `docs/re/008` 收據 B 及 `apps/hr/runtime/session_test.go` 的 `wantB` 相同；容器內 `sha256sum` 對 `screen.png` 確認） |
| CPU R（AX CX DX BX SP BP SI DI） | `0000 0138 00D3 0000 7D6A 7D6C 0000 0010` |
| CPU Hi | 全為 `0000` |
| CPU Seg（ES CS SS DS FS GS） | `27B4 1F8A 54C0 3135 0000 0000` |
| IP、FLAGS | `0098`、`7297` |
| `machine.StateDigest` | `37ef33a448ce0764d2b379a29d70792e6f653b925f0a4c59724c648fb62a5c06` |
| `dos.StateDigest` | `d3b911ef36e51a6a9ea03f994ad2e820e5b0634339095d50f57dfefa55390e96` |

### 2.2 probe 層（不經 Session，無堆疊補丁）

```
tools/dosgolem.sh go run ./cmd/probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 90000000 -clicks "35000000:312:211" -dump-screen-png /out/l0/baseline/probe-N.png -save-state 89999999:/out/l0/baseline/probe-N.state
```

一個意外：第一次用 `-save-state 90000000:…`，沒有產生狀態檔（`state-compare` 回 `open … no such file`）。原因是 probe 在每次迴圈開頭、執行該步之前檢查 `m.Steps`，而迴圈在 `m.Steps` 到達上限時結束，所以上限那一步永遠不觸發。改存第 89,999,999 步的狀態，與最後印出的暫存器相差一步；這是 probe 層狀態摘要與最終暫存器不在同一步的原因。第一次嘗試留下的 `probe-1.png`、`probe-2.png` 被第二輪覆寫（同雜湊）。

| 項目 | 值（兩次相同，`state-compare` `equal:true`） |
|---|---|
| 畫面 PNG SHA-256 | `853a695340271b1e2540702d6d5f1e78f3807e230c666a181e3985097879adaf` |
| 最終暫存器（probe 印出） | `CS:IP ＝ 1F8A:0098  AX=0000 BX=0000 CX=0138 DX=00D3`、`DS=3135 ES=27B4 SS:SP=54C0:0D6A` |
| `machine.StateDigest`（第 89,999,999 步） | `e4b810aea9fb374434c3ea07184012958b31a0a38a98fb70617e20dcf3261c04` |
| `dos.StateDigest`（第 89,999,999 步） | `dd9e744dff9d11d3b13dd5380811ce318ed958ea7f78566906e6a3786f818b86` |

基準日誌：`workplace/out/l0/baseline/`（`sess-1.log`、`sess-2.log`、`sess-compare.log`、`probe-1.log`、`probe-2.log`、`probe-compare.log`、`png-sha256.txt`、`png-sha256-probe.txt`）。

### 2.3 實作後 A/B（D(1)）

用與基準完全相同的指令與輸入（只有輸出路徑改成 `/out/l0/ab/…`），`LangDir` 為空：

```
tools/dosgolem.sh go run /orig/l0-tmp/l0drv.go -orig /orig/orig -out /out/l0/ab/sess
tools/dosgolem.sh go run ./cmd/probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 90000000 -clicks "35000000:312:211" -dump-screen-png /out/l0/ab/probe.png -save-state 89999999:/out/l0/ab/probe.state
tools/dosgolem.sh go run ./cmd/state-compare -left /out/l0/baseline/sess-1/state.state -right /out/l0/ab/sess/state.state
tools/dosgolem.sh go run ./cmd/state-compare -left /out/l0/baseline/probe-1.state -right /out/l0/ab/probe.state
```

| 項目 | Session 層 | probe 層 |
|---|---|---|
| 畫面 PNG SHA-256 | `853a6953…adaf`，與基準逐位元相同 | `853a6953…adaf`，與基準相同 |
| CPU 暫存器 | `R 0000 0138 00D3 0000 7D6A 7D6C 0000 0010`、`Seg 27B4 1F8A 54C0 3135 0000 0000`、`IP 0098`、`FLAGS 7297`，與基準相同 | `CS:IP 1F8A:0098 AX=0000 BX=0000 CX=0138 DX=00D3`、`DS=3135 ES=27B4 SS:SP=54C0:0D6A`，與基準相同 |
| `machine.StateDigest` | `37ef33a4…5c06`，`equal:true` | `e4b810ae…1c04`，`equal:true` |
| `dos.StateDigest` | `d3b911ef…0e96`，`equal:true`（`omitempty` 使空 LangDir 的舊摘要不變） | `dd9e744d…8b86`，`equal:true` |

這組 A/B 跑的是未提交的工作樹。A/B 之後，產品程式只經過突變實驗（全部以雜湊驗證逐位元還原，第 4 節）。第一輪實作的最終狀態（審查後修正見第 9 節，最終雜湊是 `post-final2.sha256`）：`workplace/l0-tmp/post-final.sha256` 是 24 個檔的雜湊；與突變前的 `pre-mutation.sha256` 比對（`sha256sum -c`），23 個 OK、1 個不同，不同的是 `apps/hr/runtime/lang_test.go`（突變實驗之後把一行 `t.Logf` 的文字改成不宣稱結果）。16 個已追蹤檔（全部是產品程式與既有測試）的 `git diff` 雜湊與突變前相同（`32bc7800…`），3 個新增的產品檔（`lang.go`、兩個 `langdir.go`）也相同，所以 A/B 當時的產品程式與最終工作樹相同。

### 2.4 `probe -lang-dir` 端對端（識別語言包）

規格 L0 出口沒有要求，另外做的收據。語言包在容器內建出（`DOSGOLEM_GO_CMD=sh … cp`，來源是原版目錄），位置 `workplace/out/l0/pack/`（`files/` 放原版的 `CFONT.15` 與 `ESPMES.MRG` 位元組不變的副本，`manifest.json` 內容是 `hello`；含原版內容，只放 `workplace/out`）：

```
tools/dosgolem.sh go run ./cmd/probe -exe /orig/orig/MAIN.EXE -root /orig/orig -lang-dir /out/l0/pack/files -steps 90000000 -clicks "35000000:312:211" -dump-screen-png /out/l0/ab/probe-lang.png -save-state 89999999:/out/l0/ab/probe-lang.state
```

| 項目 | 結果 |
|---|---|
| probe 報告的語言層 | `LangDir＝"/out/l0/pack/files"`、`manifest SHA-256＝2cf24dba…9824`（`"hello"` 的雜湊） |
| 開檔命中層 | `CFONT.15 首次 lang 最近 lang`、`ESPMES.MRG 首次 lang 最近 lang`；`MAIN.EXE`、`FACE.MRG`、`BOMB.MRG` 等 root（共 18 個檔名） |
| 畫面 PNG SHA-256 | `853a6953…adaf`，與基準相同 |
| 暫存器 | `CS:IP ＝ 1F8A:0098  AX=0000 BX=0000 CX=0138 DX=00D3`，與基準相同 |
| `state-compare`（對 baseline `probe-1.state`） | `machine_sha256` 相同（`e4b810ae…1c04`）；`dos_sha256` 不同（`2f06f409…0423`，基準 `dd9e744d…8b86`），`equal:false`。這是規格第 3.1 節預期的：有語言包的 `dos.StateDigest` 因 `LangDir`、`LangManifest` 非空而必然不同，A/B 比較對象是 `machine.StateDigest` 加畫面雜湊 |
| `probe -load-state probe-lang.state`，不給 `-lang-dir` | 拒絕載入，退出碼 1，訊息：`dos: 狀態檔的語言層與目前的 Session 不同（狀態檔 LangDir＝"/out/l0/pack/files" LangManifest＝"2cf24dba…"，目前 LangDir＝"" LangManifest＝""）…` |
| `probe -load-state probe-lang.state -lang-dir /out/l0/pack/files`，跑到 90000001 步 | 成功，程式活著 |

日誌：`ab-probe-lang.log`、`ab-probe-lang-compare.log`、`ab-probe-lang-load-nolang.log`、`ab-probe-lang-load-same.log`。`hrsoak -lang-dir` 與 `hrbot -lang-dir` 只有單元測試與編譯檢查，沒有端對端實跑。

另一條旁證：`TestColdStartOpensDataFilesFromLangLayer` 用內容與原版相同的臨時語言包（識別包），在 90M 步的畫面 PNG 也是 `853a6953…adaf`（第 3 節）。

## 3. 測試結果

### 3.1 新增的測試

| 位置 | 測試 | 涵蓋（對應規格第 8 節前 6 列與診斷列） |
|---|---|---|
| `internal/dos/lang_test.go` | `TestResolveOrderScratchLangRoot`（七個子案例）、`TestLangFallsBackToRootPerFile`、`TestResolveLangCaseBasenameAnd83`、`TestEmptyLangDirEqualsLegacy` | resolve 順序、逐檔回退、大小寫、basename、8.3、空 `LangDir` 等同現況、暫存層蓋過語言層 |
| 同上 | `TestOpenReadsLangLayerAndReportsLayer`、`TestEveryDataFileOpensFromLangLayer`、`TestReadOnlyOpenOfLangFileDoesNotCopyToScratch`；檔頭的編譯期簽章斷言 | 開檔層報告（`OpenedLayers`、`OnOpenLayer`、回呼順序、鍵為大寫）；既有 `Opened`、`OnOpen` 簽章不變；八個檔名逐一從語言層開 |
| 同上 | `TestOpenForWriteOnLangFileIsDenied`（有無暫存層、模式 1 與 2）、`TestOpenForWriteOnRootFileStillCopiesToScratch`、`TestAllowFileWritesRejectsLangLayerFile`、`TestExtendedOpenForWriteOnLangFileIsDenied` | 寫入模式拒絕（AX ＝ 5）、暫存層沒有副本、語言層檔案不變、白名單不收；對照組 `Root` 的檔照舊寫時複製 |
| 同上 | `TestRenameFromLangLayerCopiesAndNeverMovesIt`（`-saves` 為語言包祖先、前綴相同兄弟、獨立目錄）、`TestRenameFromRootLayerNeverMovesItEvenWhenScratchIsPrefix`、`TestRenameFromScratchLayerStillRenames`、`TestUnlinkCreateFamilyBehavesLikeRootFile` | 層別判斷取代字串前綴；改名、刪除、`create`、`createNew`、`extendedOpen`、`fileAttr` 對語言層檔與 `Root` 檔結果逐項相同 |
| 同上 | `TestSearchForOrderRootLangScratch`、`TestSearchForIgnoresLangDirWhenEmpty`、`TestFindFirstListsLangOnlyFile`、`TestManifestOutsideFilesIsInvisible`（含正對照） | `searchFor` 順序與覆蓋；`manifest.json` 在 `files/` 外 |
| 同上 | `TestExecLoadsProgramFromLangLayer`、`TestSpawnQueuedLoadsProgramFromLangLayer`、`TestCreateTempSkipsNamesInLangLayer`、`TestFontBytesReadsLangLayerFile` | 其餘 `resolve` 呼叫者（`exec.go` 兩處、`dosinfo.go`、`font.go`）；`fileops.go`、`files.go`、`dos.go` 的呼叫者由上列測試涵蓋 |
| 同上 | `TestSaveStateRecordsLangDirAndManifest`、`TestLoadStateComparesLangDirAndManifest`（六個子案例，`LoadState` 與 `PreflightState` 同時斷言）、`TestOldStateFileWithoutLangFieldsIsTreatedAsEmpty`（以缺兩個欄位的舊版面 gob 編碼）、`TestLangMismatchRejectsBeforeAnyChange`、`TestPreflightStateRejectsGarbage`、`TestStateDigestOmitsEmptyLangFields` | 狀態檔欄位；相同成功、不同拒絕（訊息點名兩組值）、舊檔視為空；拒絕後 DOS 狀態摘要與開著的 handle 不變；`omitempty` 使空 `LangDir` 的摘要 JSON 不含新欄位 |
| `internal/state/lang_test.go` | `TestLoadChecksLangLayerBeforeAnyChange`（四個子案例）、`TestLoadWithoutLangStillWorks` | `state.Load` 預檢：拒絕後機器狀態摘要與 DOS 狀態摘要都不變 |
| `apps/hr/runtime/lang_test.go` | `TestBindLang`（六個子案例）、`TestLangSection`、`TestTrimKeepsOpenedLayers`、`TestOpenLangDirMissingManifestFails`、`TestOpenNonexistentLangDirClearsToEmpty` | `bindLang` 規則、診斷區段文字、`OpenedLayers` 不被 `TrimDiagnostics` 清、`Open` 的兩個錯誤路徑（需原版） |
| 同上 | `TestColdStartOpensDataFilesFromLangLayer`（需原版）、`TestDiagLangSectionWithPack`（T1、T2、T3，需原版）、`TestSessionStateFileBindsToLangLayer`、`TestSessionStateFileWithoutLangLoadsAsBefore`（需原版） | 冷啟動 90M 步：識別包的 `CFONT.15` 與 `ESPMES.MRG` 命中 lang，畫面 PNG 等於收據 B；負對照語言包缺 `ESPMES.MRG` 時它落回 root；診斷三個 trigger 都有語言層區段；`CrashDump` 的 `state.state` 只能在同一語言層載入 |
| `apps/hr/runtime/diag_test.go`（既有，改） | `hasInfoSections` 加 `== 語言層 ==\nLangDir：`、`\nmanifest SHA-256：`、`\n開檔命中層：\n` | 既有的 T1（`TestCrashDumpHasDiagSections`）、T2（`TestT2*`）、T3（`TestT3ManualAndRateLimit`）都檢查新區段；沒有語言包時三項為空 |
| `cmd/probe/langdir_test.go`、`apps/hr/cmd/hrsoak/langdir_test.go` | `TestBindLangDir`、`TestBindLangDirRefusesMissingManifest` | 正規化、相對路徑、不存在目錄、缺 manifest 拒絕、不驗證內容；同一個固定雜湊 |

### 3.2 各指令的結果

所有指令都在主機上以包裝腳本啟動，結果日誌在 `workplace/out/l0/`。

| 指令 | 結果 |
|---|---|
| `tools/dosgolem.sh go test -count=1 -v ./internal/dos/ ./internal/state/ ./apps/hr/runtime/ ./apps/hr/patch/ ./cmd/probe/ ./apps/hr/cmd/hrsoak/`（原版唯讀掛為 `/orig/orig`，沒有狀態檔環境變數；`after-dosgolem-v.log`） | 六個套件全部 `ok`。`--- PASS` 384 行（含子測試），`--- SKIP` 5，`--- FAIL` 0。5 個 skip：`TestOverlayClassificationOnState`（沒設 `HR_BENCH_STATE`）、`TestT2StepDiscontinuityAfterStateLoad`、`TestCallCountsMatchProbe`、`TestSoundPlayMusicPathFromState`（沒設 `HR_SOAK_STATE`）、`TestDiagOverheadPaired`（沒設 `HR_BENCH_OVERHEAD`）。本次新增的測試 skip 數 0，需原版的新測試都實跑（原版已掛載） |
| `tools/play.sh test`（`apps/hr/patch`、`apps/hr/runtime`；`after-play-test.log`） | `ok`（`apps/hr/patch` 0.031s、`apps/hr/runtime` 278.716s）；此指令不帶 `-v`，沒有計數 |
| `HR_RACE=1 tools/play.sh test-diag`（`apps/hr/runtime` 全部測試加 `-race`，並掛載 `n00071.state` 與 `ck-001500000000.state`） | **整套一次跑會撞到 `go test` 預設的 10 分鐘逾時**（`after-test-diag-race.log`：前 30 個測試全部 PASS，累計約 585 秒，第 31 個測試開始後 `panic: test timed out after 10m0s`）。這是 `-race` 下整套測試的牆鐘時間超過預設逾時，不是某個測試失敗；腳本沒有 `-timeout` 參數。改以 `HR_TEST_RUN` 切成互不重疊的幾段，合起來涵蓋全部 84 個頂層測試：A（上述前 30 個，逾時前跑完的部分）、B（`after-race-B-hd.log`，18 個）、C（本次新增的語言層測試，9 個，`after-race-C-lang.log`）、D（`after-race-D-session.log`）、D2（`after-race-D2.log`）、E（`after-race-E-sound.log`）、E2（`after-race-E2-sound-integration-8g.log`）。**段 A 與段 D 都撞到 10 分鐘預設逾時**：段 D 的樣式含 15 個測試，跑完 13 個（`TestRunToPollAndCrashDump` 為止，累計約 585 秒）後 `panic: test timed out after 10m0s`，沒跑到的 `TestIdleForTrimIgnoresPendingKeys`、`TestSaveDiffDetectorSelfTest` 在 D2 重跑，D2 另外放了耗時最長的 `TestSoundDoesNotChangeSaves`（458 秒），讓段 E 不再逾時；**段 E 以 `FAIL` 結束**，原因是 `TestSoundEngineSessionIntegration` 被容器記憶體上限殺掉（見下一列），它在 E2 以 8g 重跑。聯集的頂層結果：30 ＋ 18 ＋ 9 ＋ 13 ＋ 3 ＋ 10 ＋ 1 ＝ 84，其中 82 PASS、2 SKIP、0 FAIL，所有輸出沒有資料競爭報告。2 個 skip：`TestDiagOverheadPaired`（沒設 `HR_BENCH_OVERHEAD`）、`TestHDHooksColdStartIdentification`（`play.sh` 只把原版掛在 `/orig/orig`，找不到 `/orig/hd-stage/catalog.tsv`；在 `dosgolem.sh` 的掛載下該測試實跑並通過，見上一列沒有列為 skip）。狀態檔相關的 `TestOverlayClassificationOnState`、`TestT2StepDiscontinuityAfterStateLoad`、`TestCallCountsMatchProbe`、`TestSoundPlayMusicPathFromState` 在這裡實跑並 PASS（真實舊狀態檔載入的相容性旁證）。本次新增的 9 個頂層測試（段 C）在 `-race` 下 PASS，其中 `TestColdStartOpensDataFilesFromLangLayer` 因兩次 90M 步跑了 167.97 秒 |
| 其中 `TestSoundEngineSessionIntegration` | 在 `-race`、4g 的段 E 與沒有 `-race`、2g 的 `dosgolem.sh` 單獨執行下被 `signal: killed`（容器記憶體上限）。**不是本次改動造成**：用 `git archive HEAD` 在容器內匯出基準樹到 `workplace/out/l0/base-src/`，在基準樹上用同樣的 2g 單獨跑，同樣 `signal: killed`（`sound-integration-BASELINE-2g.log`）；改動後的樹在 `DOSGOLEM_MEM=6g` 通過（`sound-integration-6g.log`，20.52 秒），在 `HR_PLAY_MEM=8g` 加 `-race` 通過（`after-race-E2-sound-integration-8g.log`，406.79 秒）。整套 `dosgolem.sh` 一次跑時它在 2g 內通過（20.35 秒），單獨跑才超出 |
| `HR_VERBOSE=1 tools/play.sh test-play`（`apps/hr/play`，Xvfb；`after-test-play.log`） | `ok`；`--- PASS` 150 行、`--- SKIP` 1（`TestGenCharsets`，產生器測試）、`--- FAIL` 0。本次沒有改前端 |
| `tools/dosgolem.sh go test -count=1 -v ./internal/...`（`after-internal-all.log`） | `internal/cpu386`、`dos`、`dosfile`、`fsaccess`、`machine`、`state` 都 `ok`；`internal/cpu` 在 2g 下 `TestSingleStep` 被 `signal: killed`（容器記憶體上限，套件本次未改）；`DOSGOLEM_MEM=8g tools/dosgolem.sh go test -count=1 ./internal/cpu/` 通過（86.9 秒，`after-internal-cpu-8g.log`）。全部 `--- PASS` 989、`--- SKIP` 117、`--- FAIL` 0；skip 全是 `FD2*` 與 SingleStep 語料測試（語料不在儲存庫，缺檔 skip），其中沒有 `internal/dos` 或 `internal/state` 的測試 |
| `go vet`（`./internal/dos/`、`./internal/state/`、`./apps/hr/runtime/`、`./apps/hr/cmd/hrsoak`、`./apps/hr/cmd/hrbot`、`./apps/hr/cmd/hr-smoke`、`./cmd/probe/`、`./oracle/`） | 無輸出（通過） |
| `tools/dosgolem.sh go build ./internal/... ./cmd/probe ./cmd/state-compare ./apps/hr/runtime ./apps/hr/cmd/hrsoak ./apps/hr/cmd/hrbot ./apps/hr/cmd/hr-smoke ./oracle` | 通過 |
| `tools/play.sh test-hd`、`gui*` | 未執行（`apps/hr/hd`、前端本次未改） |

預設 `go test` 的 5 個 skip（`TestOverlayClassificationOnState`、`TestT2StepDiscontinuityAfterStateLoad`、`TestCallCountsMatchProbe`、`TestSoundPlayMusicPathFromState`、`TestDiagOverheadPaired`）是環境變數閘門（`HR_BENCH_STATE`、`HR_SOAK_STATE`、`HR_BENCH_OVERHEAD`）的既有測試。其中前 4 個（需狀態檔的真實舊檔載入，也是舊狀態檔相容的旁證）已在 `HR_RACE=1 tools/play.sh test-diag` 的段落帶狀態檔實跑並通過；`TestDiagOverheadPaired` 需 `HR_BENCH_OVERHEAD=1`，未跑。本次新增的測試 skip 數為 0。

## 4. 突變驗證

每一次突變都用 Edit 改壞，在容器內跑測試確認失敗，再用 Edit 還原。還原後用容器內 `sha256sum -c /orig/l0-tmp/pre-mutation.sha256`（24 個改動與新增檔，改動前一次性錄下）確認 24 個都是 OK，並把 `git diff` 輸出重存為 `restore.diff`，容器內 `sha256sum` 與 `pre-mutation.diff` 比對相同（`32bc7800e277b7ebcfa5455afd0880275e6dadf56650755ff407215127080ac8`）。每次還原的 `sha256sum -c` 輸出在 `workplace/out/l0/restore-*.log`，測試輸出在 `workplace/out/l0/mut-*.log`。

| 編號 | 突變 | 被殺死的測試（失敗） | 還原驗證 |
|---|---|---|---|
| M1 | `resolve` 語言層與原版順序對調 | `TestResolveOrderScratchLangRoot`、`TestLangFallsBackToRootPerFile`、`TestResolveLangCaseBasenameAnd83`、`TestOpenReadsLangLayerAndReportsLayer`、`TestEveryDataFileOpensFromLangLayer`、`TestOpenForWriteOnLangFileIsDenied`、`TestAllowFileWritesRejectsLangLayerFile`、`TestExecLoadsProgramFromLangLayer`、`TestSpawnQueuedLoadsProgramFromLangLayer`、`TestFontBytesReadsLangLayerFile` | 24/24 OK，diff 雜湊相同 |
| M2 | `searchFor` 順序改 `Root`、`Scratch`、`LangDir` | `TestSearchForOrderRootLangScratch` | 同上 |
| M3 | 拿掉 `open` 的寫入拒絕區塊 | `TestOpenForWriteOnLangFileIsDenied`（四個子案例）、`TestExtendedOpenForWriteOnLangFileIsDenied` | 同上 |
| M4 | `renameFile` 層別判斷換回字串前綴（`!strings.HasPrefix(src, d.Scratch)`） | `TestRenameFromLangLayerCopiesAndNeverMovesIt`（祖先目錄、前綴相同兩個子案例）、`TestRenameFromRootLayerNeverMovesItEvenWhenScratchIsPrefix` | 同上 |
| M5a | `state.Load` 把預檢移到 `m.LoadState` 之後 | `internal/state` 的 `TestLoadChecksLangLayerBeforeAnyChange`（三個拒絕子案例，機器狀態摘要變了）；`apps/hr/runtime` 的 `TestSessionStateFileBindsToLangLayer`（拒絕之後機器被改動） | 同上 |
| M5b | `dos.LoadState` 把 `checkLang` 移到套用欄位與關 handle 之後 | `internal/dos` 的 `TestLangMismatchRejectsBeforeAnyChange`（handle 已被關閉，後續摘要取不到）。`internal/state` 仍通過，因為 `state.Load` 自己預檢；兩處預檢各由自己的測試保護 | 同上 |
| M5c | `state.Load` 完全拿掉 `PreflightState` 呼叫（只靠 `dos.LoadState` 內的檢查） | `TestLoadChecksLangLayerBeforeAnyChange`（三個拒絕子案例）；`internal/dos` 仍通過 | 同上 |
| M6 | 把檔移出語言層斷言：冷啟動測試的識別包只放 `CFONT.15` | `TestColdStartOpensDataFilesFromLangLayer`（`ESPMES.MRG` 的命中層是 root） | 同上 |
| M7a | `diagSections` 拿掉語言層區段 | `TestCrashDumpHasDiagSections`（T1）、`TestT2JmpSelf`、`TestT2CliJmpSelf`（T2）、`TestT3ManualAndRateLimit`（T3）、`TestDiagLangSectionWithPack`（T1、T2、T3 子案例） | 同上 |
| M7b | `langSection` 拿掉 manifest 雜湊那一項 | `TestCrashDumpHasDiagSections`、`TestT2JmpSelf`、`TestT3ManualAndRateLimit`、`TestLangSection`、`TestDiagLangSectionWithPack` | 同上 |
| M8 | fixture 把 `manifest.json` 放進 `files/`（語言層目錄） | `TestManifestOutsideFilesIsInvisible`（三種樣式都列出 `MANIFEST.JSON`，且 `resolve` 解析得到） | 同上 |
| M9 | `LangDir`、`LangManifest` 拿掉 `json:",omitempty"` | `TestStateDigestOmitsEmptyLangFields`（空語言層的摘要 JSON 含 `"LangDir":""`） | 同上 |
| M10 | `AllowFileWrites` 的語言層判斷改為恆不成立 | `TestAllowFileWritesRejectsLangLayerFile` | 同上 |
| M11 | `resolve` 語言層排在暫存層之前 | `TestResolveOrderScratchLangRoot`（兩個子案例）、`TestOpenReadsLangLayerAndReportsLayer`、`TestUnlinkCreateFamilyBehavesLikeRootFile` | 同上 |
| M12 | `noteOpenLayer` 每次都覆寫 `First` | `TestOpenReadsLangLayerAndReportsLayer` | 同上 |
| M13 | `LangManifest` 雜湊算法在 probe、hrsoak、runtime 三處各改一次（雜湊加一個換行） | `cmd/probe` 的 `TestBindLangDir`、`TestBindLangDirRefusesMissingManifest`；`apps/hr/cmd/hrsoak` 同兩個；`apps/hr/runtime` 的 `TestBindLang`（兩個子案例） | 同上（三處改完後一次驗證） |

M1 至 M7b 涵蓋任務清單的七項；M8 至 M13 是額外加做。M13 對應規格第 8 節 manifest 驗證列的「三處算法」負對照，該列屬 L1，只做了雜湊與正規化這一部分。

## 5. `Overlay_Drive` 比對（`dosbox-src/src/dos/drive_overlay.cpp`，唯讀）

讀了 `Overlay_Drive::FileOpen`（`:589` 至 `:686`）、`OverlayFile::Write` 與 `create_copy`（`:337` 至 `:354`、`:456` 至 `:483`）、`FileCreate`（`:690` 至 `:726`）、`FileUnlink`（`:1177` 至 `:1282`）、`Rename`（`:1843` 至 `:2054`）、`FindNext`（`:1040` 起）、`FindFirst`（`:2058` 至 `:2099`）、`FileExists`（`:1814` 至 `:1839`）、`FileStat`（`:2103` 至 `:2168`）、建構子（`:500` 至 `:535`）。錯誤碼定義見 `include/dos_inc.h:435`（`DOSERR_ACCESS_DENIED` ＝ 5）與 `:450`（`DOSERR_WRITE_PROTECTED` ＝ 19）。

DOSBox-X 只有兩層：overlay（上層，可寫）與 base（下層，唯讀）。dosgolem 現有的 `Scratch` 對應 overlay，`Root` 對應 base；語言層是這份規格新增的第三層，位於兩者之間，沒有 DOSBox-X 的對應物。

| 項目 | `Overlay_Drive` | L0 語言層 | 差異 |
|---|---|---|---|
| 層與優先序 | 讀取時先找 overlay，缺檔才回 base（`FileOpen`、`FileExists`、`FileStat`） | `Scratch`、`LangDir`、`Root`，缺檔逐層回退（`resolve`） | 相同的「上層蓋下層、缺檔回退」語意；L0 多一個唯讀的中間層 |
| 開檔（讀） | overlay 以 `rb`，缺檔再以 `localDrive::FileOpen(OPEN_READ)` 開 base（`:633` 至 `:674`） | 開 `resolve` 找到的那一層的檔 | 相同 |
| 寫入模式開 base 的檔 | 先以讀取開 base，第一次 `Write` 時 `create_copy` 複製進 overlay 再寫（copy-up on first write） | `Scratch` 存在時開檔即 `scratchCopy`（既有行為）；**語言層的檔：回 AX ＝ 5，不複製** | 差異：L0 對語言層拒絕寫入而不是寫到上層。DOSBox-X 的 `ovlreadonly`（`drives.h:1321`，預設 false）對寫入模式開檔回 `DOSERR_WRITE_PROTECTED`（19，`:595` 至 `:599`），錯誤碼與 L0 的 5 不同。規格明定 5 |
| 建檔 | 一律建在 overlay，並清除該檔的 deleted 標記（`FileCreate`） | 建在 `Scratch`，之後 `resolve` 解析到 `Scratch` | 相同；L0 沒有 deleted 標記 |
| 刪除 | overlay 的檔真的刪；base 有同名檔時加 deleted 標記，之後 base 的檔不可見（`FileUnlink`） | `unlink` 只刪 `Scratch` 的檔，`Root` 與語言層的檔不動、回成功；沒有標記 | 差異：沒有墓碑，語言層與原版的檔刪不掉（既有行為，規格已知差異） |
| 改名 | overlay 來源：直接 rename；base 來源：複製到 overlay 的新名稱並把舊名標 deleted（`Rename`） | `Scratch` 來源：`os.Rename`；`Root` 或語言層來源：複製到 `Scratch` 的新名稱，舊名不遮蔽 | 差異：舊名仍可見（沒有墓碑）；複製進暫存層的行為相同。來源層用層別判斷，不比對路徑 |
| 列舉 | `update_cache` 合併 overlay 與 base 目錄，overlay 的時間與大小優先，deleted 的不列（`FindNext`） | `searchFor` 以 `Root`、`LangDir`、`Scratch` 的順序合併，後者覆蓋前者 | 順序語意相同（上層蓋下層）；L0 沒有 deleted 過濾 |
| 屬性、存在、stat | 先看 overlay，再看 base（`FileExists`、`FileStat`、`GetFileAttr`） | `fileAttr`、`createNew` 用 `resolve` 的順序 | 相同 |
| 路徑模型 | 保留目錄樹（長短名對映、`DOSdirs_cache`） | 只認 basename（攤平） | 既有差異，不屬 L0 |
| 層重疊防呆 | overlay 目錄不可等於 base（error 2）、絕對與相對路徑須一致（error 1）、overlay 位於 base 之下時隱藏該資料夾（建構子 `:500` 至 `:535`） | 沒有檢查；層別判斷不依賴路徑前綴，所以重疊（例如 `-saves` 是語言包祖先）不會誤判層別，但 `LangDir` 與 `Root` 設成同一目錄不會被擋 | 差異 |

## 6. 規格缺案與設計選擇

規格缺案（規格沒寫、本實作自行選擇，主代理審閱時請確認）：

1. **`OpenedLayers` 的鍵與 `OnOpenLayer` 的 `name`**：規格寫「以檔名為鍵」，沒說大小寫。選大寫 basename（`strings.ToUpper(filepath.Base(path))`），因為各層磁碟檔名大小寫可以不同，不正規化則同一個檔分成兩筆，首次與最近一次失去意義。`OnOpenLayer` 傳的 `name` 與鍵相同（大寫）；既有的 `OnOpen` 與 `Opened` 仍傳磁碟上的 basename，簽章與行為不變。
2. **`OpenedLayers` 涵蓋的開檔路徑**：只記 `AH=3Dh`（`open`，含 `AH=6Ch` 開啟既有檔，因為它呼叫 `open`）。EXEC 與 overlay 載入（`AH=4Bh`，`readProgram`）、字型服務（`fontBytes`）的讀檔不記層；它們的 `resolve` 呼叫已含語言層，只是沒有報告。字元裝置 `EMMXXXX0` 與失敗的開檔不記。
3. **`OpenedLayers` 的值型別**：`map[string]OpenedLayer`，`OpenedLayer{First, Last string}`，層名是 `scratch`、`lang`、`root`。
4. **`LangManifest` 的編碼**：小寫十六進位字串（規格只說 SHA-256）。
5. **`LangDir` 不存在時的處理與檢查順序**：`Session.Open` 先正規化，再判斷目錄是否存在；不存在則 `LangDir` 與 `LangManifest` 都清為空字串，記一行，不回錯，也不讀 manifest（因此「缺 manifest 回錯」只在目錄存在時成立）。這是規格第 3.1 節對 `Session.Open` 寫的行為。`probe` 與 `hrsoak` 的 `bindLangDir` 對不存在或不是目錄的 `-lang-dir` 回錯，拒絕啟動，不退成原版：它們產生的是收據，規格也沒有授權它們吞掉不存在的目錄。`hrbot` 經 `hrrt.Open`，所以另有 `checkLangBound` 暫時防護：`-lang-dir` 非空而 `Session` 生效的 `LangDir` 為空就回錯，L1 的 `LangStatus()` 上線後換掉它（第 9 節 A1）。
6. **三處實作各自獨立**：依規格「`probe`、`hrsoak` 與 `Session` 各自實作這兩條規則」，沒有放共用 helper（也就沒有 `internal/dos` 匯出函式）。一致性靠三處測試對同一個 manifest 內容 `"hello"` 斷言同一個固定雜湊 `2cf24dba…9824` 與相同的正規化結果。
7. **`AllowFileWrites` 對語言層的檔回錯**：規格說「白名單不收語言層的檔」，沒說是回錯或靜默略過。選回錯（`可寫白名單不收語言層的檔`），避免呼叫端以為可寫。
8. **語言層寫入拒絕的細節**：用 `d.fail(c, 5)`（同時記 `lastErr`，`AH=59h` 讀得到），不記 `Missing`、不配 handle、不記開檔、不看 `AllowFileWrites` 白名單，也不論有沒有暫存層都拒絕。對照：`Root` 的檔在沒有暫存層時照舊就地寫或只記帳（既有行為），所以語言層與 `Root` 在「沒有暫存層」時行為不同；已列入第 5 節的差異。
9. **`PreflightState` 也驗魔術字與版本**：為了與 `LoadState` 共用同一個解碼與檢查（`decodeState`），預檢會拒絕不認得的 DOS 段。副作用見第 8 節第 4 項。
10. **`dos.Install` 不強制 `LangDir` 不變**：「綁定一次」靠呼叫端在 `Install` 之前設定、之後不改，`DOS.LangDir` 是公開欄位，欄位註解寫明；沒有執行期防護。
11. **診斷區段的格式**：固定三行標籤（`LangDir：`、`manifest SHA-256：`、`開檔命中層：`），沒有語言包時三行皆空，有語言包時命中層逐行列八個檔名（七個資料檔加 `CFONT.15`）的首次與最近一次，沒開過的標「未開啟」。放在 `diagSections` 最後（迴圈取樣之後）。規格表只列三項，沒指定文字。
12. **`LangStatus`、驗證原因鍵**：屬 L1，未做。

設計選擇（規格已定、實作時的細節）：

- 層別用具名型別 `Layer`（`LayerNone`、`LayerScratch`、`LayerLang`、`LayerRoot`）；所有 `resolve` 呼叫者接兩個回傳值，不需要層別的丟掉第二個。
- `state.Load` 把兩段整段讀進記憶體（機器段約為記憶體映像大小，數 MB），預檢通過才套用；`dos.PreflightState` 只解碼不改任何欄位。`dos.LoadState` 開頭的檢查在關閉舊 handle 之前。
- `hrbot` 只加 `-lang-dir`，沒有 `SkipLangDigest`（L1）。`hr-smoke` 未加旗標（規格只列 `probe`、`hrsoak`、`hrbot`）。
- 開檔層報告的測試對「需原版」的部分用臨時語言包：測試執行時把原版檔案複製進 `t.TempDir()`，不進儲存庫，缺原版時 `origRoot` 明確 `t.Skip`。

規格互相矛盾之處：沒有發現。

## 7. 未做或沒驗

- **L1 全部**：`apps/hr/l10n`、`hrl10n`、`LangDigest`、`SkipLangDigest`、`LangStatus()`、manifest 內容驗證、譯文表、前端接線。runtime 的 manifest 處理是 L0 暫時做法（只算原始位元組的雜湊，不驗內容），已寫在 `bindLang` 的註解與 `Options.LangDir` 的註解。
- **90M 步冷啟動內只開兩個資料檔**：`CFONT.15` 與 `ESPMES.MRG`。其餘六個資料檔（`COUNTRY.MES`、`SP.MES`、`SYSTEM.MES`、`UWASA.MES`、`POWERMES.MES`、`SHOPTAB.TBL`）的「從語言層開啟」只有 `internal/dos` 的合成單元測試（`TestEveryDataFileOpensFromLangLayer`），沒有走真遊戲到那些畫面的動態收據。規格第 4 節 L0 出口的 A/B 與開檔層報告以冷啟動 90M 為準，已滿足；這是涵蓋限制。
- **語言包內容與原版不同時的遊戲行為**：L0 只驗檔案層。冷啟動測試用的識別包內容與原版相同。
- **Windows、macOS、符號連結**：`LangDir` 正規化是詞法的（`filepath.Abs` 加 `Clean`，`..` 取詞法上一層）；符號連結的 `LangDir` 其上一層是詞法路徑而不是實體路徑。沒有在 Windows 或 macOS 實跑。
- **`go build ./...` 與 `go vet ./...` 整個模組**：在 `golang:1.24-bookworm` 容器內會停在 `ebitengine/oto`、`ebiten` 的 cgo 相依（缺 alsa、X11 標頭），與本次改動無關；已改為只對動到的套件與其相依者 build、vet（全部通過）。`apps/hr/play` 是獨立模組，走 `tools/play.sh test-play`。
- **gofmt**：動到的套件中，`apps/hr/runtime/diag.go`、`diag_test.go`、`bench_test.go`、`bench_diag_test.go` 與 `internal/machine/state.go` 在改動前就不符合 gofmt（`gofmt -d` 的差異在註解的全形括號與無關的對齊，不在本次改動的行），沒有順手格式化。新增檔都已 gofmt。
- **L1 交接備註**：
  - `TestOpenLangDirMissingManifestFails` 釘住的是 L0 的暫時行為（缺 manifest 時 `Open` 回錯）。L1 改成「驗證失敗以空 `LangDir` 開啟，由 `LangStatus()` 回報」時，要一併改寫這個測試與 `bindLang` 的註解；`hrbot` 的 `checkLangBound` 也在那時換掉。
  - `hrbot` 與 `hrsoak` 的輸出目前不含 `OpenedLayers`（只有 `info.txt` 與 `probe` 的報告有）。規格第 3.2 節要求 L1 的 hrbot 收據記各資料檔命中層，L1 要補輸出。
- **效能**：`open` 多一次 map 寫入與 `strings.ToUpper`，`state.Load` 多讀一份記憶體副本；沒有量測。`TestDiagOverheadPaired` 未執行（需 `HR_BENCH_OVERHEAD=1`）。
- **`docs/`、`AGENTS.md` 等**：依邊界沒有動；`docs/spec/005` 第 10 節的 `info.txt` 列與本實作一致，但規格文字沒有更新。

## 8. 邊界自檢與範圍外行為

執行過的命令類型：

- 主機：Read、Edit、Write 工具；`command grep -a`、`ls`、`wc`、`sed -n`、`cut`、`head`、`tail`；fork 內唯讀 `git -C … status|diff|log`；shell 重導向把輸出寫進 `workplace/out/l0/` 與 `workplace/l0-tmp/`；`docker ps` 與 `uptime`（只看狀態）。
- 容器（經 `tools/dosgolem.sh`、`tools/play.sh`，都是 `--rm`、限資源、`--network none`）：`go build|vet|test|run`、`state-compare`、`probe`；`DOSGOLEM_GO_CMD=gofmt`（`-l`、`-d`，對我自己新增的檔案 `-w`）與 `DOSGOLEM_GO_CMD=sha256sum`（`go.sh` 文件載明的用法，用來在容器內雜湊）。
- 為了證明 `TestSoundEngineSessionIntegration` 的記憶體上限問題在基準上也存在，另用 `DOSGOLEM_GO_CMD=sh tools/dosgolem.sh go -c '…'` 在容器內執行 `mkdir -p /out/l0/base-src && git -C /src archive HEAD | tar -x -C /out/l0/base-src`，把基準樹匯出到 `workplace/out/l0/base-src/`（只讀 fork 的 git 物件，沒有寫 fork 的 `.git`，也沒有 checkout 或 worktree），再以 `go -C /out/l0/base-src test` 跑該測試。匯出目錄只含程式碼，不含原版檔案；留在 `workplace/out/l0/`，主代理可刪。
- 第 2.4 節的識別語言包用 `DOSGOLEM_GO_CMD=sh tools/dosgolem.sh go -c 'mkdir -p /out/l0/pack/files && cp /orig/orig/CFONT.15 /orig/orig/ESPMES.MRG /out/l0/pack/files/ && printf hello > /out/l0/pack/manifest.json'` 在容器內建立（原版唯讀掛載，寫入只到 `/out/l0/pack/`，即 `workplace/out/l0/pack/`），內含原版檔案副本，不進版控。
- 沒有在主機執行 python、awk、perl、node、go、xxd、od、hexdump、sha256sum。沒有 `sed -i`。沒有在 fork 內執行 git add、commit、checkout、stash、reset、clean、branch、rebase、merge、push。沒有碰 `/tmp`、`/home/anr2/cht/dosgolem`、`~/.claude`、`~/.cache`、`workplace/orig`。沒有 docker prune、rmi、rm。沒有用網路。
- **一次失誤**：在一個命令裡寫了一個多餘的 `mkdir -p /dev/null`（A/B 輸出目錄其實由容器內的程式自己建立）。`/dev/null` 是字元裝置，該命令沒有任何效果，也沒有建立任何東西。`mkdir` 不在允許清單內，特此記錄。
- 容器內 `go run`、`go test` 可能改動 fork 的 `go.mod`、`go.sum`：最後以 `git status` 確認只有第 1 節列出的檔案，`go.mod`、`go.sum` 沒有出現在變動清單。
- `go.sh` 的容器以我的 UID/GID 執行；收尾用 `find` 檢查 root 擁有的檔案（見下）。
- 原版檔案沒有複製進 fork 的原始碼、測試資料或任何會被提交的檔案；測試只在執行時把原版複製進 `t.TempDir()`。報告與程式碼註解沒有原版對白原文。

對沒有 `-lang-dir` 的呼叫者，行為差異只有下列幾點（其餘 `resolve` 呼叫者在 `LangDir` 為空時走與改動前相同的分支，A/B 以雜湊證實遊戲行為、機器與 DOS 狀態摘要不變）：

1. `DOS` 多了 `OpenedLayers` 記錄與 `OnOpenLayer`（`AH=3Dh` 開檔成功時多記一筆，記憶體成長有界：不同檔名約 100 個）。不被 `TrimDiagnostics` 清。
2. 診斷 `info.txt` 多一個「語言層」區段（三項皆空）。
3. `renameFile` 的「來源在暫存層」判斷改為層別。舊的字串前綴比對（`strings.HasPrefix(src, d.Scratch)`）在兩種設定下與層別判斷不同：
   - `Scratch` 的路徑字串恰為 `Root` 路徑字串的前綴：舊程式把原版目錄的檔當成暫存層的檔，`os.Rename` 搬走；新程式複製進暫存層。`TestRenameFromRootLayerNeverMovesItEvenWhenScratchIsPrefix` 釘住。
   - `Scratch` 是未清理的相對路徑（例如 `./saves`，`Session.Open` 與 `hrsoak -scratch` 都把輸入原樣設進 `Scratch`）：`resolve` 回的是 `filepath.Join` 清過的 `saves/NAME`，舊的前綴比對為假，舊程式把暫存層的檔當成原版的檔複製，舊檔仍在；新程式對暫存層的檔走 `os.Rename`，舊檔消失（`AH=56h` 的語意）。`TestRenameFromScratchLayerWithUncleanRelativeScratch` 釘住。
   - 遊戲沒有 `AH=56h` 站點（規格第 2 節），A/B 不受影響；一般設定（乾淨的絕對路徑）行為相同。
4. `state.Load` 先把兩段讀進記憶體並預檢：DOS 段損壞或魔術字不符時，舊程式機器段已被覆寫才失敗，新程式在套用任何東西之前失敗（失敗路徑更安全，成功路徑結果不變）。
5. `dosState` 多兩個 `omitempty` 字串欄位，gob 向後相容，`dosStateVersion` 維持 3，空語言層的 `dos.StateDigest` 逐位元不變（A/B 證實）。

## 9. 審查後修正

依據 `workplace/l0-review.md`（審查無阻擋，列「應改」A1、A2 與建議 S1 至 S7，另有補充意見 S9；S5 不改，維持記錄所有開檔）。邊界與先前相同：主機不執行直譯器或編譯器，只用包裝腳本跑容器，不 commit。

### 9.1 逐項修改

| 項 | 改了什麼 | 測試 |
|---|---|---|
| A1 | `cmd/probe/langdir.go`、`apps/hr/cmd/hrsoak/langdir.go` 的 `bindLangDir` 簽章改為 `(dir, root, scratch) (langDir, manifest, err)`：`-lang-dir` 不存在或不是目錄時回錯，呼叫端 `die`，不再警告後退成原版（移除 warn 回傳值與兩處呼叫端的警告）。`apps/hr/cmd/hrbot/lang.go` 新增 `checkLangBound`，`main.go` 在 `hrrt.Open` 之後呼叫：`-lang-dir` 非空而 `s.DOS().LangDir` 為空就回錯，拒絕執行；註解寫明 L1 的 `LangStatus()` 上線後換掉。`Session.Open`（`bindLang`）維持規格行為，不改 | `TestBindLangDirRefusesMissingOrNonDirectory`（probe、hrsoak 各一，斷言回錯、點名「拒絕啟動」、不存在與不是目錄兩種）；`TestCheckLangBound`（hrbot）；既有 `TestBindLang` 的「目錄不存在：生效值清為空，不回錯」子案例仍在，釘住 `Session.Open` 行為 |
| A2 | `internal/dos/files.go` 的 `open`：`scratchCopy` 成功後 `layer = LayerScratch`，使 `OpenedLayers` 記的層等於實際開啟的檔所在的層；`OpenedLayers` 欄位註解寫明 | `TestOpenedLayersRecordsScratchAfterCopyUp`：原版目錄的檔（磁碟上小寫名）以寫入模式開啟（有暫存層）後，`OpenedLayers` 的 First 與 Last 為 `scratch`，`Opened` 的 basename 取自暫存層副本，`OnOpenLayer` 回呼 `SAVE.DAT=scratch`；對照組：唯讀開原版目錄的檔仍記 `root` |
| S1 | 層重疊防呆：`bindLang`（簽章改為 `(dir, root, saveDir)`，`Session.Open` 傳 `root` 與 `opt.SaveDir`）、兩個 `bindLangDir` 在正規化（`Abs` 加 `Clean`）之後，`LangDir` 等於原版目錄或暫存層（空字串不比）就回錯；放在「目錄存在」判斷之後、讀 manifest 之前 | `TestBindLangRefusesOverlappingLayers`（runtime，4 個重疊案例含拼法不同，加一個無重疊對照）、`TestOpenRefusesLangDirEqualToRootOrSaveDir`（runtime，需原版，走 `Open`）、`TestBindLangDirRefusesOverlappingLayers`（probe、hrsoak 各一，同樣 5 個案例） |
| S2 | 補 `renameFile` 測試；第 8 節差異表第 3 點補上「`Scratch` 為未清理相對路徑」的情形（舊程式複製、舊檔仍在；新程式 `os.Rename`、舊檔消失；遊戲沒有 `AH=56h` 站點，A/B 不受影響） | `TestRenameFromScratchLayerWithUncleanRelativeScratch`（`t.Chdir` 到暫存目錄，`Scratch` 為 `./saves`） |
| S3 | 補測試：暫存層與語言層都有同名檔時，寫入模式（模式 1 與 2）開檔成功並寫進暫存層（暫存層優先），語言層的檔不動 | `TestWriteOpenSucceedsWhenScratchShadowsLangFile` |
| S4 | `apps/hr/runtime/crash.go` 的 `CrashDump` 註解改為：語言包 Session 的狀態檔要用 `probe -lang-dir` 或同一語言層的 Session 載入，`hrhd` 等沒有 `-lang-dir` 的工具會被拒絕 | 註解，無測試 |
| S6、S7 | 第 3 節註明預設 `go test` 的 5 個 skip 是環境變數閘門的既有測試，4 個已在 test-diag 段帶狀態檔實跑通過；第 7 節加 L1 交接備註（`TestOpenLangDirMissingManifestFails` 與 `bindLang` 註解、`hrbot` 的 `checkLangBound`、`hrbot` 與 `hrsoak` 輸出 `OpenedLayers`） | 文字 |
| S9 | `TestStateDigestOmitsEmptyLangFields` 原本的斷言（`pack` 與 `plain` 各用不同的 `t.TempDir()`，`Root` 不同所以摘要必然不同）是恆真。改成：新增 `langDOSAt(t, root, dir, manifest)`，三個 DOS 用同一個 `Root`、同樣的狀態，只有 `LangDir`、`LangManifest` 不同，斷言摘要因新欄位而不同（三種：兩者都有、只有 `LangDir`、只有 `LangManifest`）；另加控制組：同一個 `Root`、同樣設定的兩個 DOS 摘要相同，差異才能歸因於新欄位。JSON 斷言（空欄位不進摘要 JSON）保留 | 見突變 N8 |

### 9.2 測試結果

| 指令 | 結果 |
|---|---|
| `tools/dosgolem.sh go test -count=1 ./internal/dos/ ./internal/state/ ./cmd/probe/ ./apps/hr/cmd/hrsoak/ ./apps/hr/cmd/hrbot/`（`fix-quick.log`） | 五個套件全部 `ok` |
| `tools/dosgolem.sh go test -count=1 -v -run 'Lang\|Layer\|ColdStart\|Bind\|Trim' ./apps/hr/runtime/`（`fix-runtime-lang.log`） | `ok`，語言層相關測試全部 PASS（含新增的 `TestBindLangRefusesOverlappingLayers`、`TestOpenRefusesLangDirEqualToRootOrSaveDir`） |
| `HR_RACE=1 HR_TEST_RUN='Lang\|Layer\|ColdStartOpens' tools/play.sh test-diag`（`fix-race-lang.log`） | `ok`，11 個頂層測試全部 PASS、無 skip、無資料競爭報告（`TestColdStartOpensDataFilesFromLangLayer` 204.29 秒），共 240.6 秒 |
| `tools/dosgolem.sh go test -count=1 -v` 對 `./internal/dos/ ./internal/state/ ./apps/hr/runtime/ ./apps/hr/patch/ ./cmd/probe/ ./apps/hr/cmd/hrsoak/ ./apps/hr/cmd/hrbot/`（`fix-dosgolem-v.log`） | 除 `apps/hr/runtime` 外全部 `ok`。`apps/hr/runtime` 在 2g 下被 `signal: killed`：停在 `TestSoundEngineSessionIntegration`（第 3.2 節已記錄這是基準樹上也有的容器記憶體上限問題，不是本次改動造成；上一輪同一指令在 2g 內通過，這次沒有） |
| `DOSGOLEM_MEM=6g tools/dosgolem.sh go test -count=1 -v ./apps/hr/runtime/`（`fix-runtime-6g-v.log`） | `ok`（164.3 秒）；`--- PASS` 95、`--- SKIP` 5、`--- FAIL` 0；5 個 skip 與第 3.2 節相同（環境變數閘門） |
| `tools/play.sh test`（`fix-play-test.log`） | `apps/hr/patch`、`apps/hr/runtime` 都 `ok`（runtime 140.9 秒） |
| `go vet ./internal/dos/ ./internal/state/ ./apps/hr/runtime/ ./apps/hr/cmd/hrsoak ./apps/hr/cmd/hrbot ./apps/hr/cmd/hr-smoke ./cmd/probe/ ./oracle/` | 無輸出（通過；最後一次改動是 `internal/dos/lang_test.go`，對 `./internal/dos/` 另跑 `go vet` 通過） |
| `DOSGOLEM_GO_CMD=gofmt tools/dosgolem.sh go -l` 對 27 個改過或新增的檔 | 只列出 `apps/hr/runtime/diag.go`、`apps/hr/runtime/diag_test.go`，兩個都是改動前就不合 gofmt 的既有檔案（`gofmt -d` 的差異在註解的全形括號與無關行的註解對齊，不是本次改動的行），依指示沒有格式化。10 個新增檔與其餘改過的檔無輸出 |

### 9.3 新突變

做法同第 4 節：先錄 `workplace/l0-tmp/pre-mutation2.sha256`（27 個檔）與 `pre-mutation3.sha256`（28 個檔，加 `internal/dos/state_digest.go`），每次突變用 Edit 改壞、容器內跑測試確認失敗、Edit 還原，再以容器內 `sha256sum -c` 確認全部 OK，並把 `git diff` 輸出重存、容器內雜湊與突變前相同（`3691f89718ea1783cbe639b2c40987193936ae530613d1f3ecc216dd10e8a53f`）。輸出在 `workplace/out/l0/mut-N*.log` 與 `restore-N*.log`。

| 編號 | 突變 | 被殺死的測試（失敗） | 還原驗證 |
|---|---|---|---|
| N1 | probe 的 `bindLangDir` 對不存在的目錄回 `("", "", nil)` | `cmd/probe` 的 `TestBindLangDirRefusesMissingOrNonDirectory` | 27/27 OK，diff 雜湊相同 |
| N2 | hrsoak 的 `bindLangDir` 同上 | `apps/hr/cmd/hrsoak` 的 `TestBindLangDirRefusesMissingOrNonDirectory` | 同 N1（N1 至 N3 一起還原後驗證） |
| N3 | hrbot 的 `checkLangBound` 條件恆為假 | `apps/hr/cmd/hrbot` 的 `TestCheckLangBound` | 同 N1 |
| N4 | `open` 拿掉 `layer = LayerScratch` | `TestOpenedLayersRecordsScratchAfterCopyUp`（`OpenedLayers[SAVE.DAT]` 為 root、回呼為 `SAVE.DAT=root`） | 27/27 OK，diff 雜湊相同 |
| N5 | 三處層重疊檢查（runtime 的 `bindLang`、probe 與 hrsoak 的 `bindLangDir`）條件恆為假 | runtime 的 `TestBindLangRefusesOverlappingLayers`（4 個重疊子案例）、`TestOpenRefusesLangDirEqualToRootOrSaveDir`；probe 與 hrsoak 的 `TestBindLangDirRefusesOverlappingLayers`（各 4 個重疊子案例）。第一次 `-run` 樣式寫錯，沒有選到 probe 與 hrsoak 的測試，已用正確樣式補跑 | 27/27 OK，diff 雜湊相同 |
| N6 | `renameFile` 層別判斷換回字串前綴 | `TestRenameFromScratchLayerWithUncleanRelativeScratch`（新），以及第 4 節 M4 已列的 `TestRenameFromLangLayerCopiesAndNeverMovesIt`（兩個子案例）、`TestRenameFromRootLayerNeverMovesItEvenWhenScratchIsPrefix` | 27/27 OK，diff 雜湊相同（N6 與 N7 還原後一起驗證） |
| N7 | `open` 的寫入拒絕改成「檔名在語言層目錄就拒絕」（`lookupDOS(d.LangDir, …) != ""`） | `TestWriteOpenSucceedsWhenScratchShadowsLangFile`（模式 1 與 2） | 同 N6 |
| N8 | `dos.StateDigest` 解碼後把 `LangDir`、`LangManifest` 清空（新欄位不進摘要） | `TestStateDigestOmitsEmptyLangFields`（三種情形都失敗：「同一個 Root，只有語言層欄位不同，DOS 狀態摘要必須不同」） | 28/28 OK（含 `state_digest.go`），diff 雜湊相同，`git diff --stat -- internal/dos/state_digest.go` 為空（檔案與基準相同） |

### 9.4 `LangDir` 為空的 A/B 重跑

與基準相同的指令與輸入（只有輸出路徑改成 `/out/l0/ab2/…`），在所有審查後修正與測試改動之後執行：

| 項目 | Session 層（`l0drv.go`） | probe 層 |
|---|---|---|
| 畫面 PNG SHA-256 | `853a695340271b1e2540702d6d5f1e78f3807e230c666a181e3985097879adaf`，與基準相同 | 同左（容器內 `sha256sum` 確認） |
| CPU 暫存器 | `R 0000 0138 00D3 0000 7D6A 7D6C 0000 0010`、`Hi` 全 0、`Seg 27B4 1F8A 54C0 3135 0000 0000`、`IP 0098`、`FLAGS 7297`，與基準相同 | `CS:IP ＝ 1F8A:0098  AX=0000 BX=0000 CX=0138 DX=00D3`、`DS=3135 ES=27B4 SS:SP=54C0:0D6A`，與基準相同 |
| `machine.StateDigest` | `37ef33a4…5c06`，`state-compare` `equal:true` | `e4b810ae…1c04`（第 89,999,999 步），`equal:true` |
| `dos.StateDigest` | `d3b911ef…0e96`，`equal:true` | `dd9e744d…8b86`，`equal:true` |

日誌：`ab2-sess.log`、`ab2-probe.log`；輸出 `workplace/out/l0/ab2/`。

### 9.5 最終狀態

`workplace/l0-tmp/post-final2.sha256` 是 27 個改過或新增的檔的最終雜湊；與 `pre-mutation3.sha256` 比對，最後一次突變還原之後沒有任何差異。`git status --short` 為 17 個已追蹤改動加 10 個新增檔，`go.mod`、`go.sum` 沒有變動，`workplace/out/l0` 與 `workplace/l0-tmp` 沒有 root 擁有的檔案。工作樹未 commit，留給主代理審閱。邊界：這一輪沒有在主機執行直譯器或編譯器，沒有多餘的 `mkdir`，沒有 `sed -i`，沒有 fork 內的 git 寫入操作；容器操作只用 `tools/dosgolem.sh`、`tools/play.sh`（含 `DOSGOLEM_GO_CMD=gofmt` 與 `DOSGOLEM_GO_CMD=sha256sum`）。
