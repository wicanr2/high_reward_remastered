# 029 L1 runtime 與 hrbot 語言包接線的實作收據（docs/spec/008 第八版）

日期：2026-10-04
狀態：收據（實作驗證）。記錄目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱。涵蓋 `apps/hr/runtime` 與 `apps/hr/cmd/hrbot` 的語言包驗證接線和 identity 包冷啟動 A/B；前端 `apps/hr/play` 的接線、試點、玩家端冷建置尚未做。
輸入：fork `workplace/dosgolem` 分支 `hr`，基底 `ca3611f`，本提交 `f03fc83`；補丁備份 `engine/patches/0031-apps-hr-runtime-hrbot-lang-wiring-008.patch`，已用 `git am` 套在 `ca3611f` 並確認重現同一棵樹（`2d2f88fa…`）。原版輸入 `MAIN.EXE` SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。
來源：實作者報告（`workplace/l1-wire1-report.md`，不進版控）經主代理審閱後搬入；主代理另在容器內獨立重跑 runtime 語言層測試、hrbot、五個 `l10n` 套件、`cmd/probe`、`hrsoak` 全部 `ok`，`go vet ./apps/hr/... ./cmd/probe/...` 無輸出。這一階段沒有另請審查者，接線屬於規格第 3.2 節已審查的契約。

## 1. API（`apps/hr/runtime`）

```go
type Options struct {
	// ...既有欄位
	LangDir        string // 語言包根底下的 files/（最後一段必須是 files）
	LangDigest     string // 前端以 l10n.ExpectedDigest 算好的預期輸入摘要
	SkipLangDigest bool   // 為真時略過輸入摘要，LangDigest 被忽略；只供 hrbot 與測試入口
}
const LangReasonVerifyFailed = "verify-failed"
type LangStatus struct {
	LangDir string // 生效值（正規化後；沒有語言層或驗證失敗為空）
	Reason  string // "" 或 LangReasonVerifyFailed
}
func (s *Session) LangStatus() LangStatus
func LangLayerText(layers map[string]dos.OpenedLayer) string // 診斷區段與 hrbot 共用的命中層格式
```

`Open` 的行為：

| 情形 | 結果 |
|---|---|
| `LangDir` 非空、`LangDigest` 為空、未明示 `SkipLangDigest` | `Open` 回錯（程式錯誤，在讀 `MAIN.EXE` 之前，訊息含「沒有明示 SkipLangDigest」） |
| `LangDir` 等於原版目錄或 `SaveDir` | `Open` 回錯（L0 既有行為） |
| 目錄不存在或不是目錄、最後一段不是 `files`、manifest 驗證失敗（任何原因鍵，`bad-options` 除外） | `Open` 不回錯，以空語言層開啟，記一行（含原因鍵與 `verify.Error.Detail`），`LangStatus()` 回 `{"", "verify-failed"}`；診斷 `info.txt` 語言層區段第一項另記原因鍵 |
| 通過 | `LangStatus()` 回 `{<正規化 LangDir>, ""}`，`DOS.LangManifest` 為 `manifest.json` 位元組的 SHA-256 |

原版輸入雜湊表由 `RequiredFiles()` 組成（九個輸入，與 `l10n.ExpectedInputHashes` 同源）。`bad-options` 只在呼叫端沒給必要選項時出現，不可能由使用者資料觸發，所以當程式錯誤回錯。`LangDir` 的最後一段必須是 `files`：`verify.Verify(包根)` 驗的是 `<包根>/files`，不擋的話 `LangDir` 可綁到沒驗過的 `<包根>/other`（突變 9 證明這條規則承重）。

hrbot：`-lang-dir` 傳 `LangDir` 並明示 `SkipLangDigest: true`；`LangStatus().Reason` 非空時退出碼 1；新旗標 `-allow-lang-fail` 只供負對照；結束報告與 `summary.json` 的 `lang` 欄記生效 `LangDir`、原因鍵與命中層。

## 2. 測試

