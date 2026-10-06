高報酬戰將 hr-play
===================

這是《高報酬戰將》（DOS 版）的桌面執行器。它在 dosgolem 內執行你自備的原版檔案，
並在記憶體內把堆疊從 4 KB 擴大到 32 KB，避免巢狀選單用完堆疊。

本程式不含、也不下載任何原版遊戲檔案。請自備一份原版（內含 MAIN.EXE 的資料夾）。

使用
----
1. 把原版檔案（含 MAIN.EXE 的整個資料夾內容）放進本程式旁的 original 資料夾。
   也可以用命令列指定：  hr-play -orig <資料夾>
   Linux AppImage：把 original 資料夾放在 .AppImage 檔案旁邊。
   macOS：放進 HighReward.app/Contents/Resources/original，或用 -orig。
2. 執行 hr-play。滑鼠操作遊戲。

按鍵（保留給程式，不送進遊戲）
-----------------------------
F1 功能說明與統計    F2 切換 theme    F3 聲音開關    F4 切換五語介面
F11 或 Alt+Enter 全螢幕    F12 存截圖    Ctrl+D 存診斷    Ctrl+Q 結束
macOS 筆電的 F1 至 F4 預設是亮度與系統功能，要按 Fn。
遊戲內語言在重新啟動後套用，語言包由附帶的譯文表及字模在本機建置。

存檔與資料
----------
存檔寫在使用者資料目錄的 high_reward/saves（Linux ~/.config、macOS ~/Library/Application Support、
Windows %AppData%）。原版資料夾不會被修改。截圖放在同一層的 screenshots。

目前的限制
----------
- 音樂與音效是近似：遊戲的音樂由前端的 FM 合成器播放，音色與原版不同；沒有音訊裝置時靜音運行；真實音訊裝置的輸出沒有驗證。
- 只執行主程式 MAIN.EXE，不播片頭與片尾。
- macOS 版沒有簽章，也沒有在實機驗證過（首次開啟請右鍵選「打開」）。

授權
----
見 LICENSE（RRSAL-1.0）與 THIRD_PARTY_NOTICES.txt。
此版含 HD、AI 美術及原版文字衍生譯文，依使用者決定隨公開儲存庫發行。
原版及第三方享有權利的部分不由本專案授權，見 LICENSE 第 2 條 (c)。

English
-------
hr-play runs your own copy of the original game files inside dosgolem and enlarges the
program stack in memory. It includes no game files. Put the folder that contains MAIN.EXE
into "original" next to the program, or run with -orig <folder>.
