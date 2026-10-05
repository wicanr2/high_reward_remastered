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

## 四語首句的本機畫面原型

另以四語各自的 `ESPMES#121.0` 候選譯文建立**可丟棄**副本：`workplace/m10-l3-visual.py` 從唯讀原版複製素材，只改 `CFONT.15` 的新碼格與 `ESPMES.MRG` 群組 121 第一項及其位移表。英文逐字全形版在不改詞句的前提下多插一個換行；`workplace/m10-l3-pairs.py` 的英文對照版把相鄰兩個 Noto Sans CJK TC 的 10 像素英文字畫進一個 15×15 格，空白作為格內八像素寬度。兩個腳本與修改副本均在忽略版控的 `workplace/`；來源字型、各副本摘要與字集數在 `workplace/l3-visual-20261005/receipt.json` 及 `en-pairs-receipt.json`。這是 L3 設計原型，不是第 3.4 節單一 Unicode 字元對單碼的正式補丁契約。

研究探針在四份副本各從 `MAIN.EXE` 冷啟動，第 35M 步點新遊戲，於 49.6M 步截圖。畫面均為 640×480，原版硬編碼標籤仍是繁中。探針版本、原版輸入與 Noto 字型身分同本文件前述；截圖是修改原版資料的本機合成路徑，不算玩家端正常語言包驗收。

| 本機樣張 | 修改後 `ESPMES.MRG` 長度 | 畫面 SHA-256 | 觀察 |
|---|---:|---|---|
| `workplace/out/shot-l3-zh-CN.png` | 47715 | `d8380d6b7c8bc8464c8354a22969a4299816cf74fdedab60455bc63356282273` | 簡中首句可辨 |
| `workplace/out/shot-l3-ja.png` | 47721 | `872ebb4bba2fcee85278cd509cd7e0585ce7a63e9d688561df95fa6324c907f1` | 日文首句可辨 |
| `workplace/out/shot-l3-ko.png` | 47719 | `1b0e8cb4a9788d220b3d6e3cef223f9632eadfe4af9ab257a6f9cc7bf7792379` | 韓文首句可辨，詞距是一整個全形格 |
| `workplace/out/shot-l3-en.png` | 47744 | `ce8320d05649e0472000b0d3bc3fe6afc0470a60c1020d2fc13df328f064602a` | 英文逐字全形，字距過大 |
| `workplace/out/shot-l3-en-pairs.png` | 47721 | `f6a6328c2f86b3a303217d077c87998d417f862436159bc546f50e69fc12317a` | 英文雙字共格，字距接近一般英文；需要另一套配碼契約 |

正式前端對四份修改後的原版資料都報「`ESPMES.MRG` 大小不符」並拒絕啟動；這符合原版雜湊與檔案身分保護。上表只能由研究探針重播，不能當正式前端缺陷或完成證據。四語 17 項的**原有換行**若逐字使用雙位元組碼，簡中、日文、韓文的 16 句對白各行不超過 30 bytes，英文 16 句全部有超寬行；據點項目四語都有超過 70 bytes 的原有行。這是未經建置器自動折行的初測，不能據此斷定最終行數。韓文與英文候選各 17 項均含 U+0020，須在正式配碼時解決空白被原版路徑略過的問題。譯文仍是候選，尚未由使用者驗收。

若英文按每行相鄰兩字合併，一組占一個自訂碼，16 句候選的原有換行全部在 30 bytes 內；原有行分段的 17 項共需 227 種相鄰字組。`SP.MES#56` 的原有單行為 180 bytes。以單字間空白為折點、每行最多 70 個顯示字元試排成三行後，最寬 70 bytes，17 項字組聯集變成 230 種；16 句對白最寬 30 bytes，只有一句剛好碰上限。三行小於 `SP.MES` 的四行上限，字組 230 種低於依保守候選集合計算的 3170 個可配上限。此試排只核對候選的字元數、行寬、行數與字組集合，沒有跑正式建置器的折行、`1676` 或據點畫面。組合會隨折點變動，不能沿用單字配碼契約。使用者 2026-10-05 回覆「同意雙字共格」，選此方案作英文 L2/L3 方向；英文 17 項譯文仍是 `candidate`。

