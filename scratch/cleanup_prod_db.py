import sqlite3
import os

DB_PATH = r"d:\project\Voyage\shipping-accounting-prod\shipping.db"

def cleanup():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 依照正確順序刪除資料 (子表先刪，父表後刪)
    tables_to_clear = [
        "invoice_lines",     # 1. 帳單明細
        "invoices",          # 2. 帳單主檔
        "voyage_task_logs",  # 3. 航次任務紀錄
        "reminders",         # 4. 提醒中心訊息 (通常與航次/帳單相關)
        "voyages",           # 5. 航次主檔
        "ships"              # 6. 船舶主檔
    ]

    print("--- 開始清理正式環境業務資料 ---")

    try:
        # 暫時關閉外鍵檢查以便執行 (某些情況下較快，但循序刪除較安全)
        # cursor.execute("PRAGMA foreign_keys = OFF;")
        
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table};")
            count = cursor.rowcount
            # 檢查 sqlite_sequence 是否存在再進行重設
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
            if cursor.fetchone():
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
            print(f"表格 [{table}]: 已刪除 {count} 筆資料。")

        conn.commit()
        print("--- 清理成功完成 ---")
    except Exception as e:
        conn.rollback()
        print(f"--- 清理失敗: {e} ---")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup()
