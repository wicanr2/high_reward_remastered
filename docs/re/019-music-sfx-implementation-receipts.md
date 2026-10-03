# 019 音樂與音效播放的實作收據

日期：2026-10-03
狀態：收據（`docs/spec/007` 的實作驗證）。規格仍是 DRAFT（第四版，待第四輪重審）；收據記錄的是目前實作在目前輸入下實際量到的結果，不構成「已支援」的宣稱（見第 7 節）。
輸入：`MAIN.EXE` SHA-256 `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e`；dosgolem 分支 `hr` 基準提交 `223ed99`，實作為其上的未提交修改（提交後補提交號）；Go 容器 `golang:1.24-bookworm`（`tools/dosgolem.sh`）、`eob-remake-go:1.26.7-ebiten2.9.9`（`tools/play.sh`）；`linux/amd64`。

## 1. 單元測試（不需原版）

| 套件 | 重跑 | 結果 |
|---|---|---|
| `apps/hr/sound` | `CGO_ENABLED=1 tools/dosgolem.sh go test -race -count=1 -v ./apps/hr/sound/`（日誌 `workplace/out/test-sound-race.log`，2026-10-03） | 通過，38 個測試（SMF 解析與拒絕、起音時序對獨立公式、休止與音符、基頻、聲部相加、打擊樂瞬態、引擎生命週期、淡出與佇列、世代 CAS、音效內插、靜音、`Read` 零配置、並行、`NullSink`），含 `TestEngineFadeAfterNaturalEndIsNoop`、`TestEngineDroppedStartDoesNotLeavePlayingState`、`TestEngineSFXDoesNotBumpEpoch`、`TestEngineConcurrentThenQuiescentStateMatchesLastCommand` |
| `apps/hr/runtime`（不需原版的部分） | `tools/play.sh test-diag`，`HR_TEST_RUN=Sound` | `TestSoundPostDecodesArguments`、`StatusPatchesAXOnly`、`HooksIgnoreNonEntries`、`DisabledWhenFlagNonzero` 通過 |
| `apps/hr/hd`（theme 支援） | `CGO_ENABLED=1 tools/dosgolem.sh go test -race -count=1 -run 'CheckTheme\|Preload\|LoadAssets' ./apps/hr/hd/` | 通過 |
| `apps/hr/play` | `HR_RACE=1 HR_VERBOSE=1 tools/play.sh test-play`（`go vet` 加 `go test -race`；Xvfb；日誌 `workplace/out/final007-play-race.log`（21 項，逐項名稱在內）） | 通過（含保留鍵表不含 F3、`TestAudioAlwaysHasAPuller`、`TestPullSourceOldGenerationGetsSilenceAndDoesNotAdvance`、`TestAudioStalledBackendIsTakenOver`、`TestAudioDiedBackendHandover`、`TestAudioOpenTimeoutFallsBackToPump`、`TestPullSourceIdleUsesMonotonicOffset`、`TestResolveMute`） |
| Windows 編譯 | `tools/play.sh build-cross`（日誌 `workplace/out/final007-build-cross.log`） | `windows/amd64`、`CGO_ENABLED=0` 通過（exit 0；只有一行無害的模組快取寫入權限警告）；macOS 需要 osxcross，未在此驗證 |

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

重跑：`HR_BENCH_OVERHEAD=1 HR_TEST_RUN='DiagOverheadPaired' tools/play.sh test-diag`（日誌 `workplace/out/final007-overhead.log`，2026-10-04，在最終程式上重跑，約 4 分鐘；主機負載平均約 19，成對交替量測抵消大部分負載差異）。所有場景為前端預設組合（診斷加 HD 掛鉤），比值是使用者 CPU 時間的修剪平均 ± 標準誤。

兩種 Sink 回答不同的問題：

- 跟隨型 Sink（像真的引擎，`discard`）：有 Sink 時遊戲不再重複讀 MID，所以比值是「掛鉤成本減去省下的重複讀檔」的淨值，量不到純掛鉤成本。
- 恆假 Sink（`Playing()` 恆為假，`discard`）：遊戲走和無 Sink 相同的路徑（照舊重複讀 MID），沒有省下的 I/O 來抵銷，所以比值是不被抵銷的掛鉤成本（每步的 `Insn()` 檢查、`MusicStart` 的 20000 位元組複製、`Playing()` 的 AX 改寫）。

