import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

search_queries = [
    "116 x 85 x 154",
    "reduced physical",
    "supervised or instructed by a person"
]

print("=== SEARCHING DB FOR BFX26 STRINGS ===")
for q in search_queries:
    cursor.execute('SELECT id, ENG, CHT FROM translations WHERE "ENG" LIKE ?', (f"%{q}%",))
    rows = cursor.fetchall()
    print(f"\nQuery: '{q}' ({len(rows)} matches)")
    for r in rows:
        print(f"  ID {r['id']}:")
        print(f"    ENG: {repr(r['ENG'])}")
        print(f"    CHT: {repr(r['CHT'])}")

conn.close()
