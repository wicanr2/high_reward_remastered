# 008 遊戲內文字多語系（M10）：語言層、語言包建置器、譯文表與字模

**現行交付契約（2026-10-06）**：使用者要求全量譯文接入、五語切換及 README 截圖，停止追加玩家路徑抽樣與平台／原版對拍驗證，並授權譯文與新版素材提交至 private repo。正式接入依第 3.2.5 節；下列試點審查及未完成出口保留為歷史證據，不再作本次 1.0.0 發行門檻。新契約不把未驗證路徑升為原版 parity。

狀態：READY（2026-10-04，第八版；範圍 L0 與 L1，含試點；2026-10-05 另增第 3.4 節五檔補丁驗證／CFONT 葉層、第 3.5 節英文 Prepare／budget accessor READY；第 3.2.1、3.2.2 英文及第 3.2.3 簡中／日文建包與前端接線窄範圍 CONFORMED，收據 032。第 3.2.4 韓文 8 px 接線窄範圍 CONFORMED，2026-10-06；完整 L2／L3 出口、L4、L5 不在 READY 範圍）
審查：第一版經兩位獨立唯讀審查（`workplace/spec-review/008-review-A.md` 機制與證據、`008-review-B.md` 權利與流程，不進版控），第二版經第二輪（`008-rereview-A.md`、`008-rereview-B.md`），第三版經第三輪窄範圍審查（`008-rereview2-A.md`、`008-rereview2-B.md`），都判不可升 READY。第三輪審查 A 阻擋：B1（`%s` 規則與行尾規則是啟發式，有殘留缺口）、B2（ESPMES 內層格式敘述與原版位元組不符）、B3（試點的 `%s` 畫面案例沒有可達項目）；審查 B 阻擋：B1（`zh-TW` 啟用規則自相矛盾）、B2（內容判準仍有漏報，且與跨規格清單矛盾）。第四版處理全部，並併入 `docs/re/024` 的新證據。第四輪確認審查（`008-rereview3-A.md`、`008-rereview3-B.md`）仍判不可升 READY：審查 A 阻擋 B1（行寬上限有兩套互相矛盾的規則）與 B2（試點 `SP.MES#56` 沒有冷啟動可達路徑與退路）；審查 B 阻擋 B1（F1 四種值不互斥，依序判定造成遮蔽）與 B2（前端接線不在 L0、L1 的授權範圍列舉內）。第五版處理全部（對照見第 14 節），並依審查 A 的建議補兩批冷啟動動態證據（`docs/re/025`，見第 4 節）。第五輪窄範圍差異確認（`008-rereview4-A.md`、`008-rereview4-B.md`）仍判不可升 READY：審查 A 阻擋 B1（模擬器的一條突變測試是等價突變）與 B2（啟用規則 4 與 F1 對 L2 前非 `zh-TW` 語言的說法不同）；審查 B 阻擋 B1（F1 與 F4 判定有四處矛盾，沒有真值表）、B2（建置政策不在輸入摘要，試點驗收路徑會產生同名產物）、B3（第 11 節把尚未存在的產物寫成 READY 提交時的現況）。第六版處理全部（對照見第 14 節）。第六輪審查（`008-rereview5-A.md`、`008-rereview5-B.md`）仍判不可升 READY：審查 A 阻擋 B1（「拿掉位移延續」突變的定義不可實作）；審查 B 阻擋 B1（`l10nBuilderVersion` 守護測試是同義反覆）與 B2（`probe`、`hrsoak` 沒有 manifest 驗證路徑，對 `hrbot` 的描述與程式不符）。第七版處理全部（對照見第 14 節）。第七輪審查（`008-rereview6-A.md`、`008-rereview6-B.md`）：審查 A 無阻擋，建議 R1 至 R11；審查 B 阻擋 B1（`planIngame` 的簽章缺少「是否明示」，規則 2 與 3 算不出來），建議 R1 至 R10。第八版處理全部（對照見第 14 節）。第八輪窄範圍審查（`008-rereview7-C.md`，只看第七版到第八版的差異）無阻擋，建議 R1 至 R14 在升 READY 的同一個提交處理。**READY 範圍是 L0 與 L1（含試點）**。L0 實作審查（`workplace/l0-review.md`，不進版控）後的澄清（2026-10-04，不擴張範圍）：第 3.1 節證據工具對不存在的 `-lang-dir` 失敗、層重疊是設定錯誤、`OpenedLayers` 與 `PreflightState` 的定義；第 4 節 L0 出口的 skip 計數。
範圍：讓 `MAIN.EXE` 顯示的檔案類文字（對白、敘述、傳聞、商店名稱）改用其他語言的譯文，並讓畫面畫得出譯文用字。涵蓋：
- L0：dosgolem 的語言層（檔案解析順序加一層語言目錄）、診斷、狀態檔語意。**授權範圍**。
- L1：語言包建置器（Go，玩家端可執行）、檔案類文字的解析與序列化、譯文表、預算檢查（含 `1676` 模擬器）、洩漏防線、試點（繁體中文改寫，沿用原版字碼與字模），以及**前端接線**（`apps/hr/play`：旗標 `-ingame-lang`、`-l10n`、環境變數 `HR_INGAME_LANG`、`HR_L10N`，啟動時同步建置，F1 的「遊戲內文字」狀態列，F4 提示字句）。前端接線在 `docs/spec/006` 的實作之後進行：006 的 F1 面板與 F4 已提交 fork 的 `hr` 分支（`c9c8ec3`、`adeb3e4`、`aaaf999`，收據 `docs/re/026`），008 的前端接線加在其上；F1 新字串使字元表與字型子集重產。**授權範圍**。
- L2：字模補丁與自訂字碼配置。第 3.4 節五檔驗證／CFONT 葉層及第 3.5 節英文 Prepare／budget accessor 已 READY；建包、前端與完整 L2 出口仍未完成，範圍以各小節狀態為準。
- L3：逐語言導入閘門。不在 READY 範圍。
排除：
- `MAIN.EXE` 的硬編碼字串（嚴格掃描 1343 筆、7032 字）與存檔傾印段 4073 的名稱：另立規格 009，本規格不授權任何動它們的行為。畫面上的混合語言是必然結果，見第 9 節。
- `OP.EXE`、`END.EXE`、`OP*.TXT`：目前執行路徑不跑（`AGENTS.md` 第 3 節）。
- 圖像內的文字（`docs/re/020` 第 2.5 節）。
- 前端介面文字（F1 說明等）：那是 `docs/spec/006`。
- 譯文品質的認定：由使用者決定。
關聯：`docs/re/020`（文字與字型管線，下稱 020）、`docs/re/023`、`docs/re/024`（補充證據，下稱 023、024）、`docs/re/006`（Big5 字號公式）、`docs/spec/003`、`005`、`006`（第 3、5、7 節）、`007`（無修訂）、dosgolem `internal/dos/{files,find,state,dos,fileops}.go` 與 `internal/state/state.go`。
使用者決定（2026-10-03，`AGENTS.md` 第 12 節）：納入多語系，語言為繁體、簡體、韓文、英文、日文，F4 切換；以不修改、不散布原版檔案為前提。第 12 節列出尚待使用者回答的問題與本版採用的預設值；L0 與 L1 的設計在預設值下成立（U4 答非預設時，第 3.8 節的設定與接線要修訂；U6 答非預設時，第 3.5 節的序列化要修訂；L2 依賴 U5，第 3.4 節）。

名詞：**原版檔案清冊**指 `docs/re/source-inventory.tsv`（原版檔名與雜湊）；**譯文表**指 `l10n/<code>/*.tsv`（第 3.3 節）。兩者不混用。

**預設設定下的交付**：沒有譯文表與字模補丁隨包發行（U1、U3 的預設），所以一般玩家沒有可用的遊戲內語言包；語言包只有使用者自己的機器（等同開發機）能建。這是預設值的結果，不是缺陷；使用者回答 U1、U3 後才改變。第 9 節與 `AGENTS.md` M10 列同步標示。

推論等級：confirmed、強推論、假說、未知。沒有標的敘述是設計決定。引用 020、023、024 的事實沿用它們的等級並註明節號。

## 1. 輸入與工具

| 項目 | 內容 |
|---|---|
| 原版輸入 | `MAIN.EXE`、`COUNTRY.MES`、`SP.MES`、`SYSTEM.MES`、`UWASA.MES`、`POWERMES.MES`、`ESPMES.MRG`、`SHOPTAB.TBL`、`CFONT.15`（建置的九個輸入）。檔名與 SHA-256 的來源：開發側工具讀原版檔案清冊；玩家端建置器讀 fork 內嵌的 `apps/hr/runtime/required.tsv`（`hrrt.RequiredFiles()`，由原版檔案清冊產生，測試斷言兩者一致）。`MAIN.EXE` 為 `08ed144e…`（全值見 023 第 1.1 節） |
| 位址空間 | IDA 段 ＝ dosgolem 執行期段 ＋ `0x0EF0`（`docs/re/007` 第 8 節）。下文位址同時寫兩種：IDA 位址，執行期位址在括號內（例如 `287C:02E1`（`198C:02E1`）） |
| 證據工具 | IDA Pro 9.4（`tools/ida.sh`）、dosgolem `probe`（`-call-args`、`-peek`、`-poke`、`-reads-of`）。重跑方法見 020、023、024 |
| 建置器 | Go 套件 `apps/hr/l10n`（程式庫）與 `apps/hr/cmd/hrl10n`（命令列，含 `leakscan` 子命令），放在 fork 的 `hr` 分支。純 Go、不依賴 Docker、不依賴主機直譯器，玩家端（Linux、Windows、macOS）可直接執行。相依：`golang.org/x/text`（Big5 轉碼；`apps/hr/play/go.mod` 已有間接相依，dosgolem 主模組沒有，L1 在兩個模組都加成直接相依，列入 `make_notices`） |
| 資料表（歸屬） | `esp-windows.tsv`（ESPMES 項目對窗口類別，鍵為 `ESPMES#<群組>.<子>`，原稿與版控副本 `docs/re/data/024-esp-windows.tsv`）、`reserved-codes.tsv`（保留碼位，L2）與 `charmap-zh-TW.tsv`（`docs/re/020` 第 5.3 節方法（IDA 嚴格掃描加資料檔對齊解碼）產出的 1716 碼的 Unicode 對 Big5 碼一對一表，單字不是文句；含 `MAIN.EXE` CODE 段與重定位雜訊，不等於遊戲實際會畫的字集；只由開發側產生，產生器 `tools/l10n/gencharmap/`，玩家端只讀不重算）的**權威版放在 fork** 的 `apps/hr/l10n/data/`，以 `go:embed` 內嵌（只含 id、類別、碼位與單字，不含文句，放進可能公開的 fork 不違反第 3.9 節）；`engine/patches/` 是備份。開發側（IDA 產出轉檔）產生，玩家端建置器只讀。`reserved-codes.tsv` 的「嚴格掃描」部分來自 IDA，玩家端無法重算；玩家端另以資料檔與 `MAIN.EXE` 的對齊解碼結果取聯集（第 3.4 節） |
| 開發側工具 | `tools/l10n/`（Docker 內，照 `AGENTS.md` 第 10 節：原版唯讀掛載、`--network none`、`hr-l10n-*` 前綴、UID/GID、收尾 `find -user root`）：原文匯出、字模烘製、洩漏掃描入口、驗證與突變測試。不是玩家路徑 |
| 實作位置 | L0 在 `workplace/dosgolem` 的 `internal/dos`（通用能力，不含本遊戲位址；它是宿主層的檔案解析順序，不是 DOS 行為的模擬。DOSBox-X 有分層目錄的對應物 `Overlay_Drive`（`dosbox-src/src/dos/drive_overlay.cpp`），所以 `AGENTS.md` 第 4 節「補進 dosgolem 的通用能力依 DOSBox-X 原始碼實作」不能直接宣告不適用：L0 實作前由實作者讀該檔的開檔解析順序與寫入行為，與第 3.1 節的語言層逐項比對，差異記入 L0 收據。本規格的語言層唯讀，寫入模式開檔拒絕而不是寫到上層，理由見第 3.1 節）；`apps/hr/runtime` 的 `Options.LangDir` 傳遞；L1 的建置器在 `apps/hr/l10n`，前端接線在 `apps/hr/play` |

## 2. 事實基礎

key bytes 與實驗細節在 023、024；這裡列影響設計的結論。

| 事實 | 出處與等級 |
|---|---|
| 檔案類文字（不含 `OP*.TXT`）2559 筆、40,334 字，占全部雙位元組字約 79.7%：`COUNTRY.MES` 11、`SP.MES` 116、`SYSTEM.MES` 314、`UWASA.MES` 110（只有 10 種不同內容）、`POWERMES.MES` 192、`ESPMES.MRG` 1024、`SHOPTAB.TBL` 792 個名稱欄 | 020 第 5.1、5.2 節，confirmed（統計） |
| `*.MES`：u16 K，K 個 u32 偏移，首偏移 ＝ 2 ＋ 4K，項目 i 為 `[偏移 i, 偏移 i+1)`，每個偏移前一位元組為 `00`（NUL），末偏移指向 `FF`。`SP.MES`、`SYSTEM.MES`、`UWASA.MES`、`POWERMES.MES` 精確；`COUNTRY.MES`（K ＝ 12）的條目 5 至 11 偏移比真實起點大 2，末偏移 2097 ＝ 檔長 2096 ＋ 1（真實 `FF` 位置在 2095，偏移多 2） | 020 第 2.2 節；審查 A 第三輪以位元組核對，confirmed；畫面後果（少讀第一個雙位元組字）：強推論 |
| `ESPMES.MRG` 外層：u16 N ＝ 126，**125 個** u32 偏移（沒有終止偏移，首偏移 502 ＝ 表尾）；群組 0 至 44 的偏移都是 502（空群組 0 至 43，群組 44 非空），群組 45 至 116 的偏移都是 1066（群組 45 至 115 是空群組，群組 116 是第一個從 1066 起的非空群組），群組 117 至 124 各不相同，非空群組共 10 個（44、116 至 124）。**內層**（十個非空群組逐一核對）：u16 N2，N2 個 u32 偏移（相對群組起點），首偏移 ＝ 2 ＋ 4 x N2，項目 i 為 `[偏移 i, 偏移 i+1)`（含結尾 NUL），**共 N2 減 1 項**；最後一個偏移指向群組最後一個位元組 `FF`，群組以 `00 FF` 結尾，群組長度 ＝ 末偏移 ＋ 1。N2 為 4、46、75、53、46、95、80、449、174、12，項目數合計 1024（N2 合計 1034） | 024 第 4.2 節（外層與空群組）；審查 A 第三輪（內層）；confirmed |
| `SHOPTAB.TBL` 19800 ＝ 99 x 200 ＝ 792 x 25 bytes；每個欄位名稱 20 bytes 加 5 bytes，第 21 個位元組 792／792 為 `00`；791 欄名稱尾端是 `0x20` 補白，1 欄名稱佔滿 20 bytes | 024 第 4.1 節、審查 A 第三輪，兩次獨立核對，confirmed |
| 讀取端每次取字都開檔再關檔（`ESPMES`：`237B:0464`（`148B:0464`）；`MES`：`24B2:0111`、`24B2:0030`），不快取。長跑開檔次數：`ESPMES.MRG` 110 至 181、`SYSTEM.MES` 2 至 12、`POWERMES.MES` 5 至 15、`SHOPTAB.TBL` 0 至 11、`SP.MES` 與 `UWASA.MES` 0、`COUNTRY.MES` 0 至 1 | 023 第 6.1 節 confirmed（`summary.json` 開檔計數）；逐次開檔的反組譯證據由審查 A 讀 `24B2:0111` 內 `sub_2B140`／`sub_2B187` 與 `237B:04DA`、`0560`、`05D9`（主代理未獨立重讀）：強推論 |
| `CFONT.15` 在啟動時開一次不關，handle 存 `4D38:007A`；字模取得 `287C:05A2`（`198C:05A2`）每字先 `_lseek`（絕對位置，`1000:098F`（`0110:098F`））再 `_read(…, 30)`，無快取。字模 30 bytes（15 列 x u16 大端），共 13867 字（416010 bytes，無檔頭）；`E0` 至 `F9` 的字號範圍 9785 至 13866（4082 格），檔案位移 ＝ 字號 x 30（`docs/re/006` 第 124 行公式；審查 A 兩輪以動態呼叫核對吻合） | 020 第 3.1、3.2 節 confirmed；023 第 7 節 |
| `CFONT.15` 已用字 1716（嚴格掃描），寬鬆掃描估計漏約 4%，集中在商品表；資料檔中 lead 在 `E0` 至 `F9` 的不重複字審查 A 至少找到 9 個。未對齊的位元組樣式比對會命中上萬次（`MAIN.EXE` 7,042、七個資料檔 4,478），所以「成對位元組」的普查必須用對齊解碼與字串區，不能用樣式比對 | 020 第 5.3 節；審查 A 第二輪，強推論 |
| `25DC:1676` 的雙位元組判斷表 `dseg:09D1`（經 `1000:966C`）把位元組分兩類：**S 集（單位元組路徑）**＝ `20` 至 `7E`、`A1` 至 `DF`；**P 集（成對路徑）**＝ `7F` 至 `A0`（含 `81` 至 `9F` 的 lead）、`E0` 至 `FF`、`01` 至 `1F`（`00` 與 `0A` 在迴圈頂端先離開）。表在執行期沒有寫入者（靜態無寫入，4 個時點與檔案逐位相同） | 023 第 2.1、2.5 節 confirmed（4 個時點內）；P 集範圍含 `FD` 至 `FF` 由審查 A 第三輪重讀 `966C` 確認 |
| `1676` 迴圈：P 集位元組 → 畫它、檢查 `8*si > 最大寬` 或下一個位元組為 NUL（離開），再在 `25DC:16EC` **無條件畫下一個位元組**，不查 `0x0A`；S 集位元組 → 畫它、回迴圈頂端。`287C:02E1`（`198C:02E1`）自己配對（旗標 `byte_4D3CE`，第一個 `>= 0x80` 位元組當 lead，下一次呼叫不論值為何當 trail，旗標跨呼叫保持），所以字形配對永遠對齊真實字界；`1676` 的分類與字界錯位時，只影響兩件事：被步驟 4 多吃的位元組若是 `0x0A`，換行消失；寬度停止差一個位元組（良性，理由見第 3.5 節模擬器列：寬度停止不改變 P／S 相位）。**位移狀態**：`1676` 在 P 集位元組之後多吃一個位元組；下一次分類到 S 集位元組（或單位元組字）時恢復；落在 P 集則位移延續 | 023 第 2.2 節 confirmed；位移延續的推演由審查 A 第三輪重讀反組譯；冷啟動 7 組連鎖實驗（`FD` trail、三字 P 集 trail 連鎖、`A4E0 E1E2`、S 集 trail 恢復等）預測全部吻合，confirmed（`docs/re/025`；涵蓋限制見該文第 6 節：只測 `ESPMES#121.0` 槽（`01A3` 路徑、248 寬窗口，其餘窗口是讀碼推論）；變體只有 21 個位元組，沒有碰到寬度停止，P 集位元組落在偏移 29 或 30（寬度停止邊界，0 起算，`si ＝ k - 2` 或 `k - 1`）的情形沒有動態證據；trail `FE`、`FF`、`7F`、`80`、`A0`、`01` 至 `1F` 與 lead `F9` 至 `FC`、`81` 至 `9F` 未測；lead `E2` 至 `F8`、trail `E3` 至 `FC` 與 S 集 trail `A1` 至 `DF` 沒有逐值動態收據，同類別靠判斷表的靜態確認，023 第 2.1 節） |
| 成對路徑吞換行：行尾字 lead 在 `A1` 至 `DF`、trail 在 `E0` 至 `FF`（**不是只到 `FC`**）時，換行被當半形字畫出，兩行併成一行。原版有 38 行（12 種內容）這種行尾（trail 在 `E0` 至 `FC`）。寬度邊界：lead 在 `A1` 至 `DF` 的字落在行尾第 31 位元組時，畫在上一行，下一行縮排 8 像素 | 023 第 2.3、2.4 節 confirmed（反組譯、指令級模擬、合成實驗 T0／T1／T3）；38 個真實行的畫面未觀察 |
| `%s` 展開：`SYSTEM.MES` 有 124 處、`ESPMES.MRG` 有 77 處 `%s`（024 另量得 ESPMES 的 `%ld` 39、`%03d` 44、`%1d` 22、`%d` 21 等）。ESPMES 的 `%s` 後面接 `0A` 7 處、接項目結尾（NUL）4 處、接其餘位元組 66 處；`SYSTEM.MES` 的 `%s` 後面 123 處接 `0x20`、1 處接 `>= 0x80`。`%s` 在 `_vsprintf` 展開後把原版 Big5 名稱放進同一緩衝才進 `1676`；展開的名稱可使 `1676` 與字界錯位。`01A3` 在 `_vsprintf` 之後才剝掉所有 `0x20`，所以名稱尾端補白在該路徑消失，`06CF`、`07FE` 保留 | 024 第 3.2 節、審查 A 第二、三輪（兩次獨立計數一致），confirmed（計數）；位移機制強推論 |
| 一頁行數 ＝ `floor(h / 16)`；超過時只畫第一頁，續讀指標存進物件但沒有呼叫點用傳回值續頁，結果是**截斷**，不分頁。窗口（`(w - 8) / 8` bytes x `floor(h/16)` 行）：`256x67` 為 31 x 4（`01A3`、`06CF`），`512x131` 為 63 x 8（`07FE`），`240x64` 為 29 x 4（VS 畫面，024 第 2.3、2.4 節），`SP.MES` 內文 71 x 4，`COUNTRY.MES` 內文 67 x 5。窗口共 23 種 | 023 第 4 節、024 第 2.3 節 confirmed（反組譯、動態）；「98 個呼叫點都不用傳回值」只有對話框、SP、COUNTRY 路徑 confirmed，其餘為強推論 |
| 自動折行在原版常見：走 `01A3` 或 `06CF`（31 bytes 窗口）的 625 個 ESPMES 項目（023 掃描歸屬 624，024 第 2.3 節讀碼補 `#122.168` 得 625）中，256 項含超過 31 bytes 的行（統計以 624 為底） | 023 第 4.3、4.4 節，confirmed（統計） |
| ESPMES 外層 id 對群組索引（`237B:0482` 起的 switch，`bx ＝ id − 0xC8`，大於 `0x13` 走預設）：id 200 至 204 → 群組 116 至 120；211 至 214 → 121 至 124；215、216 → 125、126（通過邊界檢查 `237B:04FE`，但表只有群組 0 至 124，越界讀）；217 至 219 → 127 至 129（經跳表，大於 N，載入端只讀 N 後回傳空字串）；205 至 210 與其他值（含 44）走預設，群組索引取 id 本身（大於 N 者同樣回傳空字串）。ESPMES 窗口歸屬（`docs/re/data/024-esp-windows.tsv`）：`win31x4`（`01A3`／`06CF`）625、`win63x8`（`07FE`）3、`win29x4` 2、**無靜態呼叫點 394**（1024 − 630 的精確值：630 個不重複 (群組,子) 呼叫點全為立即值）；394 項沒有任何載入路徑的證據（全映像 630 個 `9A 64 04 7B 23`，0 個跳轉或資料型遠指標），間接機制未排除 | 024 第 2.1、2.3 節 confirmed（反組譯、`poke` 動態佐證、位元組鏈） |
| 原版超過窗口行數的項目只有 `ESPMES#122.32`（折行後 5 行，窗口 4 行） | 023 第 4.4 節；機制 confirmed，個案畫面未驗 |
| 對話框把字串複製到 `3E41:0423`（執行期 `2F51:0423`）：`01A3` 略過 `0x20`（`237B:01F2` `26 80 3f 20`，590 個呼叫點），`06CF`（41）與 `07FE`（3）不略過。緩衝容量剛好 0x200（含 NUL，字串最長 511 bytes），緊接 `FACE.MRG`，沒有長度檢查。超長會蓋掉 `FACE.MRG` 檔名，之後臉圖載入失敗、不畫對白、開檔函式無限重試 | 023 第 3 節 confirmed（反組譯、poke 實驗）；真實溢出未跑 |
| 上游緩衝 `4028:0081`／`0281` 各 0x200，不含 `%` 的項目 511 bytes 以內都放得下 | 023 第 3.2 節 confirmed |
| `ESPMES` 最長項目：`#44.1`、`#44.2` 261 bytes（除錯用長格式字串，走 `07FE`），`#120.70` 195 bytes（走 `07FE`），其餘 118 bytes 以內 | 023 第 3.3 節 confirmed |
| 可達性：`ESPMES#121.0` 至 `#121.15`（冷啟動 16 句開場對白）與 `SP.MES#56`（點據點再點選單項目）都不含 `%`。`SP.MES#56` 已有**冷啟動收據**（單一冷啟動指令，`-click-premove 3 -click-polls 3`，新遊戲後每 2.6M 步一次共 16 次點擊關開場對白，約 97M 與 103.5M 步點地圖據點與選單項目，`-steps 125000000`；`SP.MES` 於 `#109584101`、`#109584166`、`#109584230` 讀 2、8、135 bytes，seek 226 與 6495；重跑逐步數相同；負對照去掉最後兩個地圖點擊則 `SP.MES` 讀取 0 筆；完整指令在 `docs/re/025` 第 2.1 節）。已知待查：同一支 probe 同樣的 `-clicks` 數值，在 soak 狀態選到 `SP#56`、在冷啟動選到 `SP#55`（座標換算或遊戲狀態差異，原因未查，不推翻 023）。確定可達且含 `%s` 的項目有 `ESPMES#118.2`（外層 id 202、子 2，45 bytes，2 個 `%s`），但路徑是 bot 檢查點狀態（`workplace/out/bot/snd-long-s2/ckpt/t06978.state`，12 次左鍵），不是冷啟動直達；冷啟動確定可達路徑上沒有 `%s` 項目；`SYSTEM.MES` 的 `%s` 項目可達性未知 | 024 第 3.1、3.3 節、025 第 2 節 confirmed（動態收據） |
| dosgolem：`LoadState` 以狀態檔內的絕對路徑 `os.Open`，不經 `resolve()`（`internal/dos/state.go:153`、`:218`）；`internal/state/state.go` 的 `Load` 先載機器段（`:93`）、最後才載 DOS 段（`:104`），`dos.LoadState`（`internal/dos/state.go:185`）自己在 `:193` 先關舊 handle、`:196` 起覆寫欄位；`searchFor`（FindFirst）不經 `resolve()`（`find.go:126`）；`scratchCopy` 在寫入模式開檔時把 `resolve` 找到的檔複製進暫存層（`files.go:179` 至 `:186`、`:248` 至 `:266`）；`renameFile` 以字串前綴判斷來源在暫存層（`fileops.go:194`），`stampScratch` 同（`files.go:279`）。`MAIN.EXE` 沒有 FindFirst 呼叫者，對這些資料檔一律唯讀開檔（`int 21h AH=41` 1 個站點，`AH=56` 無） | 023 第 5、6.3 節 confirmed（原始碼與靜態普查）；其餘行號為審查 B、A 的讀碼，強推論 |
| `CFONT.15` handle 換檔：每字用絕對位置 `_lseek`，字與字之間換檔不需保留位置；`_lseek` 與 `_read` 之間（約 15 道指令）換檔需新檔同大小且保留位置 | 023 第 7 節，強推論（讀碼，未跑換檔實驗） |
| 存檔：句子層級的檔案類文字不在存檔內（020 第 4.2 節命中 0 筆）；但專有名詞有重疊：`GAMEFILE.000` 有 20 筆 12 至 14 bytes 的勢力名（存檔位移 16656 起，間距 81），其他四份只比對了命中行數 | 審查 A 第一輪 S6，強推論（只有開局附近的 5 份存檔） |

## 3. 設計

### 3.1 L0 語言層（dosgolem 通用能力）

