# WORKLOG

依日期追加的工作歷程與勘誤。現況寫在 `AGENTS.md` 與 `docs/`，這裡只記過程。

## 2026-10-02

- 取得 jsdos 版與傳統 zip 原版，建立雜湊清冊與啟動鏈盤點（`docs/re/001-source-intake.md`）。
- 驗證使用者提供的第三方玩家文件（`docs/re/002-third-party-notes-verification.md`）。
- 建立 private repo `wicanr2/high_reward_remastered`，首次推送。
- Docker 清理：所有容器皆為 `--rm`，無殘留；`workplace/` 內無 root 擁有的檔案。

## 2026-10-03

- 使用者授權 push 並確認三平台範圍，總目標設為：完成移植到 dosgolem、修當機、HD 化。
- M2 完成：`workplace/dosgolem` 取自 commit `2f44a68`，探針停在 `0110:206E` 的 `66 8B`（`docs/re/003`）。
- 發現 `SingleStepTests/80386` 的 `v1_ex_real_mode` 語料（真實 386EX，real mode），作為 CPU 386 形式的驗收依據。語料與 dosgolem 副本中的 MOO 讀檔器、`TestSST386` 都不進本 repo（前者授權另有規定，後者在 `workplace/dosgolem` 的本地分支）。
- 規格 `docs/spec/001-cpu-386-real-mode-forms` 為 DRAFT，送唯讀審查中。
- 圖像容器格式逆向交給背景子代理，工作目錄 `workplace/re-img/`，結果回來後由主代理核對再搬進 `docs/re/`。
- 規格 001 第一輪審查（唯讀子代理）有 6 項阻擋，已據以修訂為第二版。內容：規格漏了語料測試必然含的 `64`／`65` 前綴；EFLAGS 高 16 位元的語料行為未定義；harness 契約與缺語料處理不明；AC 負對照不會失敗；對 `Seg`、`EAXHi`、快照與狀態檔的影響未列；證據等級與完整清單未入 docs。

### 勘誤

- `docs/re/003` 的 386 普查第一版共 20 條、12 種，漏了無前綴的 `8C`／`8E`（FS、GS 段暫存器移動），因為腳本只看帶前綴與 `0F` 的指令。審查發現後補上，現為 22 條、14 種。教訓：普查「某一世代專有的指令」要列出該世代新增的所有編碼形式（含無前綴者），不只看前綴。
- 補普查腳本時，`json.dump` 因輸出檔以預設編碼（ASCII）開啟而在含中文的鍵寫到一半失敗，產出被截斷的檔案。IDAPython 腳本的輸出檔一律明寫 `encoding="utf-8"`，並以讀回解析驗證。
- 規格 001 第二輪審查有 4 項阻擋，已修正並升為 READY（第三版）：harness 要執行 HLT 才能對上 `eip`（語料的 FINA `eip` 在 HLT 之後）；`DOSGOLEM_SST386_REQUIRE` 要經 `tools/go.sh` 轉進容器；狀態檔線上格式改為保留 `Seg [4]` 並新增 `FS`、`GS`、`Hi`，版本升 3 並接受 2 與 3；`-watch` 印的是指令結束後的 IP，預期位址改為 `2059`、`206C`、`2092`。另補：寫入 0 到未列出位址的漏洞、`66C1.5` 檔層級遮罩連 CF 與 OF 一併遮掉所以要補單元測試。
- 8088 語料下載：序列下載約 0.1 檔每秒，改為 8 條平行後約 650 KB/s。
- CPU 386 real mode 形式完成並驗收（規格 001 CONFORMED，收據 `docs/re/005`）。語料推翻一項預期：`popad` 的 ESP 格高 16 位元會寫進 ESP 高半。dosgolem 變更備份在 `engine/patches/`。
- `MAIN.EXE` 在 dosgolem 跑到標題選單與新遊戲第一畫面（`docs/re/008`），畫面雜湊重跑一致。
- 圖像格式（`docs/re/006`、`tools/img/`）與 FBOV overlay 結構（`docs/re/007`、`tools/ovr/`）由兩個背景子代理逆向，主代理重跑工具並核對（615 張 PNG 與子代理輸出逐檔相同、overlay 28 項驗證全 PASS、目視 `FACE.MRG_000` 與 `MAP01.PXZ`）。
- 探針的 `-log-calls` 與呼叫軌跡在 8 億步時被容器記憶體上限殺掉（輸出為空）。改寫專用長跑驅動 `apps/hr/cmd/hrsoak`（在 dosgolem 副本內）：不追蹤、定期輸出資源計數、存檢查點與停機現場。
- 4 億步閒置長跑沒有當機。觀察：音樂檔每 5000 萬道指令被重開約 3300 次；開著的檔案代號與配置游標在第 3 億道之後各增加一格（是否洩漏未知）。隨機輸入的長跑進行中。

