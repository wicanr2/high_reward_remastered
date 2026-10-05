# M10 L2 字碼與字模原型收據

狀態：**DRAFT 證據，未授權正式 L2 語言包**。日期：2026-10-05。範圍是自訂碼的靜態容量、`1676` 的四種合成路徑，以及兩個簡體字在遊戲內的點陣顯示。原版檔案與改寫副本都留在 `workplace/`。

## 輸入與位址

- 十個原版輸入的檔名、大小和 SHA-256 以 [`source-inventory.tsv`](source-inventory.tsv) 為準。`MAIN.EXE` 為 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`，`CFONT.15` 為 `60e55cf73ba2eb8e83018e8a9b585e22524e730e240732adb5e746b7ed54d8db`。所有原版輸入唯讀掛載，合成副本和畫面只在 `workplace/out/`。
- IDA Pro 9.4 的 `ovr374:5B1E@0x749AE` 表示 overlay 段名、段內偏移與 IDA 線性位址。`ESPMES.MRG@0x3D7A` 等是檔案位移。`198C:05A2`、`16EC:1676`、`2F51:0423` 與 `lin:380CD` 是 dosgolem 執行期位址，不能互換。
- 探針使用 `workplace/dosgolem` 提交 `ac4d9b53b02311bea29ae056be547e6edf4c3c6c`、`workplace/out/probe` SHA-256 `8d4b18a505351d5b76c644ed54ca229b258d05480faa5ebd576842412d4a9c8e`。前端樣張使用 `workplace/out/bin/hr-play` SHA-256 `d4fe0612b834bc4340e7cfc3d43d4a8eb063292e00ab5f6a79710e5058161088`。重播均在無網路、非 root 的 Docker 容器；`hr-play` 畫面另在 Xvfb 擷取。

## 靜態保留集合

`tools/l10n/reservedscan.sh` 以 L1 解析器按項目對齊掃七個資料檔；以 IDA 嚴格字串匯出及非程式碼區的連續成對片段掃 `MAIN.EXE`、`OP.EXE`、`END.EXE`。`MAIN.EXE` 的 FBOV overlay 另由 `tools/ida_l2_overlay_codes.py` 在 IDA 9.4 的 139 個 overlay 段掃描，不能把 IDA 線性位址當成平面檔案位移。工具來源與輸出都核對 `MAIN.EXE` 雜湊。

非程式碼 overlay 共找到五段兩組以上的 Big5 型態候選，只落在 `ovr374`。例子 `B6 5A BB 5A C0 5A C5 5A` 以小端 u16 看是每筆加 5 的序列；另外四段也呈現此規律。**強推論**：它們是指標表，不是對白。尚未追到讀取者，因此掃描器保守把四個新碼 `E358`、`EC59`、`F159`、`F659` 也列為候選保留碼，不宣稱它們真的被畫過。IDA 輸出 `workplace/out/re-text/ida-l2-overlay-codes-v3.json` SHA-256 `ef13dcbef40322e2baeb37512d3943fc8d5e37d92e5b52542e8012970340e864`。

原本 102 個候選加上 overlay 新增四個，保守集合為 **106／3276**，可配置上限為 **3170**。這個數值是保守配置容量，不是原版實際使用字數。`workplace/out/re-text/m10-reserved-codes.tsv` SHA-256 `1c841eb8a768ec79051090f39371abc582da8c30a8f2811b26a3089ee015a1fe`；`m10-reserved-audit.json` SHA-256 `9c653d8d54b51bfc09ff6d592541a02a3007ff5b5adeba6c9cc44d6cba49cc95`，記十個輸入、IDA 匯出、Go 版本及容器識別。重跑 `tools/l10n/reservedscan.sh`；重新取得 overlay 匯出須在固定雜湊 `MAIN.EXE` 的 IDA 9.4 資料庫執行 `tools/ida_l2_overlay_codes.py`。

掃描器只把兩組以上的連續 Big5 型態配對列入寬鬆集合，單獨一組的未識別 bytes 不在這個靜態候選域內。IDA 對資料、程式碼及未識別位元組的分類也影響可見範圍。故 3170 是**依目前候選集合計算的上限**，不是已證明全遊戲可安全使用的碼數。原版實際使用集合仍未知；發現新碼須增補保留集合並使既有配置失效。

## 字模呼叫閘門

原版冷啟動 90M 步的 86 次字模呼叫見 [`WORKLOG.md`](../../WORKLOG.md) 的「M10 冷啟動字模呼叫抽樣」。本輪另從 bot 檢查點 `workplace/out/bot/snd-long-s2/ckpt/t06978.state`，SHA-256 `5db1237028a20009013e3770fb7d2605dc00ee9962f2154cb00dc59e8063585e`，按 [`025`](025-text-pipeline-evidence-4.md) 第 9 節的十二次點擊重播 40M 步。`198C:05A2` 有 35 次呼叫，沒有一個 `(lead, trail)` 落在可配的 `E0–F9` lead 與限定 trail 範圍。`workplace/out/re-text/dyn-l2-bot-font.txt` SHA-256 `88812e8ada886507ac2cd681f927af62d2b5b545a25171f5289469f039b14ec7`。**已證實**限於這段重播，不代表全部遊戲路徑。

再從兩個已完成兩遊戲小時遊玩測試的其他檢查點，各以同一個十二次點擊腳本重播 40M 步，記錄如下。路徑是「bot 已到達的原版狀態，加固定點擊」；不是連續兩小時逐次記錄。每列的呼叫引數皆無一落在可配範圍，零呼叫列尤其不能證明有文字繪製。日誌放在 `workplace/out/re-text/`；s2-b 沿用 `dyn-l2-bot-font.txt`，其餘五段為 `dyn-l2-bot-font-<代號>.txt`。

| 代號與檢查點 | 檢查點 SHA-256 | 指令起點 | 字模呼叫 | 日誌 SHA-256 |
|---|---|---:|---:|---|
| s1-a，`t06677` | `db8d1d3f6f6f9f9e2450a514a5512c94f03d1691ebd28b17901271cf70957089` | 17,220,620,029 | 61 | `4ca73e56821041245331323b476c213275ed152f84ac925a71f9d7ea8099e16d` |
| s1-b，`t06979` | `1fa63e9dd5fc94e85cf4642573139c7086a2d08327a653462b880703359b0ee5` | 18,851,483,647 | 0 | `6e457d4ce7474e3c2c5d4940454db5682660906001d1896ff4309b9876b83662` |
| s1-c，`t07282` | `7d612b3d520c88cd75cb647313597eeb0dd13ec89745cf63e76990b335ccf733` | 20,488,472,998 | 0 | `99144f275e90c1c02875a645ff4b240d86d284a9b814adf107fac8cf4d13f02a` |
| s2-a，`t06675` | `32e86ab739a9a7281dc3731f5388f170a04d0bf736d9995eaee5a4bc72d092e7` | 4,854,153,294 | 264 | `391ba4ebe301c56208b9f0b116b687e68b248d5353c090a24979f636aff0e7b6` |
| s2-b，`t06978` | `5db1237028a20009013e3770fb7d2605dc00ee9962f2154cb00dc59e8063585e` | 6,490,912,942 | 35 | `88812e8ada886507ac2cd681f927af62d2b5b545a25171f5289469f039b14ec7` |
| s2-c，`t07282` | `ab31f7906755e5399ee5123cbec2648e058ee15eb84d6d41a7666e998e127fba` | 8,132,196,577 | 0 | `1442d24f186140f55ac1183fe6136df6cb7664101bf7064d98bd3e4930cd0490` |

六段共 240M 步、360 次字模呼叫；加上冷啟動樣本，共觀測 446 次呼叫。這是抽樣覆蓋量，不是全遊戲字碼清冊。

負對照只在合成副本 `workplace/out/re-text2/roots/l2-gate-only/` 的第一句對白放一個 `E047`，其餘字沿用 `A4` 類。第 49M 至 49.6M 步的字模函式確實收到 `E047`：完整 106 碼集合沒有漏碼；故意移除 `E047` 後，閘門報出 `E047`。`dyn-l2-gate-only.txt` SHA-256 `1463dcaed4f0e1af6f4e1fd9ea565892d74a57b2a221f3558e7d4bce99e23b62`。這證明檢查方式能抓到一個已畫出的保留碼；真實長跑仍需更廣的玩家路徑。

## `E0` 成對路徑的合成實驗

`tools/l10n/make_l2_probes.py` 從 [`023`](023-text-pipeline-evidence-2.md) 的 T0、T3a 副本建立前三組變體，只改 `ESPMES.MRG` 一個固定長度槽位。`workplace/out/re-text2/l2-probe-inputs.json` SHA-256 `61f3c072ad283b5578b29bb1a5a4b9111df38e696a87d347dcc5dcedff91a528` 記每個變體的來源與輸出雜湊。前三組都由冷啟動點選「新遊戲開始」；第二句再於 49.1M 步點一次。第四組從上述 bot 檢查點重播，不冒稱冷啟動直達。

| 條件 | `A4` 對照 | `E0` 測試 | 結果與等級 |
|---|---|---|---|
| 第一行末尾的 `E0` trail，後接 `0A` | [`023`](023-text-pipeline-evidence-2.md) T1：`A4E0` 吞換行，只有 y 110 | `E0E0` 後仍有 y 110、126，字串偏移 1059、1066 | **已證實，合成**：`E0` lead 先吃自己的 trail，避免把 `0A` 多吃 |
| 第 16 字在寬 248 窗口的 `si=30` 起 | T3a 的第二行從偏移 1090 開始 | `E040…E05C` 的第二行從偏移 1091 開始 | **已證實，合成**：P 類 lead 讓第 16 字成對完成後才分行；畫面 `shot2-l2-boundary-e0.png` |
| 一個數字加 14 個成對字，再換行 | `1` 加 14 個 `A4` 對，下一行偏移 1089 | 同長度 `E0` 對，下一行亦偏移 1089 | **已證實，合成**：兩者均分行；`shot2-l2-digit-a4.png`、`shot2-l2-digit-e0.png` |
| 第二個 `%s` 名稱尾碼為 P 類 trail，後接一個自訂碼 | 用 `-poke` 把兩份常駐名稱副本的 `CE` 改為 `E0`，再接 `A440` | 同一受控狀態接 `E040` | **已證實，合成狀態**：展開緩衝含 `B9E0 A440`／`B9E0 E040`；兩者的 y 188、204 與偏移 1059、1084 相同。畫面與日誌在 `workplace/out/re-text/shot-l2-v{2,3}-nameP.png`、`dyn-l2-v{2,3}-nameP-shot.txt` |

第四組的改動位址是 dosgolem 執行期線性 `380CD`、`4AFBB`，時刻為載入檢查點後一步 `6490912943`。這是測試專用記憶體注入，只證明 `%s` 展開的此一邊界，不作正常玩家路徑證據。原版名稱及完整原版對白沒有寫進版控。

## Noto 字模原型

字型是 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`，SHA-256 `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`，Debian `fonts-noto-cjk 1:20230817+repack1-3`、內部版本 2.004。使用字面 2 `Noto Sans CJK SC`，Pillow 12.3.0、fontTools 4.66.1，容器 `yuan-analysis:1` ID `sha256:f9ea24396753f49d4c215763aa8726755041f0b523f93c9bdbffd76b8e358fca`。來源授權是 SIL OFL 1.1；隔離出的全文 `OFL-prototype.txt` SHA-256 `f47ac356aaafd53b53c6c784b3d63e265bf2dc9fe452d4ba5aee4b9b0bf51ca8`，含 OFL 標頭且不含 GPL 段。正式發行仍受 [`008`](../spec/008-ingame-text-localization.md) 第 3.7 節與 U5 約束。

