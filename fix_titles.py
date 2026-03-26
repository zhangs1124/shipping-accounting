import sqlite3

conn = sqlite3.connect("shipping.db")
cursor = conn.cursor()
cursor.execute("UPDATE reminders SET title = REPLACE(title, '每次(每天)', '每分鐘') WHERE frequency = 'MINUTELY' AND title LIKE '%每次(每天)%';")
cursor.execute("UPDATE reminders SET title = REPLACE(title, '每次(每天)', '每小時') WHERE frequency = 'HOURLY' AND title LIKE '%每次(每天)%';")
conn.commit()
conn.close()