### 勘誤（續）

- `docs/re/003` 與 `AGENTS.md` 先前寫「IDA 常駐映像 119 個段落，overlay 尚未載入 IDA」。119 來自被 `head` 截斷的輸出；實際 IDA 9.4 預設就載入 `FBOV`，共 510 段（常駐 232、stub 139、overlay 139），普查早已涵蓋 overlay（overlay 內 386 形式為 0）。教訓：看到列表輸出被截斷時，用計數欄位而不是列出的行數；「工具載不到」的結論要用該工具的正對照（直接數段落）驗證。
- `docs/re/004` 先前寫「沒有 `int 33h`、常駐映像沒有設定圖形模式的 BIOS 呼叫」。實際是經 C 函式庫的 `_int86` 呼叫（視訊模式 12h 與滑鼠 14 處），`int` 指令普查看不到。教訓：普查「軟體中斷」要同時查 `int n` 指令與 C 函式庫的呼叫包裝。
- 主機上誤跑了兩次 `python3`（一次查版本、一次空腳本），沒有產生任何檔案；分析一律在容器內，之後不再在主機執行 python。

### 長跑與當機（2026-10-03，續）

- 長跑驅動 `hrsoak` 補了存檔槽讀取（腳本與隨機輸入並用）、正常結束退回復原點、指令軌跡環、閒置輪詢點的 SP 與 BP 鏈記錄、堆疊溢位偵測、`-stklen`。診斷紀錄不清會在 10 億步左右耗盡容器記憶體，已每 200 萬道指令清一次。
- 存檔槽 4（種子 14）停機於第 765,558,229 步，原因是玩家結束遊戲（結束碼 1，畫面是「請關閉電源再見」），不是當機。`HR.BAT` 的 `if errorlevel 1 goto quitprog` 證實結束碼 1 的語意。
- 存檔槽 2（種子 22）第 3,093,737,047 步跳進視訊記憶體位址範圍：堆疊溢位。原版堆疊 4096 bytes（`_stklen ＝ 0x1000`），選單巢狀呼叫在這個輸入下最深用到 5266 bytes。同種子把 `_stklen` 改成 0x4000 或 0x8000，跑滿 45 億步無停機，且畫面雜湊相同。五個存檔槽各 80 億步（`_stklen ＝ 0x8000`）無停機，最大深度 3094 bytes。證據與限制在 `docs/re/011`，修補規格 `docs/spec/002-stack-size.md`（DRAFT）。
- 三個子代理（唯讀）交回 `docs/re/009`（繪圖原語）與 `docs/re/010`（音樂子系統）兩份 DRAFT。音樂路徑要 `SOUND` 環境變數與 `ctmidi.drv`，dosgolem 環境沒設 `SOUND`，所以音樂與音效都不執行；這解釋了音樂檔每 1.5 萬道指令被重開一次。
- 新增 `apps/hr/cmd/hrexplore`（介面探索器）：從存檔槽與新遊戲起點，以網格左鍵、右鍵與三個按鍵系統性探索閒置畫面，畫面身分是閒置輪詢點的呼叫鏈加 SP。

### 勘誤（續二）

- 記錄「堆疊洩漏」的第一個假設是錯的：閒置基準 SP 全程不變，沒有逐次洩漏。成因是巢狀選單的深度本身超過 4 KB。
- 先前的 `docs/re/011` 草稿寫「`SP` 在更早之前已經減過 0」。軌跡重看後，呼叫端框架在 `54C0:0028`（堆疊用掉 99%），第一次繞回發生在該函式為呼叫推入參數的當下；已改寫第 4.2 節。
- 一版 `hrsoak` 的堆疊溢位偵測在第 83 步就誤報：啟動碼把 `SP` 設成 `_stklen ＋ 0x10`，不是 `_stklen`。偵測改為啟動完成後才讀頂端。
- 主機上又誤跑一次 `python3 -`（讀標準輸入，無腳本，沒有產出任何檔案），已中止該行程。分析仍一律在容器內；shell 命令前不再寫 `python3`。

### 執行層、前端、打包與 HD 規格（2026-10-03，續二）

