# MAIN.EXE 讀鍵普查（F2、F3、F4）

日期：2026-10-03
性質：證據探針報告（子代理產出，主代理審閱後入庫）。審閱時抽查：結論與 `docs/re/016` 第 92 行的旁證一致（遊戲在不讀鍵盤的畫面不取走按鍵）；位址對照表與 `docs/re/007` 第 8 節的換算規則一致。涵蓋限制見第 7 節，純靜態，沒有動態收據。
範圍：`MAIN.EXE` 靜態普查。目的是確認前端把 F2、F3、F4 保留給前端功能（不再送進遊戲）時，遊戲有沒有任何程式路徑會受影響。不含 `OP.EXE`、`END.EXE`、`PSH.EXE`、`SIG.COM`。

## 1. 摘要

- `MAIN.EXE` 共 77 個 `int 21h` 指令，讀鍵的只有 4 個，分屬 3 個函式：`sub_19623`（getch）、`_kbhit`、`sub_29BAB`（清鍵盤緩衝）。
- 沒有 `int 16h`，沒有 INT 09h 掛接，沒有讀 I/O 埠 60h，沒有存取 BIOS 鍵盤緩衝（`0040h` 段）。
- 這 3 個函式的呼叫點共 7 處：getch 5 處，`sub_29BAB` 2 處，`_kbhit` 0 處。5 處 getch 全在錯誤訊息之後（配置失敗、開檔失敗、`restore error`），2 處 `sub_29BAB` 在結束程序。沒有任何一處使用讀到的鍵值。
- 結果：F2、F3、F4 在 `MAIN.EXE` 內不會改變遊戲行為。同理，任何其他鍵在正常遊玩路徑上也沒有被讀取。

等級見第 6 節。

## 2. 輸入與工具

