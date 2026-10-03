# 010 MAIN.EXE 音樂與音效子系統（DRAFT）

日期：2026-10-03
狀態：DRAFT，未經審查。
範圍：`MAIN.EXE` 的音樂（MIDI）與音效（PCM）子系統：載入條件、驅動 `ctmidi.drv` 的呼叫介面、驅動缺席時的行為、已知的停機與無限迴圈路徑、讓三平台版出聲的選項。`OP.EXE`、`END.EXE`、`CFG.EXE` 只做字串與參照層級的比對。不涵蓋 MIDI 檔內容、驅動本體（不在原版壓縮檔內）、實際音訊輸出。
推論等級：confirmed（反組譯位元組或 dosgolem 收據可重跑）、強推論、假說、未知。

## 0. 輸入、工具、位址寫法

| 項目 | 內容 |
|---|---|
| `MAIN.EXE` | SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e` |
| `OP.EXE` | `8154bb80d018210d8d96493bcdb80c44d1c0adb81419966539ae83812e79d2e2` |
| `END.EXE` | `7734e3fb0f39fb047dda0fbf39643a4874d519ba9da96ce6fb1e64b59d2b2c60` |
| `CFG.EXE` | `4201486bcb5a87862be01431c3f943973e01077dbb423750530ff112d798ea02` |
| `SOUND_E.PCM` | `8d86588cd24ec646a48f8217ce41e9ca543519376710f48371d3fbba2f3da012`（18388 bytes） |
| 靜態工具 | IDA Pro 9.4（`ida-pro-9.4-idapython:locked-v1`），`tools/ida.sh`；腳本 `tools/ida_music_strings.py`、`ida_music_query.py`、`ida_music_callargs.py`、`ida_music_allstrings.py`；輸出在 `workplace/ida-music/out/` |
| 動態工具 | `tools/dosgolem.sh probe`（`workplace/out/probe`，SHA-256 `d6aceede38b6bf027aa8d271fb60b251bd4b6bba7405cc044686b2d6ed4b8dd6`，2026-10-03 03:59 建置；`workplace/dosgolem` HEAD `96f0ab5`，`apps/hr/cmd/hrsoak/main.go` 有他人的未提交修改，與本份收據無關）。主要收據在此建置上重跑過一次，數值相同 |
| 起點狀態 | `workplace/out/soak-s0/ck-001500000000.state`（SHA-256 `b72256931dabbe56f0f5b685f8afef3f47b4702146501c99c80c9f95d5baeea9`，第 1500000000 道指令，新遊戲後的地圖畫面） |

位址寫法：`281B:02D2` 是 IDA 選擇子:偏移。常駐映像的執行期段 ＝ IDA 段 − `0x0EF0`（`docs/re/007` 第 8 節）。本份驗證了這個換算：`192B:059B` 的位元組是 `55 8B EC 81 EC 22 01 1E B8 24 3E`，對應 IDA `281B:059B` 的 `mov ax, 4D14h` 變成 `mov ax, 3E24h`（confirmed，`workplace/out/re-music/p1-peek.txt`）；`1043:21F8`、`19FB:074D`、`1F8A:00CB` 也在動態收據中以執行期位址命中。IDA 名稱（`sub_28482` 等）只用來找位置，不當證據。overlay 內的程式碼只有 IDA 位址，執行期位址依 `docs/re/007` 第 8 節換算。

IDA 的資料名稱有一處要注意：`sub_28482`（`281B:02D2`）在 `281B:0471` 之後把 DS 當成另一個段，於是出現 `word_631A8`、`word_631B6`、`word_631C2`、`byte_63224`、`byte_63230` 這類名稱。該函式從 `281B:02D9` 起 DS 一直是 `4D14`（`281B:043B` push、`047D` pop 同一個值），所以它們的實際位址是 `4D14:01B8`、`01C6`、`01D2`、`0234`、`0240`。位移相同，段不同。

## 1. 結論摘要

| # | 結論 | 等級 |
|---|---|---|
| 1 | 聲音子系統是常駐段 IDA `281B`（執行期 `192B`，長 `0x612` bytes，IDA 建出 13 個函式，其中 `0000`、`0008` 是空殼，另有 `024E` 一個沒被建成函式的空殼）加專用資料段 IDA `4D14`（執行期 `3E24`）。把 `4D14` 當立即值載入暫存器（`mov ax, seg seg082` 或 `mov dx, seg seg082`）的指令共 23 處，全在 `281B`；overlay 與其他常駐段沒有這種指令 | confirmed（IDA 立即值搜尋；經指標傳入的存取不在搜尋範圍） |
| 2 | 同一份子系統靜態連結在 `MAIN.EXE`、`OP.EXE`、`END.EXE`：三者都有同樣的字串組與同形的初始化常式（`OP.EXE` `1E63:02DA`，`END.EXE` `1FBF:02D2`） | 字串與參照 confirmed；呼叫端與行為相同：強推論 |
| 3 | 音樂路徑：遊戲把整份 `.MID` 讀進 EMS 頁框 `+0x5000`，驅動 `ctmidi.drv` 被讀進 EMS 頁框 `+0x0000` 並當作可遠呼叫的程式碼執行，命令碼放 `BX`、遠指標放 `DX:AX`。驅動的內容與它碰的硬體埠：未知 | 介面 confirmed；驅動內部未知 |
| 4 | 音效路徑與驅動無關：遊戲自己對 Sound Blaster 的 DSP、混音器與 8237 DMA 寫埠，把 `SOUND_E.PCM` 的切片以 8 kHz 單次 DMA 播出 | 指令序列 confirmed；DSP 命令語意強推論 |
| 5 | 驅動載入條件：EMS 管理員回報正常、環境變數 `SOUND` 非空、`fopen("ctmidi.drv","rb")` 成功（只用目前目錄，不搜尋路徑）、讀入至少 17000 bytes。沒有設定檔、命令列或硬體偵測參與 | confirmed |
| 6 | 全部聲音功能由 `4D14:01B8` 的旗標控制。旗標初值 0，只在載入路徑最後被設成 1（`SOUND` 值第 4 到 7 個字元是 `SB16`）或 2（其他值）。任何一個載入條件失敗，旗標維持 0 | confirmed |
| 7 | 旗標為 0 時，所有 `call dword ptr [4D14:01C2]`（驅動入口）都不會執行，沒有跳到無效位址的路徑。9 個驅動呼叫點逐一列在第 5 節 | confirmed（位元組與位置） |
| 8 | 旗標為 0 時音樂檔仍被反覆開啟：遊戲在每次滑鼠位置輪詢（約每 14.7K 到 14.8K 道指令）呼叫「重播節拍」，節拍讀驅動狀態字 `4D14:01BA` 的 bit 0，沒有驅動時它恆為 0，節拍就一直重新載入目前曲目。把該字節 bit 0 設成 1，重載立即停止（86 次降為 1 次） | confirmed（靜態加動態對照） |
| 9 | dosgolem 現況的旗標是 0，因為環境區塊只有 `COMSPEC=C:\COMMAND.COM`（`workplace/dosgolem/internal/machine/loader.go:307`，執行期 `00D0:0000` 實測相同），`SOUND` 取得 NULL，初始化在 `fopen("ctmidi.drv")` 之前就收手。這解釋了「找不到的檔清單沒有 `ctmidi.drv`」：開檔從未被嘗試 | confirmed |
| 10 | 驅動缺席或載入失敗本身不會當機。已確認會停機或卡死的路徑有三條，前提都不是「驅動缺席」：EMS 缺席、旗標不為 0 但沒有 SB DSP、驅動狀態位元卡在 1 | confirmed（靜態加注入收據） |
| 11 | `MAIN.EXE` 的 `int 67h` 共 8 處，全在 `281B`（`docs/re/004`、`007` 與本份 `int` 清單一致），EMS 在這支程式裡只服務聲音子系統：驅動映像、MID 緩衝、PCM 緩衝都在同一個 4 頁配置內。EMS 不存在時，初始化跳出口，緩衝指標維持 0:0，第一次 `PlayMusic` 就對 `0000:0000` 做 `fread`（H1，收據 E4），這是 `AGENTS.md` 第 3 節「需要 EMS」成立的原因 | confirmed（靜態加注入） |
| 12 | 讓三平台版出聲的最小作法有五個選項，第 7 節列出各自的前置證據。沒有實作 | 選項清單，無等級 |

## 2. 位址表

### 2.1 `281B` 段的常式

| IDA | 執行期 | 長度 | 導覽名稱 | 作用 | 等級 |
|---|---|---:|---|---|---|
| `281B:0000` | `192B:0000` | 8 | `sub_281B0` | `push bp; mov bp,sp; mov ax,1; pop bp; retf`，空殼。唯一呼叫點 `7D37:0DD4`（ovr380） | confirmed |
| `281B:0008` | `192B:0008` | 8 | `sub_281B8` | 同上。唯一呼叫點 `7D37:0DE0`（ovr380） | confirmed |
| `281B:0010` | `192B:0010` | 81 | `sub_281C0` | 開始播放已載入的 MID：旗標為 0 回傳 `0FFFFh`；`4D2FC`←0；混音器索引（`base+4`）寫 `26h`，資料（`base+5`）寫 `0DDh`；驅動命令 8（`DX:AX` ＝ `[4D14:01CE]:[4D14:01CC]`）再命令 9 | 位元組 confirmed；語意強推論 |
| `281B:0061` | `192B:0061` | 63 | `sub_28211` | 停止：旗標為 0 直接返回；混音器 `26h`←0；驅動命令 `0Ah`；`2BCC:0223`←`0FFh`（目前曲號清為無） | 位元組 confirmed；語意強推論 |
| `281B:00A0` | `192B:00A0` | 67 | `sub_28250` | 要求結束目前曲目：旗標 0 回傳 `0FFFFh`；旗標 1 開始淡出（`4D2FC`←1，`4D2FE`←2×引數，計時器 `0Eh`←2×引數）；旗標 2 直接呼叫 `sub_28211` | confirmed |
| `281B:00E3` | `192B:00E3` | 60 | `sub_28293` | DSP 寫入就緒等待。DX 傳入 `base+0Ch`，輪詢 bit 7 最多 256 次，就緒回傳 0。逾時則重設 DSP（`base+6` 寫 1、寫 0），再等 `base+0Eh` bit 7 與 `base+0Ah`＝`0AAh`（沒有上限），回傳 1 | 位元組 confirmed |
| `281B:011F` | `192B:011F` | 303 | `sub_282CF` | 音效播放（引數為音效編號）：旗標為 0 回傳 `0FFFFh`；以 8237 DMA 與 DSP 播 `SOUND_E.PCM` 切片，見第 3.5 節 | 位元組 confirmed |
| `281B:024E` | `192B:024E` | 8 | 無 | 同 `281B:0000` 的空殼，沒有呼叫者 | confirmed |
| `281B:0256` | `192B:0256` | 30 | `sub_28406` | `4D30C:4D30E` 複製到 `4D2F4:4D2F6`，回傳 `DX:AX`（初始化各出口都會呼叫） | confirmed |
| `281B:0274` | `192B:0274` | 94 | `sub_28424` | 淡出節拍與狀態查詢，回傳 `4D14:01BA & 1`，第 3.2 節 | confirmed |
| `281B:02D2` | `192B:02D2` | 533 | `sub_28482` | 初始化，第 3.1 節。由 `_main`（`1975:000F`）在 `1975:0036`（執行期 `0A85:0036`）呼叫一次 | confirmed |
| `281B:04E7` | `192B:04E7` | 42 | `sub_28697` | 結束：旗標不為 0 時送驅動命令 4；不論旗標，之後都釋放 EMS 控制代碼（`AX=4500h`，`DX`＝`4D14:01C6`） | confirmed |
| `281B:0511` | `192B:0511` | 138 | `sub_286C1` | 短曲：以 12 bytes 一筆的表（`4D14:001E`）取檔名，讀入 EMS 並呼叫 `sub_281C0`，不等待結束。12 個呼叫點，引數全是 6 | confirmed |
| `281B:059B` | `192B:059B` | 119 | `sub_2874B` | 依索引載入 MID：以 13 bytes 一筆的表（`4D14:0096`）取檔名，`fread` 最多 `0x4E20` bytes 到 `4D14:01CC` 指的緩衝，不檢查旗標，不檢查 `fopen` 結果。`2BCC:0223`←引數 | confirmed |

### 2.2 呼叫端與狀態機

| IDA | 執行期 | 導覽名稱 | 作用 | 等級 |
|---|---|---|---|---|
| `1975:0036` | `0A85:0036` | `_main` | 呼叫初始化，`AX` 存到 `27B4:3958`（`sub_281C0` 的引數用，該常式不讀它） | confirmed |
| `1975:015D` | `0A85:015D` | `_main` | 啟動時呼叫 `PlayMusic(16)`（`SCOUT.MID`）一次 | confirmed |
| `1F33:21F8` | `1043:21F8` | `sub_21528` | `PlayMusic(索引)`：`sub_28250(1,1)`，接著重複呼叫 `sub_28424` 直到回傳不是 1，再 `sub_2874B(索引)`、`sub_281C0`，最後 `2BCC:0223`←索引。17 個呼叫點 | confirmed |
| `1F33:183A` | `1043:183A` | `sub_20B6A` | `PlayMusic(14)`（`NATIONAL.MID`），13 個呼叫點 | confirmed |
| `1F33:1850` | `1043:1850` | `sub_20B80` | `PlayMusic(7)` 或 `PlayMusic(6)`，依一個 `seg075` 的狀態字（IDA `4073:000D`）分支，只有 `7718:00B5` 一個呼叫點 | confirmed |
| `1F33:223C` | `1043:223C` | `sub_2156C` | 重播節拍，第 3.3 節。唯一呼叫點 `28EB:08A5` | confirmed |
| `28EB:074D` | `19FB:074D` | `sub_295FD` | 游標更新：先等 VGA 狀態埠 `3DAh` bit 3，最後在 `28EB:08A5` 呼叫重播節拍。游標隱藏旗標 `word_4D41B` 為 0 時跳過整個函式（含節拍） | confirmed |
| `28EB:00BD`、`0105`、`0067` | `19FB:00BD`、`0105`、`0067` | `sub_28F6D`、`sub_28FB5`、`sub_28F17` | 前兩者呼叫 `_int86(0x33)` AX＝3 取滑鼠位置（`28FB5` 另取按鍵）後呼叫 `sub_295FD`；`28F17` 是顯示游標 | confirmed |
| `2E7A:0012` | `1F8A:0012` | `sub_2E7B2` | 計時器安裝：取 INT 1Ch 舊向量，設為 `2E7A:00CB`（執行期 `1F8A:00CB`，與 probe 回報的 int1C 向量一致） | confirmed |
| `2E7A:0052` | `1F8A:0052` | IDA 稱 `sub_2E7F2` | `Delay(n, ticks)`：計時器 n 設值，之後在 `cs:[bx+0ABh]` 上忙等直到歸零。閒置時 CS:IP 長時間停在 `1F8A:0067` 到 `006E`，就是這個忙等 | confirmed |
| `2E7A:0076`、`0093` | `1F8A:0076`、`0093` | `sub_2E816`、`sub_2E833` | 設定、讀取計時器 n。陣列在 `2E7A:00AB`，16 個 word（INT 1Ch 處理常式開頭 `FA 60 1E 06 BB AB 00 B9 10 00`，`CX`＝16）。處理常式本體 IDA 未反組譯成 code；以 dosgolem 記憶體位元組讀出的規則是每 tick 對每個非 0 計時器減 3（夾到 0），見 `docs/re/018` 第 4 節 | 讀寫 confirmed；遞減規則 confirmed（位元組），真機頻率未驗證 |
| `1F33:03B6` | `1043:03B6` | `sub_1F6E6` | `PlaySFX(0x32)` 的包裝（介面點擊音）。17 個呼叫點 | confirmed |
| `7B3A:0488` | overlay（ovr379） | `sub_7B828` | `case 1` 直接呼叫 `sub_28211`、`sub_2874B(4)`（`ALCOHOL.MID`）、`sub_281C0` | confirmed |
| `76B6:0556` | overlay（ovr376） | `sub_770B6` | 結束路徑：`sub_28211`、`sub_28697` | confirmed |
| `1975:038C` | `0A85:038C` | `sub_19ADC` | 結束或錯誤出口：`sub_28250(1,1)`、等 `sub_28424` 回傳不是 1、`sub_28697`、`_exit(1)` | confirmed |

`PlayMusic` 以立即值呼叫的索引（`tools/ida_music_callargs.py` 的結果）：1、4、6、9、12、14、15、16、17、18 各 1 到 3 次，另有一處傳目前曲號（重播）。索引到檔名的對照是 13 bytes 一筆的表：0 `map1`、1 `map2`、2 `map3_1`、3 `map3_2`、4 `alcohol`、5 `battle1`、6 `battle2`、7 `battle3`、8 `chapel`、9 `dancer`、10 `enjoy`、11 `king`、12 `king2`、13 `mission`、14 `national`、15 `princess`、16 `scout`、17 `sys_load`、18 `sys_save`（均加 `.mid`）。表有 22 格，後 3 格是空字串。

音效編號（`sub_282CF` 的引數）以立即值呼叫的分佈：`0x35` 18 次、`0x32` 6 次、`0x33` 5 次、`0x3B` 4 次、`0x39` 2 次、`0x38` 1 次，另 1 處引數來源未解，共 37 個呼叫點，分佈在常駐段與 overlay。

### 2.3 資料（IDA `4D14`，執行期 `3E24`）

| 位移 | IDA 名稱 | 內容 | 等級 |
|---|---|---|---|
| `0008` | 無 | 11 個 word：`0, 500, 1800, 2900, 5700, 7800, 8700, 11000, 14100, 16600, 18300`（`probe -peek` 讀自 `3E24:0008`）。音效編號 `id`（`0x32` 到 `0x3B`）取 `[2×id−0x5C]` 為起點，下一個 word 為終點 | 表值 confirmed；語意強推論 |
| `001E` | 無 | 10 筆 × 12 bytes 的短曲檔名：`build`、`clear`、`dance_e`、`fight1`、`fight2`、`fightend`、`gold`、`rout`、`victory`、空。第 5 筆（`fightend.mid`）剛好 12 字元，沒有結尾 NUL，與下一筆相連成 `fightend.midgold.mid` | confirmed |
| `0096` | 無 | 13 bytes 一筆的 MID 檔名表，見 2.2 | confirmed |
| `01B4`、`01B6` | `word_4D2F4/6` | `sub_28406` 複製出的遠指標（dosgolem 實測 `D000:5000`） | confirmed |
| `01B8` | `word_4D2F8` | 旗標：0 無聲、1、2 | confirmed |
| `01BA` | `word_4D2FA` | 驅動狀態字，位址以命令 7 交給驅動；遊戲只讀不寫，讀 bit 0。bit 0 ＝「正在播放」是推論 | 讀寫關係 confirmed；語意強推論 |
| `01BC` | `word_4D2FC` | 淡出進行中 | confirmed |
| `01BE` | `word_4D2FE` | 淡出計時器重設值 | confirmed |
| `01C0` | `word_4D300` | SB 基底埠，由 `sscanf("%x", BLASTER 拷貝 +1)` 解出 | confirmed |
| `01C2` | `dword_4D302` | 驅動遠入口，載入後 `＝ 頁框:0000` | confirmed |
| `01C6` | `word_4D306` | EMS 控制代碼（dosgolem 實測 1） | confirmed |
| `01CA` | `word_4D30A` | EMS 頁框段（dosgolem 實測 `D000`） | confirmed |
| `01CC`、`01CE` | `word_4D30C/E` | MID 緩衝遠指標 ＝ 頁框:`5000` | confirmed |
| `01D0`、`01D2` | `word_4D310/12` | PCM 緩衝遠指標 ＝ 頁框:`8000` | confirmed |
| `01D4` | `byte_4D314` | `MIDI` 環境字串的拷貝（30 bytes） | confirmed |
| `01F2` | `byte_4D332` | `BLASTER` 環境字串的拷貝；`01F3` 起餵 `sscanf`，`01FB`（第 10 個字元）取 DMA 頻道字元 | confirmed |
| `0210` 起 | 無 | 字串：`SOUND`（`0210`）、`MIDI`（`0216`）、`BLASTER`（`021B`）、`%x`（`0223`）、`ctmidi.drv`（`0226`）、`rb`（`0231`）、`sound_e.pcm`（`0234`）、`rb`（`0240`）、`SB16`（`0243`）、`rb`（`0248`、`024B`） | confirmed |
| `2BCC:0223`（IDA `3ABC:0223`） | `word_3ADE3` | 目前曲號，`0FFh` ＝ 無 | confirmed |
| `2BCC:0224` | `word_3ADE3+1` | 節拍的「剛才在播放」旗標 | confirmed |

## 3. 資料流

### 3.1 初始化（`sub_28482`，`281B:02D2`）

```text
getenv("SOUND")   -> 暫存在 [bp-10h]（只用於後面的空值檢查與 SB16 比對）
getenv("MIDI")    -> strcpy(4D14:01D4, 結果)        無 NULL 檢查
getenv("BLASTER") -> strcpy(4D14:01F2, 結果)        無 NULL 檢查
sscanf(4D14:01F3, "%x", &4D14:01C0)                  SB 基底埠
int 67h AX=4000h  -> AH != 0 則跳到出口 281B:04E0    EMS 管理員狀態
int 67h AH=41h    -> 頁框段存 4D14:01CA
int 67h AH=43h BX=4 -> 控制代碼存 4D14:01C6          配置 4 頁，不檢查回傳
int 67h AX=4400h..4403h BX=0..3                      邏輯頁 0 到 3 映射到實體頁 0 到 3
4D14:01CC:01CE = 頁框:5000, 4D14:01D0:01D2 = 頁框:8000
SOUND 為 NULL 則跳到出口 281B:04E0
fopen("ctmidi.drv","rb") 為 NULL 則跳到出口
fread(頁框:0000, 1, 0x4650) 回傳 < 0x4268 則 fclose 並跳到出口
fclose; dword [01C2] = 頁框:0000
call [01C2] BX=1  DX:AX = 4D14:01D4（MIDI 字串）
call [01C2] BX=2  DX:AX = 4D14:01F2（BLASTER 字串）
call [01C2] BX=3
call [01C2] BX=7  DX:AX = 4D14:01BA（狀態字位址）
fopen("sound_e.pcm","rb"); fread(頁框:8000, 1, 0x4E20); fclose   不檢查 fopen 結果
strncmp(SOUND+3, "SB16", 4) == 0 ? [01B8]=1 : [01B8]=2
出口 281B:04E0: sub_28406; retf
```

所有驅動呼叫前，遊戲都先 `mov ax, 4D14h; mov ds, ax`，呼叫後不檢查 `AX`。驅動回報不了「硬體不存在」，遊戲會當作成功（強推論，沒有看到任何讀取回傳值的指令）。

### 3.2 換曲（`PlayMusic`，`1F33:21F8`）與淡出（`281B:0274`）

```text
sub_28250(1,1):  旗標0 -> 返回；旗標1 -> 4D2FC=1, 4D2FE=2, 計時器0Eh=2；旗標2 -> sub_28211（立即停止）
do { r = sub_28424() } while (r == 1)
sub_2874B(索引)      讀 MID 進 EMS 頁框+5000（不看旗標）
sub_281C0()          旗標0 -> 返回；否則混音器 26h=0DDh, 驅動命令 8, 命令 9
2BCC:0223 = 索引

