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

連續觀測工具入口為 [`tools/l10n/fonttrace.sh`](../../tools/l10n/fonttrace.sh)，研究準備與收據檢查在 [`fonttrace.py`](../../tools/l10n/fonttrace.py)。`build` 從固定 fork commit 的 Git archive 建立有觀測及無觀測的隔離副本；`run <名稱> plain|traced <hrbot 參數>` 逐次執行，`audit <名稱>` 比對字模碼與保留集合。副本、二進位及完整呼叫序列只放 `workplace/out/re-text/fonttrace/`，正式 fork 不改。觀測點是 dosgolem 執行期 `198C:05A2`，機器已送 IRQ 與 callback、尚未呼叫 `CPU.Step` 時比對，命中後讀 `SS:SP+4`、`+6` 的低位元組；新 Session 另記序號。研究工具只接受時長、種子、截圖／檢查點間隔與聲音旗標，不接受改原版路徑、語言包或記憶體注入旗標。短測須以相同種子比較完整機器與 DOS 狀態摘要，長跑須另有 `completed` 收據、到達記錄的目標時長、非零字模呼叫及保留碼檢查，才能形成證據。

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

可重現的開發側 DRAFT 預烘入口為 [`tools/l10n/bakeglyphs.sh`](../../tools/l10n/bakeglyphs.sh)，算法在 [`bakeglyphs.py`](../../tools/l10n/bakeglyphs.py)。輸入是折行後的 UTF-8 碼位清冊：簡中、日文、韓文欄位 `unicode`，英文欄位 `left_cp`、`right_cp`，每格為 `U+XXXX`。清冊不得重複，工具按碼位排序、跳過保留碼後配碼，輸出補丁五檔到本機 `workplace/l3-visual-20261005/patches/<名稱>/`。範例入口 `bash tools/l10n/bakeglyphs.sh en <units.tsv> <名稱>`。工具不讀原版 CFONT、不寫原版副本，也不接正式語言包；輸入單位清冊仍須由 L2 的來源與折行閘門生成。

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

目前五語各 17 項譯文已由使用者接受；繁中與英文試點的正式語言包及正常玩家畫面已有收據，英文接線見下節。簡中、日文、韓文仍只有字模原型，沒有建成正式五語語言包。`E0` 探針是有限的合成案例；早期六段 40M 步重播不連續；後續兩個種子各兩小時連續觀測仍未涵蓋所有玩家路徑。overlay 四碼的指標表分類仍是強推論。`COUNTRY.MES` 位移政策、韓文詞距、其他三語接線與點陣補丁發行授權仍有閘門；硬編碼字串另見 009。此處不能寫「五語遊戲內文字已完成」。

## 可重現的英文預烘與來源模型

固定的 `bakeglyphs.py` 與 `yuan-analysis:1` 容器，以本機 `en-pair-units.tsv` 的 230 組做兩次獨立烘製，輸出 `workplace/l3-visual-20261005/patches/en-bake3`、`en-bake4`。五檔逐位元相同；補丁身分 `f604fc1f65098bc19b0f3ca2052e1c78a4f09df62f39fc65f275b0a6120184c8`，字模 bin SHA-256 `4b7d554970c81e9710871975788a630c66cb204c2e5173913bc7a209345c6114`，字碼表 SHA-256 `1ed412b398659c2fc724b891bbc1b60bb835670daa1d2af50172cef09721cc6f`，SOURCE SHA-256 `c726bda3a69de67d6f77cb8f9e1472dddcb296021b104b775cc201547d57be54`。獨立逐筆檢查 32-byte 記錄、碼域、互異字號與 bit 0；套到唯讀原版的記憶體副本後，CFONT SHA-256 `58dc44cfc78876af26068f55f9b5a4eda65d64a9facb5cc2aed406f668498876`，與前述 17 項研究樣張逐位元相同。收據 `workplace/out/re-text/en-bake-roundtrip.json`。這完成該組光柵的重生證據，沒有建立正式語言包。

英文來源、折行與固定碼本模型在 [`enpairs.py`](../../tools/l10n/enpairs.py)，合成閘門在 [`enpairs_test.py`](../../tools/l10n/enpairs_test.py)。非 root 的固定 Python 3.12 容器中五項測試通過：來源控制碼／組合字拒絕、格式規格獨立奇數補白、固定字組重排與缺組拒絕、展開列數與 511 bytes、顯式換行及一般空白。17 項英文候選以既有 230 組碼本全部通過，據點仍為 66、70、42 bytes 三行；模型沒有修改候選表狀態。

[`enpair_budgetcheck.go`](../../tools/l10n/enpair_budgetcheck.go) 從固定雜湊的兩個原版資料檔用 L1 typed parser 取得真實項目與窗口，對模型的最終位元組重新執行 `budget.Check`，包含 `1676` 對抗模擬。17 個真實項目與四個格式規格合成項目共 21 個正例通過；這是位元組與模擬器檢查，沒有新增動態畫面驗收。獨立審查另造 `%s` 後直接換行的合成負例，同一 Go 檢查器回 `1676` 違規及非零退出，證明末端閘門不可省略。輸入與收據分別為 `workplace/out/re-text/en-pair-cases.json`、`en-pair-budget-audit.json`；各工具、收據、容器及 fork 身分在 `enpair-toolchain.json`。

