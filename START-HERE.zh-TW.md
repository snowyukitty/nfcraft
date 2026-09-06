# nfcraft｜從這裡開始

**版本：0.1.1 · 本地 agent 交接版 · 2026-09-05**

這個資料夾包含完整 app 原始碼、操作工具、設計文件、測試及交接 prompt，不需要再下載前一版 NFC Card Ops。它不是已簽名的 Windows 安裝檔，也不是已完成實體 NFC 驗收或雲端部署的成品。

## 你現在只需要做這件事

把壓縮檔的**內容**解壓縮到你本地的 `nfcraft` 資料夾，在 agent 中開啟這個資料夾，貼上：

```text
這是我們的 nfcraft 專案，請直接接手執行，不要只提出計畫。

先閱讀根目錄 AGENTS.md、START-HERE.zh-TW.md、docs/PROJECT-STATE.md，
再完整閱讀 prompts/BOOTSTRAP-LOCAL-AGENT.md，將它作為本次工作的執行 brief。

請先檢查現有程式與我的本地環境、重跑測試，再改善設計與實作，
讓 app 在本機順暢運行，並依文件完成可執行的硬體驗收、打包和公開名片部署。
保留現有可用功能與資料，不要另建一套空殼 repo。

你可以根據實際證據優化方案，但不能拿掉安全限制或把模擬結果當成實體驗收。
缺少硬體、網域或雲端授權時，先完成其他未受阻的工作，清楚記錄被阻擋的階段。
每次完成後更新專案狀態、測試證據與延續文件，讓未來的 agent 能繼續升級。
用繁體中文向我回報進度與最後操作方式。現在開始。
```

正確解壓後，`run.py`、`AGENTS.md`、`pyproject.toml` 都直接位於你開啟的資料夾。裡面另有一個 `nfcraft/` 子目錄，**它是 Python package，必須保留**，不是多解壓了一層。

```text
你選的磁碟:\...\nfcraft\
  AGENTS.md
  START-HERE.zh-TW.md
  run.py
  nfcraftctl.py
  pyproject.toml
  nfcraft\                ← 程式 package
  prompts\
  docs\
  scripts\
  cloudflare\
  tests\
```

已有修改或 `.git` 的資料夾不要直接覆蓋；解壓到另一個暫存資料夾，交由 agent 比對合併。執行資料通常不在 repo 裡，但仍應先備份。

## 你也可以先直接試 app

有 Python 3.11 以上，雙擊 **`Start nfcraft.cmd`**，或在 repo 目錄執行：

```powershell
python run.py
```

預設是模擬模式，不會感應或寫入你的木卡。啟動器優先使用 `.venv\Scripts\python.exe`；沒有才使用系統 Python。沒有 Python 時，讓 agent 先檢查並用官方工具完成環境準備，不要改全域安全設定。

不需要 AI API key、不需要 Node、不需要讀寫器，就可以試核心 demo。Node 是完整測試與公開 Worker 開發的工具，不是啟動本機 demo 的前提。關閉瀏覽器分頁不代表停止程式；在啟動終端按 Ctrl+C。啟動網址包含 operator 憑證，不要貼到公開 issue、報告或聊天。

## 重要文件

| 文件 | 用途 |
|---|---|
| `prompts/BOOTSTRAP-LOCAL-AGENT.md` | 第一次接手、執行、優化與部署的完整 prompt |
| `prompts/CONTINUE-ITERATION.md` | 未來版本繼續升級時使用 |
| `AGENTS.md` | 每個 agent 都要遵守的工程及安全規則 |
| `docs/PROJECT-STATE.md` | 現在已完成與尚未完成的真實狀態 |
| `docs/IMPLEMENTATION-PLAN.md` | 分階段工程任務、優先順序與完成條件 |
| `docs/DEPLOYMENT.md` | 本地 app、Windows 打包、preview、production 的部署邊界 |
| `docs/QUALITY-GATES.md` | 測試與驗收標準，防止「看起來完成」 |
| `docs/MIGRATION.md` | 舊版資料匯入與改名注意事項 |
| `docs/RELEASE-PROCESS.md` | 未來版本升級、資料相容與回退流程 |

## 這份交接包的界線

已提供並測試的是：改名後的核心程式、模擬批量流程、復原與安全檢查、CLI/MCP 基本連線、匯出驗證、舊資料匯入測試，以及公開頁面 handler 測試。詳見 `docs/TEST-REPORT.md`。

實體讀寫器、你的 Windows 環境、手機感應、雕刻後 QR、桌面安裝包，以及 Cloudflare/DNS/TLS，需要在你的設備和帳號上繼續驗收。沒有在你的雲端或電腦上偷偷執行任何部署。

**第一個實體目標是一張卡成功，再做十張 pilot；不是直接把全部卡拿來量產或鎖死。**
