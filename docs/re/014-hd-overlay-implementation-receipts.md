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
- 5.3 第 2b 步（單色連通區）是實作階段加入的，第八輪審查同意並要求加面積上限，見 4.2。
- 合成依列平行（規格 5.3 沒有要求）。理由是單核 11 ms 超過 10 ms 的效能目標；結果與單執行緒逐位元相同（`TestComposeWorkersEqual`）。

## 2. 單元與整合測試

`tools/dosgolem.sh go test ./apps/hr/hd ./apps/hr/patch ./apps/hr/runtime` 全數通過。需要原版的測試缺檔就 skip。

| 測試 | 驗證 |
|---|---|
| `TestVerifyMatchesNaive` | 位元列實作與逐像素定義（含解釋規則、Px 邊界外、負座標、跨 64 位元字界）逐位元相同，400 回合。突變測試：拿掉解釋規則（`&^ v.xl[k]`）後第 1 回合就失敗 |
| `TestVerifyFlatMatchesNaive`、`TestVerifyFlatDropsGhost`、`TestVerifyFlatSkipsLargeStamps` | 第 2b 步（單色連通區）與逐像素定義逐位元相同；相連的多色區保留、獨立的單色區移除；面積超過 `FlatMaxArea` 的戳記不做（見 4.2） |
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

## 4.1 游標與快照完整

- 游標（40x32）由 `28EB` 段在執行期產生，不在檔案內。`hrhd -dump-unknown` 在標題與新遊戲地圖畫面把游標戳記存成調色盤 PNG：一般位置 `e5f25238…`，x ＝ 624 的 `e3ea446b…`，x ＝ 632 的 `8f6f68df…`（共 3 個雜湊，呼叫點皆 `19FB:08A2`）。三張用美術 v2 管線（`sprite` 類別）做成 80x64 的 HD 圖，`validate.py` 檢查 3 張違規 0 張，放在 `workplace/hd-work/x2-v2/CURSOR/`。`tools/hd/catalog.py` 新增第 5 個參數（執行期取樣根目錄）把它們以 `RUNTIME:CURSOR/…` 為 id 加入清冊（595 種不同內容）。清冊含游標後，冷啟動 60,000,000 步：進入 3,745 次、已識別 3,746、未識別 0，標題畫面的游標顯示為 HD（`workplace/out/hd/title-cursor.png`）。
- 快照完整（`-poll-scan 300`，輪詢點取快照，統計最新游標戳記的整個不透明區是否都與 VRAM 相符）：標題畫面 300／300（100%）；新遊戲地圖畫面 294／300（98.0%），規格要求大於 95%。戰鬥佈陣（節點 71 點 (16,56) 後）0／100：該畫面輪詢時游標不在 VRAM 上（相符分布全部落在 0 至 50% 之間），不是快照不完整；驗證式疊層因此不畫它，與規格一致。100 毫秒退回路徑沒有量。

## 4.2 對話框殘影與單色連通區（第 2b 步）

目視 Xvfb 的新遊戲第一個畫面（`workplace/out/hd/review/2-newgame-hd.png`）發現對話框內有幾塊深色殘影。`hrhd -explain 175,145,450,220` 列出該矩形內的戳記：`SPOINT.MRG:12`（272,184）不透明 547 個、相符 330、通過 79，通過的 79 個像素只有 1 種顏色（對話框底色與該精靈的同色區）；`SPOINT.MRG:17`（400,200）與（432,156）各有 102 與 56 個通過像素落在對話框內，但這兩個精靈在框外露出多色部分。

規格 004 第 8 節原把這類殘影列為已知差異。實作階段改以第 2b 步處理：V 的 8 連通區若只含一種期望顏色就整區移除（先試過「3x3 鄰域全是同一個顏色」的逐像素版，無效：殘影在精靈輪廓邊緣，鄰域含透明像素）。第八輪審查同意寫入規格，並指出對 `GMAP` 等整張戳記的洪水填充使驗證階段多 4 至 7 ms，要求加面積上限；已加 `FlatMaxArea`（16,384 個像素），`GMAP`、`BSTAGE`、`FACE` 不做。加上限後的實測（`hrhd`，與 `-no-flat` 對照）：

