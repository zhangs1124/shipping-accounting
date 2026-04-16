# 2026-04-07: 登入異常與資料庫切換問題除錯經驗

## 問題描述
使用者反映伺服器啟動後，但「開不起來」。經由 Playwright 開啟瀏覽器確認，發現進入 `http://localhost:8080/login` 登入時會遇到 `405 Method Not Allowed` 錯誤。整個畫面無法完成登入，甚至不會彈出「帳號密碼錯誤」的正常提示。

## 根本原因分析
1. **API 錯誤處理覆蓋問題 (405 Masking 401)：**
   - 系統 `main.py` 內定義了 `status.HTTP_401_UNAUTHORIZED` 的通用例外處理，行為是 `return RedirectResponse(url="/login")`。
   - 當前端 `fetch('/auth/login', { method: 'POST' })` 遇到密碼錯誤（拋出 401）時，系統攔截並回應用以跳轉的 307 Temporary Redirect（導向至 `/login`）。
   - 瀏覽器自動跟隨 307，使用原來的 `POST` 請求發送給只有 `GET` 的 `/login` 路由，造成 `405 Method Not Allowed`，使得前端無法順利解析錯誤訊息。
2. **開發環境資料空缺 (Development Environment)：**
   - 先前環境切換 `APP_ENV=development` 時，後端連結至獨立的 `shipping_dev.db`。此資料庫是新建的空檔，未初始化，因此連預設的使用者帳號 (`admin`/`admin123`) 都不存在。
   - 因帳號不存在導致 API 傳回 401，進而被例外處理轉成 405。

## 解決方案
1. **修復例外轉發 (修正 `main.py`)：**
   - 針對 `/auth/` 開頭的 API 路徑攔截處理：若是 API 發生未授權，應退回 `JSONResponse` (HTTP 401) 而不是走 `RedirectResponse`。這樣前端介面即可正確捕捉「帳號或密碼錯誤」的字眼。
2. **重置初始資料 (測試開發環境)：**
   - 由於開發庫為空，手動在終端機執行 `python seed_data.py` 將初始的管理員與基礎測試數據補齊。
   - 執行後，使用 `admin`/`admin123` 即可順暢登入，跳轉至 `/invoices` 首頁。

## 經驗與未來改善
- 前後端分離及 AJAX API 請求的 Exception Handlers，應能識別 Request 型態 (例如確認 `/auth/` 路由區間) 分別做出跳轉 (HTML) 或是回傳 JSON (API) 的處理。
- 新增/切換資料庫環境時，應確定執行 `seed_data.py`。