| 項目 | 內容 |
|---|---|
| 輸入 | `workplace/orig/MAIN.EXE`，SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`（`tools/ida.sh` 啟動時再印一次，與此相同） |
| 工具 | IDA Pro 9.4（資料庫內 `get_kernel_version()` 回 `9.4`），image `ida-pro-9.4-idapython:locked-v1`（id `sha256:6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`），經 `tools/ida.sh run`，`docker run --rm`、非 root、`--network none` |
| 資料庫 | `idat -A -c MAIN.EXE`，不加 loader 參數。510 段（含 139 個 overlay 與 139 個 stub 段），code head 116749，函式 1968，與 `docs/re/007` 第 9 節相同 |
| 腳本 | `tools/ida_fkey_scan.py`（SHA-256 `624ccfe9f771b380e1420eefbb74f2b2bbb9944548edcd037026a2e2524f3860`）、`tools/ida_fkey_dump.py`（SHA-256 `dcbaf7bab78d706c81be94658f2276f67af7b411928ff9d15fcac80b8014a34b`） |
| 工作區 | `workplace/ida-fkey/`（`HR_IDA_WORK`），輸出在 `out/` |

位址寫法：

- 線性位址是 IDA 資料庫的線性位址（十六進位）。
- `sel:off` 是 IDA 的選擇子與偏移。
- 常駐映像的執行期段 ＝ IDA 選擇子 − `0x0EF0`（`docs/re/007` 第 8 節）。例：`sub_29BAB` 的 IDA `29BA:000B` 對應執行期 `1ACA:000B`；`sub_19623` 的 IDA `1000:9623` 對應執行期 `0110:9623`。

## 3. 與前一份普查的位址對照

`workplace/ida/out/int_MAIN.EXE.json` 的位址是「線性位址 ÷ 16 ： 線性位址 mod 16」的正規化寫法，不是 IDA 的 `sel:off`。四處讀鍵呼叫點對照如下，與前一位分析者看到的四處是同一批指令。

| 前一份寫法 | 線性位址 | IDA `sel:off` | 函式 |
|---|---|---|---|
| `29BB:000F`（`AH=08`） | `29BBF` | `29BA:001F` | `sub_29BAB` |
| `29BB:0007`（`AH=0B`） | `29BB7` | `29BA:0017` | `sub_29BAB` |
| `1966:0005`（`AH=0B`） | `19665` | `1000:9665` | `_kbhit` |
| `1964:0008`（`AX=0700`） | `19648` | `1000:9648` | `sub_19623` |

## 4. 問題 1：全部讀鍵路徑

### 4.1 DOS `int 21h`

全庫 `int 21h` 指令 77 個（`out/fkey_ints.tsv`）。原始位元組 `CD 21` 在 510 段內也只命中這 77 處，每一處都是 IDA 的指令起點（`out/fkey_raw.tsv`），未定義區沒有多出來的 `CD 21`。每個 `int 21h` 往回追 `AH`／`AX` 常數，77 處全部解出（無 `AH=?`）。

讀鍵類 `AH`（01、06、07、08、0A、0B、0C）共 4 處：

| 線性位址 | IDA `sel:off` | bytes 與前置 | 所在函式 | 服務 |
|---|---|---|---|---|
| `19648` | `1000:9648` | `b8 00 07 cd 21`（`mov ax,700h`） | `sub_19623`（`1000:9623` 至 `964E`） | 直接 stdin 輸入，不回顯 |
| `19665` | `1000:9665` | `b4 0b cd 21`（`mov ah,0Bh`） | `_kbhit`（`1000:964F` 至 `966B`） | 檢查 stdin 狀態 |
| `29BB7` | `29BA:0017` | `b4 0b cd 21` | `sub_29BAB`（`29BA:000B` 至 `002F`） | 檢查 stdin 狀態 |
| `29BBF` | `29BA:001F` | `b4 08 cd 21`（`mov ah,8`） | `sub_29BAB` | stdin 輸入，不回顯 |

`AH=01`、`06`、`0A`、`0C`：0 處。

其餘 73 處是檔案、記憶體、日期時間、向量、版本、`ioctl`、寫 stderr 等服務。讀 handle 的 `AH=3F` 有 5 處：`__rtl_read`（`10E85`）、`sub_2B1A8` 兩處（`2B1E5`、`2B203`，遊戲的檔案讀取包裝）、overlay 管理員 `sub_35AE9`（`35AF1`）與 `sub_35C45`（`35C69`）。handle 為 0（CON）的讀法見第 7 節。

`sub_19623` 與 `_kbhit` 共用 ungetch 緩衝：`byte_639BE`（旗標，`dseg` `62FF:09CE`）與 `byte_639BF`（字元）。這兩個位元組的 xref 只有這兩個函式內的讀寫，沒有別處寫入。

### 4.2 BIOS `int 16h`

| 檢查 | 結果 |
|---|---|
| `int 16h` 指令 | 0 |
| 原始位元組 `CD 16`（510 段全搜） | 0 |
| `bioskey`、`getkey` 類名稱 | 無（函式名稱表 `workplace/ida/out/names.tsv` 與 `name` 查詢） |

間接進入點：`_int86`（`1000:273D`，線性 `1273D`）的呼叫點 15 處，`_int86x`（`1000:2779`）的唯一呼叫者是 `_int86`（`1276C`）。15 處的 `intno` 都是立即值 push：

| `intno` | 處數 | 呼叫點線性位址 |
|---|---|---|
| `10h` | 1 | `2516C`（`AH=0`、`AL=12h`，設視訊模式） |
| `33h` | 14 | `28ED8`、`28F8A`、`28FD2`、`2904F`、`2908A`、`290D2`、`2911A`、`29162`、`291AA`、`291D1`、`29565`、`29597`、`295C5`、`295F2` |

`int 33h` 的功能編號：0、3、4、5、6、7、8、0Ch（`CX=0`）、0Fh、1Dh、1Fh，全是滑鼠。原始位元組搜尋 `9A 3D 27 00 10`（遠呼叫 `_int86`）也是 15 處；`9A 79 27 00 10`（`_int86x`）與 `EA 3D 27 00 10`、`EA 79 27 00 10`（遠跳）為 0。

`_int86x` 在堆疊上自組 `55 CD nn 5D CB` 再呼叫（`1000:2791` 至 `279F`），所以位元組搜尋看不到這條路，要靠上面的呼叫點表。

### 4.3 INT 09h 掛接與 IVT 直寫

向量設定與讀取只有下列幾處，沒有 INT 09h。

| 位置（線性位址） | 方式 | 向量 |
|---|---|---|
| `101A5`（`sub_10166`）、`101B7` 起（`__restorezero`） | `int 21h` `AX=25xx`、`35xx` | 0、4、5、6（Borland 啟動與還原） |
| `12995`、`12A6A`（`_setvect`、`_getvect` 呼叫） | `_setvect(0x23)`、`_getvect(0x23)` | 23h |
| `12AAC`、`12AC0` | `_setvect(0, ...)`、`_setvect(4, ...)` | 0、4 |
| `297A2`、`297C7`、`2978B` | `_setvect`、`_getvect`（`sub_29779`、`sub_297AD`） | 6 |
| `29C1F`、`29C44`、`29C08` | `_setvect`、`_getvect`（`sub_29BF6`、`sub_29C2A`） | 24h |
| `2E7B9`、`2E7CF`、`2E7EB` | `int 21h` `AX=351Ch`、`251Ch` | 1Ch（計時器） |
| `35973`、`35985`（`sub_35965`，overlay 管理員） | `AH=35`、`AH=25`，`AL` 取自 `byte ptr word_602B0+1` | `word_602B0` 的位元組是 `cd 3f`，所以是 3Fh |

`_setvect` 的 7 個呼叫點與 `_getvect` 的 3 個呼叫點，`interruptno` 都是立即值（23h、0、4、6、24h）。

IVT 直寫：把 `ES`／`DS` 設為 0 的載入只有 2 處（往回找第一個改寫該暫存器的指令是 `xor reg,reg` 或 `mov reg,0`／`40h`）：

| 線性位址 | 內容 |
|---|---|
| `29BC5`（`sub_29BAB`） | `ds` ＝ 0 後 `and word ptr ds:500h, 0FFDFh`，位址 `0000:0500`，不是鍵盤緩衝，也不是 IVT |
| `2E899`（`sub_2E893`） | `es` ＝ 0 後讀 `es:204h`、`es:206h`，是 INT 81h 的向量，用來比對處理常式前 2 bytes 是否為 `S`、`G`（`SIG.COM` 簽章），只讀 |

IDA 對絕對位移的寫法是 `es:24h`，不帶方括號。以 `(es|ds|cs|ss):24h`、`:26h`（INT 09h 向量位址）搜尋：0。`ds:500h`、`es:204h`、`es:206h` 只有上表 2 處。

### 4.4 I/O 埠

| 檢查 | 結果 |
|---|---|
| `in` 指令 | 8，全是 `in al, dx` |
| 其中 `DX` ＝ `3DAh`（VGA 狀態） | 3：`29618`、`29C55`、`29C5D` |
| 其中 `DX` ＝ Sound Blaster 基底加位移 | 5：`2829C`、`282B7`、`282BF`（`sub_28293`，呼叫者 `sub_282CF` 傳入 `word_4D300` 加 `0Ch`／`0Eh`）、`28320`、`28451`（`word_4D300` 加位移） |
| 原始位元組 `E4 60`、`E5 60`（`in al/ax, 60h`） | 0 |
| `out` 的立即埠 | 0Ah、0Bh、0Ch、68h、81h 至 83h、87h、0A1h、0A3h、0A5h、0A6h；無 60h、61h、64h |
| `out dx, al/ax` | 743 處，只影響輸出，與讀鍵無關 |

### 4.5 BIOS 資料區（`0040h` 段）

- `ES`／`DS` 載入 `0040h` 的指令：0（`mov reg, 40h` 後 `mov es/ds, reg`、`push 40h` 後 `pop es/ds` 都沒有）。
- `push 40h` 共 52 處，全是 UI 或繪圖函式的立即參數（後面接 `push 數字` 或 `call`，沒有 `pop es/ds`）。
- 資料中的遠指標常數 `xx 00 40 00`（xx ＝ 17h、18h、1Ah、1Ch、1Eh、6Ch）：0；`80 00 40 00` 2 處，位於圖樣點陣資料（`2C241`、`2C250`），不是指標。
- 絕對位移 `1Ah`、`1Ch`、`1Eh`、`41Ah`、`41Ch`、`41Eh`、`417h`、`418h`、`419h`、`496h`、`17h`、`18h`、`19h` 的 `es:`／`ds:`／`ss:` 存取共 24 處（`out/dump_12.txt`）。全在 overlay 管理員（`seg054`，19 筆）與 Borland 例外框架（`__ExceptInit`、`sub_16AC8`、`sub_17A73`，`ss:18h`、`ss:1Ah`，5 筆）內。映像內沒有任何 `ES`／`DS` 載入 `0040h` 的指令，所以這些存取的段不是 BIOS 資料區（強推論，`ES` 若由記憶體變數載入 `0040h` 則不在此檢查內）。

### 4.6 其他可能的輸入

- `_fgetchar`（`getchar` 類，讀 stdin）：無任何 xref。
- `_fgetc` 呼叫點 6 處（`25079`、`2511B`、`25225`、`25376`、`254EA`、`7D80D`）與 `_fscanf` 1 處（`7D46A`）。這 7 處所在的函式都各自呼叫 `_fopen`（`_fopen` 共 13 個呼叫點，分布在 `sub_24FF9`、seg017 的 3 個無名函式、`sub_28482`、`sub_286C1`、`sub_2874B`、`sub_7D41C`、`sub_7D4B4`、`sub_7D6DF`，見 `dump_14.txt`）。`25225` 的函式已讀：`fopen(路徑, "rb")` 的回傳值存在 `[bp-0Eh]`，空指標時印 `graph:Can't open3 %s`，之後 `_fgetc` 取 `[bp-0Eh]`。其餘以同函式內有 `_fopen` 判斷，沒有逐一讀 stream 變數的指派。
- Borland stdio 的標準串流在資料段是 20 byte 的 `FILE` 陣列：stdin 在 `62FF:013C`（線性 `6312C`，`fd＝0`，旗標 `0209h`），stdout 在 `63140`（`fd＝1`），stderr 在 `63154`（`fd＝2`，IDA 名稱 `stru_63154`）。對 `6312C` 至 `6313F` 的 xref 只來自 `__setupio`（CRT 初始化，`1166A`、`1167F`、`1168F`）。遊戲程式碼沒有任何指向 stdin 或 stdout `FILE` 的參照；stderr 有 3 處把 `stru_63154` 當 `stream` 參數（`255F4`、`25B58`、`25C1C`）。所以經 stdio 讀 stdin 的路徑不存在（限於直接取址）。
- `_sscanf` 1 處（`284E9`，剖析 `BLASTER` 環境變數字串），`_fread` 4 處（聲音檔，`285B2` 等）。
- 映像內沒有字串 `CON`、`con`、`/dev`。
- 滑鼠：`int 33h` 功能 0Ch 只有一個呼叫點（`295F2`），`CX＝0`，即關閉使用者處理常式。

