import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

terms = ["reverse", "pinch", "wire", "crank", "tip", "transport", "grasp"]

print("=== DETAILED DB TERM SEARCH ===")
for term in terms:
    cursor.execute('SELECT id, ENG, CHT FROM translations WHERE "ENG" LIKE ?', (f"%{term}%",))
    rows = cursor.fetchall()
    print(f"\nTerm: {term} ({len(rows)} matches)")
    for r in rows:
        print(f"  ID {r['id']}: ENG={repr(r['ENG'])}, CHT={repr(r['CHT'])}")

conn.close()
