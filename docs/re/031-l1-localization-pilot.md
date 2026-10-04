# 031 M10 L1 繁中 17 項試點收據

日期：2026-10-04。狀態：17 項繁中試點已由使用者接受並標為 `accepted`；M10 其餘工作仍在進行。第 1 至 4 節保留首輪候選階段的收據與限制，第 5 節記錄樣張勘誤與驗收後的現況。本文只記 id、雜湊、數值與路徑，不收錄原文、譯文或畫面。原文與樣張只在 `workplace/`，譯文表只在被忽略的 `l10n/`。

## 1 輸入與工具

| 項目 | 固定值 |
|---|---|
| 原版 `MAIN.EXE` | SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e` |
| 原版 `ESPMES.MRG` | SHA-256 `e7cd0398746fafe9a0ba8b4c07de16662983b5071fa88595a48700fed22994d3` |
| 原版 `SP.MES` | SHA-256 `f88fed9bbd525c5fb0972b2ef58718a59615b6fc92721c2ab83c5bd1cdd24b0c` |
| 其餘六個建置輸入 | 檔名與完整 SHA-256 見 `docs/re/source-inventory.tsv`；`hrl10n` 以 `apps/hr/runtime/required.tsv` 驗證九個原版輸入，包的 manifest 也逐檔記錄 |
| dosgolem fork | `workplace/dosgolem` `hr` 分支 `ac4d9b53b02311bea29ae056be547e6edf4c3c6`；重新編譯的 `probe-l10n` SHA-256 `f02e9c67e146d32d800aba5e3b71a9e2c88d775e10806b4a3a129cd625e1ac7c` |
| 建置器 | `workplace/out/hrl10n` SHA-256 `0901e5e1f909eaf18a80b2dcf4066caf3fd5ff4c470c0afcec198ce63415f914`；內嵌版本 `a96d619d`；重建探針使用 `golang:1.24-bookworm`、`GOPROXY=off` |
| 原文匯出 | `workplace/l10n-src/pilot-17.tsv` SHA-256 `321fa57750ff72eb4eb5669b72e72777c7645970a1e4a89b63c04f2bda2ab695`；CP950 逐項解碼與專案 `golang.org/x/text/encoding/traditionalchinese` Big5 解碼逐項相同，17／17 |
| 候選表 | `l10n/zh-TW/ESPMES.MRG.tsv` SHA-256 `32f400e3c446e50a60c96906e89da5074dbef4795b1bf096e76aa07f3598987e`；`l10n/zh-TW/SP.MES.tsv` SHA-256 `8bd9634c53533ddbcf0cabd9531d8e2800dd3437f4a3b34a334d10f085a11587`；全 17 列為 `candidate` |

原版檔案以唯讀掛載。譯文表與語言包不進版控、不進發行包。2026-10-04 使用者已授權整個 M10 原文交由 Codex 處理；本輪沒有送往其他服務，也沒有讓 Docker 使用網路。原始位址：`ESPMES#121.0` 檔案位移 `0x3D7A`，`#121.1` 為 `0x3D90`；`SP.MES#56` 為 `0x195F`，詳見 `docs/re/024`、`025`。下列 `148B:0464` 與 `16EC:1676` 都是 dosgolem 執行期 `segment:offset`，不是 IDA 線性位址。

## 2 建置與驗證

以 `hrl10n build -code zh-TW -mode table -orig /orig -l10n /l10n -out /out/l10n-packs/pilot -with-candidates` 建包。第一次建置檢出 3 項字集外用字（`#121.7`、`#121.9`、`#121.14`）；改用原版字集可表示的詞後，建置器採用 **17 列**、0 違規，輸入摘要 `bc685c0433f9ca227619538ea5e05bdd5eb43d99cd1d3d3a038faece99802644`。語言包在 `workplace/out/l10n-packs/pilot/zh-TW-bc685c0433f9/`，manifest SHA-256 `bac82fffb581fcce4959b98d6348284b7d6a76f2a1b01d70bd4ae7da814e4712`。