- 解析順序：暫存層（`Scratch`）、語言層（新增 `DOS.LangDir`）、原版目錄（`Root`）。語言層缺檔時回退原版。其餘規則（只認 basename、大小寫不分、8.3 截斷）沿用。暫存層優先於語言層是對的：玩家存檔蓋過一切。
- **`LangDir` 在 `Session.Open` 綁定一次，執行中不變。** `LangDir` 為空時行為與現況完全相同（零成本退路）。`LangDir` 指向不存在的目錄時，`Open` 把生效值清為空字串（狀態檔記錄的是生效值）；`probe`、`hrsoak` 與 `hrbot` 是證據工具，對不存在或不是目錄的 `-lang-dir` 一律失敗並拒絕啟動，不得把設定錯誤靜默變成原版收據（`hrbot` 經 `Session.Open`，在 L1 的 `LangStatus()` 上線前以「`-lang-dir` 非空而生效的 `LangDir` 為空就拒絕」防護；上線後以非空原因鍵非零結束）。`LangDir` 等於 `Root` 或 `Scratch`（正規化後相等）是設定錯誤，綁定時回錯。不提供執行中切換：字模 handle 常開，MES 換了而字模沒換會畫出無關的字。換語言的唯一動作是重新啟動前端。
- 語言包目錄結構：`<資料目錄>/l10n-packs/<名稱>/` 內，`files/` 是 `LangDir`，`manifest.json` 放在 `files/` 之外，避免被 `searchFor` 列舉。L1 的 `files/` 固定放八個檔（七個資料檔與 `CFONT.15`）：沒有譯文的檔與 `CFONT.15` 是原版逐位元組複本（identity 包八個檔都與原檔相同），L2 之後 `CFONT.15` 換成補丁字模。複本使 identity A/B 提前走過「字模 handle 從語言層開檔」的路徑，也使第 3.2 節的讀寫量預估成立（七個資料檔約 105 KB 加 `CFONT.15` 約 416 KB）；它與資料檔一樣只存在使用者機器、不進版控與發行包，不構成新的權利類別。
- **寫入模式開檔拒絕**：對語言層的檔以寫入模式開檔（`open` 的 `writeAccess` 路徑）回 DOS 存取被拒的錯誤碼（AX ＝ 5），不走 `scratchCopy`，也不複製進暫存層。理由：複製進暫存層後，暫存層永遠優先，語言包會失效；遊戲對這些檔一律唯讀開檔（023 第 5 節），拒絕不改變正常路徑。判定用層別（`resolve` 的新版本回傳 `(path, layer)`），不比對路徑字串。`AllowFileWrites`（`dos.go:497`）白名單不收語言層的檔。**改名、刪除、`create`／`createNew`／`extendedOpen`／`fileAttr` 維持與 `Root` 檔相同的語意**（`renameFile` 複製的是新名稱，不遮蔽舊名；`unlink` 對原版目錄的檔回成功不動作；`create` 在暫存層建同名檔，行為與原版 `Root` 同名檔相同；遊戲沒有走到這些路徑），差異記於已知差異。`renameFile`（`fileops.go:194`）以字串前綴判斷來源在暫存層，改成層別判斷（`-saves` 設成語言包的祖先目錄，或前綴相同的兄弟目錄如 `…/l10n-pack` 對 `…/l10n-packs/…` 時，字串前綴會把語言層的檔當成暫存層檔，走 `os.Rename` 而搬走語言包檔案）；`stampScratch`（`files.go:279`）的呼叫點傳入的都是暫存層路徑，不需改。
- `find.go` 的 `searchFor` 目錄順序改為 `Root`、`LangDir`、`Scratch`，後者覆蓋前者。`MAIN.EXE` 不呼叫，但通用能力要補，並加測試。
- 其他 `resolve` 呼叫者（`exec.go:224`、`:369`、`dosinfo.go:164`、`:272`、`font.go:201`、`fileops.go:147`、`:187`、`files.go:168`、`:419`）插入語言層後行為一致，各列入測試。
- **狀態檔語意**：`dosState` 新增 `LangDir`（字串）與 `LangManifest`（manifest 的 SHA-256），gob 向後相容，舊檔視為空，`dosStateVersion` 不升（欄位缺省值等價於舊行為）；`DOS` 新增對應公開欄位，由 `apps/hr/runtime` 在驗證 manifest 後設定；`cmd/probe` 與 `apps/hr/cmd/hrsoak`（自己建 `dos.New`，不經 `Session.Open`）加旗標 `-lang-dir`，並同時讀 `<dir>/../manifest.json` 取雜湊設定該欄位（檔案不存在時失敗，拒絕啟動），不驗證 manifest（否則這些工具存下的狀態檔記錄空雜湊，在 runtime Session 載入時被拒）；`apps/hr/cmd/hrbot` 經 `hrrt.Open`（`main.go:287`），加旗標只需傳 `Options.LangDir`（與明示的 `SkipLangDigest`），`LangManifest` 由 `Session.Open` 驗證後設定。`LoadState` 在**任何狀態變更之前**完成比對：狀態檔記錄的 `LangDir`（正規化路徑）與 `LangManifest` 必須與目前 Session 相同，否則明確拒絕載入，錯誤訊息點名兩個值。預檢要放在**兩處**：`internal/state/state.go` 的 `Load`（它是串流讀取，機器段解完才讀 DOS 段，所以要先把兩段讀進記憶體、對 DOS 段預檢，再 `m.LoadState`、`d.LoadState`），以及 `dos.LoadState` 開頭（任何直接呼叫它的程式繞過 `state.Load`），失敗時 handle 與欄位都不動。因為 `dosState` 未匯出，`internal/state` 解不了 DOS 段：`internal/dos` 新增匯出方法 `(*DOS).PreflightState(r io.Reader) error`，與 `LoadState` 共用同一個解碼與比對函式（解碼、魔術字與版本、語言層三項），`state.Load` 把兩段讀進記憶體後先呼叫它；兩段都有問題時 DOS 段的錯誤先出現，DOS 段損壞時機器段不再被先覆寫（失敗路徑的已知差異，成功路徑不變）。`:218` 的 `os.Open` 失敗造成的半套用是既有行為，不在本規格範圍，測試不得宣稱「任何失敗後 Session 不變」，只宣稱「`LangDir` 比對失敗後 Session 不變」。`dos.StateDigest`（`state_digest.go`）對整個 `dosState` 做 JSON：新欄位加 `omitempty`，`LangDir` 空時舊摘要不變；有語言包時新欄位 `LangDir`、`LangManifest` 本身非空，`dos.StateDigest` 必然與無語言包不同（與 `CFONT.15` handle 的來源無關），所以語言包的 A/B 比較對象寫明是 `machine.StateDigest` 加畫面雜湊加存檔位元組，不含 `dos.StateDigest`。因此：語言層與字模的驗證一律從冷啟動起跑；語言包 Session 存下的診斷狀態檔只能在同一語言包載入。狀態檔記錄的是機器本地路徑，跨機載入診斷狀態檔本來就需要相同路徑（`dos.LoadState` 以狀態檔內的絕對路徑開檔，`state.go:218`，既有行為），本條不改變這點。傳遞點是 `apps/hr/runtime/session.go:259` 的 `Options.LangDir` 與新增的 `Options.LangDigest`（前端算好的預期輸入摘要，第 3.2 節）。
- **開檔層報告**：`d.Opened []string` 與 `OnOpen func(name string)`（`dos.go:273-283`，既有使用者：`cmd/hrsoak/main.go:191`、`oracle/oracle.go:623`、`oracle/state.go`、`apps/hr/runtime/trim.go`）簽章不變。新增欄位 `OpenedLayers`（以磁碟 basename 的大寫為鍵的表，記首次與最近一次命中層 `scratch`／`lang`／`root`；只記 `AH=3Dh` 的成功開檔（含 `AH=6Ch` 開既有檔，EXEC、overlay 載入與字型服務的讀檔不記）；層標籤是實際開啟的檔所在的層，原版目錄的檔以寫入模式開啟並複製進暫存層後記 `scratch`；不同檔名約 100 個，不被 `TrimDiagnostics` 清）與新回呼 `OnOpenLayer func(name, layer string)`；不用環狀緩衝（`ESPMES.MRG` 每 2 遊戲小時開 110 至 181 次會洗掉只開一次的 `CFONT.15`）。`docs/spec/005` 既有的「不同檔名最後 8 筆」是解析前的檔名，與此並存，兩者來源不同。診斷（`info.txt`）新增三項（驗證失敗回退原版的 Session 在第一項另記 `LangStatus` 的原因鍵）：`LangDir` 的值、語言包 manifest 的 SHA-256、各資料檔與 `CFONT.15` 的命中層。
- 通用性：位址與檔名都不在 dosgolem 內。判準「換一支 binary 之後這段還成立嗎」成立。

### 3.2 語言包與建置器

- 語言包是建置產物，位置 `<資料目錄>/l10n-packs/<code>-<輸入摘要前 12 碼>/`（第 3.1 節的結構）。**輸入摘要**＝ 原版輸入雜湊、譯文表整體雜湊、補丁雜湊（L2 之後）、建置器版本（`l10nBuilderVersion`，不用 app 版本字串，由內嵌 golden 檔位元組的 SHA-256 前 8 碼導出（golden 是合成譯文表 fixture 在 table 模式的輸出雜湊，第 8 節；建置輸出改變就必須重產 golden，版本隨之改變））、**建置政策**（模式 `table` 或 `identity`，加 `with-candidates`、`allow-country-offsets`、`allow-shoptab` 三個旗標，依固定順序序列化）的 SHA-256。無譯文表與 `identity` 模式的「譯文表整體雜湊」都取空位元組串的 SHA-256，模式欄位區分兩者。建置輸出完全由這些輸入決定，所以同名目錄存在且 `manifest.json` 驗證通過（且 manifest 的 `code` 與這次相同：摘要不含代碼，目錄可能被改名或複製）就**直接使用，不重建**；政策不同的建置得到不同的目錄名，不會互相重用（例如 `hrl10n -with-candidates` 建的試作包不會被前端的預設建置沿用）。`l10nBuilderVersion` 有守護測試（第 8 節）。語言包內容含原版位元組（`keep` 項目、未動的字模），所以**只存在使用者機器的資料目錄，不進版控，不進發行包**；`leakscan` 對 `l10n-packs` 路徑與同名檔判洩漏。
- **L2 版本延伸（DRAFT）**：目前內嵌的 golden 只覆蓋 L1。L2 正式接入時須加入英文雙字共格與其他新語言的合成輸出 golden，讓 `l10nBuilderVersion` 的輸入包含 L1 與 L2 fixture、固定的 L2 契約版本；第一次接入必須產生不同於現行 L1 的建置器版本。日後改動 L2 配碼、折行、字模套用或零採用列語意時，同一次更新 L2 golden 或契約版本，讓輸入摘要改變；合成 golden 只守護其涵蓋的案例，其他語意變動靠明示更新契約版本與審查。這不改現在 L1 建置器的版本算法。
- **建置在玩家機器上執行**，輸入是玩家自備的原版檔案加譯文表（第 3.3 節）；L2 之後再加字模補丁（第 3.4 節）。建置器是 `apps/hr/l10n`，前端內嵌。
- **語言包啟用規則**（一處定義，F1、旗標、測試都引用）：先決定「遊戲內語言」`C`：優先序 `-ingame-lang <代碼|none|identity>`、環境變數 `HR_INGAME_LANG`、介面語言設定 `lang`（旗標 `-lang`、偏好設定、預設 `zh-TW`，`docs/spec/006` 第 5、7 節）。**`C` 是一對 `(代碼, 明示)`**：值來自 `-ingame-lang` 或 `HR_INGAME_LANG` 時明示為真，來自 `lang` 時為假（「明示」與第 3.8 節 `ingameStatus` 的 `override` 是同一個謂詞）。然後：
  1. `C ＝ none`：原版。
  2. `C ＝ (zh-TW, 明示)`（`-ingame-lang` 或 `HR_INGAME_LANG` 明示的 `zh-TW`）：建置並啟用 `zh-TW` 語言包（有 `l10n/zh-TW/` 譯文表就套用表，沒有就是 identity 包，全部 `keep`）。L1 試點用這個形式。`C ＝ (identity, 明示)`：一律建 identity 包（全部 `keep`），不理會任何譯文表，供 identity A/B 與玩家端冷建置驗證用（因為 `l10n/zh-TW/` 存在後，`zh-TW` 建的是套表的包，不是 identity）；`identity` 是測試用的值，不出現在 F1 的語言清單與 F4 循環。`planIngame` 的前置條件：`none` 與 `identity` 蘊含明示為真。
  3. `C ＝ (zh-TW, 非明示)`（來自介面語言設定：旗標 `-lang`、偏好設定或預設）：有 `l10n/zh-TW/` 譯文表才建置啟用，否則原版（零成本退路）。
  4. 其他 `C`（非 `zh-TW`、`none`、`identity`）：**L2 之前一律不建置**（沒有字模補丁就沒有字碼，第 3.5 節「字碼」列必然失敗；建置器以常數 `l2Supported ＝ false` 表示，L2 實作後改為 `true`）；L2 之後，有該語言的譯文表且補丁在手才建置啟用。不建置時為原版，F1 顯示原因（第 3.8 節的原因順序：先無表 `no-table`，再 L2 尚未存在 `unsupported-language`，最後補丁缺 `no-patch`）。規則 1 至 4 實作為純函式 `planIngame(C, hasTable, l2Supported, patchInHand)`（`C` 是上述 `(代碼, 明示)` 一對；同一組 `(zh-TW, 無表)` 因明示與否輸出不同：明示建置 identity，非明示不建置），輸出「不建置」「建置 table」「建置 identity」三者之一與原因鍵；`resolveStartup` 經 `planIngame` 到 `ingameStatus`（第 3.8 節）串接。
- **啟動順序與可見性**：`main.go` 先 `hrrt.Open` 後 `ebiten.RunGame`，建置在 `Open` 之前完成，此時沒有視窗；Windows 以 `-H=windowsgui` 建置，標準錯誤看不到。所以建置同步執行，輸出寫 `play.log`（同時印標準錯誤），不依賴 toast；結果顯示在 F1 的狀態列（第 3.8 節）。建置的讀寫量預估約 1 MB 讀、0.5 MB 寫，預期亞秒級（未量，L1 收據量測）。
- **譯文表（與 L2 之後的補丁）的尋找順序**與 `findHD`、`findOriginal`（`paths.go`）一致：旗標 `-l10n`、環境變數 `HR_L10N`、`.AppImage` 檔案所在目錄下的 `l10n/`、執行檔旁的 `l10n/`（AppImage 內的 `usr/bin` 在唯讀 squashfs）、macOS 的 `Contents/Resources/l10n`、目前目錄的 `l10n/`、資料目錄的 `l10n/`（這一項是 008 新增，`findHD` 沒有）；輸入檔名大小寫不分。**per-code 語意**：找的不是第一個存在的 `l10n/`，而是第一個含 `<l10n 根>/<代碼>/` 且該目錄內至少有一個七個資料檔之一的譯文表檔（`<資料檔名>.tsv`，檔名與目錄名大小寫不分）的候選（函式 `FindTableDirFor(搜尋來源, 代碼)`，回傳 l10n 根目錄與是否找到）；這個「找到」就是第 3.2 節規則與第 3.8 節 `avail` 的 `hasTable`，空的 `<代碼>/` 目錄不算存在（否則會建出採用 0 列的 table 包）。明示的旗標候選也套同一條件：旗標指向沒有該代碼譯文表的 `l10n/` 時視為沒有，不往下找，因為使用者明示的來源不能被後面的候選默默取代。預設發行包不附譯文表（U1、U3），所以預設只有開發機能建。
- **建置與寫入**：建置寫到 `l10n-packs/` 下的同層暫存目錄 `.tmp-<目錄名>-<行程識別>-<隨機>`（避免跨檔案系統的改名失敗），`manifest.json` 最後寫，成功後以 `os.Rename` 改名到位。改名失敗（目標已存在非空：另一個執行個體剛建好，或舊的同名目錄；Windows 共用違規）時**回到「已存在」分支重驗**：已存在的目錄驗證通過就用它並丟棄自己的暫存目錄；驗證失敗**不搬動舊目錄**（POSIX 上搬走正被執行個體當 `LangDir` 的目錄，會讓它逐次開檔落回原版，而 `CFONT.15` handle 仍指舊檔），改用帶序號的新名稱 `<code>-<輸入摘要前 12 碼>-<n>`（`n` 從 2 起，最多到 9）。改名失敗後重新探測，若第一個不存在的名額沒有改變（不是競爭造成的失敗，例如權限，或 Windows 上防毒軟體剛掃過新目錄的暫時性失敗），重試至多 3 次（間隔 50 ms，可注入）再回建置失敗，不空轉。**序號目錄的探測**：每次啟動依序探測基底名與 `-2` 至 `-9`，第一個驗證通過者直接使用；沒有通過者就在第一個不存在的名稱建置（`Lstat` 失敗但不是「不存在」的名額視為被占用；名額是一般檔案或空目錄也視為被占用，不被覆蓋）；全部存在且皆未通過才放棄（遊戲內文字維持原版並記一行）。所以基底名永久損毀時，後續啟動重用同一個序號目錄，不會逐次耗盡序號。啟動時盡力清掉過期的暫存目錄（`.tmp-*` 且修改時間超過 1 小時），Windows 上刪不掉就忽略。**不刪任何 `l10n-packs/<code>-…` 目錄**：沒有可靠方法判斷它是否正被其他執行個體使用，POSIX 上刪除正被使用的目錄會讓該執行個體逐次開檔落回原版；輸入改變（原版、譯文表、建置器版本、政策）而留下的舊目錄會累積，列入已知差異（第 9 節），使用者可手動刪除整個 `l10n-packs/`。中斷的建置不會留下可通過驗證的語言包。`dataDir()` 失敗而退到 `os.TempDir()`（`paths.go`）時，語言包不跨次保留，每次啟動重建（已知差異）。
- 建置步驟：
  1. 核對每個原版輸入的 SHA-256（玩家端來源 `hrrt.RequiredFiles()`），不符即失敗，不猜測套用。
  2. 解析七個資料檔，逐項以譯文表覆蓋譯文；沒有譯文的項目與 `keep` 保留原位元組；序列化（第 3.5 節）；每個檔寫出。
  3. `CFONT.15`：L1 以原版逐位元組複本放進 `files/`。L2 之後的 table 模式先計算實際採用列數與所需字組；採用列數為 0 時八個輸出檔維持與原版逐位元相同，`CFONT.15` 不套補丁，維持下文 identity 契約。採用列數大於 0 且字組是預烘碼本子集時，以原版 `CFONT.15` 為底套用完整補丁；缺組即整包拒絕，不輸出部分檔案。identity 模式也一律不套補丁。
  4. 寫 `manifest.json`：格式版本 `format`、代碼 `code`、每個檔的 SHA-256 與位元組數（依檔名排序，八個檔）、九個原版輸入的雜湊（`orig_inputs`：七個資料檔、`CFONT.15`、`MAIN.EXE`）、譯文表整體雜湊 `table_hash` 與譯文表格式版本 `table_format`（目前 `tsv-1`，是譯文表的檔案格式版本，不是譯文內容的版本；它進 manifest、不進輸入摘要，格式語意改變必然使建置輸出與 golden 改變，建置器版本隨之改變）、補丁雜湊（L2 之後，L1 為空字串）、建置器版本、建置政策（模式與三個旗標）、輸入摘要、採用列數（實際被採用的非 `keep` 譯文列數；為 0 的包等同 identity 包，第 3.8 節）。欄位順序固定，兩格縮排加結尾 LF，沒有時間戳記與主機資訊，所以 Linux 與 Windows 建出同一個包的 `manifest.json` 雜湊相同（玩家端冷建置的替代證據）。
- 重現性：同一輸入兩次建置，所有輸出檔 SHA-256 相同。建置器只做整數與位元組運算，不做浮點光柵化（光柵化在開發側預先烘製，第 3.4 節），所以結果與平台無關。
- 啟用判定：`Session.Open` 以 manifest 驗證語言包（manifest 列出的檔案存在、雜湊與大小相符、manifest 未列出的檔案不得出現在 `files/`、原版輸入雜湊相符、manifest 記錄的輸入摘要等於預期輸入摘要）。**預期輸入摘要由前端算好，經 `Options.LangDigest` 傳入**（`Session.Open` 沒有譯文表路徑，不重算；前端取 `l10n.ExpectedDigest`，`Build` 完成後另比對 `Result.Digest` 與它相等，不等（建置期間譯文表被改動）記 `build-failed`，原因比 `Open` 的摘要不符更準確）。`LangDir` 非空而 `LangDigest` 為空時，`Open` 回錯，除非 `Options.SkipLangDigest` 明示為真（避免前端漏傳而無聲略過這一項比對）；只有經 `Session.Open` 的工具路徑（`hrbot`、`tools/play.sh` 的測試入口）明示 `SkipLangDigest`，這時只略過輸入摘要這一項，其餘驗證照常。`probe` 與 `hrsoak` 不經 `Session.Open`，不驗 manifest 也不驗摘要（已知差異，第 9 節）；它們載入的目錄由 `hrl10n verify` 先驗證（下述命令列契約）。驗證失敗：不啟用，記一行，遊戲內文字維持原版，F1 顯示原因。`LangDir` 的最後一段必須是 `files`，否則同樣視為 `verify-failed`（驗證函式驗的是 `<包根>/files`，不擋的話 `LangDir` 可以綁到沒驗過的兄弟目錄）；驗證函式回的原因鍵 `bad-options`（呼叫端漏傳必要選項，不可能由使用者資料觸發）是程式錯誤，`Open` 回錯，不映射為 `verify-failed`；`LangDigest` 缺漏的檢查放在 `Open` 最前面（早於讀 `MAIN.EXE`）。**驗證函式與結果通道**：驗證函式放在葉層套件 `apps/hr/l10n/verify`（原版清單以參數傳入，runtime 與 `hrl10n` 都 import 它，避免 runtime 與 `apps/hr/l10n` 互相 import）；驗證失敗時 `Open` 不回錯，而以空 `LangDir` 開啟，並經 `Session.LangStatus()` 回報（生效的 `LangDir`、失敗原因鍵 `verify-failed` 或空；建置在 `Open` 之前由前端完成，建置錯誤由前端自己記為 `build-failed`），前端據此組成 `startFail ＝ (C_start, 原因鍵)`；經 `Session.Open` 且傳了 `LangDir` 的無頭工具（`hrbot`、`tools/play.sh` 的測試入口），在 `LangStatus()` 回報非空原因鍵時非零結束（負對照路徑明示例外），A/B 與樣張收據記錄 `LangStatus()` 的生效 `LangDir` 非空與 `OpenedLayers` 的各資料檔命中層為語言層；`SkipLangDigest` 為真時一律略過摘要比對，傳入的 `LangDigest` 被忽略；`LangDir` 非空、`LangDigest` 為空且未明示略過是程式錯誤，`Open` 回錯，先於 `LangDir` 存在性檢查，不映射為 `verify-failed`。`LangManifest` 是 `manifest.json` 檔案原始位元組的 SHA-256；`LangDir` 正規化為 `filepath.Abs` 加 `filepath.Clean`；`probe`、`hrsoak`（通用工具，不 import `apps/hr/l10n`）與 `Session` 各自實作這兩條規則，測試以同一個目錄斷言三者算出相同值。`CheckRequiredFiles`（`required.go:50`，`session.go:236` 呼叫）只驗原版，語言包另驗。
- **`hrl10n` 命令列契約**：`build -code <代碼> -mode table|identity -orig <原版目錄> [-l10n <l10n 根目錄>] -out <l10n-packs 目錄> [-with-candidates] [-allow-country-offsets] [-allow-shoptab] [-dup-ids]`（三個政策旗標只在 `hrl10n`，前端內嵌的建置器不提供；`-out` 預設是資料目錄的 `l10n-packs`（規則與 `apps/hr/play` 的 `dataDir()` 相同，兩處必須同步；Docker 內要明示）；`-l10n` 是 l10n 根目錄，table 模式再接 `<代碼>/`（大小寫不分，不存在退出碼 1），與前端旗標、`HR_L10N` 同義；`-mode identity` 拒絕 `-l10n` 與三個政策旗標（退出碼 2），避免同一份輸出得到不同目錄名；`-code` 在 identity 模式取 `zh-TW` 或 `identity`；`-dup-ids` 在 stderr 每個重複來源群組一行列出 id，沒給時只印各檔的群組數）。成功時 stdout 三行 `dir=`、`reused=`、`manifest-sha256=`，退出碼 0；建置失敗或譯文表違規退出碼 1；用法錯誤退出碼 2。`verify [-digest <預期摘要>] [-orig <原版目錄>] <語言包目錄>`（語言包目錄是含 `manifest.json` 的包根，`probe`、`hrbot` 的 `-lang-dir` 取的是包內的 `files/`；與 `Session.Open` 共用同一個驗證函式；原版輸入雜湊預設取 `hrrt.RequiredFiles()`，與 `Session.Open` 一致，給 `-orig` 時另外要求該目錄內的實際雜湊與 manifest 相符；不帶 `-digest` 時略過輸入摘要；印出 `manifest.json` 的 SHA-256 供收據記錄）；`leakscan`（第 3.9 節）。試點與 L3 的畫面樣張流程：`build -with-candidates` 建包，`verify` 驗證並把輸出與 manifest 雜湊記進收據，才用 `probe`、`hrbot` 的 `-lang-dir` 載入；負對照：竄改包內一個檔，流程必須在 `verify` 步驟失敗。
- 第三方可散布語言包（`LICENSE` 第 3 條 (c)，在其權利範圍內，不及於原版文字）：譯文表格式與建置器讓第三方在不含原版位元組的前提下產生並散布譯文表，語言包本身由使用者在自己的機器上組出。

### 3.2.1 英文建包接線（CONFORMED，2026-10-05；不含前端）

本次窄範圍只將已 READY 的 `glyphpatch` 與 `enpairs.Prepare` 接到 `Config`／`ExpectedDigest`／`Build` 及 `hrl10n build`。table 模式暫只支援 `zh-TW` 與 `en`；簡中、日文、韓文仍不可建。identity 仍只容許 `zh-TW`／`identity`，不讀補丁。前端啟用、F4 可用性、L3 玩家畫面及發行不在此接線範圍。

- `Config.PatchDir` 是直接含第 3.4 節五檔的本機目錄。`en` table 必須明示此值；其他代碼或 identity 給此值皆拒絕，不無聲忽略。命令列新增 `-glyph-patch <目錄>`，只用於 `-code en -mode table`，不自動尋找或下載字模。譯文、補丁、語言包仍不入 Git 或發行包。
- `ExpectedDigest` 與 `Build` 都先以 `glyphpatch.Load(dir,"en")` 建不可變快照；摘要的 `PatchHash` 及 manifest 的 `PatchHash` 取該快照的 `Digest()`。`Build` 只讀一次補丁，摘要、採用、套用共用此快照，不能驗摘要後重讀。譯文表仍只讀一次，沿用既有九個原版輸入 SHA-256 檢查。外部程序在兩次 API 呼叫間修改輸入時，摘要可以不同；前端將來仍須比對 ExpectedDigest 與實際 Result.Digest。
- 採用政策沿用第 3.3 節：逐列核對 id、來源摘要與重複 id，accepted 摘要不符視為 candidate，keep 及未允許的 candidate 保留原版；COUNTRY／SHOPTAB 非 keep 列的旗標 gate 不變。只有實際採用列才送英文 Prepare，空譯文拒絕。窗口由 typed 原項目及 ESPWindowClass 取得。英文 SHOPTAB 沒有已證實窗口，採用時即使給 `-allow-shoptab` 仍拒絕並點名窗口，不能猜上限。這是待補閘門，不改既有繁中名稱路徑。
- 繁中的編碼、自動折行、名稱限制、預算與群組一致性保持既有算法。英文對實際採用列用 Prepare 產生最終位元組，不再送 L1 AutoWrap，也不先用原版 Charmap 編碼。任何來源、子集或末端預算違規，整包失敗，不增加碼、不改譯文、不略過失敗列。
- 英文同來源群組的比較發生在折行之前，依原文相同群組及 `group-exception` 的既有規則。比較鍵為未折行的普通二字單位、格式規格及明示換行的典範序列：普通段每兩個 scalar 成一組，奇數補 U+0020；格式與換行各自保留邊界，以無歧義的標記與長度表示。因完整碼本一對一，這等價於比較未折行的二字單位編碼；不必要求只因後續折行而消失的字組也存在碼本。最終子集仍只對寫入結果檢查。同群組相同來源文字在不同窗口折行不同可接受；不同文字恰好折成相同結果，仍須按比較鍵拒絕。只有一列被採用時不要求其餘 keep 列一起翻。
- 通過全列驗證才序列化七檔；實際採用列數為零時八檔皆與原版逐位元相同，正數時以該數呼叫 `Patch.Apply(originalCFONT,adopted)`，套完整固定碼本，不按採用子集重新配置。零採用依然驗補丁並將其摘要放入輸入摘要；改補丁不得重用舊包。結果成功前原版檔案始終唯讀且不變。
- 建置器版本改為三份固定長度前導及內容的 SHA-256 前 8 碼：明示契約識別 `hr-l10n-l2-en-v1`、原 L1 golden、另存的 L2 golden。長度與 LF 格式固定；版本輸入不可單純串接造成邊界歧義。L2 golden 用程式產生的合成二字單位、測試點陣與譯文，只登記補丁摘要、採用計數、排除建置器版本及輸入摘要後的 manifest 摘要、八檔輸出摘要，不保存原版字模、語句或修改副本。測試點陣只驗建置流程，不稱為 Noto 字形證據。需要真實原版的建包 golden 在原版缺席時明示 skip；本機驗收必須實跑。修改任一 golden 或契約識別均須改版本；L2 golden 應涵蓋零採用、採用一列、candidate 排除／接受與固定字組重排。算法或政策改輸出時先重產 golden 再重新編譯，既有同名包不覆寫。
- 既有暫存、manifest 最後寫、驗證後重用、序號及原子改名規則保持。缺字組與其他輸入違規必須在建立 `.tmp-*` 之前失敗；不得留下半個包，也不刪除舊包。診斷只含路徑、id、規則、計數與碼位，不含原句。

接線驗收：現有 L1 全測與 golden 不改輸出；英文零列八檔 identity、正採用完整字模、同輸入重用、只改表／補丁／政策／建置器版本分別改摘要、磁碟改補丁後仍使用已驗快照、缺組無暫存／舊包不變、accepted 摘要改錯退回零列、群組窗口與折行一致性、CLI 參數組合及三平台編譯。本機以已接受的 17 項英文建乾淨包並驗 manifest，逐項讀回 typed 序列化結果及 CFONT 全格；正常玩家畫面另走 L3／前端，不能由這份接線收據代替。

版本序列化固定為 `hr-l10n-builder-version-v2\n`，再依序寫 `contract\t<十進位 bytes 長度>\n<識別 bytes>\n`、`l1\t<十進位 bytes 長度>\n<L1 golden bytes>\n`、`l2\t<十進位 bytes 長度>\n<L2 golden bytes>\n`，整串取 SHA-256 前 8 碼。比較鍵的二字 token 為 byte `P` 加兩個 u32 大端碼位，格式 token 為 byte `F` 加 u32 大端規格長度與 ASCII 規格，明示換行為 byte `N`；不含碼本配碼，只有通過來源驗證的 Text 可生成採用鍵。

本接線經 `workplace/spec-review/008-en-build-integration-review.md` 唯讀窄審無阻擋，主代理核對後升 READY。群組規則中「不同文字恰好折成相同結果」指未折行比較鍵不同但最後折行 bytes 相同；奇數字段與該段加一個尾端空白可有同一鍵，依未折行二字編碼等價處理。`group-exception` 沿用既有半形／全形分號切段、去掉段落前後空白、精確比對，不另接受以空白拆詞的例外記號。