文字審閱入口由 [`pilot_review.py`](../../tools/l10n/pilot_review.py) 產生，本機 `workplace/l3-visual-20261005/review/pilot-review.html` 對齊已接受繁中與四語各 17 項候選，附已有首句研究樣張。使用者 2026-10-05 回覆「全部接受這 68 項」，四語本機表各 17 項已記 accepted 與文字 UTF-8 SHA-256 前 16 碼；未經母語者審閱。接受譯文不代替字模、正式語言包路徑或發行驗收。審閱頁保留當時候選內容。

唯讀審查：`workplace/spec-review/fonttrace-review.md`、`bakeglyphs-review.md`、`enpairs-review.md`。主代理已核對報告、修正中斷插點與終點計數、原始 CRLF 檢查及 I/O 失敗清理，並將 SOURCE 欄名與折行排序回填 008 的 DRAFT。模型呼叫者仍須驗完整補丁與保留集合；L2 正式 Go 建置器、版本 golden、零採用列八檔 identity 與正常玩家語言包路徑尚未實作，不升 READY。

## 連續原版字模觀測

在固定 fork 提交 `ac4d9b53b02311bea29ae056be547e6edf4c3c6c` 的隔離研究副本，原版資料與保留集合唯讀；先固定種子再執行，不反覆重擲。短測 `parity3-plain`／`parity3-traced` 都是 210,662,140 步、11 次操作與六張畫面；操作與畫面一致，機器摘要 `bfb434f28d3da51720c6def6c9df251169c4a14e25a7e7a1042f80bf59b5e05d`、DOS 摘要 `18720493364d4fe3aa8af942aaec547b2d6403af12f8f0cc244d36ce33555203` 一致。觀測版記 182 次呼叫、96 種碼。這是觀測工具不擾動該短測的證據。

重跑入口：先 `bash tools/l10n/fonttrace.sh build`，再分別 `run long-s1 traced -game-hours 2 -seed 1 -sound` 與 `run long-s2 traced -game-hours 2 -seed 2 -sound`，最後 `audit long-s1`、`audit long-s2`。工具按每個 Session 核對 start／end、Steps 與字模計數，並核對 completed、終端標記、目標時長及輸入身分。正常退出後重開也有獨立 Session 邊界，不把最後 Session 的步數當成全程步數。原始日誌、輸入、摘要、audit 在本機 `workplace/out/re-text/fonttrace/<名稱>/`；匯總在 `workplace/out/re-text/fonttrace-longrun-summary.json`。建置收據 SHA-256 `361eed5717bda6f73171dd4390d0866db9a0c5f613e4dc649ee33eb24c4fbcd6`。

| 固定種子 | 遊戲小時 | 操作 | Session | 連續觀測步數 | 字模呼叫 | 不同碼 | 可配範圍內的實際呼叫 |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1.999986426584079 | 2767 | 2 | 39,325,405,901 | 44,964 | 712 | F9D8 26、E45C 14、F15A 6 |
| 2 | 2.0004593953162404 | 2702 | 3 | 39,334,747,270 | 48,044 | 703 | F9D8 42、E45C 17 |

兩組都是 completed，無 crash、freeze 或診斷 dump。種子 1 的目標時長以 PIT tick 截斷，與兩小時相差不到一 tick。總觀測 78,660,153,171 步、93,008 次呼叫、755 種碼；落在可配範圍的三個碼都已在保留 106 碼內，沒有新漏碼。**已證實**限於這兩條原版 bot 路徑，不證明全遊戲的孤立配對或未到達路徑；3170 仍是按保守集合計算的上限。

| 收據 | 種子 1 SHA-256 | 種子 2 SHA-256 |
|---|---|---|
| font-calls.tsv | `4d8bfe7b2ad87f7b674dd333b7dd8e317f9f88cf044edb95f9e419abe3364ab9` | `f931fd7cd9f2d1c8eb0758b479e87b0341a0b4c5676556a975a1a0abac4c0467` |
| font-audit.json | `04200130fba88c2e9a5e02832bbf5946053a3023ef2a38ab2a5128b2a5299b50` | `b9febe7fa50a1a371d6605a0164c9dfcbcf5fe2aeb0fcf90289f47d9bf67d46d` |
| run-inputs.json | `896289d434e102e7612452d6cece593ed82aafb93d5a14eb37b98b7b56ee6514` | `d70adc660b7f3055cdc1d1a626ae13930413ca38766744f1df35bd2ccaa0bb84` |
| summary.json | `4c8167a5e3de24eee43e814c16c620750edc94da6c6510e169d6e6e7c4292ce9` | `46182d0263c8d96803b7dcb1be85e29ecfddc67e4fa1344f1cc95ac3b3624945` |

真實呼叫負對照：將種子 2 的收據與保留清單複製到容器暫存，僅移除保留碼 F9D8；同一 audit 報 F9D8 漏碼並非零退出。原始清單及收據未改。另造截尾、少一筆呼叫與縮短時長的收據，都被拒絕。這證明完整性與漏碼偵測會報警。

兩個外層 bash 在等待 Docker 時，其入口檔被修改，返回後重新讀到錯位的 case，報語法錯誤；容器中的兩個遊玩程序已完成，終端收據與全部 Session audit 都通過。這是入口腳本操作失誤，不列遊戲缺陷。修正後 bash 語法檢查與 `stable-wrapper` 同命令短測正常退出，audit 通過；沒有重挑長跑種子。

## 五檔驗證原型與本輪窄範圍審查

