# 036 城市編成畫面的隊長姓名錯位

日期：2026-10-14。推論等級：confirmed 的項目均由原版正常點擊與 IDA 指令支持。

## 目前狀態

| 項目 | 狀態 |
|---|---|
| 原版問題 | 已重現，限城市「部隊間編成」中三位隊長的姓名 |
| 一般士兵名稱 | 已抽測商人、砲兵、舞孃，正確 |
| 修正 | 已實作並通過九項同狀態比較，契約見 [013](../spec/013-formation-commander-names.md) |
| 正式交付 | `v.1.0.5-20261014`，三平台公開補丁包與本機完整版完成，舊版保持原狀 |

## 輸入與工具

- `MAIN.EXE`，SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`。
- dosgolem 專案副本 `7989c7b7109bae9cc12cc67d8e1603cfba47ba2f`，Go 1.26.7；Docker `hr-go-ebiten:1.26.7-2.9.9-r1`。
- IDA Pro 9.4，image `ida-pro-9.4-idapython:py312-v1`；一次性複製既有 `.i64`，沒有修改正式資料庫。輸出驗證 SDK 940、1968 個函式、無 `error`。
- IDA 證據使用 selector:offset。常駐資料的執行期段為 IDA 段減 `0xEF0`；overlay 384 的載入段會變動，以執行期 stub `53E3` 識別，IDA 段為 `80F0`。換算入口見 [007 第 8 節](007-fbov-overlay-structure.md)，對照表為 `apps/hr/runtime/ovrtab.go`。

原版記憶體、狀態檔、完整反組譯輸出及截圖只留 `workplace/out/troop-names-*`，不加入 Git。

## 重現與根因

正常新遊戲，完成開場對話，點薩蘭特城，再選「部隊間編成」。點第三、四、五欄最上方的隊長。下表的隊長編號從 0 開始，畫面欄號從 1 開始。

| 隊長編號／欄號 | 正確人物 | 原版編成畫面讀出的姓名 |
|---|---|---|
| 2／3 | 商人隊長 | 砲手隊長的姓名 |
| 3／4 | 砲手隊長 | 舞孃隊長的姓名 |
| 4／5 | 舞孃隊長 | 商人隊長的姓名 |

confirmed：這是隊長姓名，並非一般商人、砲兵、舞孃的兵種名稱。左鍵選一般士兵會進入「請選擇移動目的地」，選隊長則保留「請選擇欲移動之兵士」。後者與使用者截圖相符。

confirmed：`sub_826CC`，IDA `80F0:17CC`，從動態部隊記錄取得士兵類型。記錄長 `0x17E`，士兵長 `0x1B`，首位士兵類型在部隊記錄 `+0x55`。六隊隊長的值依序是 `0,1,2,3,4,5`。姓名表則在 IDA `4839:0008 + 類型 × 0x2E`，前六筆依序對應前兩位戰士隊長、砲手隊長、舞孃隊長、商人隊長及槍兵隊長。兩種編號的 2、3、4 順序不同。原字串與畫面留在本機收據，公開文件用角色身分定位。

| IDA 位址 | 原始 bytes／運算元 | 用途 |
|---|---|---|
| `80F0:1907..1913` | `mov al,[bp+arg_2]`；`imul ax,1Bh`；`les bx,[bp+var_4]`；`mov ax,es:[bx+55h]` | 取得所選士兵類型 |
| `80F0:1917` | `6B C0 2E`，`imul ax,2Eh` | 把類型直接當姓名表索引 |
| `80F0:191A` | `05 08 00`，`add ax,8` | 指向名稱欄 |
| `80F0:191D..1920` | `push seg seg076`；`push ax` | 傳入姓名指標 |
| `80F0:192B` | `9A 74 4B 00 10`，`call _sprintf` | 只格式化姓名 |
| `80F0:1933` 起 | 重新從原部隊記錄讀能力及裝備 | 姓名表索引不參與後續能力計算 |

confirmed：個別部隊報告的雷姆姓名正確。其部隊記錄 `+0x15` 為正確的隊長名；另外兩隊同樣保存多明妮與迪詩蕾德的正確姓名。修正採名稱表完整姓名，僅把編成畫面的姓名索引 `2→4、3→2、4→3`，不交換整筆人物或兵種資料。

## 證據入口與重跑

- [IDA 匯出器](../../tools/ida_troop_names.py)：在既有資料庫的一次性副本執行，參數為輸出 JSON 與可選的 IDA `段:偏移`。輸出保留原名、位址、bytes、運算元與 xref，沒有改名。
- `workplace/out/troop-names-ida-draw.json`：包含 `80F0:17CC`、`16C6`、`1F63`。
- `workplace/out/troop_names_probe.go`：原版正常滑鼠輸入探針；移到目標後先前進 500,000 道指令，再按住至三次輪詢、放開並前進 5,000,000 道指令。原版目錄唯讀。
- `troop-names-leaders.log`、`troop-names-leaders-texts.json`、`troop-names-leaders-00.png` 至 `05.png`：六位隊長的實際繪字引數與畫面。
- `troop-names-wrong.log`：一般商人、砲兵、舞孃的正對照，名稱均正確。
- `troop-names-individual.log`、`troop-names-individual-00.png`：個別部隊報告與正確雷姆姓名。

初次探針把兵種與隊長混為一談，尚未重現；另有開場最後一句未關閉、選單滑鼠移動與按下同時送入的操作問題。修正探針後重跑，不將這些無效操作列為產品結論。

## 修正與驗證

正式 Session 在執行原版 `imul ax,2Eh` 前驗證 overlay 雙向身分、23-byte 簽章、隊長槽、部隊範圍與全域／局部部隊指標，只改 AX 的姓名索引。沒有修改原版檔案、資料表、能力、裝備、部隊記錄或存檔。實作與測試位於 `apps/hr/runtime/commander_names.go`、`commander_names_test.go`；原版 A/B 選項為 `Options.NoCommanderNameFix`。

同狀態收據 `workplace/out/commander-ab.json` 及 `troop-names-final-tests.log`：

| 比較項目 | 結果 |
|---|---|
| 三位錯名隊長 | 修正後正確；姓名區分別改變 974、1283、1374 像素 |
| 其他三位隊長、一般商人／砲兵／舞孃 | 0 像素差異 |
| 姓名區以外 | 0 像素差異 |
| 能力及裝備 | 九項各觀測三行繪字引數，A/B 相同 |
| 六隊部隊記錄 | 執行期線性 `3440F..34D02` 共 `6 × 0x17E` bytes，A/B 相同；隊長點選前後也相同 |
| 拒絕條件 | 錯位址、overlay 未載入／被重用、異常指標、非隊長、非法編號、型別不符及每一簽章 byte 的反對照均通過 |
| 既有回歸 | 原版冷啟動 A 收據、版本拒絕、`go vet`、Linux 前端及 Windows amd64 編譯通過 |

比較從同一正常玩家快照開始，輸入相同；名稱不同會改變原版繪字指令量，不能用任意同一步數判斷游標相位。收據記錄兩側實際停止步數，於原版輪詢點取得既有逐像素游標驗證通過的完整 Frame，以 `Presentation.Px` 去除游標後比較。初次固定步數比較在游標末端出現額外差異，未採納為通過；沒有擴大允許姓名矩形。允許變更矩形是 VGA `(100,358,160,16)`。

正常冷啟動再經正式 Session 走新遊戲、開場對話、城市選單及三位隊長，截圖 `troop-names-fixed-normal-02.png` 至 `04.png` 的姓名正確，沒有載入快照或注入部隊資料。原版輸入與探針雜湊保存於 `troop-names-input-hashes.json`。唯讀審查入口 `review-troop-names-spec.md`、`review-troop-names-implementation.md`。

Linux Xvfb 實際前端也從新遊戲走相同流程，`workplace/out/formation-names-gui/merchant.png`、`gunner.png`、`dancer.png` 已目視確認三位姓名正確。操作與程式日誌保存在同目錄；前端執行檔為 `workplace/out/hr-play-formation-fixed`。原版主題、繁體中文，無快照或部隊資料注入。Windows 只有編譯，未實機操作；修正驗證階段尚未重建正式封包，後續交付見下節。

執行層提交 `40f6f8a8dceb863ff8f46aa86ff0f29ff268ebab`。可重建補丁：[engine/patches/0046-formation-commander-names.patch](../../engine/patches/0046-formation-commander-names.patch)。收尾稽核 `workplace/out/troop-names-final-audit.json` 通過：補丁反向套用檢查成立，主 repo／fork 未追蹤原版完整檔，沒有 root-owned 檔案或 `.md` 目錄，fork 乾淨，本次 `hr-name-*` 容器無殘留。

## 本版交付

使用者要求重包後，以根 `5f41ed8f60bd5f485b480ba42def1ad601770350`、fork `40f6f8a8dceb863ff8f46aa86ff0f29ff268ebab` 的乾淨來源建立 `v.1.0.5-20261014`。公開補丁與本機完整版各三包。六包重新解出驗證版號、平台格式、素材及雜湊；Linux 實包正常城市編成的三位姓名正確，HD／AI 切換成功。公開包另以合法原版目錄啟動，兩類 Linux 包的執行器相同。驗收在 `dist-all/v.1.0.5-20261014/smoke/full-static.json`、`smoke/linux/receipt.json`，獨立發行審查 `workplace/out/review-release-v105.md` 無阻擋。

[正式 Release](https://github.com/wicanr2/high_reward_remastered/releases/tag/v.1.0.5-20261014) 只上傳三個 patch 包、公開清冊與 LICENSE，共五個資產，遠端大小與 SHA-256 全符本機。完整版留在 `dist-all/v.1.0.5-20261014/full-local/`。Windows／macOS 未原生實機操作，macOS 未簽章。原版 Creative 音樂研究未納入本版；舊 tag／Release 與封包不變。
