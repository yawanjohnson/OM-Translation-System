import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

keywords = ["pinch", "handlebars", "crank", "Schwinn", "Upright"]

print("=== KEYWORD SEARCH ===")
for kw in keywords:
    cursor.execute('SELECT id, ENG, CHT FROM translations WHERE "ENG" LIKE ? LIMIT 5', (f"%{kw}%",))
    rows = cursor.fetchall()
    print(f"\nKeyword: {kw} ({len(rows)} matches found)")
    for r in rows:
        print(f"  ID: {r['id']}")
        print(f"    ENG: {repr(r['ENG'])}")
        print(f"    CHT: {repr(r['CHT'])}")

conn.close()