sub_28424():
  若 4D2FC == 0: 回傳 4D14:01BA & 1
  若 計時器0Eh 未歸零: 回傳 4D14:01BA & 1
  否則: 混音器 26h 讀出值 −0x11 寫回；計時器0Eh 重設為 4D2FE；
        若新值 < 0x10: sub_28211()（停止，驅動命令 0Ah）, 4D2FC=0
        回傳 4D14:01BA & 1
```

旗標為 1 且驅動正常時，換曲要等音量每級降 `0x11`，從 `0DDh` 到 0 共 13 級。每級等計時器 `0Eh`（設為 `2n`）歸零，INT 1Ch 處理常式每 tick 減 3，所以每級 `ceil(2n/3)` 個 tick，`n ＝ 1` 時共 13 個 tick，名目 18.2065 Hz 下約 0.71 秒（強推論，真機的 INT 1Ch 頻率沒有驗證；推導見 `docs/re/018` 第 4 節）。

### 3.3 重播節拍（`1043:223C`，IDA `1F33:223C`）

```text
sub_28424() != 0            -> 2BCC:0224 = 1; 返回       （正在播放）
2BCC:0224 == 1              -> 計時器0Dh = 1             （剛結束，延遲 1 個節拍）
2BCC:0223 == 0FFh           -> 2BCC:0224 = 0; 返回       （沒有目前曲目）
計時器0Dh != 0              -> 2BCC:0224 = 0; 返回
否則 PlayMusic(2BCC:0223); 2BCC:0224 = 0
```

驅動存在時：播放中狀態字 bit 0 為 1，節拍什麼都不做；曲子結束後 bit 0 清除，等 1 個節拍再重播同一首，達成循環。驅動缺席時狀態字永遠是 0，`2BCC:0224` 因此永遠是 0，計時器 `0Dh` 也不會被設值（設定點只有節拍內的一處，`tools/ida_music_callargs.py` 對 `2E7A:0076` 的 12 個呼叫點以立即值列出的索引是 1、2、3、`0Dh`、`0Eh`、`0Fh`，`0Dh` 只出現在節拍），於是節拍每次被呼叫都走到 `PlayMusic`。計時器 `0Eh` 只被 `281B` 使用。

節拍只在游標顯示時執行：`sub_295FD` 開頭檢查 `word_4D41B`，為 0 就跳到 `28EB:08AA`，略過 `28EB:08A5` 的節拍呼叫；`28EB:0067`（顯示游標）把它設為 1，`28EB:0088`（隱藏游標）設為 0（confirmed）。`docs/re/008` 第 3 節與 `soak-s0/report.tsv` 的每 1 億道指令開檔次數在 1491 到 4924 之間浮動，與游標顯示時間比例及滑鼠輪詢頻率有關（強推論，沒有逐段對照）。

呼叫鏈（執行期位址，動態收據 `p2-call-*.txt`）：`19FB:00FF`（`sub_28F6D`）→ `19FB:074D` → `1043:223C`（由 `19FB:08AA` 返回）→ `192B:0274`（由 `1043:224A`）→ `1043:21F8`（由 `1043:227E`，引數 14）→ `192B:00A0`（由 `1043:220A`，引數 1 與 1）→ `192B:0274`（由 `1043:2212`）→ `192B:059B`（由 `1043:2221`，引數 14）。

### 3.4 短曲（`sub_286C1`）

先暫存目前曲號，呼叫停止（旗標 0 時是空操作），把曲號還原，讀 `4D14:001E + 12×索引` 的檔案進 EMS，呼叫 `sub_281C0`。不等待結束，也不檢查 `fopen` 結果。12 個呼叫點引數都是 6（`gold.mid`）。播完之後由重播節拍把原本的背景曲接回去（強推論）。

### 3.5 音效（`sub_282CF`，`281B:011F`）

```text
旗標0 -> 返回 0FFFFh
起點 = (4D14:01D2 << 4) + 4D14:01D0 + 表[2×id − 0x5C]        EMS 內 PCM 緩衝的線性位址
in  base+0Eh                                                  確認或清除 DSP 中斷
cli
等 DSP 寫入就緒（sub_28293，base+0Ch）; out base+0Ch, 0D1h     DSP 命令 D1h
等就緒; out base+0Ch, 40h; 等就緒; out base+0Ch, 83h          命令 40h，值 83h（時間常數 131）
8237: out 0Ah, (ch&3)|4（遮蔽）; out 0Ch, 0（清 flip-flop）; out 0Bh, (ch&3)|48h（模式）
      out 2×ch, 位址低位元組、位址高位元組; 頁面埠 87h/83h/81h/82h（頻道 0/1/2/3）寫位址最高位元組
      out 2×ch+1, 長度低位元組、長度高位元組; out 0Ah, ch&3（解除遮蔽）
