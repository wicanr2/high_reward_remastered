# 006 圖像與容器格式

日期：2026-10-03
範圍：`GS`、`PXS`、`MRG`、`GRP`、`BIN`、`PXZ`、`RGB`、`PCX`、`CFONT.15` 的格式與顯示環境。只讀檔案位元組與反組譯，沒有執行原版。
工具：`tools/img/run.sh`（容器內，`python:3.13-alpine` 標準庫；解碼器 `tools/img/hrimg.py`、`decode_all.py`），反組譯用 IDA Pro 9.4（`ida-pro-9.4-idapython:locked-v1`）。
來源：圖像逆向子代理的報告，主代理的核對方式在第 12 節。推論等級：confirmed（位元組或反組譯直接可見，且解碼結果已目視確認）、強推論、假說、未知。

位址寫法：`段:偏移` 是 IDA 選擇子，載入基底段 `0x1000`，線性位址 ＝ 段 × 16 ＋ 偏移，檔案位移 ＝ 線性位址 − `0x10000` ＋ MZ 標頭長（`MAIN.EXE` 18944、`OP.EXE` 與 `END.EXE` 5632）。IDA 段 ＝ dosgolem 執行期段 ＋ `0xEF0`（`MAIN.EXE`）。導覽名稱（`sub_XXXX`）不是證據，證據以位址與 bytes 為準。

## 1. 總覽

| 格式 | 檔數 | 容器 | 壓縮 | 點陣 | 調色盤 | 等級 |
|---|---:|---|---|---|---|---|
| `GS`（`ROLL.GS` 以外） | 20 | u32 長度加 LZSS | LZSS | 5 bytes 標頭加 packed 4bpp | 同名 `.RGB` | confirmed |
| `ROLL.GS` | 1 | u32 長度加 LZSS | LZSS | 無標頭，320 寬逐列平面 | `ROLL.RGB` | confirmed |
| `GMAP.PXS` | 1 | 同 `GS` | LZSS | packed 4bpp，640x400 | MAIN 內建表 | 格式 confirmed，調色盤強推論 |
| `MRG` | 18 個圖像檔，另 `ESPMES.MRG` | u16 計數加 u32 偏移表 | 依項目：無或 LZSS | 精靈（第 4 節） | MAIN 內建表 | 格式 confirmed，調色盤強推論 |
| `ARROW.GRP` | 1 | 8 格精靈串接，步幅 645 | 無 | 32x32 平面加遮罩 | MAIN 內建表 | 格式 confirmed，調色盤強推論 |
| `COIN.BIN` | 1 | 16 格精靈串接，步幅 645 | 無 | 32x32 平面加遮罩 | OP 內用 `OP7.RGB` | 格式 confirmed，調色盤強推論 |
| `PXZ` | 11 | span 表加 u32 長度加 LZSS | LZSS | 640x400 稀疏 packed 4bpp | MAIN 內建表 | 格式 confirmed，調色盤強推論 |
| `RGB` | 21（另 `H-TXT.RGB` 為 0 byte） | 16 色乘 (R,G,B)，每分量 4 位元 | 無 | 調色盤 | 自身 | confirmed |
| `PCX` | 2 | 標準 PCX v5 | RLE | 640x360、640x480，8bpp | 檔尾 768 bytes | confirmed |
| `CFONT.15` | 1 | 13867 字乘 30 bytes | 無 | 16x15 單色 | 無 | confirmed |

解碼結果 615 張 PNG（GS 21、PXS 1、MRG 554、GRP 8、BIN 16、PXZ 11、PCX 2、字型 2），錯誤 0。

## 2. 顯示環境

