import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM translations WHERE "ENG" LIKE "%MOVING THE EXERCISE BIKE%"')
rows = cursor.fetchall()
print("=== DB SEARCH FOR 'MOVING THE EXERCISE BIKE' ===")
for r in rows:
    print(f"ID {r['id']}:")
    print(f"  ENG: {repr(r['ENG'])}")
    print(f"  FRE: {repr(r['FRE'])}")
    print(f"  CHT: {repr(r['CHT'])}")
    
cursor.execute('SELECT * FROM translations WHERE "ENG" LIKE "%Your exercise bike has a pair of transport wheels%"')
rows2 = cursor.fetchall()
print("\n=== DB SEARCH FOR 'Your exercise bike has a pair...' ===")
for r in rows2:
    print(f"ID {r['id']}:")
    print(f"  ENG: {repr(r['ENG'])}")
    print(f"  FRE: {repr(r['FRE'])}")
    print(f"  CHT: {repr(r['CHT'])}")
conn.close()
