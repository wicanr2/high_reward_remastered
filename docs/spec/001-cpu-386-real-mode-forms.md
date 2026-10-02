# 001 CPU：real mode 的 386 指令形式

狀態：READY（第三版。第一輪審查 6 項阻擋、第二輪 4 項阻擋皆已修正，剩餘為文字層級修訂；審查紀錄見 `WORKLOG.md`）
日期：2026-10-03
前置：dosgolem `docs/spec/002-cpu-8086`（CPU 驗收準則）、`docs/spec/012-cpu-386-subset`（現有的 EAX 最小子集）；本專案 `docs/re/003-cold-start-capability-report`
實作位置：`workplace/dosgolem` 的 `internal/cpu` 及其呼叫端（本地分支 `hr`）

## 1. 為什麼要做

dosgolem 跑 `MAIN.EXE` 到第 61260 道指令時停在 `0110:206E`，原因是 `66 8B`（`mov edx, esp`）不在現有 386 子集內（`docs/re/003` 第 2 節）。`MAIN.EXE` 是 16 位元 real mode 程式，Borland C++ 執行期含少量 386 指令。現有子集只認 EAX 與六道 DOSJP 專用指令，EBX 以下的暫存器高半部不存在，也沒有 FS、GS。

## 2. 輸入、工具與位址空間

| 項目 | 內容 |
|---|---|
| 被分析的程式 | `MAIN.EXE`，SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e` |
| 反組譯 | IDA Pro 9.4，映像 `ida-pro-9.4-idapython:locked-v1`，非 root，對一次性資料庫執行 |
| 普查命令 | `tools/ida.sh run MAIN.EXE ida_census_386.py /work/out/census386.json`，完整輸出 `docs/re/data/003-main-resident-386-census.txt` |
| 位址空間 | IDA 選擇子 : 偏移。執行期段 = IDA 段 − 0xEF0（載入段 `0110` 對應 IDA `1000`），偏移相同。只涵蓋常駐映像 |
| 驗收語料 | `SingleStepTests/80386`，目錄 `v1_ex_real_mode`，真實 Intel 386EX 產生；固定 commit `459d49fbe6280e9ed46fee887b58dacd9cb880ab`（2026-08-09），各檔 SHA-256 見 `docs/re/data/005-sst386-corpus-manifest.txt`；revocation 清單目前一筆（SHA-1 `8abbbc61a5866292b0bc816660d7b334bea7962a`） |
| 既有基準 | `SingleStepTests/8088` v2（323 檔），`tools/fetch_sst8088.sh` 抓到 `workplace/dosgolem/testdata/8088`；取得時的 `main` HEAD 與各檔 SHA-256 記在 `docs/re/data/005-sst8088-manifest.txt` |

## 3. 範圍

### 3.1 納入的形式

證據等級：confirmed ＝ 普查在 `MAIN.EXE` 常駐映像由 IDA 解出該指令；泛化 ＝ 普查只命中其中一種運算元組合，其餘由語料驗收；完整性 ＝ 與已命中的形式同屬一個暫存器或指令族，普查沒有命中，只為避免只做一半，沒有 `MAIN.EXE` 的證據。

| 形式 | 指令 | IDA 位址（普查命中） | 等級 |
|---|---|---|---|
| `66 8B /r` | `mov r32, r/m32` | `1000:206E`（`edx, esp`）、`2078`（`ecx, eax`）、`2092`（`esp, edx`） | confirmed（暫存器對暫存器）；記憶體運算元泛化 |
| `66 9C` | `pushfd` | `1000:2074`、`2085`、`70B6` | confirmed |
| `66 9D` | `popfd` | `1000:2083`、`73EC` | confirmed |
| `66 50+r` | `push r32` | `1000:2081`（`eax`） | confirmed（EAX）；其餘暫存器泛化 |
| `66 58+r` | `pop r32` | `1000:2076`、`2087`、`70B8`（`eax`） | confirmed（EAX）；其餘暫存器泛化 |
| `66 33 /r` | `xor r32, r/m32` | `1000:2089`（`eax, ecx`） | confirmed（暫存器對暫存器）；記憶體運算元泛化 |
| `66 35 id` | `xor eax, imm32` | `1000:207B` | confirmed |
| `66 C1 /5 ib` | `shr r/m32, imm8` | `1000:70BA`（`eax, 10h`） | confirmed（EAX）；其餘運算元泛化 |
| `66 60` | `pushad` | `1000:7029` | confirmed |
| `66 61` | `popad` | `1000:7044`、`73EA` | confirmed |
| `0F A1` | `pop fs` | `1000:73E6` | confirmed |
| `0F A9` | `pop gs` | `1000:73E4` | confirmed |
| `8C /4`、`8C /5` | `mov r/m16, fs`、`mov r/m16, gs` | `1000:70CF`（`[bp+var_C2], fs`）、`70D9`（`[bp+var_C6], gs`） | confirmed |
| `0F A0`、`0F A8` | `push fs`、`push gs` | 無 | 完整性 |
| `8E /4`、`8E /5` | `mov fs, r/m16`、`mov gs, r/m16` | 無 | 完整性 |
| `64`、`65` 前綴 | FS、GS 段覆寫 | 無（常駐映像沒有 FS/GS 前綴的指令） | 完整性；語料的 `668B`、`6633`、`66C1.5` 測試含這兩個前綴，必須做 |

普查共 14 種形式、22 條指令（`docs/re/data/003-main-resident-386-census.txt`）。限制：普查只涵蓋 IDA 判定為 code 的位址，標成資料的區域不在內。

### 3.2 不納入

- `0x67` 位址大小前綴與 SIB 定址。普查在常駐映像沒有命中。
- 上表以外的 32 位元 ALU、乘除、位元運算、字串指令。
- 保護模式、分頁、除錯暫存器、x87、例外（`#GP`、`#SS`、`#UD`）。
- `FBOV` overlay 區的指令。overlay 內容尚未載入 IDA，是否有其他 386 形式未知；探針遇到時會停在新缺口，屆時增補本規格。

