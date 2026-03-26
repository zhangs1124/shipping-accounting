import os
import time
from tasks.backup_tasks import backup_sqlite_db, cleanup_old_backups, BACKUP_DIR

def test_backup():
    print(">>> 測試 1: 執行備份...")
    backup_sqlite_db()
    
    # 檢查是否產生檔案
    files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("shipping_backup_")]
    if files:
        print(f"✅ 成功產生備份檔案: {files[-1]}")
    else:
        print("❌ 未產生備份檔案")

def test_cleanup():
    print("\n>>> 測試 2: 執行清理 (模擬 8 天前的舊檔案)...")
    
    # 手動建立一個「舊」檔案
    old_file = os.path.join(BACKUP_DIR, "shipping_backup_old_test.db")
    with open(old_file, "w") as f:
        f.write("test content")
    
    # 修改 存取時間 與 修改時間 為 8 天前
    eight_days_ago = time.time() - (8 * 24 * 60 * 60)
    os.utime(old_file, (eight_days_ago, eight_days_ago))
    
    print(f"已建立模擬舊檔案: {old_file}")
    
    # 執行清理
    cleanup_old_backups()
    
    # 檢查檔案是否還在
    if not os.path.exists(old_file):
        print("✅ 舊檔案已成功刪除")
    else:
        print("❌ 舊檔案仍然存在")

if __name__ == "__main__":
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    test_backup()
    test_cleanup()
