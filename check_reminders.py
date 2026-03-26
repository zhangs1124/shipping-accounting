import sqlite3
from datetime import datetime

conn = sqlite3.connect("shipping.db")
cursor = conn.cursor()
cursor.execute("SELECT id, title, remind_type, frequency, next_remind_at, last_reminded_at FROM reminders WHERE is_closed=0;")
rows = cursor.fetchall()

with open("reminders_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Current time: {datetime.now()}\n")
    f.write(f"Found {len(rows)} unclosed reminders:\n")
    for row in rows:
        f.write(str(row) + "\n")
conn.close()