[`patchcheck.py`](../../tools/l10n/patchcheck.py) 為 DRAFT 研究驗證器，不建包、不修改原版檔。可信保留集合獨立由固定量測摘要提供，補丁不能自行縮減集合；核對五檔、SOURCE 固定算法與摘要、單位排序、決定性配碼、保留碼碰撞、記錄及字碼集合一對一、字號與 bit 0，英文格的中欄也須空白。來源識別只作 provenance，不證明字形一定由宣告工具產生。

[`patchcheck_test.py`](../../tools/l10n/patchcheck_test.py) 在非 root 的 Python 3.12 容器，以唯讀 `en-bake3`、可信保留集合與原版 CFONT 執行六組測試。缺檔／多檔、符號連結、SOURCE 欄位與摘要、重算摘要後的深層記錄／碼本突變、錯誤可信集合、保留碼碰撞、非法碼位、bit 0 與英文中欄都被拒絕。零採用 CFONT 摘要是原版 `60e55cf7…7ed54d8db`；採用後是既有研究副本 `58dc44cf…6498876`。獨立公式逐格讀回 13867 格，所有未指定格與原版相同。測試記錄及 JSON 在 `workplace/out/re-text/patchcheck-test.log`、`patchcheck-audit.json`。

唯讀審查 `workplace/spec-review/l2-contract-current-review.md` 解掉可信保留集合的契約缺口，並發現標量 U+3000 的工具差異。已按語言對齊：標量可烘 U+0020／U+3000，英文只容 U+0020。日文單一 U+3000 從固定容器烘製，再通過相同五檔驗證；補丁摘要 `f0397391fa00c05fb8992861c24a66500d83a082fdc44c211adb56266583b49d`，收據 `patchcheck-ja-space-audit.json`。此空白往返只驗工具一致性，不證明韓文詞距方案或可讀性。

008 的本輪窄審把葉層契約與實作後驗收分開；正式建置器版本 golden、八檔 identity 與玩家路徑保留為後續閘門，未以它們尚未實作推論契約未知。本輪仍不開啟四語前端，亦不授權補丁發行。

## 正式字模與英文純函式驗收

008 第 3.4 節五檔／CFONT 與第 3.5 節英文 Prepare／budget accessor 經分別唯讀窄審升 READY，正式實作在 fork 的 `apps/hr/l10n/glyphpatch`、`enpairs`、`budget`。實作審查 `workplace/spec-review/glyphpatch-implementation-review.md` 與 `enpairs-implementation-review.md` 均無阻擋。這兩個葉層不建包，不開啟前端，不能代替 L2／L3 出口。

正式碼本在補齊標量空白規則後，`en-bake5`／`en-bake6` 兩次烘製五檔相同。典範補丁摘要為 `aea8dda978f9008abe79fb22d14227d546ad1f8a6d6f59db9d226bfae22b272c`，字模 `4b7d554970c81e9710871975788a630c66cb204c2e5173913bc7a209345c6114`，字碼表 `1ed412b398659c2fc724b891bbc1b60bb835670daa1d2af50172cef09721cc6f`，SOURCE `581f050b7f637c6fa91706ff5d9c2e5f0c793ebe0e88f18299215b4806c02359`。保留清單與 OFL 摘要不變。收據在 `workplace/out/re-text/patchcheck-current-audit.json`；算法來源更新改了補丁摘要，230 格字形不變。

獨立審查以公開 API 查全部 230 個單位，並用 Python 參考計算逐格比對全部 13867 格。零採用返回原版的獨立副本；正採用套全部 230 格，其他 13637 格保持原版。Go race、vet、Windows amd64 與 macOS arm64 編譯通過，沒有宣稱 Windows 或 macOS 執行通過。Unix 使用 NOFOLLOW 開檔；非 Unix 的開啟前後身分核對不能外推成同樣的並行改名／符號連結拒絕保證。

英文純函式補測真正的渲染列優先、字面位元組優先、511 scalar 正邊界、512 拒絕及精度零。共享格式 parser 原先容許小數點後缺數字的 `%.d` 等形式，與既有 READY 文法不符，已修正為拒絕；`%.0d` 保持合法。沒有新增原版語料格式。

真實來源 probe 的第一次運行，16 句對白通過而據點缺組。根因是本機 `SP.MES.tsv` 的英文項目被 CSV writer 包引號，審閱工具的 CSV reader 將其解掉，但正式 008 TSV parser 將引號逐字保留。已只修正一項封裝，使五語 85 項正式讀取字串皆與使用者接受的歷史 HTML 內容相同，原文 ID、來源摘要及接受的譯句不變；重新計該項 acc_sha。審閱工具改用 008 的 literal quote 與反斜線跳脫規則，不再用 CSV。歷史審閱頁保留未改。

修正後 `workplace/m10-prepare-probe.go` 從真實原版 Parse／Lookup 取來源與窗口，驗 accepted／acc_sha／src_sha，再調 Prepare。17 項皆通過，逐位元與獨立研究模型 fixture 相同；據點三行長度 66／70／42 bytes。再用 L1 LoadTable 核對五語各 17 項的接受與來源摘要，85 項皆通過。原版 CFONT 與零採用摘要仍是 `60e55cf7…7ed54d8db`，正採用仍是 `58dc44cf…6498876`。未產生正式語言包，未執行玩家前端。

