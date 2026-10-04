# 030 L1 前端（apps/hr/play）語言包接線的實作收據（docs/spec/008 第八版）

日期：2026-10-04
狀態：收據（實作驗證）。記錄目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱。涵蓋 `apps/hr/play` 的 `planIngame`、`ingameStatus`、`availFor`、`resolveStartup` 擴充、啟動建置接線、F1 狀態列與 F4 提示、新字串與字型子集；試點、玩家端冷建置（Wine、macOS、AppImage 實跑）尚未做。
輸入：fork `workplace/dosgolem` 分支 `hr`，基底 `f03fc83`，本提交 `ac4d9b5`；補丁備份 `engine/patches/0032-apps-hr-play-ingame-wiring-008.patch`，已用 `git am` 套在 `f03fc83` 並確認重現同一棵樹（`fc68ae1b…`）。
來源：實作者報告（`workplace/l1-wire2-report.md`，不進版控）經主代理審閱後搬入；主代理在容器內獨立重跑 `tools/play.sh test-play`、`apps/hr/l10n`、`hrl10n`、`hrbot` 全部 `ok`。這一階段沒有另請審查者，接線屬於規格第 3.2、3.8 節已審查的契約，真值表 23 列逐列由測試斷言。

## 1. 設計與簽章

| 項目 | 內容 |
|---|---|
| `planIngame(c ingameChoice, hasTable, l2, patch bool) ingamePlan` | `C ＝ (代碼, 明示)`；輸出「不建置」「建置 table」「建置 identity」與原因鍵；`l2Supported`、`patchInHand` 在 play 內是常數 `false`（L2 之後同步改，與 `apps/hr/l10n/build.go` 未匯出的 `l2Supported` 是兩份） |
| `availFor(x, findTable, l2, patch) availResult` | `zh-TW`：`FindTableDirFor` 找到；其他語言：找到且 L2 且補丁在手（L2 前恆為 `unsupported-language`）；原因鍵順序 `no-table`、`unsupported-language`、`no-patch` 只在 `unavailReason` 一處定義；`none`、`identity` 呼叫即 panic；每次 F4 按下重新探測，F1 在兩次按下之間沿用上次結果（不在每幀掃檔案系統，測試斷言 200 次面板重畫的查表次數為 0） |
| `ingameStatus(s, e, sf, override, avail) ingameOut` | 規格第 3.8 節四步判定逐字對應；`E` 的種類由 `effectiveFromManifest(mode, adopted, code)`：模式 identity 或採用列數為 0 是 identity 種類；`override` 為真時 toast 一律「由旗標指定」 |
| `resolveStartup` 擴充 | 優先序 `-ingame-lang`、`HR_INGAME_LANG`、`lang`；七個值；不認得的值記一行並往下找，空字串視為沒給；`plan.Override` 與 `plan.Ingame.Explicit` 由同一個變數賦值 |
| 啟動接線 | `ingameBuilder` 介面（`ExpectedDigest`、`Build`）；`prepareIngame` 在 `hrrt.Open` 之前同步執行：`FindTableDirFor` 得 `hasTable`，`planIngame` 決定；不建置時不碰建置器；建置前先算 `ExpectedDigest`，建置後比對 `Result.Digest`，不等記 `build-failed`；成功時 `LangDir ＝ Result.FilesDir()`、`LangDigest ＝ 先算的摘要`，`SkipLangDigest` 不設（`TestMainWiring` 以 AST 斷言）；`finish(LangStatus)` 在 `Open` 之後得 `(E, startFail)` |
| 日誌 | 標準錯誤與 `<資料目錄>/play.log`（標籤 `lang`，每次啟動至少一行，預設路徑也有）；前綴 `ingame:`，內容為 ASCII 記號與雜湊，不含原版或譯文；違規項目逐項一行 |
| 旗標 | `-ingame-lang <代碼|none|identity>`、`-l10n <l10n 根目錄>`（環境變數 `HR_L10N`；搜尋來源順序與 `themeDirCandidates` 一致：旗標、環境變數、AppImage 所在目錄、執行檔旁、macOS Resources、目前目錄、資料目錄） |
| F1 與 F4 | F1「遊戲內文字」一行取代寫死的原版字串（行數預算不變，21 行）；F4 提示是語言自己的名稱接上 `ingameStatus` 的五種字句；ASCII 退回版用語言代碼；新字串五種語言各一份（AI 草稿，與既有字串同樣標示） |
| 字型 | 新字串使 `zh-TW`、`zh-CN`、`ko`、`ja` 的字元表改變，已用 `tools/gen_ui_fonts.sh` 重產（字元數 zh-TW 248、zh-CN 248、ko 243、en 101 沒變、ja 271）；新增 `TestCharsetFilesMatchStringTable` 防止字元表過期 |
| `go.mod` | `golang.org/x/text` 手動搬到直接 require（play 自己沒 import，是經 `replace` 的 dosgolem 模組的 `apps/hr/l10n` import，所以日後 `go mod tidy` 會加回 `// indirect`）；離線可建，`go.sum` 沒變 |

