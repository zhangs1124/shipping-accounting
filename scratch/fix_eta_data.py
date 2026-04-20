import sqlite3

conn = sqlite3.connect('shipping.db')
cursor = conn.cursor()

# Get all voyages
cursor.execute("SELECT id, eta FROM voyages")
voyages = cursor.fetchall()

for vid, eta in voyages:
    if eta and ' ' not in eta and 'T' not in eta:
        new_eta = f"{eta} 00:00:00"
        print(f"Updating voyage {vid}: {eta} -> {new_eta}")
        cursor.execute("UPDATE voyages SET eta = ? WHERE id = ?", (new_eta, vid))

conn.commit()
conn.close()
