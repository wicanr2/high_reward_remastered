# 滑鼠呈現調查

2026-10-07。對應 [Issue #4](https://github.com/wicanr2/high_reward_remastered/issues/4)。使用者在 Linux AppImage 回報游標閃爍及移動遲緩。

## 目前狀態表

| 項目 | 現況 |
|---|---|
| 正式發行 | `v.1.0.2-20261008`，建包根 `2c9d2eb`，執行層 `686581d`；新 tag 指向實際建包來源，舊版不變 |
| 本機目前交付 | `v.1.0.4-20261010`，建包根 `7249b2e`、執行層 `7989c7b`。三平台 `full-local/`、清冊及驗收均在本版 `dist-all/`；舊版與公開 Release 保留 |
| 原版游標 | DOS 軟體游標，40×32 像素，272 個不透明像素 |
| 已證實原因 | 原版繪圖 X 對齊 8 像素；前端等待 DOS 快照，HD 另等待合成 |
| 中間畫面風險 | 輪詢點以外快照可能取到擦除或重畫階段，見規格 004 第 5.1 節 |
| 原版規則 | 保留滑鼠範圍、按鍵事件、輪詢及遊戲時鐘 |
| 高速設定回報 | fork `7989c7b`、補丁 0045，010 高速增補 CONFORMED；本機 `v.1.0.4-20261010` 已納入。原版 A/B 與競態通過，仍保留原版主動隱藏。實包錄影限制見本頁「高速修正版三平台交付」 |
| 修正 | 本機 fork `b687256` 游標修正、`686581d` 五尺寸板面主題；補丁 0042、0043，已正式發行 |
| 最近測試 | 2026-10-10 高速執行層／前端競態、原版 A/B 第 167067321 步、三平台成品格式與素材驗證通過；Linux 正常新遊戲、兩項高速及三主題已操作，AI 原版隱藏補驗與未解範圍見交付段 |
| GUI 證據 | `dist-all/v.1.0.4-20261010/smoke/linux/` 保存實包正常路徑及嚴格模板結果；1144 取樣幀中 1068 單游標、76 未命中、0 重複。首輪 AI 最長 60 幀，不能宣稱零消失；補驗及原版隱藏證據見交付段 |
| 正式交付 | `dist-all/v.1.0.2-20261008/`，full-local／patch 各三包；五個 GitHub Release 資產的大小與 SHA-256 全符本機，收據 `smoke/remote-release-validation.json` |
| 交付完成 | 正式發布、三平台完整版與 60 秒原版配樂推廣片均完成；影片 `promo/HighReward-v.1.0.2-20261008-promo.mp4`，驗收 `promo/verification.json`。Windows／macOS 未實機驗收，Issue 狀態未改 |
| 介面主題工作 | [034](034-procedural-ui-panels.md) 與 [011](../spec/011-procedural-ui-themes.md)：使用者已接受實際介面，五尺寸 PLATE2 已 CONFORMED，未知原語回退原版 |

## 證據

原版 `MAIN.EXE` 的 SHA-256 以 `docs/re/source-inventory.tsv` 及 `apps/hr/patch.MainEXESHA256` 為準；執行層 Open 強制核對。靜態資料沿用 [009](009-draw-primitives-DRAFT.md) 的 IDA Pro 9.4 資料庫與匯出，沒有重新推測函式名。動態探針在 Docker `eob-remake-go:1.26.7-ebiten2.9.9` 執行，Go 1.26.7，原版輸入唯讀。

| 原始定位 | 語意 | 等級與來源 |
|---|---|---|
| IDA `28EB:0897`，bytes `25 f8 ff`；執行期 `19FB:0897` | 將游標 X 向下對齊 8 像素 | confirmed，`workplace/ida-draw/out/f04.txt` |
| 執行期 DS `3E50:001D` | 背景標頭四個 little-endian uint16：X byte、遊戲 Y、寬 byte、高；接著逐列四平面 | confirmed，009 與本輪逐像素比對 |
| 執行期 DS `3E50:02A9` | 未裁切的 805 bytes 游標精靈，40×32、遮罩透明值 16 | confirmed，解碼與未裁切戳記一致 |
| 執行期 DS `3E50:1BD1` | 當輪邊界裁切後的繪圖精靈 | confirmed，009 與右下角戳記差異 |
| 執行期 DS `3E50:02A5/02A7` | 游標熱點 | confirmed，009，動態樣本皆為 0 |
| 執行期 DS `3E50:0019/001B` | 已保存背景／啟用繪圖旗標 | confirmed，009；中間階段不能單凭旗標當作畫完 |
| IDA `28EB:00AB/00B1`；執行期 `19FB:00AB/00B1` | 隱藏函式在背景還原完成後依序清除 0019、001B | confirmed，IDA Pro 9.4 本輪唯讀匯出 `workplace/out/cursor-hide-ida.txt` |

動態探針 `workplace/out/hrmouseprobe.go` 以正常輸入從標題點「新遊戲」，沒有注入狀態或修改記憶體。結果 `workplace/out/mouse-probe-v102/receipt.json`：標題滑鼠範圍 X 265..375、VGA Y 205..235；新遊戲變成 X 0..639、VGA Y 40..439。送入 X=101 時原版游標畫於 X=96。背景解碼與游標移到不重疊位置後的畫面比較，1,280 像素全部吻合。右下角來源精靈與繪圖戳記不同，必須用裁切後精靈消除舊游標、未裁切精靈畫新游標。

本機基線錄影 `workplace/out/mouse-before-v102/mouse-before.mkv` 與 `receipt.json` 使用已發行完整包的執行器 SHA-256 `0e043c9320501c1378cdff77c8e6c6ce12c3af58a227acd2712f17d9d4d7672f`。取樣在標題，滑鼠範圍受限，不能用它宣稱完整地圖延遲改善幅度。

## 接手核對

2026-10-07 核對目前工作樹。根儲存庫 HEAD 為 `3f34c26951f649ad7b6e676608a83508bebfee7f`，執行層 HEAD 為 `28c1c2daab2fc7a048f83c0dbca4bafe9d31b84d`。游標實作仍未提交。接手沒有修改執行層程式，也沒有重新發行。

- 以既有 `eob-remake-go:1.26.7-ebiten2.9.9`、Go 1.26.7、唯讀原版輸入執行 `go test -race -count=1 -run '^TestCursor' -v ./apps/hr/runtime`。四項通過，包含真實原版狀態不變的測試；紀錄 `workplace/out/cursor-handoff-runtime-tests.txt`。
- 同容器以有界 Xvfb 執行前端 `go test -race -count=1 -run '^Test(Cursor|HDView|Screenshot|NoHDTheme)' -v .`，全部通過；紀錄 `workplace/out/cursor-handoff-play-tests.txt`。這些窄測試不取代 010 尚待補核的邊界覆蓋、審查或實包驗證。
- 上輪正常新遊戲錄影入口 `workplace/out/mouse-after-game-v102/receipt.json`，執行檔 SHA-256 為 `80f2627aa4ec3c8142cc3c9c7d94a456f452517c605ec561779c9adf303d186d`，與現存 `workplace/out/bin/hr-play` 相同。完整 `theme-1.png` 與 `theme-2.png` 目視確認 HD 與 AI 已切換；不以 `theme ready` 日誌單獨判定。
- `workplace/out/cursor-video-check.json` 的修正後樣本為 548 幀，單游標 548、未偵測 0、雙游標 0。這只證明指定錄影取樣區域內的呈現；沒有量測 DOS 按鍵延遲或使用者桌面延遲。修正前後 HD 游標形狀可能不同，原版模板未命中不能直接當成游標消失。
- 遠端 Issue #4 與 #5 仍開啟，儲存庫為 PUBLIC。主 repo 與 fork 無原版同名檔誤追蹤，工作根無 root-owned 檔案或 `.md` 目錄，接手容器均已退出並刪除。

## 2026-10-08 修正與收尾入口

- `workplace/out/cursor-final-runtime-tests.txt`、`cursor-frontend-final-tests.txt`：游標邊界、異常資料、500 毫秒停止回退及底圖配對。
- `workplace/out/review-cursor-implementation-a.md`、`review-cursor-implementation-b.md`：兩份獨立實作審查及複核。
- `workplace/out/ui-runtime-original-ab.log`：正常標題點新遊戲及兩次對話輸入，兩側各 106000000 步；UI 觀測不改 CPU、記憶體、VRAM、ticks、palette／map、DOS Stats。
- `workplace/out/ui-runtime-final-regressions.log`、`ui-play-final-regressions.log`：同值字形、保存身分、非 80-byte 列距、已驗游標的 pending 交界及 RGBA／Frame／style 三元組測試。
- `workplace/out/review-ui-final.md`、`review-ui-cursor-boundary.md`：完整唯讀審查與最後游標交界複核。
- `workplace/out/ui-final-gui/cursor-validation.json`：最終執行檔 `cd4d69a3b9530577de99a3202d1119196091b22f256e8cc9db8a2327b9c71589`，918 幀無漏畫／雙游標，F12 完整匹配；方法 `workplace/out/check-cursor-final.py`。
- `workplace/out/package-static-v102-report.md`、`verify-ui-packages-v102.py`：六包獨立內容／格式驗證與重跑程式；機器收據 `dist-all/v.1.0.2-20261008/smoke/full-static.json`。
- `dist-all/v.1.0.2-20261008/smoke/linux/receipt.json`、`cursor-validation.json`：實際 AppRun 僅使用包內資源啟動；正式版號已注入，執行器 SHA-256 `117eb4e4cc31521a0856ea17b2ca8e95cef738d9eabe5ee028b5855d52557140`。598 幀皆單游標，F12 272／272。正常輸入程式 `workplace/out/capture_v102_bundle.py` 沿 `tools/capture_promo.py`，沒有注入狀態。
- `dist-all/v.1.0.2-20261008/smoke/remote-release-validation.json`：新正式 Release 五資產與本機大小／SHA-256 相符；`promo/verification.json`：60 秒原版執行錄音推廣片已 `final-pass`，審查見 `workplace/out/promo-release-v102-review.md`、`original-music-source-review.md`。

主題圖上的橄欖色斜塊曾被當成背景殘留；完整游標模板比對顯示它是原版游標的前景色。保留這個圖形，沒有改畫游標。另由窄測獨立找出的 pending 取消下方板面缺口已修正；不把兩者混稱同一原因。

## 停止線

這是前端呈現修正，不更動 DOS 游標例程、INT 33h、原版檔案或存檔。原版座標取樣、按鍵讀取延遲與遊戲速度不在本次加速範圍。Linux 虛擬顯示器驗證不等於使用者桌面的實機驗收。

## 2026-10-10 高速設定

輸入 `MAIN.EXE` SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。根 HEAD `a4fb7ba`、fork `ae27856`，Docker `hr-go-ebiten:1.26.7-2.9.9-r1`、Go 1.26.7、Ebiten 2.9.9。原版資料唯讀。下列數值分別標示執行期與 IDA 位址，不混用。

- confirmed：正常新遊戲後推進 16 次對話，點右上筆圖示與系統設定，將時間進行及顯示的速度改為高速，關閉設定後移動滑鼠。實際前端錄影 `workplace/out/cursor-fast-before-gui/fast-cursor.mkv`、`settings-high.png`、`fast-theme-0.png` 與 `play.log` 重現指針消失及 500 毫秒重畫逾時。正常輸入腳本為 `workplace/out/cursor-fast-control.json`，執行入口 `tools/capture_promo.py`，未注入狀態或修改原版記憶體。
- confirmed：舊程式只在滑鼠輪詢或 100 毫秒無輪詢回退時取樣，`snapshot()` 即使取得 `CursorPending` 仍消耗本次要求。高速下同一取樣相位可連續落在重畫中，逾時後發布不含游標的原始畫面。`workplace/out/cursor-fast-probe.go`、`cursor-fast-sample.log` 保存補充探針；探針中的 state 是從正常路徑取得，僅供縮小問題。
- confirmed：既有 IDA Pro 9.4 匯出 `workplace/ida-draw/out/f04.txt` 的原始函式 `sub_295FD`，IDA `28EB:074D`，在 IDA `28EB:089D` 呼叫精靈繪圖，返回點 IDA `28EB:08A2`，bytes `83 c4 0a`。對應執行期 `19FB:089D`／`19FB:08A2`。IDA `28EB:07C4` 的 `c7 06 19 00 01 00` 已將保存背景旗標設為 1；此後才複製裁切精靈並繪圖。返回點也是既有 `hd.CursorSite`，不另推測完成位址。
- confirmed：`workplace/out/cursor-fast-return-probe.log` 的 pending 快照在第 184667146 步，執行期 `54C0:7F6B`，旗標 0／1；正常繼續 10840 步到執行期 `19FB:08A2`，新快照通過完整游標驗證，旗標 1／1。一次指令前進探針 `cursor-fast-return-probe_test.go` 只觀察，不寫記憶體。
- 修正設計：已知重畫中的快照保留一次補取機會，在上述繪圖返回點補取，再走 010 的完整格式與像素驗證。每次要求最多增加一張補取快照，避免重畫失敗時無界取樣。正式隱藏、未知格式、500 毫秒回退與原始 `Frame.Px` 契約保留。

當時待補項目為高速正常 GUI 三主題、補取回歸、執行層開關的機器狀態 A/B、游標與前端競態測試；後續結果見下文「計數勘誤與最終驗證」。規格增補入口為 [010](../spec/010-cursor-presentation.md#高速設定的補取畫面)。

首次補取修正的回歸與 A/B 已通過，兩側第 167067321 步的機器快照及 DOS 統計完全相同，收據 `workplace/out/cursor-fast-tests.log`。但 GUI `cursor-fast-after-gui/cursor-validation.json` 仍有原版 2／363、HD 88／368、AI 110／401 個未偵測幀，不能宣稱完成。修正前收據 `cursor-fast-before-gui/cursor-validation.json` 為原版 245／363、HD 147／365、AI 183／372。

程式已證實非同步合成器只讀最近一張 Frame，pending 的 `Presentation()` 回 nil。完整補取幀若在合成器讀取前被後續 pending 覆蓋，合成器會保留更早的底圖與隱藏狀態。這是可受控驗證的漏讀分支；實際 GUI 的精確相位仍為強推論。增補規格回 DRAFT，保存最近完整呈現幀，讓 pending 帶著整張配對底圖供合成器使用，不改原版隱藏語意。

### 計數勘誤與最終驗證

後續逐幀核對推翻「首次修正後的大量未命中代表 HD／AI 仍持續漏畫」的判讀。模板只接受完整正常色盤，黑畫面及轉場也會未命中。獨立以資訊欄固定白字核對，首次修正 HD 的 88 幀有 85 幀的 HUD 白字強度為 0，AI 的 110 幀有 92 幀的 HUD 白字強度為 0。其餘一般色盤下連續未命中最長 8 幀，不能由原始計數證實非同步漏讀的 GUI 相位。保留前述原始收據與設計歷史；完整幀傳遞的必要邊界由可達程式分支與受控漏讀回歸獨立驗證。

最終修正增加一次繪圖返回補取，並保存整張已還原背景、過濾游標戳記的完整呈現幀。pending 引用此幀，讓原版前端及非同步合成器取得同一份底圖、游標、色盤及 HD／UI 資訊。完整隱藏幀取代舊可見幀；未知格式清除保存，不改原版隱藏規則或 500 毫秒期限。

- `workplace/out/cursor-fast-final-runtime-race.log`：游標、補取上限、一層保存鏈、原始快照不可變、隱藏／未知格式、停止後到期，競態測試通過，1.528 秒。
- `workplace/out/cursor-fast-final-original-ab.log`：正常新遊戲、16 次對話及兩項高速設定；第 166967321 步取得 pending，沒有新要求仍補取成功。開關兩側第 167067321 步的完整機器快照與 DOS 統計相同，25.520 秒。
- `workplace/out/cursor-fast-final-frontend-race.log`：受控跳過完整幀後的兩種消費者、呈現 Seq 去重、同一 Seq 到期、HD 世代、UI 與截圖，競態測試通過，13.143 秒。`go vet` 及 Windows amd64 編譯通過；未做 Windows／macOS 實機操作。
- `workplace/out/cursor-fast-final-gui/`：由正常新遊戲設定兩項高速，原版、HD、AI 各 60 次移動；設定畫面、三主題截圖、錄影與收據均保留。執行器 SHA-256 `71fe9a36ca9ef81d7d2dd1fd43ab237ff21dc96c8ad80c75008d2781c5e8fef4`，沒有 state 注入，沒有再記錄 500 毫秒游標逾時。

| 最終錄影 | 取樣幀 | 單游標 | HUD 白字為 0 時未命中 | 一般色盤未命中 | 重複游標 |
|---|---:|---:|---:|---:|---:|
| 原版 | 367 | 312 | 49 | 6 | 0 |
| HD | 367 | 349 | 15 | 3 | 0 |
| AI | 364 | 250 | 106 | 8 | 0 |

原始嚴格模板收據 `cursor-validation.json` 沒有修改判準，仍記錄 187 個未命中。`workplace/out/classify-fast-cursor.py` 另以游標區域外的資訊欄白字強度區分轉場，輸出各輪 `visibility-classification.json`。170 幀只代表該區各像素 RGB 最小分量的最大值為 0；獨立審查逐幀檢查全 RGB，140 幀確為全黑，30 幀仍有非零像素，不能將 170 幀全部稱為整體黑畫面。修正前一般色盤的最長連續未命中為原版 82、HD 32、AI 66 幀；最終最長為 5 幀，約 0.17 秒。最終 17 個一般色盤未命中的抽樣 `active-missing-220.png`、`400`、`719`、`984`、`1166` 均在人物換圖期間，可見換圖及局部未畫完的肖像。沒有逐幀記錄原版隱藏旗標，這些幀不能稱為全部已證實的正式隱藏，也不能宣稱全錄影零未命中。持續數秒消失的回報未再出現；不為清除短暫未命中而強制顯示原版主動隱藏的游標。

首次把原版長流程與全部游標測試一起開競態模式，達 240 秒外層上限後停止，部分紀錄為 `cursor-fast-final-runtime-race-interrupted.log`。同一工具鏈改為快速游標競態、正常模式原版 A/B、前端競態後乾淨重跑通過，屬驗證範圍配置問題。

審查入口 `workplace/out/review-fast-cursor-spec.md`、`review-fast-cursor-implementation.md`。完成前審查允許此狹義切片升 CONFORMED，保留上述換圖限制。fork 提交 `7989c7b7109bae9cc12cc67d8e1603cfba47ba2f`，備份 [0045](../../engine/patches/0045-fast-cursor-presentation.patch)。本輪只修程式與保存補丁，不重建或覆寫既有 `v.1.0.3-20261010` 完整包，也未發布新 Release。收尾稽核入口為 `workplace/out/cursor-fast-final-audit.py` 與 `cursor-fast-final-audit.json`。

## 2026-10-10 高速修正版三平台交付

使用者要求 commit、push 與三平台完整版。修正根 `7249b2e20f17761b94340b51be9fc2f3ab184ca1` 已推送，fork `7989c7b7109bae9cc12cc67d8e1603cfba47ba2f` 由補丁 0045 保存，不推送 fork 上游。三包從乾淨暫存工作樹與既有固定 Docker 工具鏈重建；其他未提交音樂研究未納入。唯一交付為 `dist-all/v.1.0.4-20261010/full-local/`，公開 Release／tag 仍為 1.0.2。

- `workplace/out/v104-full-build.log`、`verify-fast-cursor-packages-v104.py` 及 `smoke/full-static.json`：重新解包核對原版 148 檔大小與 SHA-256、HD 595、AI 595、五語譯表與 Noto 字模、正式版號及平台架構。Linux 固定 AppImage runtime／ELF、Windows PE／ZIP CRC／UTF-8／README BOM／CRLF、macOS universal arm64＋x86_64／plist／ICNS／執行位元均通過。Windows／macOS 未實機執行。首次驗證僅缺少 smoke 輸出目錄，建立後以同容器與命令重跑，未修改封包。
- `smoke/linux/receipt.json`：實際 AppRun 僅使用包內資料，正常新遊戲、16 次對話、兩項高速及 F2 三主題各 60 次移動；沒有狀態注入。執行器 SHA-256 `8d68febf4586b8ca46ece887e63635c6029cf8139865ccd751027a74b33881a1`，與三包靜態收據對應。設定畫面已目視確認兩項高速；沒有 500 毫秒重畫逾時紀錄。
- 原始模板取樣為原版 364／375、HD 390／390、AI 314／379 單游標，76 未命中、0 重複。AI 最長連續未命中 60 幀約兩秒。首次全畫面搜尋錯用 decoder n，原檢查使用經時間戳補幀的 rawvideo 輸出 idx；來源 1851 幀、輸出 1939 幀，兩種編號不可混用。原錯誤交叉核對保留並標 invalid，修正後相同串流的全畫面核對仍為 76 未命中，入口 `workplace/out/v104-fullscreen-cursor-check.py`、`rawvideo-aligned-fullscreen-crosscheck.json`。沒有放寬模板門檻。
- `workplace/out/v104-fast-cursor-observed/`：同一實包外部逐次截圖補驗，180 次中 170 次完整命中。AI 連續未命中時請求既有 Ctrl+D，唯讀解碼得執行期 `20C2:27E0`、第 418011136 步、游標雙旗標 `0/0`；state SHA-256 `b5b3d44f542f3e4dff2b7131245cf228dcb2cf04b03cbe896a8fe16190fbe05c`。只證明診斷當下原版已隱藏，不回填首輪 60 幀的逐幀語意。
- `workplace/out/v104-trace-bin/source.json`、`v104-fast-cursor-trace/`、`v104-fast-ai-trace/`：只在容器暫存副本加入原版快照、實際 Draw 與繪圖返回紀錄，正式 fork 與封包不改。AI 正常移動的 1.674 秒隱藏段顯示 Seq 1800..1814，這 15 張原始快照皆為 `0/0`、非 pending；前端隨新隱藏幀前進。第一張隱藏 Draw 起算約 1581 毫秒才有繪圖返回，1661 毫秒取得可見 Seq 1815，1777 毫秒顯示該幀。末端包含約 117 毫秒的呈現傳遞時間，不能稱整段都沒有返回；前端沒有持續停留舊隱藏幀。入口 `analyze-v104-presentation-trace.py` 與該輪 `presentation-trace-summary.json`，原始行號保留。同步日誌會影響時間，不稱為未修改實包逐幀對拍。

已證實補驗中的原版主動隱藏及恢復，不能把所有未命中都算成呈現錯誤。首輪 AI 60 幀沒有同步原版旗標，原因仍保留 unknown；不宣稱全錄影零消失、全部未命中已分類或完整原版 parity。此次交付包含已驗證的 pending 補取修正，沒有強制蓋過原版 hide，也沒有因此追加新規則。

| 本機交付路徑，位於 `dist-all/v.1.0.4-20261010/` | 位元組 | SHA-256 |
|---|---:|---|
| `full-local/HighReward-v.1.0.4-20261010-x86_64.AppImage` | 158251512 | `73ae377e2fb0ba29fb1bdee5adefa99ed9d2d45fa68336f08631d58b94ea38a4` |
| `full-local/HighReward-v.1.0.4-20261010-win64.zip` | 160098510 | `413f16e430e1efdea38d648679344e07aa71192762ea57de96aa24fd7ec7b2fb` |
| `full-local/HighReward-v.1.0.4-20261010-macos.zip` | 164337330 | `706e1cd3b5455480d8872536b39cc347cafe5b2b89ad900dc19de0f64406c8e7` |

清冊重生入口 `bash tools/finalize_full_local.sh`，固定 `HR_VERSION=v.1.0.4-20261010`、`HR_BUILD_SOURCE_COMMIT=7249b2e20f17761b94340b51be9fc2f3ab184ca1`、`HR_BUILD_FORK_COMMIT=7989c7b7109bae9cc12cc67d8e1603cfba47ba2f`。建包後的文件提交不改寫來源。收尾稽核入口 `workplace/out/v104-final-audit.py` 與 `v104-final-audit.json`；原版、診斷與完整版只留本機。
