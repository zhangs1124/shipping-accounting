import sqlite3
import os

def migrate():
    db_path = "shipping.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Checking for ChargePackage tables...")
    
    # 建立 charge_packages 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS charge_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 建立 charge_package_items 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS charge_package_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package_id INTEGER NOT NULL,
        charge_item_id INTEGER NOT NULL,
        default_quantity DECIMAL(18, 4) DEFAULT 1,
        FOREIGN KEY (package_id) REFERENCES charge_packages (id) ON DELETE CASCADE,
        FOREIGN KEY (charge_item_id) REFERENCES charge_items (id)
    )
    """)

    conn.commit()
    conn.close()
    print("Migration successful: ChargePackage tables created.")

if __name__ == "__main__":
    migrate()