英文首句字模呼叫重播：dosgolem fork commit `ac4d9b53b02311bea29ae056be547e6edf4c3c6c`，`probe` SHA-256 `8d4b18a505351d5b76c644ed54ca229b258d05480faa5ebd576842412d4a9c8e`，原版 `MAIN.EXE`、`ESPMES.MRG`、`CFONT.15` SHA-256 分別為 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`、`e7cd0398746fafe9a0ba8b4c07de16662983b5071fa88595a48700fed22994d3`、`60e55cf73ba2eb8e83018e8a9b585e22524e730e240732adb5e746b7ed54d8db`。研究副本仍是 `workplace/l3-visual-20261005/roots/en-pairs`，第 35M 步點新遊戲，第 48M 至 49.6M 步攔 `198C:05A2` 的兩個參數，得到 38 次字模呼叫、29 種碼；首句配置的 12 種新碼全被呼叫，無額外未配置的可配碼。重抓畫面 SHA-256 `f6a6328c2f86b3a303217d077c87998d417f862436159bc546f50e69fc12317a`，與前次相同。日誌在 `workplace/out/l3-en-pairs-trace.log`，SHA-256 `f379392909cd40b273d7fc17054b37b54c4f353d8475a7292b4eee1c7e745145`。這只證明研究副本中的首句，未證明語言包路徑與其他 16 項。

17 項研究副本用 `workplace/m10-l3-pairs-17.py` 在固定的 `yuan-analysis:1` 容器製成，輸出 `workplace/l3-visual-20261005/roots/en-pairs-17`，收據 `en-pairs-17-receipt.json`。原版 `SP.MES` SHA-256 `f88fed9bbd525c5fb0972b2ef58718a59615b6fc92721c2ab83c5bd1cdd24b0c`；修改後 `CFONT.15`、`ESPMES.MRG`、`SP.MES` 的 SHA-256 依序為 `58dc44cfc78876af26068f55f9b5a4eda65d64a9facb5cc2aed406f668498876`、`13da13709609f033b92e0a78235d68451f34437bda308c28c49cf5217ff76e8e`、`c5726f1bde205eb1836e767e3671b89c81ac711db637d03651f5472bf5649c67`。同容器映像與固定輸入第二次在 `/tmp` 從零重建，三檔雜湊逐一相同；這只驗研究腳本的決定性，尚無正式受版控烘製器。獨立讀回比較：字模恰改 230 格；`ESPMES` 群組 121 恰改項目 0 至 15，後續 63 項原始內容相同；`SP.MES` 的 116 項只改 56，其餘 115 項相同；其他原版檔案逐位元相同。據點三行為 66、70、42 bytes，含換行與 NUL 的項目 181 bytes；16 句對白最長項目 96 bytes。

這次研究的映像 ID 為 `sha256:f9ea24396753f49d4c215763aa8726755041f0b523f93c9bdbffd76b8e358fca`；Pillow 12.3.0、fontTools 4.66.1。`m10-l3-pairs-17.py`、被它調用的 `m10-l3-pairs.py` 與共用的 `m10-l3-visual.py` SHA-256 依序為 `07064408563ac61e79471a303c4bc5d598fa52eb92ad505f844c31e53f9ce401`、`04c055e1411cb4769ca5544b4d7f1a569439010eb96fe69966d57d393bcb1d24`、`253b844faa1ed10d58c0bbc3cb5e8902ce17c2d5735370a21842eae6d686da00`。腳本與修改副本只在本機；重跑時以原版資料唯讀掛 `/orig`、專案唯讀掛 `/repo`、固定 Noto 字型唯讀掛 `/font`、研究工作區可寫掛 `/out`，在該映像執行 `python /repo/workplace/m10-l3-pairs-17.py`。

依 [`025`](025-text-pipeline-evidence-4.md) 第 2.1 節的冷啟動點擊序列重播此研究副本，`-steps 125000000 -click-premove 3 -click-polls 3`；第 109584229 步從 `SP.MES` 讀得 181 bytes，與新項目長度相符。第 100M 至 125M 步攔 `198C:05A2` 得 163 次呼叫，據點項目的 71 種雙字碼全部出現。畫面 `workplace/out/shot-l3-en-pairs-17-sp.png` SHA-256 `3dc457792f2b3d655e0232e79115b905c0e2b1d818c10650d4d082d98c8be331`，三行可見；固定介面文字仍為原版繁中。日誌 `workplace/out/l3-en-pairs-17-sp.log` SHA-256 `c51b6052285064d6765e8bc4b593ea8d4b25e831b468483a52b2e02e2e693e85`。這是修改原版檔的研究副本，不是 L0/L1 的 `LangDir` 語言包，正式前端仍會因原版雜湊不符而拒絕。

## 限制與下一閘門

上述字模原型有簡體兩字、英文首句與 17 項研究副本的據點畫面，沒有建成五語語言包，也沒有逐句畫面驗收。`E0` 探針是有限的合成案例；bot 的六段 40M 步重播不連續，也未涵蓋所有玩家路徑。overlay 四碼的指標表分類仍是強推論。`COUNTRY.MES` 位移政策、韓文詞距、英文雙字共格的正式契約與全部畫面、四語譯文審閱及點陣補丁發行授權仍未決。`docs/spec/008` 的 L2 需經獨立證據審查後才可升 READY；L3 與硬編碼字串仍另有閘門。此處不能寫「五語遊戲內文字已完成」。