| 場景 | 診斷開 ÷ NoDiag（對照，`docs/spec/005`） | 聲音掛鉤 ÷ 無聲音掛鉤（跟隨型） | 聲音掛鉤 ÷ 無聲音掛鉤（恆假，不被抵銷） |
|---|---:|---:|---:|
| 冷啟動（HD 掛鉤） | 1.027 ± 0.005（無 HD 掛鉤）、1.011 ± 0.006（HD 掛鉤） | 0.875 ± 0.005 | 0.998 ± 0.007 |
| 戰鬥佈陣（HD 掛鉤） | 1.029 ± 0.006（無 HD 掛鉤）、0.978 ± 0.004（HD 掛鉤） | 0.926 ± 0.006 | 0.986 ± 0.005 |

全部在閘門 1.05 之內。不被抵銷的掛鉤成本約為零（冷啟動 −0.2%、戰鬥佈陣 −1.4%，在誤差內）。診斷開對 NoDiag 的對照欄是 `docs/spec/005` 的量測，每次重跑有 ±2% 的主機負載波動。

### MID 緩衝的位址與複製路徑

`MusicStart` 複製的 MID 緩衝在線性位址 `0xD5000`（EMS 頁框區，高於 `A0000`）。`SoundStats.MidAddr` 記最近一次複製的位址，`SkippedStarts` 記因緩衝與 VGA 視窗相交而略過的 `MusicStart` 次數。`TestSoundHooksDoNotChangeTheGame` 在冷啟動 90M 步的結果：`MidAddr=0xd5000`、`Starts=4774`、`SkippedStarts=0`（最終程式，`workplace/out/final007-runtime-sound.log`）。

- 複製的條件是「範圍不與 VGA 視窗 `A0000–AFFFF` 相交」就用區塊複製（`copy` 自 `Mem`，不觸發讀取監看）；相交時略過這次 `MusicStart` 並計數（平面模式下讀視窗有 VGA latch 副作用，`Peek` 對視窗只回 0）。掛鉤所有觀察讀取（旗標、MID 遠指標、切片表、堆疊引數）一律用 `Machine.Peek8`／`Peek16`，沒有副作用。`Read8` 對 `0xD5000` 沒有特殊語意，EMS 映射又是把頁資料複製進頁框位址（`internal/dos/ems.go` 的 `WriteBytes`），所以區塊複製與 `Read8` 的值相同；第一次 `MusicStart` 的位元組通過「以 `SCOUT.MID` 開頭」的檢查（`TestSoundHooksDoNotChangeTheGame`）。`TestSoundPostDecodesArguments` 補了與視窗相交（`A000:F000`、`A000:0000`、`9FFF:FFF0`）與緊貼視窗但不相交（`9B1E:0000`、`B000:0000`）的案例。

## 3. 離線轉檔（`tools/dosgolem.sh music`）

重跑：`tools/dosgolem.sh build && tools/dosgolem.sh music -out /out/music/wav -expect /out/music/midisum.tsv -check`（`midisum.tsv` 由 `tools/music/run.sh midisum` 產生，已存為 `docs/re/data/018-midisum.tsv`）。輸出表存為 `docs/re/data/019-hrmusic-report.tsv`：每個非空 MID 的曲長（解析器與獨立工具）、音符數（兩者）、峰值、RMS、近乎削波取樣數、聲部取代次數、活動音符數與窗 RMS 的相關、聽得到的比例、`Engine.Read` 與離線轉檔是否逐取樣相同、WAV 的 SHA-256 前 16 碼（限 `linux/amd64` 同一建置，不跨 `GOARCH`）。

結果：27 個檔全部通過 `-check`：曲長與獨立工具相符（0.1% 加 2 毫秒內）、音符數全部相等、聲部取代 0、近乎削波 0、峰值 0.210 到 0.701、RMS 0.039 到 0.193、活動相關 0.30（`PRINCESS`）到 0.96、聽得到的比例全部 100%、兩次轉檔相同、`Engine.Read` 與離線轉檔逐取樣相同。

