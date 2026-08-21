import sqlite3
import os

db_path = os.path.join("data", "translations.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

patterns = ["%MANUAL%", "%DISTANCE%", "%TIME%", "%CALORIES%", "%FAT BURN%"]
for p in patterns:
    print(f"=== Pattern: {p} ===")
    rows = cursor.execute("SELECT id, \"ENG\", \"CHT\" FROM translations WHERE \"ENG\" LIKE ?", (p,)).fetchall()
    for r in rows:
        print(f"  ID: {r['id']}")
        print(f"  ENG: {repr(r['ENG'])}")
        print(f"  CHT: {repr(r['CHT'])}")
        print("-" * 40)

conn.close()