## 4. 語意

語意以語料為準。下列是預期行為，語料與本節衝突時以語料為準，並把本節改成語料的行為。

1. 暫存器：EAX 至 EDI 各有高 16 位元（`Hi`）。16 位元寫入不動高半部；32 位元寫入同時寫低半與高半。現有 `EAXHi` 欄位併入 `Hi`。
2. 段暫存器：新增 `FS`、`GS`，與 ES、DS 同樣存 16 位元值，段基底為 `段 × 16`。索引依 x86 的段暫存器編碼：ES=0、CS=1、SS=2、DS=3、FS=4、GS=5。`64`、`65` 前綴在 `Model80386` 下設定本道指令的段覆寫為 FS、GS，行為與 `26`、`2E`、`36`、`3E` 相同。
3. `0F` 位元組：在 `Model80386` 下是雙位元組 opcode 的跳脫位元組，不再是 8086 的 `POP CS`。只支援 §3.1 列出的 `0F A0`、`A1`、`A8`、`A9`，其餘 `0F xx` 回傳「未實作」錯誤（失敗即關閉）。
4. 運算元大小前綴 `66`：在 `Model80386` 且 16 位元碼段下，把本道指令的運算元寬度改為 32 位元。
5. 堆疊：`push r32`、`pop r32`、`pushfd`、`popfd`、`pushad`、`popad` 每格 4 bytes，`SP`（16 位元）以 4 遞減或遞增，位移各自在 16 位元內計算。`push esp` 推入的是指令執行前的 ESP；`pop esp` 的結果是彈出的值（覆蓋遞增後的 ESP）。
6. `pushad`：依序推入 EAX、ECX、EDX、EBX、指令執行前的 ESP（完整 32 位元，含高半）、EBP、ESI、EDI，`SP` 共減 32。`popad`：反向彈出，ESP 那一格丟棄，不動 ESP 的高半。
7. EFLAGS：
   - 語料的 INIT 與 FINA 的 `eflags` 位元 18 至 31 恆為 1（1000 筆 `669C` 中 979 筆非例外測試全為 `0xFFFC`，`669D` 的 FINA 同為 `0xFFFC`），與指令及彈出值都無關。這是 SMM 傾印的假象，不是 CPU 行為。
   - 因此 CPU 模型只保存低 16 位元（`Flags`，`Model80386` 的固定位元沿用 `SetFlags`：位元 1 恆為 1，位元 3、5、15 恆為 0，位元 12 至 14 可寫）。`pushfd` 推入 `uint32(Flags)`，位元 16 至 31 為 0（語料 `669C` 推入的 4 個位元組，高兩個皆為 0）。`popfd` 以彈出值的低 16 位元寫入 `Flags`，位元 16 至 31 忽略。
   - harness 載入 `eflags` 只取低 16 位元，比對只看位元 0 至 17（RF、VM 在語料恆為 0），這是唯一的 harness 自加遮罩，明文在此。其餘遮罩一律只用語料附的 `RM32`。
   - AC（位元 18）不可寫：語料 `669D` 的彈出值取自測試的隨機記憶體內容，FINA 的位元 18 恆為 1，不隨彈出值改變。這個行為決定 `MAIN.EXE` 的 CPU 型號偵測（`word_63694`）得到 3（386）而不是 4。語料的直接證據只到「popfd 不改變傾印的位元 18」，將它解讀為「CPU 沒有 AC」屬強推論。
