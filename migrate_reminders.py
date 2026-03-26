import sqlite3
import os

DB_PATH = "shipping.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Checking for column additions...")
    
    # 1. Update task_categories
    try:
        cursor.execute("ALTER TABLE task_categories ADD COLUMN base_milestone VARCHAR")
        print("Added base_milestone to task_categories.")
    except sqlite3.OperationalError:
        print("base_milestone already exists in task_categories.")

    try:
        cursor.execute("ALTER TABLE task_categories ADD COLUMN expected_offset_hours INTEGER DEFAULT 0")
        print("Added expected_offset_hours to task_categories.")
    except sqlite3.OperationalError:
        print("expected_offset_hours already exists in task_categories.")

    # 2. Update voyages
    try:
        cursor.execute("ALTER TABLE voyages ADD COLUMN operator_id INTEGER REFERENCES employees(id)")
        print("Added operator_id to voyages.")
    except sqlite3.OperationalError:
        print("operator_id already exists in voyages.")

    # 3. Create reminders table (if not exists)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR NOT NULL,
        content TEXT,
        remind_type VARCHAR DEFAULT 'TASK_OVERDUE',
        source_table VARCHAR,
        source_id INTEGER,
        target_employee_id INTEGER NOT NULL REFERENCES employees(id),
        is_closed INTEGER DEFAULT 0,
        deadline DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Ensured reminders table exists.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