| 本機收據 | SHA-256 |
|---|---|
| `workplace/out/re-text/enpairs-formal-pilot-audit.json` | `7d2aae4af79db663061acefb141ff403bb3963e721bc970af9c97dd419928e7e` |
| `workplace/out/re-text/tsv-normalization-audit.json` | `facf2b51d97f26e4e0317ae3f1213aa09d883825ee4c614663b7c2b0daae0466` |
| `tools/l10n/patchcheck.py` | `32d5dc54fba1f5f022ac9f53af5e53f778d7218e3b34619ba4fd7e2ea09e36bf` |
| `tools/l10n/patchcheck_test.py` | `3f4b4e69a94a46d1ba5f4aad0032fab351fe089f8deba60ec68c580b2e13c56d` |

以上 probe 用 Go 1.26.7、`eob-remake-go:1.26.7-ebiten2.9.9`，映像 ID `39d6e05c9abc60a566e376cde6afd29c24aa21c30eeec1e1fd92c8b16e62aa60`，原版輸入唯讀。收據只輸出 id、長度與摘要。譯文、補丁及原版副本均不進版控。

## 英文正式建包接線

008 第 3.2.1 節經獨立窄審升 READY，實作後審查 `workplace/spec-review/en-build-implementation-review.md` 無阻擋。fork 提交 `9684ad7`，備份 `engine/patches/0034-apps-hr-l10n-en-build-008.patch`。英文使用正式 Prepare、未折行群組鍵、一次五檔快照、原有採用政策與完整碼本套用；其他三語仍拒絕，不使用全語系開關推定支援。

L1 golden 保持原輸出。L2 golden 的五個固定變體只存合成字組接線的摘要，不含原版字模或語料；與契約識別及 L1 golden 共同導出建置器版本 `7ba662d3`。兩個嵌入檔固定 LF，避免跨平台 checkout 改變版本。含真實原版的七套件測試通過，獨立審查另跑 l10n／hrl10n 回歸及真實 CLI 冷建、verify、重用，均通過。

主代理的 `workplace/m10-build-probe.go` 在同 Go 容器唯讀載入原版、accepted 表及 `en-bake5`，實際建包後 Parse 七個資料檔：17 項與獨立研究 fixture 逐位元相同，所有未採用項目保持原版，CFONT 與前述 13867 格驗收摘要相同。第二次重用相同目錄及 manifest。全 keep 的英文表輸出八檔 identity，但補丁摘要仍綁定；缺字組拒絕且沒有新目錄或 `.tmp-*`，舊包仍有效。九個原版輸入前後相同。

| 本機建包收據 | 值 |
|---|---|
| `workplace/out/re-text/en-build-formal-pilot-audit.json` SHA-256 | `38be1fa325d8783c44dd18608fcb0d285dfc0a422d3308179353e458438435ea` |
| 輸入摘要 | `0ce391d1be19bb4fdd1bf7f086c97b887b9b81012c2b359308bc4deb457ddc45` |
| manifest SHA-256 | `b97d48c2897c8d68a91070186b29a227f5ce03f7dafab81fbed39e77d670796c` |
| 本機包目錄 | `workplace/out/l10n-packs/en-0ce391d1be19/` |

Linux、Windows amd64、macOS amd64／arm64 的命令列只驗編譯，後兩平台沒有實機執行。譯文表、五檔補丁及含原版位元組的包都留本機。

正式前端的正常玩家驗收入口為 [`verify_en_gui.sh`](../../tools/l10n/verify_en_gui.sh)，操作與有界程序清理在 [`verify_en_gui.py`](../../tools/l10n/verify_en_gui.py)。以 `bash tools/l10n/verify_en_gui.sh <新的標籤>` 在相同 Go／Xvfb 容器執行，輸出只放 `workplace/out/re-text/<標籤>/`，拒絕覆寫既有收據。原版、表、補丁與 fork 唯讀，測試用表與包只改輸出副本。自動收據只證明建包生命週期、回退及輸入；完整畫面另須獨立目視核對，上下兩個對白框都要看。

## 英文正常玩家前端驗收

008 第 3.2.2 節的同源探測只開英文，補丁取已選中的實際表目錄，沒有跨來源拼接。啟動與 F4 使用同一探測；F4 不即時替換遊戲內文字。英文零採用仍標為 en 的驗證包，不誤報另一語言。Linux 全套 race、最終英文窄測與 vet 通過；Windows amd64 及 macOS 雙架構 universal 只驗編譯。

fork 提交 `1c8128c`，備份 `engine/patches/0035-apps-hr-play-en-l10n-008.patch`。前端實作與建包分開提交，重建順序沿用 AGENTS 第 4 節。

實作後唯讀審查 `workplace/spec-review/en-frontend-implementation-review.md` 無阻擋，獨立相關前端回歸與五項 CID 清理負例通過。審查者未代替主代理重跑 GUI 或目視畫面。主代理核對實作、審查與玩家收據後，008 第 3.2.1／3.2.2 只在此英文窄範圍升 CONFORMED。

主代理以固定原版輸入和 accepted 英文表，從前端冷啟動正常點新遊戲，再逐句點擊至據點；沒有載入研究 state、修改存檔或記憶體。`en-gui-v3` 六階段乾淨退出。完整 `dialogue-00.png` 至 `dialogue-15.png` 已逐句目視確認與接受表一致，文字在框內。對白 #121.3、6、7、10、14 使用下框；最後 #121.15 使用中央第三位置，不能只裁上框判定漏句。`location-info.png` 的據點為既有 66／70／42 bytes 三行，內容可見。

同次驗收另確認重開重用、舊 CFONT 被測試副本竄改後另建序號包且舊包不變、缺補丁及補丁 SOURCE 無效時回原版。F4 選日文後，下次啟動讀到日文偏好，沒有日文包時回原版；不是即時切換成功。所有 screenshot 與終端 log 的摘要重新核對相同。

