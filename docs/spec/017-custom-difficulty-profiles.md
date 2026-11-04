# 017 自訂難度設定與獨立進度

狀態：CONFORMED。日期：2026-11-04。上層設計：[016](016-difficulty-rule-options.md)，現況與證據：[037](../re/037-difficulty-modes.md)。

## 已確認範圍與停止線

使用者確認八項開關預設全開，飛機與戰車分別提供均衡削弱及運輸為主，預設均衡削弱。之後明確選擇每組完整設定各有進度，可切回相同設定繼續遊玩。

本切片只實作設定值、身分摘要及進度準備 API。它不把尚未 READY 的 016 規則套入 Session，不提供可執行但忽略開關的自訂難度，也不改選擇頁或工具列。正式玩法及 UI 在 016 證據與規則定案後接入。原版及舊 `hard-v1` 的 API 與進度保持原樣。

## 原始碼證據

基準 fork `68638002ed4c2f86bd15a055bbf9a1a463f6543b`，工具 Go 1.26.7／Ebiten 2.9.9。以下位址空間為 Go 原始碼，沒有新增 DOS 掛鉤：

- 已證實：`apps/hr/runtime/difficulty_profile.go` 的 `prepareDifficulty` 已完整驗證 RequiredFiles、排除來源 GAMEFILE、投影必要檔案並建立五行 FNAME；來源 FNAME 由有效 Scratch 索引覆蓋。`SavePath` 仍為原版基底或基底加 `-hard`。
- 已證實：同檔 `realTarget` 解析既存祖先的符號連結；`insidePath` 判斷重疊；`regularBytes` 拒絕非一般檔；`checkProfileIndex` 核對五行索引與欄位長度。
- 已證實：`session.go` 的 `Open` 在建 CPU 前呼叫 `prepareDifficulty`，隨後綁語言、呼叫 `initDifficulty`，再設定 DOS Scratch。單純準備 profile 不會執行 CPU。舊規則零值保留原版。
- 原版進度污染邊界與 31,839-byte 存檔長度沿用 014；來源 `MAIN.EXE` SHA-256 為 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。
- 實作測試補證：`required.tsv` 包含 158-byte `FNAME.DAT`，SHA-256 `79a1e43ef303b9782cd0c306f8b12cdb0b4bc773f9bfa0c2509e426a004ea1b3`。RequiredFiles 是完整輸入驗證名單，不能等同可共用的資料投影名單。現行舊 hard 藉有效 Scratch 索引覆蓋來源 FNAME；本切片另要求共用投影完全不含進度索引，不修改舊 hard。

## 設定與正規表示

新增 `ChallengeRules`，JSON 固定欄位及順序如下：

| 欄位 | 型別與值 |
|---|---|
| `schema` | 整數 1。 |
| `revision` | 固定字串 `challenge-v1`，識別日後定稿的整套規則與數值。數值改版必須新 revision，不讓舊進度無聲換規則。 |
| `debt_x5` | 布林。 |
| `half_rewards` | 布林。 |
| `staged_story` | 布林。 |
| `late_aircraft_shops` | 布林。 |
| `aircraft` | `original`、`balanced`、`transport`。`original` 代表母開關關閉。 |
| `tank` | 同上，可與飛機不同。 |
| `western_guards` | 布林。 |
| `fortress_defenses` | 布林。 |

`DefaultChallengeRules()` 明確填入六項 true 及兩項 balanced，不把零值當預設。零值結構因 schema／revision 不符而拒絕。全關為六項 false、兩項 original，仍是合法自訂組合，不與正式原版 profile 混用。

嚴格解碼拒絕缺欄位、重複欄位、未知欄位、非預期型別、null、大小寫不同的鍵、尾隨第二份 JSON、未知 schema／revision／enum。Unicode escape 解碼後相同的鍵仍屬重複。欄位順序與空白不影響語意；重新序列化依固定結構順序、無縮排、無尾隨換行。身分為此正規 JSON 的完整 SHA-256 小寫 64 hex。固定 revision 不接受任意使用者自行命名。