`hrl10n verify -digest <上述輸入摘要> -orig /orig <包根>` 通過：8 個檔案、table 模式、採用 17 列。另將包複製到 `workplace/out/l10n-packs/pilot-tampered/`，只翻轉 `files/ESPMES.MRG` 一個位元組；相同驗證以 `file-hash: ESPMES.MRG` 非零退出。對照用 identity 包的輸入摘要 `7b8a4c0c2f857f2c98e8fb9c34e3dc3b6fba8dba20991df80c403e7afca4113a`，manifest SHA-256 `ac84830e64ffc962f4b33f3a7b7d7a21201757f02d39c61352eebd0c0f96e5ac`，建置後也通過同樣的 `verify`。

## 3 正常冷啟動路徑

兩包都先通過 `verify`，再以重建後的 `probe-l10n` 指向各包 `files/`。同一輸入：第 35M 步點新遊戲；第 49.4M 步起，每隔 2.6M 步點對白一次，共 16 次；第 97M 與 103.5M 步點據點與選單項目。指令寫在 `workplace/out/re-l10n-pilot/clicks.txt`；`-click-premove 3 -click-polls 3`，跑到 125M 步。兩包的 `148B:0464` 都依序收到 `211,0` 至 `211,15`，共 16 次。`SP.MES` 都 seek 到 226、6495；identity 在 `#109584230` 讀 135 bytes，候選包在 `#109584231` 讀 112 bytes。兩包都跑滿 125M 步，沒有例外或停機；候選包日誌記錄的語言層 manifest 與建置時相同。這證明 17 項的冷啟動讀取可達，候選包實際生效；個別對白畫面另用下表核對。

| 樣本 | 同步取樣步數 | identity 與候選畫面差異像素（640×480） |
|---|---:|---:|
| `ESPMES#121.0` | 49.3M | 687 |
| `ESPMES#121.1` | 49.8M | 5,582 |
| `ESPMES#121.4` | 57.6M | 7,044 |
| `ESPMES#121.8` | 68.5M | 6,289 |
| `ESPMES#121.10` | 73.7M | 9,443 |
| `ESPMES#121.15` | 87.3M | 3,890 |
| `SP.MES#56` | 116.45M | 9,887 |

`SP.MES#56` 讀取後在 109.585M 至 110M 的六個取樣畫面都沒有差異，也沒有已知的文字繪製呼叫；125M 的單張終點圖同樣無差異。補上一個第 112M 步的正常點擊後，`16EC:1676` 在約 116.25M、116.34M 呼叫：第一列的緩衝起點都是 129，第二列 identity 推進到 200，候選包推進到 190。第 116.35M、116.45M 步畫面差異分別是 6,172、9,887 像素；第 116.26M 與 117M 步沒有差異。因而據點樣張固定取 116.45M，避免把讀檔時點誤當畫面時點。

樣張只在本機：`workplace/out/re-l10n-pilot/contact-dialogue.png`（六列，左 identity、右候選，依表中對白順序；SHA-256 `f591139693a0071bf35be021779e20359ae952c70d2d1997591bf4bde1e7a8a5`）及 `contact-sp.png`（左 identity、右候選；SHA-256 `438e38fb85021d508b81c168f47cb599c58bf0dac4342cc4e14615ffc1adf807`）。畫面經裁切與 2 倍放大供閱讀；原始 640×480 PNG 和完整 probe 日誌在同目錄，沒有進版控。差異像素是 ImageMagick `compare -metric AE` 的整張圖結果，證明畫面有變，不是語意或版面品質的判定。

## 4 限制與下一閘門

- 17 列是 `candidate`，使用者尚未看過樣張並接受，沒有獨立回譯審查的定稿；不得標 `accepted` 或隨包發行。
- 六個對白與一個據點資訊窗有畫面差異收據，其餘十句只驗到逐項載入。每個項目的最長行、換行與語意仍需人工抽樣審查；建置器已對全部採用項執行預算與 `1676` 對抗檢查。
- `ESPMES#118.2` 的 `%s` 展開畫面變體、其他窗口、玩家端 Linux／Wine 冷建置與 macOS 實機仍未驗。附錄實驗 `docs/re/025` 第 8 節只涵蓋無 `%s` 的合成邊界案例。
- 本次 `SP.MES#56` 的 extra click 只為抵達真正顯示時點，仍是正常玩家輸入；沒有注入記憶體或存檔。候選與 identity 的同一步數畫面是附近狀態比較，不能因像素不同宣稱原版規則 parity。

