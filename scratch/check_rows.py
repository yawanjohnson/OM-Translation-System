import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT id, ENG, CHT FROM translations WHERE id BETWEEN 1080 AND 1100')
rows = cursor.fetchall()
print("=== DB ROWS 1080-1100 ===")
for r in rows:
    print(f"ID {r['id']}:")
    print(f"  ENG: {repr(r['ENG'])}")
    print(f"  CHT: {repr(r['CHT'])}")

conn.close()
