# 028 L1 語言包建置器與洩漏判準的實作收據（docs/spec/008 第八版）

日期：2026-10-04
狀態：收據（實作驗證）。記錄目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱。只涵蓋 L1 的程式庫與命令列（預算與模擬器、檔案格式與譯文表、轉碼、洩漏判準、建置器、manifest 與驗證）和入口腳本；前端接線、試點譯文、玩家端冷建置（Wine、macOS）尚未做，見第 8 節。
輸入：fork `workplace/dosgolem` 分支 `hr`，基底 `fabe4f2`，L1 提交 `ca3611f`；補丁備份 `engine/patches/0030-apps-hr-l10n-builder-leakscan-l1-008.patch`，已用 `git am` 套在 `fabe4f2` 並確認重現同一棵樹（`f0445243…`）。原版輸入的 SHA-256 以 `apps/hr/runtime/required.tsv` 與 `docs/re/source-inventory.tsv` 為準。
來源：四位實作者的報告（`workplace/l1-budget-report.md`、`l1-formats-report.md`、`l1-leakscan-report.md`、`l1-build-report.md`，不進版控）經主代理審閱後搬入；預算、格式、洩漏判準三份各有一位唯讀審查者的報告（`workplace/l1-budget-review.md`、`l1-formats-review.md`、`l1-leakscan-review.md`），建置器的審查見第 7 節。審查發現的阻擋與應改項目都已處理。

## 1. 套件與驗收

| 套件 | 位置（fork） | 驗收指令 |
|---|---|---|
| 預算與 `1676` 模擬器 | `apps/hr/l10n/budget` | `tools/dosgolem.sh go test -count=1 -race ./apps/hr/l10n/budget/` |
| 檔案格式、譯文表、轉碼、資料表 | `apps/hr/l10n` | `tools/dosgolem.sh go test -count=1 ./apps/hr/l10n/` |
| 洩漏判準 | `apps/hr/l10n/leakscan`、`apps/hr/cmd/hrl10n` 的 `leakscan` 子命令 | `tools/dosgolem.sh go test -count=1 ./apps/hr/l10n/leakscan/ ./apps/hr/cmd/hrl10n/` |
| 建置器、manifest、驗證 | `apps/hr/l10n`（`build.go`、`digest.go`、`tabledir.go`、`budgetadapter.go`）、`apps/hr/l10n/verify`、`apps/hr/cmd/hrl10n` | 同上 |

整體：`tools/dosgolem.sh go test -count=1 ./apps/hr/l10n/... ./apps/hr/cmd/hrl10n/`，五個套件全部 `ok`；`go vet` 與 `gofmt -l` 無輸出。原版缺席時需原版的測試明確 skip（不是通過）。

## 2. 預算與模擬器（`apps/hr/l10n/budget`）

| 項目 | 結果 |
|---|---|
| 測試 | 頂層 41 個、子測試 28 個，全通過；`-race` 通過 |
| 模擬器性質測試 | seed 20261004，隨機 40000 組，具體模式失敗 14625 組，對抗模式（保守）涵蓋全部具體失敗；吃換行的判定與 `k` 無關 |
| 模擬器窮舉 | 展開字串取 {S 代表值 `41`、P 代表值 `E0`}：單個 `%s` 的樣板長度 0 至 8（511 種）、兩個 `%s` 各 0 至 8（511 x 511 種） |
| 對拍 | `docs/re/023` 的 T0、T1、T3a、T3b 與 `docs/re/025` 的 V1 至 V7：預測偏移與是否吃換行全部吻合；試點邊界變體（k 為 31，P 在偏移 30）同步假說 [0, 32, 35]、位移假說只剩一次呼叫且吃換行；對照組（P 在偏移 29）[0, 31] |
| 自動折行性質測試 | 單行 5000 組（六種窗口），3839 組需折行，2412 成功、1427 回違規；多行 8000 組，折行成功 2693 組（含以 `0x0A` 結尾而被折的行 1325 條）、回違規 3429 組 |
| 突變 | 實作者報告的突變表 M 系列 43 列、審查後 N 系列 11 列（含 a、b 變體），全部被殺死；N6 有已知限制（性質測試看不見不必要的拒絕，那個方向靠確定性案例） |