| 結論 | 等級 | 證據 |
|---|---|---|
| 三支程式都設 VGA 模式 12h（640x480，16 色平面） | confirmed（位元組） | OP `1815:0D6D`、MAIN `24FF:016F`、END `182B:21B1` 皆為 `c6 46 f0 12`，接著 `push 10h`、`call _int86`。dosgolem 執行 `MAIN.EXE` 的收據同樣是模式 12h（`docs/re/008`） |
| 屬性暫存器 6、8 至 15 改成恆等映射，像素值 0 至 15 直接對到 DAC 0 至 15 | confirmed | OP `1815:0D85` 至 `0DCB`、MAIN `24FF:0184` 至 `01CA` |
| 遊戲畫面是 640x400，放在 VRAM 第 40 列起（`A000:0C80`），上下各留 40 列 | 常數 confirmed；「每個畫面都這樣放」強推論 | 所有讀過的繪圖常式都以 `A0C8h` 為段（OP `1A4C:00C2`、END `182B:1A8C`、MAIN `2B47:00AA`、`323A:014C`），列寬 80 bytes。dosgolem 的畫面收據一致（`ES=A0C8`，畫面上下各有黑邊） |
| DAC 值 ＝ 4 位元分量 乘 0x87 右移 5 | confirmed | OP `1B56:00DD`、MAIN `29C4:00E8` |

PNG 的 8 位元色值 ＝ `(d << 2) | (d >> 4)`，d 是上式的 6 位元 DAC 值。

## 3. LZSS（所有壓縮格式共用）

| 參數 | 值 | 證據 |
|---|---|---|
| 開頭 | u32 小端，解壓後長度 | OP `1A75:0D56` 至 `0D6E` |
| 環狀緩衝 | 1024 bytes，初值 0 | OP `1A75:0D4C`；索引 `and 3FFh` |
| 寫入起點 | 0x3BE | OP `1A75:0D74` |
| 旗標 | 1 byte 管 8 項，LSB 先，1 ＝ 字面值 | OP `1A75:0DBF` 至 `0DCC` |
| 參照 | 2 bytes `b1 b2`：位置 ＝ `b1 \| (b2 & 0xC0) << 2`，長度 ＝ `(b2 & 0x3F) + 3` | OP `1A75:0DCE` 至 `0DE4` |
| 複製 | 逐 byte 從環讀出並寫回環與輸出，允許與寫入位置重疊 | OP `1A75:0DF9` 至 `0E0E` |

重現步驟：讀 u32 `total`；`ring ＝ [0]*1024`，`r ＝ 0x3BE`；每 8 項讀一個旗標 byte；位元為 1 讀 1 byte 寫入 `ring[r]` 與輸出；位元為 0 讀 `b1 b2` 依上表複製 `len` 次；輸出滿 `total` 停止。實作：`hrimg.lzss_decompress`。

驗證（confirmed）：21 個 `GS`、`GMAP.PXS`、163 個 LZSS 的 `MRG` 項目，消耗長度都恰好等於檔案或項目長度，沒有溢出；11 個 `PXZ` 的 LZSS 恰好吃到檔尾。已讀過的變體：OP `1A75:0D32`、END `1BD0:040C`、MAIN `2FB2:25A1`、`2E92:0414`/`066A`、`323A:000A`；MAIN `33AD:0D3E` 只看到同樣的環狀複製，未逐行讀。

## 4. 精靈點陣（5 bytes 標頭）

`MRG` 項目、`GRP`、`BIN` 的每一格，以及 `GS` 解壓後的資料，都以同一個標頭開始：u16 寬（像素，8 的倍數）、u16 高、u8 格式旗標。證據：MAIN `2B47:002E`、`003A`、`0063`；OP `1A4C:0020`、`002A`。

平面 k 是像素值的第 k 位元，每個 byte 的 bit 7 是最左邊的像素。packed 格式每 byte 存兩個像素，高 4 位元在左。

