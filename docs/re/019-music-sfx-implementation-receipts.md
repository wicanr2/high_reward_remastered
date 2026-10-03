# 019 音樂與音效播放的實作收據

日期：2026-10-03
狀態：收據（`docs/spec/007` 的實作驗證）。規格仍是 DRAFT（第三版，第三輪審查尚未做）；收據記錄的是目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱（見第 7 節）。
輸入：`MAIN.EXE` SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`；dosgolem 分支 `hr` 基準提交 `223ed99`，實作為其上的未提交修改（提交後補提交號）；Go 容器 `golang:1.24-bookworm`（`tools/dosgolem.sh`）、`eob-remake-go:1.26.7-ebiten2.9.9`（`tools/play.sh`）；`linux/amd64`。

## 1. 單元測試（不需原版）

| 套件 | 重跑 | 結果 |
|---|---|---|
| `apps/hr/sound` | `CGO_ENABLED=1 tools/dosgolem.sh go test -race -count=1 ./apps/hr/sound/` | 通過（SMF 解析與拒絕、起音時序對獨立公式、休止與音符、基頻、聲部相加、打擊樂瞬態、引擎生命週期、淡出與佇列、世代 CAS、音效內插、靜音、`Read` 零配置、並行、`NullSink`） |
| `apps/hr/runtime`（不需原版的部分） | `tools/play.sh test-diag`，`HR_TEST_RUN=Sound` | `TestSoundPostDecodesArguments`、`StatusPatchesAXOnly`、`HooksIgnoreNonEntries`、`DisabledWhenFlagNonzero` 通過 |
| `apps/hr/hd`（theme 支援） | `CGO_ENABLED=1 tools/dosgolem.sh go test -race -count=1 -run 'CheckTheme\|Preload\|LoadAssets' ./apps/hr/hd/` | 通過 |
| `apps/hr/play` | `tools/play.sh test-play` | 通過（含保留鍵表不含 F3、`TestAudioAlwaysHasAPuller`） |
| Windows 編譯 | `tools/play.sh build-cross` | `windows/amd64`、`CGO_ENABLED=0` 通過；macOS 需要 osxcross，未在此驗證 |

## 2. runtime 掛鉤（需原版）

重跑：`HR_TEST_RUN=Sound HR_SOAK_STATE=/state/soak/ck-001500000000.state tools/play.sh test-diag`（`workplace/out/soak-s0/ck-001500000000.state`，`docs/re/010` 的取樣狀態檔）。

| 測試 | 內容 | 結果 |
|---|---|---|
| `TestSoundHooksFailClosedOnBytes` | 10 個檢查點各自被改動最後一個比對位元組後 `newSoundHooks` 失敗並點名；原版映像通過 | 通過 |
| `TestSoundHooksDoNotChangeTheGame` | `Playing()` 恆為假的 Sink 與無 Sink，冷啟動 90M 步（35M 步點新遊戲）後畫面 PNG 雜湊、CPU 暫存器、1 MiB 記憶體逐位元相同；`Starts ＝ 4774`、`Fades ＝ 4774`、`Queries ＝ 9546`、`Stops ＝ 0`、`SFX ＝ 0` | 通過 |
| `TestSoundPlayingSuppressesReload` | 30M 步：Playing 恆假 1706 次 `MusicStart`（與 `docs/re/010` 第 5 節 E0b 的獨立收據同為 1706）；DOS 層實際開 `SCOUT.MID` 的次數等於 1706（獨立 oracle）；跟隨型 Sink 1 次且 DOS 層開檔 1 次；Playing 恆真（卡住的驅動）0 次，`CS:IP` 停在 `192B:027E`（`0274` 內） | 通過 |
| `TestSoundNaturalEndReplays` | 跟隨型 Sink 在開機後令 `Playing()` 變假，遊戲在 20M 步內再次 `MusicStart`，位元組仍是 `SCOUT.MID` | 通過 |
| `TestSoundPlayMusicPathFromState` | 載入取樣狀態檔（目前曲號 14）後，音樂事件順序為 `fade`、`start`（點擊音 `sfx` 可能穿插），`start` 的資料是 `NATIONAL.MID`，跟隨型 Sink 回報播放中後不再重載，曲號維持 14 | 通過 |
| `TestSoundStateFilesAreClean` | Sink 開啟時 `3E24:01BA ＝ 0`；存下的狀態檔由無 Sink 的 Session 載入後 10M 步內仍有開檔（遊戲不卡在 `PlayMusic` 的等待迴圈） | 通過 |

### 效能（成對、同行程、150 對、每塊 1M 步，`HR_BENCH_OVERHEAD=1`）

「聲音」欄是前端預設組合（診斷加 HD 掛鉤）加聲音掛鉤（跟隨型 Sink、不保留資料）對同組合不加聲音掛鉤的使用者 CPU 時間比（修剪平均 ± 標準誤）。有 Sink 時遊戲不再重複讀 MID，所以比值是「掛鉤成本減去省下的重複讀檔」的淨值，不是純掛鉤成本。

| 場景 | 診斷開 ÷ NoDiag（對照，`docs/spec/005`） | 聲音掛鉤 ÷ 無聲音掛鉤 |
|---|---:|---:|
| 冷啟動（HD 掛鉤） | 0.985 ± 0.007 | 0.862 ± 0.006 |
| 戰鬥佈陣（HD 掛鉤） | 0.985 ± 0.006 | 0.934 ± 0.005 |

另一次量測（Sink 的 `Playing()` 恆為假，遊戲路徑與無 Sink 相同，且 Sink 保留每份 20 KB 的複本）冷啟動比值為 1.090 ± 0.004，超過閘門 1.05。這個情境只出現在 Sink 一直回報「沒在播」時（等於原版旗標 0 的重複讀檔路徑），成本主要是每 14.7K 步一次的 `MusicStart` 複製 20000 bytes 與保留複本造成的 GC 壓力；玩家路徑不會遇到，不計入閘門，但記在這裡，因為它是 `Playing()` 實作出錯時的退化樣子。

## 3. 離線轉檔（`tools/dosgolem.sh music`）

重跑：`tools/dosgolem.sh build && tools/dosgolem.sh music -out /out/music/wav -expect /out/music/midisum.tsv -check`（`midisum.tsv` 由 `tools/music/run.sh midisum` 產生，已存為 `docs/re/data/018-midisum.tsv`）。輸出表存為 `docs/re/data/019-hrmusic-report.tsv`：每個非空 MID 的曲長（解析器與獨立工具）、音符數（兩者）、峰值、RMS、近乎削波取樣數、聲部取代次數、活動音符數與窗 RMS 的相關、聽得到的比例、`Engine.Read` 與離線轉檔是否逐取樣相同、WAV 的 SHA-256 前 16 碼（限 `linux/amd64` 同一建置，不跨 `GOARCH`）。

結果：27 個檔全部通過 `-check`：曲長與獨立工具相符（0.2% 加 2 毫秒內）、音符數全部相等、聲部取代 0、近乎削波 0、峰值 0.210 到 0.701、RMS 0.039 到 0.193、活動相關 0.30（`PRINCESS`）到 0.96、聽得到的比例全部 100%、兩次轉檔相同、`Engine.Read` 與離線轉檔逐取樣相同。

基頻抽查（`apps/hr/cmd/hrmusic/pitch.go`，判準只來自 SMF 的音高與時間，不依賴合成器參數）：26 個非空檔，真渲染器 798/799 個音符通過（期望音高的調和累加至少是 ±12 個半音內最大值的 70%，要求每檔至少 90%）；偵測器自測用壞渲染器（每個音符播固定 440 Hz 正弦、起訖準時），26/799 通過，低於 60% 的上限。`-pitch-debug` 可列出不符的音符。`ALCOHOL.MID` 是 0 byte 檔，略過。

峰值不再是驗收門檻（只要求 0.05 到 0.99）：增益在驗收之前固定為 0.30（`docs/spec/007` 第 5.1 節）。

聽感沒有評估：沒有原版聲音可對拍，音色是本專案的 FM 參數。WAV 在 `workplace/out/music/wav/`，由使用者試聽。

## 4. 前端實跑（Xvfb、沒有音訊裝置）

重跑：`tools/play.sh gui`（`workplace/out/gui-help.png`、`gui-newgame.png`、`gui-title.png`）。

- Linux 後端確實載入了 `libasound.so.2`（日誌可見 ALSA 的錯誤訊息 `Unknown PCM default`），`snd_pcm_open` 回報失敗後，前端印出「音訊裝置不可用，靜音運行」並改用牆鐘拉取執行緒，遊戲照常進到新遊戲畫面，沒有結束（confirmed）。
- F1 說明列出 `F3 sound on/off` 與 `Sound: on (F3)`（`gui-help.png`）。
- 真實音訊裝置上的輸出沒有驗證（容器沒有裝置）。Windows 與 macOS 的 oto 後端只驗證了 Windows 能編譯，沒有執行。

## 5. 機器人長跑（`-sound`，NullSink）

重跑：`tools/bot.sh run snd-long-s1 -sound -game-hours 2 -seed 1`、`snd-long-s2 -sound -game-hours 2 -seed 2`（輸出 `workplace/out/bot/snd-long-s{1,2}/summary.json`，gitignore）。Sink 是 `NullSink`（用遊戲 tick 當時鐘，不開裝置），所以這一節只覆蓋掛鉤、引擎狀態與遊戲路徑，不覆蓋音訊裝置。

| 項目 | 種子 1 | 種子 2 |
|---|---:|---:|
| 狀態 | completed | completed |
| 遊戲時間（小時） | 2.00 | 2.00 |
| 動作 | 2767 | 2702 |
| 重開／結束遊戲 | 2／1 | 3／2 |
| 不同畫面 | 228 | 187 |
| 最低 SP | `6FA0` | `7502` |
| 疑似凍結 | 0 | 0 |
| 當機（`crash`） | 空 | 空 |
| T2 轉儲 | 0 | 0 |
| T2 最長靜默（遊戲秒） | 3.40 | 1.89 |
| 聲音鉤子停用（`sound.disabled`） | 空 | 空 |
| 聲音：`starts`／`fades`／`stops` | 208／207／1 | 84／83／1 |
| 聲音：`sfx`／`bad_sfx` | 1020／0 | 516／0 |
| 聲音：`queries`（`02C9` 狀態查詢） | 1,009,282 | 378,263 |
| 耗時（秒） | 3471 | 3436 |

- 觀察到的檔案開啟：`NATIONAL.MID` 67 與 68 次，不是每次查詢一次；有 Sink 時遊戲不再因為 `Playing()` 為假而重複讀 MID（對照 `docs/re/017` 第 6 節無 Sink 的 263,768 次，該次不同種子與輸入，只作量級對照）。`DANCER.MID`、`BATTLE2.MID`、`ALCOHOL.MID`（種子 1 六次、種子 2 一次）都有被開啟；`GOLD.MID` 在兩輪都沒有出現。
- `ALCOHOL.MID` 的開啟只表示遊戲開了這個檔，不表示 `7B3A:0488` 的路徑被走到並正確處理；第 7 節仍列為未覆蓋。
- 結論限於這兩個種子、2 遊戲小時、`-sound` 的 NullSink：沒有當機、沒有凍結、T2 零轉儲、鉤子沒有被停用。沒有驗的維度：真實音訊裝置、Windows 與 macOS、GOLD 路徑、存檔 A/B（第 7 節）。

## 6. 洩漏掃描

`tools/pkg/leakscan.py` 加入音訊判準（副檔名 `.wav` 等、檔頭 `RIFF…WAVE` 與 `MThd`、與清冊 `.MID`／`.PCM` 同名的檔）。控制組：一個假 `SCOUT.wav`（`RIFF…WAVE` 檔頭）與一個改了副檔名的 `MThd` 檔，掃描回報 4 項命中；同目錄的 `README.txt` 無命中。HD 素材檔名與音訊檔名沒有碰撞（以 `required.tsv` 的 `.MID`、`.PCM` 檔名主幹比對 `hd/` 下全部檔案）。

## 7. 尚未覆蓋、不能稱為已支援的路徑

| 路徑 | 狀況 |
|---|---|
| 短曲 `GOLD.MID`（`192B:0511`，`MusicStop` 接 `MusicStart`） | 沒有觸發這條路徑的收據 |
| `ALCOHOL.MID`（`7B3A:0488`，0 byte 檔） | 沒有收據 |
| 點擊音實機路徑（`PlaySFX(0x32)`，`1043:03B6`） | 冷啟動到新遊戲 90M 步內 `SFX ＝ 0`；載入取樣狀態檔後觀察到 1 次 `sfx`，但沒有逐 id 的收據 |
| 真實音訊裝置、Windows、macOS 實際出聲 | 沒有驗證 |
| 存檔 A/B（Sink 與無 Sink 的 `GAMEFILE.00x`、`fname.dat` 相同） | 待補 |
| AppImage、Wine 驗收 | 待補 |
| 聽感 | 由使用者試聽 |