等就緒; out base+0Ch, 14h; 等就緒; out base+0Ch, 長度低; 等就緒; out base+0Ch, 長度高
sti
```

`ch` 是 `4D14:01FB`（`BLASTER` 拷貝第 10 個字元）`& 3`。時間常數 131 對應取樣率 1000000 ÷ (256 − 131) ＝ 8000 Hz（SB DSP 的時間常數公式；`workplace/dosgolem/internal/machine/sb_dsp.go` 的實作用同一公式，這是專案內的對照，不是外部文件的對照，強推論）。`0D1h`（喇叭開）、`14h`（8 位元單次 DMA 輸出）同樣以 `sb_dsp.go` 對照。`SOUND_E.PCM` 以 `0x4E20` bytes 為上限讀入，檔案實長 18388 bytes。

### 3.6 結束（`sub_28697`）

旗標不為 0：驅動命令 4。接著不論旗標都釋放 EMS 控制代碼。`281B:04F5` 的 `jz` 目標是 `281B:0505`（釋放那一行），所以旗標為 0 時只是跳過命令 4。

## 4. 逐題回答

### 4.1 `ctmidi.drv` 字串的參照者與載入方式

- 參照者：`sub_28482`（IDA `281B:02D2`，執行期 `192B:02D2`）。參照指令 `281B:03D8` `push offset aCtmidiDrv`（位元組 `68 26 02`），緊接 `281B:03DB` 呼叫 `_fopen`（執行期 `192B:03D8` 起的位元組 `68 26 02 9A 4D 3A 10 01`，confirmed，`p1-peek.txt`）。`MAIN.EXE` 內該字串只有這一個參照者。
- 呼叫者：`_main`（`1975:0036`，執行期 `0A85:0036`），啟動時一次。位於常駐段，不在 overlay。
- 條件：依序為 EMS 管理員狀態正常、`SOUND` 非 NULL、`fopen("ctmidi.drv","rb")` 成功、`fread` 回傳不少於 `0x4268`（17000）。檔名沒有路徑，只在 DOS 目前目錄找（dosgolem 的 `resolve` 取 basename 後在 `-root` 找）。沒有設定檔、命令列旗標或硬體偵測。`SOUND` 的內容只用來決定旗標是 1 還是 2。
- 方式：`fopen`、`fread` 整份讀進 EMS 頁框的 `+0x0000`，`dword [4D14:01C2]` 指向它，之後以 `call far` 呼叫。沒有 EXEC，沒有重定位，沒有檢查檔案內容。驅動需要在「頁框段:0000」被呼叫時正確執行（位置相依性：未知）。
- 對照：`FILELIST` 列有 `CTMIDI.DRV`（`docs/re/001` 第 40 行），原版壓縮檔沒有。其來源與授權：未知。名稱暗示 Creative 的 MIDI 驅動，這一點沒有驗證，不列為結論。

### 4.2 沒有裝置或載入失敗時的行為

- 任何一個載入條件失敗：跳到出口 `281B:04E0`，旗標維持 0（資料檔初值，`4D14:0190` 到 `020F` 全為 0，位元組取自 IDA 資料庫，`q1.out`），遊戲繼續執行。這是跳過，不是重試，也沒有呼叫空指標。
- 之後的 API：`sub_281C0`、`sub_28211`、`sub_28250`、`sub_282CF`、`sub_28697` 的驅動與埠動作全部被旗標擋下。`sub_2874B`、`sub_286C1` 不看旗標，仍會讀檔。
- 重複開啟 MID 的迴圈在重播節拍（`1043:223C`，第 3.3 節），掛在滑鼠位置輪詢函式裡。原因是狀態字在沒有驅動時永遠是 0，節拍把「曲目已結束」判為真，一直重新載入目前曲目。收據：從狀態檔起 5 百萬道指令內 `192B:059B` 被呼叫 86 次，間隔 14698 到 14829 道指令，引數恆為 14（`NATIONAL.MID`）；呼叫者返回位址恆為 `1043:2221`。把 `3E24:01BA` 設成 1 之後，同一區間只剩 1 次（設值前那一次）。
- 缺席的原因有三種，結果相同：`SOUND` 未設、`ctmidi.drv` 開不起來、讀入不足 17000 bytes。dosgolem 現況屬第一種，見第 5 節收據 E1、E2。
- 每次重載是一次 `fopen`、`fread`（`0x4E20` 上限）、`fclose`。冷啟動 3 千萬道指令內開檔 1723 次，其中 `SCOUT.MID` 1706 次（`p3-cold30m.txt`）。檔案代號沒有累積（`docs/re/008` 第 3 節觀察到 2 到 3 個），與 `fclose` 成對一致。

### 4.3 驅動的呼叫介面

介面是 far 函式，不是軟中斷：`call dword ptr ds:[01C2]`，命令碼在 `BX`，遠指標引數在 `DX:AX`，DS 在每次呼叫前設為 `4D14`。驅動本體由遊戲載入到 EMS 頁框 `+0`，最多 18000 bytes，起碼 17000 bytes。

| `BX` | 呼叫點（IDA） | `DX:AX` | 推測意義 | 等級 |
|---|---|---|---|---|
| 1 | `281B:044A` | `4D14:01D4`，`MIDI` 字串拷貝 | 交給驅動解析 | 呼叫 confirmed；意義強推論 |
| 2 | `281B:045C` | `4D14:01F2`，`BLASTER` 字串拷貝 | 交給驅動解析 | 同上 |
| 3 | `281B:0468` | 無 | 初始化 | 強推論 |
| 7 | `281B:0479` | `4D14:01BA` | 設定狀態字位址 | 強推論 |
| 8 | `281B:004B` | `4D14:01CE:01CC`（頁框:5000） | 設定曲目資料位址 | 強推論 |
| 9 | `281B:0057` | `DX` 沿用命令 8 呼叫的回傳值，`AX` 在 `281B:004F` 重載為 `4D14h`（執行期 `3E24h`） | 開始 | 呼叫 confirmed；意義強推論 |
| `0Ah` | `281B:008A` | 無 | 停止 | 強推論 |
| 4 | `281B:0500` | 無 | 結束 | 強推論 |

沒有看到命令 0、5、6、`0Bh` 以上。MID 資料是整份載入：`fread` 一次讀到 `0x4E20`（20000）bytes，最大的 `MAP1.MID` 是 11743 bytes，緩衝在頁框 `+5000` 起，到 `+7DDE` 結束，沒有碰到 `+8000` 的 PCM 緩衝；沒有串流、分段補資料。驅動要在不被遊戲重新映射的前提下讀這塊 EMS：遊戲只在初始化映射一次 4 頁，之後不再呼叫 `AH=44h`（`int 67h` 的 8 處全在 `281B`，`docs/re/004`）。

### 4.4 驅動存在時會寫哪些埠

遊戲自己的埠存取（`281B` 內全部 31 條 `in`／`out`，整個資料庫的 overlay 內沒有 `in`／`out`，`docs/re/007` 第 9 節）：

| 埠 | 用途 | 位置 | 等級 |
|---|---|---|---|
| `base+4`、`base+5` | SB 混音器索引與資料；索引 `26h`，設 `0DDh`（開始）、設 0（停止）、讀出減 `11h` 再寫回（淡出） | `281B:0033` 起、`007B` 起、`029F` 起 | 位元組 confirmed；`26h` ＝ MIDI 或 FM 音量是依一般 SB 混音器暫存器配置的記憶，未對照原文件，強推論 |
| `base+6`、`base+0Ah`、`base+0Ch`、`base+0Eh` | DSP 重設、讀資料、寫命令與寫入就緒狀態、讀取就緒狀態與中斷確認 | `281B:00E3`、`011F` | 位元組 confirmed；命令語意強推論 |
| `0Ah`、`0Bh`、`0Ch`、`2×ch`、`2×ch+1`、`81h`、`82h`、`83h`、`87h` | 8237 DMA 與頁面暫存器 | `281B:01AD` 起 | 位元組 confirmed |

`base` 來自 `BLASTER` 的第 2 個字元起的十六進位（`A220` 解出 `0220h`，E1 實測 `4D14:01C0` ＝ `0220`）。遊戲沒有對 OPL（388h、389h）、MPU-401（330h、331h）、PIT、喇叭（61h）寫埠，也沒有偵測這些裝置。驅動自己碰哪些埠：未知（驅動不在手上）。`MIDI` 與 `BLASTER` 字串原樣交給驅動，埠位址與合成器種類由驅動決定。

### 4.5 驅動缺席但程式假設存在的路徑

驅動缺席（旗標 0）時，9 個 `call dword ptr [01C2]` 的保護如下：

| 呼叫點 | 保護 |
|---|---|
| `281B:004B`、`0057` | `281B:0019` `cmp [01B8],0`，為 0 回傳 `0FFFFh` |
| `281B:008A` | `281B:006A` `cmp [01B8],0`，為 0 跳過 |
| `281B:0500` | `281B:04F0` `cmp [01B8],0`，為 0 跳過 |
| `281B:044A`、`045C`、`0468`、`0479` | 在載入成功路徑內，`dword [01C2]` 在 `281B:0438` 才設定 |

所以「驅動缺席，卻呼叫到無效位址」在 MAIN.EXE 內沒有路徑（confirmed）。下表是已確認會停機、卡死或破壞記憶體的條件，前提都不是驅動缺席本身，但都與聲音子系統的假設有關：

| # | 條件 | 證據 | 結果 | 等級 |
|---|---|---|---|---|
| H1 | EMS 管理員不存在 | `281B:0349` 到 `034F` 跳出口，`4D30C:4D30E` 維持資料檔初值 0:0（`4D14:01CC` 到 `01CF` 為 0）；`_main` 之後的 `PlayMusic` 走到 `281B:05E6` 到 `05F6` 的 `fread(0000:0000, 1, 0x4E20, …)`，寫進中斷向量表與 BIOS 資料區。收據 E4：把 `192B:0344` 的 `CD 67` 改成 `B4 80` 模擬，第 801086 道指令停機，`0000:0000` 起出現 `MThd` 簽章（`SCOUT.MID` 的檔頭），CS:IP 跑到 `B808:0353` | 向量表被 MIDI 資料蓋掉，程式飛走 | confirmed（注入） |
| H2 | 旗標不為 0（驅動載入成功）但沒有真的 SB DSP | `sub_282CF` 第一次等待逾時，重設 DSP 後在 `192B:0107` 到 `0117` 等 `base+0Eh` bit 7 與 `base+0Ah`＝`0AAh`，沒有上限，而且全程在 `cli` 之後。收據 E3b、E3d：旗標、基底埠與驅動入口以 `-poke` 設好，`PlaySFX(50)` 一呼叫就進入迴圈，第 1504500000、1505000000、1507000000 道指令的 CS:IP 都在 `192B:010A`，`AX＝0080`、`DX＝022E`，IF ＝ false（E3b 的 probe 輸出），埠 `0226` 被寫過。dosgolem 的 `Machine.In8` 對沒有裝置的埠回 `0xFF`（`workplace/dosgolem/internal/machine/machine.go` 該函式最後一行），與 `AX＝0080` 相符：`022E` 的 bit 7 是 1 所以第一個迴圈放行，`022A` 讀到 `0FFh` 不等於 `0AAh` 所以第二個條件一直不成立 | 無限迴圈，計時器中斷關閉，遊戲完全卡死 | confirmed（注入） |
| H3 | 驅動狀態字 bit 0 卡在 1 | `PlayMusic` 的 `1043:2212` 迴圈只靠驅動清除 bit 0。收據 E3e：在 `PlayMusic` 內把 `3E24:01BA` 設成 1，第 1505000000 與 1507000000 道指令時 CS:IP 在 `192B:02C9` 與 `192B:0274`，IF ＝ true，`192B:059B` 之後一次也沒被呼叫 | 無限忙等（中斷開著，輸入不處理） | confirmed（注入）；需要驅動才會把 bit 設為 1，驅動缺席時不發生 |
| H4 | `MIDI` 或 `BLASTER` 環境變數不存在 | `strcpy` 的來源是 `getenv` 的 NULL，無檢查。dosgolem 實測 `4D14:01D4` 與 `01F2` 都是 `51 01 10 01 04`，即 `0000:0000` 起的中斷向量表位元組，複製到第一個 0 為止。緩衝各 30 bytes；若中斷向量表開頭 30 bytes 都不含 0 會溢位，真實 DOS 的內容：未知 | 讀向量表；溢位條件未驗證 | 複製行為 confirmed；溢位未知 |
| H5 | `fopen` 失敗不檢查 | `sub_2874B`（`281B:05DE` 到 `05F6`）、`sub_286C1`、`sound_e.pcm` 的 `fopen`（`281B:0486` 到 `04A3`）都直接把結果交給 `fread` | `fread` 以 NULL 的 `FILE *` 運作，後果未跑過 | 靜態；原版檔案齊全時不觸發（`ALCOHOL.MID` 是 0 byte，`fopen` 仍成功，`fread` 回傳 0，緩衝保留上一首的資料，強推論未跑） |
| H6 | 12 bytes 短曲表第 5 筆 | `fightend.mid` 無結尾 NUL，組成 `fightend.midgold.mid`，`fopen` 必失敗；但 12 個呼叫點引數全是 6 | 不可達 | confirmed（靜態） |

## 5. 動態收據

起點狀態的步數是絕對值。輸出在 `workplace/out/re-music/`（已 gitignore）。環境注入用 `-poke "00D0:0000@1=<hex>"`，內容見 `env-hex.txt`：`COMSPEC=C:\COMMAND.COM`、`SOUND=C:\SB16`、`BLASTER=A220 I5 D1 T3`、`MIDI=SYNTH:1 MAP:E`、程式路徑 `C:\PROG.EXE`。替身驅動 `root-stub/ctmidi.drv` 是自寫的 18000 bytes（`B8 01 00 CB` 重複 4500 次，即 `mov ax,1; retf`），其餘檔案是指向 `/orig/orig/` 的符號連結。

| 編號 | 命令（精簡） | 結果 | 檔案 |
|---|---|---|---|
| E0 | `probe -load-state … -steps 1500000000 -peek 00D0:0000:48,3E24:01B0:80,…` | 環境區塊只有 `COMSPEC` 與程式路徑；`3E24:01B8`（旗標）＝0、`01BA`＝0、`01C0`＝0、`01C6`（EMS 控制代碼）＝1、`01CA`＝`D000`、`01CC`＝`5000`、`01D0`＝`8000`；`01D4`、`01F2` ＝ `51 01 10 01 04` | `p1-peek.txt` |
| E0b | 冷啟動 `-steps 30000000` | 開檔 1723 次，無 `ctmidi.drv`、無 `sound_e.pcm`；`EMS`：第 65010 道指令配置 4 頁並映射 0 到 3；找不到的檔只有 `C:\PROG.EXE`，這是 dosgolem 環境區塊尾端的預設程式路徑（`loader.go`），不在 `-root`，查找者與聲音無關，來源未追 | `p3-cold30m.txt` |
| E1 | 冷啟動 2 千萬道，注入環境，不給驅動檔 | 找不到的檔多出 `ctmidi.drv`（出現 2 筆）；旗標維持 0；`4D14:01C0`＝`0220`，`01D4` 是 `SYNTH:1 MAP:E`，`01F2` 是 `A220 I5 D1 T3`；`sound_e.pcm` 未開；遊戲照常，`SCOUT.MID` 開 1026 次；埠寫入集合仍是 PIC 與 VGA | `e1-env-nodrv.txt` |
| E2 | 同上，`-root` 改為含替身驅動的目錄 | 第 65811 道指令開了 `ctmidi.drv`，`fread` 以 512 bytes 緩衝分段讀滿 18000 bytes（17920 加 80）；`dword [01C2]`＝`D000:0000`；第一次驅動呼叫 `BX=1`、`DX:AX＝3E24:01D4`（命令 1 與 MIDI 字串，與靜態一致）時 probe 停機：`CS:IP＝D000:0000`，原因是 `cmd/probe/main.go` 與 `apps/hr/cmd/hrsoak/main.go` 的護欄「CS 線性位址 ≥ A0000 視為跑飛」。EMS 視窗 `D000:0000` 可讀，位元組與替身檔一致。CPU 本身能否執行該區：未驗證 | `e2-env-stubdrv.txt` |
| E3a | 狀態檔，第 1503740000 道指令 `-poke 3E24:01BA=01`，`-call-args 192B:059B` | 5 百萬道內 1 次（無注入時 86 次）。重播節拍由狀態字 bit 0 抑制 | `e3a-status-poke.txt` |
| E3b、E3c、E3d | 狀態檔，第 1500000010 道指令 `-poke` 旗標＝1、基底埠＝`0220`、驅動入口＝`192B:0000`（空殼） | `PlaySFX` 在第 1503289248 道指令由 `1043:03C6`（`sub_1F6E6` 的返回位址）以引數 50 呼叫（不注入時同一步數也有同一次呼叫，旗標為 0 立即返回，`p4-sfx-nopoke.txt`）；之後卡在 `192B:010A`，`DX＝022E`，寫過的埠多出 `0226`；驅動空殼入口 0 次被呼叫（卡死在 SFX，沒走到音樂）；IF ＝ false | `e3b-…`、`e3c-…`、`e3d-hang-*.txt` |
| E3e | 狀態檔，第 1503734225 道指令（`PlayMusic` 內）`-poke 3E24:01BA=01` | 無限忙等於 `192B:0274` 與 `192B:02C9`，IF ＝ true | `e3e-spin-*.txt` |
| E4 | 冷啟動 3 千萬道，`-poke 192B:0344@1=B4 80`（EMS 不可用） | 第 801086 道指令停機，`CS:IP＝B808:0353`；`0000:0000` 起為 `MThd` | `e4-ems-denied.txt` |
| 呼叫軌跡 | `-call-args`：`192B:059B`、`1043:21F8`、`1043:223C`、`19FB:074D`、`192B:0274`、`192B:00A0`，窗口 1500000000 到 1505000000 | 次數 86、86、86、91、172、86；呼叫者位址見 3.3 | `p2-call-*.txt` |

靜態輸出：`workplace/ida-music/out/q1.out` 到 `q7.out`（反組譯、呼叫者、`in`／`out`、`int` 清單）、`callargs.txt`、`music_strings*.txt`、`cfg_strings.txt`、`qcfg.out`、`cfg_names.tsv`。

## 6. `CFG.EXE`、`OP.EXE`、`END.EXE`

- `CFG.EXE`（6072 bytes）：Turbo C++ 1990 的程式，共 45 個小函式；可印字串只有版權、執行期錯誤訊息與 `Configuration`；沒有檔名字串；沒有 `in`／`out`；`int 21h` 只有 RTL 的結束、向量、寫檔、ioctl、lseek。靜態上看不到任何與音效設定有關的行為。用途：未知。
- `OP.EXE`、`END.EXE`：與 `MAIN.EXE` 同樣的音樂檔名表、`SOUND`、`MIDI`、`BLASTER`、`ctmidi.drv`、`sound_e.pcm` 字串，各有一個參照 `ctmidi.drv` 的初始化常式（`OP.EXE` `1E63:02DA`，`END.EXE` `1FBF:02D2`）。呼叫端與行為沒有逐項追，視為同一份函式庫。
- `HR.BAT`、`INST.BAT`、`CONFIG.IBM` 內沒有設定 `SOUND`、`BLASTER`、`MIDI` 的行。

## 7. 讓三平台版出聲的選項

只列選項與需要的證據，沒有實作。第三方驅動不在手上，下表不假設能取得它。

| 選項 | 做法 | 需要的證據或前置 | 風險 |
|---|---|---|---|
| A 攔截 API 邊界 | 以 `OnCall` 掛在 `192B:059B`（取得索引，曲名在 `3E24:0096 + 13×索引`）、`192B:0010`（開始）、`192B:0061`（停止）、`192B:00A0`（淡出）、`192B:011F`（音效編號），由前端播放；維持 `3E24:01BA` bit 0 與「曲子結束」同步，否則重播節拍會一直重載 | 每個 hook 的完整副作用（靜態已有）；`OnCall` 能掛在 MZ 實機路徑（`apps/rich2` 已在用，本專案未驗證）；MIDI 合成器選型與 MID 的音色對映（GM、MT-32 或 FM 專用）：未知，需要檔內程式變更分佈；旗標要為 1 才保留遊戲自己的淡出邏輯，需要在環境區塊注入 `SOUND`，而 dosgolem 目前寫死 `COMSPEC` | 實作量最小；與遊戲自己的狀態機的耦合要逐一核對 |
| B 自寫替身驅動加環境注入 | 自寫一個 ≥17000 bytes 的 `ctmidi.drv` 與環境字串，讓遊戲走完整路徑，替身把命令轉給前端 | dosgolem 要能執行 EMS 頁框內的程式（E2：harness 護欄停在 `D000:0000`，CPU 本身未驗證）；SB DSP 重設交握（回 `0AAh`）、寫入就緒、讀取就緒與 8237 DMA，否則 H2；dosgolem 有 `sb_dsp.go`、`DMA8237` 與 AdLib 偵測，掛在 LE 路徑（`le_opl_ports.go`），MZ 實機對 `022x` 讀回 `0FFh`（E3d），能否掛到 MZ 路徑：未查；替身必須是自寫，不複製原廠驅動 | 前置多；能同時啟動音樂與音效 |
| C 真驅動加硬體模擬 | 使用者自備 `CTMIDI.DRV`，dosgolem 模擬它碰的 OPL 或 MPU 等硬體 | 驅動本體（反組譯得到第 4.4 節缺的埠清單）；權利邊界（AGENTS.md 第 2 節，第三方檔案）；B 的全部前置 | 最重；依賴不在原版壓縮檔內的檔案 |
| D 只做音效 | `OnCall` 掛 `192B:011F`，讀 `3E24:0008` 的表與 `SOUND_E.PCM` 切片，以 8 kHz、8 位元無號播放，不模擬 DSP 與 DMA | `SOUND_E.PCM` 的格式（`docs/re/001` 記錄開頭 4 bytes 是長度 `0x47D4`，其後 `80` 重複；表從 0 起算，是否包含這 4 bytes：未知）；編號 `0x32` 到 `0x3B` 對應的切片邊界；hook 在入口取代函式，不依賴旗標 | 沒有音樂 |
| E 不出聲，只去掉重載 I/O | 把 `3E24:01BA` bit 0 維持為 1，或 hook `1043:223C` 讓節拍不做事 | E3a 已證明狀態字抑制重載；要確認 bit 0 維持為 1 不影響 `PlayMusic` 的等待迴圈（H3：`PlayMusic` 會在 `1043:2212` 無限等待，所以 hook 節拍比常設 bit 0 安全）| 不改變聲音，只改變 I/O 量 |

## 8. 尚未回答的問題

| 問題 | 狀態 |
|---|---|
| `CTMIDI.DRV` 的內容、碰的硬體埠、命令 3 與 9 的意義、命令 8 的引數是否含長度 | 未知（驅動不在手上） |
| 狀態字 `4D14:01BA` 的 bit 位元語意（只確認遊戲讀 bit 0） | 強推論 |
| 旗標為 2 對應什麼硬體；`SOUND` 其他取值的行為 | 未知（只知 `SB16` 比對的位置） |
| `BLASTER` 第 10 個字元當 DMA 頻道是固定偏移，真實字串（例如 IRQ 兩位數）是否破壞它 | 未驗證 |
| INT 1Ch 處理常式本體（`2E7A:00CB` 起）的節拍週期 | 遞減規則已由位元組讀出（每 tick 減 3，`docs/re/018` 第 4 節）；真機的節拍週期未驗證 |
| 真實 DOS 上 `0000:0000` 起的 30 bytes 是否含 0（H4 溢位條件） | 未知 |
| jsdos 版是否設定 `SOUND`（DOSBox 預設是否設 `BLASTER`、`SOUND`） | 未查 |
| MID 檔的音色映射與是否依賴特定合成器 | 未知（未分析檔內容） |
| `SOUND_E.PCM` 切片是否含 4 bytes 檔頭；表最後一個值 18300 與檔長 18388 的差 88 bytes 的用途 | 未知 |
| `7D37:0D59` 為何呼叫兩個空殼（`192B:0000`、`192B:0008`） | 未知 |
| 未被 `PlayMusic` 立即值呼叫的索引（0、2、3、5、7、8、10、11、13）是否被計算值呼叫 | 未追 |
| `OP.EXE`、`END.EXE` 的呼叫鏈與行為是否與 `MAIN.EXE` 相同 | 未追 |
| dosgolem 的 CPU 能否執行 EMS 頁框內的程式（E2 只證明 harness 護欄先停機） | 未驗證 |
| 真實 DOS 無 `SOUND` 時，每次滑鼠輪詢重讀 MID 的行為與影響 | 未知，沒有實機 |

## 9. 重跑

```text
# 靜態（輸出在 workplace/ida-music/out/，唯一證據是輸出檔）
export HR_IDA_WORK=$PWD/workplace/ida-music
tools/ida.sh run MAIN.EXE ida_music_strings.py /work/out/music_strings.txt
tools/ida.sh run MAIN.EXE ida_music_query.py /work/out/<命令檔> /work/out/<輸出>     # 命令檔放在 workplace/ida-music/out/
tools/ida.sh run MAIN.EXE ida_music_callargs.py /work/out/callargs.txt 281B:011F 1F33:21F8 281B:059B 281B:0511

# 動態（E0）
tools/dosgolem.sh probe -load-state /out/soak-s0/ck-001500000000.state -steps 1500000000 \
  -peek 00D0:0000:48,3E24:0000:32,3E24:01B0:80,3E24:0210:48,192B:059B:20
# 重載節拍的呼叫軌跡
tools/dosgolem.sh probe -load-state /out/soak-s0/ck-001500000000.state -steps 1505000000 -call-args 192B:059B:2:1500000000:1505000000
# E3a：狀態字注入
tools/dosgolem.sh probe -load-state /out/soak-s0/ck-001500000000.state -steps 1505000000 \
  -poke "3E24:01BA@1503740000=01" -call-args 192B:059B:1:1500000000:1505000000
# E1：環境注入（hex 見 workplace/out/re-music/env-hex.txt）
tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 20000000 -poke "00D0:0000@1=<env-hex>"
# E4：EMS 不可用
tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 30000000 -poke "192B:0344@1=B4 80" -peek 0000:0000:32
```
