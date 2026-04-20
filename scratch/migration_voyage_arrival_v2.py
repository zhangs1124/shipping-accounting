import sqlite3
import os

db_path = 'shipping.db'

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Checking for arrival_date column in voyages table...")
    cursor.execute("PRAGMA table_info(voyages)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'arrival_date' not in columns:
        print("Adding arrival_date column to voyages table...")
        try:
            cursor.execute("ALTER TABLE voyages ADD COLUMN arrival_date DATETIME")
            conn.commit()
            print("Successfully added arrival_date column.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("arrival_date column already exists.")

    conn.close()

if __name__ == "__main__":
    migrate()