規格模板 (1) 的詞序是「原版（繁體中文）」，原字串是「繁體中文（原版）」，`game.text.orig` 五種語言已對齊模板。

## 2. 測試

| 項目 | 動手前 | 完成後 |
|---|---:|---:|
| `tools/play.sh test-play` 頂層通過 | 132 | 170 |
| skip | 1（`TestGenCharsets`，需 `HR_GEN_CHARSET`） | 1（同一個） |
| 失敗 | 0 | 0 |

新增頂層測試 38 個。`HR_RACE=1` 通過，0 個 `DATA RACE`；`go vet`、`gofmt -l apps/hr/play` 無輸出；`tools/play.sh build`、`build-cross`（windows/amd64）通過；`apps/hr/l10n/...`、`runtime` 語言層測試仍通過。涵蓋（對照規格第 8 節「啟用規則…」那一列）：

- `planIngame`：七個代碼 x 明示 x `hasTable` x `l2` x `patch` 窮舉（前置條件過濾後 96 組）加規格列舉案例；`((zh-TW, 明示), 無表)` 建 identity、`((zh-TW, 非明示), 無表)` 不建置。
- `resolveStartup`：優先序、七個值、不認得的旗標、不認得的旗標加 `HR_INGAME_LANG=ja`、空字串、日誌；明示欄等於 `override` 的斷言跑 1152 組（12 個旗標值 x 是否給 x 12 個環境值 x 4 種 `lang` 來源）。
- 串接：`TestIngameChain` 以真 `resolveStartup`、真 `FindTableDirFor`、假建置器、假 `LangStatus`、真 `ingameStatus` 走 27 個案例。
- `ingameStatus`：真值表 23 列逐列斷言（F1 值與 toast 都斷言）；性質測試在前置條件域內窮舉 926 組（`S` 七個值、`E` 九種、`startFail` 15 種、`override` 兩種、`avail` 四種），函式有定義、F1 值屬四類、toast 屬五種。
- 預設路徑不呼叫建置器（含四個控制組證明偵測器不是恆零）；建置失敗與摘要不符九個案例；`LangDir` 非空時 `LangDigest` 非空。
- 最長組合不被截斷（五種語言 x 五種 toast 字句、五種語言 x 全部 F1 值，兩種量法；ASCII 退回版只含 ASCII）。

## 3. 突變驗證

16 個突變（`planIngame` 規則 2 與 3 的明示判斷對調；`ingameStatus` 第 1 與第 2 步對調；第 2 步誤讀 `avail(none)`、`avail(identity)`；`avail` 原因鍵順序對調；identity 包標「部分翻譯」；`override` 時 toast 不回旗標指定；不認得的旗標值不往下找；`C` 的明示欄與 `override` 不一致；預設路徑呼叫建置器；拿掉建置後的摘要比對；`LangDigest` 不傳（函式層與 `main.go` 兩處）；F1 仍寫死原版字串；F4 不清 `avail`；拿掉採用列數 0 視同 identity；拿掉第 4 步兜底；`staticKey` 少算欄位），全部被至少一個測試殺死；每次還原後 57 個檔以容器內 `sha256sum -c` 逐位元相同。突變 2、3a、3b 整套跑時因 `avail(identity)` 或 `avail(none)` panic 使測試程式中止（panic 本身就是偵測），另以 `HR_TEST_RUN` 篩選的跑法確認真值表與相同關係測試自己能偵測。

## 4. gui 收據（`tools/play.sh gui-ingame`，Xvfb，資料目錄以 `XDG_CONFIG_HOME` 指到 `workplace/out/l1-wire2/home/<階段>`，截圖含原版畫面，只放 `workplace/out`）