## 5 樣張勘誤、獨立回譯與使用者驗收

第 3 節首輪樣張有取樣時點錯誤：第 3、6 句的圖早於該句 `148B:0464` 載入，第 11、14 句的圖也只顯示部分文字。這些圖與差異像素保留為歷史收據，不用於版面驗收。重新用 identity 包與最終譯文包跑相同點擊腳本，從兩側日誌核對 16 次載入順序均為 `211,0` 至 `211,15`，並在下表各句載入之後、下一次點擊之前取樣。七張對白的整張 640×480 差異像素都非零；PNG 左側為 identity，右側為譯文，依表順序排在 `workplace/out/re-l10n-pilot/aligned/contact-aligned.png`（SHA-256 `625db75da33defb3ab42ff3281ecc0f88ee081ffd227040fb6831e927c49c8bb`）。這次對照用 `-dump-at`、`-call-args 148B:0464:2:49000000:89000000` 與 `-click-premove 3 -click-polls 3`；兩側記錄在 `aligned/identity.log`、`aligned/accepted.log`。

| 對白 id | 同步取樣步數 | identity／譯文載入步數 | 差異像素 |
|---|---:|---:|---:|
| `#121.1` | 50.3M | 49,537,915／49,535,283 | 3,896 |
| `#121.3` | 56.0M | 55,428,381／55,412,768 | 4,210 |
| `#121.6` | 63.8M | 63,069,726／63,069,244 | 7,566 |
| `#121.8` | 69.2M | 68,290,277／68,301,128 | 6,556 |
| `#121.11` | 77.0M | 76,233,341／76,232,229 | 2,038 |
| `#121.14` | 84.8M | 84,039,565／84,028,158 | 8,420 |
| `#121.15` | 87.7M | 86,981,173／86,975,827 | 3,858 |

據點資訊窗樣張在 `workplace/out/re-l10n-pilot/contact-sp-final.png`（SHA-256 `4157339f9f7422364d6ab58acc9346e642548b004fd746959b7a07d22d70fec3`），左側 identity、右側譯文，第 116.45M 步差異 9,595 像素。試點共 17 項，使用者過目的樣張是七句對白加一個據點，比例 8／17；其中 `#121.8` 達四行，是對白最多行案例，`SP.MES#56` 是最長項目與自動折行案例。其餘項目通過建置器的預算與 `1676` 檢查，樣張抽樣不能取代逐項目視。

獨立回譯在 `workplace/l10n-work/zh-TW/pilot-20261004/`：`review.md` 初審 11 項成立、6 項建議修訂；`review-revised.md` 複審 5 項已解決、`#121.11` 尚有建議；`review-final-11.md` 確認最後修訂的語意、語氣、斷行與 `acc_sha`。修訂後全部 17 項通過建置器，未經母語者審閱的註記保留。使用者先回覆「接受這 17 項」；我指出樣張取樣錯誤並提供重新對齊的七句及據點樣張後，使用者再回覆「全部接受喔」。依 `docs/spec/008` 第 3.10 節，17 列設為 `accepted`，`acc_sha` 是反跳脫後 UTF-8 文字 SHA-256 前 16 碼。

## 6 預設建置與玩家前端

最後一版候選稿在 `-with-candidates` 下建包，摘要 `68cca8b476e2c5806df2737a3684fe54085258198a47a1717f265ae4644fdbb0`，manifest SHA-256 `a89ef8f0bba11d0fbfaf9e68f46d4c141abbbda5b8beb24c26a52716762d0f6f`。使用者接受後，兩份被忽略的譯文表 SHA-256 分別是 `ESPMES.MRG.tsv` 的 `ccb92a1babfade8dde722ba7ae7fd60bae53887c9b58631318f9e7544deacfb3`、`SP.MES.tsv` 的 `bc3fb2c7b23b2994c8cfc929f8167cd808f8798f314154725dff558bb9e9ff46`。不帶 `-with-candidates` 的正式政策建包採用 17 列，摘要 `92e3bad71b7e8337437a0576908dfa748b48a7542db50bea5150da779ca6bc52`，manifest SHA-256 `e97a9a166bde8b32ea0671abd8a1d9c981bdd3879b6f87688e1114b4d2f7c5ae`；`hrl10n verify` 通過 8 檔。正式政策包與最後候選包的 `files/` 逐檔相同，只有建置政策與 manifest／摘要不同。

