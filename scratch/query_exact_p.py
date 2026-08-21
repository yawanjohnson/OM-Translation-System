import sqlite3
import os

db_path = os.path.join("data", "translations.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== Search by P1-P5 prefix ===")
for prefix in ["P1%", "P2%", "P3%", "P4%", "P5%"]:
    rows = cursor.execute("SELECT id, \"ENG\", \"CHT\" FROM translations WHERE \"ENG\" LIKE ?", (prefix,)).fetchall()
    print(f"Prefix: {prefix} ({len(rows)} found)")
    for r in rows:
        print(f"  ID: {r['id']} | ENG: {repr(r['ENG'])} | CHT: {repr(r['CHT'])}")
        print("-" * 50)

conn.close()