審查後的改動：標點只認 lead `A1`；`Input.BreakAfter` 可由呼叫端提供；新增 `WrapAndCheck`（折完再檢查，因為折行新增的換行會使 `length` 在折完才超過）；補 `length` 計換行、最後一列的 `1676`、lead 後接 NUL 的測試。

## 3. 檔案格式、譯文表、轉碼（`apps/hr/l10n`）

| 項目 | 結果 |
|---|---|
| 解析再序列化 | 七個檔案逐位元相同（SHA-256）；項目數 11、116、314、110、192、1024、792；ESPMES 項目總數 1024 由測試自己的讀法獨立數出（N2 合計 1034 減 1，非空群組 10、空群組 115） |
| 負對照 | 七個檔案各改一個偏移位元，比較器與往返都失敗 |
| 測試 | 原版與 IDA 輸出在手 69 通過；`HR_ORIG=/nonexistent` 57 通過、12 skip（需原版者） |
| 字集 `charmap-zh-TW.tsv` | 1716 字（與 `docs/re/020` 相同）；x/text 的 Big5 對這 1716 字一對一（Undecodable 0、Collisions 0）；兩次產生逐位元相同；產生器 `tools/l10n/gencharmap/main.go`（容器內執行，讀 IDA 輸出，不進 fork） |
| 與整檔嚴格掃描的差異 | 整檔法得 1721 字：只在整檔法 6 個、只在 IDA 法 1 個；原因是 MZ 重定位 word 與資料段之外的程式碼區，不是遊戲文字（實作者報告第 5 節） |
| 窗口資料表 `esp-windows.tsv` | 鍵集合 1024，計數 625／3／2／394；內嵌雜湊守門 `f236e42c…`；與 `docs/re/data/024-esp-windows.tsv` 位元組相同 |
| 突變 | 23 個第一輪加 17 個審查後（N1 至 N17），全部被殺死 |

審查後新增：`Table.Merge`（不覆蓋 `accepted` 與 `keep`）、`Table.Coverage`、`Table.UnclaimedIDs`、`group-exception` 的邊界比對、`Adopt` 查不到窗口類別時記違規而不提早回傳、SHOPTAB 名稱含換行記違規、`Policy.SerializeOptions`。

## 4. 洩漏判準（`apps/hr/l10n/leakscan`）

| 項目 | 結果 |
|---|---|
| 單位 | 3728 個（視窗鍵 16252、整段鍵 368）：七個資料檔加 `OP.TXT`、`OP0.TXT` 至 `OP5.TXT`（60 個）；沒有查找鍵的單位 111 個（`ESPMES.MRG` 42、`SYSTEM.MES` 69，原因是正規化後不足 3 字或非標點字不足 3 個），其餘 3617 個都有鍵 |
| SHOPTAB 對齊 | 792 筆、每筆 25 bytes、第 21 個位元組 792／792 為 `00`；792 個單位起點與 25 的餘數為奇數的 0 個、落在名稱欄之外的 0 個；全形英數不轉半形後 SHOPTAB 的沒有鍵單位由 360 降到 0 |
| 測試 | 最終樹（原版在手）`leakscan` 套件 53 個頂層測試通過；實作者在審查修正後量到（含 `cmd/hrl10n` 的 leakscan 測試，`cmd/hrl10n` 當時的 build、verify 測試數與最終不同）66 個頂層、123 個通過（含子測試）、0 skip；原版缺席 61 個頂層通過、34 skip（需原版的測試） |
| 全單位自我回收 | 3617 個有鍵單位以 UTF-8 文字與 Big5 位元組各自掃一次，全部命中自己 |
| 突變 | leakscan 61 個（M 系列 28、N 系列 33）加 `cmd/hrl10n` 的 C 系列 7 個，共 68 個，全部被殺死 |
| 閘門 | 原版單位來源缺檔、雜湊不符（`required.tsv` 與 `OP*.TXT` 的內嵌雜湊）、索引自檢失敗、allowlist 無效、掃描範圍為空、清單項目不存在、歷史串流缺結尾標記或記錄數不符，全部退出 2 |
| 範圍與耗時 | repo 163 個檔 0.95 秒、fork 361 個檔 0.82 秒（容器啟動計入） |