### 3.2.2 英文前端接線（CONFORMED，2026-10-05）

只啟用第 3.2.1 節英文 table 包的既有玩家路徑；L1 繁中與 identity 不改，簡中、日文、韓文仍不可用。沿用第 3.8 節的單一 lang 設定、F4 下次啟動生效、明示覆蓋、F1 部分翻譯及失敗回原版。不新增持久化設定、發行內容或即時切換遊戲內文字。

字模放在已找到的實際英文譯文表目錄下的 `glyph-patch/`，直接含第 3.4 節五檔。此為忽略版控的 `l10n/en/` 本機輸入，不是新交付目錄。前端不新增字模旗標，不到其他來源尋找補丁：既有 FindTableDirFor 優先來源決定了表位置，該來源的補丁不足時不從較低優先來源拼接。命令列建包仍使用第 3.2.1 的明示 `-glyph-patch`。

- 以逐語言函式取代 production 的全域 `l2Supported=false`／`patchInHand=false`：只有 `en` 的 L2 支援值為真，其他三語為假；zh-TW 不依賴這兩值。純函式 planIngame／availFor 的布林真值表維持，production caller 依代碼傳值，不能一次放行全部語言。
- 「補丁在手」只是可用性探測：`glyph-patch` 為實際目錄且不是符號連結，五個精確檔名都是一般檔且不是符號連結。缺目錄、缺檔、特殊檔或符號連結視為 no-patch；SOURCE／字碼／字形內容的真正驗證仍由 ExpectedDigest／Build 的 Load 完成。五檔存在但無效，在啟動時回 build-failed。沿用目前可用性快取，每次 F4 清空後重新探測，F1 使用該次結果；補丁剛放入或移除可在下一次 F4 的下次啟動提示反映，不讀完整內容來決定 avail。
- prepareIngame 在決定建置 table 時，英文 Config.PatchDir 指向該實際表目錄的 `glyph-patch`。ExpectedDigest 與 Build 結果摘要比對維持，補丁或譯文在兩次呼叫間變更時 build-failed，不啟用不一致的包。presence 探測不能取代補丁快照驗證；探測後已決定的路徑不可用、Load 不合格或兩次摘要不符時回原版。若合法內容在 ExpectedDigest 前完成變更，可正常驗證並使用新快照，不宣稱 presence 能察覺所有置換。
- no-table／unsupported-language／no-patch 的既有優先順序保持，F4 與啟動使用相同逐語言支援與探測函式。沒有表或補丁時不建包、不新增暫存；有表／補丁且採用零列時仍顯示原版文字的驗證用包，不稱翻譯生效。新增可達狀態為 E＝`effIdentityPack{Code:en}`；S＝en 時視為相同選擇，F1 為驗證用英文包、F4 為不變。S＝en 對 Code≠en 的 identity 種類包仍視為不同；S＝zh-TW 或明示 identity 對 identity 種類包的既有相同關係保持。只有 adopted>0 的英文包通過 Session.Open 才顯示部分翻譯。
- 原版九檔保持唯讀，語言包仍在使用者可寫資料目錄。存檔格式、名稱及寫入路徑不變；這次不翻硬編碼或存檔名字。F2 主題與 F3 聲音保持既有行為。所有新增日誌只含路徑、id、規則、計數、碼位與摘要。

驗收包括既有前端真值表與啟動測試回歸；逐語言 production caller 的支援值、同源補丁路徑、五檔 presence 負例、實際 Config.PatchDir、缺組／無效補丁／摘要變更的回退、英文零採用狀態、F4 動態探測與下次啟動。Linux Xvfb 必須用乾淨使用者目錄與已接受 17 項本機表，在正常前端冷建置英文包、新遊戲、對白與據點，確認包驗證生效及實際字模呈現，退出重開顯示重用，再驗移除補丁回原版。既有包在啟動前被竄改時，由 Build 驗出後另建序號，應驗安全重建與舊包不覆寫；verify-failed 回原版則針對 Build 完成後、Session.Open 前的竄改，由既有 runtime 或前端依賴測試覆蓋，不增加正式玩家測試旗標。測試不修改記憶體、原版或存檔以跳過玩家路徑。Windows／macOS 至少編譯，未實跑時明確限制；本輪不打包或發行，也不能以研究 probe 截圖代替前端收據。

本接線經 `workplace/spec-review/008-en-frontend-integration-review.md` 唯讀窄審，零採用狀態與竄改時間邊界補齊後無阻擋；主代理核對後升 READY。實作與玩家收據完成前不宣稱英文玩家路徑完成。

2026-10-05 實作後，建包與前端獨立審查均無阻擋；版本 golden、八檔零採用、真實 17 項 typed 讀回、完整字模、缺組無輸出及相關回歸通過。Linux Xvfb 的正常冷建包、16 句對白、據點、重用、損壞包重建、失敗回退及 F4 下次啟動收據見 `docs/re/032`。主代理核對後只將第 3.2.1／3.2.2 窄範圍升 CONFORMED；Windows／macOS 只編譯，其他語言、全遊戲內容、存檔 A/B、完整 L2／L3 與發行皆未被此狀態涵蓋。

### 3.2.3 簡中與日文標量接線（CONFORMED，2026-10-05）

範圍限 `zh-CN`／`ja` 的非白名單字元一字一碼、既有自動折行、建包與同源前端。沿用 B 案 Noto 全新非白名單字模、五檔驗證、固定原碼子集、原版輸入保護及本機權利邊界。韓文仍受第 3.6 節詞距閘門，不因此開放；英文雙字共格、繁中 L1 與 identity 的規則不改。

本機 accepted 各 17 項均無格式規格及 U+0020／U+3000。正式據點折為兩行，簡中 60／60、日文 68／68 bytes。原版來源、窗口、保留集合與字型身分沿本規格及 032。獨立唯讀契約審查 `workplace/spec-review/008-cjk-scalar-integration-review.md` 無阻擋，標點分類建議已納入，實作前先升 READY。

實作後獨立審查 `workplace/spec-review/cjk-integration-implementation-review.md` 無剩餘阻擋。主代理另驗固定 Noto 的兩次重烘、全 13867 格、真實各 17 項讀回及 Linux 正常冷建包、完整對白、據點、重用與回退，逐張目視通過；race、vet、Windows／macOS 編譯及結構通過，後兩平台未實跑。正式收據見 032，窄範圍升 CONFORMED；不升完整 L2／L3 或授權發行。

- 來源先驗 UTF-8、Unicode 15.0.0 及最多 511 scalar／2044 UTF-8 bytes 的必要上界。明示 U+000A 例外保留；Cc、Cf、Cs、Co、Cn、Mn、Mc、Me、Zl、Zp 拒絕。普通 U+0020 拒絕，避免默默選取詞距；U+3000 可用經五檔驗證的整格空白。完整 `%` 規格沿 L1 parser 保留，不配字碼，並與 typed 原項目的規格比對；格式中的 ASCII 不當普通來源字元處理。
- 單位元組白名單沿現行 `singleByteOK`：數字、大寫字母、`/`、`:` 保留原碼；換行與完整轉換規格亦保持原 bytes。其餘字元只用 `Patch.Lookup([]rune{r})` 的固定標量碼，不沿用原版共用漢字。Patch 必須為相同代碼的已驗 `scalar15` 快照，nil、英文／韓文 Patch 或缺字即拒絕，診斷只含 id、規則及碼位。
- 可用每項來源建立局部正反碼表，交既有 Encode 與折行器；不改共享 L1 Charmap 的字集、白名單或 Big5 回查。BreakAfter 只將局部 `fromBig` 還原出的來源 scalar 依 Unicode 15.0.0 的 `unicode.IsPunct(r)` 分類，不能把 IsSymbol 算作標點，也不能把 E0 自訂碼經 Big5 解碼當標點。白名單單位元組 `/`、`:` 不列折點。來源字只查已驗不可變 Patch，不重讀磁碟、不重新配碼或烘製。
- 按 typed 項目取得窗口與原項目，先編碼，再以現行 `WrapAndCheck` 自動折行及 `1676` 對抗檢查，原有明示換行保持。群組一致性取折行前的編碼 bytes，輸出取檢查通過的最終 bytes；相同來源譯文可依不同窗口折行，異文恰好折成同結果仍拒絕。accepted／candidate／keep、摘要降級、來源 id、例外、COUNTRY gate 沿既有共同採用層。SHOPTAB 仍按未知窗口拒絕，不猜名稱寬度。
- table 增加這兩個代碼，必須明示 `Config.PatchDir`；CLI `-glyph-patch` 對英文、簡中、日文 table 可用，其餘模式或代碼拒絕。ExpectedDigest 與單次 Build 各自 Load 相同代碼；Build 的摘要、採用與 Apply 共用一次快照。全列驗過才 Serialize，零採用八檔 identity 仍綁補丁摘要，正採用套完整補丁，缺字不留部分包或暫存，原版與舊包不變。
- 新契約識別為 `hr-l10n-l2-scalar-v1`。現行版本長度串流保持，L1 golden 不改；L2 golden 追加兩語的零採用、採用、candidate 排除／採用與重排固定變體。合成點陣只驗接線，沒有原版語句或字模，不稱 Noto 視覺證據。契約與 golden 變動自然換版本及輸入摘要，不能覆寫舊英文包；既有英文輸出 bytes 應保持相同。
- 前端逐語言支援只增加簡中、日文；同一實際表目錄的 `glyph-patch/` 與五個相應檔名探測沿英文路徑，不跨來源拼接。新零採用狀態為 `effIdentityPack{Code:zh-CN|ja}`，與同代碼選擇視為相同，其他代碼關係及繁中／明示 identity 舊規則保持。F1、F4 下次啟動、失敗回原版、偏好與覆蓋沿既有規則；韓文仍不支援。存檔格式及路徑不改，不翻硬編碼或存檔名字。

驗收須包括來源分類／非法 UTF-8、白名單、完整格式、標點回查、明示與自動折行、群組不同窗口、缺字、代碼錯配、一次快照、零列八檔、完整字模、採用政策、摘要與版本、L1／英文回歸及 golden；前端須驗新增代碼、同源 Config、presence、零採用、失敗與 F4。開發側兩次固定 Noto 重烘相同，正式五檔 Load 成功。真實各 17 項建包後逐項讀回、未採用項目不變、字模全格及 manifest 通過，再在 Linux Xvfb 冷建包、新遊戲、完整對白、據點、重用與缺補丁回退，目視檢查字形及裁切。Windows／macOS 至少編譯，實跑缺席照實限制；此節不授權發行或外推全遊戲。

### 3.2.4 韓文 8 px 空白接線（CONFORMED，2026-10-06）

使用者已在兩種實測詞距中選「韓文8 像素」。本輪驗收及完成聲明限既有 accepted 17 項韓文試點的建包與正常前端，不在編碼器加入只容這 17 個 id 的特殊限制；可修改譯文表的固定碼本能力沿既有契約。原版輸入、窗口、字型、保留集合及權利邊界沿第 3.2.3、3.4 節及 032。8 px 的原版行為 confirmed 範圍是 032 的兩個 01A3 槽位，不外推全遊戲；正式據點畫面須另驗。獨立唯讀審查 `workplace/spec-review/008-ko8-contract-review.md` 無阻擋，通用例外回指及清冊範圍已補，升窄範圍 READY。

- `ko` 沿用標量驗證、KR face 1 的 Noto 全新字模與固定碼本。來源 UTF-8、511 scalar／2044 bytes、Unicode 15.0.0 類別、格式與未知窗口拒絕沿第 3.2.3。唯一來源例外是普通 U+0020：每個空白編成單位元組 `0x21`，不查字模；前後與連續空白保持，不 trim、不正規化。換行與完整格式 token 保留原 bytes，token 內不轉換空白，格式仍須通過原項目比對與 L1 parser。來源 U+0021 `!` 必須查 Noto 自訂雙碼字模，不可輸出原碼 `0x21`；U+3000 仍為經驗證的整格空白。其餘非白名單字元沿不可變 Patch 的單 scalar Lookup，缺字拒絕。
- 不改共享 L1 Charmap.Encode 或現有白名單。韓文私有編碼路徑做上述例外及逐 token 讀回核對，群組一致性使用折行前 bytes。預算 Input 增加預設 false 的韓文空白旗標，只有韓文 Prepare 啟用：允許單位元組 `0x21`，按 1 byte、8 px 計量；旗標 false 時仍拒絕。雙碼尾位元組 `0x21`、原碼 `0x20`、格式、控制碼與 1676 閘門不放寬。WrapAndCheck 必須保留旗標。沿既有標點排序與自動折行，不新增詞界折行或刪除行尾空白。
- Build／CLI table 增加 `ko`，必須明示相同代碼的五檔 PatchDir，仍只 Load 一次快照；身分摘要、採用政策、accepted 摘要降級、COUNTRY、完整 Apply、零採用八檔 identity、缺字無半成品與原版不變沿第 3.2.3。identity 模式、繁中、英文、簡中與日文編碼保持。
- 契約識別改為 `hr-l10n-l2-ko8-v1`，版本串流保持並綁新增 golden。既有 L1／L2 golden 前綴保持，追加韓文零列、採用、candidate 排除／採用、重排，以及普通空白與字面驚嘆號不同碼的合成案例。契約變更自然換版本及摘要，不覆寫舊包，不把合成點陣稱 Noto 證據。
- 前端逐語言增加 `ko`，同實際 table 目錄的 glyph-patch 五檔探測及 Config、F1、F4 下次啟動、偏好覆蓋、失敗回原版沿第 3.2.3。`effIdentityPack{Code:ko}` 與同碼選擇視為相同。存檔格式、路徑、硬編碼字串與 4073 不變。

驗收須包括 8 px 單碼、字面驚嘆號雙碼、連續／前後空白、格式保留與非法格式、UTF-8／類別拒絕、旗標 false 反對照、行尾與 1676 拒絕、缺字原子失敗及既有 golden 回歸。固定 Noto 兩次重烘五檔相同、Load／Lookup 及完整 13867 格核對；真實 17 項 typed 讀回，每個來源普通空白對應 `0x21`，未採用項目及原版輸入不變，零列八檔、重用及摘要通過。Linux 正常前端冷建包、全部 16 句、據點、重用與回退，逐張目視字形、空白及裁切；Windows／macOS 至少編譯，未實跑照實限制。獨立實作審查無阻擋後，只有本節可升 CONFORMED；完整 L2／L3、全量譯文與發行仍未授權或未完成。

獨立實作審查 `workplace/spec-review/ko8-integration-implementation-review.md` 無未解阻擋。主代理完成固定 Noto 雙烘、全 13867 格、17 項 typed 讀回及 101 個空白核對，正常 Linux 前端六階段、全部對白與據點三行逐張目視通過；回歸、race、vet 及 Windows／macOS 編譯結構通過，後兩平台未實跑。收據見 032。本節窄範圍升 CONFORMED，不升完整 L2／L3 或授權發行。

### 3.2.5 全量正式接入（READY，2026-10-06）

使用者取消追加玩家路徑抽樣、平台實跑與原版 parity 驗證。本次完成條件是已接受四語七檔各 2559 項全部接入、F4 五語切換可用，以及 README 有實際執行截圖。MAIN 顯示文字另依 009 的顯示專用接線，不改此規格的檔案格式。

| 路徑 | 正式接線 |
|---|---|
| 六檔共 1767 項 | `COUNTRY.MES`、`SP.MES`、`SYSTEM.MES`、`UWASA.MES`、`POWERMES.MES`、`ESPMES.MRG`，採用 accepted 且 `acc_sha` 相符的 UTF-8 譯文。前端開 `AllowCountryOffsets`，COUNTRY 重建精確偏移；其餘解析、長度、佔位符、折行、碼位與輸入雜湊檢查沿用既有契約 |
| 商店名稱 792 項 | `DisplayShoptab` 政策驗證來源身分、接受摘要及重複原文群組一致性。SHOPTAB 的固定 20 bytes 名稱欄與 5 bytes 其他資料完全保持原版；runtime 的顯示觀察器由同源譯文表畫出 UTF-8 譯文。六個英文名稱超過固定欄位，仍完整顯示，不裁切、不改識別值 |
| 未觀測 ESP 項目 | 已有 `class=none` 的 394 項沿用既定保守窗口；本次不要求新增可達路徑收據，不放寬 511 bytes 容量或佔位符規則 |
| 語言包摘要 | `adopted` 是實際序列化的 1767 項；`display_adopted` 是 SHOP 的 792 項。兩數分列，不把顯示替換稱為資料回填。建置政策及輸入摘要包含 `display-shoptab`，建置契約改為 `hr-l10n-full-six-plus-shop-display-v1` |
| F4 | 保留既定語意：介面立即切換，遊戲內語言寫入設定並在下次啟動生效；`-ingame-lang` 明示固定語言時維持覆寫。顯示譯文與資料譯文使用同一次啟動選擇 |
| 失敗 | 原版輸入缺席、雜湊不同、錯誤接受摘要、缺字組或超出既定記憶體／格式規則時拒絕語言包並保留原版文字；不猜測版本，不改原版與存檔 |

正式譯文來源為 `l10n/<code>/<資料檔名>.tsv`，四語各 2559 項已接受。各語五檔 Noto 字模補丁放在同目錄 `glyph-patch/`。使用者已授權它們與 AI 新素材進入 private repo，本機產生且含原版資料的 `l10n-packs/` 仍不加入版控。舊有 U1／U3 預設在這個 private repo 範圍由本次決定取代，公開散布並未授權。

最小建置收據：`workplace/l10n-work/full-build-integration.json`，四語均為 1767 資料採用加 792 顯示採用，原版 SHOP 雜湊保持；這份收據只證明全量建置與採用接線，不聲稱全程遊玩或原版同狀態 parity。

### 3.3 譯文表

位置 `l10n/<code>/<檔名>.tsv`（UTF-8，製表符分隔，跳脫 `\n`、`\t`、`\\`）：

| 欄 | 內容 |
|---|---|
| `id` | `*.MES`：`<檔名>#<項目索引>`；`ESPMES.MRG`：`ESPMES#<群組>.<子>`；`SHOPTAB.TBL`：`SHOPTAB#<記錄>.<欄位>` |
| `src_sha256` | 原項目位元組（以 NUL 切出的實體項目，去掉結尾 NUL，保留內部 `0A`）的 SHA-256 前 16 碼；`SHOPTAB` 取 20 bytes 欄位含補白。只當版本綁定，不當保密手段（見下） |
| `text` | 譯文（UTF-8，`\n` 表示換行，`%` 序列原樣保留） |
| `status` | `candidate`、`accepted`、`keep`（保留原版位元組，不翻譯） |
| `acc_sha` | `accepted` 列接受時 `text` 的 SHA-256 前 16 碼；與目前 `text` 不符即視為 `candidate` |
| `by`、`batch`、`date` | 譯者（人或模型與版本）、批次、日期（比照 `hd/provenance.tsv`） |
| `note` | 譯者備註（譯名、語境），**禁止含原文**，由建置工具以第 3.9 節的內容判準檢查 |

- **格式嚴格度與合併**（`LoadTable`、`Merge`）：第 1 行固定表頭 `id`、`src_sha256`、`text`、`status`、`acc_sha`、`by`、`batch`、`date`、`note`（製表符分隔，9 欄）；接受 UTF-8 BOM 與 CRLF；空行、未知跳脫、結尾反斜線、欄數不符、`status` 不是三值之一、雜湊欄不是 16 碼小寫十六進位（`acc_sha` 可空）、`id` 重複，都是錯誤並點名行號；`acc_sha` 的雜湊對象是反跳脫後的 UTF-8 `text`。同群組（原項目位元組相同）一致性只比對被採用的列，部分採用的群組是已知差異（不失敗）；例外記號是 `note` 以半形或全形分號切段後，去除段首尾空白所得的完整 `group-exception`。`COUNTRY.MES` 與 `SHOPTAB.TBL` 的「非 `keep` 列」看 `status` 字面值（`candidate` 也算），所以 L3 期間這兩個檔的草稿列要保持 `keep`。合併規則由 `Table.Merge` 承載：批次只替換 `candidate` 或不存在的列，覆蓋 `accepted` 或 `keep` 要明確旗標並自動退回 `candidate`；`Table.Coverage` 回報表缺哪些項目與表內不屬於該檔的 id（第 8 節「刪一列」的負對照）；`Table.UnclaimedIDs` 回報不被任何資料檔認領的 id。
- **措辭與風險**：譯文表不含原文位元組。短項目（`SHOPTAB` 名稱欄、`SP.MES` 最短 7 bytes）的雜湊可由 Big5 字典暴力還原，所以逐項雜湊不是保密手段，只當版本綁定。譯文表整體（尤其簡體等近似原文的譯文）視為原版文字的衍生物處理（`LICENSE` 第 2 條 (c) 已承認譯文是衍生著作），不依賴雜湊的不可逆性。位元組數不寫進譯文表（建置時由原版算）。
- **未決定前建置器拒絕的項目**：`COUNTRY.MES` 有非 `keep` 列（U6 的行為變更）、`SHOPTAB.TBL` 有非 `keep` 列（名稱使用端尚未追蹤），建置失敗並點名；開放要旗標明示（`-allow-country-offsets`、`-allow-shoptab`），旗標的預設關閉隨 U6、使用端追蹤完成後才改變。這兩個旗標只存在於命令列 `hrl10n`，前端內嵌的建置器不提供，玩家端無法到達。
- **`status` 的採用規則**：建置器預設只採用 `accepted` 與 `keep` 列，`candidate` 列視為 `keep`（保留原版位元組）；`-with-candidates` 旗標（只在 `hrl10n`，不在前端內嵌的建置器）才採用 `candidate` 列，供使用者過目試作批的版面。`with-candidates` 屬建置政策（第 3.2 節），進輸入摘要與 manifest，所以試作包的目錄名與前端預設建置的不同，前端不會沿用它。**試點與 L3 的畫面樣張一律用 `hrl10n -with-candidates` 建包，以 `probe`、`hrbot` 的 `-lang-dir`（或 `tools/play.sh` 的測試入口）載入驗證**；前端內嵌的建置器只顯示 `accepted` 的譯文，不載入試作包。這與 HD 素材的執行期做法（候選圖直接顯示）不同，因為譯文的 `accepted` 要使用者明示接受（第 3.10 節），不能讓未接受的譯文隨一般建置進包。
- 重複來源：`UWASA.MES` 110 項只有 10 種內容。建置報告列出所有「原項目位元組相同」的 id 群組（只列 id；函式庫由 `Result.Duplicates` 回傳，命令列預設只印各檔的群組數，`-dup-ids` 才逐群組列 id）；同群組的譯文必須相同，除非 `note` 明示例外。一致性比對的是編碼後、折行之前的位元組：原項目位元組相同而 ESPMES 窗口類別不同的兩個項目，同一段譯文各依自己的窗口折行，不算不一致；反向（兩段不同文字折行後恰好相同）判不一致，偏保守。
- **譯文表的列必須屬於該檔**：`<資料檔名>.tsv` 內 id 前綴不屬於該檔的列、查不到對應原項目的 id 都是違規，建置失敗並點名（不無聲略過）。
- **`SHOPTAB.TBL` 名稱欄的規則**（第 3.5 節窗口表沒有 SHOPTAB 窗口，轉接器不做預算檢查與自動折行）：編碼後 <= 20 bytes、不含 `0x0A`、不含 `0x00`；名稱內的轉換規格（`%s`、`%d` 等）必須與原項目逐字相同（原項目沒有就不得有），違規規則鍵 `placeholder`。窗口與寬度規則等名稱使用端追蹤、第 3.5 節補上窗口後再加。
- 合併規則：批次合併只能替換 `candidate` 列；改動 `accepted` 或 `keep` 列要明確旗標，並自動退回 `candidate`。
- 詞表 `l10n/<code>/glossary.tsv`：`term_key`（名稱位元組的 SHA-256 前 16 碼，名稱表以 020 第 2.3 節的段偏移定位）、`譯名`、`note`。建置器另從原版名稱表與對白切詞，產生只存在 `workplace/l10n-work/` 的 join 檔（`term_key` 對 `id` 與位置），供批次翻譯的全域一致性掃描使用；join 檔不進版控。
- 原文匯出：翻譯需要原文時，建置工具從使用者的原版檔案匯出到 `workplace/l10n-src/`（`id`、`src_text`，Big5 解碼），不進版控。

### 3.4 字碼與字模（L2，五檔／CFONT 葉層 READY；其餘 DRAFT）

本輪將規格授權與實作後驗收分開。已固定的原版輸入、保留集合、四組成對探針、兩個固定種子連續觀測、230 組重烘與英文來源模型見 032。尚未跑過的路徑仍未知，不因此宣稱全遊戲安全配碼。

**本輪 READY 範圍**只含五檔補丁驗證／CFONT 記憶體套用。英文 Prepare 純函式與 budget 唯讀 accessor 另由第 3.5 節窄審升 READY，不涵蓋正式建包或前端。正式建置器、前端啟用、語言包版本 golden、八檔 identity、正常玩家與逐語言導入仍另驗；韓文詞距、硬編碼文字與發行不在本次授權範圍。最後窄審見本機 `workplace/spec-review/l2-contract-current-review.md`，五檔／CFONT 葉層無阻擋，主代理核對後升 READY。研究工具不直接進正式路徑。

**實作介面**：`apps/hr/l10n/glyphpatch` 的 `Load(dir, code)` 讀一份有界、唯讀補丁快照，回傳不可由呼叫者改寫內部碼本的 Patch；`Digest()` 回傳五檔典範摘要，`Lookup(scalars)` 只查原碼，`Apply(original, adopted)` 核對正式原版 CFONT 身分，零採用列回逐位元副本，正採用列只套完整補丁。套件不讀譯文、不建包、不重烘，不變更 `l2Supported=false`。輸入 `adopted` 必須是非負整數。

**實作後閘門**：第 8 節的結構突變、字號互異、獨立整格讀回與零採用 CFONT 必須通過，葉層才可標 CONFORMED。接正式建置器時再驗固定子集、摘要與版本 golden、零採用八檔 identity、拒絕無部分包及正常玩家路徑。字模品質與母語可讀性依逐語言導入驗收；譯文接受不代替它們。補丁仍只在本機，使用者尚未授權入版控或發行。

**2026-10-05 DRAFT 光柵化與碼位實驗**（證據 [`docs/re/032`](../re/032-l2-glyph-code-prototype.md)，第一輪唯讀審查要求補強）：固定 SHA-256 的 Noto Sans CJK Regular TTC 字面 2 `Noto Sans CJK SC`，以 Pillow 12.3.0、fontTools 4.66.1 在固定容器內取 13 像素灰階遮罩，置中到 15×15，不縮放，閾值 128，逐列打包成大端 u16 的 30 bytes，第 16 欄留白；字模候選與樣張只在本機，開發工具放 `tools/l10n/`。`SOURCE-prototype.json` 記字型、OFL 全文、容器、參數與兩次烘製相同的雜湊。四語各 17 項候選的 13 像素遮罩均無超格或字型缺碼；韓文與英文的 U+0020 都是預期零墨跡。英文研究原型已用雙字共格的格內空白顯示詞距；正式配碼與玩家路徑未驗，韓文詞距仍未解。兩字簡體原型在 dosgolem 原版 theme、Xvfb 前端原版與 HD theme 可讀，尚不能外推至全字集。靜態十個輸入加 FBOV overlay 得到**106 個保守候選碼**、依該集合計算的可配上限 3170；其中四個新碼疑似指標表，僅作安全保留。掃描器未收單獨一組的未識別配對，不能把 106 稱為實際使用字數或把 3170 稱為全遊戲安全容量。原版冷啟動 90M 步與六個 bot 檢查點各 40M 步，共 446 次字模呼叫，沒有命中可配範圍；合成已畫碼 `E047` 的完整集合通過，刻意移除 `E047` 時報警。四組 `E0` 探針與 `A4` 對照的觀察也在 032，其中 `%s` 案例靠測試專用記憶體注入，不能當正常玩家路徑。此段不改 L2 的 DRAFT 狀態；後續兩個固定種子各兩遊戲小時的連續觀測共 93,008 次字模呼叫，可配範圍內的三碼都已在保留集合，移除實際畫出的 F9D8 時報警（032）；只覆蓋這兩條路徑，正式建置契約仍待審查，補丁入版控及發行措辭仍待 U5。

設計（採 B 案）：

