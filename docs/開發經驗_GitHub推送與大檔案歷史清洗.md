# 開發經驗：GitHub 推送與大檔案歷史清洗

## 背景與問題
在 2026 年 5 月 26 日，嘗試將本地積累的 61 個 Commit 推送至 GitHub 遠端倉庫（`https://github.com/zhangs1124/shipping-accounting.git`）時，Git 報出以下錯誤：
```text
remote: error: File gitea_server/gitea.exe is 206.59 MB; this exceeds GitHub's file size limit of 100.00 MB
To https://github.com/zhangs1124/shipping-accounting.git
 ! [remote rejected] main -> main (pre-receive hook declined)
error: failed to push some refs to 'https://github.com/zhangs1124/shipping-accounting.git'
```
由於 GitHub 限制單一檔案大小不能超過 100MB，且該限制會溯及所有即將被推送的 Commit 歷史。即使當前工作區中沒有該大檔案，只要歷史 Commit（此處為 `b09caa4`）中曾經提交過該檔案，推送就會被攔截。

---

## 解決步驟

### 1. 建立本地安全備份
在進行任何 Git 歷史重構操作前，先建立一個備份分支以防萬一：
```bash
git branch backup-main-before-filter
```

### 2. 清洗 Commit 歷史
使用 `git filter-branch` 來遍歷並過濾本地未推送的 61 個 Commit（即自 `origin/main` 到 `HEAD` 的範圍），從歷史中徹底抹除 `gitea_server/gitea.exe` 的紀錄：
```bash
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch gitea_server/gitea.exe" --prune-empty --tag-name-filter cat -- origin/main..HEAD
```
此命令成功在 24 秒內完成所有 61 個 Commit 的重新改寫，且完全沒有觸及已經安全推送到遠端的老舊歷史。

### 3. 設定環境變數 (隱私保護)
使用者提供了 GitHub Personal Access Token (PAT) 作為驗證憑證。
* **避免將 Token 寫入追蹤的 `.env` 檔案中**：因為 `.env` 目前是 Git 追蹤的檔案，若寫入並推送，將會被 GitHub 自動偵測並立即失效（Revoke）。
* **正確做法**：使用 Windows 的 `setx` 命令，將 `GITHUB_TOKEN` 寫入系統環境變數中，保護機密性：
  ```cmd
  setx GITHUB_TOKEN "ghp_************************"
  ```
* 暫存的 token 說明檔 `1.md` 則保持為 Git 未追蹤狀態（Untracked），確保其不會被推送至遠端。

### 4. 成功推送到 GitHub
使用含有 Token 驗證的 HTTPS 網址進行推送：
```bash
git push https://ghp_************************@github.com/zhangs1124/shipping-accounting.git main
```
推送順利完成：
```text
To https://github.com/zhangs1124/shipping-accounting.git
   3af64a7..926382c  main -> main
```

### 5. 同步本地與遠端追蹤分支
最後執行 `git fetch origin`，將本地的 `origin/main` 追蹤指針更新到最新狀態。執行 `git status` 顯示：
```text
On branch main
Your branch is up to date with 'origin/main'.
```

---

## 經驗總結與防範建議
1. **二進位大檔案處理**：開發過程中應嚴格將 `.exe`、`.db` 等大檔案寫入 `.gitignore`，避免意外提交到 Git 中。
2. **歷史清洗工具**：針對本地未推送的 commits，使用限制範圍的 `git filter-branch ... origin/main..HEAD` 能夠快速且安全地解決大檔案限制問題，而不需要對整個倉庫進行全局重構。
3. **敏感資訊保護**：永遠不要將 `GITHUB_TOKEN` 或 API Key 提交到會被 GitHub 追蹤的程式碼或設定檔中，改用系統環境變數或本地未追蹤的 `.env` 是最安全的做法。