## 5. 基準掃描（`tools/l10n/leakscan.sh`，原版在手，2026-10-04）

工作樹：本 repo 的 `git ls-files`（含 `engine/patches/`、`hd/`）加 fork 的 `git ls-files`（路徑加 `workplace/dosgolem/` 前綴），掃 2026 個檔，單位 3728 個，命中 12 項，allowlist 放行 0 項。命中只列路徑與單位身分：

| 路徑 | 單位身分 |
|---|---|
| `docs/spec/004-hd-overlay.md` | `ESPMES.MRG@A2AC.0` |
| `tools/img/decode_all.py` | `ESPMES.MRG@AA39.0`、`ESPMES.MRG@B971.0` |
| `workplace/dosgolem/internal/dos/dos.go` | `ESPMES.MRG@5491.0` |
| `workplace/dosgolem/apps/buckrogers/ecl_pre056_corpus_test.go` | `ESPMES.MRG@9EBA.0`、`SYSTEM.MES@1012.0` |
| `workplace/dosgolem/docs/findings/003-pool-of-radiance-runs-but-stalls.md` | `ESPMES.MRG@A2AC.0` |
| `workplace/dosgolem/docs/knowledge-base/010-dos-int21-coverage.md` | `ESPMES.MRG@A2AC.0` |
| `workplace/dosgolem/docs/knowledge-base/030-protected-mode-and-dos4gw.md` | `ESPMES.MRG@A2AC.0` |
| `workplace/dosgolem/docs/spec/007-com-loader-and-keyboard.md` | `ESPMES.MRG@A2AC.0` |
| `workplace/dosgolem/docs/spec/014-hardware-keyboard.md` | `ESPMES.MRG@A2AC.0` |
| `workplace/dosgolem/docs/spec/185-keyboard-trace-and-keypad-names.md` | `ESPMES.MRG@6A76.0` |

說明：

- `ESPMES.MRG@A2AC.0` 出現在本 repo 一份與 fork 內五份文件，其中 fork 的檔案是鍵盤與 DOS 服務一類的上游文件，與本專案無關。單位的所屬段長度由 `leakscan -check-allow` 判定可否登記；本表不判斷。
- 來自長段（所屬段超過 7 個字）的 3 至 5 字片段不能登記（`docs/spec/008` 第 3.9 節第 5 項的補救路徑待 U8）。`ecl_pre056_corpus_test.go` 的 `ESPMES.MRG@9EBA.0`（3 字，所屬段 12 字）是已知的一筆。
- 全歷史（`tools/l10n/leakscan.sh --history`，約 1 分 14 秒）：本 repo 1028 筆（路徑, blob）記錄 9 項命中（`docs/spec/004-hd-overlay.md` 7、`tools/img/decode_all.py` 2，同一批單位在多個 commit 的版本），fork 4104 筆記錄 93 項命中（`internal/dos/dos.go` 73，其餘在上述文件與 `apps/buckrogers`）。歷史命中不是 push 閘門的條件（`docs/spec/008` 第 3.9 節第 5 項），轉公開前由使用者決定處理方式。
- `docs/re/012` 引用的 5 個標籤在 `MAIN.EXE` 的硬編碼字串，不是資料檔單位，所以不在命中內，這類引用靠人工複核（規格 009 的範圍）。
- 正對照：基準掃描本身就是正對照（12 項命中），單元測試以合成世界與原版世界的全單位自我回收提供額外證據；空目錄掃描退出 2、乾淨目錄退出 0 已用 `tools/l10n/leakscan.sh` 實測；`tools/pkg/leakscan.py` 對放進 `l10n/zh-TW/` 的暫存包回報路徑洩漏（退出 1）。
- allowlist `tools/l10n/leakscan-allow.tsv` 目前沒有登記項目（U8 待使用者回答）。`--check-allow` 對空檔回報被拒 0 行。

## 6. 建置器、manifest、驗證

