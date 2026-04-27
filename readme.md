# Shipping Accounting System

一個基於 FastAPI 的船運會計管理系統。

## 功能
- 船隻管理
- 航次管理（支援 ETD, ETA(DateTime), ArrivalDate(DateTime)）
- 進出港管理（SOP 任務時間檢核清單與規費關聯）
- 檢疫項目管理（CRUD 維護基本檔）
- 帳務管理（主檔/明細）
- 費用項目管理
- 費用組套管理（批次帶入預設費用項目，提升登錄效率）
- 帳單編號自動產生（格式：`Ayyyymmdd-001`，依日期流水號）
- 報表列印（CSS 列印版面）
- 報表匯出 Excel（主檔在上、明細在下）
- 主檔刪除規則：僅「草稿且無明細」可刪
- 可從清單頁或詳細頁直接「套用到新費用單」（新日期、新編號、複製明細）
- 系統維護介面優化（全系統統一 Modal + AJAX 模式，無須跳頁即可維護）
- 進出港項目（SOP）維護（修復群組存取 Bug 與動態更新）
- 客戶管理（重構為 Modal 模式，新增關鍵字搜尋過濾功能）
- 登入與權限管理 (規畫中)

## 安裝與執行

### 啟動方式 (Port 8001)
直接執行以下批次檔即可啟動系統：
- **`run_app.bat`**：啟動於 Port 8001，支援熱重載（Hot Reload）。

## 開發規範
- **語言**：全繁體中文。
- **Git**：每次修改後皆須執行 Git Commit。
- **運行**：於 `shipping-accounting` 目錄下進行開發與部署。

## 相關文件
- [專案規範檔 (.cursorrules)](.cursorrules)
- [專案規劃記錄 (包含 Docker 與 CI/CD 規劃)](docs/專案規劃記錄.md)
- [開發經驗：帳務組套功能實作](docs/開發經驗_帳務組套功能.md)
- [開發經驗：Playwright 伺服器測試](docs/開發經驗_Playwright伺服器測試.md)