- 簡體、日文、韓文的非白名單字元（含全形標點）各配一個自訂碼；韓文普通空白另依第 3.2.4 節，清冊不含 U+0020，字面 U+0021 仍需烘製。英文採雙字共格：每個普通文字段按顯示順序每兩個 Unicode scalar 配一個自訂碼，包含大寫字母、數字、標點與 U+0020；奇數長度段末尾以 U+0020 補成一組。英文普通文字不使用第 3.5 節的單位元組白名單；換行與 `%` 轉換規格保持原位元組，字組不得跨越兩者。建置器先確定折行，再由各行與各轉換規格之間的文字段形成字組。玩家端只使用補丁已預烘的字組與字碼；新增字組就拒絕並提示重製補丁，不在玩家端重新配碼或烘製。這是 L2/L3 的 DRAFT 設計，不改 L1 已實作的 `Encode`。四語自訂碼共用 lead `0xE0` 至 `0xF9`，**trail 限 `0x40` 至 `0x7E` 與 `0xA1` 至 `0xDF`**（126 值，共 26 x 126 ＝ 3276 碼，全在 S 集）。理由：trail 在 P 集（`E0` 至 `FF`）時，位移狀態會延續到行尾（第 2 節）；trail 限制使任何位移在下一個字自行恢復（L2 前提 5 的第四組探針驗證）。lead 在 `1676` 眼中全是 P 集；字形全來自同一個光柵來源，風格一致；不需要把原版字模當作其他語言的字模來源。
- **保留碼位**：原版（硬編碼字串、段 4073 名稱、資料檔）已經在這個範圍使用的碼位不可配給譯文，其字模在語言包內維持原版。保留集合取（嚴格掃描 ∪ 寬鬆掃描 ∪ 十個輸入的對齊解碼結果），寫成 `reserved-codes.tsv`（只含碼位與來源，不含字形）。可用碼數 ＝ 3276 減保留集合落在該範圍的碼數。某語言的字集超過可用碼數，閘門失敗，不縮字集硬塞。
- 例外：繁體中文（`zh-TW`）改寫版的語言包（L1 試點使用）沿用原版 Big5 碼與原版字模，不配自訂碼，字集限於 `charmap-zh-TW.tsv`（原版 1716 字，一對一）。此時譯文含 S 集 lead 與 P 集 trail 的字，第 2 節的缺陷會生效，所以第 3.5 節的 `1676` 模擬器逐行檢查。
- 配碼確定性：開發側製作預烘補丁時，簡體、日文、韓文的字元依 Unicode 碼位排序，英文的二字組依左、右 Unicode 碼位排序，依序配給未保留的碼，完整字碼表固定在補丁內。玩家端建包時，先依採用列與建置政策定稿折行，取得「需要的字組集合」，逐項查預烘的 `charmap-<code>.tsv`；集合是補丁字組集合的子集才可建置，且一律沿用補丁的原碼，不按子集重新編號。譯文或政策改變就依第 3.2 節換語言包輸入摘要；只要新集合仍是子集，可重用同一補丁。缺字組時拒絕建包並提示重製補丁，不輸出原句，也不以其他字組代替；CLI 錯誤與前端 `play.log` 列項目 id 及兩個 `U+XXXX` 碼位，F1 沿用 `build-failed` 原因鍵，不新增狀態。
- **字模補丁**：開發側（Docker，`tools/l10n/`）由開放授權字型依固定參數預先烘製，輸出：
  - `glyphs-<code>.bin`：記錄 `(碼 u16 大端, 30 bytes 字模)`，依碼排序；
  - `charmap-<code>.tsv`：簡體、日文、韓文欄位為 `unicode<TAB>code_hex`，前欄為 `U+XXXX` Unicode scalar；英文欄位為 `left_cp<TAB>right_cp<TAB>code_hex`，前兩欄為 `U+XXXX` 形式的 Unicode scalar，包含實際空白或行尾補白。兩種格式都以代碼固定辨識，不能靠欄數猜測；同碼只對一個字元或一個字組。
  - `SOURCE.txt`：字型檔名、SHA-256、版本、授權檔識別、光柵化工具與版本、固定參數（字面、像素大小、閾值、位移、裁切規則）、容器映像 ID，以及下述四個輸入檔的 SHA-256。
  補丁只含 OFL 衍生字模，不含原版位元組。字型候選以 `docs/spec/006` 第 1 節登錄的 Noto Sans CJK（雜湊、字面、授權）為首選。補丁是否入版控與隨包發行屬使用者決定（第 12 節 U5），決定前只放 `workplace/`。
- 玩家端建置在採用列數大於 0 時只做「原版 `CFONT.15` 加完整預烘補丁」：補丁每筆的碼不得落在保留集合，被換的位置就地覆蓋 30 bytes，其餘位元組原樣保留。採用列數為 0 或 identity 模式則保留整份原版字模檔。對原版字模只允許**整格原樣保留**，不做改圖、縮放、合成（`LICENSE` 第 1 條 (b) 把點陣字型列為原版素材）。
- **保留集合的信任來源草案**：正式驗證器的可信集合由受審查的量測版本決定，不由補丁自帶的檔案宣告。目前量測版取 032 的 106 碼，`reserved-codes.tsv` SHA-256 固定為 `1c841eb8a768ec79051090f39371abc582da8c30a8f2811b26a3089ee015a1fe`；補丁內的清單須逐位元相同。呼叫者提供可信清單時同樣先核對這個固定摘要。發現新保留碼時，重新量測與審查、更新可信摘要及 L2 契約版本，使舊配置失效；玩家不得用改寫 SOURCE 摘要繞過保留碼。這是拒絕契約補強，不新增原版使用碼結論。
- **正式補丁的拒絕契約草案**：先核對原版 `CFONT.15` 長度 416010 與 SHA-256 `60e55cf73ba2eb8e83018e8a9b585e22524e730e240732adb5e746b7ed54d8db`；來源不符即拒絕。`glyphs-<code>.bin` 長度必須為 32 的倍數，每筆正好是大端 u16 碼加 30 bytes 字模，碼嚴格遞增且不重複；`charmap-<code>.tsv` 的字元或二字組與碼各不重複，與二進位補丁的碼集合一對一，並與上述排序、跳過保留集合所得的決定性配碼完全相同。每碼 lead 僅 `E0` 至 `F9`，trail 僅 `40` 至 `7E` 或 `A1` 至 `DF`，不得與保留集合碰撞。`SOURCE.txt` 的字型、字面、容器及光柵參數須能解析；它記錄的檔案摘要須與補丁位元組相符。僅開發側烘製器對已存在的補丁輸出路徑拒絕，不遞迴覆寫；玩家端語言包仍依第 3.2 節重用有效同名包，無效同名包改用序號目錄。
- **補丁身分草案**：一份補丁恰含五檔：`glyphs-<code>.bin`、`charmap-<code>.tsv`、`reserved-codes.tsv`、`OFL.txt`、`SOURCE.txt`，檔名區分大小寫。`SOURCE.txt` 為 UTF-8、LF 結尾、鍵名排序且不重複的 `key<TAB>value` 列；`format` 的值固定為 `hr-l2-source-v1`，另必填 `language`、`units_sha256`、`unicode_version`、`font_file`、`font_sha256`、`font_version`、`face_index`、`face_name`、`pillow_version`、`fonttools_version`、`pixel_size`、`cell`、`threshold`、`placement`、`container_image_id`、`unit_mode`、`rasterizer_version`、`rasterizer_sha256`，以及 `glyphs_sha256`、`charmap_sha256`、`reserved_sha256`、`ofl_sha256`。`unit_mode` 對簡體、日文、韓文為 `scalar15`，對英文為 `pair2x7`；英文另必填 `source_canvas`＝`12x15`、`source_anchor`＝`ls`、`source_origin`＝`0,11`、`source_clipping`＝`canvas-before-getbbox`、`source_crop`＝`0,0,bbox-right,15`、`shrink`＝`width-gt7:BILINEAR:7x15`、`half_origin`＝`0,0;8,0`、`blank_column`＝`7`、`blank_scalar`＝`U+0020`；`placement`＝`pair2x7-baseline11`。源字先在固定畫布繪製與裁切，取非零灰階 `getbbox` 的右界，從畫布原點取整個 15 列，不去掉左 bearing；右界大於 7 才以 BILINEAR 縮到 7×15，再置於左右半格，逐列以閾值 128 打包。畫布外的源墨跡會裁切，這是已展示原型的算法；新字集仍須有覆蓋及可讀性驗收，不把五檔存在當作字形品質證明。標量模式的 `placement`＝`mask-center-floor`，13 像素 L 遮罩寬高均須不超過 15，左上位移為 `floor((15-w)/2),floor((15-h)/2)`，不縮放。後四項分別核對前四檔的 SHA-256，不含自身，沒有循環。第 3.2 節的單一「補丁雜湊」定為 SHA-256：串流先寫 ASCII `hr-l2-patch-v1\n`，再依上述四檔及 `SOURCE.txt` 的檔名 UTF-8 位元組排序，每檔寫 `檔名<TAB>十進位大小<TAB>小寫 SHA-256 十六進位<LF>`；不含目錄路徑或時間戳。任何檔案變動都會改輸入摘要，不能重用舊語言包。保留集合本身也進入雜湊；補丁資料的檔案清單、內容或語言代碼不符即拒絕。
- **SOURCE 的值域與信任範圍**：檔案恰含上述必填鍵，英文另加列出的九個 `pair2x7` 鍵，缺鍵、多鍵、重複鍵、BOM、CR、NUL、非 UTF-8 或無結尾 LF 均拒絕。鍵按 UTF-8 位元組排序。所有 SHA-256 是 64 位小寫十六進位，`container_image_id` 為 `sha256:` 加 64 位小寫十六進位。`language` 等於呼叫者選定代碼。字型固定為 `NotoSansCJK-Regular.ttc`、SHA-256 `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`、完整內部版本 `Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603`；OFL 全文摘要固定為 `f47ac356aaafd53b53c6c784b3d63e265bf2dc9fe452d4ba5aee4b9b0bf51ca8`。字面與固定算法值符合本節，`pillow_version=12.3.0`、`fonttools_version=4.66.1`、`unicode_version=15.0.0`。數字是此契約列出的典範十進位值，不容額外前導零。`rasterizer_version` 是非空 `[A-Za-z0-9._-]+` 來源識別，未知識別可接受，但未知 format、unit_mode 或算法值拒絕。容器、烘製器識別及兩個來源摘要只作 provenance，進五檔摘要，不能證明字形確由宣告工具產生。字形來源與品質另靠開發側重生、樣張及驗收。
- **補丁讀取邊界**：每檔最多 2 MiB，五檔必須是一般檔案，符號連結、子目錄與特殊檔案拒絕；完整五檔恰含指定大小寫檔名。字模最多 3276 記錄；空碼本拒絕，零採用列是建包政策，不用空補丁表示。同一快照用來核對來源摘要、解析與計算補丁摘要，不再次讀取可變檔案。任何錯誤在記憶體套用前返回，不輸出 CFONT 或部分語言包。
- **來源碼位邊界**：Unicode 15.0.0 scalar，拒絕 Cc、Cf、Cs、Co、Cn、Mn、Mc、Me、Zl、Zp；英文來源的明示 U+000A 在 token 層例外保留。英文空白只容 U+0020，簡中／日文／韓文的標量字模另容 U+3000，均可烘成零墨跡。U+3000 不能進英文二字組。碼位清冊不含換行或格式規格 token；明示換行與格式規格不配碼。韓文第 3.2.4 節的來源 U+0020 編成單碼 0x21，不烘為字模；這個例外不放寬其他語言。新版 Unicode 分類或來源規則改變時更新契約版本。
- **字模定位與驗收草案**：在上述限定碼域，令 `tail = trail - 0x40`（trail <= `0x7E`），否則 `tail = trail - 0x62`；字號 `index = (lead - 0xA4) × 157 + tail - 0x198 + 0x305`，位移 `index × 30`。驗證 `0 <= index < 13867`、位移加 30 不超出 416010、各碼字號互異。每字模 15 列，每列大端 u16；bit 15 至 bit 1 依序是左至右 15 像素，bit 0 必為零。 英文第 7 欄須零；左碼位為 U+0020 時各列 `word & 0xFE00 == 0`，右碼位為 U+0020 時 `word & 0x00FE == 0`。標量 U+0020／U+3000 整格須零。這強制執行已定空白留白契約，不判斷其餘字形品質。補丁套用後長度不變，所有指定的 30-byte 格都與補丁相同，所有未指定的位元組都與原版逐位元相同；任一條失敗即不產生語言包。這項檢查由獨立的容器測試讀回輸出再驗一次。
- **字面與空白邊界**：本機候選用同一固定雜湊的 Noto Sans CJK TTC，`zh-CN` 字面 2 `Noto Sans CJK SC`、`ja` 字面 0 `Noto Sans CJK JP`、`ko` 字面 1 `Noto Sans CJK KR`、`en` 字面 3 `Noto Sans CJK TC`；正式字面仍須在各語畫面審查後固定於 `SOURCE.txt`。簡體、日文、韓文的 13 像素遮罩置中，不保留來源基線。英文研究原型是 10 像素字面、每字 7 像素寬，置於 15×15 格的第 0 至 6 與 8 至 14 欄；第 7 欄留白，U+0020 在對應半格留白。來源遮罩在 12×15 格以基線 11 繪製，墨跡寬度大於 7 時以 Pillow BILINEAR 縮至 7，再以 128 為閾值打包。正式烘製仍須固定工具版本、參數與畫面審查。韓文 U+0020 已選 8 px，正式接線及驗收依第 3.2.4 節；英文普通文字不得輸出原始 `0x20`，行尾補白也只存在於字模格內。
- 樣張閘門要含並排畫面（原版字模與補丁字模，`original` 與 `hd` 兩種 theme 各取一次；硬編碼說話者標籤用原版字模，必然與譯文字風格不同）。15x15 光柵化對筆畫多的字可能糊。
- 補丁的決定性：開發側同一輸入兩次烘製，輸出 SHA-256 相同（同一容器映像內）。玩家端不重烘，所以不受跨平台浮點差異影響（macOS arm64 與 amd64 的光柵結果可能不同）。

### 3.5 預算與檢查（建置器強制，違反即失敗並列出全部違規項目的 id）

窗口表：ESPMES 項目對窗口類別查 `esp-windows.tsv`（鍵 `ESPMES#<群組>.<子>`，群組索引已由第 2 節的 switch 換算），其餘檔案用固定窗口：

| 檔案或類別 | 行寬（位元組） | 行數 |
|---|---:|---:|
| `ESPMES` `win31x4`（`01A3`、`06CF`） | 30 | 4 |
| `ESPMES` `win63x8`（`07FE`：`#44.1`、`#44.2`、`#120.70`） | 62 | 8 |
| `ESPMES` `win29x4`（VS 畫面，2 項：`#122.165`、`#122.166`） | 28 | 4 |
| `ESPMES` 無靜態呼叫點（`none`，394 項，沒有載入路徑的證據） | 30（窗口未知，比照 `win31x4`） | 4 |
| `SP.MES` | 70 | 4 |
| `COUNTRY.MES` | 66 | 5 |
| `UWASA.MES`（走 `01A3`，023 第 4.4 節） | 30 | 4 |
| `SYSTEM.MES`、`POWERMES.MES`（窗口歸屬未普查，比照 `win31x4`；這兩個檔的原項目沒有超過 31 bytes 的行，手動行數最多 3 與 4 行，023 第 4.4 節） | 30 | 4 |

有歸屬的窗口，行寬 `W` 取窗口容量 `(w - 8) / 8` 再減一格，向下取偶數（雙位元組字成對，避免行尾雙位元組字跨出窗口造成 8 像素溢位，023 第 2.3 節）。**窗口未知的項目一律比照 `win31x4`**（與下表「空白」列的「窗口歸屬未知一律當作走 `01A3`」同一個假設）：這是與原項目最長行相容的窗口假設（強推論，不是普查結果，已知風險見第 9 節）；真窗口若更寬，只是譯文比必要的更嚴格，若更窄，譯文可能被折行或截斷。窗口未知者 `H ＝ 4`，(3) 的 `max(H, R_item)` 提供項目相依的部分。

**計算慣例**（行位元組數的算法，窗口表、展開預算與渲染列數都用同一個）：`%s` 以 **20 bytes** 計（這是**假設**：依據是名稱表固定寬度 20 bytes，未把 `%s` 實參對到來源欄位；原版自己在此慣例下就有 ESPMES 36／67、`SYSTEM.MES` 49／121 的含 `%s` 行超過 30，表示 20 對多數項目過寬；這組數字是審查者的量測，未入證據文件，由 L1 的預算統計收據在容器內重算）；`%d` 6、`%ld` 11、帶寬度的轉換規格（`%03d`、`%10ld` 等）取寬度與型別上界的較大值。**行寬只有這一套規則**：令 `W` 與 `H` 為上表的窗口行寬與行數，`E_item` ＝ 原項目最長行的計算慣例位元組數，`R_item` ＝ 原項目的渲染列數（下述）。譯文一行的**渲染列數** ＝ `max(1, ceil(展開位元組 / W))`（引擎在窗口容量折行，每折一次多一列；除數取 `W` 而不是窗口容量，因為引擎每次呼叫至少消耗窗口容量個位元組，以 `W` 為除數只會高估列數，這個算法偏保守），項目的渲染列數是各行之和。`R_item` 的算法相同，但除數取窗口容量 `(w - 8) / 8`（窗口未知時為 31；接近引擎實際的折行；若也取 `W`，會高估只含 31 bytes 行的原項目，放寬譯文的列數上限，使譯文在原項目不截斷的窗口被截斷）。譯文每一行（以 `0x0A` 或項目結尾分隔）須同時滿足：(1) **字面位元組**（每個 `%` 轉換規格只算它在格式字串中占的字元）<= `W`；(2) **展開位元組**（計算慣例）<= `max(W, E_item)`；整個項目須滿足 (3) **渲染列數** <= `max(H, R_item)`。(1) 使沒有 `%` 的列、與含 `%` 列的字面部分，都不會超過窗口而被引擎折行；(2) 的 `E_item` 讓原項目自己的展開預算合格（不會因慣例過寬，讓原版自己就超過 30 的含 `%s` 項目變成無法翻譯）；(3) 數的是折行後的列數，超過窗口列數的後果是截斷（023 第 4.2 節），所以被 (2) 放寬展開位元組的含 `%s` 列，多出的折行列同樣計入。`%s` 的展開預算只加在含該 `%s` 的列，不放寬其他列。原項目自己不受 (1) 約束（原版有字面行超過 30 的項目），(3) 也不保證原項目自己合格（譯文的算法偏保守），只有譯文受約束；原項目維持 `keep` 時不經檢查。佔位符檢查是項目層級（個數、順序、型別），不阻止譯者把 `%s` 搬到別的列，但搬過去的列同樣受 (1)、(2) 約束。長跑加 `_vsprintf`（`237B:01D3`、`06F9`、`0828`，`24B2:00F1`；執行期位址減 `0x0EF0`）的實參長度與結尾位元組遙測，用來修正這個假設（L1 收據）。

| 檢查 | 規則 | 依據 |
|---|---|---|
| 單項長度 | 編碼後位元組數 <= 511（含 `%` 展開後的最壞值，依計算慣例） | 023 第 3 節（`3E41:0423` 容量 0x200 含 NUL，無長度檢查） |
| 行寬與行數 | 譯文每行（以 `0x0A` 或項目結尾分隔）滿足上面「行寬只有這一套規則」的 (1)、(2)，整個項目滿足 (3)。**超過就失敗，不交給引擎折行**（超過行數的後果是截斷，023 第 4.2 節）。自動折行：建置器對超寬行依單位寬度（S 集字元 1、雙位元組字 2）自動插入 `0x0A`，優先在標點之後折，不拆雙位元組對；**以插入的 `0x0A` 結尾的那一列必須通過 `1676` 模擬**（折點之後下一列從同步狀態起算），可用貪婪加回退或動態規劃，對每個候選折點對前綴列跑模擬（`%s` 對抗模式同樣適用）；折完仍超過行數或找不到合格折點則失敗 | 023 第 4 節 |
| **`1676` 模擬器** | 建置器內嵌 `1676` 的 S／P 分類模擬（S 集、P 集定義見第 2 節；P 集位元組畫完後無條件多吃下一個位元組），逐行（含建置器自己插入的 `0x0A`）檢查：**任何一種可到達的狀態使行尾的 `0x0A` 被步驟 4 當作多吃的位元組吃掉，即失敗**。項目結尾的 NUL 永遠不會被步驟 4 吃掉（步驟 3 先查 NUL，`25DC:16DA`），所以 `%s` 緊接 NUL 安全、不需要特別處理。模擬器有**兩個模式**：(1) **具體模式**：展開位元組已知（以 `-peek` 讀 `2F51:0423`，或測試自造），做確定性模擬，預測 `1676` 的呼叫次數與每次呼叫的字串偏移；(2) **對抗模式**（建置時用，因為實參未知）：每個 `%s` 的展開是長度 0 至計算慣例上限、內容任意的位元組串，所以展開之後的狀態集合與進入狀態無關，恆為 {同步, 位移}，模擬只需探索離開狀態（`%s` 緊接 `0x0A` 因此一律失敗）；對抗模式是具體模式在所有可能展開上的上界（性質測試，第 8 節）。沿用原版 Big5 碼的字（trail 可在 P 集）由這個模擬逐行判定；自訂碼字（trail 在 S 集，L2）的位移在下一字恢復，模擬同樣適用。**吃換行的判定與寬度無關**；T3a／T3b 對拍要預測字串偏移，所以模擬器另帶最大寬參數 `k ＝ (w - 8) / 8`（迴圈頂端條件 `si >= k` 離開）。寬度停止不改變 P／S 相位：023 第 4.3 節量到的 23 種立即值窗口（涵蓋 97 個呼叫點；本規格用到 248、504、232、568、536）的最大寬都是 8 的倍數，步驟 3 的寬度離開（`8 * si > 最大寬`）不可達，寬度停止只發生在迴圈頂端（同步狀態），新一次呼叫從同樣的同步狀態繼續（審查 A 第四輪，強推論，與 T3 的偏移 1059、1090 吻合；P 集位元組落在偏移 29 或 30（寬度停止邊界，0 起算，`si ＝ k - 2` 或 `k - 1`）的情形沒有動態證據，列入 L1 擴充，第 4 節）。另有 1 個計算值呼叫點的窗口未量：它的最大寬若不是 8 的倍數，相位保證對它不成立，列為已知風險（第 9 節）；窗口未知的項目比照 `win31x4`，不改變這個風險。模擬器用 023 的 T0／T1（T0 兩行、T1 併成一行）與 T3a／T3b 當 oracle 對拍，並以 `docs/re/025` 的冷啟動位移連鎖實驗與 `ESPMES#118.2` 在畫面層級驗證（第 4 節 L1 試點） | 第 2 節 `1676` 兩列；審查 A 第三、四輪 |
| 控制碼 | 不含 `0x00`；`0x0A` 只用於換行 | 020 第 7 節 |
| 空白 | **不含 `0x20`**（`01A3` 路徑會略過所有 `0x20`；窗口歸屬未知的項目一律當作走 `01A3`）。需要詞距的語言見第 3.6 節 | 023 第 3.1 節 |
| 單位元組白名單 | 韓文普通空白另依第 3.2.4 節窄例外；其他情況只允許 `0x0A`、數字 `0x30` 至 `0x39`、`/`（`0x2F`）、`:`（`0x3A`）、大寫字母 `0x41` 至 `0x5A`，以及與原項目相同的 `%` 序列。其餘字元（含 `.`、`,`、`-`、`(`、`?`、小寫字母）一律用雙位元組字，因為半形字模沒有它們（`0x21` 至 `0x2D` 等畫空白，小寫畫成另一組樣式的數字與大寫，020 第 3.3 節） | 020 第 3.3 節 |
| 佔位符 | 比對完整轉換規格（旗標、寬度、精度、長度修飾 `l`），個數、順序、型別與原項目相同；原版不支援位置參數（所以日文與韓文語序受限於 `%s` 的順序，記為已知差異）。原項目的序列由建置器從原版解析 | 020 第 2.3 節；Borland 不支援 `%n$`：強推論 |
| 名稱欄位 | `SHOPTAB` 欄位 <= 20 bytes，尾端補 `0x20`；名稱之後的第一個位元組必須是 `00`（原版 792 欄全部如此），後 4 bytes 原樣不動。建置器預設拒絕 `SHOPTAB` 譯文（第 3.3 節） | 020 第 2.2 節；024 |
| 字碼 | 韓文普通空白另依第 3.2.4 節；每個字都有字碼（單位元組白名單，或第 3.4 節的原版 Big5 碼（`zh-TW` 改寫版，字須在 `charmap-zh-TW.tsv` 內，往返得到原碼），或第 3.4 節的自訂碼）；字集不超過可用碼數（L2） | 第 3.4 節 |

韓文單碼空白的白名單窄例外見第 3.2.4 節，旗標預設關閉，原碼 0x20 與格式規格規則保持。

**英文 L2/L3 延伸草案**：上表及 `WrapAndCheck` 描述的是現行 L1 路徑；英文雙字共格不能直接把一字一碼的 `AutoWrap` 套在未配碼字串上。英文先保留譯者明示的換行；超寬行只在 U+0020 詞界嘗試折行，折點的空白改為 `0x0A`，其餘空白仍是字模半格，不產生原始 `0x20`。候選折點用折行後每段 `2 × ceil(Unicode scalar 數 / 2)` bytes 計寬，超過窗口行寬、行數或 511 bytes 上限就拒絕；無可用詞界時拒絕，不拆字組硬塞。折行定稿後才依第 3.4 節從預烘字碼表查碼並驗證子集，最後由位元組層的 `Check` 與 `1676` 模擬器重新驗證，任何一關失敗都不輸出。格式轉換規格是不可拆邊界，計算寬度仍依本節展開預算；對含格式規格的英文項目，正式折行算法與最壞展開仍待獨立審查。研究模型 `tools/l10n/enpairs.py` 的候選折法依序優先：較少渲染列、較少插入換行、較少字面位元組；同分取較長的前行。它先固定折法再查字組子集，缺組時直接拒絕，不另找碼本可以接受的折法。模型的呼叫者須先驗補丁五檔、保留碼與完整碼本；行寬、展開上限與行數上限須為有限的正整數，由 typed 原項目與本節規則計算，不由玩家任意提供。來源模型成功只表示前段來源、折行與子集成立，末端必須對實際寫入的位元組強制執行既有 `Check` 與 `1676` 對抗模擬。研究模型的 4096 scalar 長度上限只保護本機探針，不成為正式玩家契約。這段沒有改變 L1 的 READY 契約。

**英文正式純函式介面（READY，2026-10-05 窄範圍）**：`apps/hr/l10n/enpairs.Prepare(Input)` 接收項目 `ID`、`File`、`Class`、typed 原項目 `Orig`、UTF-8 譯文 `Text` 與已由 `glyphpatch.Load` 驗過的英文 Patch，回最終位元組及帶 id／規則鍵的違規。不接受玩家提供行寬或任意 map，nil 或非英文 Patch 拒絕。`Orig`、窗口類別與來源摘要由上層原版 parser／Adopt 核對，本函式不能取代原版輸入驗證。預算套件新增唯讀 accessor，重用既有 `WindowFor`、`itemMetrics` 與轉換規格解析，回 W、`max(W,E_item)`、`max(H,R_item)`、511 上限及原項目完整轉換規格序列；不另寫第二套原項目預算。無窗口或原項目含不支援轉換規格時回錯。 原項目的規格辨識保持 `scanUnits` 的原始位元組優先語意，高位元組直接接 `%` 時先辨識規格，不把 `%` 當 Big5 trail。共用 `parseSpec` 的小數點後精度須至少一位數；`%.d`、`%.s`、`%1.d`、`%1.s` 拒絕，`%.0d` 為合法精度零。此修正恢復既有第 3.5(e) READY 文法，不新增原版語料格式。

正式來源資源邊界可由既有 511 bytes 契約導出：普通二字組兩個 scalar 輸出兩 bytes，奇數段只多補一 byte；格式規格與明示換行逐位元保留；折點只以一 byte 換行取代一個 U+0020。故任何成功結果的未展開字面位元組數不小於來源 scalar 數，來源超過 511 scalar 必定不合法，可在折行前以 `length` 拒絕；UTF-8 原始字串超過 2044 bytes 也直接拒絕，這是四 bytes／scalar 的必要上界。來源先驗 UTF-8、Unicode 15 分類及 token，再驗與原項目相同的完整規格序列。格式寬度／精度的十進位累加沿用預算套件飽和上限 `1<<20`，避免整數溢位。DP 只處理最多 511 scalar 的一次來源快照，不用研究模型的 4096 保護值。最後仍以原 typed 輸入和實際輸出跑 `budget.Check`；有任何違規就回 nil 結果。缺組回 id 和兩個碼位，不在訊息輸出原句。

本介面及資源邊界經本機 `workplace/spec-review/008-enpairs-api-review.md` 唯讀審查，無阻擋；主代理已核對精度修正與既有測試，升純函式及 budget 唯讀 accessor READY。正式測試在實作後驗收，未接 Build／前端，也不代表英文語言包已完成。

**預算與檢查的約定**（`apps/hr/l10n/budget` 與 `apps/hr/l10n` 的責任拆分與細則）：預算套件負責長度、控制碼、空白、單位元組白名單、佔位符、行寬、展開寬度、渲染列數與 `1676` 模擬（規則鍵 `length`、`control`、`space`、`whitelist`、`placeholder`、`line-width`、`expanded-width`、`rows`、`1676`）；上表「名稱欄位」與「字碼」兩列由 `apps/hr/l10n`（`Adopt` 與 `Encode`）負責，違規訊息點名項目 id。細則：(a) 自動折行的優先折點「標點」在 zh-TW 指雙位元組字 lead 為 `A1` 者（`charmap-zh-TW.tsv` 內 lead `A1` 的 20 字全是標點，`A2` 區是全形數字與字母，`A3` 區不是標點）；單位元組的 `:`、`/` 不算標點（它們出現在時間與日期串內）；L2 之後標點落在自訂碼，改由字集表決定（`Input.BreakAfter`）；(b) 結尾 `0x0A` 造成的最後空行計一列（偏保守，`R_item` 以同一算法計算）；(c) 具體模式模擬在 `0x0A` 或寬度停止後已無位元組時，不記尾端空呼叫（沒有動態觀察）；`ConcreteCalls` 的輸入是 `_vsprintf` 展開並（`01A3` 路徑）剔除 `0x20` 之後的緩衝；(d) lead 之後直接接 `0x0A` 或 `0x00` 回 `control`，單獨的高位元組回 `whitelist`；(e) 轉換規格只支援 `%s`、`%d`、`%ld`（旗標 `-`、`+`、`#`、`0`，寬度與精度須為數字），其餘（`*`、空白旗標、`%%`、其他型別）失敗即關閉；原版語料的規格集合是 `%s`、`%d`、`%ld`、`%03d`、`%1d`、`%2d`、`%02d`、`%10ld`、`%4d`（`docs/re/024` 第 3.2 節），全在支援範圍；佔位符比對規格文字完全相同（含寬度）；(f) `Encode` 的 `%` 文法（旗標 `-+#0`、寬度與精度須有數字、長度 `l h L`、型別 `diuoxXcs`，`%%` 不合法：原版七個資料檔 0 處）只保證文法與原樣輸出，個數、順序與型別由預算檢查比對；(g) 折行新增的換行會增加位元組數與展開值，`AutoWrap` 之後必須再 `Check`（建置器用 `WrapAndCheck`）。