| 來源 | 旗標 | 每列資料 | 繪圖常式 | 等級 |
|---|---|---|---|---|
| 未壓縮 | bit0 ＝ 0 | 平面 0、1、2、3，各 w/8 bytes | MAIN `2B47:00A5` | confirmed（`NOWEAPON.MRG`） |
| 未壓縮 | bit0 ＝ 1 | 平面 0、1、2、3、遮罩 | MAIN `2B47:0285`（`02A5` 先跳過 4 個平面讀遮罩） | confirmed（ITEM、KOMA、BC32 等） |
| LZSS | 0x80 | packed 4bpp，w/2 bytes | OP `1A4C:0011`、MAIN `348F:0005` | confirmed（GS、FACE、VS） |
| LZSS | 0 | 平面 0、1、2、3 | MAIN `2E92:0414` | confirmed（CANNON、PANZER、PLANE） |
| LZSS | 非 0 | 遮罩、平面 0、1、2、3 | MAIN `2E92:066A` | confirmed（BSTAGE） |

遮罩：位元 1 ＝ 不透明，0 ＝ 保留背景（MAIN `2B47:04FE` 設寫入模式 3）。未壓縮精靈的遮罩在列尾，LZSS 精靈的遮罩在列首。資料佐證：11 個有遮罩的未壓縮 `MRG` 檔加 `GRP`、`BIN`，「有顏色但遮罩為 0」的像素全為 0；BSTAGE 以列首解讀為 0。PNG 輸出：有遮罩的精靈與 `PXZ` 未覆蓋處使用 17 色調色盤，索引 16 在 `tRNS` 設為透明。

## 5. GS 與 PXS

| 位移 | 內容 | 例：`ED0.GS` `05 f4 01 00 3f 80 02 90 01 80` |
|---:|---|---|
| 0 | u32 解壓後長度 | `0x0001F405` ＝ 128005 ＝ 5 ＋ 640x400/2 |
| 4 | LZSS 第一個旗標 byte | `0x3F`：前 6 項是字面值 |
| 5 至 9 | 字面值：解壓後標頭 w、h、旗標 | 640、400、`0x80` |

| 檔案 | 解壓後 | 調色盤 | 等級 |
|---|---|---|---|
| `IMG`、`ED0` 至 `ED7`、`OP10` | 640x400，0x80 | 同名 `.RGB` | confirmed |
| `OP0` 至 `OP7` | 320x400，0x80 | 同名 `.RGB` | confirmed |
| `OP8` | 640x100，0x80 | `OP8.RGB` | confirmed |
| `OP9` | 128x64，0x80（版權字樣） | `OP9.RGB`，只憑檔名；三個 EXE 都沒有 `OP9` 字串 | 格式 confirmed，配對為假說，讀取端未知 |
| `ROLL` | 320000 bytes，無標頭，320x2000，每列 160 bytes ＝ 平面 0 至 3 各 40 bytes | `ROLL.RGB` | confirmed（END `182B:196D`、`1A5D`、`1BAF`） |
| `GMAP.PXS` | 640x400，0x80 | MAIN 內建表 | 格式 confirmed（MAIN `2FB2:265B`），調色盤強推論 |

GS 與 RGB 的配對由 OP、END 每組載入呼叫點逐一查出（`IMG`、`OP0` 至 `OP8`、`OP10`、`ED0` 至 `ED7`、`ROLL`），confirmed；`OP9.GS` 例外。

## 6. MRG

容器（confirmed，MAIN `24FF:0B7A` 至 `0C4A`）：u16 N，其後 N−1 個 u32 偏移，第一個偏移 ＝ 2 ＋ 4(N−1)；項目 i ＝ `[off[i], off[i+1])`，共 N−2 項，最後一個偏移是資料結尾。項目是未壓縮精靈或 LZSS 精靈：若 `5 + w/8 × h × (4 或 5)` 等於項目長度即未壓縮，否則 LZSS 且必須恰好吃完項目。

