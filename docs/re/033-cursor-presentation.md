# 滑鼠呈現調查

2026-10-07。對應 [Issue #4](https://github.com/wicanr2/high_reward_remastered/issues/4)。使用者在 Linux AppImage 回報游標閃爍及移動遲緩。

## 目前狀態表

| 項目 | 現況 |
|---|---|
| 正式發行 | `v.1.0.2-20261008`，建包根 `2c9d2eb`，執行層 `686581d`；新 tag 指向實際建包來源，舊版不變 |
| 原版游標 | DOS 軟體游標，40×32 像素，272 個不透明像素 |
| 已證實原因 | 原版繪圖 X 對齊 8 像素；前端等待 DOS 快照，HD 另等待合成 |
| 中間畫面風險 | 輪詢點以外快照可能取到擦除或重畫階段，見規格 004 第 5.1 節 |
| 原版規則 | 保留滑鼠範圍、按鍵事件、輪詢及遊戲時鐘 |
| 修正 | 本機 fork `b687256` 游標修正、`686581d` 五尺寸板面主題；補丁 0042、0043，已正式發行 |
| 最近測試 | 2026-10-08 完整前端與 UI／游標競態測試、獨立完成前審查、六包靜態驗證及實際 AppImage 抽測通過；原版 A/B 兩側各 106000000 步，機器狀態相同 |
| GUI 證據 | 候選實包 `dist-all/v.1.0.2-20261008/smoke/linux/` 正常新遊戲含 F2 三主題、F1、F12、左右鍵；598 幀全為單游標，F12 模板 272／272。先前 standalone 的 918 幀另留 `workplace/out/ui-final-gui/` |
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