## 5. 問題 2：呼叫者與回傳值用法

### 5.1 `sub_19623`（getch）

呼叫點 5 處（IDA 的 xref 與原始位元組 `9A 23 96 00 10` 都是 5 處，一致）。沒有資料 xref，沒有 `EA` 遠跳，沒有近呼叫。

| 呼叫點（線性、`sel:off`） | 所在函式 | 情境 | 回傳值 |
|---|---|---|---|
| `21A33`、`1F33:2703` | `sub_21A18`（`1F33:26E8`） | `printf("\x1B[1;1H%s ", 訊息)` 後等鍵。3 個呼叫者 `sub_20BC6`（`Can't alloc BombPattern`）、`sub_21906`、`sub_2198F` 都在配置失敗分支 | 由 `sub_21A18` 回傳，3 個呼叫者都是 `add sp,4` 後 `jmp`，不讀 `AX` |
| `25838`、`24FF:0848` | `sub_25806` | `Can't open file in hloadGraph` 之後 | 下一道指令 `mov ax,0FFFFh` 覆寫 |
| `2586E`、`24FF:087E` | `sub_25806` | `not include in file fno=%d ...` 之後 | 下一道指令 `mov ax,0FFFEh` 覆寫 |
| `25C64`、`24FF:0C74` | `sub_25BE7` | `contents=%d` 除錯訊息之後。進入條件是 `cmp [bp+var_2],3Ch` 後 `jg`，比的是內容數，不是鍵值 | 後接 `printf`，`AX` 未讀 |
| `28131`、`27C5:04E1` | `sub_28104` | `restore error %d` 之後（`si` 超出範圍時） | 後接 `mov bx,si`，`AX` 未讀 |

