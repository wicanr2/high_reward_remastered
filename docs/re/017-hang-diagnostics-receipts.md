# 017 停機與 hang 診斷的實作收據與模擬

日期：2026-10-03
範圍：`docs/spec/005`（READY）的實作、測試、效能與一次模擬 hang。對象是 dosgolem 內執行的 `MAIN.EXE`，不是使用者環境。不含：聲音、`OP.EXE`、`END.EXE`、DOSBox-X 交叉驗證。
推論等級：confirmed（程式碼、測試輸出或實跑直接可見）、強推論、假說、未知。

## 1. 結論

- 遊戲 hang 住（或停機）時，runtime 會存一份診斷：暫存器、呼叫鏈、堆疊頂部、最近呼叫與服務中斷、最後一次呼叫的目標、最近開啟的檔名、迴圈取樣、畫面與狀態檔。confirmed（第 4 節的模擬）。
- 觸發有三種：非正常停機（T1，沿用 `CrashDump`）、遊戲碼的服務中斷靜默滿 30 遊戲秒（T2，自動）、前端按 Ctrl+D（T3，手動）。confirmed（單元測試，第 3 節）。
- 模擬「`1F69:000E` 被呼叫後不返回」：診斷在遊戲時間 1.5 分（`1F69:000E` 被改成 `jmp $` 之後約 30 遊戲秒）產生，「最後一次呼叫的目標」是 `1F69:000E`，呼叫處是 `19FB:07BF`（IDA `28EB:07BF`），取樣第一名是 `1F69:000E` 的 4096 次。confirmed（第 4 節）。
- 偵測器已用正對照驗證會報警（`jmp $`、`cli; jmp $`、卡在 ISR 內、有滑鼠回呼與持續輸入、routine 掛起），反對照（標題畫面 40 遊戲秒）零報警。confirmed（第 3 節）。長跑反對照見第 6 節（2 遊戲小時 × 2 種子，零報警）。
- 熱迴圈成本：診斷開與 `NoDiag` 的同行程成對量測，修剪平均比值 0.96 至 1.02（標準誤 0.006 至 0.012），閘門 1.05 通過。跨執行檔的 A/B 在這台主機上雜訊太大，量不出 5%（第 5 節）。
- 找到並處理的設計問題：dosgolem 內部的 `CD F6`（EMS trampoline）在 `EMSSeg`，不在 `StubSeg`，會被誤算成遊戲碼的服務中斷；把所有前綴都當呼叫候選會讓冷啟動 15.2% 的步數進完整分類（第 5 節）。
- 限制：診斷是 dosgolem 的觀測，不等於原版 DOS 環境下的當機；使用者的當機症狀仍未確認；T2 對迴圈內含服務中斷的卡死與等鍵盤畫面是盲的（`docs/spec/005` 第 3 節）。

## 2. 實作

| 項目 | 位置 |
|---|---|
| 規格 | `docs/spec/005-hang-diagnostics.md`（兩位審查者獨立審查，第一版退回，第三版 READY） |
| 診斷核心 | dosgolem 分支 `hr` 的 `apps/hr/runtime/diag.go`、`ovrtab.go`（由 `tools/gen_ovr_table.sh` 產生）、`session.go` 與 `crash.go` 的接線 |
| 前端 | `apps/hr/play`：Ctrl+D、Ctrl 按住不送字元、F1 說明列最近一份、`onDiag` |
| 機器人 | `apps/hr/cmd/hrbot`：`-hang-seconds`、`-hang-routine SEG:OFF`、`-hang-after-minutes`，`summary.json` 的 `t2` |
| 補丁備份 | `engine/patches/0021` 至 `0025`（0022、0023 是效能基準，0024 是診斷，0025 是前端的小修） |
| 工具 | `tools/bench.sh`（交錯 A/B）、`tools/play.sh test-diag`、`tools/play.sh test-play`、`tools/gen_ovr_table.*` |

## 3. 測試

`tools/play.sh test-diag`（容器內，原版與狀態檔唯讀掛入；缺檔的測試 skip）。`diag_test.go` 有 31 個測試，另有 `overhead_test.go`（成對量測，`HR_BENCH_OVERHEAD=1`）與前端的 `keys_test.go`（`tools/play.sh test-play`，Xvfb 內）。最後一次完整執行（`apps/hr/runtime` 全部測試）44 個通過、1 個失敗：`TestAddrClasses` 的預期值沒跟上 `EMSSeg` 的新分類，已更正並單獨重跑通過；其餘沒有失敗。主要對應：