| 套件 | 基準（原版在手） | 改動後（原版在手） | 改動後（原版缺席） |
|---|---|---|---|
| `apps/hr/runtime` | 80 通過、5 skip（`-skip` 版） | 91 通過、5 skip（`-skip` 版 90、5） | 35 通過、61 skip |
| `apps/hr/cmd/hrbot` | 1 | 5 | 3 通過、2 skip |
| 其餘四個 `l10n`、`hrl10n` 套件 | 同 `docs/re/028` | 同 | 同 |
| 合計 | 333 通過、6 skip | 348 通過、6 skip、0 失敗 | 269 通過、85 skip、0 失敗 |

- runtime 新增 10 個頂層測試（驗證矩陣九種失敗、`SkipLangDigest` 四個案例、`LangDigest` 缺漏先於存在性檢查、`LangStatus`、真建置器造的 identity 包），L0 既有測試中依賴「manifest 只讀位元組不驗證」的案例已改寫，原因逐項在實作者報告（三類：假 manifest 被拒、`LangDigest` 缺漏先擋、缺 manifest 不再回錯），沒有放寬新行為。
- `TestSoundEngineSessionIntegration` 在 2g 容器內 `signal: killed`（基準樹也被殺，與語言層無關，單獨跑 4g 通過 26 秒），所以完整跑 runtime 套件的結果在 2g 下不穩；驗收以 `-skip` 版為準。
- `-race`：hrbot 全套與 runtime 語言層相關測試（含三個 90M 步冷啟動測試）通過，0 個 `DATA RACE`；runtime 全套超過 `go test` 預設的 10 分鐘上限，其餘測試沒有跑過 `-race`。
- `gofmt -l`：改動的檔案無輸出；`apps/hr/runtime` 有 4 個既有檔案（`bench_diag_test.go`、`bench_test.go`、`diag.go`、`diag_test.go`）在基準樹就有輸出，沒有格式化。

## 3. 突變驗證

13 個突變（拿掉摘要比對；`SkipLangDigest` 為真時仍比對；驗證失敗時 `Open` 回錯；驗證失敗不清空生效 `LangDir`；`LangDigest` 缺漏檢查改在存在性檢查之後；`LangStatus` 永遠回空；hrbot 對非空原因鍵不非零結束；`-allow-lang-fail` 無效；拿掉 `files` 最後一段規則；`LangManifest` 算法改動；`normDir` 不正規化；診斷區段不記原因鍵；hrbot 不傳 `SkipLangDigest`），全部被至少一個測試殺死，還原後八個檔以 `sha256sum -c` 全部相同。突變 5 與 7 暴露並修正了兩個測試缺陷（錯誤訊息比對被測試目錄路徑污染、突變存活時測試會真的玩一遊戲小時）。

## 4. A/B 收據

驅動程式是 L0 的 `l0drv.go` 加 `-lang-dir`、`-lang-digest`、`-skip-digest` 與 `LangStatus`、`OpenedLayers` 輸出（`workplace/l1-wire1-tmp/l1drv.go`，不進版控）；輸入與 L0 基準相同（`Interval: NativeInterval`、堆疊補丁開、冷啟動、第 35,000,000 步在 (312, 211) 點左鍵、跑到 90,000,000 步，`docs/re/027` 第 2 節）。語言包用 `hrl10n` 在容器內建出（identity 包：`dir=zh-TW-7b8a4c0c2f85`，manifest 雜湊 `49227349d44924109634b9cdb7a4cd94532ab067dd4d9702d55067f5f5f9a88c`，輸入摘要 `7b8a4c0c…113a`，建置器版本 `a96d619d`，`hrl10n verify` 退出碼 0）。語言包含原版位元組，只放 `workplace/out/l1-wire1/`。