`sub_21A18` 的 3 個呼叫者（`sub_20BC6`、`sub_21906`、`sub_2198F`）都在「配置結果為空指標」的分支（`or ax, es:word_...` 為零才進入，`jnz` 跳過）。三者在同一函式後段各以 `Bomb.mrg`、`fchar.mrg`、`item.mrg` 呼叫 `sub_25BE7`。後兩者的訊息字串（`unk_3AE42`、`unk_3ABF2`）沒有解碼。

### 5.2 `_kbhit`（`1000:964F`）

0 個 xref（程式碼與資料），原始位元組 `9A 4F 96 00 10`、`EA 4F 96 00 10`、`4F 96 00 10` 都是 0。沒有被任何東西呼叫。

### 5.3 `sub_29BAB`（`29BA:000B`）

呼叫點 2 處（xref 與原始位元組 `9A 0B 00 BA 29` 一致）。

| 呼叫點 | 所在函式 | 說明 |
|---|---|---|
| `19B90`、`1975:0440` | `sub_19ADC`（`1975:038C`） | 結束序列：`sub_2E7DA`（還原 INT 1Ch）、`sub_29BAB`、`sub_297AD`（還原 INT 6）、`sub_29C2A`（還原 INT 24h）等，最後 `push 1`、`call _exit`（`19BB3`、`19BB5`）。`sub_19ADC` 的呼叫者是 ovr380 的 `sub_7DA63`（`7DB02`，`cmp ax,1` 為真時） |
| `77125`、`76B6:05C5` | `sub_770B6`（ovr376，`76B6:0556`） | 同樣的還原序列，之後以 `sub_34A9A(0,0)` 的結果決定迴圈或 `push 0`、`call _exit`（`7716C`、`7716E`）。經 stub 別名 `sub_62A40` 由 ovr368 的 `sub_66AB6`（`67200`）呼叫 |