在 `eob-remake-go:1.26.7-ebiten2.9.9` 容器的 Xvfb 內重建 `apps/hr/play`，執行 `hr-play -orig /orig -saves /out/re-l10n-pilot/player-saves -scale 1 -ingame-lang zh-TW -l10n /l10n`。前端從唯讀原版與被忽略的譯文表冷建置，日誌有 `pack-ready ... reused=false mode=table code=zh-TW adopted=17` 與 `pack-active`，manifest SHA-256 與命令列建包相同；八個 `files/` 逐檔相同。前端二進位 SHA-256 `d4fe0612b834bc4340e7cfc3d43d4a8eb063292e00ab5f6a79710e5058161088`，日誌與 F1 畫面在 `workplace/out/re-l10n-pilot/player-cold.log`、`player-cold-f1.png`。Linux Xvfb 的此路徑通過；Windows Wine 的 identity 冷建置見第 7 節，AppImage 測試包見第 8 節。正式平台包及 macOS 實機仍待驗，不能由本收據代替。

`1676` 的冷啟動字面前綴 13 個新增變體見 `docs/re/025` 第 8 節，含真實 `%s` 展開的六組變體見第 9 節。它們證明指定窗口的預測與實測一致，不代表全部文字窗口都已驗。譯文表與語言包仍只放使用者機器，不進版控或發行包。

## 7 Windows Wine 玩家端冷建置

將目前 `apps/hr/play` 交叉編譯成 Windows 執行檔，SHA-256 `7cf57964156efc1cfbacd1f57361d0134fbfb25d9775ce05a8120ad3c6fb03f8`，放入只供測試的 ZIP（SHA-256 `30a05972616150ed352a6ede269717b7e804afb6975b35ed26f45dd2510be137`）。`tools/pkg/verify_wine.sh` 在 `psychicwar-wine:latest` 容器內解包，用 Wine、Xvfb 啟動 ZIP 內的程式，參數為 `-scale 1 -ingame-lang identity`。原版唯讀掛載，容器無網路。日誌記錄 `reused=false mode=identity code=identity adopted=0`，接著記錄 `pack-active`。這是 Windows 玩家程式從原版冷建置並啟用 identity 包的收據；測試 ZIP 不是正式發行包。

Wine manifest 在 `workplace/out/re-l10n-wine-fixture4-identity-manifest.json`，與 Linux 前端以相同 `-ingame-lang identity` 冷建置的 `workplace/out/re-l10n-pilot/linux-identity-manifest.json`，SHA-256 都是 `ac84830e64ffc962f4b33f3a7b7d7a21201757f02d39c61352eebd0c0f96e5ac`。截圖 `workplace/out/re-l10n-wine-fixture4-title.png` SHA-256 `8092ce3e49b890b07b4c0b3d3c9ca6789f836fceb030006a5c5d9065cd3968c5`；視窗是 640×400、16 色，人工檢視確認顯示遊戲主選單。日誌在同前綴的 `-identity.log`。這些檔案擁有權是執行者 UID/GID `1000:1000`，不進版控。

驗證腳本原先只等候固定時間並截整個 Xvfb 根視窗，可能收進空白或裁切畫面。本輪改為等待語言包啟用、辨識 `hr-play.exe` 視窗、確認 640×400 畫面有多於一色，並保存 manifest；解包也改在有界容器內執行。正式 Windows ZIP 與 macOS 實機仍未驗。AppImage 測試包見第 8 節。

## 8 Linux AppImage 測試包

以目前 `apps/hr/play` 建置 Linux 執行檔，SHA-256 `11437ca89d4854e06bf9f5daf34ccb39085aa9f0da73f67607610a697656d5e8`。在 `psychicwar-appimage:latest` 容器內製成只供測試的 AppImage，SHA-256 `5c8a92f87b6d013250f72fdc6e5c0556a2f3f9f9865d7054bff31f4f6e`。測試包位於 `workplace/out/re-l10n-pilot/HR-m10-test.AppImage`，不在正式交付目錄，也未經正式封包的授權檔、manifest 與外洩驗收。

