# 008 dosgolem 冷啟動收據（M3）

日期：2026-10-03
範圍：`MAIN.EXE`（對應 jsdos 版 autoexec 的 `main`）在 dosgolem 內的執行：標題選單、新遊戲的第一個畫面、閒置長跑。
引擎：`workplace/dosgolem` 本地分支 `hr`（commit `16d87e5` 起，CPU 規格 `docs/spec/001-cpu-386-real-mode-forms` 為 CONFORMED，收據 `docs/re/005`）。
工具：`tools/dosgolem.sh`（`probe`、`soak`）。畫面存成 PNG 只留在 `workplace/out/`（原版美術的衍生物，不進 repo），這裡記錄 SHA-256。
推論等級：confirmed（可由指令重跑並比對雜湊）、強推論、假說、未知。

## 1. 收據

| 收據 | 命令 | 結果 | 畫面雜湊（PNG，SHA-256） |
|---|---|---|---|
| A 標題選單 | `probe -exe MAIN.EXE -steps 30000000 -dump-screen-png` | 程式活著；視訊模式 12h；計時器送出 47 次；平面寫入模式 0 使用 2314358 次、模式 3 使用 277185 次；畫面是世界地圖加三行的選單（含新遊戲與讀取遊戲兩個項目），游標是遊戲自己畫的 | `112cd52c2060d430c533b98ef8228ecc86063fce53a3db781b6047c4a3a86a6e` |
| B 新遊戲第一畫面 | `probe -exe MAIN.EXE -steps 90000000 -clicks "35000000:312:211" -dump-screen-png` | 在第 3500 萬道指令於 (312, 211) 按左鍵（選單的新遊戲項目），到第 9000 萬道時畫面是遊戲地圖，左上角角色頭像加對白框，右下角負債總額 1000000、償還額度 5000、所持金 8000 | `853a695340271b1e2540702d6d5f1e78f3807e230c666a181e3985097879adaf` |

決定性：收據 A、B 各重跑 2 次，畫面雜湊逐位元相同（B 另與第一次的輸出相同）。confirmed。

視訊：畫面 640x480，模式 12h；遊戲畫面 640x400，上下各 40 列黑邊，與 `docs/re/006` 第 2 節的靜態結論一致。標題選單的字型與對白文字由 `CFONT.15` 繪出，顯示正常。

## 2. 服務與缺口

- 90M 道指令內，探針回報的「沒實作的服務」只有一種：`int 10h AH=01 AL=4A`（設定游標形狀，一次）。不影響畫面與流程。
- 檔案服務：`MAIN.EXE` 自己讀 overlay（`0xC6D0` 預載，`docs/re/007`）；之後開啟 `CFONT.15`、`DISK_B.INF`、`DISK_C.INF`（磁片檢查，開了即關）、`PLATE1.PAT`、`PLATE2.PAT`、`LTIME.MRG`、`BOMB.MRG`、`KOMA.MRG`、`CURSOR.MRG`、`GMAP.PXS`、音樂檔等。沒有檔案找不到的記錄。
- 滑鼠：`int 33h` 功能 0、3、4、5、6、7、8 都有被呼叫（功能 3 在 90M 道內約 4771 次輪詢），dosgolem 已支援。
- 鍵盤中斷送出 0 次：這條路徑沒有用輸入驅動，標題與新遊戲只用滑鼠。
- `HR.BAT` 的 `PSH` 顯示 PCX、`SIG.COM` 常駐、`OP.EXE` 片頭、`END.EXE` 片尾這四步沒有走。jsdos 版只跑 `main`，所以目前的收據對應 jsdos 版。

## 3. 閒置長跑（M4 的第一個觀察）

`tools/dosgolem.sh soak -steps 400000000 -input none`（新遊戲第一畫面後不再輸入）：4 億道指令，30 秒（約 1300 萬道每秒），**沒有當機**，停機原因為跑滿步數。`report.tsv` 的觀察：

| 觀察 | 數值 | 等級 |
|---|---|---|
| 音樂檔（`NATIONAL.MID`、`SCOUT.MID`）被反覆開啟 | 每 5000 萬道指令約 3300 次（約每 1.5 萬道一次），且每次都關閉 | confirmed |
| 開著的檔案代號數 | 前段穩定為 2，第 3 億道之後為 3 | confirmed（數值）；是否為洩漏：未知，需要更長的觀察 |
| 配置游標（`freeSeg`） | `7C41`，第 3 億道之後 `7C81`（增加 `0x40` 段落，與畫面雜湊變動同時） | confirmed（數值）；成因未知 |
| EMS | 1 個控制代碼、4 頁，全程不變 | confirmed |

這些是「看起來值得追」的線索，不是結論。當機的判準與長跑方法見 `docs/spec`（M4 規格尚未寫）；`CTMIDI.DRV` 不在原版壓縮檔內，音樂檔的重複開啟是否與它缺席有關，未知。

## 4. 重跑

```text
tools/dosgolem.sh build
tools/dosgolem.sh probe -exe /orig/orig/MAIN.EXE -root /orig/orig -steps 90000000 -clicks "35000000:312:211" -dump-screen-png /out/x.png
tools/dosgolem.sh soak -steps 400000000 -report-every 50000000 -out /out/soak1 -input none
```

## 5. 尚未涵蓋

- `HR.BAT` 完整啟動鏈與 `SIG.COM`（`int 81h`）。
- DOSBox-X 的雙側交叉驗證。
- 鍵盤輸入路徑、存檔與讀檔（`GAMEFILE.000` 至 `.004`、`复件 GAMEFILE.001`）。
- 進入戰鬥、買賣、事件等遊戲內畫面。