`sub_29BAB` 的內容：

```
push bp; mov bp,sp; push ds; mov ax,583Ah; mov ds,ax; push ds
L: mov ah,0Bh; int 21h; or al,al; jz done
   mov ah,8; int 21h; jmp L        ; AH=08 讀到的值丟棄
done: xor ax,ax; mov ds,ax; and word ptr ds:500h,0FFDFh; pop ds; pop ds; pop bp; retf
```

它是「把鍵盤緩衝讀光」的迴圈，只看 `AH=0B` 的 `AL` 是否為 0。遇到 F2 這類擴充鍵時，DOS 先回 `AL＝0`，下一次回掃描碼，兩次都被丟棄。

`sub_19ADC` 與 `sub_770B6` 的結束碼 1 與 0，和 `docs/re/011` 第 2 節的結束碼分類方向一致（假說，未核對呼叫鏈）。

### 5.4 鍵值比較

對全部 code head 搜尋 `cmp`、`sub`、`test`、`and`、`xor` 且運算元為 `3Ch`、`3Dh`、`3Eh`、`3C00h`、`3D00h`、`3E00h` 的指令，共 26 處（`out/dump_all.txt` 的 `grep` 段）。全部與鍵值無關：

| 類別 | 位址（線性） |
|---|---|
| 函式庫：`__unixtodos`、`sub_1301B`（`cmp [bp+arg_0], 3Ch`）、`_getenv`（`cmp byte ptr es:[bx+di], 3Dh`，字元 `=`） | `12E4F`、`12E65`、`131B8`、`131CE`、`14112` |
| 欄位位移 `es:[bx+3Dh]`、`es:[bx+3Eh]`，以及 `sub sp, 3Eh`（配置區域變數） | `1ABD5`、`1ABD9`、`1BCBA`、`1C488`、`1C48F`、`1C4A5`、`7C9C8`、`7C9ED`、`7CAED`、`7FF87`、`8061D`、`838CB`、`78BE1`、`84FDC` |
| 遊戲函式內與 `3Ch` 比較區域變數或 `ax`：`sub_1A49D`、`sub_25BE7`、`sub_7A4BF`、`sub_7A682`、`sub_7DB0F` | `1A50B`、`25C4F`、`7A54D`、`7A558`、`7A6EC`、`7A6F7`、`7DC10` |

