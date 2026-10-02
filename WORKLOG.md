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