`tools/l10n/glyph_prototype.py` 固定 13 像素、15×15 格、遮罩置中、不縮放、灰階閾值 128、第 16 欄空白，逐列打包為大端 u16，共 30 bytes。只把自造示例「简体」配置為 `E040`、`E041`，覆蓋使用者本機原版 `CFONT.15` 副本的兩格；另改寫一個固定長度對白槽位。來源、參數、工具與輸出雜湊在本機 `workplace/out/re-text2/SOURCE-prototype.json`，SHA-256 `0287ce47739996f9ebc51f50f90dbd608298c55554552954b411ec73bfa1fbef`。兩次在相同容器重烘，`glyphs-zh-CN-prototype.bin` 都是 `d67ba0b7e72367073ddb6e2950f131a951ec542ce3161012f095e276e2369b9c`，改寫的 `CFONT.15` 都是 `0cfb262f59bf399e9c51ab9b06ffb8fcfcc65913f905ed0821c8e0955ac0b1aa`。

另在唯讀 Docker 內獨立枚舉 3276 個可配碼，依 [`008`](../spec/008-ingame-text-localization.md) 第 3.4 節公式得到 3276 個互異字號，最小 9785、最大 13835，都在 13867 格之內。逐格比較本機修改副本與原版：只有字號 9785、9786 改變，其餘 415950 bytes 相同；兩格 15 列的 bit 0 全為零。這驗證本次兩字原型的定位與未修改格，不替正式補丁驗證器背書。