| 承諾（規格第 10 節） | 測試 | 結果 |
|---|---|---|
| 分類函式、前綴、`66` 不分類、15 個前綴放棄 | `TestClassifyCall` | 通過 |
| 呼叫前 `SP`（含 `SP＝0`、`1`、`2` 繞回）與目標 | `TestCallEventTargetAndSP` | 通過 |
| 連續相同合併、交替不合併、第二結構 | `TestCallRingMergesOnlyConsecutive` | 通過 |
| `int 3Fh` stub 解碼、檔名、`StubSeg` 內的中斷不計 | `TestIntRecordingFilenameAndStub` | 通過 |
| `CS＝SS` 的返回位址 | `TestIntFromStackStubRecordsReturn` | 通過 |
| tick 不產生幻影呼叫 | `TestNoPhantomCallsOnTick` | 通過 |
| `intCount[0x33]` ＝ `DOS.Mouse.Calls` 總和 | `TestIntCountMatchesMouseCalls` | 通過 |
| EMS 的 `CD F6` 不計（遊玩路徑上 `int 67h` ×7、`int F6h` ×0） | `TestInternalTrampolinesNotCounted` | 通過 |
| 註記表 17 個入口前 8 bytes 與 IDA 位址換算 | `TestKnownRoutinesTable` | 通過 |
| `ovrtab` 139 筆、互異、起點 `CD 3F`、補丁開關相同 | `TestOvrTable` | 通過 |
| 位址分類（補丁開關各一組） | `TestAddrClasses` | 通過 |
| overlay 判定的兩個算式一致（戰鬥佈陣狀態檔） | `TestOverlayClassificationOnState` | 通過 |
| `NoDiag` 與診斷開的狀態摘要相同（30,000,000 步） | `TestDiagDoesNotChangeMachineState` | 通過 |
| T2 正對照 A：`jmp $`（IF＝1），取樣第一名是該位址、次數 3500 至 4096、不重複 | `TestT2JmpSelf` | 通過 |
| T2 正對照 B：`cli; jmp $`（IF＝0） | `TestT2CliJmpSelf` | 通過 |
| T2 正對照 C：卡在 ISR 內（`int 21h` 向量指向 `cli; jmp $`） | `TestT2StuckInISR` | 通過 |
| T2 正對照 D：已登記 `AX＝0Ch` 滑鼠處理常式且持續輸入，仍觸發（處理常式確實被呼叫過） | `TestT2StillFiresWithMouseHandlerAndInput` | 通過 |
| T2 反對照：標題畫面 40 遊戲秒零報警，`HangEvals ＞ 0` | `TestT2NoFalseAlarmAtTitle` | 通過 |
| `HangSeconds＝0` 不觸發；次數上限 3 | `TestT2DisabledAndCap` | 通過 |
| `adapt` 降速中途不提早報警 | `TestT2AdaptLoweringDoesNotFireEarly` | 通過 |
| 載入狀態檔後步數不連續不誤報 | `TestT2StepDiscontinuityAfterStateLoad` | 通過 |
| T3 手動、5 秒間隔、同一秒的 `-manual-02` | `TestT3ManualAndRateLimit` | 通過 |
| routine 掛起：`20C2:25A1`，呼叫處 `1A8D:0027`（返回位址 `1A8D:002C`） | `TestRoutineHangGMAP` | 通過 |
| 呼叫計數與 `probe -call-args` 的獨立交叉檢查（各 10 次） | `TestCallCountsMatchProbe` | 通過，進入計數 10 與 10 |
| `-stklen 1024` 溢位後的診斷與垃圾 `BP` 鏈 | `TestStackOverflowDiagWithGarbageBP` | 通過 |
| 寫檔失敗不停機、`OnDiag` 不被通知 | `TestDiagWriteFailureDoesNotStopGame` | 通過 |
| 保留清理只刪符合條件的目錄（符號連結、缺標記、T1 現場、名稱不符都保留） | `TestPruneDiagDirs` | 通過 |
| `RequestDiag` 與 `OnDiag` 無資料競爭 | `TestRequestDiagConcurrent`（`HR_RACE=1`，`-race`） | 通過 |
| `info.txt` 的區段與標記、T1 路徑含新區段 | `TestCrashDumpHasDiagSections` 與 `hasInfoSections` | 通過 |
| 穩態 `stepBatch` 零配置 | `TestStepBatchSteadyStateNoAllocs` | 通過 |
| Ctrl 按住與 F1 說明開著不送鍵；`lastDiag` 顯示 | `TestSendKeysToGame`、`TestLastDiagName`（前端） | 通過 |
| 前端端對端：Xvfb 內啟動視窗、點新遊戲、按住 Ctrl 再按 D | `tools/play.sh gui-diag` | `crash/20261003-121136-manual/` 出現（`info.txt` 原因「手動：Ctrl+D」、`screen.png`、`state.state`），`play.log` 記一行 `diag`，F1 說明列出 `last diagnostics: 20261003-121136-manual`（`workplace/out/gui-diag-help.png`）。xdotool 的瞬間按放（約 12 毫秒）在負載高時會被 60 TPS 的輪詢漏掉，所以腳本拉長按住時間 |