8. `xor`、`shr`（32 位元）：結果與旗標依 386 定義。`xor`：CF＝OF＝0，SF、ZF、PF 依結果。`shr`：移位數先遮成 5 位元；移位數為 0 時旗標不變；CF 為最後移出的位元；SF、ZF、PF 依結果；OF 只在移位數為 1 時有定義；AF 未定義。未定義的旗標位元由語料的 `RM32` 遮罩處理，實作不得為了通過而自行遮罩。32 位元的移位與 ALU 是新程式碼，現有 `shiftRotate`、`aluCore` 只有 16 位元。
9. `mov r32, r/m32`：`r/m` 為記憶體時用 16 位元定址模式，讀 4 bytes。
10. `8C /r`：`reg` 為 4、5 時取出 FS、GS 的 16 位元值，`r/m` 為暫存器時只寫低 16 位元（不加 `66` 前綴的形式）；`8E /r` 反向。`reg` 為 6、7 以及 `8E /1`（寫 CS）在 386 是 `#UD`，語料以 EXCP 呈現，不在本規格處理。

## 5. 對現有程式的影響

這些位置都會被動到，實作要逐一處理並有測試：

| 位置 | 變更 |
|---|---|
| `internal/cpu/cpu.go` | `Seg [4]uint16` 改 `[6]uint16`（讓所有按值複製的呼叫端編譯失敗，逼逐一處理）；新增 `FS`、`GS` 常數；`Hi [8]uint16` 取代 `EAXHi`；`Reset` |
| `internal/cpu/ops.go` | `Step` 增加 `0x64`、`0x65` 前綴；`execute` 在 `Model80386` 下 `0x0F` 走雙位元組分派；`8C`／`8E` 在 `Model80386` 下接受 `reg` 4、5（現有 `reg&3` 會把 4、5 當成 ES、CS） |
| `internal/cpu/ops386.go` | 泛化現有只認 EAX 的實作（`setOperand32` 遇非 AX 目前會 panic，`66 C1` 只接受 `SHL EAX`）；保住 `docs/spec/012` 的六道 DOSJP 指令行為 |
| `internal/machine/le_startup.go`（第 461 至 481 行）、`dpmi_real_mode.go`（第 133、181 行）、`ops386_test.go` | 引用 `EAXHi` 的地方改用 `Hi[AX]`。這兩處只搬運低半暫存器與 EAX 的高半，其他暫存器的高半與 FS、GS 不跨越這條路徑，維持現狀 |
| `internal/machine/snapshot.go`（`segs`）、`callback.go`（`segs`）、`internal/dos/exec.go`（`procFrame.seg`，存於第 132 行、還原於第 304 行） | 記憶體內結構：`segs [6]uint16`，新增 `hi [8]uint16`，存與還原時一併處理 |
| `internal/machine/state.go`、`internal/dos/state.go` | 線上格式（gob）：保留 `Seg [4]uint16`（ES、CS、SS、DS，gob 對陣列長度不同會報錯，所以不能改長度），另加 `FS`、`GS uint16` 與 `Hi [8]uint16`（gob 對缺少的欄位補 0）。`stateVersion` 與 `dosStateVersion` 由 2 升為 3，載入時接受 2 與 3（現有程式嚴格比對版本，要放寬），讀到 v2 時新增欄位為 0。`dos/state.go` 的 `procState` 同樣處理 |
| `internal/machine/machine.go`（第 511 行）、`dpmi_real_mode.go`（第 126 行，DPMI 實模式呼叫用的 CPU）、測試 `le_real_mode_files_test.go`、`le_dma_clock_test.go`、`pushsp_test.go` | 設定 `Model80386` 的位置。`docs/spec/012` 宣稱「升 model 的唯一影響是 0x66 不再報錯」，本規格擴大了影響面（`0F`、`64`、`65`、`8C`／`8E`），這些使用點與 012 都要檢查並同步修訂；迴歸跑 `go test ./...` |
| `internal/dos/dos_test.go`（第 434 至 446 行）、`internal/machine/mouse_contract_test.go`（第 165 至 180 行） | 這兩處比對回呼前後的 `R`、`Seg`、`Flags`，要補上 `Hi`、`FS`、`GS` |
| `tools/go.sh`（dosgolem 副本，第 31 行的環境變數轉交清單） | 加入 `DOSGOLEM_SST386`、`DOSGOLEM_SST386_REQUIRE`、`DOSGOLEM_SST386_ONLY`，否則容器內設不到（`REQUIRE` 會失效） |

