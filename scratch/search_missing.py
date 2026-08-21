import sqlite3
from modules.db_manager import _normalize, clean_text, split_prefix_suffix, should_skip_translation

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

test_cases = [
    "NOTE: Be careful not to pinch any wires while assembling handlebars.",
    "NOTE: Left crank arm is reverse threaded so it is very important to tighten counter-clockwise. Tightening the opposite direction can damage pedal or crank arm.",
    "Upright Bikes & INDOOR CYCLES: firmly grasp the handlebars, carefully tip toward you, and roll on the transport wheels.",
    "MODEL NAME:  Schwinn      UPRIGHT BIKE",
    "80",
    "4"
]

print("=== DB SEARCH TEST ===")
for tc in test_cases:
    print(f"\nSearching for: {repr(tc)}")
    print(f"  Cleaned text: {repr(clean_text(tc))}")
    print(f"  Should skip: {should_skip_translation(tc)}")
    
    # Split prefix suffix
    prefix, core, suffix = split_prefix_suffix(clean_text(tc))
    print(f"  Split results: prefix={repr(prefix)}, core={repr(core)}, suffix={repr(suffix)}")
    
    # Query database
    # Let's search exact matching
    cursor.execute('SELECT * FROM translations WHERE "ENG" = ?', (tc,))
    exact = cursor.fetchall()
    print(f"  Exact Match: {len(exact)} rows found")
    for r in exact:
        print(f"    ID: {r['id']}, ENG: {repr(r['ENG'])}, CHT: {repr(r['CHT'])}, FRE: {repr(r['FRE'])}")
        
    # Let's search core exact matching
    cursor.execute('SELECT * FROM translations WHERE "ENG" = ?', (core,))
    core_exact = cursor.fetchall()
    print(f"  Core Exact Match: {len(core_exact)} rows found")
    for r in core_exact:
        print(f"    ID: {r['id']}, ENG: {repr(r['ENG'])}, CHT: {repr(r['CHT'])}, FRE: {repr(r['FRE'])}")

    # Let's search normalized case-insensitive matching
    norm_tc = _normalize(tc).lower()
    norm_core = _normalize(core).lower()
    print(f"  Normalized search value (core): {repr(norm_core)}")
    
    # Let's retrieve all rows and check normalized
    cursor.execute('SELECT * FROM translations WHERE "ENG" IS NOT NULL AND "ENG" != ""')
    all_rows = cursor.fetchall()
    matches = []
    core_matches = []
    for r in all_rows:
        db_val = r['ENG'] or ''
        norm_db = _normalize(db_val).lower()
        if norm_db == norm_tc:
            matches.append(r)
        if norm_db == norm_core:
            core_matches.append(r)
            
    print(f"  Normalized Match (full): {len(matches)} rows found")
    for r in matches:
        print(f"    ID: {r['id']}, ENG: {repr(r['ENG'])}, CHT: {repr(r['CHT'])}, FRE: {repr(r['FRE'])}")
        
    print(f"  Normalized Match (core): {len(core_matches)} rows found")
    for r in core_matches:
        print(f"    ID: {r['id']}, ENG: {repr(r['ENG'])}, CHT: {repr(r['CHT'])}, FRE: {repr(r['FRE'])}")
        
    # If no matches, check substring matching
    if not matches and not core_matches:
        keywords = [w for w in core.split() if len(w) > 4]
        if keywords:
            query = " AND ".join([f'"ENG" LIKE ?' for _ in keywords])
            params = [f"%{w}%" for w in keywords]
            cursor.execute(f'SELECT * FROM translations WHERE {query} LIMIT 3', params)
            partial = cursor.fetchall()
            print(f"  Partial Substring Matches (using {keywords[:3]}): {len(partial)} rows found")
            for r in partial:
                print(f"    ID: {r['id']}, ENG: {repr(r['ENG'])}, CHT: {repr(r['CHT'])}, FRE: {repr(r['FRE'])}")

conn.close()