- 規格 `docs/spec/002`（堆疊補丁）與 `003`（執行層與前端）經唯讀審查後升為 READY。實作在 `workplace/dosgolem` 分支 `hr` 的 `apps/hr`（`patch`、`runtime`、`hd`、`play`、`cmd`），備份在 `engine/patches/`。執行層測試 14 項通過（`docs/re/013`）。
- 前端是獨立 Go 模組（ebiten 2.9.9）。打包腳本 `tools/package.sh`：Linux AppImage（cgo，ebiten 在 Linux 不支援 `CGO_ENABLED=0`）、Windows zip（`CGO_ENABLED=0`，Wine 驗啟動與標題）、macOS universal（osxcross，未簽章，只驗結構）。外洩掃描以原版檔名與雜湊比對，發行包不含原版素材與 HD 素材。
- 規格 `docs/spec/004`（HD 疊層）審查已六輪。第一版 6 項阻擋、第二版 6 項、第三版 4 項、第四版 3 項（第五輪）、第五版 2 項（第六輪）。第五輪結果：游標殘影靠 3x3 驗證只能從游標面積的 15.2% 降到 4.45%，要靠呼叫點 singleton；淡入公式對參考值小於 16 的通道用加法，DAC 全 0 時留下未淡化的底色；3x3 的樸素實作在 512 個戳記要 18 至 23 ms。第五版據此修訂（`2fc86f0`）。第六輪的 2 項阻擋是數字沿用解釋規則之前的值、混合順序要由大到小並略過已覆蓋像素（由小到大在 512 個戳記要 17 至 21 ms），設計不變；第六版修訂後送窄範圍複核。
- 快照改為拉取式（前端 `RequestFrame`），`Frame` 帶像素值、`Map` 與 `DAC`。起因：每 8 ms 推送一次 RGB 快照，`PlanarRGB` 一次 1.8 至 3.3 ms，會吃掉兩到四成的單核。

### 勘誤（續三）

- 規格 004 第一至三版的依事件移除規則（新繪圖覆蓋舊戳記就移除；還原後相符比例低於 70% 就移除）都會誤刪：遊戲貼圖前備份背景，對話關閉時還原的是含精靈的舊畫面，不重繪；`SPOINT_014`、`SPOINT_012`、`GMAP`、`BC32:120` 長期只有 27% 至 68% 相符。第四版起刪除所有依事件的移除規則。
- 第四版假說「3x3 鄰域驗證消除游標殘影」被第五輪實測推翻（降到 4.45%，不是接近 0）。游標改以呼叫點（返回位址 `19FB:08A2`）為 singleton 鍵，因為游標靠右緣時雜湊會變。
- 淡入中間狀態不是參考調色盤的整體比例：73 個狀態的最大殘差 8 位元為 7.9 至 19.8。第三版的全域比例假設不成立；第四版改為逐像素縮放，第五版再把 `R < 16` 通道的加法改成乘法。
- 前幾輪的 `docs/re` 與 `AGENTS.md` 文字還有幾次在主機用 `perl`、`python3` 做文字處理或查版本。分析與轉檔一律走容器；純文字修改用 Edit 工具、`sed`、`awk`。

### HD 疊層實作（2026-10-03，續三）

- 規格 `docs/spec/004` 第七輪窄範圍複核確認設計無阻擋，文字與數字修正落實後升為 READY（第六版，`f03756c`）。
- 實作在 `workplace/dosgolem` 分支 `hr`（`65706a9`、`6a0ff0d`）：`apps/hr/hd` 的戳記佇列、位元列 3x3 驗證、由大到小的前往後混合、純乘法淡入縮放、清冊載入、進入點掛鉤；`apps/hr/runtime` 的 `Frame.Stamps` 與 `FrameLimiter`；`apps/hr/play` 的 `-hd`、`-no-hd` 與背景合成；`apps/hr/cmd/hrhd` 驗收工具。收據 `docs/re/014`。
- 冷啟動到新遊戲與戰鬥佈陣兩個情境，所有精靈與串流的返回時相符比例皆 1.000，未識別的只有游標；掛鉤開關不改變遊戲（畫面、暫存器、1 MB 記憶體逐位元相同）；淡入掃描 8,787 張快照、1,800 張全黑，漏光 0 張。
- 合成時間單核約 11 至 13 ms（負載高時），超過規格的 10 ms 目標；改依來源列平行（4 核約 6 ms，結果與單執行緒逐位元相同）。單核目標未達。

### 勘誤（續四）

- 規格 004 第 4.1 節原本寫 `2E92:066A` 與 `348F:0005` 的「位置取自偏移」，沒寫要加 40 列。第一次實作把偏移直接當 Px 列，`FACE` 返回時只有 20.2% 相符；`hrhd` 的診斷找到最佳位移 `(+0, +40)`。規格已補。教訓：規格的座標系（遊戲區或 Px）要寫在每個參數旁，審查者的工具與實作用不同座標時，數字不能直接互相引用。
- 又在主機執行了一次 `python3 --version`（只印版本，沒有產生檔案）。分析與版本查詢都走容器；主機上只用 `sed`、`awk`、Edit 做文字處理。

