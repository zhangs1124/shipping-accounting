import sqlite3
import os

DB_PATH = r"d:\project\Voyage\shipping-accounting-prod\shipping.db"

def check_schema():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"--- 檢查正式環境資料庫: {DB_PATH} ---")
    
    # 檢查 table 定義
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='voyages';")
    print(f"Voyages Table SQL:\n{cursor.fetchone()[0]}")
    
    # 檢查索引
    print("\nVoyages Indices:")
    cursor.execute("PRAGMA index_list('voyages');")
    indices = cursor.fetchall()
    for idx in indices:
        print(f"Index Name: {idx[1]}, Unique: {idx[2]}")
        cursor.execute(f"PRAGMA index_info('{idx[1]}');")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  Column: {col[2]}")

    conn.close()

if __name__ == "__main__":
    check_schema()