序列化規則：
- `*.MES`：偏移表依實體項目重算（首偏移 ＝ 2 ＋ 4K，每個偏移前一位元組為 NUL，末偏移指向 `FF`）。**`COUNTRY.MES` 的兩種模式逐檔判定**：全部 `keep`（identity）的檔原樣保留偏移表的 +2 偏差與最後偏移多 1；含任何譯文的檔重算為精確偏移（譯文完整顯示，與原版項目 5 至 10 少讀第一個字不同，記為已知差異；U6 回答前建置器拒絕這種檔，第 3.3 節）。其他 `*.MES` 沒有已知偏差，一律精確。
- `ESPMES.MRG`：外層保留 `N ＝ 126` 與 125 個偏移（沒有終止偏移）的原結構，空群組（0 至 43、45 至 115）依「相鄰偏移」判斷，不把它們當相鄰群組的別名；內層依第 2 節的格式：群組 i 的 N2 ＝ 項目數 ＋ 1，N2 個偏移相對群組起點，首偏移 ＝ 2 ＋ 4 x N2，項目 j 為 `[偏移 j, 偏移 j+1)`（含 NUL），最後一個偏移指向 `FF`，群組以 `00 FF` 結尾，**序列化時重新寫出 `FF`**；項目總數 ＝ N2 減 1 的合計（原版 1024），解析器若得到 1034 即為錯誤。群組 125、126（外層 id 215、216）會通過載入端 `237B:04FE` 的邊界檢查而讀到表外，這是原版缺陷，序列化不修。
- `SHOPTAB.TBL`：99 x 200 bytes 結構不變。
- identity 包必須與原檔逐位元組相同。

### 3.6 韓文詞距與英文（韓文選 8 px，英文試點已驗）

- 韓文需要詞間空白，而 `0x20` 在 `01A3` 路徑被略過。2026-10-05 的八次合成短句／行尾冷啟動已確認 `0x21` 保留且前進 8 px，雙位元組零字模前進 16 px；原版緩衝、分派與完整 PNG 互相核對，收據與限制見 `docs/re/032` 的韓文詞距原型。原先假說只在這兩個 01A3 槽位成立，不外推其他窗口。使用者 2026-10-06 選「韓文8 像素」，普通 U+0020 採 `0x21`；正式接線閘門見第 3.2.4 節。
- 英文：原版半形字模沒有小寫字母與大多數標點（020 第 3.3 節）。使用者 2026-10-05 比較同一候選的逐字全形與 Noto 雙字共格畫面後選雙字共格。字組包含英文字母、標點、數字及格內空白，每組占一個雙位元組自訂碼；開發側只為預烘清單中的實際字組配碼，不預先配置 95 x 95 全組合，清單超過可用碼數就拒絕。玩家端的最終折行字組須是清單子集，否則拒絕並提示重製補丁。已接受的 17 項使用 230 組，16 句對白每行最多 30 bytes，`SP.MES#56` 為三行 66／70／42 bytes；正式折行、佔位符、`1676`、全部 16 句畫面及正常前端建包已驗，見第 3.2.1／3.2.2 與 `docs/re/032`。使用者已接受四語各 17 項，共 68 項譯文，簡中與日文試點亦已接通，見第 3.2.3 節；韓文已選 8 px，接線見第 3.2.4 節，完整 L2／L3 仍有閘門；不以英文試點完成外推全遊戲或發行驗收。

### 3.7 字模來源與授權（L2 的前提）

- 字模只用開放授權字型（OFL 或公有領域），逐一登記來源與授權。授權全文隨補丁保存（只取該段，斷言無 GPL，做法沿用 `docs/spec/006` 第 6 節）。Reserved Font Name 在發行前以原檔核對（`docs/spec/006` 的停止線同一條）。
- **OFL 義務**：15x15 點陣補丁是外框字型改變格式而得，符合 OFL 對 Modified Version 的定義，只能在 OFL 下散布，補丁隨 `OFL.txt` 與版權聲明、標為第三方元件，`make_notices` 與 `verify_*.sh` 納入。`LICENSE` 第 1 條 (a) 把「字型烘製結果」列為本作品、第 2 條 (d) 又把字型列為第三方元件，補丁入版控或隨包前，由使用者決定字句如何對齊（`LICENSE` 變更屬需明確授權事項，第 12 節 U5）。預設不散布，所以不阻擋 L0、L1。
- Copyleft 字型（GPL 等）對衍生字模與語言包的影響必須讀授權全文後判定，未判定前不使用。
- 不使用原版字型（`CFONT.15`）作為其他語言字模的來源。
- 簡體、日文（新字體）、韓文的涵蓋字集要對照該語言的譯文用字，缺字在烘製時失敗。

### 3.8 F4 與遊戲內語言

本規格對 `AGENTS.md` 第 12 節「F4 切換語言（繁體、簡體、韓文、英文、日文）」的解讀：**F4 切換的是單一語言設定 `lang`**（`docs/spec/006` 第 7 節的偏好設定，不新增欄位），其效果分兩層：

- 前端介面文字：立即生效（`docs/spec/006` 第 5 節）。
- 遊戲內文字：`LangDir` 在 `Session.Open` 綁定，所以**下次啟動時生效**，生效與否依第 3.2 節的啟用規則。
- 旗標 `-ingame-lang <代碼|none|identity>` 與環境變數 `HR_INGAME_LANG` 單獨覆蓋遊戲內語言。覆蓋生效時，F4 只改 `lang`（介面語言），不改遊戲內語言。使用者想要「介面為某語言、遊戲內維持原版」目前只能帶 `-ingame-lang none`（是否持久化獨立的遊戲內語言設定列 U4）。不認得的代碼（不在 `zh-TW`、`zh-CN`、`ko`、`en`、`ja`、`none`、`identity` 之內）當作沒給：`play.log` 記一行，依序往下找環境變數與 `lang`。
- **可用性** `avail(X)`（值是 `(布林, 原因鍵)`；只對 F4 循環的五種語言定義，`none` 與 `identity` 只能由覆蓋旗標指定，不經 F4，它們的 `avail` 值是「未定義」，讀取即 panic，使第 2 步誤讀它的突變可被偵測）：`zh-TW` 的 `avail` ＝ `l10n/zh-TW/` 譯文表存在；其他語言的 `avail` ＝ 該語言的譯文表存在，且 L2 已實作（常數 `l2Supported`，第 3.2 節規則 4），且補丁在手。`avail` 不要求建置成功，因為建置要下次啟動才知道。`avail(X)` 為假時的**原因鍵**依序判定，先中先停：沒有該語言的譯文表 → `no-table`；L2 尚未實作 → `unsupported-language`；補丁不在手 → `no-patch`。`zh-TW` 沒有譯文表時 `avail` 為假、原因 `no-table`，但這時生效的原版與 `zh-TW` 視為相同（見下）。
- **相同關係**：選擇 `S` 與生效 `E` 只在下列情形視為相同，其餘為不同：`S ＝ none` 且 `E ＝` 原版；`S ＝ identity` 且 `E` 為 identity 種類的包；`S ＝ zh-TW` 且 `E` 為 identity 種類的包或 `zh-TW` 表包；`S ＝ zh-TW`、`E ＝` 原版且 `avail(zh-TW)` 為假；`S ＝` 其他語言 X 且 `E ＝` X 的語言包（其他語言包帶語言代碼）。
- **F1「遊戲內文字」的狀態與 F4 提示**由同一個純函式 `ingameStatus(S, E, startFail, override, avail)` 決定，輸出 F1 值、原因鍵與 toast 鍵（`docs/spec/006` 第 10 節的純函式清單加入它，第 11 節）。輸入：**生效** `E`（原版，或通過 manifest 驗證的語言包；包的種類是 identity 包（manifest 模式為 identity，或採用列數為 0：譯文表存在但全是 `candidate` 或 `keep`）、`zh-TW` 表包（採用列數大於 0）、其他語言包）；**啟動失敗** `startFail` ＝ `(C_start, 原因鍵)`，沒有則為空（`C_start` 是啟動時決定的遊戲內語言）；**選擇** `S`（覆蓋旗標生效時是覆蓋值，否則是 `lang` 的目前值，F4 會改它）；`override`（覆蓋旗標是否生效）；`avail` ＝ `avail(S)` 的 `(布林, 原因鍵)`。**前置條件**：`S ＝ none` 蘊含 `override` 為真、`E ＝` 原版且 `startFail` 為空；`S ＝ identity` 蘊含 `override` 為真，且 `E` 是 identity 包，或 `E ＝` 原版且 `startFail ＝ (identity, ·)`；測試在這個域內斷言函式全定義（第 8 節的性質測試）。F1 值分四類（(1) 至 (4)），字句模板共五個：(1) `原版（繁體中文）`、(2) 的 `語言包 <代碼>（部分翻譯）` 與 `語言包 <代碼>（原版文字，驗證用）`、(3) `已選 <S>，下次啟動生效`、(4) `已選 <S>，無法使用：<原因>`。**依序判定，先中先停**：
  1. `startFail` 非空，且 `S ＝ C_start`（選擇沒有被 F4 改走）→ F1 (4) `已選 <S>，無法使用：<startFail 的原因鍵>`；toast「遊戲內文字：無法使用（維持原版）」（啟動失敗時 `E` 必為原版）；
  2. `S` 與 `E` 不同：`avail(S)` 為真 → F1 (3) `已選 <S>，下次啟動生效`，toast「遊戲內文字：下次啟動生效」；`avail(S)` 為假 → F1 (4) `已選 <S>，無法使用：<avail 的原因鍵>`，toast「遊戲內文字：尚無語言包」；
  3. `E` 為語言包 → F1 (2) `語言包 <代碼>（部分翻譯）`；identity 包（含採用列數為 0 者）則寫 `語言包 <代碼>（原版文字，驗證用）`，不標「部分翻譯」；toast「遊戲內文字：不變」；
  4. 其餘 → F1 (1) `原版（繁體中文）`，toast「遊戲內文字：不變」。
  `override` 為真時，toast 一律是「遊戲內文字：由旗標指定，不隨 F4 改變」（先於上列各步），F1 值仍依上列各步判定（F4 不改 `S`，所以 `S` 與 `E` 的關係在整個執行期間固定）。`startFail` 的原因鍵只有 `build-failed`（建置錯誤、序號用盡、資料目錄不可寫）與 `verify-failed`（manifest 驗證失敗、`LangDir` 不存在）。`<原因>` 是有鍵的列舉（進字串表，五種語言）：`no-table`、`build-failed`、`verify-failed`、`no-patch`、`unsupported-language`，F1 顯示該語言的譯名，不顯示原始鍵；`<S>` 與 `<代碼>` 顯示字串表中的語言譯名，`identity` 顯示字面 `identity`（ASCII，字元表已含）；ASCII 細節只寫 `play.log`（避免字元不在介面字型子集內）。toast 是語言名稱（沿用 `docs/spec/006` 第 5 節）接上字句，單行；測試斷言五種語言的最長組合在 `fitLine` 下不被截斷。
- **真值表**（每列一個案例，測試逐列斷言，第 8 節）：

  | # | 情形 | S | E | startFail | override | avail(S) | F1 | toast |
  |---|---|---|---|---|---|---|---|---|
  | 1 | 預設啟動，沒有 `l10n/zh-TW/` | zh-TW | 原版 | 無 | 否 | (假, `no-table`) | (1) | 不變 |
  | 2 | 預設，F4 一圈回到 zh-TW（輸入與列 1 相同，算同一個案例） | zh-TW | 原版 | 無 | 否 | (假, `no-table`) | (1) | 不變 |
  | 3 | 預設，F4 選 ko，沒有表 | ko | 原版 | 無 | 否 | (假, `no-table`) | (4) `no-table` | 尚無語言包 |
  | 4 | 預設，F4 選 ja，L2 前有 `l10n/ja/` | ja | 原版 | 無 | 否 | (假, `unsupported-language`) | (4) `unsupported-language` | 尚無語言包 |
  | 5 | L2 之後，F4 選 ja，有表有補丁 | ja | 原版 | 無 | 否 | (真) | (3) | 下次啟動生效 |
  | 6 | `-lang zh-TW`，`l10n/zh-TW/` 存在（有 `accepted` 列），建置成功 | zh-TW | `zh-TW` 表包（採用列數 > 0） | 無 | 否 | (真) | (2) 部分翻譯 | 不變 |
  | 7 | 同 6，F4 選 ko，沒有表 | ko | `zh-TW` 表包（採用列數 > 0） | 無 | 否 | (假, `no-table`) | (4) `no-table` | 尚無語言包 |
  | 8 | `-ingame-lang zh-TW`，`l10n/zh-TW/` 存在（有 `accepted` 列） | zh-TW | `zh-TW` 表包（採用列數 > 0） | 無 | 是 | (真) | (2) 部分翻譯 | 旗標指定 |
  | 9 | `-ingame-lang zh-TW`，沒有表 | zh-TW | identity 包 | 無 | 是 | (假, `no-table`) | (2) 驗證用 | 旗標指定 |
  | 10 | `-ingame-lang identity`，建置成功 | identity | identity 包 | 無 | 是 | 不定義 | (2) 驗證用 | 旗標指定 |
  | 11 | `-ingame-lang none` | none | 原版 | 無 | 是 | 不定義 | (1) | 旗標指定 |
  | 12 | `-ingame-lang ja`，L2 之前有 `l10n/ja/`（不建置） | ja | 原版 | 無 | 是 | (假, `unsupported-language`) | (4) `unsupported-language` | 旗標指定 |
  | 13 | `-lang ja`，L2 之後有表有補丁，建置失敗 | ja | 原版 | (ja, `build-failed`) | 否 | (真) | (4) `build-failed` | 無法使用 |
  | 14 | 同 13，驗證失敗 | ja | 原版 | (ja, `verify-failed`) | 否 | (真) | (4) `verify-failed` | 無法使用 |
  | 15 | 13 之後 F4 選 ko，沒有表（第 1 步因 `S ≠ C_start` 不成立） | ko | 原版 | (ja, `build-failed`) | 否 | (假, `no-table`) | (4) `no-table` | 尚無語言包 |
  | 16 | 15 之後 F4 繞回 ja | ja | 原版 | (ja, `build-failed`) | 否 | (真) | (4) `build-failed` | 無法使用 |
  | 17 | `-ingame-lang identity`，建置失敗 | identity | 原版 | (identity, `build-failed`) | 是 | 不定義 | (4) `build-failed` | 旗標指定 |
  | 18 | `-ingame-lang ja`，沒有 `l10n/ja/` | ja | 原版 | 無 | 是 | (假, `no-table`) | (4) `no-table` | 旗標指定 |
  | 19 | `-lang zh-TW`，有表，建置失敗 | zh-TW | 原版 | (zh-TW, `build-failed`) | 否 | (真) | (4) `build-failed` | 無法使用 |
  | 20 | 預設啟動沒有表，F4 由 ko 繞回 zh-TW，之後才放入 `l10n/zh-TW/` | zh-TW | 原版 | 無 | 否 | (真) | (3) | 下次啟動生效 |
  | 21 | `-ingame-lang zh-TW`，`l10n/zh-TW/` 存在但全是 `candidate`，table 模式建置成功 | zh-TW | table 模式，採用列數 0（視同 identity） | 無 | 是 | (真) | (2) 驗證用 | 旗標指定 |
  | 22 | `-ingame-lang zh-TW`，有表，建置失敗 | zh-TW | 原版 | (zh-TW, `build-failed`) | 是 | (真) | (4) `build-failed` | 旗標指定 |
  | 23 | `-lang zh-TW`，`l10n/zh-TW/` 存在但全是 `candidate`，table 模式建置成功（預設路徑上最容易出現「驗證用」的情形） | zh-TW | table 模式，採用列數 0（視同 identity） | 無 | 否 | (真) | (2) 驗證用 | 不變 |
- 預設設定下沒有譯文表，所以 F4 切到任何語言後遊戲內文字都維持原版（前言）。混合語言畫面（第 9 節）只出現在使用者自己建出語言包的機器上，是否可接受由使用者決定（第 12 節 U4）。
- 發行說明標示「部分翻譯：對白與敘述」，F1 的 (2) 標示（部分翻譯）；兩處都不稱「支援某語言」。
- **前端實作的補充**（`docs/re/030`）：F1 在兩次 F4 之間沿用上次（或啟動時）算好的 `avail`，不在每幀掃檔案系統，所以 F4 之外放入或移走譯文表要到下一次 F4 才反映；字型載入失敗的 ASCII 退回版，F4 提示的語言名稱用語言代碼；啟動日誌前綴 `ingame:`、內容只有 ASCII 記號與雜湊，寫標準錯誤與 `<資料目錄>/play.log`（標籤 `lang`，每次啟動至少一行，預設路徑也有）；介面語言不是 `zh-TW` 而沒有該語言譯文表時，F1 一開就是 (4)，不必先按 F4（真值表列 3 與 18 的輸入）；`l2Supported` 與 `patchInHand` 在 `apps/hr/play` 與 `apps/hr/l10n` 各有一份常數，L2 實作時要同步。

### 3.9 洩漏防線

進版控的檔、`docs/re/` 的收據與子代理報告搬運的路徑，一律遵守：

1. 只含 id、計數、雜湊、位址與個別字碼，不含原版對白、敘述等整句文字，也不含含原文的樣張、before/after 對照。樣張、批次報告、對照圖只放 `workplace/`。**短 UI 標籤**（單行 <= 7 個字）的引用在證據文件中可能必要（例如 `docs/re/012` 引用了遊戲內提示與選單字串），登記於 `tools/l10n/leakscan-allow.tsv`（只含路徑與單位身分；工具拒絕登記所屬段（`0x00` 與 `0x0A` 之間，段起點由單位身分的位移取得）超過 7 個字的單位，避免長句被 ASCII 或 `%` 序列切成多個短片段後逐片段登記；字數以解碼後字元數計，雙位元組字與單位元組字元各算一字），由使用者在審查時確認（第 12 節 U8）；登記以外的命中仍失敗。
2. 譯文表的 `note` 欄與詞表禁止含原文，由建置器以下述內容判準檢查。
3. **內容判準（演算法）**，由 `hrl10n leakscan` 實作：
   - 單位：**與建置器的解析器無關**（所以基準掃描能在 L1 解析器完成前進行）：由使用者原版的七個資料檔（`COUNTRY.MES`、`SP.MES`、`SYSTEM.MES`、`UWASA.MES`、`POWERMES.MES`、`ESPMES.MRG`、`SHOPTAB.TBL`，不含 `CFONT.15`：點陣字模沒有文字，對齊解碼只會得到偶然成立的片段）的原始位元組，以 `0x00` 與 `0x0A` 切段（偏移表的位元組會在段內造成雜訊，被對齊解碼的過濾擋掉）；每段做對齊的 Big5 解碼，取出**連續雙位元組字的片段**（遇 ASCII 或無法解碼的位元組就切開）；只取長度 >= 3 個字的片段，且所屬段長度 >= 8 bytes（純 ASCII 與 `%` 格式的段不取，避免誤報；更短的片段與一般詞無法區分）。**單位身分** ＝ `<原版檔名>@<段起點位移（十六進位）>.<片段序號>`，不依賴解析器；解析器就位後，輸出另附對應的 `ESPMES#<群組>.<子>` 等項目 id 供閱讀，登記與比對仍以單位身分為準。細節：檔名大寫，位移為大寫十六進位且無前導零，片段序號由 0 起算且只算 >= 3 字的片段；3 至 5 字與 >= 6 字的分類以正規化後的片段長度為準，不是抽取時的原始字數；結構合法但 `golang.org/x/text` 解不出的雙位元組碼標為「僅位元組形式」（原版目前 0 個）；單位來源除上述七個資料檔外加片頭文字檔 `OP.TXT`、`OP0.TXT` 至 `OP5.TXT`（純文字，抽取規則不需改動），來源檔缺任何一個即失敗。
   - **正規化**：兩邊（單位與被掃檔案文字）走同一條路徑，逐字元分類為切斷、可移除、標點、成員四類：
     - 切斷：ASCII 英數、全形英數以外的半形英數、`golang.org/x/text` 的 Big5 解不出的字元；全形英數統一後保持原樣，留在片段內當成員（它們是原版字模內的雙位元組字，SHOPTAB 的名稱有近半數含全形英數），半形英數則切斷片段，兩者不互相等同。
     - 可移除：空白、控制字元、Unicode 格式字元（類別 Cf，例如零寬空白、BOM、軟連字號）、ASCII 標記字元（反引號、星號、底線、`>`、`<`、`|`、`#`、`^`、`~`、反斜線、單雙引號、括號）與全形括號引號（Unicode Ps、Pe、Pi、Pf）。
     - 標點：其餘標點與符號，全形與半形統一成同一個符號，留在片段內（讓單位片段的字數與「連續雙位元組字」的定義一致，6 字視窗才能跨過逗號），片段頭尾的標點去掉。
     - 成員：Big5 可解的非標點字元。
     - 可移除字元同時做「連接」（直接去掉，行內被標記或跳脫換行切開的引用仍命中）與「切開」（當分隔，表格儲存格與逐行列出的短標籤各自成片段）兩種處理，命中取聯集。
     - 跳脫還原：`\n`、`\r`、`\t` 視為空白類，`\\` 視為一個反斜線，`\uXXXX` 與 `\UXXXXXXXX` 還原成該碼位的字元（JSON `ensure_ascii` 輸出與原始碼字串常值）；`0xHH` 與 `\xHH` 序列、空白分隔或連續的十六進位對（>= 12 個位元組）還原成位元組。
   - **比對**：長度 >= 6 個字的片段，以連續 6 個字（12 bytes）的滑動視窗比對，所以引用一行中的半句也命中；3 至 5 個字的片段只比整段相等（被掃檔案切出的片段與單位片段逐一比相等；嵌在較長連續 CJK 文字內的 3 至 5 字片段不命中，避免與一般詞誤報，列入已知漏報）。被掃檔案的文字同樣先切成連續 CJK 字的片段再比對（被 ASCII 或標記隔開的引用，各片段分別比）。視窗與 3 至 5 字整段鍵至少含 3 個非標點字（`minMembers`）：標點占多數的片段（成排的符號與方框字元的裝飾線、含 <= 2 個非標點字的短片段）與一般文件的標點序列無法區分，不是引用證據，不比對（基準掃描因此從 269 筆命中降到 12 筆）。每個單位以 Big5 位元組與 UTF-8 解碼文字（`golang.org/x/text` 的 Big5；無法解碼的單位只比位元組形式）兩種形式比對；被掃檔案含 NUL 的視為二進位檔，只比位元組形式。
   - 範圍：發行包目錄、`git ls-files` 列出的檔（工作樹內容）、`docs/`、`tools/`，**以及 fork**（`git -C workplace/dosgolem ls-files` 的工作樹內容，因為資料表與 `apps/hr/l10n` 放在可能公開的 fork）；二進位檔只比位元組形式。轉公開前另做**全歷史掃描**（`hrl10n leakscan -history`，對本 repo 與 fork 都掃 `git rev-list --all` 的全部 commit 內容，包含已刪除的檔，`AGENTS.md` 第 2 節）。
   - 輸出：只有路徑（歷史模式加 commit 與路徑）與單位身分，不輸出內容。已知良性命中登記於 `leakscan-allow.tsv`。
   - 已知漏報：簡體轉換版與其他語言的譯文（第 12 節 U1）；`MAIN.EXE`、`OP.EXE`、`END.EXE` 的硬編碼字串（單位只取資料檔與 `OP*.TXT`，歸規格 009；`AGENTS.md` 第 10 節的 push 前檢查要寫明內容判準不涵蓋它們，`docs/re` 對這類字串的引用靠人工複核；基準掃描已證明 `docs/re/012` 引用的標籤在 `MAIN.EXE`，完全不被偵測）；以其他轉寫（例如拼音、部分字替換）引用的文字；base64 等其他位元組編碼的拼寫；3 至 5 個字的單位的十六進位拼寫（6 至 10 位元組，低於 12 位元組的還原門檻）；嵌在較長連續 CJK 文字內的 3 至 5 字片段；沒有查找鍵的單位（標點占多數或非標點字不足 3 個，數量與原因分類由基準收據列出）；UTF-16 檔（含 NUL，只比位元組形式）；標點被刪除或改寫後跨標點的視窗（兩側各 >= 6 個非標點字時仍命中）；commit message 與檔名本身（歷史串流只帶檔案內容）。
4. **入口與接線**：`tools/l10n/leakscan.sh [路徑…]`（Docker，repo 根唯讀掛載、`workplace/orig` 唯讀掛載、`--network none`）。`hrl10n` 的原始碼在 fork，入口腳本在 Docker 內建出執行檔（`golang:1.24-bookworm`、`GOPROXY=off`、fork 唯讀掛載與 `-mod=readonly`，所以 `go.mod` 與 `go.sum` 必須已完整；可寫的只有 `workplace/gocache`、`workplace/gomodcache` 與 `workplace/out`，執行檔在 `workplace/out/hrl10n`）；`tools/package.sh` 呼叫的是這支腳本，不需泛化 `go_build`。fork 主模組的 `go.mod` 先手寫 `require golang.org/x/text v0.29.0`（離線：模組快取 `workplace/gomodcache` 已有該版本的 zip、mod、ziphash 與 `big5.go`，`GOPROXY=off` 可解）。`git ls-files` 與歷史掃描在主機以唯讀 git 產生，經標準輸入餵給容器內的 `hrl10n`（repo 以 `/repo` 唯讀掛載，容器工作目錄 `/repo`，所有路徑都是 repo 相對；本 repo 與 fork 在同一個呼叫、同一個路徑命名空間，fork 的檔案加 `workplace/dosgolem/` 前綴，所以 `leakscan-allow.tsv` 的路徑也這樣寫，避免兩棵樹的同名相對路徑共用同一列登記）。工作樹模式的清單是本 repo 的全部追蹤檔（含 `engine/patches/`、`WORKLOG.md`、`hd/`）加 fork 的全部追蹤檔，以 NUL 分隔（`-files-from0`）。歷史串流的格式：每筆 `<commit>\t<路徑>\t<大小>\n` 加 blob 內容加 `\n`，同一個（路徑, blob）只記第一次出現的 commit（含 merge commit 與已刪除的檔），最後一行 `END\t<記錄數>\n`，記錄數不符或串流在結尾標記之前結束即失敗；路徑含 Tab 或換行時串流產生器失敗。`tools/package.sh` 在既有 `leak_scan`（檔名與雜湊判準，三處呼叫）之內加入它，並加 `test -f workplace/orig/MAIN.EXE`；`tools/pkg/py.sh` 只傳參數不傳環境變數，`HR_WITH_L10N` 豁免用參數。`hrl10n leakscan` 與 `tools/l10n/leakscan.sh` 就位後（L1 第一個交付，第 5 項），`AGENTS.md` 第 10 節的 push 前檢查才加入它（第 11 節：條文與工具同一個提交）。**閘門失敗關閉**：發行與 push 前的閘門在原版缺席時**失敗，不略過**；單元測試在原版缺席時 skip。失敗關閉的完整條件（退出碼 2）：原版單位來源檔缺任何一個，或 SHA-256 與 `apps/hr/runtime/required.tsv` 及 `OP*.TXT` 登錄的雜湊不符（雜湊驗證在 `cmd/hrl10n`，不在 `leakscan` 套件，保住套件的獨立性）；任一來源檔抽不出單位；索引建好後的正對照自檢失敗（取數個單位的 UTF-8 文字與 Big5 位元組各自掃一次，必須命中自己，否則表示分類表或 `golang.org/x/text` 異常使鍵集合縮小）；allowlist 有被拒的行；掃描 0 個檔案或歷史 0 筆記錄（確定要放行時才加 `-allow-empty`，只供測試）；`-files-from` 或 `-files-from0` 的項目不存在（預設失敗，`-skip-missing` 才略過並印計數）；歷史串流缺結尾標記或記錄數不符。退出碼 0 無命中、1 有命中、2 閘門失敗或用法錯誤。
5. **基準掃描是 L1 的第一個交付**：先對現有版控樹、fork，與本 repo 和 fork 的全歷史跑一次，命中數與政策（例如 `docs/re/012` 的短 UI 標籤引用）寫進 `docs/re` 收據，再開始任何原文匯出。登記以外的命中仍使閘門失敗（push 閘門掃的是工作樹；全歷史中的舊引用不能靠改工作樹消除，只能改寫歷史，所以歷史命中記入收據，不是 push 閘門的條件，處理方式在轉公開前由使用者決定，`AGENTS.md` 第 2 節），所以工作樹命中的處理順序是：先由主代理把證據文件中的引用改成單位身分與位址（不需使用者答覆），剩下必須保留的短 UI 標籤才交使用者決定是否登記（第 12 節 U8）；U8 回答前，閘門對未處理的命中失敗，push 前先處理完。**偶然命中的補救路徑**：來自長段（所屬段 > 7 個字）的 3 至 5 字片段，可能與不相干的檔偶然相等（基準掃描有數筆落在 fork 內其他遊戲專案的程式與上游文件，收據見 `docs/re/028`）。這類單位不得以一般登記處理（登記上限擋的是逐片段還原長句），補救只有兩條：改動命中的檔，或由使用者在 U8 決定另開「偶然命中」登記區，限定每個路徑最多 2 筆且合計字數 <= 10。使用者回答前，兩條都不自行採用，命中維持失敗。
6. `tools/pkg/leakscan.py` 的路徑規則沿用並加 `l10n`、`l10n-packs`（`HR_WITH_L10N` 時 `l10n` 路徑豁免，內容判準仍執行；`l10n/zh-TW` 的譯文表與原版逐字相同的行必然命中內容判準，所以 **`zh-TW` 譯文表不隨包**，`tools/package.sh` 以**路徑級排除**（`l10n/zh-TW/` 一律不複製進包）強制，不只靠內容命中）。
7. 負對照的 fixture 在測試執行時由使用者原版產生到暫存目錄，**不入版控**。
8. `.gitignore` 已含 `/l10n/` 與 `/l10n-packs/`；決定譯文表進版控後才移除前者。若要附進發行包，旗標 `HR_WITH_L10N`（比照 `HR_WITH_HD`）附**譯文表與補丁，不附語言包**，版本字串加後綴，附說明檔，只供私人流通；repo 保持 private，轉公開前處理 git 歷史，並由使用者決定是否調整 `LICENSE` 第 2 條 (c) 對譯文的措辭。