已讀過的兩處：

- `sub_25BE7` 的 `25C4F`：比的是檔案內容數（`var_2`），超過 `3Ch` 才印 `contents=%d` 並等鍵。
- `sub_7DB0F`（ovr380）的 `7DC10`：`mov ax, es:word_40747` 後與 `3Ch`、`0B4h`、`258h` 比較，三選一挑 `sprintf` 格式字串，其餘分支也是同樣的「資料值挑格式」。`word_40747` 是 `seg075` 的設定值，不是串流或鍵盤來源。該函式是多路 `switch` 加多個 `sprintf` 的組字串函式。

其餘 3 個遊戲函式（`sub_1A49D`、`sub_7A4BF`、`sub_7A682`）的語意沒有逐一讀。判斷它們與鍵值無關的依據是資料流：5.1 至 5.3 的 7 個呼叫點都不使用讀鍵函式的回傳值，所以沒有鍵值能流到這些比較。

## 6. 問題 3：結論與等級

| 命題 | 等級 | 依據 |
|---|---|---|
| `MAIN.EXE` 讀鍵的指令只有 4 個（`19648`、`19665`、`29BB7`、`29BBF`） | confirmed | 77 個 `int 21h` 逐一解出 `AH`／`AX`，原始位元組搜尋與指令解碼一致；重跑 `tools/ida_fkey_scan.py` 可重現 |
| 沒有 `int 16h`、INT 09h 掛接、埠 60h 讀取、`0040h` 段存取 | confirmed（限已解碼的指令與原始位元組樣式，限制見第 7 節） | 第 4.2 至 4.5 節 |
| 3 個讀鍵函式的全部呼叫點是 7 處，且沒有任何一處使用鍵值 | confirmed | xref、原始位元組搜尋（含資料中的遠指標樣式）、逐處閱讀反組譯 |
| 這 7 處的情境是錯誤等待（5 處）與結束時清鍵盤緩衝（2 處） | 強推論 | 5 處前面都是錯誤訊息的 `printf`（其中 `sub_2198F`、`sub_21906` 的訊息字串沒有解碼）；2 處所在函式以 `_exit` 結尾 |
| F2、F3、F4 不會讓 `MAIN.EXE` 改變行為 | 強推論 | 上列事實加上涵蓋限制；沒有任何已知程式取得鍵值 |
| 保留 F2、F3、F4 的唯一可觀察差異是錯誤等待畫面少了三個可關閉畫面的鍵 | 強推論 | 5 處 getch 是「任何鍵」等待；擴充鍵先以 `00` 位元組使 getch 返回 |
| 遊戲在正常遊玩的任何畫面不讀鍵盤 | 強推論 | 同上。旁證：`docs/re/016` 第 92 行記載，遊戲在不讀鍵盤的畫面不取走按鍵，`Stdin` 因此一直非空；`docs/re/008` 第 25 行記載冷啟動到新遊戲鍵盤中斷送出 0 次 |

## 7. 涵蓋限制與未知