修訂後的 `tools/pkg/verify_appimage.sh` 在 `eob-remake-go:1.26.7-ebiten2.9.9` 容器的 Xvfb 內，以唯讀原版及 `-ingame-lang identity` 從測試包冷啟動。日誌記錄 `reused=false mode=identity code=identity adopted=0` 與 `pack-active`。AppImage manifest 在 `workplace/out/re-l10n-appimage-final-identity-manifest.json`，SHA-256 `ac84830e64ffc962f4b33f3a7b7d7a21201757f02d39c61352eebd0c0f96e5ac`，與 Linux 原生前端及 Wine 的 identity manifest 相同。

主選單截圖 `workplace/out/re-l10n-appimage-final-title.png` SHA-256 `c685fa8f613305de51f9dd1597735970bd0ce63978ababf3053a6a1d8bdc8c1e`；用正常滑鼠點「新遊戲」後的截圖 `workplace/out/re-l10n-appimage-final-newgame.png` SHA-256 `3c494d786e218d06d35c41c5db5a65d8b99a6bfe16e58db9b5cde5896176488b`。兩張均為 1280×800、16 色，已人工檢視畫面內容。腳本現在等待語言包啟用、確認非空白畫面並保存 manifest；原有的新遊戲點擊仍通過。三個輸出檔擁有權是執行者 UID/GID `1000:1000`，只留在 `workplace/`。正式 AppImage 發行包與 macOS 實機仍未驗。

## 9 原文預算統計

在 `eob-remake-go:1.26.7-ebiten2.9.9` 容器內，以 `apps/hr/l10n.Parse` 讀取六個文字資料檔、`ESPWindowClass` 與 `budget.WindowFor` 取得窗口。一次性統計程式依規格第 3.5 節的 `%s = 20`、`%d = 6`、`%ld = 11`，以及寬度／精度取較大值的慣例逐行展開；`R_item` 是每行 `max(1, ceil(展開位元組數 / 窗口容量))` 的總和。程式在被忽略的 `workplace/out/re-l10n-pilot/budget-stats.go`，SHA-256 `5bb504357318028bfd0194c582ab103204f5844ede92e8b62b6563c18fc6d485`；只含 id 與計數的輸出 `budget-stats.json` SHA-256 `e294d8b93433a70c2cdf7a53853baedde5e995be5f5ac747b0cd5bae4b81a2c9`。原版唯讀掛載，雜湊見第 1 節與 `docs/re/source-inventory.tsv`。`SHOPTAB.TBL` 沒有窗口，依規格不列入渲染預算。

| 檔案 | 項目數 | 含 `%s` 行 | 按慣例展開後超過 30 bytes 的含 `%s` 行 | `R_item > H` 項目數 |
|---|---:|---:|---:|---:|
| `COUNTRY.MES` | 11 | 0 | 0 | 0 |
| `SP.MES` | 116 | 0 | 0 | 0 |
| `SYSTEM.MES` | 314 | 121 | 49 | 0 |
| `UWASA.MES` | 110 | 0 | 0 | 0 |
| `POWERMES.MES` | 192 | 0 | 0 | 0 |
| `ESPMES.MRG` | 1,024 | 67 | 36 | 22 |

`R_item > H` 的全部 22 項如下。欄位只有 id、預估渲染列數 `R_item`、窗口行數 `H`，不含原文。

| `R_item/H` | id |
|---|---|
| 9/8 | `ESPMES#44.1`、`#44.2`、`#120.70` |
| 6/4 | `ESPMES#120.69` |
| 5/4 | `ESPMES#120.67`、`#121.46`、`#122.1`、`#122.13`、`#122.32`、`#122.62`、`#122.66`、`#122.86`、`#122.87`、`#122.129`、`#122.174`、`#122.357`、`#122.367`、`#122.368`、`#122.375`、`#122.376`、`#122.379`、`#122.405` |