| 項目 | L0 基準 | identity 包 | 差一列的 table 包（負對照） | 竄改一個位元組的包 |
|---|---|---|---|---|
| 畫面 PNG SHA-256 | `853a6953…adaf` | `853a6953…adaf`（相同） | `5d49d5f6…c72b`（不同） | `853a6953…adaf`（回退原版，相同） |
| R、Seg、IP、FLAGS | `0000 0138 00D3 0000 7D6A 7D6C 0000 0010`、`27B4 1F8A 54C0 3135 0000 0000`、`0098`、`7297` | 相同 | 不同（`000F 0000 03CE 0190 …`、IP `051D`） | 相同 |
| `machine.StateDigest` | `37ef33a4…5c06` | `37ef33a4…5c06`（相同） | 不同 | 相同（回退原版） |
| `dos.StateDigest` | `d3b911ef…0e96` | `5c20b510…3559`（不同，`LangDir` 與 `LangManifest` 非空必然不同，不比） | 不比 | 與基準相同（語言層為空） |
| `LangStatus` | 無 | `{LangDir, ""}` | `{LangDir, ""}` | `{"", verify-failed}` |
| 命中層 | 無 | `CFONT.15` 與 `ESPMES.MRG` 是 lang，其餘十六個檔名是 root，另六個資料檔 90M 步內未開啟 | `CFONT.15`、`ESPMES.MRG` 是 lang | `CFONT.15`、`ESPMES.MRG` 是 root |

- 負對照包：`ESPMES#121.0`（原項目 21 bytes）以一列合成的 8 個字（取自 `charmap-zh-TW.tsv`）替換，`hrl10n build -mode table -with-candidates` 建出，`verify` 通過；開 `screen.png` 確認對白框顯示的是這 8 個合成字，所以雜湊改變來自這一列。這一列替換整個項目，不是只差一個字（只差一個字要讀原項目位元組來改，不在權限內）。
- 竄改負對照：複製 identity 包到另一個目錄，`files/SP.MES` 偏移 100 由 `00` 改 `FF`（`cmp -l` 只有 1 個位元組不同）；`hrl10n verify` 退出碼 1（`file-hash: SP.MES`）；hrbot 退出碼 1 並拒絕執行；加 `-allow-lang-fail` 能啟動，原因鍵 `verify-failed`。
- 摘要比對：不帶 `-skip-digest`，傳正確摘要時啟用；傳全零摘要時回退原版（原因 `digest`），畫面與暫存器同基準。
- `LangManifest` 三工具對拍：`hrl10n verify`、Session（驅動程式與 hrbot）、`cmd/probe`、`apps/hr/cmd/hrsoak` 對同一個 identity 包印出同一個 `manifest-sha256`。`probe` 與 `hrsoak` 的測試仍用內容 `hello` 的假 manifest（它們不驗證內容），所以「三處同值」在測試層只由 runtime 側的 `TestLangIdentityRules` 加端對端對拍支撐，兩個套件各自缺一個以真 manifest 為輸入的測試。
- `tools/dosgolem.sh probe` 用的 `/out/probe` 是 L0 之前建的舊執行檔，不認得 `-lang-dir`；本次改用 `go run ./cmd/probe`，沒有動 `/out/probe`（要重建它用 `tools/dosgolem.sh build`）。

## 5. 未做與已知差異

- 前端 `apps/hr/play`（`planIngame`、`ingameStatus`、旗標 `-ingame-lang`、`-l10n`、F1 狀態列、F4 提示）、試點、identity 包的玩家端冷建置：未做。
- 冷啟動 90M 步內只開 `CFONT.15` 與 `ESPMES.MRG`；`SP.MES` 要走到約 97M 步以後；其餘五個資料檔的語言層開檔只由 `internal/dos` 的單元測試涵蓋。
- 診斷 `info.txt` 在驗證失敗回退時只有第一項記原因鍵，第二、第三項（manifest 雜湊、命中層）為空，規格 `docs/spec/005` 沒有規定這時要不要列命中層（`OpenedLayers` 在回退的 Session 仍有值，全是 root）。
- `TestSoundEngineSessionIntegration` 在 2g 下不穩，列為後續處理。