| 檔案 | N | 項目 | 內容 |
|---|---:|---|---|
| `BC32` | 143 | 118 未壓縮（64x32 等，有遮罩）加 23 個長度 0 | 戰鬥人物動作 |
| `BOMB` | 6 | 4 未壓縮 32x32 遮罩 | 爆炸 |
| `BSTAGE` | 10 | 8 LZSS，576x176，旗標 1 | 戰鬥舞台地面 |
| `BUTTON` | 23 | 21 未壓縮（24x24、64x24、16x16、32x32） | 介面按鈕 |
| `CANNON`、`PANZER`、`PLANE` | 10 | 各 8 LZSS，272x88，旗標 0 | 兵器圖 |
| `CURSOR` | 3 | 1 未壓縮 24x24 遮罩 | 游標 |
| `DEAD` | 21 | 19 未壓縮（64x32、16x16） | 煙霧特效 |
| `EXIST` | 5 | 3 未壓縮 16x16 加表外 1 格（165 bytes） | 旗幟 |
| `FACE` | 108 | 106 LZSS，128x160，0x80 | 人物臉 |
| `FCHAR` | 28 | 26 未壓縮 32x32 | 人物小圖 |
| `ITEM` | 62 | 60 未壓縮 24x24，遮罩全為 1 | 道具圖示 |
| `KOMA` | 74 | 72 未壓縮 24x24 | 地圖棋子 |
| `LTIME` | 15 | 13 未壓縮（尺寸不一） | 時間指針 |
| `NOWEAPON` | 3 | 1 未壓縮 272x88，旗標 0 | 無兵器底圖 |
| `SPOINT` | 54 | 52 未壓縮（48x36 等） | 據點圖示 |
| `VS` | 27 | 25 LZSS，256x160，0x80 | 對戰畫面 |
| `ESPMES` | 126 | 巢狀 MRG，內容是 Big5 文字 | 非圖像 |

邊界：`EXIST.MRG` 最後一個偏移之後還有一格 165 bytes 的 16x16 遮罩精靈，兩條載入路徑都讀不到（位元組事實 confirmed，用途未知）；`BC32.MRG` 有 23 個長度 0 的項目。

## 7. PXZ（戰場地圖）

u32 A（span 表長度）；A bytes 的 u16 成對 (s, c) 表；u32 解壓後長度（解碼器略過）；LZSS 串流（packed 4bpp）。解碼（MAIN `323A:000A`）：`di ＝ 0`；逐對讀 (s, c)，`di += s + 2`，`di >= 32000` 結束；接著畫 `(c >> 1) + 1` 組，每組 8 bytes ＝ 16 像素，畫在 VRAM 位移 `di`（x ＝ (di mod 80) 乘 8，y ＝ di / 80），每組 `di += 2`。畫面 640x400，span 以外不寫。11 檔都滿足「組數乘 8 ＝ u32 長度」、LZSS 恰好吃到檔尾、最後 `di ＝ 32000`。confirmed。span 以外的畫面內容未知，PNG 輸出為透明。

## 8. GRP、BIN、RGB、PCX、CFONT