### HD 素材進版控（2026-10-03，續四）

- 使用者先授權把 HD 候選素材放進 `hd/`，隨即要求先看合成圖；產生六個畫面的並排對照與 4 張局部放大後，使用者回覆「可以」。建立 `hd/`（595 張 PNG、清冊、調色盤表、`provenance.tsv` 狀態 `candidate`），新增 `docs/re/015`（美術 v2 方法紀錄，由 `workplace/hd-work/METHOD.md` 搬入並補驗收狀態），收據 `docs/re/014` 第 9 節。
- 這輪發現：從狀態檔載入的畫面沒有戳記，HD 欄等於原版（載入不經繪圖函式），驗收圖要用會整個重畫的路徑產生。此限制在 `docs/re/014` 第 9 節記錄；正常遊玩不受影響。

### 含 HD 素材的發行包（2026-10-03，續五）

- 使用者授權發行含 HD 素材的版本與推送 fork 的 `hr` 分支。`tools/package.sh` 新增 `HR_WITH_HD=1`：把 `hd/` 放進三平台包（`dist-all/with-hd/`、版本加 `-hd`、附 `hd/NOTICE.txt` 與 README 的 HD 段）。版本 `d3fea9e-dg8eb277d-hd`，AppImage 與 Windows（Wine）不另掛目錄即顯示 HD，macOS 只驗結構（`docs/re/013` 第 4.2 節）。
- 推送 `hr` 分支到公開 repo `wicanr2/dosgolem` 被分類器拒絕（Out-of-Place Publication）。該分支的基底 `2f44a68` 已在遠端的 `fix/stubseg-font-collision-program-path`，推送只會多出 18 個提交、64 個檔案，沒有原版或 HD 素材，但含 `apps/hr/runtime/required.tsv`（77 個原版檔案的檔名、大小與 SHA-256）。沒有繞過，也沒有加遠端；等使用者再次明確指示。

### HD 素材整體接受（2026-10-03，續六）

- 使用者表示「HD 我都接受」。`hd/provenance.tsv` 的 595 列由 `candidate` 改為 `accepted`，新增 `accepted_by`、`accepted_date` 兩欄；`packaging/HD_NOTICE.txt`、AGENTS.md、`docs/re/014`、`docs/re/015` 同步。這是看過代表畫面（六個合成畫面與四張局部放大）後的整體接受，不是逐張審查。
- 使用者另外授權在 private repo 建立 Release（含 HD 的發行包）、把 Buck Rogers 分支整合進目前的 `hr` 分支（之後由使用者處理 dosgolem main 的合併），並要求安排「真的遊玩兩小時」的當機測試。含 HD 的包因 `provenance.tsv` 與 NOTICE 改變而重建。

### Release、Buck Rogers 合併（2026-10-03，續七）

- 在 private repo 建立 Release `v0.1.0-hd`（預發行，目標 commit `9d4f0f0`）：三個含 HD 的包與 `SHA256SUMS.txt`（`docs/re/013` 第 4.2 節）。HD 素材 595 張全部 `accepted` 後重建，版本 `9d4f0f0-dg8eb277d-hd`。
- 使用者授權把 Buck Rogers 分支整合進 fork 的 `hr` 分支。從公開 repo 以 URL 抓 `buck-rogers-cht-output-overlay`（tip `beca734`，354 個提交、459 個檔案，與 `hr` 的共同祖先 `d9c0c27`），打標籤 `hr-pre-buckrogers` 後合併，合併提交 `50ffc62`。衝突三處：`internal/dos/int21.go` 的 `AH=2Ah`（保留 `d.Date`，沒設才用 `virtualDate()`）、`internal/machine/state.go` 的 `SaveState`（保留 hr 的 CPU 欄位並加 Buck Rogers 的 VGA 與時脈欄位）、`docs/spec/000-index.md`（兩邊條目都留）。根模組現在需要 ebiten 與 `golang.org/x/sys`，離線建置要用含模組快取的映像（`DOSGOLEM_GO_IMAGE=eob-remake-go:1.26.7-ebiten2.9.9`，`tools/go.sh` 轉送 `GOPROXY`、`GOSUMDB`、`GOTOOLCHAIN`，模組快取從該映像複製到 `workplace/gomodcache`）。
- 驗證：`go build ./...` 通過；`go test ./internal/... ./apps/hr/...` 全部通過（hr 的收據 A、B 畫面雜湊、堆疊補丁、`internal/cpu` 386 形式都在內）；`apps/hr/play` 的前端仍能建置。沒有推送。
