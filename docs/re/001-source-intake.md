# 001 來源取得與檔案清冊

日期：2026-10-02
範圍：IDEA.md 第 1 項（取得 jsdos 版原版）與檔案盤點。只記錄標頭與位元組可見的事實，不解讀遊戲語意。
推論等級：confirmed（位元組或腳本輸出直接可見）、強推論、假說、未知。

## 1. 來源

| 項目 | 內容 |
|---|---|
| 頁面 | `https://legacy.dos.zczc.cz/games/%E9%AB%98%E6%8A%A5%E9%85%AC%E6%88%98%E5%B0%86/` |
| 網站識別名 | `高报酬战将`（URL 路徑，簡體字形） |
| 取得日期 | 2026-10-02 |
| 取得方式 | 容器內 Python `urllib`（映像 `python:3.13-alpine`），HTTP 200 |
| 權利人 | 未查證。網站是第三方轉載站，轉載不構成散布授權 |

頁面是 Vue 單頁應用，下載位址由 JS 組出，頁面 HTML 本身沒有連結：

| JS 檔 | SHA-256 | 內容 |
|---|---|---|
| `js/game~game_info.099e7f42.js` | `4bc1a171276ed37bba0e8b0bcfdb3b6bb487f5170424730b10f8458e74a811a2` | `jsdos_binary_url` 為 `${host}/${encodeURIComponent(identifier)}.jsdos.zip`，`binary_url` 為 `${host}/${identifier}.zip` |
| `js/app.c9d074be.js` | `4a98aff3c9a05486f04248cffb79a64088cd6f624d279385051305f720f26803` | 列出主機常數，含 `https://b2.zczc.cz/file/dos-bin`（標為 Cloudflare） |

本次直接使用 `https://b2.zczc.cz/file/dos-bin`。回應標頭的 `Last-Modified` 是下載當下時間（2026-10-02 15:14 GMT），不能當作檔案日期；沒有 `ETag`。

## 2. 兩份壓縮檔

| 檔案 | URL 尾段 | 位元組 | SHA-256 |
|---|---|---:|---|
| `hr_src.jsdos.zip` | `%E9%AB%98%E6%8A%A5%E9%85%AC%E6%88%98%E5%B0%86.jsdos.zip` | 2567596 | `47f6c4780607c319e26430420e43ca813ac7c60afcc156f8a012c86cb719bb4a` |
| `hr_src.zip` | `%E9%AB%98%E6%8A%A5%E9%85%AC%E6%88%98%E5%B0%86.zip` | 2565317 | `bcddffab2157335093f4cbc9beb57868f7479976ab9444dccc10f30523a83850` |

confirmed（`tools/inventory.sh`）：兩份各含 148 個檔案，檔名與逐檔 SHA-256 全部相同。jsdos 版多出 `.jsdos/jsdos.json` 與 `.jsdos/dosbox.conf`。完整清冊（路徑、大小、SHA-256、檔頭 8 bytes）在 `source-inventory.tsv`。重跑方法：`tools/inventory.sh`。

## 3. 缺口與異常（confirmed）

| 項目 | 事實 |
|---|---|
| 零位元組檔 | `ALCOHOL.MID`、`H-TXT.RGB`、`TEMP` |
| `FILELIST` 列出但壓縮檔沒有 | `CTMIDI.DRV` |
| 壓縮檔有但 `FILELIST` 沒列 | `FNAME.DA_`、`INST.BAT`、`复件 GAMEFILE.001` |
| `DISK_D.INF` | `MAIN.EXE`、`OP.EXE`、`END.EXE` 內都有此字串，`FILELIST` 與壓縮檔都沒有此檔（只有 A、B、C、E） |
| `DEARJ` | `INST.BAT` 呼叫 `DEARJ x -vv -y %1*.001`，壓縮檔內沒有 DEARJ |
| `GAMEFILE.000` 至 `.004` | 各 31839 bytes，內容兩兩不同；`复件 GAMEFILE.001` 同為 31839 bytes 但內容與 `GAMEFILE.001` 不同。用途：假說為存檔槽，未驗證 |