### 3.10 翻譯流程

- 原文（匯出的 `src_text`）**只送往 Claude Code 子代理**（與主 session 同一服務）。主代理自己讀解碼後的原文（例如 L1 試點改寫）與子代理的暴露面相同，同屬這個範圍，不是降低依賴的辦法。其他服務（codex、外部機器翻譯、第三方譯者）先問使用者（第 12 節 U2；`AGENTS.md` 第 12 節 M8 的先例：外送原版美術被分類器擋下）。
- 2026-10-04 使用者回覆「授權整個 M10 文字範圍」，因此 Codex 可處理本專案 M10 原文；這是上一項外送預設的明示例外。其他服務、譯文表入版控與隨包發行沒有因此獲授權。
- 翻譯子代理的 prompt 逐項引用 `AGENTS.md` 第 11 節：可寫目錄 `workplace/l10n-work/<代碼>/<批次>/`（批次唯一檔名）、唯讀來源 `workplace/l10n-src/`、禁止修改的目錄（其他 repo、`~/.claude/`、`~/.cache/`、`/home/anr2/cht/dosgolem`）、禁止 commit 與 push、Docker 規則、`hr-*` 前綴、禁止 prune 與 rmi；另寫明：禁止 WebFetch、WebSearch 與 `isolation: remote`（原文不得出境）；回報只放 `workplace/l10n-work/`，不含 before/after，不得搬進 `docs/re/`；同一份指令檔與固定的模型階層。批次流程依 `~/.claude/knowledge-base/workflows/batch-subagent-localization.md`（七步，含全域一致性掃描）。
- L3 閘門含「試作一批給使用者確認風格與尺度」。
- `accepted` 只能在使用者明示接受後，由主代理批次設定，並記錄日期、範圍與接受語句（比照 `AGENTS.md` 第 12 節對 HD 的做法）。定義：機械檢查通過，加獨立回譯審查，加使用者看版面樣張，並標示「未經母語者審閱」。以抽樣加整體接受取代逐條（抽樣比例與最壞案例，即最長行、最多行，寫進閘門）。
- 專有名詞策略（對白內人名地名先譯或先保留）與 `SHOPTAB` 的納入時機（商品名也出現在硬編碼的道具名表，單獨翻譯會與背包畫面不一致；`SHOPTAB` 名稱欄的使用端尚未追，L3 前補）列使用者決定（第 12 節 U4）。

## 4. 階段與閘門

| 階段 | 內容 | 出口條件 |
|---|---|---|
| L0 | dosgolem 語言層、寫入模式開檔拒絕、`searchFor`、`LoadState` 預檢、開檔層報告 | 單元測試通過（第 8 節）；冷啟動 A/B：`LangDir` 為空的 Session，在 90M 步後的畫面 PNG 雜湊、CPU 暫存器、`machine.StateDigest`，與 **L0 實作前同一輸入下記錄的基準**相同（基準綁定 commit 與乾淨工作樹或記錄差異，記在 `docs/re` 收據；不比較同一條程式路徑，那是恆真）；新增的需原版測試 skip 數為 0，既有環境變數閘門的 skip 另列並註明在 test-diag 段實跑，附收據；收據含與 DOSBox-X `Overlay_Drive` 的比對差異（第 1 節實作位置列） |
| L1 | 建置器：解析、序列化、預算檢查與 `1676` 模擬器、譯文表、manifest、洩漏判準（基準掃描為第一個交付）；**前端接線**（`apps/hr/play`：旗標、啟動建置、F1 狀態列四類值、F4 提示五種字句（第 3.8 節的 `ingameStatus` 與真值表），在 006 的實作就位之後加上；新字串使字元表與字型子集重產） | 七個檔案「解析再序列化等於原位元組」（SHA-256 相同，ESPMES 項目總數為 1024，獨立的總數斷言）；預算檢查與模擬器單元測試（模擬器對 023 的 T0／T1／T3 與 `docs/re/025` 的冷啟動連鎖實驗 oracle 對拍）；繁中 identity 語言包（`-ingame-lang identity`，全部 `keep`）冷啟動 A/B 與 L0 基準相同；**玩家端冷建置**：Linux 實跑，Windows 以 Wine 實跑（擴充 `verify_appimage.sh`、`verify_wine.sh` 做 identity 包冷建置，用同一個旗標並把 `manifest.json` 拷出），macOS 只驗結構並註記未實機；替代證據：Linux 與 Wine 建出同一包的 `manifest.json` 雜湊相同；前端接線：`ingameStatus` 真值表 23 列的前端單元測試與 `gui` 收據；洩漏防線：基準掃描收據（第 3.9 節第 5 項）、`hrl10n leakscan` 單元測試、`tools/package.sh` 整合；預算統計收據（在容器內重新統計：計算慣例下超過 30 bytes 的含 `%s` 行數，與 `R_item > H` 的項目清單，只列 id 與計數，第 9 節；加 `_vsprintf` 實參長度與結尾位元組遙測，第 3.5 節）；第 8 節沒有標 L2 的列全部通過；skip 數為 0 |
| L1 試點 | 垂直切片，語言為繁體改寫（`l10n/zh-TW/` 譯文表，字限 `charmap-zh-TW.tsv`，不需 L2）。**建置與驗證路徑**：試點譯文在 U7 預設下是 `candidate`，所以用 `hrl10n -with-candidates` 建包（第 3.3 節），先以 `hrl10n verify` 驗證（收據含驗證輸出與 manifest 雜湊；竄改包內一個檔時流程必須在 `verify` 步驟失敗），再以 `probe`、`hrbot` 的 `-lang-dir` 與 `tools/play.sh` 的測試入口載入（identity 包重跑冷啟動點擊腳本也先 `verify`）；前端內嵌的建置器只顯示 `accepted`，不用於試點畫面。**項目限定**：`ESPMES#121.0` 至 `#121.15`（冷啟動 16 句開場對白，都不含 `%`，024）與 `SP.MES#56`（點據點再點選單項目，不含 `%`，冷啟動收據 `docs/re/025` 第 2 節），共 17 項。`SP.MES#56` 的冷啟動收據是 probe 層級（沒有 `LangDir`、沒有 hr 執行層 Session，`docs/re/025` 第 6 節），所以先以 identity 包（`probe -lang-dir`）重跑同一個點擊腳本，確認同樣在 `SP.MES` 讀到 seek 226、6495 與 135 bytes，再換譯文包；點擊間隔很長，預期不受譯文繪製差異影響，但這是假設，由收據證明。驗證行寬、行數、折行、序列化與真畫面。量測各畫面字元來源比例（`287C:02E1`（`198C:02E1`）的來源字串位址，檔案緩衝對硬編碼區）作為使用者決定 U4 的數字。**`1676` 模擬器的畫面層級驗證**有兩層：(1) **冷啟動字面前綴實驗**：照 023 的 T0／T1 做法改 `ESPMES#121.0` 的 22 bytes，用字面位元組（S 集 lead 加 P 集 trail 等）模擬「`%s` 展開的名稱結尾為位移狀態」；`docs/re/025` 第 3、4 節已有 7 組先寫預測後實測的收據，**預測 7／7 吻合**（併行：`FD` trail、三字 P 集 trail 連鎖、`A4E0 E1E2`；兩行：S 集 trail 恢復的各變體與 `E040 E17E`），L1 以它們當模擬器的 oracle 並擴充未測的 `FE`、`FF`、`7F`、`80`、`A0` trail 與 lead `F9`、`FA` 至 `FC`、`81` 至 `9F`，另加一組變體（用 023 的 T3 先例所用的 `ESPMES#121.1`，該項長 60 bytes，`#121.0` 的 22 bytes 放不下）：P 集位元組放在偏移 30（0 起算，即第 31 個位元組、`si ＝ k - 1`），預測第二次呼叫的偏移為 32（`k ＋ 1`），偏移 32 至 34 為 `E0 E1 0A`；槽位前 30 個位元組全為 S 集且不含 `0x20`、`0x25`（相位在前綴內不變）、偏移 31 取 S 集位元組（不是 `0A` 或 NUL）、偏移 35 起至少再接 1 個 S 集位元組才接 NUL。觀測量是 `1676` 的呼叫序列，以緩衝內絕對偏移列出（`2F51:0423` ＝ 1059 起）：同步假說預測 1059、1091、1094；若第二次呼叫改從位移狀態起算，`E0` 被吃、`E1` 多吃 `0A`，只有 1059、1091 兩次呼叫，兩個假說因此可分；對照組：P 集位元組放在偏移 29，偏移 30 起全為 S 集位元組（不含 `0A`）直到 NUL，預測 1059、1090 兩次呼叫，兩個假說的預測相同（它是兩個假說預測相同的控制，與 023 的 T3a、T3b 先例一致）；填充位元組一律避開 `0x20`（`01A3` 路徑會略過它，使緩衝內偏移與槽位偏移不同）與 `0x25`（`%` 轉換規格的起頭）；其餘涵蓋限制（trail `01` 至 `1F`、其他窗口只有讀碼推論、同類別逐值靠判斷表的靜態確認）在收據註明；觀測量是 `1676` 各次呼叫的**字串偏移**與呼叫次數（`ESPMES#118.2` 在基準上就因寬度停止有兩次呼叫，所以不能只看次數）；(2) **`ESPMES#118.2`**（承接 `docs/re/025` 第 6 節未測的「`%s` 展開後接 `0x0A`」畫面；含 2 個 `%s`，可達路徑是 bot 檢查點狀態 `t06978.state`，檢查點與 Session 的 `LangDir` 皆空，所以可用 `probe` 的 `-scratch` 以測試專用暫存層放改過的 `ESPMES.MRG`（保持長度、不動偏移表），不是產品路徑），在名稱結尾已知（`-peek` 讀 `2F51:0423`）的狀態下改寫 `%s` 之後的位元組，至少 6 個變體（預測併行與預測分行各至少 3，不足由補充變體湊足，含 `%s` 緊接 `0x0A`、後接 S 集 trail 字元、後接 P 集 trail 原碼字、兩字連鎖、lead 在 `E0` 至 `F9`），畫面實測的字串偏移必須吻合預測。`SYSTEM.MES` 的可達項目以項目級覆蓋遙測（第 5 節）找到後再加 | 試點包的畫面樣張使用者過目；冷啟動前綴實驗的預測與實測吻合（不吻合者以實測為準修正模擬器與第 2 節敘述，再回到審查）；`ESPMES#118.2` 變體的預測與實測吻合，收據標明畫面來源是 bot 檢查點加暫存層；若 `ESPMES#118.2` 的檢查點無法重播，(2) 退為 (1) 加 023 的 T0／T1／T3 oracle（(1) 有冷啟動畫面證據） |
| L2 | 字模補丁與自訂碼（第 3.4 節，**不在 READY 範圍**） | 開工前提見第 3.4 節；出口：補丁決定性與第 3.4 節的拒絕契約逐項通過；「碼位置換等價包」僅為 `workplace/` 中忽略版控的原版 oracle 測試副本：把一批原版字改編成自訂碼，暫時在這些碼位放原版同字字模，畫面像素與原版**逐位元相同**，範圍限定在全行 <= 30 bytes 的 ESPMES 項目（368 個，審查 A 第二輪）並扣掉 38 行名單，所以沒有折行與溢位差異。此測試副本用後清理，不得放進正式 OFL 補丁、語言包、版控或發行包；正式補丁仍只從 OFL 字型烘製。另做合成測試：自訂碼位置放已知字模，dosgolem 的 `-call-args 198C:05A2` 取到的 `(lead, trail)` 引數符合放入的碼，`_lseek`（`1000:098F`，執行期 `0110:098F`）的偏移符合公式、`_read` 的 30 bytes 等於放入的字模 |
| L3 | 逐語言導入（簡體、日文；韓文與英文待第 3.6 節） | 每個語言：字模來源通過盤查；字集不超過可用碼數；譯文表全部項目非 `candidate`；樣張使用者過目；**長跑**（第 5 節）；同狀態收據；使用者決定譯文的權利處理（第 12 節 U1） |
| L4 | 規格 009：硬編碼字串與段 4073 | 不在本規格；排程列入 `AGENTS.md` 第 13 節 |
| L5 | 執行中換 `CFONT.15` | 實驗：dosgolem handle 換檔的可行性與副作用。靜態推論安全（023 第 7 節），未實驗；通過才可讓 F4 同步帶動遊戲內語言而不重啟 |

READY 的範圍：本規格升 READY 時只授權 L0 與 L1（含試點）。L2 以第 3.4 節前提完成後的修訂版升 READY；L3 每個語言以「來源盤查文件加樣張通過」為前提，在該語言的 `docs/re` 收據中記錄後才實作。

## 5. 可達性與長跑

可達性（023 第 6 節、024 第 3.1、3.3 節、025 第 2 節）：

| 檔案 | 觸發 | 等級 |
|---|---|---|
| `ESPMES`（群組 121） | 冷啟動新遊戲第一句起的 16 句開場對白，冷啟動直達 | confirmed |
| `ESPMES#118.2`（含 `%s`） | bot 檢查點狀態 `t06978.state` 加 12 次左鍵，不是冷啟動直達 | confirmed（動態收據） |
| `SP.MES` | 世界城鎮地圖點據點，再點彈出選單的唯一項目；已用 `-click-premove 3 -click-polls 3` 動態重現，起點有 soak 檢查點與**冷啟動**兩種（冷啟動指令見 `docs/re/025` 第 2.1 節） | confirmed |
| `COUNTRY.MES` | 世界地圖畫面（`GMAP.PXS`）主迴圈的第二個工具列熱區 | 靜態鏈與 soak 收據共現，強推論；動態重現未成功 |
| `UWASA.MES` | 城鎮選單酒店指令，且被詢問人物要在某國 16 格名單內才讀 | 強推論（靜態鏈）；動態：未知 |
| `SHOPTAB.TBL` | 每次建城鎮選單與執行城鎮指令 | bot 收據開檔 confirmed |
| `SYSTEM.MES`、`POWERMES.MES`、`ESPMES.MRG` 其餘 | bot 長跑開檔 | confirmed（開檔）；顯示窗口對應部分未歸屬；`SYSTEM.MES` 的觸發條件與含 `%s` 項目的可達性未查 |

- 長跑無法證明 `COUNTRY.MES`、`UWASA.MES`、`SP.MES` 的語言包被讀到。這三個檔的 L1 驗收靠檔案層測試（開檔層斷言）與合成包，並在收據標明「畫面未覆蓋」（`SP.MES#56` 在試點有畫面）。
- **項目級覆蓋遙測**：對 `237B:0464`、`24B2:0111`、`24B2:0030` 用 `-call-args` 或 `OnCall` 記 `(檔, 索引)`（位址用執行期位址 `148B:0464`、`15C2:0111`、`15C2:0030`，IDA 位址減 `0x0EF0`），報告每輪看過多少項目；沒看過的項目靠最壞案例樣張（最長行、最多行）。
- **L3 長跑閘門**：每個語言包以機器人跑 `docs/re/016` 同規格（2 種子 x 2 遊戲小時，冷啟動起跑），報告最低 SP 與原版基準比較、疑似凍結、T2 轉儲，偵測器正對照；譯文長度與 `vsprintf` 展開會改變堆疊與緩衝使用。

## 6. 失敗模式

| 情形 | 預期 |
|---|---|
| 原版輸入雜湊不符 | 建置失敗，不產生語言包 |
| 譯文表 `src_sha256` 與原項目不符 | 建置失敗，點名項目 |
| 譯文違反預算（長度、控制碼、空白、白名單、佔位符、`1676` 模擬、行寬、行數、缺字碼） | 建置失敗，列出全部違規項目的 id |
| `COUNTRY.MES` 或 `SHOPTAB.TBL` 有非 `keep` 列而旗標未開 | 建置失敗，點名檔案與旗標 |
| 字集超過可用自訂碼數（L2） | 建置失敗，列出超出的字 |
| 譯文含白名單外且沒配到字碼的字 | 建置失敗（不得以 `?` 或空白悄悄替換） |
| `accepted` 列的 `acc_sha` 與 `text` 不符 | 視為 `candidate`，建置報告標示 |
| 建置失敗（含序號用盡、資料目錄不可寫） | 不阻擋遊戲：遊戲內文字維持原版，`play.log` 記一行，F1 顯示 `build-failed`；不留下可通過驗證的語言包 |
| 建置中斷 | 同層暫存目錄，manifest 最後寫，整目錄改名；中斷後驗證必須拒絕 |
| 語言包 manifest 驗證失敗（檔案缺、雜湊或大小不符、`files/` 內有 manifest 未列的檔、輸入雜湊不符），或缺 `CFONT.15`（L2 之後） | 不啟用該語言包，記 `play.log` 一行，遊戲內文字維持原版，F1 顯示 `verify-failed` |
| `LangDir` 指向不存在的目錄 | 等同空，`Open` 把生效值清為空字串，記一行，F1 顯示 `verify-failed` |
| 語言包缺某檔案 | 該檔案回退原版（語言層缺檔規則），建置報告標示 |
| 載入的狀態檔記錄的 `LangDir` 或 `LangManifest` 與目前不同 | `LoadState` 在任何狀態變更前明確拒絕，錯誤訊息點名兩個值，Session 不變 |
| 寫入模式開語言層的檔 | 拒絕（存取被拒），不複製進暫存層 |
| 長跑中語言包造成無進展或例外 | 依 `AGENTS.md` 第 6 節的停機分類，另加「語言包內容」一類（條文與落點見第 11 節）：同輸入冷啟動，分別用 identity 包與譯文包，比對停機點，不用狀態檔 |

## 7. 玩家垂直路徑與存檔影響

玩家路徑：啟動（帶或不帶語言包）、新遊戲、對話與選單、商店、存檔與讀檔、F4 切換語言（下次啟動生效）。語言包只影響顯示：句子層級的檔案類文字不在存檔內，所以存檔位元組不隨語言改變；專有名詞（勢力名等）在存檔內的名稱欄位維持原文，檔案類文字走譯文，**畫面上同一勢力可能兩種寫法**（已知差異）。`FNAME.DAT` 的國名 token 來自段 4073（不翻譯）。`SHOPTAB` 的譯文對存檔的影響未驗（預設拒絕，第 3.3 節）。存檔與原版互通。收據要求：
- identity 包：同一輸入與步數，`GAMEFILE.00N`、`FNAME.DAT` 與無語言包逐位元組相同。
- 譯文包：因繪製指令數、點擊節奏不同，同輸入同步數到不了同一遊戲狀態，所以不比位元組。改為跨載入：有包存的檔在無包 Session 載入，反之亦然，驗證結構與欄位不變。
- 語言包機器人長跑後，掃描它產生的 `GAMEFILE.00N`，不得出現語言包獨有的位元組序列（以語言包的譯文用字產生掃描樣式）。**正對照**：對一份人為植入該序列的合成存檔，掃描必須命中；掃描範圍含段 4073 與整個存檔檔案。

## 8. 測試

