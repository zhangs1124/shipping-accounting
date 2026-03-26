import sqlite3

def upgrade_reminders_table():
    print("Migrating reminders table...")
    conn = sqlite3.connect("shipping.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE reminders ADD COLUMN frequency VARCHAR DEFAULT 'ONCE'")
        print("Column 'frequency' added.")
    except sqlite3.OperationalError as e:
        print(f"Skipped frequency: {e}")
        
    try:
        cursor.execute("ALTER TABLE reminders ADD COLUMN last_reminded_at DATETIME")
        print("Column 'last_reminded_at' added.")
    except sqlite3.OperationalError as e:
        print(f"Skipped last_reminded_at: {e}")
        
    try:
        cursor.execute("ALTER TABLE reminders ADD COLUMN next_remind_at DATETIME")
        print("Column 'next_remind_at' added.")
    except sqlite3.OperationalError as e:
        print(f"Skipped next_remind_at: {e}")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    upgrade_reminders_table()