| 畫面 | 移除的像素 | 驗證階段（開 ／ 關第 2b 步） | 說明 |
|---|---|---|---|
| 新遊戲第一個畫面 | 132 | 3.35 ／ 2.48 ms | `SPOINT_012` 79 → 0；兩個 `SPOINT_017` 少 45 與 5 等；目視殘影消失，剩下的 `Y` 形小圖是遊戲自己的「繼續」符號（基底層也有） |
| 戰鬥佈陣（節點 71 點 (16,56)） | 2,089（通過的 2.3%） | 3.15 ／ 1.64 ms | 審查者量 362 幀平均 1,866（最大 3,401），78% 本來就被序號更大的戳記蓋過，可見的 98% 是 `BC32` 單位的單色區，改顯示同色的基底層（色差平均 0.0） |
| 標題 | 0 | 0.96 ／ 2.56 ms（雜訊） | |

量測時主機 load 約 4 至 11。審查者獨立實作的樸素版與本實作對拍 2,091 個重播取樣與 3,000 個隨機回合，差異 0；本實作的 `TestVerifyFlatMatchesNaive`、`TestVerifyFlatDropsGhost`、`TestVerifyFlatSkipsLargeStamps` 通過。

## 5. 前端（Xvfb 內的 GUI，confirmed 限於一次執行）

`tools/pkg/verify_hd.sh workplace/out/hr-play-hd workplace/hd-stage workplace/out/hd/gui`：Linux、cgo、Xvfb 1280x800。標題畫面顯示 HD 的 `GMAP`，標題選單與游標（無 HD，還原成基底層）正常；點「新遊戲」後的第一個畫面顯示 `FACE` 的 HD 肖像與地圖、對話框、錢數字。截圖 `workplace/out/hd/gui-title.png`、`gui-newgame.png`。這台機器在量測時負載 22 至 28，前端自動把計時器間隔降到 150,000（`docs/spec/003` 第 4 節）。

## 6. 效能（容器內，受主機負載影響大）

| 項目 | 結果 |
|---|---|
| 掛鉤對模擬速度的影響 | 冷啟動 90,000,000 步交錯各跑兩次（主機 load 22）：關 11.0 s、9.0 s，開 12.2 s、7.8 s。差異在雜訊內；規格估計每步多 0.2 至 0.5 ns |
| 合成時間，戰鬥佈陣 121 個戳記（105 個有 HD），每幀通過 93,795 個像素 | 單核（容器 2 核限額、平行化前）10.3 至 13.4 ms；平行化後（容器 4 核限額，主機 load 8 至 11）6.1 與 6.4 ms，其中基底 0.2 至 0.7、驗證 1.1 至 2.4、繪製 3.1 至 3.5 ms。不疊 HD（`-nohd`）4.5 至 7.1 ms |
| 加第 2b 步與面積上限後（容器 2 核限額，主機 load 約 4.5，每個畫面一次） | 標題 13.4 ms（`GMAP` 整張，1M 個 HD 像素）、新遊戲 5.0 ms、戰鬥佈陣 7.7 ms。標題超過 10 ms 的目標，低於 60 Hz 的 16.7 ms；審查者量到加第 2b 步前後驗證階段的差，戰鬥佈陣 +4.1 ms、標題 +7.0 ms（沒有面積上限時），加上限後各畫面約 +0.9 ms 或沒有增加 |

規格的目標是實際畫面平均 ≤ 10 ms。平行化後 4 核達標；單核與負載高時約 11 至 13 ms，低於 60 Hz 的 16.7 ms 但高於 10 ms：單核目標未達。壓力情境（512 個戳記）本實作沒有量。

## 7. 沒有驗證的項目

- 規格第 7 節：「被蓋住與還原」（`SPOINT_021`、`SPOINT_014` 的實際重播）、「游標」掃描 100 個位置、100 毫秒退回路徑、「3x3 等價」的 6 個情境數字：本實作沒有在這些情境重播。演算法與逐像素定義的等價由單元測試證明；情境的數字是審查者的實測。
- 「目視」：使用者尚未看過。HD 素材尚未驗收，`hd/` 未建立，發行包不含 HD 素材。
- `2378:1155`、`2E92:0414`（排除）、旗標非 0 與 x 非 8 的倍數的路徑（略過並計數）：未觸發或未驗證。
- 游標的 HD 圖是工具直接處理的結果，沒有人工修整，使用者尚未看過。
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