基頻抽查（`apps/hr/cmd/hrmusic/pitch.go`，判準只來自 SMF 的音高與時間，不依賴合成器參數）：26 個非空檔，真渲染器 798/799 個音符通過（期望音高的調和累加至少是 ±12 個半音內最大值的 70%，要求每檔至少 90%）；偵測器自測用壞渲染器（每個音符播固定 440 Hz 正弦、起訖準時），26/799 通過，低於 60% 的上限。`-pitch-debug` 可列出不符的音符。`ALCOHOL.MID` 是 0 byte 檔，略過。

峰值不再是驗收門檻（只要求 0.05 到 0.99）：增益在驗收之前固定為 0.30（`docs/spec/007` 第 5.1 節）。

聽感沒有評估：沒有原版聲音可對拍，音色是本專案的 FM 參數。WAV 在 `workplace/out/music/wav/`，由使用者試聽。

## 4. 前端實跑（Xvfb、沒有音訊裝置）

重跑：`tools/play.sh gui`（日誌 `workplace/out/final007-gui.log`，2026-10-04，最終程式；截圖 `workplace/out/gui-help.png`、`gui-newgame.png`、`gui-title.png`）。

- Linux 後端確實載入了 `libasound.so.2`（`final007-gui.log` 有 ALSA 的 `Unknown PCM default`），`snd_pcm_open` 回報失敗後，前端印出「音訊裝置不可用，靜音運行」並改用牆鐘拉取執行緒，遊戲照常進到新遊戲畫面，沒有結束（confirmed）。
- F1 說明列出 `F3 sound on/off` 與 `Sound: on (F3)`（`gui-help.png`）。
- 真實音訊裝置上的輸出沒有驗證（容器沒有裝置）。Windows 與 macOS 的 oto 後端只驗證了 Windows 能編譯，沒有執行。

## 5. 機器人長跑（`-sound`，NullSink）

重跑：`tools/bot.sh run snd-long-s1 -sound -game-hours 2 -seed 1`、`snd-long-s2 -sound -game-hours 2 -seed 2`（輸出 `workplace/out/bot/snd-long-s{1,2}/summary.json`，gitignore）。Sink 是 `NullSink`（用遊戲 tick 當時鐘，不開裝置），所以這一節只覆蓋掛鉤與遊戲路徑，不覆蓋 `Engine` 的狀態機（命令佇列、世代、淡出）與音訊裝置。

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
| 存檔 A/B（Sink 與無 Sink 的 `GAMEFILE.00x`、`fname.dat` 相同） | 第 8 節：一條路徑已驗（讀槽 0、存槽 2）；停止常式與跟隨型 Sink 的路徑未驗 |
| AppImage、Wine 驗收 | 待補 |
| 聽感 | 由使用者試聽 |

## 8. 存檔 A/B

重跑：`HR_TEST_RUN='SaveDiffDetector|SoundDoesNotChangeSaves' tools/play.sh test-diag`（`apps/hr/runtime/sound_save_test.go`，約 62 秒）。腳本與 `TestSaveGoesToScratchAndLeavesOriginalAlone` 相同：標題讀取遊戲檔案、槽 0、地圖筆圖示開系統選單、檔案存入、槽 2，跑到 246M 步。分別在無 Sink 與 `Playing()` 恆假的 Sink 下各跑一次（恆假的 Sink 讓遊戲走與無 Sink 相同的路徑，指令軌跡一致）。

結果：`GAMEFILE.002`（31839 bytes）與 `FNAME.DAT`（158 bytes）逐位元相同。Sink 那一輪的掛鉤確實在運作（`Starts ＝ 11849`、`Fades ＝ 11849`、`SFX ＝ 2`、`Queries ＝ 23692`），所以不是空跑。比較器另有自測（翻轉一個位元組必須被找到、長度不同必須被報告）。

限制：
- 這條路徑 `Stops ＝ 0`，停止掛鉤寫 `2BCC:0223` 的路徑沒有被走到。`2BCC:0223` 的線性位址 `0x2BEE3` 在存檔傾印範圍（IDA `4073:0008` 起 31839 bytes，執行期線性位址約 `0x31838` 起）之外，推得不影響存檔；未用收據證明。
- 跟隨型 Sink 會讓遊戲少讀 MID，tick 數與指令軌跡改變，存檔可能因時間欄位而不同，那不是掛鉤改寫存檔，所以沒有納入比較。
- 只驗了槽 2 的寫入，沒有驗讀入原版存檔後的行為（讀槽 0 在腳本內已發生，到存檔時狀態一致）。

## 9. 第三輪審查後的重跑與突變驗證

