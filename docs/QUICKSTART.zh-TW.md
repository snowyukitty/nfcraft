# nfcraft：繁體中文快速開始

第一次交給本地 agent，先看根目錄 `START-HERE.zh-TW.md` 和 `prompts/BOOTSTRAP-LOCAL-AGENT.md`。本版為 0.1.1 交接版。

這是可試用的本機 app 與原始碼 repo，不是已完成實體讀寫器驗收、免安裝的 Windows 成品。介面目前是英文；**預設只操作模擬卡片，不會碰你的木質卡片**。

## 先試 app，不必先買讀寫器

解壓縮，確認電腦有 Python 3.11 以上，進入 repo 目錄執行：

```sh
python run.py
```

Windows 也可雙擊 `Start nfcraft.cmd`。它會開啟本機瀏覽器 app。核心模擬版不需要第三方套件、AI API key、雲端帳號或 NFC 硬體。請保留啟動的終端視窗；結束時按 Ctrl+C。啟動時印出的 operator 網址含有本機管理憑證，請勿分享。

先到 **Public profile** 修改顯示名稱。回到 **Workbench**，點 **New batch**，建立 10 張卡的批次。範例網址 `https://tap.example.com` 只供模擬，不能當作實體名片交付。

點 **Arm this batch**，輸入 `ARM 批次名稱` 後批准。之後每張卡不必再次批准：按 **Place virtual card**，等待驗證，再按 **Remove**，接著放下一張。批准最長十分鐘，或到達本次嘗試上限就失效。

試試把情境改成 **Interrupted write**。這張卡會進入待查核，而不是算成功。到 **Card inventory** 點 **Review & recover**，重新確認後，它會用原來的卡片身份與網址復原，並不是發一個新的網址。

## 電腦可以直接讀写 NFC，但必須有硬體

主方案：電腦 → USB NFC 讀寫器 → 一張 NTAG215 卡片。手機不必介入。一般 USB、藍牙或 Wi-Fi 本身不是 NFC 天線；能讀 UID 的設備，也不代表具備本 app 需要的底層讀寫能力。

目前 repo 選定 **ACS ACR1552U 的 PICC 介面**作為待驗證目標。不是把任意其他讀寫器的名稱填進去就能使用。第一次請只讀取，不寫卡：

```sh
python -m pip install -e ".[hardware]"
python nfcraftctl.py --mode hardware doctor
python run.py --mode hardware --reader "doctor 顯示的完整 PICC 名稱"
```

硬體模式的預設是唯讀。這份版本**沒有實體 NFC 測試紀錄**，讀寫器韌體的 transparent exchange、RF 回覆與 ACK 行為仍須在本地核對。詳見 `HARDWARE.md`。不要跳過唯讀檢查，也不要先拿全部卡片試。

完成檢查並由你決定用一張可犧牲的卡片試寫，才考慮啟用明確的 experimental flag；指令見 README。它依然需要在 app 裡批准批次。永久鎖卡、改密碼、改 lock bits 功能根本沒有實作，不會由 agent 自動決定。

## 讓本地 agent 幫忙

先啟動 app。另開終端：

```sh
python nfcraftctl.py status
python nfcraftctl.py batch-create --name "Pilot 01" --count 10 --base https://tap.example.com
python nfcraftctl.py audit
```

Agent 可以建批次、讀取狀態、檢查卡片、暫停、匯出與整理結果。**啟動實體寫入的批准仍在你手上**。每張卡的寫入循環由固定程式執行，不等待模型思考、不逐張消耗 AI API 額度。

`examples/mcp-config.json` 是 stdio MCP 設定範例。請把 Python 和 repo 路徑改成你本機的絕對路徑。`prompts/BOOTSTRAP-LOCAL-AGENT.md` 可交給 Codex／Claude Code 延續開發。`AGENTS.md` 記錄不可移除的安全條件。

## 寫成功，不等於可以發名片

這份 app 有三個容易混淆、但必須分開的事實：

- **Written / verified**：已寫入，且重新讀回與預期一致。
- **Published**：網址真的能在公網打開；目前需要你另外部署並驗證。
- **Ready to hand out**：最終木卡、QR code、手機開頁、儲存聯絡人都測試通過。

app 只會直接證明第一項，而且在 demo 模式下也只是模擬結果。公開頁面的 Cloudflare Worker / D1 原始碼已提供，但**尚未部署**；app 裡的 Suspend 只是本機設定，重新匯出及部署後才會讓公開頁面停用。

NFC 內只放你長期掌控網域下的一條 HTTPS 網址。每張卡有不同的隨機 ID；UID 只在本機對照，不是秘密或防偽機制。公開 manifest 不包含原始 UID，CSV 和資料庫備份则包含，請勿公開。

QR 匯出需要選裝：

```sh
python -m pip install -e ".[qr]"
```

之後在 **Card inventory** 點 **QR SVG**。列印、雷射雕刻或上漆後，要再次掃描真正成品。不要把電腦畫面中的成功提示當成印刷品或手機相容性的保證。

## 手機方案的定位

Android Chrome 的 Web NFC 能做只需 NDEF 的簡易寫卡站，但無法讀 NTAG215 的底層安全頁、驗證完整記憶體配置。需要完整檢查時，再做 Android 原生 NfcA bridge。這兩個手機 adapter 在本版都是設計，尚未實作。

手機插上 USB 線，不會自動变成電腦可用的 NFC 讀寫器。不要把本機服務改綁 `0.0.0.0` 當作手機連線捷徑；未來手機站需要另外設計 HTTPS、配對、任務租約和回報機制。

## 已知限制與安全

目前是原始碼 app，不是簽名安裝檔。選裝的桌面視窗與系統托盤尚未在真實 Windows 測試。無自動雲端同步、無 Android app、無公開 AI 分身對話、無逐卡寄信、無多站協同。個人履歷及聯絡資料請自行確認後才發布。

工作資料預設在 `%LOCALAPPDATA%\nfcraft\demo`；硬體模式用另一個 `hardware` 子目錄。資料庫未加密。不要刪除實體卡的工作資料來「重新開始」，否則會失去原本的卡片對照及復原證據。先使用 **Activity & audit → Back up local journal**。

未寫保護的卡片仍可能被附近的其他 NFC 寫入器改寫。第一批 pilot 保持可重寫是為了除錯，不代表適合直接做成無人看管的公開標籤；正式大量交付前，還要單獨決定並驗證寫保護／封存流程。本版不會執行或記錄永久封存。

先試模擬流程，再驗證一張硬體卡，接著做十張 pilot；通過後才擴大到整批。

舊版 `%LOCALAPPDATA%\NfcCardOps` 有卡片資料時，先閱讀 `MIGRATION.md`。不要為了改名而刪除舊資料庫；本版提供預檢及明確批准後才執行的匯入工具。