| 承諾 | 測試 | 負對照 |
|---|---|---|
| `resolve` 順序：暫存層、語言層、原版；回退；大小寫；8.3；空 `LangDir` 等同現況；暫存層放同名檔時蓋過語言包 | 單元（暫存目錄，不需原版） | 把語言層與原版順序對調，測試必須失敗 |
| `searchFor` 順序（`Root`、`LangDir`、`Scratch`，後者覆蓋前者） | 單元 | 順序對調，測試必須失敗 |
| 寫入模式開語言層的檔被拒且暫存層不出現副本；改名、刪除、`create` 維持與 `Root` 檔相同語意；層別判斷取代字串前綴（`-saves` 設在語言包父目錄時不誤判）；其他 `resolve` 呼叫者行為一致 | 單元 | 拿掉拒絕，測試必須失敗；把層別判斷換回字串前綴，`-saves` 案例必須失敗 |
| `manifest.json` 在 `files/` 外：`searchFor` 與目錄列舉看不到 | 單元 | 把 `manifest.json` 放進 `files/`，列舉測試必須失敗 |
| `LoadState` 的 `LangDir` 與 `LangManifest` 比對：相同載入成功，不同明確拒絕，舊狀態檔（無欄位）視為空；**`LangDir` 比對失敗後 Session 的機器記憶體與 DOS 狀態摘要不變**（預檢在 `state.Load` 與 `dos.LoadState` 兩處，在任何套用之前）；`StateDigest` 新欄位 `omitempty`，`LangDir` 空時舊摘要不變 | 單元加需原版 | 把預檢移到套用之後，「拒絕後不變」測試必須失敗 |
| 開檔層報告：每個資料檔確實從語言層開啟（`OpenedLayers`、`OnOpenLayer`）；既有 `Opened`、`OnOpen` 簽章不變、既有使用者編得過 | 需原版，冷啟動；編譯期 | 把該檔移出語言層，斷言必須失敗 |
| 七個檔案解析再序列化等於原位元組（含 `COUNTRY.MES` 的 +2 偏差、`ESPMES` 的 125 偏移與空群組、內層 N2 與 `00 FF` 結尾） | 需原版，缺檔明確 skip（閘門不 skip） | 改動一個偏移的位元組，往返比對必須失敗（驗證比較器）；**獨立的總數斷言**（項目總數 1024，每個群組項目數等於 N2 減 1）在解析器多出一項（得到 1034）時必須失敗（往返在解析器與序列化器一致地錯時仍相等，不能當偵測器） |
| 預算檢查全部規則（第 3.5 節每一列各一個違規輸入與一個合法輸入），含計算慣例、窗口未知比照 `win31x4`、渲染列數 (3)；**渲染列數反例**：自造輸入，只類比 `ESPMES#118.2` 的長度與 `%s` 個數（1 行、44 個內容位元組（含 NUL 為 45）、2 個 `%s`，`E_item` ＝ 80，`R_item` ＝ 3），譯文 3 行，前兩行各含一個 `%s`（放在行首與行中）與 23 個字面位元組（字面 25、展開 43），第三行 10 個字面位元組，行尾字取 S 集字元或數字，使模擬器等其他規則通過：(1)、(2) 都合格，渲染列數 2 ＋ 2 ＋ 1 ＝ 5 超過 `max(4, 3)`，建置報告的違規只有渲染列數一項，必須被擋；原項目自己（原版位元組）通過 (2)；**`R_item` 反例**：原項目 1 行 31 bytes 加 3 行短行（`R_item` ＝ 4，引擎實際 4 列），譯文 5 行各 30 bytes 通過 (1)、(2)，渲染列數 5 超過 `max(4, 4)`，必須被 (3) 擋下（`R_item` 的除數若取 `W`，則 `R_item` ＝ 5，譯文會被放行）；兩個反例的行尾字都取 S 集字元或數字，使模擬器與白名單等其他規則通過，建置報告的違規只有渲染列數一項；原項目全 `keep` 時建置不因預算檢查失敗 | 單元（合成輸入，位元組自造，不含原版文字） | 每條規則各一個違規輸入必須被擋；把 (3) 改回只數 `0x0A` 行數，渲染列數反例必須失敗；把 `R_item` 的除數改回 `W`，`R_item` 反例必須失敗；把窗口未知的行寬改回 `E_item`，窗口未知的字面超寬案例必須失敗（案例：`SYSTEM.MES` 類項目，原項目含 `%s` 使 `E_item > 30`，例如 64；譯文一行 40 個字面位元組、不含 `%`，必須失敗） |
| `budget` 套件的補充案例：單項長度的換行計數邊界（窗口 `win63x8`，行樣板 `pairs(A4 40, 20) + "%s1" + 0A` 重複 8 行，尾行使總展開恰 511 通過、512 只回 `length`，兩者字面總長都小於 511）；譯文端渲染列數除數取 `W` 的案例（`%s` 加 5 字加 `1` 重複 4 行，展開恰 31，除數取 `Cap` 則被放行）；`AutoWrap` 最後一列：以 `0x0A` 結尾的行最後一列固定以 `A4 E0` 加 `0A` 結尾時回 `no-breakpoint`，以項目結尾的行最後一列以 `A4 E0` 結尾必須折成功且無違規；`WrapAndCheck`：`AutoWrap` 回報違規的行必在 `Check(輸出)` 的違規內，折完後 `length` 才超過的案例（`win63x8`、原項目 9 列以上、譯文單行 504 bytes 折成 9 列加 8 個換行得 512）；全形數字之後不折行（標點判定只認 lead `A1`）；lead 之後接 NUL、模擬器 `41 00 0A` | 單元（自造位元組） | 拿掉長度規則的換行計數、譯文端除數改成 `Cap`、拿掉 `AutoWrap` 最後一列檢查的 `\|\| term` 或改恆真、標點集合改回 `A1` 至 `A3`、拿掉 lead 後接 NUL 的條件、拿掉模擬器頂端的 NUL 檢查，各必須使對應案例失敗 |
| **`1676` 模擬器**：對 023 的 T0／T1／T3 與 `docs/re/025` 的冷啟動連鎖實驗對拍（具體模式，預測字串偏移）；`%s` 後接 `0x0A` 失敗、後接 NUL 通過、後接 S 集 trail 字元通過；(S 集 lead、P 集 trail) 加 `0x0A` 在兩個離開狀態都失敗（必須失敗）；**`%s` 離開狀態含位移的最小案例**：`%s` 後接 (lead 在 `E0` 至 `F9`、trail 在 `E0` 至 `FE`) 再 `0x0A` 必須失敗（同步離開通過、位移離開失敗）；trail 在 `FD`、`FE` 的行尾字被擋；位移延續反例被擋：無 `%s` 的 `A4 E0 A4 E1 0A`（必須失敗）；`[%s] A4 E0 E1 E2 0A`（必須失敗，同步與位移兩種離開都失敗）；`[%s] E0 E1 E2 E3 0A`（必須失敗，只有位移離開失敗）；`[%s][L1 T1][L2 T2][0A]` 形式（L1 取 `A1` 至 `DF`、T1 取 `E0` 至 `FE`、L2 取 `E0` 至 `F9`、T2 取 `E0` 至 `FE`）；自動折行不選違規折點（以 `0x0A` 結尾的那一列通過模擬）；**性質測試**：對隨機展開位元組串（長度 0 至 20，與 `%s` 以 20 計一致；字母表排除 `0x00` 與 `0x0A`），搭配固定語料加隨機的樣板行（必須含只有位移離開失敗的 `[%s] E0 E1 0A` 與只有同步離開失敗的 `[%s] E0 E1 E2 0A`），具體模式判定失敗者，對抗模式必須也判定失敗（對抗模式是上界，這個性質與長度上限無關；另加確定性窮舉：展開字串取類別字母表 {S, P}（各取一個代表值）、長度 0 至 8，兩個必含樣板都要涵蓋；隨機部分固定 seed 並記錄）；**256 值逐點對照**：S 集與 P 集的分類逐值對照第 2 節的範圍定義（範圍寫死在測試內；`00` 與 `0A` 是終止值，不屬 S 集或 P 集的分類結果，第 2 節 P 集範圍文字含 `01` 至 `1F`，其中 `0A` 在迴圈頂端先離開） | 單元（合成位元組）；畫面層級見第 4 節 L1 試點 | 把 P 集範圍縮回 `E0` 至 `FC`，`FD`／`FE` 案例必須失敗；拿掉位移延續（被步驟 4 多吃一個位元組後設旗標；下一個在迴圈頂端分類的位元組若屬 P 集且旗標為真，只畫它、不多吃；分類後旗標清除），原判定為失敗的 `A4 E0 A4 E1 0A` 與 `[%s] A4 E0 E1 E2 0A` 在突變下通過，所以測試對它們的「必須失敗」斷言必須使突變被殺死（`[%s] E0 E1 E2 E3 0A` 在突變下仍因同步離開那一支失敗，殺不死它）；**突變「`%s` 離開狀態只探索同步」必須使離開位移案例與性質測試失敗；突變「`%s` 離開狀態只探索位移」必須使 `[%s] E0 E1 E2 0A`（原始位元組，只放模擬器單元測試）失敗**；突變「P 集上界改成 `FE`」等 256 值單點突變必須使逐點對照測試失敗 |
| 序列化：`COUNTRY.MES` 逐檔兩種模式與 U6 前的拒絕；`SHOPTAB` 名稱後第一個位元組 `00` 與預設拒絕 | 單元（合成）加需原版 | 破壞該位元組，檢查必須失敗；移除拒絕，測試必須失敗 |
| 資料表：`required.tsv` 與原版檔案清冊一致；`esp-windows.tsv` 的鍵集合等於 1024 項、類別計數 625／3／2／394；`charmap-zh-TW.tsv` 往返；各表只含 id、類別、碼位、單字；`apps/hr/l10n/data/esp-windows.tsv` 的 SHA-256 等於測試內寫死的值（更新該檔時同步更新測試內的值與 `docs/re/data/024-esp-windows.tsv`） | 單元 | 改一個雜湊或刪一列，檢查必須失敗 |
| 譯文表完整性與合併規則：`accepted` 的 `acc_sha`、批次不覆蓋 `accepted`、重複來源群組譯文一致、TSV 跳脫 | 單元 | 刪一列或改一字，檢查必須失敗 |
| 建置原子性與重用：建置中途失敗不留下可通過驗證的語言包；同輸入兩次建置輸出相同；同名目錄驗證通過就不重建；`os.Rename` 失敗時回到「已存在」分支重驗；已存在目錄驗證失敗時**不搬動舊目錄**而改用帶序號的新名稱（序號用盡則放棄、遊戲內文字維持原版）；兩個執行個體並行建置收斂到同一個有效目錄；暫存目錄（`.tmp-*`，超過 1 小時）的清理只刪過期暫存目錄，預先放一個舊的 `l10n-packs/<code>-…` 目錄，啟動後仍在；建置政策進輸入摘要：`with-candidates`、`allow-*` 或模式不同，目錄名與摘要必須不同；序號目錄的探測（依序探測基底名與 `-2` 至 `-9`，第一個驗證通過者使用；基底名永久損毀時連續啟動 10 次，每次得到同一個序號目錄，不重複建置）；`l10nBuilderVersion` 守護：版控放一份合成譯文表 fixture（放在 fork 的 `apps/hr/l10n/testdata/`，是合成資料不是譯文，不在 `l10n/` 路徑，與 `AGENTS.md` 草稿不衝突；自造文字須通過 `leakscan` 且不靠登記；涵蓋 ESPMES、`*.MES`、含 `%s` 與折行的項目，`accepted` 與 `candidate` 列都有，並以預設政策與 `-with-candidates` 各建一次，`COUNTRY.MES` 與 `SHOPTAB` 在 `-allow-*` 旗標下各有一個變體），測試以使用者原版加 fixture 在 table 模式建包，對 `files/` 內每個檔算 SHA-256，與內嵌（`go:embed`）的 golden 檔比對；`l10nBuilderVersion` 由 golden 檔位元組的 SHA-256 前 8 碼導出，所以輸出改變就必須重產 golden，版本隨之改變，不可能只重產 golden 而保留舊版本；輸出與 golden 不符即失敗（identity 包的輸出恆等於原檔、manifest 內含版本，兩者都不能當黃金值）；golden 是機器產生、無註解、固定排序、LF 的文字檔，`.gitattributes` 設 `-text`（`apps/hr/l10n/data/` 的 `.tsv` 與 golden、`testdata/fixture/` 全部檔案都要設：譯文表以原始位元組算整體雜湊，Windows 以 autocrlf 檢出成 CRLF 會使表雜湊、golden 比對與 `Version()` 改變），另列各變體的採用列數，以及 manifest 去掉版本與輸入摘要後的欄位（這兩項都不含版本，不會循環）；fixture 的 `accepted` 是測試值，不構成使用者接受，L3 閘門的統計排除 fixture；`-allow-*` 變體另加（預設政策下基礎 fixture 不含這兩個檔的非 `keep` 列），選內容夠長、無法由字典窮舉還原 `src_sha256` 的項目；不在 fixture 內的路徑不在守護範圍；需原版，缺檔 skip，閘門不 skip；摘要輸入逐項：表雜湊、原版雜湊、建置器版本、政策項、模式各改一個，目錄名必須改變 | 單元加需原版 | 在 manifest 寫入前注入失敗，驗證必須拒絕；拿掉摘要中的政策項，`with-candidates` 與預設建置必須撞名而使測試失敗；把清理改成刪舊序號目錄，「舊目錄仍在」必須失敗；目錄存在也一律重建，以哨兵檔斷言的重用案例必須失敗；序號用盡後覆寫 `-9`，用盡案例必須失敗；讓 map 迭代順序進入輸出，重現性案例必須失敗；不重用已通過驗證的序號目錄，連續啟動案例必須失敗；改序列化器一個位元組，golden 比對必須失敗；golden 內容改一個位元組，`l10nBuilderVersion` 必須不同；兩個執行個體並行建置以測試縫隙（建置完成、改名之前由測試建立競爭目錄）確定性觸發，改名失敗時直接回建置失敗的突變必須使縫隙案例失敗；「舊目錄不搬動」斷言舊目錄 inode 與內容不變且 `-2` 已建立；新的 `.tmp-*`（修改時間為現在）必須留下、過期的必須被刪，不看年齡一律刪的突變必須失敗；序號探測各補一個案例（基底名與 `-2` 都有效用基底名，突變由 `-9` 往回探測；基底名無效、`-2` 不存在、`-3` 有效用 `-3`，突變遇到第一個不存在的名稱就停；基底名不存在、`-2` 有效用 `-2`）；重用案例以放在包根（`files/` 之外）的哨兵檔斷言，不用修改時間；重現性案例重複建置至少 20 次 |
| 啟用規則（第 3.2 節四條加明示值 `identity`；規則 4 在 L2 之前不建置，由常數 `l2Supported` 控制）對 `planIngame` 斷言（輸出與原因鍵；規則 2 與 3 的差異：`((zh-TW, 明示), 無表)` 輸出「建置 identity」，`((zh-TW, 非明示), 無表)` 輸出「不建置」），`resolveStartup` 經 `planIngame` 到 `ingameStatus` 的串接測試（中間的建置與 `Session.Open` 以假建置器與假 `LangStatus` 提供 `E` 與 `startFail`）；`resolveStartup` 層：`-ingame-lang <不認得>` 且無環境變數得 `(lang, 非明示)` 且 `override` 為否，不認得的旗標加 `HR_INGAME_LANG=ja` 得 `(ja, 明示)` 且 `override` 為真，空字串視為沒給，對所有旗標與環境組合斷言 `C` 的明示欄等於 `override`；與 `ingameStatus`（第 3.8 節）：真值表 23 列逐列斷言（含採用列數為 0 的包標「驗證用」、不認得的旗標代碼當作沒給）；`ingameStatus` 的性質測試：在前置條件域內窮舉（`S` 七個值、`E` 的種類、`startFail`、`override`、`avail`），函式有定義，F1 值屬四類之一、toast 屬五種之一；另測：相同關係各情形（`S ＝ none` 與原版、`S ＝ identity` 與 identity 包、`S ＝ zh-TW` 與表包或 identity 包或原版且無表）、`avail` 的原因鍵順序（`no-table` 先於 `unsupported-language` 先於 `no-patch`）、`startFail` 兩種原因鍵、啟動失敗後 F4 離開 `C_start` 再繞回（驗第 1、2 步順序）、`-ingame-lang`、`HR_INGAME_LANG`、`lang` 的優先序、覆蓋旗標生效時 toast 一律為旗標指定、identity 包標「驗證用」不標「部分翻譯」、原因鍵顯示譯名不顯示原始鍵 | 前端單元（`docs/spec/006` 的測試縫隙；`ingameStatus` 是純函式） | 拿掉一條規則或把優先序對調（例如第 2 步排在第 1 步前、把 `S ＝ none` 移出相同關係、規則 4 在 L2 前仍建置、把規則 3 改成與規則 2 相同），對應案例必須失敗；拿掉採用列數為 0 即視同 identity 的判定，列 21 與列 23 必須失敗；拿掉第 4 步的兜底，性質測試必須失敗；讓第 2 步讀取 `avail(none)`（把 `S ＝ none` 移出相同關係），列 11 必須因 panic 而失敗；讓不認得的旗標使 `override` 為真，`resolveStartup` 案例必須失敗 |
| 建置失敗不阻擋遊戲；`LangDir` 不存在；manifest 列出但缺檔、manifest 未列的多餘檔 | 單元加需原版 | 讓建置失敗，遊戲仍須啟動 |
| identity 語言包的冷啟動 A/B（畫面 PNG 雜湊、`machine.StateDigest`、存檔），對照 L0 前基準 | 需原版，`tools/play.sh` 的 test-diag 類入口 | 以建置器加 fixture 建出差一個字的包（不是改包內檔案：那會使 manifest 驗證失敗而回退原版），畫面雜湊必須改變 |
| 試點包的真畫面案例（17 項：16 項冷啟動對白加 `SP.MES#56`）；`docs/re/025` 的 7 組冷啟動位移連鎖實驗（預測字串偏移對實測，L1 以它們當 oracle 並擴充）；`ESPMES#118.2` 的 `%s` 變體（`-scratch` 暫存層，預測字串偏移對實測） | 需原版，樣張使用者過目 | 模擬器預測錯誤的變體必須被偵測 |
| manifest 驗證：檔案遭竄改、缺檔、manifest 未列的多餘檔、輸入雜湊不符、**manifest 記錄的輸入摘要不等於預期輸入摘要**（`Options.LangDigest`，例如譯文表或建置政策改了而目錄未換）都不啟用語言包；`LangDir` 非空、`LangDigest` 為空且未明示 `SkipLangDigest` 時 `Open` 回錯；明示 `SkipLangDigest`（`hrbot`、測試入口）時只略過輸入摘要，其餘驗證照常；前端對 `Open` 的呼叫在 `LangDir` 非空時 `LangDigest` 必須非空（以 `resolveStartup` 的輸出斷言）；`hrl10n verify` 與 `Session.Open` 共用同一個驗證函式；驗證失敗時 `Open` 不回錯，`LangStatus` 回報原因鍵；`LangManifest` 與正規化後的 `LangDir` 在 `probe`、`hrsoak`、`Session` 三處對同一個目錄算出相同值 | 單元 | 竄改一個位元組，驗證必須失敗；拿掉輸入摘要比對，「譯文表改了」案例必須失敗；`SkipLangDigest` 為真時摘要不符的包仍可啟用，但檔案雜湊不符的包必須被拒；拿掉前端的 `LangDigest` 傳遞，斷言必須失敗；`hrl10n verify` 對竄改過的包必須回失敗；讓 `Open` 在驗證失敗時回錯，`LangStatus` 案例必須失敗；改掉任一處的 `LangManifest` 算法，三處比對必須失敗 |
| 譯文表 `status` 採用規則：預設只採用 `accepted` 與 `keep`，`candidate` 視為 `keep`；`-with-candidates` 才採用；前端內嵌的建置器不提供 `-with-candidates`、`-allow-country-offsets`、`-allow-shoptab` | 單元 | 預設採用 `candidate`，測試必須失敗 |
| 洩漏判準：部分引用（單行半句）、行內被標記切開、跳脫換行、十六進位拼寫、Big5 與 UTF-8 各自單獨命中、純 ASCII 長字串不誤報、短於 8 bytes 不命中、`leakscan-allow.tsv` 登記項目放行、登記來自超過 7 個字的段的單位被工具拒絕（含來自長段的短片段）、登記以外的命中仍使閘門失敗、單位身分不依賴解析器、3 至 5 字片段只比整段相等（嵌在較長 CJK 文字內不命中，記為已知漏報）、`HR_WITH_L10N` 時 `l10n/zh-TW/` 被路徑級排除（放入 fixture 譯文表，包檢查必須失敗）、原版缺席時閘門失敗、全歷史掃描能命中舊 commit 內的 fixture（輸出含 commit 與路徑）、工作樹乾淨而歷史有命中時預設模式（push 閘門）通過、`-history` 模式回報命中、fork 範圍命中、`minMembers` 邊界成對案例（含 2 個非標點字的視窗不命中，含 3 個命中）、全單位自我回收（每個有鍵的單位以 UTF-8 文字與 Big5 位元組各自掃一次必命中自己）、`-files-from` 缺檔與空範圍失敗、歷史串流空串流與結尾標記（缺標記、記錄數不符、結尾之後還有資料都失敗）、stderr 與 stdout 的輸出餵回掃描器零命中、原版雜湊不符失敗、索引自檢失敗退出 2 | 單元（fixture 執行時由原版產生，缺檔 skip）；閘門測試 | 放一個含原版項目的檔案，掃描必須命中 |
| 玩家端冷建置 | Linux 實跑；Wine 實跑；macOS 只驗結構；Linux 與 Wine 的 manifest 雜湊相同 | 輸入雜湊不符，建置必須失敗 |
| 診斷新增三項（`LangDir`、manifest 雜湊、開檔層）；`docs/spec/005` 第 10 節 `info.txt` 區段檢查含新欄位（T1、T2、T3 都要有） | 單元加機器人模擬 hang | 拿掉欄位，`info.txt` 檢查必須失敗 |
| F1 的五個字句模板（原版、部分翻譯、驗證用、下次啟動生效、無法使用）與 F4 提示的五種字句（旗標指定、無法使用、下次啟動生效、尚無語言包、不變）在字串表中各有五種語言、非空；原因列舉以字串表鍵顯示譯名，不顯示原始鍵；toast 的語言名稱加字句，五種語言的最長組合在 `fitLine` 下不被截斷 | 前端單元 | 拿掉任一個 F1 字句模板（含驗證用）或任一種 toast 字句，測試必須失敗 |
| `reserved-codes.tsv` 與字集相關測試（L2） | 單元 | 屬 L2，L1 不存在 |
| L2 補丁輸入與 CFONT 格位：原版雜湊錯、32-byte 記錄截斷、重複或亂序碼、字碼表與字模集合不一致、保留碼碰撞、字號越界、bit 0 非零、未修改格被改動；五檔中任一檔變一位元組使補丁雜湊改變；既有有效語言包須重用，開發側同名補丁輸出須拒絕 | L2 容器單元與需原版測試 | 各突變都在包建立前失敗，或使新輸入摘要不同；不得覆寫既有包 |
| L2 英文雙字共格：字組依左右 Unicode 碼位排序、奇數段補 U+0020、字碼表往返與字模集合一對一；顯式換行及 `%` 規格不得跨組；`A%sB` 兩側各占一個字組，寬度分別計算；詞界折行移走一個 U+0020、字組及語言包摘要重算；配碼前拒絕 U+0009、無效 `%` 與不支援的 Unicode 組合；同一輸入兩次烘製位元組相同；玩家端譯文改動但字組仍為補丁子集時沿用原碼建新包，出現缺組時拒絕，不能重烘；最後仍跑 `Check` 與 `1676` | L2/L3 容器單元、獨立烘製與研究畫面；正式驗收待第 3.4 節第 4、6 至 8 項 | 將兩段錯併、拿掉行尾補白、把原始空白寫成 `0x20`、略過來源檢查、子集重新編碼、接受缺組或略過末端 `Check`，對應案例必須失敗 |
| L2 零採用列與版本：table 模式所有列為 `candidate` 且未帶 `-with-candidates` 時，八檔等於原版；同表帶旗標採用一列後套完整補丁並產生不同摘要；再回退為零列時重算摘要且再次不套補丁；identity 模式永遠不套補丁；L2 首次啟用及輸出語意改變時 golden 或契約版本跟著更新 | 容器單元、manifest 與 `CFONT.15` 位元組比對 | 無採用列仍改動字模、採用列存在卻略過補丁、回退零列卻沿用舊包、golden 涵蓋的 L2 行為改變但版本與摘要不變，對應案例必須失敗 |

## 9. 原版 oracle 與已知差異

繁中 identity 語言包的 oracle 是原版（dosgolem 同狀態，對照 L0 前基準）。其他語言沒有原版對應物，驗收靠樣張與使用者過目。已知差異：
- **預設設定下 M10 對一般玩家沒有可用交付**：譯文表與補丁預設不隨包，語言包只有使用者自己的機器能建（前言）。
- **混合語言是必然**：說話者標籤（段 3EA3）、選單、按鈕、人物名、地名、戰鬥紀錄屬硬編碼，每個對白框都是「繁體名牌加譯文」。規格 009 完成前任何語言都如此。L1 試點量測各畫面字元來源比例作為使用者決定 U4 的數字。
- 圖像內文字不翻譯（標題標誌、地圖上烘進圖的國名）。
- 勢力名等專有名詞在存檔內維持原文，畫面上可能兩種寫法。
- `COUNTRY.MES` 項目 5 至 10 在原版少讀第一個雙位元組字（強推論）；含譯文的檔重算精確偏移，與原版行為不同（U6，預設拒絕）。
- F4 切換語言時遊戲內文字下次啟動才生效（`LangDir` 啟動時綁定）。
- 同一行內原版字模（硬編碼字串）與補丁字模（譯文，L2 之後）筆畫風格不同。
- 原版 `printf` 不支援位置參數，`%s` 順序固定，日文與韓文語序受限。
- `%s` 緊接 `0x0A` 一律失敗的後果：原版 ESPMES 有 7 處 `%s` 緊接 `0A`（`ESPMES#120.66`、`#120.67`、`#120.69` 有靜態呼叫點，屬 `win31x4`；`#120.73`、`#120.74`、`#120.75`、`#120.77` 屬 `none`），譯者必須把 `%s` 移出行尾，譯文與原版斷行位置因此可能不同。另記一個事實：`SYSTEM.MES#126` 的 `%s` 後接 `0x20` 再 `0A`，若該項走 `01A3`（剝掉所有 `0x20`），原版自己就是 `%s` 緊接 `0A`（窗口歸屬未普查）。
- 改名、刪除、`create` 語言層的檔維持與 `Root` 檔相同語意，不拒絕（遊戲不走這些路徑）。
- 譯文未經母語者審閱（AI 草稿）。
- 英文雙字共格試點的正式配碼與正常語言包路徑已驗。韓文已選 8 px 空白，正式接線驗收沿第 3.2.4 節；兩語都不外推全量導入。
- 影響範圍是 `MAIN.EXE` 的檔案類文字；`OP.EXE`、`END.EXE` 未查。
- `dataDir()` 退到暫存目錄時語言包每次啟動重建。
- 輸入改變（原版、譯文表、建置器版本、建置政策）時換新目錄名，舊的 `l10n-packs/<code>-…` 目錄不自動刪除，會累積（理由見第 3.2 節）；使用者可手動刪除整個 `l10n-packs/`。
- `probe` 與 `hrsoak` 的 `-lang-dir` 不經 `Session.Open`，不驗 manifest 與輸入摘要，只讀 manifest 雜湊記入狀態；`hrbot` 與測試入口經 `Session.Open`，明示 `SkipLangDigest`，只略過輸入摘要；前端路徑驗全部。載入前由 `hrl10n verify` 驗證（第 3.2 節）。
- `R_item > H` 的項目（原版自己就超過窗口行數者，已知 `ESPMES#122.32`；以及渲染列數算法偏保守造成者）：預算規則 (3) 放行譯文同樣超過，畫面上可能截斷，與原項目同風險；清單由 L1 的基準統計產生，只列 id 與 `R_item`，記入 `docs/re`。
- 窗口歸屬未普查的項目（`SYSTEM.MES`、`POWERMES.MES`、`ESPMES` 的 394 項）比照 `win31x4`：這與原項目最長行（沒有超過 31 bytes 的行，手動行數最多 3 與 4 行，023 第 4.4 節）相容，是強推論；真窗口若比 31 bytes 更窄，譯文可能被引擎折行或截斷。
- L2 之後，`S ＝ zh-TW`、`E ＝` 他語言包而沒有 zh-TW 譯文表時，F1 判 (4) `no-table`，實際下次啟動是原版（第 3.2 節規則 3）；L2 之前不可達，L2 規格修訂時處理，並在第 3.8 節的真值表加對應列。
- `1676` 的相位保證（寬度停止不改變 P／S 相位）依賴最大寬是 8 的倍數；023 第 4.3 節有 1 個計算值呼叫點的窗口未量，保證對它不成立。

## 10. 停止線與權利邊界

- 停止線：譯文或字模涉及未盤查的來源；字集超過可用碼數；需要修改原版 EXE 或把原版位元組放進任何版控或發行包；L5 前想讓遊戲內語言在執行中切換；長跑出現語言包造成的新停機點；內容判準在版控、`docs/` 或 fork 命中原版項目（`leakscan-allow.tsv` 登記者除外）；原文送往 Claude Code 或已授權的 Codex 以外的服務而使用者未答覆；L2 前提（第 3.4 節）未完成就動手；在 U6 回答前開放 `COUNTRY.MES` 的譯文偏移重算。
- 權利：譯文是原版文字的衍生物。預設（第 12 節）：譯文表不進版控、不進發行包；語言包只在使用者機器；字模補丁只放 `workplace/`；未決定前不為翻譯畫面建立 `docs/images/` 的新截圖。repo 保持 private。`AGENTS.md` 第 2 節補譯文、譯文表、語言包的權利條（比照 HD 的 [HARD] 條款）。
- 字型來源：只用開放授權字型，授權檔隨補丁保存；不使用原版字型作為其他語言字模的來源，但可以在語言包內整格保留原版字模（建置時從使用者自備的原版取得）。

## 11. 跨規格修訂清單（每格單一負責者）

本節即 `003`、`005` 修訂的紀錄（日期為 READY 提交日；`006` 另在檔頭記一筆）。**時機欄**：標「READY 提交」的列與本規格升 READY 同一個提交；標「對應產物提交時」的列涉及尚未存在的工具、目錄或旗標，**不在 READY 提交寫入**（現況文件只寫現況），由產出該物的提交一併修訂，負責者仍是本規格；標「實作合併時」的列在實作合併並重建發行包時修訂；標「L1 前端接線時」的列在 L1 前端接線的提交時修訂（比照 `docs/spec/006` 第 60 行的做法）。

| 位置 | 修訂 | 負責 | 時機 |
|---|---|---|---|
| `docs/spec/003` 第 2 節必要檔案敘述（第 18 行） | 清單路徑更正為 `apps/hr/runtime/required.tsv`（現況，`apps/hr/data` 不存在）；語言包 manifest 另驗 | 008 | READY 提交 |
| `docs/spec/003` 第 3 節 `Options` 列（第 26 行） | 加 `LangDir`、`LangDigest`、`SkipLangDigest`；`Open` 在語言包驗證失敗時不回錯，另有 `Session.LangStatus()`（第 3.2 節） | 008 | READY 提交 |
| `docs/spec/003` 第 5 節存檔與檔案（暫存層與原版目錄兩層查找，第 55 至 63 行） | 加語言層，順序暫存層、語言層、原版目錄；寫入模式開語言層的檔拒絕 | 008 | READY 提交 |
| `docs/spec/003` 第 8 節驗收的外洩掃描列（第 96 行） | 加內容判準、fork 範圍與 `l10n`、`l10n-packs` 路徑；閘門失敗關閉 | 008 | 對應產物提交時（`hrl10n leakscan` 與 `tools/l10n/leakscan.sh` 就位） |
| `docs/spec/005` 第 5 節診斷紀錄內容（`info.txt`） | 新增 `LangDir`、manifest SHA-256、各資料檔與 `CFONT.15` 的命中層 | 008 | READY 提交 |
| `docs/spec/005` 第 10 節 `info.txt` 區段檢查列（第 233 行） | T1、T2、T3 的 `info.txt` 都含三項新欄位 | 008 | READY 提交 |
| `docs/spec/005` 第 5 節診斷紀錄內容中 `state.state` 的敘述（第 122 行一帶） | 補「語言包 Session 存下的狀態檔只能在同一 `LangDir` 與 manifest 載入，否則 `LoadState` 明確拒絕」；狀態檔記錄機器本地路徑，跨機載入本來就需要相同路徑（既有行為） | 008 | READY 提交 |
| `docs/spec/006` 第 6 行範圍句「F4 在五種語言之間循環（只切換前端介面文字）」 | 改為「F4 切換單一語言設定 `lang`：前端介面立即生效，遊戲內文字下次啟動生效（`docs/spec/008` 第 3.8 節）」 | 008 | READY 提交 |
| `docs/spec/006` 第 5 節（第 179 至 181 行）：前兩句「F4 切換的是前端介面文字…M10 之前不隨 F4 改變」、第三句「M10 的 L1 實作後，F4 同時設定遊戲內語言包」、第 181 行 F4 提示 | 三處合併為：F4 切換單一語言設定 `lang`，前端介面立即生效，遊戲內文字下次啟動生效；F4 提示是語言名稱接上 `ingameStatus` 選出的字句，共五種（`docs/spec/008` 第 3.8 節） | 008 | READY 提交 |
| `docs/spec/006` 第 3 節 F1 狀態列「遊戲內文字語言」（第 74 行） | 四類值與依序判定（見 008 第 3.8 節的 `ingameStatus` 與真值表） | 008 | READY 提交 |
| `docs/spec/006` 第 7 節優先序括號（第 201 行）「環境變數（目前只有 `HR_MUTE`）」 | 保持「設定值的環境變數只有 `HR_MUTE`」；補一句：遊戲內語言另有 `-ingame-lang` 與 `HR_INGAME_LANG`，不參與 theme、lang、sound 的優先序（見 `docs/spec/008` 第 3.2 節）；`HR_L10N` 是譯文表目錄定位，不是設定值 | 008 | READY 提交 |
| `docs/spec/006` 第 10 節純函式清單（第 242 行）：`resolveStartup(flags, env, prefs, available)` 與 `panelLines(lang, face, info)` | `resolveStartup` 的輸入加遊戲內語言旗標與環境變數（`-ingame-lang`、`HR_INGAME_LANG`），輸出加遊戲內語言選擇與覆蓋旗標是否生效；新增純函式 `planIngame(C, hasTable, l2Supported, patchInHand)`（第 3.2 節）與 `ingameStatus(S, E, startFail, override, avail)`（第 3.8 節），串接為 `resolveStartup` 到 `planIngame` 到 `ingameStatus`；`panelLines` 的 `info` 帶 `ingameStatus` 的輸出（F1 值與原因鍵） | 008 | READY 提交 |
| `docs/spec/006` 檔頭狀態行與第 5 行「流程」段 | 檔頭記一筆修訂「F4 與遊戲內語言語意，依 `docs/spec/008`（日期為 READY 提交日）」；「流程」段「實作草稿未提交到 fork 的 `hr` 分支」更正為已提交（`c9c8ec3`、`adeb3e4`、`aaaf999`） | 008 | READY 提交 |
| `docs/spec/006` 第 11 節已知差異（第 281 行）「遊戲內文字不隨 F4 改變（M10）」 | 改為「遊戲內文字在 F4 後下次啟動才改變」 | 008 | READY 提交 |
| `docs/spec/006` 第 93 行與第 273 行 | 第 93 行的字元數改為「以當次 `TestGenCharsets` 實測為準（現值見 `docs/re/026` 第 4 節）」；第 273 行 e2e「第六次回到起點與第一張相同」的前提加「生效語言與 `lang` 都回到 zh-TW」 | 008 | READY 提交 |
| `docs/spec/006` 第 186 至 189 行的字元表與字型子集 | 規格文字不改；新 i18n 字串使字元表與字型子集重產，並記收據 | L1 前端接線 | L1 前端接線時 |
| `docs/spec/007` | 無修訂；`tools/pkg/leakscan.py` 的音訊控制組（4 項命中、反對照 0）要持續通過 | 無（008 只驗證控制組） | 無 |
| `AGENTS.md` 第 2 節 | 新增條文草稿：「[HARD] 譯文、譯文表（`l10n/`）與語言包是原版文字的衍生著作（`LICENSE` 第 2 條 (c)）；語言包含原版位元組，屬原版素材（`LICENSE` 第 1 條 (b)、第 5 條 (e)），只存在使用者機器的資料目錄。譯文表預設不進版控、不進發行包。要改這個預設（進 private repo、隨包發行、公開）先問使用者；repo 保持 private，轉公開前先處理 git 歷史，並由使用者決定是否調整 `LICENSE` 第 2 條 (c) 對譯文的措辭（`docs/spec/008` 第 12 節 U1、U8）。原文只送往 Claude Code（主 session 與子代理），其他服務先問使用者（`docs/spec/008` 第 3.10、12 節）。」 | 008 | READY 提交 |
| `AGENTS.md` 第 4 節（遊戲專屬層表，第 54 至 58 行） | 補 `apps/hr/l10n`、`apps/hr/l10n/verify`、`apps/hr/cmd/hrl10n` | 008 | 對應產物提交時（L1 建置器目錄建立） |
| `AGENTS.md` 第 6 節（停機分類，第 88 行） | 把「(c) 其他」改為「(d) 其他」，新增「(c) 語言包內容：同輸入冷啟動，分別用 identity 包（`-ingame-lang identity`）與譯文包，比對停機點；不用狀態檔（狀態檔記錄 `LangDir` 與 manifest，換包載入會被拒）。」 | 008 | 對應產物提交時（`-ingame-lang identity` 旗標就位） |
| `AGENTS.md` 第 9 節目錄表 | 補 `l10n/`、`tools/l10n/` | 008 | 對應產物提交時 |
| `AGENTS.md` 第 10 節（push 前檢查，第 143 行一帶） | 加內容判準（原版在手時執行，**原版缺席時失敗，不略過**） | 008 | 對應產物提交時（`hrl10n leakscan` 就位，第 3.9 節第 5 項） |
| `AGENTS.md` 第 13 節 M10 列 | 狀態字樣同步：READY 範圍 L0、L1；L2 前提；預設下玩家沒有可用交付；規格 009 的排程；**U1 至 U8 尚未回答、暫以預設值推進**，記在此列而不是第 12 節定案表，因為第 12 節末段要求實作照定案走，預設值不是使用者的定案。M9 列不需修訂（已含遊戲內文字的 F4 語意見 M10） | 008 | READY 提交 |
| `AGENTS.md` 第 14 節（旗標說明與外洩掃描句） | `HR_WITH_L10N` 的完整說明（旗標、產物目錄、版本後綴、附說明檔）比照 `HR_WITH_HD`，加在說明 `HR_WITH_HD` 的那一項；外洩掃描那一項只加內容判準 | 008 | 對應產物提交時 |
| `README.md` 第 118 行（現寫「遊戲內文字不隨之改變，見 `docs/spec/008`」）與 `packaging/README.dist.txt` 第 19 行（現只寫「切換介面語言」） | README 改為「遊戲內文字下次啟動生效；預設沒有語言包；標示『部分翻譯：對白與敘述』」；發行說明補同樣兩句 | 008 | 實作合併時 |

## 12. 使用者決定

下列問題有部分已回答；其餘暫用預設值。預設值下 L0 與 L1 都能完成（L1 之後第一次 push 前要先處理 U8 的命中，見該列）。**U5 已選 B 案，但補丁入版控、隨包發行與授權措辭未決；U1、U3 與 U5 未決的散布部分維持不入版控、不隨包發行。U6 的預設是行為變更，不是保守值，所以建置器拒絕直到使用者回答。**

