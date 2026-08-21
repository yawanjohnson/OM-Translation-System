import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

targets = ["Rear Stabilizer", "Seat Adjustment Knob", "Crank Arms"]
print("=== DB LOOKUPS ===")
for t in targets:
    cursor.execute('SELECT * FROM translations WHERE "ENG" = ?', (t,))
    row = cursor.fetchone()
    if row:
        print(f"Match exact for {repr(t)}:")
        print(f"  FRE: {repr(row['FRE'])}")
        print(f"  CHT: {repr(row['CHT'])}")
    else:
        # try LIKE
        cursor.execute('SELECT * FROM translations WHERE "ENG" LIKE ?', (f"%{t}%",))
        rows = cursor.fetchall()
        print(f"LIKE matches for {repr(t)}:")
        for r in rows:
            print(f"  ID {r['id']}: ENG: {repr(r['ENG'])} | FRE: {repr(r['FRE'])}")

conn.close()
