import sqlite3
import os
import shutil

def migrate_db(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    print(f"--- 開始處理資料庫: {db_path} ---")
    
    # 建立備份
    backup_path = db_path + ".bak"
    shutil.copy2(db_path, backup_path)
    print(f"已建立備份: {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. 取得舊表的建立 SQL (含原有的欄位定義)
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='voyages';")
        create_sql = cursor.fetchone()[0]
        print(f"舊表 SQL: {create_sql}")

        # 2. 重新設定外鍵檢查 (暫時關閉)
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # 3. 建立新表 (暫定名稱 voyages_new)
        # 注意：我們需要手動組合新的建立 SQL，移除原本欄位上的 UNIQUE，並加入複合 UNIQUE
        # 這裡採取最保險的方法：直接寫死符合 models.py 的新 SQL
        new_create_sql = """
        CREATE TABLE voyages_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
            voyage_no VARCHAR NOT NULL, 
            ship_id INTEGER NOT NULL, 
            port_of_loading VARCHAR, 
            port_of_discharge VARCHAR, 
            etd DATE, 
            eta DATE, 
            status VARCHAR, 
            operator_id INTEGER, 
            created_at DATETIME, 
            updated_at DATETIME, 
            FOREIGN KEY(ship_id) REFERENCES ships (id), 
            FOREIGN KEY(operator_id) REFERENCES employees (id),
            UNIQUE (ship_id, voyage_no)
        );
        """
        cursor.execute(new_create_sql)
        print("已建立新表 voyages_new")

        # 4. 搬移資料
        cursor.execute("""
            INSERT INTO voyages_new (
                id, voyage_no, ship_id, port_of_loading, port_of_discharge, 
                etd, eta, status, operator_id, created_at, updated_at
            )
            SELECT 
                id, voyage_no, ship_id, port_of_loading, port_of_discharge, 
                etd, eta, status, operator_id, created_at, updated_at
            FROM voyages;
        """)
        print(f"已從舊表搬移 {cursor.rowcount} 筆資料")

        # 5. 刪除舊表並重新命名新表
        cursor.execute("DROP TABLE voyages;")
        cursor.execute("ALTER TABLE voyages_new RENAME TO voyages;")
        print("已完成表格更換")

        # 6. 重新建立索引 (原本 id 有 index)
        cursor.execute("CREATE INDEX ix_voyages_id ON voyages (id);")
        cursor.execute("CREATE INDEX ix_voyages_voyage_no ON voyages (voyage_no);")
        print("已建立索引")

        conn.commit()
        print(f"--- {db_path} 遷移成功 ---")

    except Exception as e:
        conn.rollback()
        print(f"--- {db_path} 遷移失敗: {e} ---")
    finally:
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.close()

if __name__ == "__main__":
    # 分別處理開發與正式環境
    dbs = [
        r"d:\project\Voyage\shipping-accounting\shipping_dev.db",
        r"d:\project\Voyage\shipping-accounting-prod\shipping.db"
    ]
    for db in dbs:
        migrate_db(db)