| 本機驗收項目 | SHA-256 |
|---|---|
| `workplace/out/re-text/en-gui-v3/receipt.json` | `cd301ab704a0e3a829654fb84e04bed438bd607fe8e606b1a4c4aa30792780f0` |
| GUI 實際執行檔 | `84ebee772c86f946d0c74840f6cf0ca0ad97f98b1b6c4383695121d8cdf76256` |
| 中央末句完整畫面 | `08fd8a3271247ee7145af8ac73b0e40cb14df0b69f9c96f7f822c02473f2bcf8` |
| 據點完整畫面 | `5871240f102ca5fa11b9ab2c0b295187dd344f5fc303f1b04dc4289b36cba7a5` |
| v3 執行時的 shell 入口 | `61cb544566ee20c3416d037667403e912b7a7f182e9ab9ced5d3aa343461edaf` |
| 補容器 ID 清理後的最終 shell 入口 | `6c8ac00895bfeccfeb88bbbe0f4276ae766836ca5292e68f8e9a4d9f8af38838` |
| 最終 Python 操作器 | `5f5c3229dc1442a64bebb2719fc554ad0a935729e4336163aa19c23eb65e013b` |
| accepted `ESPMES.MRG.tsv` | `031c3522fc904cef6189fa931a159abfb9bd8c954d25e9ce15b33d968af559cb` |
| accepted `SP.MES.tsv` | `bb074cececabbf7786f6495730180d3a92cc1b3a8618a04585d04fdbd3b0ee3d` |
| manifest 表整體摘要 | `3bc3dc769c781cf009f2809e847aa80e3d4c0a3f4f92cf3209cab039622c0072` |

v1 的相同座標 `xdotool mousemove --sync` 等待逾時，已修正。v2 容器已完成六階段，但主代理在 Docker 等待期間改入口，外層 bash 重讀檔後報 EOF；v3 固定入口不再修改，乾淨重跑通過。這些列操作環境問題。v3 收尾後另補 EXIT／INT／TERM trap，以本次 `docker run --cidfile` 寫出的完整容器 ID 確認擁有權，不能僅按名稱清理。語法及窄審另核對，不以此宣稱又重跑全 GUI。

Windows／macOS 沒有實機玩家收據；沒有測本輪語言包的全遊戲內容、音訊或存檔 A/B。來源與補丁使用與上節相同身分、Go 1.26.7 及容器映像。五檔已安裝到本機 `l10n/en/glyph-patch/`，語言包及本次畫面只留 `workplace/`，沒有納入 Git 或 Release。

## 簡中與日文標量接線的字模基準

008 第 3.2.3 節經獨立窄審無阻擋，升 READY。標量接線使用每項局部正反表與 Unicode 15 的 `unicode.IsPunct`，保留既有白名單、格式、typed 窗口及折行前群組一致性。簡中與日文的各 17 項接受表沒有 U+0020 或 U+3000，普通半形空白在這個窄契約中拒絕；韓文仍需詞距定案。

`workplace/m10-scalar-units.py` 從正式 TSV 的接受文字與摘要產生非白名單單位，簡中 198、日文 166。既有 `bakeglyphs.sh` 各烘兩次，使用上節固定 TTC、OFL、Pillow 12.3.0、fontTools 4.66.1 與 yuan 映像，分別選 SC 字面 2、JP 字面 0。兩次五檔逐位元相同。Go 葉層獨立探針 `workplace/m10-cjk-leaf-audit.go` 驗 Load、全部 Lookup、13867 格完整 Apply 與零採用 identity；收據 `workplace/out/re-text/cjk-leaf-audit.json` 的 SHA-256 為 `42da4ed18b70b3161325798d82163b0170638919d8b812725241134eb6c13761`。

| 項目 | 簡中 | 日文 |
|---|---|---|
| 單位表 SHA-256 | `886344709ceaed7dda5879d887154abb379561e392020a682e1f374affca1615` | `3a84d6d808b153019160e5b2fd9a7f756920dd70808127844a62525c0573da79` |
| 五檔補丁摘要 | `8e3a81653c5d8b98c113d2894172d33c4e95869462b6eccecec9ac8d551b265e` | `5b8654a03f52e61d07ccea3c45788f293fb30fe1da1059448f65cbc7d55e8d59` |
| 正採用完整 CFONT SHA-256 | `28e157806b0699ea39ffd2dfc9957a42bb1548a888bc2c9baa2b33dbf48b8ef7` | `a582c8bad663641a09c5afbe4f41c53078ed579ab69651910915d08cc299a3eb` |
| 本機輸出 | `workplace/l3-visual-20261005/patches/sc-pilot-bake1/` | `workplace/l3-visual-20261005/patches/ja-pilot-bake1/` |

第一版獨立探針把 CFONT 當平坦 Big5 格表，報索引不符。改用 006 的原版字號換算後，以同映像及輸入乾淨重跑通過；正式補丁與程式未因此改動。此節只證明字模身分、可重現性及套用，建包與正常玩家驗收另記。

## 韓文詞距可丟棄原型

研究報告 `workplace/spec-review/ko-space-probe-report.md` 與完整八張畫面保存在 `workplace/ko-space-probe/`。來源為上節同一 MAIN、CFONT 與 ESPMES；固定 probe SHA-256 `8d4b18a505351d5b76c644ed54ca229b258d05480faa5ebd576842412d4a9c8e`，工具與位址基準沿 020，沒有載入 state 或注入存檔、記憶體。四份研究副本只改 CFONT 的三格與兩項合成對白，原版 148 個輸入前後摘要相同。這些副本不是正式五檔補丁或已接受 17 項的玩家驗收。