日期：2026-10-03。對應 `docs/spec/007` 第 8 節與審查項 X1、X2、X4、T2。命令與日誌如下，日誌在 `workplace/out/`（gitignore）。

### 9.1 Engine 加 Session 整合測試

重跑：`HR_TEST_RUN='SoundEngineSession' tools/play.sh test-diag`（日誌 `test-sound-engine-session.log`，約 39 秒）。靜音的真 `Engine`，每個遊戲秒餵 44100 框，跑到連續三次 `MusicStart`。

| 項目 | 值 |
|---|---|
| `MusicStart` 的遊戲秒 | 0.11、36.47、72.94 |
| 相隔（第 1 至 2 次、第 2 至 3 次） | 36.36、36.47 |
| `SCOUT.MID` 曲長 | 36.38 |
| 判準 | 兩個相隔都在曲長正負 0.35 內；每次 `MusicStart` 的資料以 `SCOUT.MID` 開頭 |
| 結果 | 通過 |

### 9.2 突變驗證

腳本把原始檔的雜湊記在 `workplace/out/mutation-007.log`（`engine.go` 前 16 碼 `7ad920886d07b4e9`，`audio.go` 前 16 碼 `87194ad09ee47961`），每項突變後還原並核對雜湊相同。基準（未突變）的所有被測測試先通過。

| 突變 | 測試 | 結果 |
|---|---|---|
| M1：`cFade` 的 `if e.cur.SongDone()` 改成 `if false && …`（拿掉 Z1 修正；只改 `engine.go` 的第一處，曲末 CAS 那一處不動） | `TestEngineFadeAfterNaturalEndIsNoop` | 失敗：「曲末後的淡出應是空操作：fading＝true pending＝true」 |
| 同上 | `TestSoundEngineSessionIntegration` | 失敗：`MusicStart` 在遊戲秒 0.11、36.47、73.65；第 2 至 3 次相隔 37.18，比通過時的 36.47 多 0.71 秒（`FadeSeconds(1)`）；第 1 至 2 次相隔 36.36 不受影響，與審查的推論一致 |
| M2：`pullReader.Read` 的 `if r.gen != r.s.gen` 改成 `if false && …`（拿掉世代檢查） | `TestPullSourceOldGenerationGetsSilenceAndDoesNotAdvance` | 失敗：「被接手的舊世代拉取者應只拿到靜音」 |
| 同上 | `TestAudioStalledBackendIsTakenOver` | 失敗：「被接手的舊拉取者應只拿到靜音」（前端測試以 `-race` 執行） |
| M3：`SFX` 在送命令前遞增世代並寫狀態字 | `TestEngineSFXDoesNotBumpEpoch` | 失敗：「播放中呼叫過 SFX 之後，曲子到曲末仍應自然結束」 |

結論：這三項修正各有至少一個會失敗的測試守住。舊版 `TestSoundEngineSessionIntegration`（只比第 1 至 2 次相隔）與舊版停滯測試（靜音、舊拉取者只讀 2 秒）在對應突變下仍會通過，也就是審查 X1、X2 指出的空轉，本輪已改為上述有鑑別力的版本。

### 9.3 其餘本輪新增的測試

| 測試 | 內容 |
|---|---|
| `TestAudioOpenTimeoutFallsBackToPump` | 開啟裝置卡住：`startAudio` 在逾時後返回，曲子由牆鐘拉取者推到自然結束，晚到的裝置被關閉剛好一次 |
| `TestPullSourceIdleUsesMonotonicOffset` | 停滯偵測的 `idle()` 隨拉取重設、隨時間增加 |
| `TestResolveMute` | `-mute`、`HR_MUTE`、偏好設定 `sound` 的 13 種組合 |
| `TestEngineConcurrentThenQuiescentStateMatchesLastCommand` | 並行命令洪流結束、讀取者停止後，最後一個音樂命令決定 `Playing()` |

另有改動：`MusicStart` 的 20000 位元組複製改為區塊複製（第 4 輪後的現行條件見第 2 節「MID 緩衝的位址與複製路徑」）；`pullSource` 的看門狗改用單調時鐘；`patches.go` 檔頭補流程紀錄；`hrmusic` 失敗訊息與判準一致。

### 9.4 runtime 的 Sound 測試全跑