不把介面語言、主題或模式顯示名稱加入摘要。UI 日後暫存「關閉前的強度」也不進摘要；實際關閉即 original，不產生效果相同但身分不同的兩份進度。

## 進度與共用資料

以傳入的原版存檔基底 `base` 計算自訂根 `filepath.Clean(base)+"-custom"`。空基底拒絕。範例：原版 `high_reward/saves`、舊高難度 `high_reward/saves-hard`；自訂根 `high_reward/saves-custom`。

| 路徑，相對自訂根 | 用途 |
|---|---|
| `root.json` | 固定根標記，含模式 `custom-root-v1` 與原版來源 SHA-256。 |
| `data-v1/` | 唯一共用的未修改資料投影。由 RequiredFiles 排除 `FNAME.DAT`、`FNAME.DA_` 及 `GAMEFILE.*` 後取得允許清單，逐檔完整雜湊核對。 |
| `<完整設定摘要>/difficulty.json` | 模式 `custom-v1`、來源 SHA-256、設定摘要及完整正規設定。 |
| `<完整設定摘要>/fname.dat` | 同 014 的五行合法空索引，已有進度則保留原索引。 |
| `<完整設定摘要>/gamefile.000` 至 `.004` | 五槽原版格式存檔。大小寫政策沿用 014，重複大小寫拒絕。 |

新增 `PrepareChallengeProfile(root, base, rules)`，回傳有效設定、完整摘要、DataDir 與 SaveDir。它沒有 CPU、遊戲 Session、語言綁定或自動存檔副作用。API 存在不代表八項玩法已完成。

1. 先驗規則、原版 RequiredFiles 與來源雜湊；原始來源只讀。
2. 解析原版根、原版存檔基底、舊 hard 目錄與自訂根的實際路徑。自訂根不能與前三者互相包含；根、資料投影、profile 及其中檔案均不得透過符號連結指向其他位置。
3. 已有未標記內容、來源／設定標記不符、未知項目、非一般檔或索引／存檔長度不符，一律保留並回錯。未知摘要目錄不自動匯入，也不搬移、清空或刪除舊存檔。
4. 自訂根首次建立後寫固定標記。若根已存在且沒有標記，只接受完全空白的根；有任何內容就拒絕。根內容只接受 `root.json`、`data-v1` 及小寫 64 hex 的 profile 目錄。
5. 完整輸入仍通過全部 RequiredFiles 驗證，包含來源 FNAME；可投影清單則從中排除 `FNAME.DAT`、`FNAME.DA_` 與 `GAMEFILE.*`，比較時不分大小寫。共用投影只接受此過濾後名單的一般檔，逐檔驗原始與目標 SHA-256。缺檔可由已驗來源補足；現有檔損壞、額外 FNAME／GAMEFILE／未知檔一律回錯，不覆寫。新增檔先寫同目錄暫存檔，再以不覆蓋的發布方式提供，不使用硬連結回原版。
6. 新 profile 先在自訂根下建立私有暫存目錄，寫完標記與五行索引後才 rename 到完整摘要路徑。已存在的目標只能重新驗證，不覆蓋。失敗僅清理本次明確建立的暫存目錄。
7. 既有 profile 核對完整設定與摘要，允許五槽、單一大小寫 FNAME 及標記，拒絕其他內容。存檔必須 31,839 bytes，未存槽可缺席。回傳投影根作日後 DOS root，profile 作 Scratch，避免從合法原版資料夾回退讀到其他進度。

不跨 profile 複製 GAMEFILE、不自動繼承債務或部隊。不為每種組合各複製一套遊戲資產；只建立實際使用過的組合。多行程同時準備若遇不完整狀態可以回錯，不以覆寫資料化解競爭；不能損壞已有效的 profile。