- `ARROW.GRP`：8 格 32x32 遮罩精靈，每格 645 bytes（5 ＋ 4x32x5），MAIN `2404:00F1`（`imul ax, 285h`）。`COIN.BIN`：16 格同規格，OP `1A0E:004C`。confirmed。`COIN.BIN` 在 OP 用 `OP7.RGB`（強推論），在 END 用哪個調色盤未知。
- `RGB`：48 bytes ＝ 16 色乘 (R, G, B)，每分量低 4 位元。OP `18F3:0E11` 至 `0E44`。confirmed。
- MAIN 內建調色盤（強推論）：`MAIN.EXE` 檔案位移 `0x4CDCA`（`583A:002A`）的 16 個 u16，格式 `0x0RGB`：`0000 004A 00AC 0440 08A0 0B90 0DE6 0F32 0A50 0F86 0988 0DCC 0FA7 0FB8 0FC9 0FFF`。理由：整個 `MAIN.EXE` 只有一處 `ba c8 03`（`29C4:00DB`，DAC 寫入常式），這張表的 16 個參照全是 push；MAIN 讀的圖以它輸出，畫面色調合理，且與 dosgolem 實跑的遊戲畫面（`docs/re/008`）一致。
- `PCX`：標準 v5 RLE 8bpp，`RAIN.PCX` 640x360、`H-TXT.PCX` 640x480，調色盤在檔尾 `0x0C` 之後 768 bytes。confirmed。顯示它們的 `PSH.EXE`（LE）沒有分析。
- `CFONT.15`：每字 30 bytes ＝ 15 列乘 u16 大端，bit 15 在左，字寬 16。Big5 轉字號的公式在 OP `1C8F:05A3` 至 `06F7`：`t' ＝ t − 0x40`（t ≤ 0x7E）否則 `t − 0x62`；lead ≤ A3 為 `(lead−A1)×157 + t'`；C6A1 至 C8FE 為 `(lead−C6)×157 + t' − 0x3F + 0x198`；其餘 `(lead−A4)×157 + t' − (lead ≥ C9 ? 0x198 : 0) + 0x305`；檔案位移 ＝ 字號 乘 30。F9FE 算出 13866，恰為最後一字。confirmed。

## 9. 與 `001-source-intake.md` 的差異

| 001 的敘述 | 本次結果 |
|---|---|
| GS 首位元組 `05`、共用檔頭 `05 F4 01 00 3F 80 02 90` | 前 4 bytes 是 u32 解壓長度（等於 5 加像素 bytes，所以低位元組恰為 05），接著 LZSS 旗標，再接字面值 w、h |
| `ROLL.GS` 檔頭不同 | 解壓後沒有 5 bytes 標頭 |
| GRP/BIN：u16 寬、u16 高、u32 計數 | 不成立：每格各帶 5 bytes 標頭，步幅 645 |
| RGB：16 色乘 3 分量 | 成立，分量 4 位元，順序 R、G、B |
| CFONT：15x15 | 字寬 16、高 15 |
| PXZ 前 4 bytes 為 1550 至 1986 的 u32 | span 表長度 |
| MRG：偏移表在檔頭 | 成立，另確認項目數是 N−2 |

## 10. 未解

| 項目 | 狀態 |
|---|---|
| `OP9.GS` 的讀取端與調色盤 | 讀取端未知，配對為假說 |
| `COIN.BIN` 在 END 的調色盤 | 未知 |
| MAIN 執行中是否換過基底調色盤 | 強推論為否（只做了靜態分析，執行期收據可驗） |
| `PXZ` span 外的畫面內容 | 未知 |
| `EXIST.MRG` 表外第 4 格 | 用途未知 |
| `PSH.EXE` 顯示 PCX 的模式 | 未知 |
| 各圖出現在哪個畫面、用什麼座標 | 未做（HD 替換規格需要） |

## 11. 檔案

`tools/img/`：`hrimg.py`（LZSS、精靈、PXZ、PCX、調色盤、字型索引、PNG 寫出）、`decode_all.py`、`run.sh`。輸出在 `workplace/re-img/out/`（原版美術的衍生物，不進 repo）；`inventory.tsv`（615 列）與 `out/decode_log.txt`（輸入雜湊、計數）在同處。

## 12. 主代理的核對

- 重跑 `tools/img/run.sh`：615 張 PNG，與子代理的輸出逐檔相同。
- 目視：`FACE.MRG_000` 與 dosgolem 實跑畫面中莫洛迪南多的頭像相同；`MAP01.PXZ` 是等角視角的戰場地圖，左上角有小地圖。
- 顯示環境與 dosgolem 的實跑收據一致（模式 12h、`ES=A0C8`、畫面上下黑邊）。
- 未獨立重做的部分：各繪圖常式的逐行讀碼（採信子代理的位址與 bytes）。