| 項目 | 結果 |
|---|---|
| 建置器版本 | `Version()` ＝ `data/builder-golden.txt` 位元組的 SHA-256 前 8 碼 ＝ `a96d619d`（完整 `a96d619d9e50a273c046f793f0f4c053ff20d0384b25d57033644593a465a7e7`，在容器內以 `sha256sum` 取得，golden 在審查修正前後逐位元相同） |
| golden | 合成 fixture 在 table 模式以使用者原版建出四個變體：預設（採用 25 列）、`-with-candidates`（41）、`-allow-country-offsets`（27）、`-allow-shoptab`（28）；golden 與 fixture 只含 id、雜湊、計數與自造字序列（審查者逐檔讀過，採用列數由 tsv 手數核對） |
| 輸入摘要 | 九個原版輸入雜湊、譯文表整體雜湊、補丁雜湊（L1 為空）、建置器版本、政策（模式與三個旗標），固定順序與標頭 `hr-l10n-input-digest v1`；`ExpectedDigest` 與 `Build` 走同一條 `cfg.digest` 路徑 |
| manifest | 欄位 `format`、`code`、`policy`、`files`（依檔名排序八個）、`orig_inputs`（九個）、`table_hash`、`table_format`（`tsv-1`）、`patch_hash`、`builder_version`、`input_digest`、`adopted`；兩格縮排加結尾 LF，沒有時間戳記與主機資訊 |
| `files/` 內容 | 八個檔（七個資料檔與 `CFONT.15`）；identity 包八個檔與原檔逐位元相同；`CFONT.15` 是原版複本 |
| 原子性與重用 | 同層暫存目錄 `.tmp-<名>-<pid>-<隨機>`、`manifest.json` 最後寫、`os.Rename` 到位；改名失敗回到已存在分支重驗，驗證失敗不搬動舊目錄而改用 `-2` 至 `-9`；序號探測六種情形；過期（>1 小時）`.tmp-*` 才清、不碰 `<代碼>-…`；重用要求 manifest 代碼相同 |
| 測試（最終樹，原版在手） | `l10n` 128 通過 1 skip（`TestUpdateFixture`，只在 `HR_L10N_UPDATE_FIXTURE=1` 執行）、`verify` 15、`cmd/hrl10n` 15；全樹（五個套件）252 通過、0 失敗、1 skip；`HR_ORIG=/nonexistent` 231 通過、0 失敗、22 skip；`go vet`、`gofmt -l` 無輸出；`-race` 對 `l10n`、`verify`、`cmd/hrl10n` 通過 |
| 突變 | 第一輪 50 個（`digest.go`、`build.go`、`verify.go`、`budgetadapter.go`、`tabledir.go`、`cmd/hrl10n`），審查修正再加約 30 個，全部被殺死；`verify.go` 第一處大小檢查的突變存活，判為等價（第二處 `n != fe.Size` 回相同原因鍵與相同格式的 Detail，只差「大小不符且檔案不可讀」，要依賴檔案權限） |
| golden 的偵測能力 | 改 `budget` 折行平手規則（`<` 改 `<=`）`TestGolden` 失敗；`Encode` 對一個 fixture 用到的字改碼 `TestGolden` 在 golden 比對處失敗；改字集 tsv 的碼則先在載入時的 x/text 往返自檢失敗（比 golden 更早）；序列化器改一位元組、`Adopt` 採用規則改動（第一輪 M29、M30、M39）golden 失敗 |

審查修正後的行為（`docs/spec/008` 已澄清）：`FindTableDirFor` per-code 尋找（`l10n/<代碼>/` 內要有譯文表檔，空目錄不算；旗標明示的來源不被後面候選取代；`HR_L10N` 與其他來源是一般候選）、`hrl10n verify` 的原版雜湊預設取 `required.tsv`（`-orig` 選填）、SHOPTAB 名稱欄的 `placeholder` 規則、`-dup-ids`、譯文表只讀一次、改名失敗重試（1 次初次加最多 3 次重試，間隔 50 ms）、`wrapRun` 改用 `WrapAndCheck`、`safeName` 白名單、`verify` 套件 import 守護測試。符號連結的包根目前被 `Verify` 與 `Build` 的重用接受（連結後內容仍須通過全部驗證），規格第 3.2 節未寫明，列為已知差異。

