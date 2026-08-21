from modules.db_manager import DBManager

db = DBManager('data/translations.db')

print("=== TEST DB TRANSLATION CLEANING ===")

# Case 1: Lookup "Rear Stabilizer" (should get Stabilisateur arrière)
row1 = db.lookup_eng("Rear Stabilizer")
print("\nLookup: 'Rear Stabilizer'")
if row1:
    print(f"  FRE: {repr(row1.get('FRE'))}")
    print(f"  CHT: {repr(row1.get('CHT'))}")

# Case 2: Lookup "Rear Stabilizer (15)"
row2 = db.lookup_eng("Rear Stabilizer (15)")
print("\nLookup: 'Rear Stabilizer (15)'")
if row2:
    print(f"  FRE: {repr(row2.get('FRE'))}")
    print(f"  CHT: {repr(row2.get('CHT'))}")
