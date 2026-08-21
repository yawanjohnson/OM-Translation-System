from modules.db_manager import DBManager, split_prefix_suffix, split_step_number

# Test 1: Suffix/Prefix Stripping
test_cases = [
    "□ Handlebar Set (30)",
    "Console Mast (33)",
    "  • Hardware Pack (4,5) : ",
    "ASSEMBLY STEP 3"
]

print("=== TEST 1: PREFIX/SUFFIX STRIPPING ===")
for tc in test_cases:
    p, c, s = split_prefix_suffix(tc)
    print(f"Input: {repr(tc)}")
    print(f"  Prefix: {repr(p)}")
    print(f"  Core:   {repr(c)}")
    print(f"  Suffix: {repr(s)}")

# Test 2: DB Lookup and Step Remapping
db = DBManager('data/translations.db')

print("\n=== TEST 2: STEP REMAP LOOKUP ===")
# Let's see if we have ASSEMBLY STEP 1 or similar in database
# We will lookup 'ASSEMBLY STEP 3' in Chinese
row = db.lookup_eng("ASSEMBLY STEP 3")
if row:
    print("Found step remapped translation:")
    print(f"  ENG: {repr(row['ENG'])}")
    print(f"  CHT: {repr(row.get('CHT'))}")
    print(f"  FRE: {repr(row.get('FRE'))}")
    print(f"  GER: {repr(row.get('GER'))}")
else:
    print("Step remapped translation NOT found.")