## 4. jsdos 設定與啟動鏈（confirmed）

`.jsdos/dosbox.conf` 重點：

| 區段 | 設定 |
|---|---|
| `[dosbox]` | `machine=svga_s3`、`memsize=16` |
| `[cpu]` | `core=auto`、`cputype=auto`、`cycles=auto` |
| `[sblaster]` | `sbtype=sb16`、`sbbase=220`、`irq=7`、`dma=1`、`hdma=5` |
| `[midi]` | `mpu401=intelligent` |
| `[dos]` | `xms=true`、`ems=true`、`umb=true` |
| `[autoexec]` | `mount c .`、`c:`、`main` |

`HR.BAT` 的啟動鏈：`PSH RAIN.PCX`、`PSH H-TXT.PCX`、`sig`、`OP`、（errorlevel 非 0 則結束）`MAIN`、（同上）`END`、`sig /r`。

jsdos 版只執行 `main`，沒有跑 `PSH`、`sig`、`OP`、`END`。

`CONFIG.IBM` 是 IBM DOS/V 的設定範本（`COUNTRY=081,932`、`$FONT.SYS`、`$DISP.SYS`、`KKCFUNC.SYS`），jsdos 設定沒有使用它。它與 Big5 文字檔並存的原因：未知。

## 5. 執行檔（標頭與字串）

| 檔案 | 位元組 | SHA-256 前 16 碼 | confirmed 事實 | 解讀 |
|---|---:|---|---|---|
| `MAIN.EXE` | 539424 | `08ed144e8f8d6e97` | 純 MZ，無 LE、NE、PE 標頭。標頭 1184 段落（18944 bytes），宣告映像結束於檔案位移 361856，載入映像 342912 bytes，重定位 4352 項，`SS:SP=53B0:0080`，`CS:IP=0000:0000`，`min=0000`、`max=FFFF`。位移 361856 起為 `46 42 4F 56`（`FBOV`），後接 177568 bytes。含字串 `Borland C++ - Copyright 1993 Borland Intl.`，以及 `DISK_A.INF` 至 `DISK_E.INF` 與 `B:` 前綴的同組字串。載入映像內 `CD 3F` 原始位元組出現 748 次（未排除誤判） | 強推論：16 位元 real mode 的 Borland C++ 程式，附 overlay。未經反組譯驗證 |
| `OP.EXE` | 140542 | `8154bb80d018210d` | 純 MZ，檔案長度等於標頭宣告長度。含 `Bad_cast`、`Bad_typeid`、`typeinfo` 字串，以及與 `MAIN.EXE` 相同的 `DISK_*.INF` 字串組 | 強推論：同一類 Borland C++ 工具鏈。用途未探 |
| `END.EXE` | 149704 | `7734e3fb0f39fb04` | 純 MZ，檔案長度等於標頭宣告長度。含與 `OP.EXE` 相同的 RTTI 與 `DISK_*.INF` 字串 | 同上 |
| `PSH.EXE` | 58966 | `de1164fa92fd5af3` | MZ stub 10830 bytes，`e_lfanew` 指到 `LE` | 32 位元 Linear Executable（DOS extender 程式）。強推論：PCX 顯示器（依 `HR.BAT` 的命令列） |
| `DOS4GW.EXE` | 265420 | `dd9f4f342533f995` | 含 `DOS/4G` 字串，位移 62580 起為 `BW` 簽章 | 強推論：DOS/4GW extender，與 `PSH.EXE` 配套 |
| `SIG.COM` | 1172 | `512f0feeb6835cf9` | 字串 `Install Signal Socket`、`Remove Signal Socket`、`$SIG version 1.0 94/04/25 00:00:00`、`usage  :sig [-\|/option]`、`-R)emove`。`MAIN.EXE`、`OP.EXE`、`END.EXE` 內沒有含 `SIG` 的字串 | 強推論：常駐程式。`MAIN` 是否依賴它：未知 |
| `QUIT.EXE`、`CFG.EXE` | 6092、6072 | `8c93ac4cea93472a`、`4201486bcb5a8786` | 純 MZ | 用途未探 |