含 `%s` 行的 36／67 與 49／121 和規格第 3.5 節記錄的獨立審查量測相同。這是以 20 bytes 假設推得的預算統計，不是執行期實參長度；第 10 節只補到一個真實項目的兩個實參，其餘仍待量測，不據此宣稱 20 bytes 假設已獲驗證。

## 10 一個真實 `%s` 項目的實參遙測

承接 `docs/re/025` 第 9 節的 `ESPMES#118.2` 檢查點與正常點擊腳本。原版輸入雜湊同第 1 節；檢查點 `t06978.state` SHA-256 `5db1237028a20009013e3770fb7d2605dc00ee9962f2154cb00dc59e8063585e`，探針 `probe-l10n` SHA-256 `f02e9c67e146d32d800aba5e3b71a9e2c88d775e10806b4a3a129cd625e1ac7c`。原版唯讀掛載，執行環境是 `eob-remake-go:1.26.7-ebiten2.9.9` 容器，無網路。

探針在第 6,512,222,689 步到達執行期 `148B:01D3`，下一步從遠呼叫進入 `0110:4BA1`。`148B:01D3` 的 IDA 定位是 `237B:01D3`，兩者的 segment 差 `0x0EF0`；不能把 IDA 位址直接交給執行期 `-call-args`。進入 `0110:4BA1` 時，前三組堆疊參數是目的緩衝 `54C0:7D8E`、格式字串 `3138:0081`、可變參數列表 `54C0:7FA6`。格式字串含兩個 `%s`；可變參數列表前兩組遠指標指向 `4ABE:072A` 與 `3183:6892`。以上指標對應由呼叫入口暫存器／堆疊與同一步數的記憶體傾印直接核對，等級為 confirmed；`0110:4BA1` 的 `_vsprintf` 語意由原有控制流與格式字串支持，標為強推論。

| `%s` 實參 | NUL 前內容長度 | 最後一個內容位元組 |
|---|---:|---|
| `4ABE:072A` | 6 bytes | `A6` |
| `3183:6892` | 12 bytes | `CE` |

兩個長度都小於建置預算假設的 20 bytes。原槽位 45 bytes 含結尾 NUL，去掉兩個 `%s` 各 2 bytes，補入 6 與 12 bytes，得到 58 個內容位元組，與 `docs/re/025` 第 9 節在繪製入口量到的 58 相同。這項交叉檢查只確認此項目、此檢查點的展開長度；不能據此把所有 `%s` 的 20 bytes 上界降為 12，也沒有驗證 `SYSTEM.MES` 的實參。

含原版位元組的四份傾印只留 `workplace/out/re-l10n-pilot/`，不進版控：`vsprintf-entry-54C0_7FA6.bin` SHA-256 `45f7249c401e4b42d7ef531a067fc3090506ce267d31f17605c525631e0e0c01`、`vsprintf-entry-3138_0081.bin` SHA-256 `3405b5c214fe641483bef5731ab13edd67c9ca3e96f8daf2ea836496d68eddab`、`vsprintf-name-4ABE_072A.bin` SHA-256 `584a107525f2911c44bb16e3bb38dc70c99c098df17166ae726509c9accb4776`、`vsprintf-name-3183_6892.bin` SHA-256 `974edf3a4b9f869afce33707f5f871fa3a9afdc976223f15827fb1e29a6c5a1e`。呼叫紀錄 `vsprintf-args.log` SHA-256 `1bfd9ae67203d7d30daab3a6916684c201a9785ff268069e67025c9d2ac58fe1`；短軌跡 `fmttrace.log` SHA-256 `57d9c7a3591004962b8f299e7f2833cb32c9cab759068dd30acd7b0eec910701`。重播共兩輪，都用 `-root /orig/orig -load-state /out/bot/snd-long-s2/ckpt/t06978.state -click-premove 3 -click-polls 3` 與 `docs/re/025` 第 9 節同一點擊腳本。第一輪跑到 `-steps 6512300000`，以 `-call-args 0110:4BA1:10:6512000000:6512300000 -arg-regs` 記入口堆疊；第二輪跑到 `-steps 6512222690`，以 `-dump-seg` 保存上述段:位移的記憶體。
