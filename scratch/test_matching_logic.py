import os
import re
import sqlite3
from modules.db_manager import DBManager, clean_text, split_prefix_suffix

db_path = os.path.join("data", "translations.db")
db = DBManager(db_path)

raw_texts = [
    'P1)\tmanual: Adjust your speed manually during your workout.',
    'P2) DISTANCE: Push yourself and go further during your workout with 13 distance workouts. Choose from L1: 1.6 km,     \u2028       L2: 3.2 km, L3: 5km, L4: 8 km, L5: 10km, L6: 12.8 km, L7: 15km, L8: 16 km, L9: 20km, L10: half marathon, \u2028       L11: 24 km, L12: 32 km and L13: marathon goals. User sets starting speed levels.',
    'P3)\tTime: Set goals for Time. User could set up the speed and Incline to start.',
    'P4) CALORIES: Set goals for burning calories. Calories burned are calculated using distance and speed.',
    'P5)\tFAT BURN: A workout designed specifically to target fat. Promotes weight loss by increasing and decreasing the \t\tspeed, while keeping you in your fat burning zone. Includes 10 levels.'
]

for raw in raw_texts:
    print(f"Raw text: {repr(raw)}")
    
    # 1. replace returns and CJK/spaces
    cleaned_part = clean_text(raw.replace('\r', '\n').replace('\u2028', '\n').replace('\u2029', '\n'))
    print(f"  Cleaned part: {repr(cleaned_part)}")
    
    # 2. split prefix and suffix
    prefix, core, suffix = split_prefix_suffix(cleaned_part)
    core_cleaned = clean_text(core)
    print(f"  Prefix: {repr(prefix)} | Core: {repr(core_cleaned)} | Suffix: {repr(suffix)}")
    
    # 3. Lookup exact match in DB
    exact = db.lookup_eng(core_cleaned)
    if exact:
        print(f"  --> EXACT MATCH FOUND in DB (ID: {exact['id']})")
        print(f"      CHT: {repr(exact.get('CHT'))}")
    else:
        print("  --> NO EXACT MATCH")
        # 4. Lookup similar match in DB
        similar = db.find_similar_eng(core_cleaned)
        if similar:
            print(f"  --> SIMILAR MATCH FOUND (ID: {similar['id']}, Similarity: {similar['similarity'] * 100:.1f}%)")
            print(f"      ENG in DB: {repr(similar['ENG'])}")
            print(f"      CHT in DB: {repr(similar['CHT'])}")
        else:
            print("  --> NO SIMILAR MATCH")
            
    print("=" * 60)