| 階段 | 條件 | 結果 |
|---|---|---|
| (a) 預設 | 無 `l10n/` | 日誌 `plan=none reason=no-table`，沒有建置、沒有 `l10n-packs/`；F1「遊戲內文字：原版（繁體中文）」 |
| (b) identity | `-ingame-lang identity` | 前端冷建置 identity 包（`pack-ready … mode=identity adopted=0 digest=7b8a4c0c2f85`），`pack-active`，F1「語言包 identity（原版文字，驗證用）」；第二次啟動 `reused=true` |
| (c) F4 一圈 | 預設，不設 `HR_TEST_FREEZE_UI`（toast 才畫） | ko、ja 的 toast 是「尚無語言包」類字句，F1 是（4）「已選 … 無法使用：沒有譯文表」；之後放入資料目錄的 `l10n/zh-TW/`，F4 回 zh-TW，toast 與 F1 是「下次啟動生效」（真值表列 20；證明 `avail` 在 F4 時重算，資料目錄的 `l10n/` 在搜尋順序內） |
| (d1) 竄改包 | 預先放同名而竄改一個位元組的 identity 包 | 舊目錄的內容雜湊與 inode 啟動前後不變（沒被搬動），前端改建 `-2` 並啟用 |
| (d2) 違規譯文表 | `-ingame-lang zh-TW`，一列 `accepted` 譯文含字集外的字 | 日誌 `violation … 字集外的字 …`、`build-failed`，沒有 `pack-active`；F1「已選 繁體中文，無法使用：建置失敗」；遊戲仍啟動，無 panic |
| (e) table 包 | `-l10n` 指向一列合法 `accepted`（八個取自 `charmap-zh-TW.tsv` 的字），沒有 `-ingame-lang` | 真的 table 模式建置（`adopted=1`）加 `Session.Open` 的 manifest 與摘要驗證通過，F1「語言包 繁體中文（部分翻譯）」；F4 到 zh-CN：F1（4）、toast「暫無語言包」 |
| `gui-lang` 回歸 | 新增子命令 `gui-lang-cmp` 比對動手前複本 | 六張 F1 面板各只有第 11 行（遊戲內文字）不同，其餘 20 行逐像素相同 |

階段 (d2)、(e) 的譯文表需要 `ESPMES#121.0` 原項目的 `src_sha256` 前 16 碼；它是原版衍生值，不進版控：`tools/play.sh` 由 `workplace/out/l1-wire2/src-sha-esp121-0.txt` 讀入（產生方法見 `tools/l10n/srcsha/main.go` 檔頭），主代理接手時把實作者寫死在腳本內的值改成這個做法，並重跑 `gui-ingame`（結果見第 5 節）。

## 5. 主代理的重跑與已知差異

主代理的重跑（容器內）：`tools/play.sh test-play` 全部 `ok`；`tools/dosgolem.sh go test -count=1 ./apps/hr/l10n/... ./apps/hr/cmd/hrl10n/ ./apps/hr/cmd/hrbot/` 全部 `ok`；改成由檔案讀入原項目雜湊之後重跑 `tools/play.sh gui-ingame`，六個階段（(a)、(b)、(c)、(d1)、(d2)、(e)）通過，退出碼 0。

- 預設路徑上介面語言不是 `zh-TW` 且沒有譯文表的玩家，F1 一開就是（4）「已選 X，無法使用：沒有譯文表」，不必先按 F4（規格第 3.8 節真值表列 3 與 18 的輸入）；使用者決定 U4 時一併考慮。
- F1 在兩次 F4 之間沿用上次算好的 `avail`（規格只寫 F4 每次按下時重算）；ASCII 退回版的 F4 提示用語言代碼。
- `Session.Open` 側的 `verify-failed` 沒有走過 gui（(d1) 驗的是建置器重驗並改建 `-2`），只有假 `LangStatus` 與 `docs/re/029` 的 runtime 測試覆蓋。
- 真值表列 5、13 至 16 的 `avail(ja) ＝ 真` 只有注入覆蓋（L1 算不出，`l2Supported` 為假）；`unsupported-language`、`no-patch` 沒有 gui 截圖。
- 建置時間只有秒級（日誌時間戳解析度）、RSS 未量；`gui` 基本版與 `gui-theme` 沒重跑；Windows（Wine）、macOS、AppImage 沒實跑，只做 windows 交叉編譯；`-scale 1`、`-linear`、全螢幕沒驗。
- 日誌同時寫 `<資料目錄>/play.log`：`tools/pkg/verify_appimage.sh` 與 `verify_hd.sh` 只印 `play.log` 的尾端，沒有行數或首行斷言（主代理已讀）。
- 實作者在主機上誤執行一次 `python3 --version`（沒有使用輸出），已記入 `WORKLOG.md`。