| 編號 | 問題 | 預設值 | 影響 |
|---|---|---|---|
| U1 | 譯文表（含簡體等近似原文的譯文）進不進 private repo；進的話是否比照 HD 的條件；發行包附不附譯文表與建置器 | 不進版控、不附 | L3 與打包。不附時玩家機器上沒有譯文表，語言包只有開發機能建（前言） |
| U2 | **已決：**整個 M10 原文可交由 Codex 處理；原先 Claude Code 主 session 與子代理的既有路徑不變。其他服務仍須先問，禁止代理使用網路查原文 | L1 試點、L3 |
| U3 | 發行包內嵌語言包建置器（Go，已是前端的一部分）時，是否同時附譯文表與補丁 | 建置器隨前端（無原版素材），譯文表與補丁不附 | 玩家端能否得到語言包 |
| U4 | 混合語言畫面是否可接受；對白內人名地名先譯或先保留；`SHOPTAB` 的納入時機；F4 切換語言時遊戲內文字下次啟動才生效是否可接受；是否持久化獨立的遊戲內語言設定（目前介面與遊戲內不同只能每次帶 `-ingame-lang`） | F4 寫 `lang`，遊戲內下次啟動生效；沒有譯文表時維持原版 | 006 的 F4 語意（見第 3.8 節） |
| U5 | **字模策略已決：B 案，全部由 OFL 的 Noto Sans CJK 產生；英文選雙字共格，玩家端只用預烘字組。**已存在字組可重排，新字組拒絕並提示重製補丁。仍待決定點陣補丁的 OFL 與 `LICENSE` 措辭，以及何時入版控或隨包 | 補丁只放 `workplace/`，不散布 | B 案與英文雙字共格可作本機 L2/L3 試作；發行前處理授權與包裝 |
| U6 | `COUNTRY.MES` 偏移：含譯文的檔補回精確偏移（**行為變更**，`AGENTS.md` 第 1 節要求先經使用者決定）或照原樣截斷 | **建置器拒絕**含譯文的 `COUNTRY.MES`（旗標 `-allow-country-offsets` 明示才開放） | 序列化 |
| U7 | **已決：**繁中 17 項試點已由使用者接受。其餘語言的審閱範圍、日韓是否需要母語者及接受語句仍待決定 | 其餘候選標示「未經母語者審閱」，只在使用者明示接受後設定 `accepted`（第 3.10 節） | L3 |
| U8 | 基準掃描（第 3.9 節，結果在 `docs/re/028`）的 12 筆工作樹命中，`leakscan-allow.tsv` 登記哪些（只有路徑與單位身分；命中的內容是短標籤或遊戲名稱一類的專有名詞時才可登記，所屬段超過 7 個字的單位依第 3.9 節第 5 項的補救路徑處理）；`docs/re/012` 引用的遊戲內提示與選單字串已證明是 `MAIN.EXE` 的硬編碼字串，不在資料檔單位範圍內，不產生命中也無從登記，它們的政策是人工複核（歸規格 009）；是否需要調整 `LICENSE` 第 2 條 (c)「不含原版內容本身」的措辭（短 UI 標籤登記進 `docs/re` 超出該句字面） | 基準掃描前不登記；命中先由主代理把證據文件的引用改成單位身分與位址（不需使用者答覆），剩下必須保留的短標籤才把清單（只有路徑與單位身分）交使用者決定；回答前閘門對未處理的命中失敗，push 前先處理完（第 3.9 節第 5 項） | 洩漏判準的誤報政策，不阻擋 READY；`LICENSE` 措辭由使用者決定 |

2026-10-04 決定紀錄：U2 的 Codex 處理範圍已由使用者授權整個 M10；U7 的繁中試點 `ESPMES#121.0` 至 `#121.15` 與 `SP.MES#56` 共 17 項，在使用者看過重新對齊的樣張後回覆「全部接受喔」，已標為 `accepted` 並註明未經母語者審閱；U5 的字模策略選 B 案，所有新語言字模由 OFL 的 Noto Sans CJK 產生，先留本機試作，發行授權另議。其餘語言的 U7 驗收方式、U1、U3、U4、U5 的發行部分、U6 與 U8 仍待決定。收據見 `docs/re/031-l1-localization-pilot.md`。這段紀錄不變更 L0、L1 的 READY 範圍，也不授權譯文或字模補丁入版控或隨包發行。

2026-10-05 決定紀錄：使用者回覆「同意雙字共格」，選定英文兩個 Noto 字符共用一個 15×15 格作為 L2/L3 方向。依 [`docs/re/032`](../re/032-l2-glyph-code-prototype.md) 的本機樣張與字模呼叫重播，修訂第 3.4、3.6 節的 DRAFT。這項決定不等於接受英文譯文，也不變更 L0/L1 的 READY 範圍或補丁、譯文的版控及發行權限。

同日後續決定：使用者選擇「只用預烘字組；已有字組可重排，新字組就拒絕並提示重製補丁」。第 3.4 節因此把英文 `charmap` 當固定碼本，玩家端採用列及折行結果的字組集合必須是碼本子集；語言包仍依譯文與建置政策計摘要，缺組時不輸出包。這只決定本機建置政策，不授權補丁入版控或發行。正式驗證仍受第 3.4 節第 4、6 至 8 項閘門約束。

## 13. 升 READY 的條件與紀錄

1. `docs/re/025` 已併入第 2、4、5 節（`SP.MES#56` 冷啟動收據成立、7 組位移連鎖預測全部吻合）；未測的 trail 與 lead 範圍列為 L1 擴充。
2. 審查：八輪唯讀審查（第 14 節）；第八輪（`workplace/spec-review/008-rereview7-C.md`，只看第七版到第八版的差異）無阻擋，其建議 R1 至 R14 在升 READY 的同一個提交處理。
3. 第 11 節標「READY 提交」的列與升 READY 同一個提交完成（`003`、`005`、`006`、`AGENTS.md` 第 2 節與 M10 列）；其餘列由對應產物的提交修訂。
4. U1 至 U8 皆採預設值，皆不是升 READY 的條件（預設值下 L0 與 L1 可完成）。U6 預設拒絕，不納入試點；U8 不阻擋 READY，但 L1 之後第一次 push 前要先處理基準掃描的命中。
5. 外層 id 換算與 394 項差集已併入 `docs/re/024`。
6. **READY 之後的實作回饋（2026-10-04，L1 程式庫完成時，不改變 READY 範圍與閘門）**：實作與審查（預算、格式、洩漏判準、建置器各一位唯讀審查者，收據 `docs/re/028`）發現規格有未寫明或內部不一致之處，已澄清在原條文：第 3.1、3.2 節 `files/` 含 `CFONT.15` 複本、manifest 欄位與 `table_format`、`-l10n` 取 l10n 根目錄、identity 模式拒絕政策旗標、`verify` 的原版雜湊來源、per-code 的譯文表尋找與 `hasTable` 定義、重用條件含代碼、改名失敗的重試、`LangDigest` 與 `Result.Digest` 比對；第 3.3 節格式嚴格度與合併、重複來源與折行前比對、列必須屬於該檔、SHOPTAB 名稱欄規則；第 3.9 節單位細節（序號、`OP*.TXT`）、正規化的實際分類、`minMembers`、閘門失敗關閉條件、歷史串流格式與命名空間、偶然命中的補救路徑；第 12 節 U8 的例子。這些澄清把實作者與審查者選定的行為寫成條文，沒有新增功能。

## 14. 審查意見的取捨

第一輪的處理對照在第二版，第二輪在第三版，第三輪在第四版；第五版保留這些處理並補第四輪意見（本節前一個表是第三輪的處理）：

| 項 | 處理 |
|---|---|
| 第三輪 A-B1 `%s` 規則與行尾規則是啟發式，有殘留缺口 | 採納：先前的兩條啟發式換成 `1676` 模擬器（第 3.5 節），`%s` 以對抗方式建模；P 集範圍更正為 `E0` 至 `FF`（含 `FD`、`FE`）；zh-TW 改寫版的「走單位元組路徑」措辭更正（lead 在 `E0` 至 `F9` 者走成對路徑）；`01A3` 與 `06CF` 的名稱尾端差異寫入第 2 節，模擬器的對抗建模不依賴它；測試表加反例（位移延續兩字）與負對照；畫面層級驗證列入 L1 試點 |
| 第三輪 A-B2 ESPMES 內層格式 | 採納：第 2 節與第 3.5 節按位元組核對的格式重寫（N2 ＝ 項目數 ＋ 1，`00 FF` 結尾，序列化重寫 `FF`，項目總數 1024）；測試加「解析器多出一項必須失敗」 |
| 第三輪 A-B3 試點的 `%s` 畫面案例沒有可達項目 | 採納：024 找到可達且含 `%s` 的 `ESPMES#118.2`（bot 檢查點狀態）；因 `LangDir` 比對不能與語言包同時載入，以測試專用暫存層變體驗證；不能達成時出口退為 oracle 對拍加「畫面未覆蓋」註記 |
| 第三輪 A-R1 `COUNTRY.MES` 預設拒絕 | 採納（第 3.3 節、U6） |
| 第三輪 A-R2、B-B1 `zh-TW` 啟用規則矛盾 | 採納：第 3.2 節四條啟用規則，明示的 `zh-TW` 才建置 identity 包；F1 四種值對 `zh-TW` 舉例 |
| 第三輪 A-R3、B-R1 原子改名與重建 | 採納：目錄以輸入摘要命名，驗證通過就不重建；同層暫存目錄；替換與並行處理 |
| 第三輪 A-R4 `%s` 最壞展開假設 | 採納：計算慣例標明為假設、「原項目自己為上限」用同一慣例、`%s` 緊接 NUL 安全、實參遙測 |
| 第三輪 A-R5、B-R8 原碼字來源與名詞 | 採納：`charmap-zh-TW.tsv`（原版 1716 字一對一）；「九個輸入」與「十個輸入」分開 |
| 第三輪 A-R6 計數 | 採納：`%s` 後接 `0A` 為 7 處，另補接 NUL 與其他的分布 |
| 第三輪 A-R7 L0 實作細節 | 採納：全路徑、兩處預檢、`LangManifest` 輸入與旗標、`StateDigest` 的 `omitempty`、不存在 `LangDir` 的生效值、寫入模式開檔拒絕與其他維持 `Root` 語意、層別判斷取代字串前綴 |
| 第三輪 A-R8 測試負對照 | 採納：`searchFor`、`manifest.json`、解析器多出一項、失敗模式測試拆列；`reserved-codes.tsv` 標 L2 |
| 第三輪 A-R9 `SHOPTAB` 授權範圍 | 採納：預設拒絕，`src_sha256` 取含補白 20 bytes |
| 第三輪 A-R10 窗口表換算 | 採納：併入 `docs/re/024`（換算、`win29x4`、394 精確值），第 2 節引用 |
| 第三輪 A-R11 | 採納：`_lseek` 位址、`printf` 無位置參數、逐項語意、`golang.org/x/text` 兩個模組 |
| 第三輪 B-B2 內容判準 | 採納：正規化與滑動視窗、十六進位展開、fork 範圍、短 UI 標籤政策與 `leakscan-allow.tsv`、閘門失敗關閉與第 11 節一致、基準掃描為 L1 第一個交付、接線細節 |
| 第三輪 B-R2 F1 值優先序 | 採納：`avail` 判定、依序判定、原因為有鍵列舉、F4 提示兩種字句 |
| 第三輪 B-R3 跨規格清單 | 採納：003 節號拆開與路徑更正、006 補第 6、179 至 181、201、281 行與字元表和 e2e、`AGENTS.md` 第 4、14 節與 M9、007 負責者、(d) 排在「其他」之前、005 引用改指 `AGENTS.md` 第 6 節 |
| 第三輪 B-R4 預設下交付為零 | 採納：第 1 節、第 9 節、`AGENTS.md` M10 列 |
| 第三輪 B-R5 第 12 節抬頭與 U2、U7 | 採納：抬頭更正、U2 如實說明、U7 預設具體、試點限 17 項 |
| 第三輪 B-R6 `COUNTRY.MES` 機械強制 | 採納（同 A-R1） |
| 第三輪 B-R7 試點 `%s` 案例 | 採納（同 A-B3） |
| 第三輪 B-R9 至 R14 | 採納：接線細節、`HR_WITH_L10N` 與 zh-TW 譯文表不隨包、`AGENTS.md` 記錄位置改放 M10 列、搜尋路徑措辭、雙記位址、L2 探針加第四組 |

### 第四輪確認審查（第四版）的處理

| 項 | 處理 |
|---|---|
| 四輪 A-B1 行寬上限有兩套互相矛盾的規則 | 採納：第 3.5 節改為單一規則（字面位元組每列 <= `W`、展開位元組每列 <= `max(W, E_item)`、行數 <= `max(H, 原項目行數)`；窗口未知者 `W ＝ E_item`），表格與計算慣例段、測試表同步；佔位符搬列後的列同樣受約束 |
| 四輪 A-B2 `SP.MES#56` 沒有冷啟動可達路徑與退路 | 採納並解決：探針取得冷啟動收據（`docs/re/025`），`SP.MES#56` 納入試點，試點維持 17 項；不再需要「縮為 16 項」的退路，座標待查項（冷啟動選到 `SP#55`）記在第 2 節 |
| 四輪 A-R1 模擬器定義三件事 | 採納：具體模式與對抗模式、刪「（或項目分隔）」括號（NUL 先於步驟 4）、最大寬參數與寬度停止不改變相位的理由 |
| 四輪 A-R2 負對照缺口 | 採納：離開位移的最小案例與突變、(S 集 lead、P 集 trail) 加 `0A` 必須失敗、總數斷言獨立於往返 |
| 四輪 A-R3 試點 `%s` 畫面驗證 | 採納：觀測量改為字串偏移；增加兩字連鎖與 lead 在 `E0` 至 `F9` 的變體；冷啟動字面前綴實驗取代對 bot 檢查點的依賴，`ESPMES#118.2` 以 `-scratch` 暫存層變體做第二層 |
| 四輪 A-R4 至 R12 | 採納：`-lang-dir` 同時讀 manifest 雜湊、`PreflightState` API 形狀、層別判斷只改 `renameFile`、`StateDigest` 理由更正、024 引用節號更正、217 至 219 換算、空群組連續區間措辭、自動折行措辭、`%s` 緊接 `0A` 的原版 7 處與譯者後果寫入已知差異 |
| 四輪 B-B1 F1 四種值不互斥 | 採納：第 3.8 節改為（生效、啟動失敗、選擇）三量的狀態判定，優先序「啟動失敗 > 選擇與生效不同 > 生效為語言包 > 原版」；明寫 `zh-TW` 無表等同原版、L2 前非 `zh-TW` 的 `avail` 為假（原因 `unsupported-language`）、`no-patch` 在 L2 之後產生、identity 包不標「部分翻譯」、覆蓋旗標生效時 F4 不改遊戲內層與其提示字句 |
| 四輪 B-B2 前端接線不在授權範圍列舉 | 採納：範圍、實作位置、L1 列加「前端接線」，寫明與 006 實作的順序 |
| 四輪 B-R1 替換流程 | 採納：改名失敗回到「已存在」分支重驗；不搬動舊目錄，改用帶序號的新名稱；暫存目錄命名與清理；建置器版本專用常數；manifest 驗證補輸入摘要；新增明示值 `identity`（`l10n/zh-TW/` 存在後 `zh-TW` 建的是表包） |
| 四輪 B-R2、R3 F1／F4 文案與測試 | 採納：覆蓋旗標字句、identity 標示、原因為字串表鍵、測試補案例 |
| 四輪 B-R4、R5 第 3.9 節定義與接線 | 採納：片段（連續雙位元組字）與視窗定義、單位與解析器無關（基準掃描可先進行）、十六進位範圍列入已知漏報、`leakscan-allow.tsv` 拒絕登記超過 7 個字的單位、歷史用 `git rev-list --all`、`go_build` 泛化、`go.mod` 先手寫 `require`、git 串流備案、zh-TW 譯文表路徑級排除 |
| 四輪 B-R6 第 11 節 | 採納：補 `resolveStartup`、006 檔頭修訂記錄、`005` 的狀態檔載入限制、`AGENTS.md` 第 2、6 節條文草稿；改正「實作時處理」的責任歸屬（規格文字修訂歸 008，程式與字元表重產歸第 4 節 L1 前端接線） |
| 四輪 B-R7 至 R10 | 採納：L0 與 `AGENTS.md` 第 4 節「依 DOSBox-X」不適用的說明、`-allow-*` 與 `-with-candidates` 旗標只在 `hrl10n`、`status` 採用規則、「第 1 節」改「前言」、新增 U8（`leakscan-allow.tsv` 的政策），U4 補持久化獨立遊戲內語言設定 |

### 第五輪確認審查（第六版）的處理

| 項 | 處理 |
|---|---|
| 五輪 A-B1 突變「進入狀態只探索同步」是等價突變 | 採納：刪除該突變；第 3.5 節模擬器列改為展開之後的狀態集合與進入狀態無關，只探索離開狀態；第 8 節加性質測試（具體模式判定失敗者，對抗模式也必須失敗）；「拿掉位移延續」突變寫成可實作的內容 |
| 五輪 A-B2、B-B1(a)(c) 規則 4 與 `avail`、原因順序 | 採納：規則 4 在 L2 之前一律不建置（常數 `l2Supported`）；原因鍵順序 `no-table`、`unsupported-language`、`no-patch`；第 3.8 節、測試表與規則 4 同源 |
| 五輪 B-B1(b)(d)、A-R3 `avail(zh-TW)`、相同關係、真值表 | 採納：`avail` 逐語言定義；相同關係列舉；純函式 `ingameStatus` 同時決定 F1 值與 toast（五種字句）；16 列真值表；`-ingame-lang` 值域統一為 `代碼\|none\|identity` |
| 五輪 B-B2、A-R4 建置政策不在摘要、試點路徑 | 採納：政策（模式與三個旗標）進輸入摘要與 manifest；`Options.LangDigest` 由前端傳入；試點與 L3 樣張走 `hrl10n -with-candidates` 加 `-lang-dir`，前端只顯示 `accepted`；`l10nBuilderVersion` 守護測試 |
| 五輪 B-B3 第 11 節時機 | 採納：加時機欄；依賴尚不存在產物的 `AGENTS.md` 各列與 `003` 外洩掃描列改為對應產物提交時；U8 預設補命中處理順序 |
| 五輪 A-R1 預算規則 (3) 不計折行 | 採納：渲染列數 `ceil(展開位元組 / W)`；加反例與突變 |
| 五輪 A-R2 窗口未知的字面上限 | 採納：窗口未知比照 `win31x4`（行寬 30，行數 `max(4, R_item)`）；`UWASA.MES` 歸 `win31x4` 列 |
| 五輪 A-R5、R6、R7 涵蓋限制、試點重證、窗口種類 | 採納：第 2 節與試點列補 `docs/re/025` 第 6 節的涵蓋限制與寬度停止邊界變體；試點先以 identity 包重跑冷啟動點擊腳本；「所有窗口」改為 22 種立即值窗口，並記計算值窗口未量的風險 |
| 五輪 A-R8 至 R10 計數出處、節號、措辭 | 採納：625 與 624 的出處、36／67 與 49／121 的出處、第 5 節引用節號、`-ingame-lang` 值域、其餘措辭 |
| 五輪 A-R11、B-R8 升 READY 條件與前言措辭 | 採納：第 13 節重寫；前言註明 U4、U6 答非預設時要修訂的節；U1 至 U8 |
| 五輪 B-R1 第 11 節 `003`、`005`、`006` 的列 | 採納：`006` 第 201 行改寫、第 93 行修訂內容、`006` 第 5 行與本規格第 7 行的過時敘述、README 與發行說明兩列、`AGENTS.md` 第 14 節落點、M9 列重複與 U 編號 |
| 五輪 B-R2、R3 F4 提示組成與測試缺口 | 採納：toast 組成與寬度斷言、純函式與五種字句；第 8 節補 `verify-failed`、離開 `C_start`、優先序、leakscan 與守護測試；L1 出口加洩漏防線 |
| 五輪 B-R4 摘要重算與清理 | 採納：`Options.LangDigest`、空表雜湊常數、不清舊目錄、累積列入已知差異、原因鍵對應 |
| 五輪 B-R5 第 3.9 節定義 | 採納：單位身分、3 至 5 字只比相等、十六進位門檻漏報、歷史範圍統一、git 串流三元組、U8 的 `LICENSE` 問題 |
| 五輪 B-R6 `AGENTS.md` 草稿與 `LICENSE` 引用 | 採納：第 2 條 (c) 與第 1 條 (b) 引用更正、草稿加 [HARD]、private 與轉公開條件、「主 session 與子代理」、(c) 與 (d) 的順序 |
| 五輪 B-R7 L0 與 `AGENTS.md` 第 4 節 | 採納：第 1 節實作位置列改寫，L0 出口加與 `Overlay_Drive` 的比對差異；本輪沒有讀其行為，比對留給 L0 實作者 |
| 五輪 B-R9 正文敘述自己怎麼弄錯 | 採納：第 1 節與第 3.5 節的相關句改為只寫現況；檔頭審查沿革與本節是事實性記錄，保留 |
| 五輪 B-R10 狀態檔綁定路徑 | 部分採納：不改機制；寫明狀態檔記錄的絕對路徑本來就使跨機載入需要相同路徑（既有行為，`state.go:218`），回報流程不受本規格影響 |

### 第六輪確認審查（第七版）的處理

| 項 | 處理 |
|---|---|
| 六輪 A-B1 「拿掉位移延續」突變不可實作 | 採納：突變改為「被多吃一個位元組之後，緊接著分類到的 P 集位元組不再觸發多吃」；反例寫成具體位元組（`A4 E0 A4 E1 0A`、`[%s] A4 E0 E1 E2 0A`；審查 A 報告初稿曾把 `[%s] E0 E1 E2 E3 0A` 列為殺手案例，定稿已更正；主代理逐步推演確認它在突變下仍因同步離開失敗而殺不死突變，改列為一般反例） |
| 六輪 A-R1 試點邊界變體 | 採納：用 `ESPMES#121.1`，P 集位元組放偏移 30，預測第二次呼叫偏移 32，尾端 `E0 E1 0A`，加偏移 29 對照組 |
| 六輪 A-R2 模擬器突變缺口 | 採納：加「離開狀態只探索位移」突變與 `[%s] E0 E1 E2 0A`；性質測試補樣板與字母表；加 256 值逐點對照 |
| 六輪 A-R3 至 R10 數字、措辭與紀錄 | 採納：`E_item` ＝ 80 與 44 個內容位元組、23 種立即值窗口、窗口未知的措辭與已知風險、`R_item > H` 清單、`R_item` 的除數改為窗口容量（加 `R_item` 反例）、表格行數欄寫 4、`1676` 事實列括號、`%s` 後接 `0A` 的承接；`docs/re/025` 標頭更新 |
| 六輪 B-B1 守護測試是同義反覆 | 採納：黃金值綁合成譯文表 fixture 的 table 模式輸出，golden 記錄建置器版本，兩個負對照（改序列化器、只改常數；第八版改為由 golden 導出版本，見第七輪處理表 B-R1） |
| 六輪 B-B2 `probe`、`hrsoak` 沒有驗證路徑 | 採納：第 3.1 節更正 `hrbot` 經 `Session.Open`；`probe`、`hrsoak` 不驗 manifest；`hrl10n verify` 與 `Session.Open` 共用驗證函式，試點載入前先驗證，加負對照 |
| 六輪 B-R1 `ingameStatus` 介面與輸入域 | 採納：`startFail` ＝ `(C_start, 原因鍵)`、`avail` ＝ `(布林, 原因鍵)`、前置條件、`identity` 顯示字面、不認得的旗標代碼當作沒給；真值表加 5 列（共 21 列） |
| 六輪 B-R2、R3 括號矛盾與字句不符 | 採納：關係固定的敘述；toast 改為「尚無語言包」；採用列數寫入 manifest，為 0 的包標「驗證用」；L2 之後 `S ＝ zh-TW` 的待決列入第 9 節 |
| 六輪 B-R4、R5、R6 序號探測、`SkipLangDigest`、命令列契約 | 採納：序號目錄依序探測並重用；`LangDigest` 為空且未明示略過時 `Open` 回錯；`hrl10n` 命令列契約 |
| 六輪 B-R7、R12、R13 負對照、`planIngame`、審查範圍 | 採納：第 8 節補負對照；純函式 `planIngame` 與串接測試；第 13 節範圍補第 3.3 節與 U8 |
| 六輪 B-R8、R9 第 3.9 節登記粒度與歷史 | 採納：登記以所屬段的字數為準；單位來源限七個資料檔；歷史命中記入收據，不是 push 閘門條件 |
| 六輪 B-R10、R11 第 11 節三處與 `AGENTS.md` 草稿 | 採納：刪重複的 M9 句、README 現況與修訂句、拆開兩個負責者、草稿補第 1 條 (b) 與第 5 條 (e)、改為由使用者決定 `LICENSE` 措辭 |

### 第七輪確認審查（第八版）的處理

| 項 | 處理 |
|---|---|
| 七輪 B-B1 `planIngame` 簽章缺少是否明示 | 採納：`C` 定義為 `(代碼, 明示)`，「明示」與 `ingameStatus` 的 `override` 是同一個謂詞；`planIngame` 加兩個案例與規則 3 改成與規則 2 相同的負對照 |
| 七輪 B-R1 守護測試的殘留缺口 | 採納：`l10nBuilderVersion` 由內嵌 golden 檔位元組的 SHA-256 前 8 碼導出，輸出改變就必須重產 golden，版本隨之改變；fixture 涵蓋 `accepted`／`candidate`、`-with-candidates`、`-allow-*` 變體，位置在 fork 的 `apps/hr/l10n/testdata/`（合成資料，與 `AGENTS.md` 草稿不衝突），不在 fixture 的路徑列為不在守護範圍 |
| 七輪 B-R2、R3 前置條件、真值表欄位 | 採納：前置條件收窄；性質測試列入第 8 節；真值表加 `avail` 欄、列 21 與列 23 的 E 欄寫「table 模式，採用列數 0」、補列 22 與 23（共 23 列，列 1 與列 2 輸入相同），加突變 |
| 七輪 B-R4 F1 字句數 | 採納：F1 值四類、字句模板五個，字串表測試與負對照涵蓋「驗證用」；發行說明與 F1 (2) 的字面分開寫 |
| 七輪 B-R5 驗證函式位置、結果通道、`LangManifest` 算法 | 採納：驗證函式放在葉層套件 `apps/hr/l10n/verify`；驗證失敗 `Open` 不回錯，經 `Session.LangStatus()` 回報；`LangDigest` 缺漏的回錯先於存在性檢查；`LangManifest` 與 `LangDir` 正規化規則寫明，三處算出相同值的測試 |
| 七輪 B-R6 至 R10 | 採納：並行縫隙、舊目錄 inode、暫存目錄年齡、序號探測、哨兵檔、重複建置；歷史命中測試與「字」的定義；第 11 節 003 列加 `SkipLangDigest`、第 13 節範圍加第 3.1 節、試點加 `verify` 與負對照；`hrl10n` 命令列細節；L2 之後加真值表列；U8 例子是否在單位範圍內（需容器重現） |
| 七輪 A-R1、R2、R3 突變 M 的尾註、「第 30 個位元組」基準、試點變體前提 | 採納：突變 M 改為明確的旗標語句；第 2 節與第 3.5 節改為偏移 29 或 30（0 起算）；試點變體寫明前綴全為 S 集、偏移 31 取 S 集位元組、尾端位元組，預測以絕對偏移列出（同步假說 1059、1091、1094；位移假說 1059、1091；對照組 1059、1090） |
| 七輪 A-R4 至 R11 | 採納：渲染列數除數的理由（引擎每次呼叫至少消耗窗口容量個位元組）；`R_item` 除數直接寫成窗口容量；預算列的共用前提與 `R_item` 負對照、原項目全 `keep` 不經檢查；計數出處改為審查者量測、由 L1 統計收據重算；`00` 與 `0A` 為終止值；性質測試的確定性窮舉；第 14 節審查 A 的轉述更正；L1 預算統計收據加 `_vsprintf` 遙測 |

### 第八輪確認審查（第八版，升 READY）的處理

第八輪無阻擋；建議 R1 至 R14 的處理：

| 項 | 處理 |
|---|---|
| 八輪 R1、R7 試點對照組版面、填充位元組 | 採納：對照組寫明偏移 30 起全為 S 集、不含 `0A`，兩個假說預測相同；填充位元組避開 `0x20` 與 `0x25` |
| 八輪 R2、R3、R11 無頭路徑、`LangStatus` 原因鍵、`SkipLangDigest` | 採納：經 `Session.Open` 的無頭工具在 `LangStatus()` 回報非空原因鍵時非零結束，收據記生效 `LangDir` 與命中層；identity A/B 的負對照改為以建置器建出差一個字的包；`LangStatus()` 的原因鍵限 `verify-failed`，建置錯誤由前端記；`SkipLangDigest` 為真時忽略 `LangDigest` |
| 八輪 R4、R5、R14 `resolveStartup` 層測試、輸入域、串接測試 | 採納：`resolveStartup` 案例（不認得的旗標、空字串、明示等於 `override`）與負對照；規則 2 涵蓋 `(identity, 明示)`，`planIngame` 前置條件；相同關係改為只靠 E 的種類；`avail` 的「未定義」為讀取即 panic；串接測試用假建置器與假 `LangStatus` |
| 八輪 R6、R8 golden 穩定性、fixture 權利說明 | 採納：golden 機器產生、無註解、固定排序、LF、`-text`；另列採用列數與 manifest 其餘欄位；fixture 的 `accepted` 是測試值，L3 統計排除；`-allow-*` 變體選無法字典窮舉的項目 |
| 八輪 R9、R10、R12、R13 第 11 節與措辭 | 採納：`003` 的 `Open` 列補 `LangStatus()`、`AGENTS.md` 第 4 節補 `apps/hr/l10n/verify`、`info.txt` 第一項另記 `LangStatus` 原因鍵；第 14 節舊列加註；時機圖例補第四種；F1「四類值」統一；`verify` 參數順序；刪重複負對照 |