`MAIN.EXE` 的 `FBOV` 區：標頭後第一個 u32 為 `0x0002B590`（177552），等於 `FBOV` 區總長 177568 減 16。算術吻合，欄位語意未驗證。

## 6. 資料檔家族（檔頭 8 bytes 見 `source-inventory.tsv`）

| 副檔名 | 數量 | confirmed 事實 | 推論 |
|---|---:|---|---|
| `MID` | 28 | 27 檔以 `MThd` 開頭（另 1 檔 `ALCOHOL.MID` 為 0 byte） | 標準 MIDI 檔 |
| `PCX` | 2 | `RAIN.PCX`、`H-TXT.PCX` 檔頭 `0A 05 01 08` | PCX v5、RLE、8 bpp |
| `TXT` | 7 | `OP.TXT`、`OP0.TXT`、`OP1.TXT` 以 Big5 嚴格解碼可得通順繁體中文。`OP0.TXT`、`OP1.TXT` 以 GBK、Shift_JIS 嚴格解碼失敗；`OP.TXT` 以 cp932 可解碼，但結果是半形假名的無意義字串。`OP2` 至 `OP5` 未逐檔解碼 | 文字為 Big5 |
| `MES` | 5 | 檔頭是小端整數表。`COUNTRY.MES` 的表之後可讀出 Big5 字串 | 強推論：整數表加 Big5 字串。其餘 4 檔未逐檔驗證 |
| `MRG` | 19 | 檔頭為 u16 計數 N，其後 u32 的值皆等於 `2 + 4 × (N - 1)`，19 檔逐一核對吻合 | 強推論：打包檔，偏移表在檔頭。表項範圍未驗證 |
| `GS` | 21 | 20 檔首位元組為 `05`；`ED0` 至 `ED6`、`IMG.GS` 與 `GMAP.PXS` 共用同一組檔頭 `05 F4 01 00 3F 80 02 90`（`ED7.GS` 只有第 5 byte 為 `BF`）；`ROLL.GS` 檔頭不同 | 圖像容器。格式未知 |
| `PXZ`、`PXS` | 11、1 | `MAP01` 至 `MAP11.PXZ` 檔頭前 4 bytes 為小端 u32，介於 1550 與 1986 | 疑為地圖。格式未知 |
| `RGB` | 22 | 21 檔為 48 bytes，`H-TXT.RGB` 為 0 byte | 假說：16 色乘 3 分量的色盤。未驗證 |
| `GRP`、`BIN` | 1、1 | `ARROW.GRP`、`COIN.BIN` 檔頭同為 `20 00 20 00 01 00 00 00` | 假說：u16 寬、u16 高、u32 計數。未驗證 |
| `PCM` | 1 | `SOUND_E.PCM` 前 4 bytes 為 u32 `0x000047D4`（18388），等於檔案長度，其後為 `80` 重複 | 強推論：附長度標頭的 8 位元無號 PCM |
| `15` | 1 | `CFONT.15` 為 416010 bytes，等於 30 × 13867 | 假說：每字 30 bytes 的 15×15 點陣字型。未驗證 |
| `TBL`、`PAT`、`INF`、`DAT`、`DA_` | 1、2、4、1、1 | `INF` 為 4 bytes（字母、`0D 0A`、`1A`）；`FNAME.DAT`、`FNAME.DA_` 為 158 bytes 文字，開頭 `0 2007/0` | `TBL`、`PAT` 格式未知 |

## 7. 未知清單

- `FBOV` 區的欄位與 overlay 呼叫慣例（`INT 3Fh` stub 的格式）。
- `SIG.COM` 的功能，以及 `MAIN.EXE` 是否呼叫它。
- `MAIN.EXE`、`OP.EXE`、`END.EXE` 對 `DISK_*.INF` 的檢查行為，以及 `DISK_D.INF`、`CTMIDI.DRV` 缺檔的影響。
- 所有圖像與地圖容器（`GS`、`PXZ`、`PXS`、`GRP`、`BIN`、`MRG` 內容）的格式。
- 遊戲執行時的視訊模式與解析度。
