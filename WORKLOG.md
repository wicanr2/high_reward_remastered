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