獨立交叉檢查的原始輸出：`docs/re/data/017-probe-call-args.txt`（`probe -load-state soak-s0/ck-001500000000.state`，窗口 1,500,000,000 至 1,503,000,000 步：`1D11:000A` 與 `1D29:000E` 各被呼叫 10 次）。進入計數（以 `call` 的目標計）與 `probe`（以步前 `CS:IP` 等於入口計）在這個窗口一致。

## 4. 模擬：routine 進入後不返回

命令（容器內，原版唯讀掛入，機器人在遊戲開始 1 遊戲分鐘後，於第一個輪詢點把 `1F69:000E` 的入口兩個位元組改成 `EB FE`）：

```text
tools/bot.sh run hang-demo2 -game-hours 0.15 -seed 1 -hang-routine 1F69:000E -hang-after-minutes 1
```

`1F69:000E`（IDA `2E59:000E`）在 `docs/re/009` 第 3 節標 confirmed：把 VRAM 矩形存到記憶體（游標與備份池用）。機器人輸出一行 `診斷：…/diag/20261003-115956-hang（hang：服務中斷靜默超過 30 遊戲秒）`，之後機器人自己的凍結偵測也判為凍結（`frozen`，這一輪結束在遊戲時間 0.20 小時），兩個偵測器各自獨立報警。節錄見 `docs/re/data/017-hang-sample-info.txt`，重點如下：

| 欄位 | 內容 | 怎麼讀 |
|---|---|---|
| 原因 | `hang：服務中斷靜默超過 30 遊戲秒` | T2 觸發 |
| 本道指令 | `1F69:000E（常駐，IDA 2E59:000E） [把 VRAM 矩形存到記憶體]`，位元組 `EB FE 00 00 56 57 1E 06 …` | 停在那個 routine 的入口。原本是 `C8 00 00 00 56 57 1E 06`（`enter 0,0`、`push si; push di; push ds; push es`），前兩個位元組被改成 `EB FE`（`jmp $`） |
| 呼叫鏈 | `#0 返回 19FB:0102`、`#1 19FB:0254`、`#2 15A7:00BF`、`#3 148B:02C1`、`#4 6899:0247（overlay ovr373，IDA 6DB5:0247，stub+10h 交叉一致）`、`#5 5EDB:0A4E（overlay ovr368，IDA 669D:0A4E，交叉一致）`、`#6 1440:0078`、`#7 0A85:0236`、`#8 0110:012E` | 沿 `BP` 鏈由內向外，第 4、5 層在 overlay，已換算成 IDA 的 `ovrNNN` 位址 |
| 最後一次呼叫的目標 | `1F69:000E`，上一筆是 `1F69:0169 [從保存區寫回原位置]` | 最近的呼叫是進入這個 routine，之前剛呼叫過 `1F69:0169`（強推論：`docs/re/009` 把這兩個 routine 描述成游標背景的還原與保存，所以這是游標的重畫） |
| 最後一次呼叫的呼叫處 | `19FB:07BF（IDA 28EB:07BF）`，呼叫前 `SP ＝ 7CFC`，接在 `19FB:07A2` 呼叫 `1F69:0169` 之後 | 要查是哪一段程式造成：看 IDA 的 `28EB:07BF` |
| 取樣 | `4096 次  1F69:000E` | 4096 道指令全在這個位址，確認是無限迴圈 |
| 時間 | 距最後一次服務中斷與最後一次滑鼠輪詢各 163,864,736 步（約 30.0 遊戲秒），`DOS.Blocked ＝ false` | 沒有在等鍵盤，是自己卡住 |
| 服務中斷 | `int 21h ×168169`、`int 33h ×40410`、`int 3Fh ×5`、`int 10h ×13`、`int 67h ×7`（沒有 `int F6h`） | 累計；最後 16 筆含完整 `AX` 與呼叫處，`int 33h` 來自堆疊 stub，返回位址 `0110:27DF`（IDA `1000:27DF`） |
| 最近開啟的檔名 | `scout.mid`、`GMAP.PXS`、`MAP05.PXZ`、`exist.mrg`、`spoint.mrg`、`FACE.MRG`、`ESPMES.MRG`、`national.mid` | 卡住之前遊戲在載入哪些資源 |

