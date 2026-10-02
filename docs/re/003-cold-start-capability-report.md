# 003 冷啟動能力報告（M2）

日期：2026-10-03
範圍：以 dosgolem 直接執行 `MAIN.EXE`（對應 jsdos 版 autoexec 的 `main`），記錄能跑到哪裡、缺什麼。缺口只記錄，不在本階段補。
推論等級：confirmed、強推論、假說、未知。

## 1. 環境與重跑方法

| 項目 | 內容 |
|---|---|
| dosgolem | `workplace/dosgolem`，取自 `/home/anr2/cht/dosgolem` 的已提交 commit `2f44a68ebfc54b28fb15dd4a34510b0b04a5415d`（分支 `fix/stubseg-font-collision-program-path`，2026-09-30），本地分支 `hr`，`upstream` 推送位址為 `DISABLED` |
| 建置與執行 | `golang:1.24-bookworm`，`--network none`，原版目錄唯讀掛載 |
| 輸入 | `MAIN.EXE`，SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e` |
| IDA | `ida-pro-9.4-idapython:locked-v1`，非 root，一次性資料庫 |

```text
tools/dosgolem.sh build
tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 20000000 -log-calls -seg-log
tools/ida.sh run MAIN.EXE ida_census_386.py /work/out/census386.json
```

完整探針輸出：`data/003-probe-main-cold-start.txt`。386 形式普查摘要：`data/003-main-resident-386-census.txt`。

## 2. 探針結果（confirmed）

執行 61260 道指令後停止。停止原因：`cpu: 0110:206E op 66 8B：386 子集沒有這一道（docs/spec/012）`。

| 項目 | 結果 |
|---|---|
| 載入 | 載入段 `0110`，PSP `0100` |
| DOS 服務 | 9 種：`21h` 的 `AH=35`、`4A`、`3D`、`3F`、`25`、`42`、`44`、`30`、`3E`。沒有「沒實作的服務」 |
| 記憶體調整 | `AH=4A` 四次，皆成功 |
| 中斷向量 | `int 00h` 設為 `0110:0151`，`int 3Fh` 設為 `2692:0531` |
| 檔案存取 | 程式自己開啟 `MAIN.EXE`：先讀位移 0 的 5 與 20 bytes，位移 361856（`FBOV` 區起點）讀 16 bytes，關閉，重開後位移 361872 讀 50896 bytes 到 `55C3:0000` |
| 找不到的檔 | `C:\PROG.EXE`（`AH=3D` 的第一次嘗試），隨後以 `main.exe` 開啟成功 |
| 視訊與輸入 | 視訊仍是文字模式 `03h`，沒有畫面輸出。計時器與鍵盤中斷送出 0 次（探針沒有注入輸入） |

強推論：`int 3Fh` 向量與位移 361872 的讀取是 Borland overlay manager 在初始化並載入第一個 overlay 區塊。`FBOV` 區位移 361856 起，標頭 16 bytes，其後的 overlay 內容從位移 361872 開始，與 `001-source-intake.md` 第 5 節的算術一致。

停在 `0110:206E`，不是 DOS 服務缺口，是 CPU 缺口。

## 3. 缺口一：CPU 的 386 指令（confirmed）

`MAIN.EXE` 是 16 位元 real mode 程式，但含少量 386 指令。dosgolem 的 `internal/cpu` 只有 DOSJP 用的最小子集（`docs/spec/012-cpu-386-subset`，只支援六道 EAX 相關指令），`internal/cpu386` 是 DOS/4GW 平坦模式用的另一套，兩者都不適用。

IDA 對常駐映像（載入段 `0110`，510 個段落（常駐 232、stub 139、overlay 139）、1968 個函式、116749 個 code head）的普查：全部指令中只有 22 條帶 386 形式，共 14 種（含無前綴的 `8C`／`8E` FS、GS 段暫存器移動，完整清單見 `data/003-main-resident-386-census.txt`）：

| 次數 | 形式 | 範例（IDA 位址） | 指令 |
|---:|---|---|---|
| 3 | `66 8B` | `1000:206E` | `mov edx, esp` |
| 3 | `66 9C` | `1000:2074` | `pushfd` |
| 3 | `66 58` | `1000:2076` | `pop eax` |
| 2 | `66 9D` | `1000:2083` | `popfd` |
| 2 | `66 61` | `1000:7044` | `popad` |
| 1 | `66 35` | `1000:207B` | `xor eax, 40000h` |
| 1 | `66 50` | `1000:2081` | `push eax` |
| 1 | `66 33` | `1000:2089` | `xor eax, ecx` |
| 1 | `66 60` | `1000:7029` | `pushad` |
| 1 | `66 C1 /5` | `1000:70BA` | `shr eax, 10h` |
| 1 | `0F A9` | `1000:73E4` | `pop gs` |
| 1 | `0F A1` | `1000:73E6` | `pop fs` |
| 1 | `8C /4` | `1000:70CF` | `mov [bp+var_C2], fs` |
| 1 | `8C /5` | `1000:70D9` | `mov [bp+var_C6], gs` |

IDA 位址與 dosgolem 執行期位址的換算：`IDA 段 = 執行期段 + 0xEF0`，偏移相同（執行期 `0110:206E` 即 IDA `1000:206E`）。

用途（強推論，依反組譯上下文）：

- `1000:2042` 起是 Borland C++ 執行期的 CPU 型號偵測：依序測 `FLAGS` 高 4 位元（8086）、`FLAGS` 位元 12 至 15（286）、`EFLAGS` 的 AC 位元 18（386 對 486 以上），結果寫入資料段的 `word_63694`，值為 0（8086）、2（286）、3（386）、4（486 以上）。IDA 在該處加註 `BCC v4.x/5.x DOS runtime`。
- `1000:7010` 起的函式在 `word_63694 >= 3` 時走 386 路徑：`pushad`、複製 32 bytes 暫存器區、`popad`、`pushfd` 後取高 16 位元（`shr eax, 10h`）。`1000:73E4` 起以 `pop gs`、`pop fs`、`pop es`、`pop ds`、`popad`、`popfd`、`retf` 還原現場。用途未驗證；IDA 的 FLIRT 把該函式標為 `_RaiseException`（導覽名，不是證據）。
- 偵測結果決定走哪條路徑。AC 位元可寫（值 4）或不可寫（值 3）是 M3 要決定的 CPU 模型選擇；jsdos 設定 `cputype=auto` 在原版執行時對應哪一種，未驗證，要在 M3 以兩側收據比對。

說明：IDA 9.4 的 DOS loader 預設就載入 `FBOV` overlay（139 段，`docs/re/007` 第 9 節），上表因此涵蓋整個程式；overlay 內的 386 形式為 0。普查只涵蓋 IDA 判定為 code 的位址。

## 4. overlay 區

- `MAIN.EXE` 的程式碼大部分在 `FBOV` 區，結構已解（`docs/re/007`）：139 段 overlay，每段有 stub 與入口，初始化預載其中 122 段（共 50896 bytes，即探針讀到的位元組數）。
- 探針只跑到第一個 CPU 缺口，沒有走到之後的 `int 3Fh`。dosgolem 規格庫沒有 Borland overlay manager 的專屬規格（`AGENTS.md` 第 3 節記錄搜尋方式與結果）；overlay manager 只用 DOS 檔案與記憶體服務，後續實跑收據見 `docs/re/008`。

## 5. 還沒量到（未知）

- 視訊模式與解析度（已量到，見 `docs/re/006`、`docs/re/008`）。
- 鍵盤、滑鼠、計時器、Sound Blaster 與 MIDI 的使用（滑鼠與視訊見 `docs/re/007` 第 9 節）。
- `SIG.COM` 是否被 `MAIN.EXE` 依賴。
- 缺檔（`CTMIDI.DRV`、`DISK_D.INF`）的影響。
- `HR.BAT` 完整啟動鏈（`PSH`、`OP`、`END`）在 dosgolem 下的行為。

## 6. 對 M3 的結論

M3 的第一步是補 `MAIN.EXE` 常駐段用到的 14 種 386 形式（規格 `docs/spec/001-cpu-386-real-mode-forms`）。範圍小，且每一種都有位元組與上下文證據，可以直接寫成 DRAFT 規格再審查。補完後重跑探針，會推進到下一個缺口，通常是 overlay 區載入之後的行為或視訊與輸入服務。