| 分隔 | 空白邏輯前進量 | 兩字白色墨跡間隔 |
|---|---:|---:|
| 無空白 | 0 px | 5 px |
| 原始 0x20 | 0 px，複製時被略過 | 5 px |
| 0x21 | 8 px | 13 px |
| 雙位元組零字模 | 16 px | 21 px |

confirmed 範圍限 `ESPMES#121.0`、`#121.1` 的 01A3 合成對白。行尾試驗先放 15 個雙碼字，8／16 px 空白兩案都使下一字換行，但分別耗一／兩位元組；不外推其他窗口或 1676 相位。白色墨跡以原始遮罩與右移一像素聯集驗完整 PNG，八圖逐像素相同。第一版量測未套這個樣式，修正研究腳本後核對同批原始圖通過，未挑選新畫面。

對照圖 `workplace/ko-space-probe/comparison.png` SHA-256 `9109bda2b57d2698c9e0a5dd3f62f628df4e34e0fbca6a2a9fd4de13503adb2b`，量測 `measurements.json` SHA-256 `cd7ce43240551419f06044f995e2dc728e7a9eaa012e83111fb8de7e8c21abb6`。已向使用者展示 8／16 px 兩案，正式詞距待決；未因此開放韓文 production。

## 簡中與日文正式建包及正常前端

第 3.2.3 節實作後獨立唯讀審查 `workplace/spec-review/cjk-integration-implementation-review.md` 無剩餘阻擋。來源分類、格式、typed 窗口、折行前群組、完整碼本、單次補丁快照、零採用八檔、採用政策、同源前端與 F4 下次啟動均有窄測。Go race、vet 與純 Go 命令列 Linux／Windows amd64、macOS 雙架構編譯通過；實機執行不在聲明範圍。

建置器版本 `74ef5533` 綁 `hr-l10n-l2-scalar-v1`、原 L1 golden 與追加兩語的 L2 golden。L1 SHA-256 保持 `a96d619d9e50a273c046f793f0f4c053ff20d0384b25d57033644593a465a7e7`，英文 golden 前綴保持 `508566847f68024a5a5693368772ac9de6c59eb8378ac6277d04b5561c439b5f`；英文資料與 CFONT 輸出不變，版本與包摘要自然改變，不覆寫舊包。

主代理獨立探針 `workplace/m10-cjk-build-audit.go` 將每個已接受 scalar 查固定碼，按來源 Unicode 標點交既有預算層，再獨立 Parse 實際包。兩語各 17 項匹配，所有未採用項目保持原版；CFONT 與前節完整格驗收相同。這份預期折行共用既有 budget，沒有另冒稱原版布局 oracle。重用、零採用八檔 identity、缺字無新包或暫存、舊包仍有效與九個原版輸入不變均通過。

| 本機建包項目 | 簡中 | 日文 |
|---|---|---|
| 包目錄 | `workplace/out/l10n-packs/zh-CN-342a6f7641db/` | `workplace/out/l10n-packs/ja-9717931b76e6/` |
| 輸入摘要 | `342a6f7641db4a4f27d41886c4aef88a507d9d798e9e813106d64baa68f282dc` | `9717931b76e6222ef36d11eb140b953d3c7c1fa6cd03b9accbcc56c2959f8da3` |
| manifest SHA-256 | `7c74590fa40507f0e87147e97fa0951c9d018b201ba8f8e5a5cc7b4d551395f2` | `87ef792f5d2dec8113cc0df941f8aedd811f95bbd829f23ec5d56a3a73cfc352` |
| GUI 收據 SHA-256 | `fa2ba23bee603df08983d6f437801a4bac73b31e600ca87c10ccc466f3e819d5` | `be9e0fc15f39634bfb626cb73822af99e2e6401dd2c42b9803daaf462cafb41b` |
| 據點完整畫面 SHA-256 | `737105e4e30b207e074df84e08d8b7d901e263d5941923dd875f70ec7741d2a2` | `f5ba93ddccade955cff57c38c7336c51c8fbb5ee733640617df79c4298f1ba6b` |

建包收據 `workplace/out/re-text/cjk-build-formal-pilot-audit.json` SHA-256 `d15fca643d50d803e7c74a311b0fca98f979be86fcf9a0ab166f57543a185ad6`。正常 GUI 入口仍是 `bash tools/l10n/verify_en_gui.sh <新的標籤> [代碼]`，可用 en、zh-CN、ja，省略代碼保持英文舊用法。此次 shell／Python SHA-256 分別為 `74e8a0c90e39269ba16a076b13f62d10d6437a5f9a313c4a676a0f99ddc3a133`、`c4bb1c2a8d6782c3bf6f36aa80cf9d2fd2fcf4330f77e58ae9516d00da79effd`。

`sc-gui-v1`、`ja-gui-v1` 以相同 GUI binary SHA-256 `af7dfdb814d7fca68b6b0bdb66175e8808b2fec0cd0a53e077729e2567dd0ef0`，各自從正常前端冷建包、新遊戲逐句點到據點。沒有跳關 state 或記憶體注入。主代理逐張看全部上下框及中央末句，34 項與接受文字相同且在框內，據點各兩行 60／60、68／68 bytes。完整畫面及附接受文字的審閱拼圖在各 GUI 目錄的 `visual-review/`，不入版控。