說明：

- 最後一次呼叫的呼叫處是 `19FB:07BF`，不是 `19FB:07A2`：後者呼叫的是 `1F69:0169`，已返回；沒有 `RET` 追蹤，所以診斷把這個欄位稱為「最後一次呼叫的目標（可能已返回）」，這次它剛好等於目前所在的 routine，因為卡住就發生在進入它的那一刻。
- 診斷落在 `diag/<時間>-hang/`：`info.txt`、`screen.png`、`state.state`（約 330 KB），狀態檔可用 `hrhd` 或探針載入重現。這些是原版內容的衍生物，不進版控。
- 機器人的 `summary.json` 含 `t2`：`enabled`、`hang_seconds`、`evals`、`max_silent_sec`、`dumps`。

## 5. 效能

### 5.1 量法的演進

| 階段 | 做法 | 結果 |
|---|---|---|
| 初版 | 每步在執行後讀 `Op()`、位址、記憶體、查表，所有前綴都當呼叫候選 | 冷啟動 20,000,000 步中 15.2%（3,043,843 次）進完整分類，但真正的呼叫事件只有 165,959 筆（每步 0.0083）。區段覆蓋前綴與 `rep` 在繪圖迴圈很常見 |
| 改良 | 執行前順手讀起點位元組（`a` 本來就算好了）；呼叫候選，或前綴加其後一個位元組是呼叫候選，才進完整分類；`NoDiag` 與取樣用不同的分類表，不另設分支 | 進完整分類降到 1.4%（277,602 次），呼叫事件數不變（165,959 筆）。每步密度：服務中斷 0.00047、呼叫事件 0.0083 |
| 量測 | 跨執行檔 A/B（`tools/bench.sh`，交錯 5 次） | 主機負載平均 30 至 46（14 核，另有其他專案的行程）。同一個 A 執行檔相鄰兩次的使用者 CPU 時間相差約 2 至 2.5 倍（例：`battle` 場景 5.99 秒與 15.2 秒），B/A 的比值落在 0.90 至 2.23。A 對 A 的對照（同一個執行檔的兩份，交錯 3 次）B/A 也落在 0.72 至 1.25（`cold-hdhooks` 1.247、`battle-hdhooks` 1.116、`cold` 0.724、`battle` 1.001）。量不出 5% |
| 量測 | 同行程成對量測（`TestDiagOverheadPaired`）：診斷開與 `NoDiag` 兩個 `Session` 交錯各跑 10⁶ 步，150 對，取修剪平均 | 見下表 |

### 5.2 同行程成對量測（改良後）

| 場景 | 診斷開 ÷ NoDiag（修剪平均 ± 標準誤） | 中位數 | 閘門 1.05 |
|---|---|---|---|
| `cold` | 0.993 ± 0.011 | 0.998 | 通過 |
| `cold-hdhooks` | 1.006 ± 0.006 | 1.007 | 通過 |
| `battle`（戰鬥佈陣，`n00071.state` 加點擊 (16,56)） | 0.964 ± 0.012 | 0.947 | 通過 |
| `battle-hdhooks` | 1.015 ± 0.009 | 1.015 | 通過 |