`dosgolem` 原版 theme 畫面 `workplace/out/re-text2/shot-l2-font-sc-original.png` SHA-256 `dd66b0c5697ae35ad25ca71c0bd441b80a9cdc7f55a79218f79c37746b625ecb`；Xvfb 前端正常點新遊戲的 HD theme 與切回原版 theme 畫面 SHA-256 分別為 `603455a20375c1ec7d69e86121877fb01e16189d843218ff20ecd07e4a2a7b3f`、`4cd8a6aca3feede2b3cd3d7c7ab02158f65d7db34187f45aa9c0db958e962e96`。目視兩字可辨，但筆畫小；旁邊原版硬編碼標籤仍用舊字模。四語 17 項候選的來源字面涵蓋統計另在 `workplace/m10-font-coverage.json`：簡中 200、日文 168、韓文 176、英文 32 個非白名單字元在 13 像素均無遮罩超格或缺碼。韓文與英文各有一個零墨跡字元，都是 U+0020 空白，L3 詞距尚未處理。

## 限制與下一閘門

上述字模原型只驗兩字，沒有建成五語語言包。`E0` 探針是有限的合成案例；bot 的六段 40M 步重播不連續，也未涵蓋所有玩家路徑。overlay 四碼的指標表分類仍是強推論。`COUNTRY.MES` 位移政策、韓文詞距、英文雙字母字模、四語譯文審閱與點陣補丁的發行授權仍未決。`docs/spec/008` 的 L2 需經獨立證據審查後才可升 READY；L3 與硬編碼字串仍另有閘門。此處不能寫「五語遊戲內文字已完成」。