檔案及目錄發布使用作業系統的不覆寫操作：Linux `Renameat2(RENAME_NOREPLACE)`、macOS `RenamexNp(RENAME_EXCL)`、Windows `MoveFileEx` 不帶 replace 旗標。入口為 runtime 的 `challenge_publish_<平台>.go`，沿用鎖定的 x/sys v0.36.0。作業系統或檔案系統不支援時回錯，不退回可能替換既存空目錄的 `os.Rename`。本切片支援專案既定三平台，不擴張其他平台。

## 測試與完成範圍

- 設定：預設全開、兩種載具獨立、全關與零值區分、JSON 欄位重排仍同摘要、每個有效差異產生不同摘要、語言與 theme 無關。缺欄位／重複欄位／錯型別／未知欄位／版本及尾隨內容均拒絕。
- 檔案：兩組進度不同、切回同組重用同目錄、現有 FNAME／GAMEFILE 雜湊不變、共用 DataDir 且只一份投影、原版及舊 hard 不變。實際原版缺失時明確 skip，收據列出有無 skip。
- 失敗：未標記資料、標記或摘要不符、短存檔、大小寫重複、污染投影、來源或祖先別名、profile／資料 symlink，全部回錯且保留原檔。
- 現行相容：014 難度與進度隔離回歸，原版及舊 hard 的 `SavePath`、CLI 及 Session 不變。

本切片不宣稱正常 UI、新玩法或整體平衡驗收完成。後續需由 016 的設定頁 → 遊戲結果 → 存檔 → 重開驗證補足玩家垂直鏈，才可交付新自訂難度。禁止在全部規則尚未接上時，用全開外觀冒充可用的新難度。

## READY 審查

唯讀審查 `workplace/out/options-profile-spec-review.md` 無阻擋，主代理已複核。補強 null／重複鍵與大小寫、初次發布失敗、同設定競爭、懸空與祖先 symlink、五槽大小寫重複及舊資料保留測試。實作不得直接以會覆蓋既有目標的 `profileWrite` 假定已滿足禁止覆寫契約。READY 僅限本切片，不提升 016。

初次實作測試因 RequiredFiles 含 FNAME 而明確拒絕，沒有改動原版或玩家進度。依新增證據退回 DRAFT，將完整輸入驗證與可投影清單分開；複核解除後再修正實作並重跑。

第二輪唯讀複核 `workplace/out/options-profile-spec-review-r2.md` 無阻擋，直接核對全部 77 個必要輸入的大小及 SHA-256，包含來源 FNAME。共用投影明確為排除 FNAME 後的 76 檔，主代理讀取並恢復 READY。實作的允許清單與複製迴圈必須使用同一過濾清單，完整輸入驗證不變。

## 實作驗收

新增 `challenge_rules.go`、`challenge_profile.go`、四平台發布 helper 及 `challenge_test.go`。`options-profile-tests-r3.log` 全部通過，9.458 秒，沒有 skip；包含 576 組設定、嚴格 JSON、實際 77／76 清單、逐檔投影雜湊、進度切換重用、污染與符號連結拒絕、發布失敗保留、競爭及舊 hard 回歸。競態檢查通過，1.576 秒，`options-profile-race.log`；`go vet` 通過。三平台正式 API 的 Windows amd64、Darwin amd64／arm64 編譯均成功，日誌為 `options-profile-build-*.log`。

唯讀實作審查 `workplace/out/options-profile-implementation-review.md` 無阻擋，主代理已讀取。審查另驗 Linux 既有檔案、空目錄、有效目錄及 symlink 均不覆寫。最初跨平台測試編譯被既有 Linux 專用 `bench_test.go` 阻擋，改為編譯正式 API，未修改該測試或產品行為。後續獨立攻城診斷與本切片驗收分開，未將其失敗當成 API 缺陷。

CONFORMED 僅涵蓋本文件的設定身分與進度準備 API。正常 UI、新八項玩法及整體平衡仍由 016 管理；Windows／macOS 沒有原生操作驗收。