解讀：診斷路徑相對於 `NoDiag` 的額外成本在量測誤差內（約 ±2%），低於閘門。`NoDiag` 仍保留每步一次「讀位元組、查表、比較」，這一小段相對於基準提交（A）的成本沒有被這個量測涵蓋；跨執行檔的對照量不準，預期低於 2%（每步 3 至 5 道機器指令對每步約 25 至 150 ns），沒有可靠的實測值。

## 6. 長跑反對照（T2 零報警）

長跑反對照（`docs/spec/005` 第 10 節）：2 遊戲小時、種子 1 與 2，與正對照同一個 `hrbot`、`-hang-seconds 30`，指令 `tools/bot.sh run diag-long-s1`、`diag-long-s2`，2026-10-03 約 20:00 起跑，21:09 結束（容器 `hr-bot-diag-long-s{1,2}`）。輸出在 `workplace/out/bot/diag-long-s{1,2}/`（gitignore），下表取自各自的 `summary.json`（SHA-256 `4be96fc3b77efdcc0d08705bc2bf96c230f36e246f9507d3cadf3dbfaed280fa`、`9f14c9c405f3f8033cd535a4ac998f395e90b93a0857f2b9b3b8fd640ff9a4d6`）。

| 項目 | 種子 1 | 種子 2 |
|---|---:|---:|
| 狀態 | completed | completed |
| 遊戲時間（小時） | 2.00 | 2.00 |
| 牆鐘（秒） | 3831 | 3625 |
| 動作數 | 2723 | 2705 |
| 重開、結束遊戲 | 2、1 | 2、1 |
| 不同畫面 | 175 | 194 |
| 最低 SP | 781E | 7744 |
| 疑似凍結 | 0 | 0 |
| T2 `enabled` | true | true |
| T2 `evals` | 19,216,485 | 19,221,452 |
| T2 `max_silent_sec` | 3.55 | 3.66 |
| T2 `dumps` | 0 | 0 |

結論（confirmed，限於這兩組輸入、2 遊戲小時、修補後的 32 KB 堆疊、無聲音掛鉤）：T2 在長時間遊玩中零報警，最長的服務中斷靜默只有 3.66 遊戲秒，離 30 遊戲秒門檻有 8 倍餘裕。沒驗的維度：原版 4 KB 堆疊、更長時間、其他種子、帶聲音掛鉤的路徑（`docs/spec/007`）、真人操作。

另一個副產品：同一份 `summary.json` 的 `file_opens` 顯示無聲音驅動時 MID 被反覆開檔，種子 1 的 2 遊戲小時內 `NATIONAL.MID` 開了 263,768 次、`DANCER.MID` 48,547 次（`docs/re/010` 第 4.2 節的重載節拍），這是 `docs/spec/007` 要消除的 I/O。

## 7. 已知限制

- 主環是最近 1024 筆原始事件，只涵蓋最後約 0.02 遊戲秒（模擬那份：最早一筆在步數 337,511,405，最後一筆在 337,625,289，約 113,884 步）。不合併重複的多筆循環。更早的 routine 靠「最近不同的呼叫目標」（直接對映，雜湊衝突時覆蓋）。
- 沒有 `RET` 追蹤，呼叫鏈沿 `BP` 鏈（near 框的 `[BP＋4]` 會讀到引數，標 `?`）。
- 熱迴圈只認單一前綴後的呼叫（兩個以上前綴連用後接呼叫會漏）；原版有沒有這種指令沒有普查。tick 命中那一步，若原指令不是候選而 ISR 的第一道是 `call`，該呼叫漏記。
- T2 的盲點：迴圈裡含服務中斷的卡死、等鍵盤畫面（`int 21h/AH＝08` 以 `Rewind` 每步重跑）、門檻內解除的等待迴圈。遊戲等一個前端送不進去的按鍵時，使用者可能描述成「凍結」，T2 看不到，要靠 Ctrl+D。
- 診斷在 dosgolem 內觀測；原版 DOS 環境下的當機不一定同樣出現。使用者的當機症狀（凍結、花屏、回到 DOS、重開）與場景仍未確認。
- 前端與機器人的 Ctrl+D、診斷目錄在 Linux（Xvfb 內測試）驗過；Windows 與 macOS 沒有實機驗證。前端的新功能尚未重建發行包（`v0.1.1-hd` 不含）。