每語六階段還驗重用、破壞測試包 CFONT 後另建序號且保留舊包、缺補丁／無效 SOURCE 回原版。F4 分別選韓文、繁中後，下次啟動讀到偏好；隔離測試根沒有該語言表，按原規則回原版，沒有即時換字。主代理另重算每語 34 個畫面及終端日誌摘要，皆與收據相同。容器清理另經七項 mock 驗證，完整 CID 加本次容器 Name 同時相符才刪除，無效、缺席、inspect 失敗或其他名稱皆不刪。

正式五檔已安裝在忽略版控的 `l10n/zh-CN/glyph-patch/`、`l10n/ja/glyph-patch/`。此節限本機試點與 Linux 正常前端；不外推全遊戲、全量翻譯、長跑、母語可讀性、存檔 A/B、Windows／macOS 實跑或發行。

前端補充驗證 `workplace/spec-review/cjk-play-platform-verification.md` 與 `workplace/out/re-text/cjk-play-platform/` 保存全套 race、vet、Windows PE 與 macOS universal 切片收據。Windows、macOS universal SHA-256 分別為 `37939d2113a1dbc01b1c63aa33ead43a86309719e07077112e310c3759730b73`、`313997f1b8e7330a318d2b2280480e036a71142ffda0ffbe8cdec4bd3de0bf29`。Go 映像缺 `file` 只讓末段結構 wrapper 回 127，沿用 osxcross 的 `file` 與獨立 PE／fat 解析補驗通過，沒有改產品或重編挑結果。

主代理讀完審查及平台報告後，只修正三處舊英文限定註解，並替沿用名稱的 golden 測試補三語範圍說明，沒有改行為或 golden。fork 建包與前端分別提交 `935e6a5`、`ff9459d`，備份 [`0036`](../../engine/patches/0036-apps-hr-l10n-scalar-build-008.patch)、[`0037`](../../engine/patches/0037-apps-hr-play-cjk-l10n-008.patch)。主代理按上述實作、正常玩家與目視收據將第 3.2.3 窄範圍升 CONFORMED。本機最新開發版 `workplace/out/bin/hr-play` SHA-256 `b0c040c417f6a2f53a7d9e044eead269b2f40d770b3f8769c85d685345ecc5ad`，與 GUI 執行檔的差異包含提交及建置身分，沒有重宣稱一份新 GUI 收據。


### 韓文 8 px 定案與正式接線閘門（2026-10-06）

使用者選「韓文8 像素」，普通 U+0020 採 raw 0x21，字面驚嘆號另取 Noto 雙碼。原型時點的待決記錄保留；正式接線依 [008 第 3.2.4](../spec/008-ingame-text-localization.md) 窄契約，經獨立唯讀審查無阻擋後升 READY。本節不外推全遊戲或發行。

#### 固定韓文字模葉層

`workplace/spec-review/ko-glyph-audit-report.md` 及 `workplace/out/re-text/ko-leaf-audit.json` 是本機收據入口。主代理已核對報告與 JSON；收據 SHA-256 `67deba8ff58dc68db99d4fbee1ae645b1f60a8f014733a36ffd844d5c7166b0a`。17 項來源與接受摘要均吻合，173 個單 scalar 清冊排除 101 個普通空白，字面驚嘆號配 `E040`，普通 U+0020 沒有 Lookup。

兩份五檔 `ko-pilot-bake1`／`ko-pilot-bake2` 逐位元相同。固定 Noto Sans CJK KR 2.004、face 1、13 px、mask-center-floor、閾值 128，字型及 OFL 身分沿前節；Pillow 12.3.0、fontTools 4.66.1、Unicode 15.0.0，image `yuan-analysis:1` 的 ID 沿本文件烘製器契約。五檔 Load、Lookup、全 13867 格 Apply 及零採用 identity 通過。原版清冊 148 檔於製作前後逐檔核對，全部不變。這是檔案與索引的 confirmed 驗證，沒有原版韓文語句 oracle。

| 產物 | SHA-256 |
|---|---|
| `glyphs-ko.bin` | `3ea2fb22c48570a6266aae37e712661c1d61805716fa58cfcfd102b2c8d4a8ff` |
| `charmap-ko.tsv` | `f46d9d3bdb28297c9ebec5bc039683c58d4b12998350e74a438dd10f638971ae` |
| `SOURCE.txt` | `08c6b90d7c98f376861744e712b60efe8662943a00a0254eea2c6d705e03ebf1` |
| 五檔補丁摘要 | `8206a80bb994c8dea10bcfa36c2279041313e5a7aeb58f8f219d6de60e5cee04` |
| 完整 CFONT | `4efd04bb03cfbd5baba81d82c635c4a620292fd30c3b488f9eb2c6369a6e6e55` |
| `units-ko-pilot-v1.tsv` | `77ab3708bdef3c96c8c0ac308076c852063233434e9befe45d851370e7f2d192` |

重烘入口：`tools/l10n/bakeglyphs.sh ko workplace/out/re-text/units-ko-pilot-v1.tsv <未使用名稱>`，順序呼叫兩次，不覆寫舊收據。清冊工具 `workplace/m10-ko-units.py` SHA-256 `0a2ad94ac6ae0dd40fb4683ac295d498ab88b0e5f8e3e5287253eb59d7d71d1b`；完整格驗證 `workplace/m10-ko-leaf-audit.go` SHA-256 `61a027c592846ccd667722ff23a987d514142da7498df48b4a1272066de87d27`。Go 容器、唯讀掛載、離線 module cache 與入口命令同本機報告。

