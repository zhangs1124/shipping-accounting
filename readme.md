# Shipping Accounting System

一個基於 FastAPI 的船運會計管理系統。

## 功能
- 船隻管理
- 航次管理
- 帳務管理（主檔/明細）
- 費用項目管理
- 帳單編號自動產生（格式：`Ayyyymmdd-001`，依日期流水號）
- 報表列印（CSS 列印版面）
- 報表匯出 Excel（主檔在上、明細在下）
- 主檔刪除規則：僅「草稿且無明細」可刪
- 可從清單頁或詳細頁直接「套用到新費用單」（新日期、新編號、複製明細）
- 客戶管理（基本 CRUD）

## 安裝與執行

```bash
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

開啟網址：

- 本機：`http://127.0.0.1:8000`
- 內網：`http://<你的IP>:8000`


## 相關文件
- [專案規劃記錄 (包含 Docker 與 CI/CD 規劃)](docs/專案規劃記錄.md)
