import sqlite3
import os

db_path = os.path.join("data", "translations.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== Search for TIME related entries ===")
rows = cursor.execute("SELECT id, \"ENG\", \"CHT\" FROM translations WHERE \"ENG\" LIKE ?", ("%Set goals for Time%",)).fetchall()
for r in rows:
    print(f"  ID: {r['id']} | ENG: {repr(r['ENG'])} | CHT: {repr(r['CHT'])}")
    print("-" * 50)

print("\n=== Search for FAT BURN related entries ===")
rows = cursor.execute("SELECT id, \"ENG\", \"CHT\" FROM translations WHERE \"ENG\" LIKE ?", ("%specifically to target fat%",)).fetchall()
for r in rows:
    print(f"  ID: {r['id']} | ENG: {repr(r['ENG'])} | CHT: {repr(r['CHT'])}")
    print("-" * 50)

print("\n=== Search for MANUAL related entries ===")
rows = cursor.execute("SELECT id, \"ENG\", \"CHT\" FROM translations WHERE \"ENG\" LIKE ?", ("%Adjust your speed manually during your workout%",)).fetchall()
for r in rows:
    print(f"  ID: {r['id']} | ENG: {repr(r['ENG'])} | CHT: {repr(r['CHT'])}")
    print("-" * 50)

conn.close()
