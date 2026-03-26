import os
import sqlite3
import shutil
from datetime import datetime, timedelta
import time

# 設定
DB_PATH = "shipping.db"
BACKUP_DIR = "backups"
RETENTION_DAYS = 7

def backup_sqlite_db():
    """
    執行 SQLite 線上備份。
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_file = os.path.join(BACKUP_DIR, f"shipping_backup_{timestamp}.db")
    
    print(f"[{datetime.now()}] 正在執行資料庫備份至: {backup_file}...")
    
    try:
        # 使用 sqlite3 的 backup API 進行線上備份
        # 這會安全地處理 WAL 並避免鎖定
        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(backup_file)
        
        with dst:
            src.backup(dst)
            
        dst.close()
        src.close()
        
        print(f"[{datetime.now()}] 備份成功。")
        
        # 備份完後執行清理
        cleanup_old_backups()
        
    except Exception as e:
        print(f"[{datetime.now()}] 備份失敗: {e}")

def cleanup_old_backups():
    """
    刪除超過指定天數的備份檔案。
    """
    print(f"[{datetime.now()}] 正在檢查並清理超過 {RETENTION_DAYS} 天的舊備份...")
    
    now = time.time()
    retention_seconds = RETENTION_DAYS * 24 * 60 * 60
    
    count = 0
    try:
        if not os.path.exists(BACKUP_DIR):
            return
            
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith("shipping_backup_") and filename.endswith(".db"):
                file_path = os.path.join(BACKUP_DIR, filename)
                # 取得檔案修改時間
                file_time = os.path.getmtime(file_path)
                
                if now - file_time > retention_seconds:
                    os.remove(file_path)
                    print(f"已刪除舊備份: {filename}")
                    count += 1
        
        if count == 0:
            print("無須清理任何檔案。")
        else:
            print(f"清理完成，共刪除 {count} 個檔案。")
            
    except Exception as e:
        print(f"[{datetime.now()}] 清理舊備份時發生錯誤: {e}")

if __name__ == "__main__":
    # 手動測試執行
    backup_sqlite_db()
