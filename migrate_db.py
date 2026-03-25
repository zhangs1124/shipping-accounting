import sqlite3

def migrate():
    conn = sqlite3.connect('shipping.db')
    cursor = conn.cursor()
    
    # 檢查並新增 is_reminded
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN is_reminded INTEGER DEFAULT 0")
        print("✅ 新增欄位 is_reminded 成功")
    except sqlite3.OperationalError:
        print("⚠️ 欄位 is_reminded 已存在")

    # 檢查並新增 last_reminded_at
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN last_reminded_at DATETIME")
        print("✅ 新增欄位 last_reminded_at 成功")
    except sqlite3.OperationalError:
        print("⚠️ 欄位 last_reminded_at 已存在")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