#### 正式韓文建包與正常前端

本機實作報告 `workplace/spec-review/ko-build-implementation-report.md`，獨立讀回收據 `workplace/out/re-text/ko-build-formal-pilot-audit.json`。主代理的 `workplace/m10-ko-build-audit.go` 不呼叫 production Prepare，逐字查固定碼本並明示來源 U+0020 轉單碼 `0x21`，再按 typed 原項目取窗口及末端預算。逐項空白數與最終輸出相同，合計 101；17 項讀回、未採用文字、完整 CFONT、零列八檔、摘要、重用、缺字無包及暫存、舊包與九檔原版不變全部通過。據點折為三行 64／52／41 bytes，所有對白每行不超過 30 bytes。沒有採用原型修改過的原版副本。

| 身分 | SHA-256 或值 |
|---|---|
| 建置器版本／契約 | `55af19f2`／`hr-l10n-l2-ko8-v1` |
| 正式韓文輸入摘要 | `e2b7e05d461846e61985efa62cfd53a3b98091716a06c762447dcd2e0b79c01b` |
| manifest | `5ceda5a11959e067052937e2a555be206eb52c8696cfc13ba502ee28b64c2113` |
| 獨立建包收據 | `291f27d766b70682ebfa4589b051819d2926f48f7ccd8cfb1b2a7b67b8eeb842` |
| 獨立讀回探針 | `010de08df7ef5edcf21f423ffc29465e2230914cf50a9ea36371060a73f3891d` |
| L1 golden，保持 | `a96d619d9e50a273c046f793f0f4c053ff20d0384b25d57033644593a465a7e7` |
| 原十五段 L2 golden 前綴，保持 | `c0dabd8867ca99a6b41450c25e9443e93d97ab4d02fbb4c9f0e858afa94ffd5a` |
| 新 L2 golden | `43289a2bfddc96a24c0e48c410232f0383740b6601bc3b0c17f818f413e7441c` |
| `ko-gui-v1/receipt.json` | `314851f395611be740d3a0c40064e8eff136fdbebdd62364ee0fe98bcc9863d6` |
| GUI 執行檔 | `99c5d80e70b038ddeb74a64d21c48298da3eb3ed9fc421a3600f00d9b3f4c5ef` |

正常 GUI 入口 `bash tools/l10n/verify_en_gui.sh <新的標籤> ko`，輸出在 `workplace/out/re-text/<標籤>/`。`ko-gui-v1` 六階段乾淨退出：冷建 17 項、新遊戲全部對白與據點、F4 下次啟動選英文但無表、重用、損壞包保留另建 `-2`、缺補丁及無效補丁回原版。F4 不改本次已啟用包。28 張 PNG 加六份終端 log 的 SHA-256 逐檔重算吻合。完整畫面與接受表並列頁在 `ko-gui-v1/visual-review/page-1.png` 至 `page-5.png`；主代理逐張核對上、下與中央框的 16 句及據點三行，字形與空白可辨、字面驚嘆號正常，沒有裁切。接受狀態沿使用者先前確認的譯文，未經母語者審閱。

建包、budget 與 CLI 全回歸、race、vet 通過，含真實簡中、日文、韓文各 17 項及原有英文／繁中 golden；前端全套、韓文窄 race、vet 通過。獨立審查最先捕捉前端的舊支援守護仍排除 ko，修正後同工具鏈乾淨重跑。正式包探針第一次在 Docker 啟動前就因不存在的掛載來源被 `test -d` 停下，改用既有 `out/re-text`；GUI 摘要核對第一版誤將 28 張畫面加六份 log 當成 34 張 PNG，改按實際清單重驗通過。兩項是驗證腳本問題，沒有變更產品迎合檢查。

平台報告 `workplace/spec-review/ko-platform-report.md`，收據 `workplace/out/re-text/ko-play-platform/verification.json` SHA-256 `5cd57161af674d262088bfa188e5813e2d0d54f4495259d7ab5af6d58b58ff2b`。Windows amd64 前端與四目標 CLI 編譯／結構通過；macOS 前端兩架構及 universal 切片逐位元相同，SDK 15.5、最低 11.0。Go 1.26.7 純 Go macOS CLI 最低 12.0，尚未統一發行下限。3016 個來源檔前後不變。沒有 Windows／macOS 實跑，不重建 Release、不宣稱完整 L2／L3 或全量多語完成。

已驗五檔裝入本機 `l10n/ko/glyph-patch/`。譯文、補丁、語言包、收據與畫面只留忽略版控的本機路徑，不加入 Git 或發行包。


獨立終審 `workplace/spec-review/ko8-integration-implementation-review.md` 已核程式、golden、字模、正式建包及 GUI／平台收據，無未解阻擋。主代理只將 008 第 3.2.4 窄範圍升 CONFORMED。fork 提交 `c1fbbe8`、`48ae45f`，備份 [`0038`](../../engine/patches/0038-apps-hr-l10n-ko8-008.patch)、[`0039`](../../engine/patches/0039-apps-hr-play-ko-l10n-008.patch)，不推送 dosgolem 公開上游。


本機最新開發前端 `workplace/out/bin/hr-play` 由乾淨 fork `48ae45f` 重建，SHA-256 `e02ad28bf46d3576359555381f70f52e45e6b132a317ee3dbf6d48b4e2e2c307`。與 GUI 執行檔的差異含提交與建置身分，不將這次重建當成新 GUI 收據。
