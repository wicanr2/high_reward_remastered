# 程序板面與文字遮罩

2026-10-07。對應 [Issue #5](https://github.com/wicanr2/high_reward_remastered/issues/5)，接線契約見 [011](../spec/011-procedural-ui-themes.md)。目前證據涵蓋 PLATE2 的五種尺寸，其他介面原語仍未定案。

## 輸入與工具

| 檔案 | 大小 | SHA-256 |
|---|---:|---|
| MAIN.EXE | 539424 | `08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e` |
| PLATE1.PAT | 128 | `4f32df39caecd88e6f239622311d6fcc057207ebd4ca06fbc7ad1e49c298baf8` |
| PLATE2.PAT | 128 | `c512580a5cad8400638e57e137b2f56aa4d7b6328832e95915be3211c8b75b3b` |

動態探針使用 Docker、Go 1.26.7 與本機 dosgolem 副本。靜態查詢使用 IDA Pro 9.4，只讀既有資料庫。IDA 位址與執行期 CS:IP 分欄列出；VGA 像素座標包含上方 40 列。

完整方法與工具收據入口是 `workplace/out/ui-integration-evidence.md`，連到 `hr-ui-evidence-probe.go`、`hr-ui-evidence-receipt.json`、`hr-ui-evidence-shape.go`、`hr-ui-evidence-shape.json` 與 IDA 匯出。原版畫面、遮罩及來源資料只留本機。

## 已證實範圍

| 執行期定位 | IDA 定位 | 語意與等級 |
|---|---|---|
| `1D84:000A` | `2C74:000A` | confirmed：far call 參數為 x、y、欄數、行數、PAT 遠指標；矩形為 `(x,y+40,(欄數+2)*8,(行數+1)*8)` |
| `1D84:003D` 至 `0048` | `2C74:003D` 至 `0048` | confirmed：四平面圖樣 OR 的遮罩決定覆寫，原色 0 在此保留背景 |
| `1C35:01C5` | 依既有字形證據換算 | confirmed：旗標 0 的來源是 16 列、每列 3 bytes 的 24×16 遮罩，含同值寫入 |
| `1F69:000E`、`1F69:0169` | `2E59:000E`、`2E59:0169` | confirmed：保存／還原以四個 uint16 標頭與逐列四平面為準 |

正常冷啟動、點新遊戲及開場對話共 210000000 步。11 次板面呼叫皆匹配 PLATE2 的完整 128-byte 雜湊，返回後改變像素沒有落在矩形之外。標題選單、債務與現金面板、肖像外框和對話框都經此入口；不以 prototype 的固定矩形識別。

同一正常呼叫 entry 的快照另分成背景 0 與 15 的受控 RE 分支，執行原版至 far return。兩側相同的位置是覆寫，不同的位置保留背景。五個尺寸都符合局部 `2 ≤ x < W−2`、`1 ≤ y < H−1`，差異及矩形外誤判皆為 0。

| 尺寸 | 不透明像素 | 透明像素 |
|---|---:|---:|
| 128×56 | 6696 | 472 |
| 168×48 | 7544 | 520 |
| 168×32 | 4920 | 456 |
| 144×168 | 23240 | 952 |
| 272×72 | 18760 | 824 |

形狀收據 SHA-256 `2b95dafc25684e8c1ed9c065731cddb03cf9f8a86f4c7c72cbed97cca8acda8d`。分支都保留正常機器的 CPU、步數、記憶體與畫面。這是局部原語 RE，不把受控背景帶入正式遊戲，也不取代正常玩家路徑驗收。

1504 次畫面內、旗標 0 的字形呼叫，其改變像素全在來源遮罩內；1338 次與已畫板面相交。另 40 次傳輸矩形跨右緣，未量測，必須回退。188 次非游標保存與 165 次非游標還原中，320816 個還原像素都符合保存資料。保存高度可能比板面高，不能以板面矩形替代保存標頭。

## 接線限制

- 同色的字形或後畫物件不能只靠 Expected 相符判斷。使用字形寫入遮罩與繪製順序；未知寫入保守回退。
- 原版保存區只含索引色。新呈現 metadata 必須隨相同保存區記錄及恢復，核對指標、標頭和資料摘要。
- `drawDisplayText` 的原色 Before 擦除會破壞主題背景。擦除須從同一 Frame 的主題背景取色，文字位置、Noto 字型與譯文維持既有契約。
- PLATE1、其他尺寸、非 8 對齊座標、純線框及獨立抖色 helper 仍是未知或未驗範圍，不宣稱全部非人物介面完成。

## 實作與驗證入口

正式接線在本機 fork `686581d`，備份 `engine/patches/0043-procedural-ui-themes.patch`。只涵蓋上述五尺寸，不把未觀測原語升級為已支援。

- 作者報告：`workplace/out/ui-runtime-implementation.md`、`ui-renderer-implementation.md`。
- 獨立審查：`workplace/out/review-ui-spec-a.md`、`review-ui-spec-b.md`、`review-ui-final.md`、`review-ui-cursor-boundary.md`。
- 原版隔離與窄測：`ui-runtime-original-ab.log`、`ui-runtime-stride.log`、`ui-runtime-final-regressions.log`、`ui-play-final-regressions.log`，均在 `workplace/out/`。
- 正常畫面與錄影：`workplace/out/ui-final-gui/`、`ui-english-gui/`。前者等 HD／AI 實際完成載入後取樣；圖片已從 README 提供入口。

這些結果尚不代替實際發行包驗證或使用者的美術過目。

## 勘誤回查

| 原始鍵 | 現行證據 | 舊文件入口 |
|---|---|---|
| MAIN.EXE／IDA `2C74:000A`／PLATE*.PAT | 本檔與來源清冊：PAT 各 128 bytes；1024 是配置容量 | [009 程序板面補核](009-draw-primitives-DRAFT.md#程序板面補核) |

原有證據與歷史文字保留，勘誤同步記入 WORKLOG。