重跑：`HR_TEST_RUN='Sound|SaveDiffDetector' tools/play.sh test-diag`（日誌 `workplace/out/test-runtime-sound-all.log`，2026-10-03，約 119 秒；第 4 輪審查後在最終程式重跑的日誌見第 10 節，不帶 `-race`：帶 `-race` 時 90M 步的測試超過 `go test` 預設的 10 分鐘逾時；並行相關的測試已在 `apps/hr/sound` 與 `apps/hr/play` 以 `-race` 跑過）。13 個測試全部通過：`TestSaveDiffDetectorSelfTest`、`TestSoundDoesNotChangeSaves`、`TestSoundPostDecodesArguments`、`TestSoundStatusPatchesAXOnly`、`TestSoundHooksIgnoreNonEntries`、`TestSoundDisabledWhenFlagNonzero`、`TestSoundHooksFailClosedOnBytes`、`TestSoundHooksDoNotChangeTheGame`、`TestSoundPlayingSuppressesReload`、`TestSoundNaturalEndReplays`、`TestSoundPlayMusicPathFromState`、`TestSoundStateFilesAreClean`、`TestSoundEngineSessionIntegration`。

## 10. 最終驗證（第四輪審查後，2026-10-04）

在規格 007 第五版對應的最終程式上，整批重跑（腳本 `workplace/final-verify-007.sh`，日誌 `workplace/out/final007-*.log`，gitignore）。被測原始檔雜湊（前 16 碼）記在 `final007-hashes.log`：`engine.go` `7ad920886d07b4e9`、`audio.go` `87194ad09ee47961`、`engine_test.go` `57f882f2305c8674`、`audio_test.go` `36592dbbe2da1a5c`、`sound_test.go` `daa82e6dbde77943`。

| 項目 | 指令與日誌 | 結果 |
|---|---|---|
| `apps/hr/sound` | `go vet` 加 `go test -race`（`final007-sound-race.log`） | 38 項通過 |
| `apps/hr/play` | `HR_RACE=1 tools/play.sh test-play`（`final007-play-race.log`） | 21 項通過、1 項略過（`TestGenCharsets`，沒設 `HR_GEN_CHARSET`，字集重建用） |
| `apps/hr/runtime` Sound | `HR_TEST_RUN='Sound|SaveDiffDetector' tools/play.sh test-diag`（`final007-runtime-sound.log`，95 秒，不帶 `-race`） | 13 項通過；整合測試 `MusicStart` 在遊戲秒 0.11、36.47、72.94（相隔 36.36、36.47，曲長 36.38）；`MidAddr=0xd5000`、`Starts=4774`、`SkippedStarts=0` |
| 效能 | 第 2 節（`final007-overhead.log`，235 秒） | 全部在閘門 1.05 內 |
| 突變 M1 至 M5 | `final007-mutation.log` | 5 項全部使對應測試失敗，還原後原始檔雜湊與基準相同（第 9.2 節 M1 至 M3；M4：`send` 丟棄 `cStart` 時不回復狀態字，`TestEngineDroppedStartDoesNotLeavePlayingState` 失敗；M5：裝置回報 died 時不接手，`TestAudioDiedBackendHandover` 失敗） |
| 離線轉檔 | `hrmusic -check`（`final007-hrmusic.tsv`） | 27 個檔通過；輸出表與已提交的 `docs/re/data/019-hrmusic-report.tsv` 比對無差異（`final007-hrmusic.diff` 為空），WAV 的 SHA-256 前 16 碼相同 |
| Windows 編譯 | `tools/play.sh build-cross`（`final007-build-cross.log`） | `windows/amd64` 通過；輸出只有模組快取寫入權限的一行警告 |
| 前端 | `tools/play.sh gui`（`final007-gui.log`） | 見第 4 節。ALSA 沒有 `default` 裝置，前端靜音運行；日誌另有一行 `跑不到 18.2 Hz（2 秒內 21 個 tick，應有 36）：間隔 300000 → 270000`，是 Xvfb 軟體繪圖加主機負載下既有的計時器降頻（`Session.Lowered`），與聲音無關 |

結論範圍：Linux、無音訊裝置、`NullSink` 與離線轉檔。真實音訊裝置輸出、macOS、`GOLD.MID` 與 `ALCOHOL.MID` 路徑、逐 id 的點擊音收據仍在第 7 節，使用者尚未試聽。
