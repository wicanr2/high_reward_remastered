# 005 CPU 386 real mode 形式的驗收收據

日期：2026-10-03
對應規格：`docs/spec/001-cpu-386-real-mode-forms`（READY，第三版）
實作：`workplace/dosgolem` 本地分支 `hr`，commit `3cdc3ae`（基底 `2f44a68`）
重跑：以下命令都在容器內執行（`tools/dosgolem.sh`）。

## 1. 80386 語料（規格 §6.1）

```text
tools/fetch_sst386.sh <30 個檔名>
DOSGOLEM_SST386_REQUIRE=1 tools/dosgolem.sh go test ./internal/cpu -run TestSST386 -v -count=1
```

- 語料：`SingleStepTests/80386` `v1_ex_real_mode`，commit `459d49fbe6280e9ed46fee887b58dacd9cb880ab`，30 個檔的 SHA-256 在 `data/005-sst386-corpus-manifest.txt`。
- 結果（逐檔 `RECEIPT` 行在 `data/005-sst386-run.txt`）：30 個檔全部有測試被執行，合計總數 37500、執行 35994、失敗 0、排除 `excp` 1506、排除 `revoked` 0。每個檔的有效測試比例都在 92% 以上（最低 `665C`：927 對 1000）。
- 驗收過程中語料推翻了規格第一版的一條預期：`popad` 的 ESP 那一格，彈出值的高 16 位元會寫進 ESP 高半（手冊只說「丟棄」）。`6661` 的 2318 個有效測試逐筆如此。規格 §4.6 已改，實作與單元測試已改。

## 2. 既有基準不退化（規格 §6.2）

- 8088 語料（323 個檔，`data/005-sst8088-manifest.txt`）：`TestSingleStep` 執行 315 個檔、0 skip、0 失敗。其餘 8 個是 FPU 檔（`D8` 至 `DF`），dosgolem 既有規則不做 x87，整檔跳過（`docs/spec/001` §3 第 2 點）。
- `go test ./... -count=1`（`DOSGOLEM_SST386_REQUIRE=1`）：15 個套件 `ok`、19 個無測試檔、0 失敗，逐行見 `data/005-go-test-all.txt`。需要原版素材或 `DOSGOLEM_FD2_EXE` 的測試依既有規則 skip。

## 3. 負對照（規格 §6.3）

每項都先做出會失敗的變體、確認失敗、再還原（還原後 `git diff` 為空）：

| 變體 | 預期失敗的測試 | 實測 |
|---|---|---|
| `pushad` 推入 `esp - 16`（遞減後的值） | `6660`、`TestPushadPopad` | `6660`：2427 筆有效測試全部失敗；`TestPushadPopad` 失敗 |
| 移除 `64`、`65` 前綴支援 | `668B`、`TestFSGSOverridePrefixes` | `668B`：973 筆中 101 筆失敗；單元測試失敗 |
| `popfd` 讓位元 18 可寫（`pushfd` 一併推出） | `TestCPUDetectionSequence386` | 失敗 |

單元測試（`internal/cpu/ops386_real_test.go`）涵蓋：CPU 型號偵測序列（AC 不可寫，結果為 0）、`shr`／`shl` 32 位元的 CF、OF、SF、ZF、PF（含移位數 0、32、33 的遮罩行為，期望值由人工依手冊寫出）、`pushad`／`popad`、`push esp`／`pop esp`、`pushfd`／`popfd`、FS／GS 的 push、pop、mov 與 `64`／`65` 前綴、`0F` 跳脫（386 只認四道，8086 與 80186 維持 `POP CS`）、80186 以下 `64` 不是前綴、16 位元寫入保留高半。

## 4. 快照與狀態（規格 §6.4）

`internal/machine/state386_test.go`、`internal/dos/state386_test.go`：快照、回呼、EXEC 父行程框、狀態檔來回後 `Hi`、`FS`、`GS` 逐位元相同；`stateVersion` 與 `dosStateVersion` 為 3，v2 檔可載入且新欄位為 0，版本 1 與 4 被拒絕。`dos_test.go` 與 `mouse_contract_test.go` 的回呼前後比對已含 `Hi`、`FS`、`GS`。

## 5. 程式層收據（規格 §6.5）

```text
tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 3000000 -watch 54794-54795 -coverage /out/cov-main-3m.json
```

輸出節錄在 `data/005-probe-main-3m-watch.txt`。

- `MAIN.EXE` 跑滿 3000000 道指令仍然活著，不再停在 `0110:206E`。
- `-watch`（只記值改變的寫入，印指令結束後的 `CS:IP`）：第 61258 道，`word_63694` 由 0 變 2，寫入者 `0110:206C`（起點 `2066`）；第 61271 道，由 2 變 3，寫入者 `0110:2092`（起點 `208C`）。最終值為 3，沒有 `0110:209D`（不會寫 4）。`mov word_63694, 0` 的寫入（`0110:2059`）沒改變值，所以不在記錄裡。
- 程式在第 66884 道切到視訊模式 12h，之後 `ES=A0C8`，平面寫入模式 0 使用 70400 次，計時器送出 5 次，鍵盤 0 次。
- 覆蓋率（`-coverage`）：CPU 偵測常式 `0110:206E` 有執行；`pushad`（`0110:7029`）、`popad`（`0110:7044`）、`pop gs`（`0110:73E4`）的路徑在這 3M 道指令內沒有被走到，這幾種形式目前只由語料驗收。

## 6. 結論

規格 001 §6 的五項驗收全部成立，規格狀態改為 CONFORMED。已知差異不變：CPU 型號固定為 386，不做例外，`0x67` 與 SIB 不支援。M3 下一步：以 `MAIN.EXE` 繼續冷啟動，進入片頭、主選單與遊戲（見 `AGENTS.md` 第 13 節）。