## 6. 驗收

全部條件都要成立，收據記入 `docs/re/`。

### 6.1 80386 語料

harness 在 `internal/cpu/moo_test.go`（MOO 1.1 讀檔器）與 `sst386_test.go`（`TestSST386`）。

```text
tools/fetch_sst386.sh <規格 §6.1 的檔名…>
DOSGOLEM_SST386_REQUIRE=1 tools/dosgolem.sh go test ./internal/cpu -run TestSST386 -v -count=1
```

契約：

- 載入：32 位元暫存器拆成低半（`R`）與高半（`Hi`）；段暫存器取低 16 位元；`eip` 取低 16 位元；`eflags` 取低 16 位元（§4.7）。記憶體是平坦稀疏位址空間，不做 A20 折返。
- 執行：語料每個測試是「被測指令加一道 `F4`（HLT）」，FINA 的 `eip` 落在 HLT 之後。harness 從 `CS:IP` 呼叫 `Step()` 執行被測指令（回傳錯誤算失敗），確認新的 `CS:IP` 處的位元組是 `F4`（不是就算失敗），再 `Step()` 一次並要求 `Halted` 為真，然後才比對。
- 比對：比對 EAX、EBX、ECX、EDX、ESI、EDI、EBP、ESP、六個段暫存器、`eip`、`eflags`（FINA 沒列的暫存器等於 INIT），以及 FINA 的 RAM 項目；不比 `cr0`、`cr3`、`dr6`、`dr7`；週期與匯流排不比。
- 記憶體寫入規則：寫到 INIT 與 FINA 都沒列出的位址算失敗（含寫入 0）；寫到 INIT 有列出但 FINA 沒列出的位址，值改變算失敗；讀到 INIT 沒列出的位址算失敗。
- 遮罩：只用語料的 `RM32`（檔案層級與單筆最終狀態，兩者都有時取交集）與 §4.7 的 `eflags` 規則，harness 不得另加遮罩。注意 `66C1.5` 檔層級的 `eflags` 遮罩（`0xFFFFF7EE`）把 CF、AF、OF 一併遮掉，所以 32 位元 `shr` 的 CF 與 OF 語料驗不到，由 §6.3 的單元測試補。
- 排除只有兩類，逐檔計數輸出：`excp`（測試含 `EXCP` 子區塊，硬體產生例外，本規格不做例外）；`revoked`（測試的 HASH 在語料的 `revocation_list.txt`）。
- 檔案檢查：每個檔的 `MOO ` 檔頭 CPU ID 必須是 `386E`，`META` 的 `cpu_mode` 必須是 0（real mode），測試總數必須大於 0。
- `DOSGOLEM_SST386_REQUIRE=1` 時：缺語料目錄、缺檔、缺 `revocation_list.txt` 都算失敗，且拒絕 `DOSGOLEM_SST386_ONLY` 篩選。驗收一律用此模式。`tools/go.sh` 要轉交這些環境變數（§5）。
- 通過條件：下列 30 個檔每一個都有測試被執行，且失敗數為 0；每個檔有效（未排除）測試數不少於總數的 90%（工程門檻，不是統計宣稱）。
  `668B`、`669C`、`669D`、`6650` 至 `6657`、`6658` 至 `665F`、`6633`、`6635`、`66C1.5`、`6660`、`6661`、`0FA0`、`0FA1`、`0FA8`、`0FA9`、`8C`、`8E`。
- 收據：測試輸出的 `RECEIPT` 行（每檔的總數、執行、失敗、各類排除）與 `go test` 的 `ok` 行，存 `docs/re/data/`。

### 6.2 既有基準不退化

- 抓齊 8088 語料後，`tools/dosgolem.sh go test ./internal/cpu -v -count=1` 全綠，並列出 `singlestep_test.go` 實際執行的檔案數（323 檔都要被執行，不是 skip）。
- `tools/dosgolem.sh go test ./... -count=1` 全綠；缺原版素材而 skip 的測試列出數量。

### 6.3 負對照

確認測試真的會抓到錯誤，每一項都要先做出會失敗的變體再還原：