## 7. 建置器審查

唯讀審查者對照規格第 3.1 至 3.3 節、第 4 節 L1 列、第 8、9 節審查（全程手推，沒有執行測試）：阻擋 0；應改 A1 至 A6（`.gitattributes` 範圍、`FindTableDir` 的 per-code 語意、`verify` 的原版雜湊來源、SHOPTAB 佔位符、重複群組 id、錯誤文件）；建議 B1 至 B13。實作者的 14 項規格缺案與設計選擇逐項判斷：全部可接受，其中第 3、6、9、10 項需配合規格修訂（已澄清在 `docs/spec/008`，第 13 節第 6 點）。A1 由主代理在提交前補上（`data/.gitattributes` 加 `builder-golden.txt -text`，`testdata/fixture/.gitattributes` 為 `* -text`）；A2 至 A6、B1、B3、B4、B6 至 B10 由實作者處理（第 6 節）；B5 只補註解；B2（前端接線時比對 `Result.Digest` 與先算的摘要）已寫進規格，留待接線；B11（`-out` 預設與 play 的 `dataDir()` 兩份規則）、B12（建置無 `fsync`）、B13（golden 對標點優先的折點不敏感，該規則由 `budget` 自己的測試涵蓋）記為已知差異。審查者另列三項需容器重現的項目（golden 前 8 碼、兩個 golden 突變、M15 等價性），已重現，結果在第 6 節。審查者的邊界自檢：主機用了 `cat`、`find`、`ls` 與管線尾端的 `head`、`cut`，沒有用被禁的工具。

主代理獨立驗證（提交前，容器內）：五個套件全部 `ok`、`go vet` 與 `gofmt -l` 無輸出、`builder-golden.txt` 雜湊與實作者所記相同；`tools/l10n/leakscan.sh` 掃 fork 與本 repo（提交前 2106 個檔）命中仍是第 5 節的 12 項，新增的 80 個檔沒有新命中；補丁 `0030` 以 `git am` 套在 `fabe4f2` 重現同一棵樹（`f0445243…`）。

## 8. 未做與已知差異

- 前端接線（`apps/hr/play`、`apps/hr/runtime` 的 `bindLang` 換成 `verify`，旗標 `-ingame-lang`、`-l10n`，F1 狀態列與 F4 提示、`Options.LangDigest` 與 `SkipLangDigest`、`Session.LangStatus()`）、`hrbot` 對 `LangStatus` 的非零結束、試點譯文與 `-with-candidates` 的畫面樣張、identity 包冷啟動 A/B 與 L0 基準對照、玩家端冷建置（Linux、Wine、macOS 結構）：未做。
- 預算統計收據與 `_vsprintf` 遙測（規格第 9 節）：未做。
- 建置的讀寫量與耗時（規格第 3.2 節預估亞秒級）：測試中一次建置在容器內是毫秒級，沒有正式的計時收據。
- `FindTableDir` 在 AppImage 與 macOS app 實際路徑上的行為：只做純函式與暫存目錄測試。
- 洩漏判準已知漏報：見 `docs/spec/008` 第 3.9 節；`MAIN.EXE`、`OP.EXE`、`END.EXE` 的硬編碼字串不在單位範圍。
- 本文件的數字都來自實作者與審查者在容器內的執行；主代理另外重跑確認了五個套件 `ok`、`go vet` 與 `gofmt -l` 無輸出，以及 `tools/l10n/leakscan.sh` 的基準掃描與全歷史掃描。

## 9. 重跑方法

```
tools/dosgolem.sh go test -count=1 ./apps/hr/l10n/... ./apps/hr/cmd/hrl10n/
tools/l10n/leakscan.sh                 # 工作樹基準掃描
tools/l10n/leakscan.sh --history       # 全歷史
tools/l10n/leakscan.sh --check-allow   # 驗證登記檔
```

重產 golden（建置輸出改變時，`Version()` 隨之改變）：

```
DOSGOLEM_GO_CMD=env tools/dosgolem.sh go HR_L10N_UPDATE_GOLDEN=1 go test -run 'TestGolden$' ./apps/hr/l10n/
```
