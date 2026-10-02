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
