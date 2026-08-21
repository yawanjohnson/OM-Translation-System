import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM translations WHERE "ENG" LIKE "%Insert Left Pedal%"')
rows = cursor.fetchall()
print("=== DB SEARCH FOR 'Insert Left Pedal' ===")
for r in rows:
    print(f"ID {r['id']}:")
    print(f"  ENG: {repr(r['ENG'])}")
    print(f"  CHT: {repr(r['CHT'])}")
conn.close()
