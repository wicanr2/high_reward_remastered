# 014 HD 疊層的實作與驗收收據

日期：2026-10-03
範圍：`docs/spec/004-hd-overlay`（READY，第六版）的實作與驗收。不含 HD 素材的驗收（使用者目視）與 `hd/` 目錄的建立。
輸入：`MAIN.EXE`（SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`）；清冊與調色盤表由 `tools/hd/catalog.py` 產生（`workplace/hd-work/catalog.tsv` 592 種不同內容、`palettes.tsv` 24 種）；HD 圖是美術 v2 基準（`workplace/hd-work/x2-v2`，615 張，`METHOD.md`）。
工具：`workplace/dosgolem` 分支 `hr`，實作 commit `65706a9`（掛鉤、驗證、合成、前端）與 `6a0ff0d`（平行合成、淡入掃描、`SnapshotNow`），基底 `160f55c`；備份 `engine/patches/0012`、`0013`。驗收工具 `apps/hr/cmd/hrhd`（`tools/dosgolem.sh hd …`）。Go 1.24（容器 `golang:1.24-bookworm`，前端用 `eob-remake-go:1.26.7-ebiten2.9.9`）。
推論等級：confirmed（可由指令重跑）、強推論、假說、未知。HD 輸出 PNG 是原版美術的衍生物，只放 `workplace/out/hd/`，不進版控。

## 1. 實作內容

| 位置 | 內容 |
|---|---|
| `apps/hr/hd/stamp.go` | `Queue`：去重（`x`、`y`、`w`、`h`、雜湊）、呼叫點 singleton（只有游標 `19FB:08A2`）、LRU 1024，沒有依事件的移除規則（規格 4.2） |
| `apps/hr/hd/verify.go` | `Verifier`：位元列的 3x3 鄰域驗證加「被序號更大的戳記解釋」，全相符與全不符的快速路徑（規格 5.3 第 1、2 步） |
| `apps/hr/hd/compose.go`、`compose_draw.go` | `Composer`：基底層放大、由大到小的前往後 over 混合、純乘法淡入縮放（`g` 的分母為 0 的處理）、羽化區；依來源列分 band 平行 |
| `apps/hr/hd/assets.go` | `Assets`：讀清冊與調色盤表，HD 圖延遲載入並檢查尺寸與調色盤，失敗每個雜湊記一次、回退基底層 |
| `apps/hr/hd/capture.go` | `Overlay`：五個進入點的掛鉤（偏移點陣圖先篩）、返回鉤子（`SP` 對得上才轉有效）、記錄模式、返回時相符比例的量測 |
| `apps/hr/runtime` | `Options.HDHooks` 等、`Frame.Stamps`、`stepBatch` 的 `Pre`／`Post`、`FrameLimiter`（16 ms）、`Session.SnapshotNow`（無頭驗收用） |
| `apps/hr/play` | `-hd`、`-no-hd`；背景合成 goroutine（`hdView`）；`Layout` 依倍率；不開 HD 時維持原路徑 |

與規格不同之處：

- 規格 4.1 沒寫清楚 `2E92:066A` 與 `348F:0005` 的 VRAM 偏移要加 40 列。第一次實作以偏移直接當 Px 列，`FACE` 返回時只有 20.2% 相符，診斷的最佳位移是 `(+0, +40)`；加上後 100%。規格已補（4.1 表）。審查者的工具用遊戲區座標，所以沒有遇到。
- 合成依列平行（規格 5.3 沒有要求）。理由是單核 11 ms 超過 10 ms 的效能目標；結果與單執行緒逐位元相同（`TestComposeWorkersEqual`）。

## 2. 單元與整合測試

`tools/dosgolem.sh go test ./apps/hr/hd ./apps/hr/patch ./apps/hr/runtime` 全數通過。需要原版的測試缺檔就 skip。

| 測試 | 驗證 |
|---|---|
| `TestVerifyMatchesNaive` | 位元列實作與逐像素定義（含解釋規則、Px 邊界外、負座標、跨 64 位元字界）逐位元相同，400 回合。突變測試：拿掉解釋規則（`&^ v.xl[k]`）後第 1 回合就失敗 |
| `TestVerifyPaths` | 全相符走快速路徑、全不符為空、孤立相符被 3x3 否決、角落被蓋時損失 4 個像素、被後序戳記解釋時只損失角落本身 |
| `TestQueue` | 去重、singleton 取代（同呼叫點、不同雜湊與位置）、LRU、被丟棄後 singleton 追蹤跟著清 |
| `TestComposeFrontToBackEqualsPainter` | 由大到小的前往後混合與「序號由小到大逐一覆蓋」逐像素比對，150 回合含羽化與部分透明，最大差 1 |
| `TestComposeStamps`、`TestComposeBase` | 基底層最近鄰放大；無 HD 的戳記遮蔽 HD；不相符的像素不畫 |
| `TestComposeWorkersEqual` | Workers ＝ 1、3、8 逐位元相同 |
| `TestFade` | 恆等；DAC 全 0 時任何顏色輸出 0；參考調色盤有全 0 通道時（`g` 的分母為 0）仍輸出 0；一半亮度的縮放 |
| `TestLoadAssets` | 清冊與調色盤載入；尺寸不符拒絕並只記一次；不在清冊的雜湊沒有 HD；缺清冊回錯誤 |
| `TestHDHooksDoNotChangeTheGame`（需要原版） | 冷啟動到新遊戲 90,000,000 步，掛鉤開與關：畫面 PNG、步數、`IP`、段暫存器、通用暫存器、1 MB 記憶體逐位元相同 |
| `TestHDHooksColdStartIdentification`（需要原版與清冊） | 解碼失敗 0、返回對不上 0；未識別的只有游標；佇列中游標戳記 1 個；返回時相符比例最低 ≥ 0.99 |
| `TestFrameLimiter` | 144 Hz 呼叫時間隔皆 ≥ 16 ms（約 48 Hz）；60 Hz 與 30 Hz 每次放行 |
| `TestCatalogCrossCheck`（先前） | Go 解碼的 553 個 MRG 項目雜湊與清冊相同 |

## 3. 識別率與返回時相符比例（`hrhd`，confirmed）

清冊目錄 `workplace/hd-stage`（`catalog.tsv`、`palettes.tsv` 的副本，`x2` 連到 `x2-v2`），`-check 3`（每個雜湊前 3 次出現在返回時以 `Machine.Planar` 量一次）。

| 情境 | 指令 | 結果 |
|---|---|---|
| 冷啟動到新遊戲 | `tools/dosgolem.sh hd -hd /orig/hd-stage -steps 90000000 -click 35000000:312:211` | 90,050,000 步。進入：`2B47:0022` 4,791、`348F:0005` 1、`2FB2:25A1` 2。建立 4,793，解碼失敗 0，略過 0，返回對不上 0。已識別 18，未識別 4,775，全是游標（`19FB:08A2`，40x32，雜湊 `e5f25238…`）。佇列 18。相符比例 10 個雜湊全為 1.000（含 `FACE.MRG:0`、`GMAP.PXS`） |
| 戰鬥佈陣 | `-state /out/explore2/nodes/n00071.state -click 0:16:96 -steps 18000000`（探索節點 71，點 (16,56)） | 進入：`2B47:0022` 792、`2E92:066A` 1。建立 793，解碼失敗 0，返回對不上 0。已識別 331，未識別 462（全是游標）。佇列 121，其中 105 個有 HD 圖。21 個雜湊的相符比例首次與最低皆 1.000（含 `BSTAGE.MRG:7`、`BC32`、`DEAD`） |

等級：進入點參數、解碼與位置換算 confirmed（兩個情境，所有取樣 1.000）。`2378:1155`（24x24 快取）在這兩個情境沒有被呼叫，位置與參數沒有實測：未驗證。

## 4. 淡入淡出（confirmed，限所掃描的範圍）

`-fade-scan -fade-slice 5000 -steps 44000000 -click 35000000:312:211`：從冷啟動起每 5,000 步在批次邊界取快照（`SnapshotNow`）並合成。8,787 張快照，14 種不同的顯示調色盤，1,800 張全黑（DAC 全 0），**漏光 0 張**（全黑時合成結果每個像素皆為 0），HD 參與 7,854 張。`TestFade` 另驗恆等與參考調色盤有全 0 通道的情形。中間狀態的偏差分布沿用審查者的實測（規格 5.4），本實作未重量。

## 5. 前端（Xvfb 內的 GUI，confirmed 限於一次執行）

`tools/pkg/verify_hd.sh workplace/out/hr-play-hd workplace/hd-stage workplace/out/hd/gui`：Linux、cgo、Xvfb 1280x800。標題畫面顯示 HD 的 `GMAP`，標題選單與游標（無 HD，還原成基底層）正常；點「新遊戲」後的第一個畫面顯示 `FACE` 的 HD 肖像與地圖、對話框、錢數字。截圖 `workplace/out/hd/gui-title.png`、`gui-newgame.png`。這台機器在量測時負載 22 至 28，前端自動把計時器間隔降到 150,000（`docs/spec/003` 第 4 節）。

## 6. 效能（容器內，受主機負載影響大）

| 項目 | 結果 |
|---|---|
| 掛鉤對模擬速度的影響 | 冷啟動 90,000,000 步交錯各跑兩次（主機 load 22）：關 11.0 s、9.0 s，開 12.2 s、7.8 s。差異在雜訊內；規格估計每步多 0.2 至 0.5 ns |
| 合成時間，戰鬥佈陣 121 個戳記（105 個有 HD），每幀通過 93,795 個像素 | 單核（容器 2 核限額、平行化前）10.3 至 13.4 ms；平行化後（容器 4 核限額，主機 load 8 至 11）6.1 與 6.4 ms，其中基底 0.2 至 0.7、驗證 1.1 至 2.4、繪製 3.1 至 3.5 ms。不疊 HD（`-nohd`）4.5 至 7.1 ms |

規格的目標是實際畫面平均 ≤ 10 ms。平行化後 4 核達標；單核與負載高時約 11 至 13 ms，低於 60 Hz 的 16.7 ms 但高於 10 ms：單核目標未達。壓力情境（512 個戳記）本實作沒有量。

## 7. 沒有驗證的項目

- 規格第 7 節：「被蓋住與還原」（`SPOINT_021`、`SPOINT_014` 的實際重播）、「游標」掃描 100 個位置、游標右緣裁切形、「快照完整」（游標矩形完整比例）、100 毫秒退回路徑、「3x3 等價」的 6 個情境數字：本實作沒有在這些情境重播。演算法與逐像素定義的等價由單元測試證明；情境的數字是審查者的實測。
- 「目視」：使用者尚未看過。HD 素材尚未驗收，`hd/` 未建立，發行包不含 HD 素材。
- `2378:1155`、`2E92:0414`（排除）、旗標非 0 與 x 非 8 的倍數的路徑（略過並計數）：未觸發或未驗證。
- 游標的 HD 素材與右緣兩個裁切形：沒有。游標目前沒有 HD，顯示基底層。
- macOS 與 Windows 上的 HD 前端：沒有實機。Windows 與 macOS 的發行包尚未重建，`hr-play` 在其中仍是不含 HD 的舊版。
- 長時間遊玩下戳記佇列、HD 圖快取的記憶體用量：未量。

## 8. 重跑

```text
# 清冊目錄（只含衍生資料的副本與連結，在 workplace 內）
mkdir -p workplace/hd-stage && cp workplace/hd-work/catalog.tsv workplace/hd-work/palettes.tsv workplace/hd-stage/
ln -sfn ../hd-work/x2-v2 workplace/hd-stage/x2
tools/dosgolem.sh build
tools/dosgolem.sh hd -hd /orig/hd-stage -steps 90000000 -click 35000000:312:211 -png /out/hd/cold-newgame.png
tools/dosgolem.sh hd -hd /orig/hd-stage -state /out/explore2/nodes/n00071.state -steps 18000000 -click 0:16:96 -png /out/hd/bat71.png
tools/dosgolem.sh hd -hd /orig/hd-stage -fade-scan -fade-slice 5000 -steps 44000000 -click 35000000:312:211
tools/dosgolem.sh go test ./apps/hr/...
```