| 項目 | 說明 |
|---|---|
| 靜態分析 | 沒有動態收據。要驗證可在 dosgolem 對上述 4 個 `int 21h` 位址（執行期 `0110:9648`、`0110:9665`、`1ACA:0017`、`1ACA:001F`，依 `docs/re/007` 第 8 節換算）下 `OnCall` 計數，遊玩中預期為 0，結束時才有 `sub_29BAB` 的命中 |
| 未定義位元組 | 全庫 164042 個未定義 byte，集中在資料段（以 `mov ax, seg segNNN` 加 `mov ds, ax` 引用）。32 byte 以上的區間共 335 個，其中 134 個開頭是 `00`／`FF`；開頭是其他值的 201 個，前 40 個的前 12 bytes 看過，是 Big5 文字或表格，其餘 161 個沒有逐一判讀（`out/dump_all.txt` 的 `unkstat`）。這些位元組內沒有 `CD 16`、`CD 21`、`E4 60`、`E5 60` |
| 間接呼叫 | 3 個讀鍵函式的函式指標（遠指標 `23 96 00 10`、`4F 96 00 10`、`0B 00 BA 29`）在整個映像只出現在已知的呼叫指令內。若指標是動態算出（偏移與段分開計算），這個樣式看不到 |
| `_int86` 路徑 | 15 個呼叫點的 `intno` 都是立即值。若有程式碼不經 `_int86`、自組 `CD nn`，只有 `_int86x` 內的一處，已讀 |
| handle 為 0 的讀取 | `sub_2B1A8` 有 36 個呼叫點，其中 34 個的第一個 push（handle）是 `si` 或 `di`（`sub_2B140` 開檔回傳值，失敗時回 `0FFFFh` 且呼叫者先比對，`out/dump_all.txt` 的 `pushargs` 段）。另 2 個（`32078`、`347C5`，組合語言的解壓縮讀取器 `sub_3206A`、`sub_347B8`）的 handle 來自入口參數（`sub_320C1` 的 `[bp+arg_0]`、`sub_3480E` 的 `[bp+arg_4]`），其呼叫者傳的也是 `si`（`pushargs 320C1`、`pushargs 3480E`）。沒有逐一證明每個 `si`／`di` 都來自 `sub_2B140`，所以「沒有讀 CON」是強推論，不是 confirmed。stdio 路徑見 4.6 節 |
| `in al, dx` 的 `DX` | 5 處聲音相關的 `DX` ＝ `word_4D300` 加位移。`word_4D300` 在 `sub_28482` 由 `getenv("BLASTER")` 取得字串，跳過第一個字元後 `sscanf(..., "%x", &word_4D300)`（`284C4`、`284E9`），值在執行期由環境變數決定，沒有逐一推算。位移是 `04h`、`05h`、`06h`、`0Ah`、`0Ch`、`0Eh`（Sound Blaster 寄存器位移），基底若被設成 `0054h` 之類才會碰到埠 60h，屬於使用者設定錯誤 |
| 其他程式 | `OP.EXE` 與 `END.EXE` 在 `workplace/ida/out/int_OP.EXE.json`、`int_END.EXE.json` 各有 `AH=08`、`AH=0B`（`OP.EXE` 另有 `AX=0700`），用法未分析。前端日後若跑 `HR.BAT` 完整啟動鏈，F2、F3、F4 對這兩支的影響：未知。`SIG.COM` 只掛 INT 81h（`docs/re/004` 第 2 節），不掛鍵盤向量 |
| 作業系統層 | 主機側的 DOS 驅動（`ANSI.SYS` 之類）、TSR 與 BIOS 行為不在映像內，不在本普查範圍。錯誤訊息含 ANSI 控制碼 `\x1B[1;1H`，表示作者預期這些路徑有 `ANSI.SYS`，與按鍵無關 |
| AH 回溯 | 回溯是往前最多 14 道指令找 `mov ah/ax`，遇 `call`／`jmp`／`ret` 即停。77 處全部有解，`mov` 與 `int` 之間相隔 0 至 4 道指令（40 處緊鄰，21 處隔 1 道，6 處隔 2 道，9 處隔 3 道，1 處 `_lseek` 隔 4 道）。另外讀過 `sub_2B140`、`sub_2B1A8`、`sub_34A9A`、`sub_35965` 的全文與 18 處前置指令，沒有發現解錯。方法本身仍是啟發式 |

## 8. 與既有文件的出入

處理：`docs/spec/003` 第 7 節與驗收表、`docs/re/013` 的鍵盤一行已改為引用本份；`docs/re/004`、`docs/re/011`、`docs/re/012` 是當時的證據紀錄，句子字面正確，不改。

