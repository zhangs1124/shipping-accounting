import sqlite3
conn = sqlite3.connect('shipping.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(voyages)")
for row in cursor.fetchall():
    print(row)
conn.close()
