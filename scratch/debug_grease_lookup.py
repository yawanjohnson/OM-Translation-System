import sqlite3
from modules.db_manager import DBManager, _normalize

db = DBManager('data/translations.db')
eng_text = "NOTE: A light application of grease may aid in the installation of hardware. Any grease, such as lithium bike grease is recommended"

print("Original search text:", repr(eng_text))
print("Normalized search text:", repr(_normalize(eng_text).lower()))

# Run lookup
row = db.lookup_eng(eng_text)
if row:
    print("\nLookup found row:")
    for k, v in row.items():
        if v:
            print(f"  {k}: {repr(v)}")
else:
    print("\nLookup returned None!")
    
# Let's inspect raw rows containing grease
conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM translations WHERE "ENG" LIKE "%grease%"')
rows = cursor.fetchall()
print("\nRaw database rows containing 'grease':")
for r in rows:
    print(f"ID {r['id']}:")
    print(f"  ENG: {repr(r['ENG'])}")
    print(f"  CHT: {repr(r['CHT'])}")
    print(f"  Normalized ENG: {repr(_normalize(r['ENG'] or '').lower())}")
conn.close()
