import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Search for any row containing 'Heart rate monitoring'
cursor.execute('SELECT * FROM translations WHERE "ENG" LIKE "%Heart rate monitoring%"')
rows = cursor.fetchall()
print("=== DB SEARCH FOR 'Heart rate monitoring' ===")
for r in rows:
    print(f"ID {r['id']}:")
    print(f"  ENG: {repr(r['ENG'])}")
    print(f"  FRE: {repr(r['FRE'])}")
    print(f"  CHT: {repr(r['CHT'])}")
conn.close()