- `pushad` 推入遞減後的 ESP：`6660` 必須失敗。
- 移除 `64`、`65` 前綴支援：`668B` 必須失敗。
- `popfd` 讓位元 18 可寫並寫入內部旗標：下列 CPU 型號偵測單元測試必須失敗。
- 單元測試（不含任何原版位元組）：以標準的偵測序列 `pushfd / pop eax / mov ecx, eax / xor eax, 40000h / push eax / popfd / pushfd / pop eax / xor eax, ecx` 執行，期望結果為 0（AC 不可寫，386）。
- 單元測試：`shr r/m32, imm8` 的 CF 與 OF（語料遮罩掉它們）。至少涵蓋：移位數 1（CF 為原 bit 0、OF 為原 bit 31）、移位數 31、移位數 32 與 33（遮成 5 位元，等於 0 與 1）、移位數 0（旗標不變）、值為 0 與 `0xFFFFFFFF`。期望值由人工依手冊逐列寫出，不以實作輸出回填。

### 6.4 快照與狀態

- 快照（記憶體內）與狀態檔來回測試：寫出再讀回，`Hi`、`FS`、`GS` 逐位元相同；`machine` 與 `dos` 兩份狀態都測。
- 版本：`stateVersion`、`dosStateVersion` 為 3；載入 v2 格式（不含新欄位）成功且新欄位為 0；版本 1 或 4 以上拒絕。
- `dos_test.go`、`mouse_contract_test.go` 的回呼前後比對包含 `Hi`、`FS`、`GS`。

### 6.5 程式層收據

固定 `-steps`，重跑 `tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -watch 54794-54795`（線性位址 `0x54794` ＝ 執行期 `540F:06A4` ＝ IDA `62FF:06A4`，即 `word_63694`）：

- `-watch` 印的寫入者位址是「指令執行完之後的 `CS:IP`」（`cmd/probe/main.go` 第 332、333 行），不是指令起點。偵測常式依序寫入 `word_63694`：`mov word_63694, 0`（起點 `2053`，印成 `0110:2059`）、`2`（起點 `2066`，印成 `0110:206C`）、`3`（起點 `208C`，六位元組，印成 `0110:2092`）。收據要顯示這三次寫入，最終值為 3，且沒有 `0110:209D`（`mov word_63694, 4`，起點 `2097`）。這證明偵測常式真的跑過，且結果不是靜態初值。
- 停止原因不是 §3.1 列出的任何形式。
- 記錄 `7029`（`pushad`）與 `73E4`（`pop gs`）所在的路徑有沒有被冷啟動走到；沒走到的形式只有語料驗收，收據要寫明。

## 7. 失敗模式

- 遇到 §3.1 以外的 386 形式：`Step()` 回傳「未實作」錯誤，不靜默放行（與 `docs/spec/012` 同）。
- 語料缺檔：預設 skip；`REQUIRE=1` 時失敗。
- 狀態檔版本：載入接受 2 與 3，其餘拒絕；v2 的新欄位為 0；寫出一律 v3。

## 8. 玩家垂直路徑與存檔影響

本規格沒有直接的玩家可見行為。它讓冷啟動越過 CPU 型號偵測，是 M3「冷啟動到片頭、主選單、進入遊戲」的第一步。存檔影響：dosgolem 的 `machine` 與 `dos` 狀態檔版本 2 升 3，v2 仍可載入（§5、§7）；遊戲自己的存檔不受影響。

## 9. 原版 oracle 與已知差異

- oracle：指令層級用硬體語料（真實 386EX）。程式層（`MAIN.EXE` 是否走對的路徑）尚無原版 oracle；jsdos 的 `cputype=auto` 對應哪種 CPU 型號未驗證。
- CPU 型號固定為 386（偵測值 3）。若 M3 的雙側收據顯示 386 與 486 以上在 `MAIN.EXE` 的行為不同，另開規格。
- 不做例外。語料的 `EXCP` 測試只計數。包含：dword 存取跨過 `0xFFFF` 位移時 386 real mode 會 `#GP` 或 `#SS`（本實作的位移各自 wrap，不處理）、`LOCK` 前綴用在不合法的指令、前綴超過長度上限。
- `0x67` 與 SIB 不支援。
- 語料是 386EX（16 位元匯流排），與 386DX 的差異只在時序，本驗收不比時序。

## 10. 停止線與權利邊界

- 本規格結束於 §3.1 的形式。overlay 區的新缺口不在這裡處理。
- 語料有自己的授權，不進本 repo、不進發行包；`docs/re/` 只收指令位址、助憶碼與位元組數，不收原版的連續反組譯或資料。測試用語料檔留在 `workplace/`。
