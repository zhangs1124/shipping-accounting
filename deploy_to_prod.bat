@echo off
setlocal
:: 設定來源與目標路徑 (請根據實際目錄調整)
set SOURCE="D:\project\Voyage\shipping-accounting"
set TARGET="D:\project\Voyage\shipping-accounting-prod"

echo ============================================================
echo [部署工具] 開始自開發環境同步至正式環境...
echo 來源: %SOURCE%
echo 目標: %TARGET%
echo ============================================================

set /p confirm="確定要同步嗎？這將會更新正式環境的程式碼 (Y/N): "
if /i "%confirm%" neq "Y" (
    echo [取消] 部署已中止。
    pause
    exit /b
)

:: 使用 robocopy 同步
:: /E (包含子目錄), /MT (多執行緒加速), /Z (可繼續傳輸)
:: /XD (排除資料夾), /XF (排除檔案)
:: 排除項目說明:
:: .git: 版本紀錄 (正式環境不需要版本庫)
:: __pycache__: Python 快取檔
:: backups: 各自環境的備份
:: .playwright-mcp: 測試暫存區
:: .env: 環境標記 (正式環境需保留 APP_ENV=production)
:: *.db*: 資料庫檔案 (避免覆蓋正式資料)

robocopy %SOURCE% %TARGET% /E /MT:8 /Z ^
    /XD .git __pycache__ backups .playwright-mcp .vscode .idea gitea_server ^
    /XF .env *.db *.db-shm *.db-wal *.log *.png deploy_to_prod.bat

echo ============================================================
echo [完成] 程式碼同步已結束。
echo.
echo 注意事項:
echo 1. 已自動排除 .env 與 *.db 檔案，不會影響正式環境資料。
echo 2. 請記得到正式環境 (Port 8000) 確認重啟服務。
echo ============================================================
pause