- `docs/re/004` 第 36 行寫「鍵盤走 DOS 的 `AH=08`、`0B`」，`docs/re/011` 第 22 行與 `docs/spec/003` 第 77 行寫「遊戲只用 `int 21h` 的 `AH=08`、`0B`、`0700` 讀鍵盤」。這些句子指出了服務編號，但讀者容易理解成遊戲玩法會讀鍵。實際只有錯誤等待與結束清空。
- `docs/spec/003` 第 80 行與 `docs/re/013` 第 124 行把「遊戲讀鍵盤的畫面與按鍵」和「前端保留鍵與遊戲按鍵的衝突」列為未普查。本份結果可回答：`MAIN.EXE` 沒有這類畫面，保留鍵不會與遊戲按鍵衝突。
- `docs/re/012` 第 22 行與 `docs/re/011` 第 1 節記載 Esc、Enter、空白經 BIOS 緩衝送入是空操作。本份結果推論（強推論）經 `d.Stdin` 送入同樣沒有玩法效果，除了結束時的清空與錯誤等待。

## 9. 重跑方法

```bash
cd /home/anr2/cht/hr
export HR_IDA_WORK=/home/anr2/cht/hr/workplace/ida-fkey
tools/ida.sh run MAIN.EXE ida_fkey_scan.py
tools/ida.sh run MAIN.EXE ida_fkey_dump.py /work/out/spec_all.txt /work/out/dump_all.txt
```

IDAPython 的 stdout 看不到，exit code 不可信。重跑後檢查 `workplace/ida-fkey/out/` 內檔案存在、非空、時間戳更新。第一個腳本約 25 秒，第二個約 30 秒。`spec_all.txt` 是 `spec_1.txt` 至 `spec_7.txt`、`spec_9.txt` 至 `spec_14.txt` 的串接（`spec_8.txt` 的指令被 `spec_9.txt` 取代，未串入）；`dump_all.txt` 與對應各別 `dump_N.txt` 的串接逐 byte 相同（已 `diff` 驗證）。

`ida_fkey_dump.py` 的指令：`func`、`callers`、`ctx`、`bytes`、`flowdump`、`xrefsto`、`xrefrange`、`grep`、`grepc`、`seqgrep`、`rawpat`、`name`、`unkstat`、`pushargs`。`spec_5.txt` 的 `seqgrep` 條件過鬆（結果 152 筆多為無關的 `mov es, reg`），結論不引用它；ES／DS 設 0 或 40h 的判斷以 `fkey_segzero.tsv` 為準。`spec_13.txt` 的兩個 `name` 查詢（`^stru_6`、`^(_streams|...)`）結果為空，因為 `idautils.Names()` 不含自動命名（`stru_63154` 是自動名稱），不引用；該處改以 `xrefrange` 與 `bytes` 為準。

## 10. 輸出檔（`workplace/ida-fkey/out/`）

| 檔案 | 內容 |
|---|---|
| `fkey_ints.tsv` | 全庫 104 個 `int n` 指令（77 個 `int 21h`），附 `AH`／`AX` 回溯與前置指令 |
| `fkey_inout.tsv` | 769 個 `in`／`out` 指令（8 個 `in`） |
| `fkey_raw.tsv` | 原始位元組樣式 `CD 09`、`CD 16`、`CD 21`、`E4 60`、`E5 60` 的命中與 IDA 狀態 |
| `fkey_segzero.tsv` | 把 `ES`／`DS` 設為 0 或 `40h` 的指令（2 筆） |
| `fkey_scan_meta.txt` | IDA 版本、code head 數、函式數、段落清單與計數 |
| `spec_1.txt` 至 `spec_14.txt`、`spec_all.txt` | 傾印規格檔 |
| `dump_1.txt` 至 `dump_14.txt`、`dump_all.txt` | 傾印結果。`dump_8.txt` 是 `sub_2B1A8` 呼叫者的原始前置指令，被 `pushargs`（`dump_9.txt`）取代，保留備查 |

另有新增的腳本 `tools/ida_fkey_scan.py`、`tools/ida_fkey_dump.py`（在 `tools/`，不在 `workplace/ida-fkey/`）。資料庫與原版副本在 `workplace/ida-fkey/run/`（`MAIN.EXE`、`MAIN.EXE.i64`），已在 `workplace/` 的 gitignore 範圍內。
