# 037 原版與高難度模式調查

日期：2026-11-03。契約：[014 難度選擇與獨立進度](../spec/014-difficulty-modes.md)。

## 目前狀態

本表是本項功能的唯一目前狀態表。較早的結案紀錄不構成本次功能已完成的證據。

| 項目 | 目前結果 |
|---|---|
| 程式來源 | 根基準 `d322103`，原有未提交文件修改保留；現行 fork `68638002ed4c2f86bd15a055bbf9a1a463f6543b`，工作樹乾淨。難度規則備份 [0047](../../engine/patches/0047-difficulty-modes.patch)，工具列備份 [0048](../../engine/patches/0048-toolbar-difficulty-switch.patch)。 |
| 正式交付 | 本機現行 `v.1.0.5-20261014`，本次尚未重建或修改正式包。 |
| 使用者需求 | 遊戲開始前選原版／高難度，進度分開。高難度減半劇情獎金、加強劇情敵人、移除初始區域北方的飛機商店。 |
| 已授權 | 必要時修改高難度專用資料副本，兩種模式分別啟動。 |
| 已確認倍率 | 使用者選擇債務 ×5，劇情獎金除以 2。 |
| 已確認敵軍倍率 | 劇情敵軍基本戰鬥能力 ×1.5，兵種、數量與裝備不變。建立端及消費端已核對。 |
| 技術查證 | 債務、13 組劇情給錢、9 個劇情戰鬥 caller、敵方生命與攻防、北方 3 間飛機商店已定位；014 狀態 CONFORMED。 |
| 新功能驗證 | 規則、進度隔離、前端、Linux 選單／存讀檔、正常舞孃預付款及護送戰鬥通過；中斷重入已修正。完成範圍與限制見[正常護送戰鬥驗證完成](#正常護送戰鬥驗證完成)。 |
| 本機影片 | `v.1.0.6-20261103` 難度模式展示片，60 秒 1080p30，真實選擇／新遊戲／城市編成／F2 與原版配樂。此版號識別本機錄影版，正式遊戲包仍為上述 1.0.5。 |
| 工具列延伸 | 使用者選擇立即切換。契約 [015](../spec/015-toolbar-difficulty-switch.md) CONFORMED；取消、錯誤復原、雙向切換、各自讀檔與正常新遊戲通過。本機啟動入口 `workplace/out/run-difficulty-preview.sh` 已指向新版。 |

## 輸入與位址基準

| 輸入 | SHA-256 |
|---|---|
| `workplace/orig/MAIN.EXE`，539424 bytes | `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e` |
| 既有 `workplace/ida/run/MAIN.EXE.i64` | `209f4ab5838978f5120c06f2cdc678c5b726282ca10f4fa07cfdb5e028354df2` |
| 函式索引 `workplace/ida/out/names.tsv` | `da2a0b945af693ce6ff30a453dd468ccf7956ed06a346ff0a69dee212664eb83` |

原版及正式資料庫保持唯讀，查詢使用一次性資料庫副本。IDA 工具版本先以最小輸出檔驗證；未通過前不採其語意結論。後續記錄分別標示 IDA linear address、原始 selector:offset、執行期段位址或檔案位移，不混用。

## 變更前的接線基準

| 結論 | 等級 | 出處 |
|---|---|---|
| 前端目前在 `main()` 直接尋找原版、準備語言包並開啟 Session，沒有難度選擇頁。 | 已證實，限目前程式 | `apps/hr/play/main.go:75`、`:138`、`:169`，路徑相對 fork。 |
| 目前預設存檔目錄為使用者資料目錄下的 `high_reward/saves`。 | 已證實，限目前程式 | `apps/hr/play/main.go:114`；`apps/hr/play/paths.go`。 |
| DOS 讀檔依序查暫存層、語言層與原版根目錄。單獨換 SaveDir，仍可能讀到原版根目錄附帶的舊存檔。 | 已證實，限目前程式 | `internal/dos/files.go:54` 至 `:74`。 |
| 原版必要資料依檔名與大小檢查，可要求 SHA-256。高難度資料不能靠取消驗證混入原版模式。 | 已證實，限目前程式 | `apps/hr/runtime/required.go`。 |

## 調查範圍與停止線

- 債務：原始位元組及正常冷啟動已確認初值 1000 萬；高難度改為 5000 萬，還款額度不變。008 的歷史數字不作本項基數。
- 劇情獎金：以 13 組固定 caller 界定，保留一般委託、交易、退款、賭金與金庫提領。
- 劇情敵軍：依建立端與實際消費端修改戰鬥記錄，不使用 002 的人物上限候選表。
- 飛機商店：原始地圖及國家城鎮表已確認北方三間，第三方攻略只作線索。
- 進度隔離：涵蓋五槽、FNAME、來源回退與語言層，正式存檔內容仍為原版 31,839 bytes。

所有未解出的欄位與語意維持未知。停止線為足以完成本次難度功能及其正常玩家路徑，不擴大成整支 MAIN.EXE 的反組譯。

## 2026-11-03 接線證據

### 工具與收據

- IDA 9.4／1968 函式的最小探針通過，資料庫輸入 SHA-256 與原版相同。收據 `workplace/out/difficulty-ida-run/probe.json`，使用現有 `ida-pro-9.4-idapython:py312-v1`、UID 1000。
- Linux 工具鏈由既有 `tools/docker/Dockerfile.hr-build-r1` 及已核對的三檔 context 恢復，沿用 `hr-go-ebiten:1.26.7-2.9.9-r1`。Go 1.26.7、Ebiten 2.9.9、固定 FFmpeg 與模組 checksum 通過，沒有換用別的專案版本。
- IDA 匯出均由正式資料庫的唯讀來源重製一次性副本，沒有改名或保存語意註記。`census.json`、`targets.json`、`followup.json`、`enemy-save.json`、`enemy-construction.json`、`story-battles.json`、`story-enemy-data.json`、`enemy-battle-records.json` 位於上述研究輸出目錄。它們是本機原始證據，不加入 Git。

### 債務與金錢

| 項目 | 原始定位與消費端 | 等級 |
|---|---|---|
| 新遊戲債務 10,000,000 | `MAIN.EXE` 檔案位移 `0x3B334`，`80 96 98 00`；IDA `4073:6204`；原版畫面使用者 `1F33:0FD1`。執行期線性 `0x37A34`。 | 已證實，固定輸入及本次正常冷啟動 |
| 償還額度 5000 | 檔案位移 `0x3B330`；IDA `4073:6200`；畫面消費端 `1F33:101C`。 | 已證實，固定輸入及本次正常冷啟動 |
| 現金 8000 | 檔案位移 `0x3B328`；IDA `4073:61F8`；畫面消費端 `1F33:107E`。 | 已證實，固定輸入及本次正常冷啟動 |
| 共用加錢 | IDA `298A:0005`，`add es:word_46928,bx`／`adc es:word_4692A,dx`，並限制 0 至 99,999,999。21 個直接 caller，不能整個 helper 無條件除 2。 | 已證實，靜態資料流 |
| 獎金通知 | IDA `298A:02AC`，actor 加上 32-bit 金額轉交 `298A:0187`。部分劇情分支先通知再加錢，兩處須一致處理。 | 已證實，靜態呼叫順序 |

債務原型來源 `workplace/out/difficulty_debt_probe.go`。使用目前 fork 原始碼與鎖版工具鏈建置，第一次指令前僅在 hard 探針將初始債務改為五倍，再用正常標題選單滑鼠操作進新遊戲。兩側皆為 82,500,000 步；原版顯示 10,000,000，高難度顯示 50,000,000，償還額度 5000 及現金 8000 相同。PNG、JSON 在 `workplace/out/difficulty-normal-probe/debt-{original,hard}.*`。這證明初值及畫面接線，不證明存讀檔或完整高難度功能完成。

劇情獎金以 caller 及腳本事件界定。原版文字顯示 `6EE9:2243` 是賭金收入，`6EE9:0D1A` 是退錢，不能因它們也呼叫相同加錢 helper 就當成通關獎金。其餘固定獎金仍須與對應事件逐項登錄。原文及詳情留本機，不在公開文件轉載。

### 劇情敵方記錄

| 接線 | 原始證據 | 等級 |
|---|---|---|
| 劇情挑戰入口 | IDA `2404:05AA`，按第二個參數乘 `0x51`，從 `5ACF:0008` 起複製一筆 81-byte 對手模板到局部堆疊，再在 `2404:05FD` 呼叫 `62A5:00A2`，後者直接跳到 `7718:0000`。 | 已證實，靜態資料流 |
| 特殊事件與一般戰鬥須區分 | 上述橋接函式有 10 個直接 caller，其中一個在催繳事件段 `669D`，其餘在劇情段 `6EE9`／`749C`。不以共用戰鬥入口本身判定所有遭遇都是劇情。 | 已證實，直接 caller；事件範圍待最終規格列舉 |
| 敵我分開建立 | 戰鬥主函式在 `7718:014E` 建玩家側，`7718:0159` 建敵方；敵方建立函式 `7718:1555`。 | 已證實，靜態呼叫順序 |
| 敵方戰鬥記錄 | DS 為原始 `5BF4` 對應的常駐資料段；敵方表起點為 DS:`0591`，步長 `0x23`，至多 11 筆。有效筆數寫在 DS:`0008`。玩家表在 DS:`0410`，不能一併修改。 | 已證實，建立端 |
| 生命與攻防欄位 | 敵方建立端寫 DS:`059A`、`059C`、`05A0`、`05A2` 加上索引乘 `0x23`。分別對應現生命、最大生命、基本攻擊、基本防禦；後三者使用原版能力 helper 的 case 1／2／3，與玩家側相同欄位的來源對照。 | 已證實的靜態資料流；消費端補證及正常護送戰鬥見下節 |

實作在敵方記錄建立完成後、實際戰鬥使用前，只對指定劇情 caller 的有效敵方記錄施加一次倍率。共用角色上限表、玩家側記錄、裝備及經驗欄位保留原值。

### 商店與存檔

- 已證實商店表為 99 筆、每筆 200 bytes、8 格各 25 bytes。`2B09:0009` 載入單筆；`24D0:0038` 與 `24D0:0207` 均將格內 `+0x18` 等於 `0xFF` 的項目略過。來源與先前 024 的格式收據相符。
- 原版 20 個商店格的類型為 `0x38` 至 `0x3F`，名稱及商品類別對應航空機。北方三間的位置見下節。原版 GMAP 圖確認 Cellafe 位於初始 Zelerd 北方，Phasys 在東側；第三方攻略的便宜航空機線索不屬本次北方範圍。
- 已證實 `7D37:00AC` 固定讀五行 FNAME，每行格式 `%c %s %s %s`，未檢查各次 fscanf 的成功數。不能用空檔案充作全新存檔索引。`7D37:036F` 按選中的槽位開啟 `GAMEFILE.00%d`。
- 已證實原版存檔將 IDA `4073:0008` 起的 31,839 bytes 寫出／讀回，包含債務欄位。實作只改新遊戲初值，載入高難度存檔不再乘五。隔離與存讀檔收據見下節。

### 區域與欄位消費端補證

- 已證實：`2404:08F1` 將城鎮編號與 IDA `4073:28BC` 起的國家記錄比較，每筆 73 bytes、`+0x39` 起 16 個有號城鎮編號。初始 region 4 包含城鎮 44 至 56；北方 region 7 包含 57 至 64 及 22。原始 GMAP 圖確認此區在初始區域北方，東方 region 5 不屬本次刪除範圍。收據 `town-map.json`。
- 已證實：北方航空商店只有 town 57／slot 4、60／slot 6、63／slot 6，SHOPTAB.TBL 類型 byte 位移 `0x2D04`、`0x2F8E`、`0x31E6`，原值 `38/3B/3A`。以 `FF` 停用沿用原版城市選單過濾，不移除城市、道路或其他商店。
- 已證實，靜態消費端：戰鬥 `7718:0BC7` 讀記錄 `+0x11` 基本防禦並合併裝備防禦；`7718:0BEE` 讀 `+0x0F` 基本攻擊參與傷害乘算；`7718:0882` 讀敵方 DS:`059A` 判定存活；敵軍健康列在 `7718:3549/355F` 讀 DS:`059C/059A` 作為最大及現生命。收據 `battle-stat-consumers.json`，欄位由強推論提升為已證實的靜態資料流，正常玩家戰鬥正例見[正常護送戰鬥驗證完成](#正常護送戰鬥驗證完成)。
- 劇情給錢的 13 組及劇情戰鬥的 9 個 caller 列在 014。`64E8:00E3` 是城市金庫提領，不納入過劇情獎金。退款與賭金保留原額。判定依函式控制流與原版事件文字，不從共用 helper 名稱推論。
- `FNAME.DA_` 同樣含舊進度，不能當作空白索引；以五行合法佔位列初始化新 profile，再由原版正常存檔取代。程式的語言包驗證允許清單另須確認不含進度檔。

## 實作與目前驗證

- 唯讀審查：`workplace/out/difficulty-spec-review.md`。索引時間字串改為 8 bytes，載入時檢查日期／時間／地名的 byte 上限；高難度另對已驗語言包加上八檔允許清單，拒絕 manifest 自列的 FNAME 與 GAMEFILE。
- 執行層：fork 的 `apps/hr/runtime/difficulty.go`、`difficulty_profile.go`。原版零值不開啟規則；高難度使用獨立目錄、標記及必要檔案投影。來源與投影資料的雜湊不變，三商店只在載入後 buffer 停用。
- 前端：fork 的 `apps/hr/play/difficulty.go`。選定前不建立 Session；取消不建立進度；啟動失敗保持原模式並顯示錯誤。兩種模式另有明確旗標，F2 顯示主題與難度獨立。
- 字型：五份 Noto 子集已更新並通過字形墨跡及卡片邊界測試。重生入口 [tools/subset_ui_fonts.py](../../tools/subset_ui_fonts.py)，先由前端 `TestGenCharsets` 產生字元表，再以 fontTools 4.66.1 及固定 Noto TTC 執行。來源及 wheel SHA-256 記於 fork 的 `apps/hr/play/fonts/SOURCE.txt`。
- 執行層測試：`workplace/out/difficulty-runtime-tests.log`，含 13 組通知／入帳、退款及賭金、9 個劇情 caller 與催繳反例、四欄位以外記憶體不變、一次倍率、溢位原子拒絕、99 城鎮只有三個 buffer byte 不同、索引格式、短存檔保留、目錄別名、語言層進度污染及原版冷啟動收據 A。
- 前端全量測試與 Linux 建置通過，Windows amd64 編譯通過；`workplace/out/difficulty-frontend-tests.log`。Windows／macOS 原生操作尚未驗證。
- 正常存檔：`difficulty-saved-{original,hard}.*`；新行程讀回後的完整畫面為 `difficulty-load-finished-{original,hard}-wait.png`。存檔長度均為 31,839，債務分別為 1000 萬／5000 萬，現金均 8000。兩包只有存檔位移 `0x61FD` 至 `0x61FF` 三個 byte 不同，全部落在債務欄位。完整 SHA-256 與 diff 在 `workplace/out/difficulty-save-diff.json`。
- 索引使用小寫 `fname.dat`，配合原版寫入名稱，避免在 Linux 產生大小寫重複檔。五行 EMPTY 索引的存檔視窗已目視確認；未存槽沒有任何來源 GAMEFILE 可回退。
- Linux 實際選單：`workplace/out/difficulty-gui/chooser.png`、`hard-title.png`、`original-title.png`。滑鼠選原版、鍵盤選高難度及正常退出通過；Esc 取消沒有建立進度。首次過短的合成 Ctrl+Q 未被讀到，改為有明確按住時間後乾淨重跑通過，屬驗證輸入節奏。

正常劇情敵軍抽測已完成，014 已提升為 CONFORMED，範圍見[正常護送戰鬥驗證完成](#正常護送戰鬥驗證完成)。測試起點包括正常新遊戲，以及本機未修改的原版 GAMEFILE 樣本；樣本只複製到本輪測試目錄，不匯入正式玩家進度。使用者本機個人 `high_reward/saves` 已唯讀核對為空，沒有寫入。所有 state、原始樣本、截圖及編譯輸出均留在 `workplace/out/`，不加入 Git。

### 正常劇情獎金及中斷回歸

- 未修改的原版 `GAMEFILE.004` 只複製到本機測試 profile；透過正常旅行、酒店對話及配屬接下舞孃護送。此測試原本載入的債務值保留，不能用它當作新遊戲五倍債務的證據。領款流程在 `difficulty-dancer-accepted.*`，兩個掛點均記錄 10,000 → 5,000。
- 同狀態對照使用正常流程得到的 `difficulty-grant-ab-input.state`，SHA-256 `9b30ea7605ca46500816207d5d2b7a0deb884677be0fbfc74a23a60e0448db7e`。兩側還原相同 CPU、DOS 時鐘及亂數狀態，再送相同滑鼠輸入。現金起點均 2,026,194，原版為 2,036,194，高難度為 2,031,194。收據 `difficulty-grant-ab-{original,hard}.json`。此結果只覆蓋舞孃預付款，其他 12 組以接線測試與靜態證據界定。
- 唯讀實作審查 `workplace/out/difficulty-implementation-review.md` 找到並重現 IRQ 重入：`Machine.Step` 在執行指令前先派送 IRQ，IRET 回掛點可能再次減半或再次停用商店。修正以 CS／IP／SS／SP／BP 保留本次變更，經實際 `Insn` 及 SP 變化確認指令消耗後才清除。
- `TestHardHooksSurviveIRQBeforeInstruction` 對通知、入帳與商店各強制兩次 IRQ，且第二次重用相同堆疊位置。六例均精確套用一次，後續呼叫不被舊標記略過。收據 `difficulty-irq-regression-tests.log`；重新執行難度測試與原版冷啟動 A 通過，見 `difficulty-runtime-tests.log`。
- 既有七個錄影／驗證入口已調整。當前原始碼的 GUI 驗證明選 `-difficulty original`；接受既有執行檔的工具先查 `-h`，有新旗標才加入，以保留舊正式包相容性。五份 Python 工具的新舊參數分支與兩份 shell 語法均已核對。

### 本機開發版交接

- 014 初版 Linux 執行檔為 `workplace/out/hr-play-difficulty`，保留作原收據來源。現行啟動腳本 `workplace/out/run-difficulty-preview.sh` 已指向下節工具列預覽。不帶難度參數會先選模式；附加 `-difficulty original` 或 `-difficulty hard` 可直接啟動。腳本只提供本機試玩，不是正式交付包。
- 執行檔從上述乾淨 fork 提交重建，`difficulty-build-info.txt` 記錄 Go 1.26.7 與 `vcs.modified=false`。最終視窗收據 `difficulty-final-gui/receipt.json` 綁定實際執行檔 SHA-256，滑鼠選原版、鍵盤選高難度、兩側標題及正常退出均通過。首次腳本在程式已退出後向舊視窗送 keyup，修正為全域釋放按鍵後乾淨重跑，屬驗證腳本問題。
- 正常護送需要在 town 42 停留。IDA `2404:08BD` 的判定同時要求部隊 `+0x31` 為該城鎮、`+0x26` 為 2，證據 `difficulty-ida-run/arrival-guard.json`。已透過正常攻城及守軍戰進入此狀態，實際劇情正例見下節。沿途一般戰鬥、人工 BP 框架或能力測試不作替代收據。
- 實作審查提出的 overlay 返回表示疑慮已由本次實際 BP 鏈與唯讀複核覆蓋。其他 overlay 狀態保留證據限制，不擴大為全量驗收要求。
- 原版資料、個人進度及 `v.1.0.5-20261014` 正式包未修改。收尾完整檔案與擁有權核對見 `workplace/out/difficulty-final-audit.json`。本輪只在 fork 本機提交，沒有推送或發布。

### 正常護送戰鬥驗證完成

- 路由重新核對「READY／CONFORMED 閘門」，沿用規格閘門及既有驗證契約。正式程式仍為上述乾淨 fork 提交，本輪沒有修改玩法程式。
- 已證實，限固定輸入及本次正常路徑：未修改樣本的 town 42 類型為 2。IDA `1B8C:110E` 的抵達處理不會直接將這種城鎮設為停留；正常「占領」會先扣城防，再由 `19BC:15E4` 處理守軍。城防依序由 98 降至 89、73、43、24、0，戰勝守軍後城鎮類型變為 1，部隊 `+0x26=2`、`+0x31=42`。證據為 `arrival-flow.json`、`entry-permission.json`、`world-battle-dispatch.json`、`siege-skill.json`、`siege-damage.json` 及 `escort-battle-trigger.json`，均在 `workplace/out/difficulty-ida-run/`。位址是原始 IDA selector:offset，工具及輸入沿用上方基準。沒有改部隊、座標、城防、金錢或劇情旗標跳關。
- 正常輸入到達護送劇情 `6EE9:034D`，敵軍六名。收據 `workplace/out/difficulty-guard-continue-r3.json`、`difficulty-guard-continue-r3-story-battle.png`。捕捉工具只增加本機 state 輸出，沒有更改規則或原版狀態；同狀態比較另用未插入捕捉的正式執行層。
- 同狀態檢查點 `difficulty-story-6EE9-034D.state`，SHA-256 `7e410140eddba464c00d8eccf7eb40253136af7077a9d743f97f13e4f05359dd`。開始指令數 9,703,960,657，兩側還原相同 CPU、DOS 時鐘及記憶體後，各執行一步。比較點位於原版敵軍建表後，這一步不呼叫 RND；不重擲，也不比較整段戰果骰序。

| 敵軍 | 原版：現生命／最大生命／基本攻擊／基本防禦 | 高難度 | 結果 |
|---|---|---|---|
| 前五名，各一筆 | 15／15／9／9 | 22／22／13／13 | 四欄均為 ×1.5 向下取整 |
| 第六名 | 45／45／27／27 | 67／67／40／40 | 四欄均為 ×1.5 向下取整 |

- 已證實，限該比較：四欄以外的整份記憶體相同，包含玩家側、敵軍兵種、數量與裝備。收據 `workplace/out/difficulty-battle-ab.json`；兩側生命顯示分別在 `difficulty-battle-ab-original.png`、`difficulty-battle-ab-hard.png`。重跑入口是本機 `hrdifficulty-battle-ab`，來源 `difficulty-battle-ab.go` 及其 Go overlay 清單；在既有 `hr-go-ebiten:1.26.7-2.9.9-r1` 容器內，以唯讀原版 `/orig`、fork `/src` 及可寫 `/out` 執行，不在主機跑程式。
- 已證實，該掛點執行期為 `6276:015C`；主 BP=`7F72` 返回常駐 `1514:0602`，parent BP=`7FD8` 返回 `5CC3:034D`，header stub=`5382` 且反向指向 `5CC3`，因此可還原原始 `6EE9:034D`。更外層 BP=`7FE6` 出現 `5362:0000` 的 stub 返回形式；這不在本掛鉤讀取的 parent 層。它由 manager 卸載改寫而成仍為強推論，其他狀態會使所需 parent 漏辨識仍是假說。唯讀複核 `workplace/out/difficulty-overlay-review-r2.md` 無阻擋；不外推所有 overlay 狀態已驗。
- 加強後戰鬥正常獲勝，護送尾款通知 `6EE9:0418` 及入帳 `6EE9:0422` 均為 10,000 → 5,000。戰後現金 1,904,411 → 1,909,411，正常返回地圖。最終收據及畫面為 `difficulty-escort-finished-r4.json`、`difficulty-escort-finished-r4-finish.png`，指令數 9,912,269,953。本機重播清單 `difficulty-battle-path-replay.json` 保存本輪輸入批次及檔案雜湊。
- 014 的正常戰鬥閘門已補足，升為 CONFORMED。其餘八個劇情入口仍以靜態證據與接線測試覆蓋，未宣稱完整劇情通關或所有 overlay 狀態一致；Windows／macOS 原生操作仍未驗。現有本機預覽可試玩，正式包與公開 Release 未重建。

### 本機難度模式影片

使用者要求重新錄製影片。成品為 [HighReward-v.1.0.6-20261103-promo.mp4](../../dist-all/v.1.0.6-20261103/promo/HighReward-v.1.0.6-20261103-promo.mp4)，4,801,605 bytes，SHA-256 `d6a297785f085e9458669cec2e470e9ccd0dd908770b52f55e5da07dcf9dddbd`。60 秒、1920×1080、30fps、1800 幀，AAC 48kHz 雙聲道。52 秒來自實際視窗錄影，前後各 4 秒字卡。

影片由新啟動的前端經正常鍵盤與滑鼠操作，先選高難度，再走新遊戲、城市部隊編成及兩次 F2。原版比較也由同版前端正常新遊戲取得。畫面分別顯示債務 10,000,000／50,000,000，償還額度 5000、現金 8000 相同；右下角數字直接從各自錄影裁切放大。這支影片展示難度入口及玩法操作，不以它取代上節的劇情戰鬥收據。沒有載入快照、注入部隊或金錢。

專用錄影程式由乾淨 fork `d7aae8e52b75a99c438fc308374e75d9a245f80c` 建立，只以連結旗標設定 `main.version=v.1.0.6-20261103`，Go 1.26.7、`vcs.modified=false`。執行檔為 `workplace/out/promo-v106-bin/hr-play`，SHA-256 `a3b863eb559e2606d5076edf04971545cdca9b5a5aa41b94e335c5e16a1f4213`。本版為本機錄影版，片尾也明示開發版；沒有建立新版遊戲封包、tag 或 Release。

| 入口 | 用法及證據 |
|---|---|
| [錄影工具](../../tools/capture_promo.sh) | `HR_CAPTURE_BINARY_DIR` 指向錄影程式目錄。高難度設 `HR_CAPTURE_DIFFICULTY=choose` 並用[高難度分鏡](../../tools/promo-difficulty-hard.json)；原版設 `original` 並用[原版分鏡](../../tools/promo-difficulty-original.json)。`HR_CAPTURE_CONTROL_FILE` 指定分鏡，工作名必須尚不存在。 |
| 本輪錄影 | `workplace/out/promo-v106-hard/`、`promo-v106-original/`。各自的 `receipt.json`、`events.json`、PNG 及 MKV 記錄真實操作；來源與素材唯讀掛載。 |
| [合成工具](../../tools/promo.sh) | `HR_VERSION=v.1.0.6-20261103`、`HR_PROMO_FOCUS=difficulty`、`HR_PROMO_LIVE` 指向高難度錄影，`HR_PROMO_ORIGINAL` 指向原版錄影。兩次 F2 保留按鍵及主題完成畫面，預載等待的時長調整有字幕明示。 |
| 原版配樂 | `HR_PROMO_AUDIO_MODE=original-recording`。WAV 為 `workplace/out/original-audio/record-original-verified/capture/main_000.wav`，來源收據為同工作根的 `provenance.json`，分別由 `HR_PROMO_AUDIO_FILE`、`HR_PROMO_AUDIO_RECEIPT` 指定。WAV SHA-256 沿用 `338014322925a94393b9ac03c01e143063594b15c1599e76227ef5b2e3f3e8f5`，未修改原版與原廠驅動播放。 |
| [驗證工具](../../tools/verify_difficulty_promo.py) | 在既有 `hr-go-ebiten:1.26.7-2.9.9-r1` 容器內，以 `--version`、`--hard-capture`、`--original-capture`、`--binary` 指定本輪檔案。核對來源雜湊、1800 幀、音訊、字幕與債務裁切；字型唯讀掛載至 `/usr/share/fonts/opentype/noto`。 |
| 交付收據 | `dist-all/v.1.0.6-20261103/promo/` 的 `verification.json`、`rights.json`、`ffprobe.json`、`contact.png`、`review.md`、兩份 capture JSON 與 build info；根 `SHA256SUMS.json` 記錄本機影片檔案、真正引擎提交及錄影工具工作樹雜湊。 |

技術檢查與唯讀複核通過。音訊平均 −18.9 dB、峰值 −4.2 dB，沒有黑幀或長靜音命中；音訊僅核對來源與技術收據，沒有聲稱真人聽驗。債務裁切的壓縮後 RGB 平均誤差為原版 1.1046／255、高難度 1.1084／255。字卡、選單與數字閱讀停留符合分鏡，兩次 F2 及完整片尾已目視確認。最終獨立審查來源為 `workplace/out/review-promo-v106.md`，無阻擋。

影片及原版配樂只留本機。現行 1.0.5 正式包、影片及 LICENSE 共八項再按原清冊核對相符；原有研究與未提交文件保留。本輪收尾見 `workplace/out/promo-v106-final-audit.json`，可重生清冊的本機入口為 `workplace/out/finalize-promo-v106.py`。

工具列擴充前，已按本版清冊逐檔保存七份錄影／合成／驗證工具的精確來源；索引為 `workplace/out/promo-v106-source.json`，副本為同工作根的 `promo-v106-source-*`。本版清冊中的工具工作樹雜湊指向錄影當時的快照，不改成後來的工具列相容修訂。影片及原清冊保持原樣。

### 工具列立即切換的接線證據

使用者在工具列原型後選擇立即切換，仍使用兩種獨立進度。原型只用於確認配置，沒有改原版或正式遊戲。工具列的新玩家路徑由 [015](../spec/015-toolbar-difficulty-switch.md) 另行規定，014 的已驗規則保持 CONFORMED。

已證實，限基準 fork 的原始碼：`apps/hr/play/main.go` 的 start closure 在 `hrrt.Open` 後才建立音訊、偏好寫入者及 Run。`game.go` 仍是 1280×800，輸入為 x/2、y/2。`runtime/session.go:629` 的 Run 可由 context 取消並返回 nil；取消後重新 Run 會重設牆鐘基準。`HoldAdapt` 只管降頻，不能暫停遊戲。`play/switcher.go:352` 的 Quit 尚未等候預載，重建前必須收完舊工作。這些是新增前端生命週期的依據，不是 DOS 記憶體語意推論。

### 工具列驗證完成

- 現行來源為上方狀態表的乾淨 fork，Linux 程式 `workplace/out/hr-play-difficulty-toolbar-final`，SHA-256 `456139b888eb4a6c91582caa9f7a91b8c9f48ab22648fd39e99b5a3d4d3d1061`。`toolbar-build-info.txt` 與 `toolbar-windows-build-info.txt` 均記錄該提交及 `vcs.modified=false`。舊 `hr-play-difficulty`、錄影專用程式與影片清冊保留原雜湊。
- 前端測試通過，8.429 秒；實際原版的 `TestClearMouseInputBeforeThreePolls`、`TestDifficultyDebtAndProfileIsolation`、`TestColdStartReceiptA` 通過，3.787 秒，沒有 skip。切換 runner、音訊綁定、重複關閉、延後偏好寫入與預載收尾的競態檢查通過，1.868 秒。`go vet` 及 Windows amd64 編譯通過。收據為 `toolbar-frontend-tests.log`、`toolbar-runtime-tests.log`、`toolbar-race-tests.log` 與 `toolbar-vet.log`。
- 唯讀規格複核先解除三次輪詢滑鼠殘留及多份輸出 worker 的阻擋，再進正式接線。實作審查 `toolbar-implementation-review.md` 無阻擋。新 `ClearMouseInput` 只在 Run 已取消並 join 後清滑鼠；取消恢復同一 Session。音訊及偏好 writer 各共用一份，每輪舊預載、HD view、Run 與 DOS 檔案依序收完。
- `toolbar-gui/` 的正常視窗先載入原版槽 0，驗預設 Enter 取消及同模式。故意破壞複製的高難度 profile 標記後，切換失敗顯示「原本遊戲仍保留」，Esc 返回原遊戲；之後還原測試標記，正常切換通過。未改玩家存檔或原始輸入。連續四次成功替換後，開啟檔案數與 OS 執行緒仍為 10／22；音訊裝置只初始化一次。這是本次抽樣，不外推為無限長跑證明。
- 透過正常標題及對話，各在原版、高難度重新開始遊戲，債務顯示 10,000,000／50,000,000，償還額度及現金均為 5000／8000。畫面為 `toolbar-gui/{original,hard}-newgame.png`。HD 主題在切換後保留；初次並行編譯時有畫面尚未繪完的取樣，未作驗收，改採已完成畫面。
- 最終乾淨程式另重跑選擇頁、硬模式槽 0、工具列切回原版槽 0、900×700 縮放下拉、F12 遊戲畫布及 `-no-toolbar` 舊座標讀檔。畫面已目視核對，收據 `toolbar-final-gui/receipt.json` 綁定程式雜湊，兩次退出皆為 0。新視窗為 1280×844，F12 及舊模式為 1280×800；遊戲區不重排。
- 既有錄影與 GUI 工具先查旗標，對新版加入 `-no-toolbar`，對舊包保留原參數。`HR_CAPTURE_TOOLBAR=1` 可錄完整 1280×844 工具列視窗，分鏡座標需包含上方 44 像素；預設仍用原分鏡。既有影片精確來源快照沿用前節索引。本次不重錄或覆寫已交付影片。

015 升為 CONFORMED，僅涵蓋本項工具列與生命週期。014 的玩法、存檔格式與既有正常劇情證據不變。Windows／macOS 原生操作未驗，正式 1.0.5 封包與本機 1.0.6 影片保持原樣，沒有推送或 Release。收尾稽核入口 `workplace/out/toolbar-final-audit.json`。
