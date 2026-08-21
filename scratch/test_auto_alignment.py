import re

def detect_language(text):
    if not text:
        return 'ENG'
    text = text.lower()
    if any(c in text for c in ('ä', 'ö', 'ü', 'ß')):
        return 'GER'
        
    STOP_WORDS = {
        'GER': {'der', 'die', 'das', 'und', 'ist', 'in', 'zu', 'den', 'dem', 'mit', 'von', 'für', 'anzeigefenster', 'steigung'},
        'ENG': {'the', 'and', 'is', 'in', 'to', 'of', 'for', 'on', 'with', 'at', 'incline', 'calories', 'speed', 'time', 'distance'},
        'DUT': {'de', 'het', 'een', 'en', 'van', 'ik', 'te', 'dat', 'die', 'in', 'voor', 'met'},
        'DAN': {'og', 'i', 'jeg', 'det', 'at', 'en', 'den', 'til', 'med', 'på'},
        'FRE': {'le', 'la', 'les', 'et', 'un', 'une', 'en', 'que', 'est', 'dans', 'pour', 'avec'},
        'SPA': {'el', 'la', 'los', 'las', 'un', 'una', 'y', 'es', 'en', 'con', 'para', 'por'},
        'ITA': {'il', 'la', 'i', 'gli', 'le', 'un', 'una', 'e', 'di', 'in', 'per', 'con'},
        'POL': {'w', 'i', 'z', 'na', 'do', 'o', 'że', 'to', 'nie', 'się'},
        'PRB': {'o', 'a', 'os', 'as', 'um', 'uma', 'e', 'em', 'com', 'para', 'por'},
        'RUS': {'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со'},
        'TRK': {'bir', 've', 'bu', 'ne', 'da', 'de', 'için', 'ile', 'en', 'o'},
        'GRK': {'και', 'το', 'του', 'τα', 'στην', 'στο', 'την', 'της', 'από', 'που'},
        'VTM': {'và', 'là', 'trong', 'của', 'được', 'một', 'có', 'cho', 'với', 'người'},
        'THI': {'และ', 'ใน', 'เป็น', 'ของ', 'ได้', 'มี', 'การ', 'ที่', 'ให้', 'กับ'},
        'ARB': {'من', 'في', 'على', 'و', 'أن', 'إلى', 'هذا', 'هذه', 'مع', 'كل'},
        'JPN': {'の', 'に', 'は', 'と', 'を', 'た', 'が', 'で', 'て', 'し'},
        'KOR': {'이', '그', '저', '을', '를', '은', '는', '이', '가', '에'},
        'CHT': set("的是在有個這我我們你們他們與或及以於"),
        'CHS': set("的是在有个这我我们你们他们与或及以于")
    }
    
    words = set(re.findall(r'[a-zA-Z\u00C0-\u024F]+', text))
    scores = {}
    for lang, sw in STOP_WORDS.items():
        if lang in ('CHT', 'CHS'):
            chars = set(text)
            scores[lang] = len(chars.intersection(sw))
        else:
            scores[lang] = len(words.intersection(sw))
            
    max_lang = max(scores, key=scores.get)
    if scores[max_lang] > 0:
        return max_lang
    return 'ENG'

def clean_and_validate_extracted_text(text):
    import re
    if not text:
        return None
    text = text.strip()
    
    # 1. Must contain at least one Chinese character, OR at least one word (with letters and length >= 2)
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
    has_word = re.search(r'\b[a-zA-Z\u00C0-\u024F]{2,}\b', text)
    if not (has_chinese or has_word):
        return None
        
    # 2. Strip leading bullets, layout decorations, and common list items
    cleaned = re.sub(r'^[•▪▲⏰■○●□◇◆▫★☆☞☞▶▷➔➜\-\*\+•\s]+', '', text)
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    return cleaned

def merge_blocks(blocks, index):
    if index < 0 or index >= len(blocks) - 1:
        return blocks
    b1 = blocks[index]
    b2 = blocks[index + 1]
    
    t1 = b1['text']
    t2 = b2['text']
    
    # Concatenate with space if both end/start with western alphabetical characters
    needs_space = re.search(r'[a-zA-Z\u00C0-\u024F]$', t1) and re.match(r'^[a-zA-Z\u00C0-\u024F]', t2)
    b1['text'] = t1 + (" " if needs_space else "") + t2
    
    # Remove the next block
    blocks.pop(index + 1)
    return blocks

def extract_keywords(text):
    keywords = []
    # Match words inside parenthesis
    paren_matches = re.findall(r'\(([^)]+)\)', text)
    for m in paren_matches:
        word = m.strip().upper()
        if len(word) >= 3:
            keywords.append(word)
            
    # Match uppercase words of length >= 3
    upper_matches = re.findall(r'[A-Z]{3,}', text)
    for w in upper_matches:
        if w not in keywords:
            keywords.append(w)
    return keywords

def align_blocks_to_table(table_rows, new_blocks, lang_code):
    aligned_rows = [dict(r) for r in table_rows] # Clean copy
    
    for block in new_blocks:
        text = block['text']
        matched_idx = -1
        
        if len(aligned_rows) > 0:
            keywords = extract_keywords(text)
            
            # Find parenthesis keywords
            block_parens = []
            paren_matches = re.findall(r'\(([^)]+)\)', text)
            for m in paren_matches:
                word = m.strip().upper()
                if len(word) >= 3:
                    block_parens.append(word)
            
            best_score = 0
            for i, row in enumerate(aligned_rows):
                score = 0
                
                if lang_code != 'ENG':
                    # Aligning translation to ENG row
                    eng_text = row.get('ENG', '')
                    eng_upper = eng_text.upper()
                    eng_label = eng_text.split(':')[0].strip().upper()
                    
                    for bp in block_parens:
                        if bp in eng_label:
                            score += 100
                    for kw in keywords:
                        if kw in eng_upper:
                            score += 10
                else:
                    # Aligning ENG to translation row (e.g. CHT, GER)
                    ref_text = ''
                    for key in row:
                        if key != 'ENG' and row[key]:
                            ref_text = row[key]
                            break
                            
                    if ref_text:
                        ref_upper = ref_text.upper()
                        ref_label = ref_text.split(':')[0].strip().upper()
                        
                        ref_parens = []
                        ref_paren_matches = re.findall(r'\(([^)]+)\)', ref_text)
                        for m in ref_paren_matches:
                            word = m.strip().upper()
                            if len(word) >= 3:
                                ref_parens.append(word)
                                
                        for bp in block_parens:
                            if bp in ref_label or bp in ref_parens:
                                score += 100
                        for kw in keywords:
                            if kw in ref_upper:
                                score += 10
                                
                if score > best_score:
                    best_score = score
                    matched_idx = i
                    
        if matched_idx != -1:
            aligned_rows[matched_idx][lang_code] = text
        else:
            new_row = {}
            new_row[lang_code] = text
            aligned_rows.append(new_row)
            
    return aligned_rows

def run_test():
    print("=== STARTING SMART EXTRACTION E2E AUTOMATED ALIGNMENT TEST ===")
    
    # 0. Test Strict Text Validation and Sanitization (Unit number, symbols, Units filter)
    print("\nTesting Strict Text Filtering (Noise reduction):")
    assert clean_and_validate_extracted_text("•") is None
    assert clean_and_validate_extracted_text("12.5") is None
    assert clean_and_validate_extracted_text("1:00") is None
    assert clean_and_validate_extracted_text("• 1,200") is None
    assert clean_and_validate_extracted_text("---") is None
    
    # Good strings should pass:
    assert clean_and_validate_extracted_text("ZEIT") == "ZEIT"
    assert clean_and_validate_extracted_text("時間") == "時間"
    assert clean_and_validate_extracted_text("• ZEIT (TIME)") == "ZEIT (TIME)"  # Strips bullet
    print("✅ Strict Text Filtering passed!")
    
    # 0.5. Test Source-Level Block Merging (with spacing verification)
    print("\nTesting Source-Level Block Merging:")
    test_blocks = [
        {'text': "ZEIT (TIME): Stellen Sie Ihre"},
        {'text': "Trainingszeit ein."}
    ]
    merged = merge_blocks(test_blocks, 0)
    print(f"Merged blocks: {merged}")
    assert len(merged) == 1
    assert merged[0]['text'] == "ZEIT (TIME): Stellen Sie Ihre Trainingszeit ein."
    print("✅ Source-Level Block Merging passed!")
    
    # 1. Test Language Detection
    print("\nTesting Language Detection:")
    eng_text = "TIME: Set goals for Time. User could set up the speed."
    ger_text = "ZEIT (TIME): Stellen Sie Ihre Trainingszeit und -geschwindigkeit ein."
    spa_text = "TIEMPO (TIME): Establezca los objetivos para el tempo."
    dut_text = "TIJD (TIME): Stel de doelen in voor de trainingstijd."
    
    lang_eng = detect_language(eng_text)
    lang_ger = detect_language(ger_text)
    lang_spa = detect_language(spa_text)
    lang_dut = detect_language(dut_text)
    
    print(f"Detected '{eng_text[:15]}...' as: {lang_eng}")
    print(f"Detected '{ger_text[:15]}...' as: {lang_ger}")
    print(f"Detected '{spa_text[:15]}...' as: {lang_spa}")
    print(f"Detected '{dut_text[:15]}...' as: {lang_dut}")
    
    assert lang_eng == 'ENG'
    assert lang_ger == 'GER'
    assert lang_spa == 'SPA'
    assert lang_dut == 'DUT'
    print("✅ Language Detection passed!")
    
    # 2. Test Keyword Extraction
    print("\nTesting Keyword Extraction:")
    kw_1 = extract_keywords("ZEIT (TIME): Stellen Sie...")
    kw_2 = extract_keywords("STEIGUNG (INCLINE): Dargestellt...")
    kw_3 = extract_keywords("CALORIES without parenthesis")
    
    print(f"Keywords for 'ZEIT (TIME)': {kw_1}")
    print(f"Keywords for 'STEIGUNG (INCLINE)': {kw_2}")
    print(f"Keywords for 'CALORIES': {kw_3}")
    
    assert "TIME" in kw_1
    assert "INCLINE" in kw_2
    assert "CALORIES" in kw_3
    print("✅ Keyword Extraction passed!")
    
    # 3. Test Alignment Algorithm Flow
    print("\nTesting Semantic Alignment Flow:")
    
    # Initial state: Uploaded English manual blocks (starts empty, so it populates table with ENG)
    initial_rows = []
    eng_blocks = [
        {'text': "TIME: Set goals for Time."},
        {'text': "INCLINE: Adjust the treadmill incline."},
        {'text': "CALORIES: Check calories burnt."}
    ]
    
    table = align_blocks_to_table(initial_rows, eng_blocks, 'ENG')
    print("Populated table with English:")
    for i, r in enumerate(table):
        print(f"  Row {i}: {r}")
        
    assert len(table) == 3
    assert table[0]['ENG'] == "TIME: Set goals for Time."
    
    # Second upload: German manual blocks (should sense GER and align with matching ENG rows)
    ger_blocks = [
        {'text': "ZEIT (TIME): Stellen Sie Ihre Trainingszeit ein."},
        {'text': "STEIGUNG (INCLINE): Zeigt die gewählte Steigung an."}
    ]
    
    aligned_table = align_blocks_to_table(table, ger_blocks, 'GER')
    print("\nAligned table with German blocks:")
    for i, r in enumerate(aligned_table):
        print(f"  Row {i}: {r}")
        
    assert len(aligned_table) == 3 # Should not create extra rows!
    assert aligned_table[0]['GER'] == "ZEIT (TIME): Stellen Sie Ihre Trainingszeit ein."
    assert aligned_table[1]['GER'] == "STEIGUNG (INCLINE): Zeigt die gewählte Steigung an."
    assert 'GER' not in aligned_table[2] # Calories row has no GER value yet
    
    print("✅ Semantic Alignment Flow passed!")
    
    # 4. Test Single Column Clearing
    print("\nTesting Single Column Clearing:")
    cleared_table = [{**r} for r in aligned_table] # Copy table
    for r in cleared_table:
        r['GER'] = ''
    print(f"Cleared table (GER): {cleared_table}")
    assert cleared_table[0]['ENG'] == "TIME: Set goals for Time."
    assert cleared_table[0]['GER'] == ""
    assert cleared_table[1]['ENG'] == "INCLINE: Adjust the treadmill incline."
    assert cleared_table[1]['GER'] == ""
    print("✅ Single Column Clearing passed!")
    
    # 5. Test Block Deletion and Alignment Update
    print("\nTesting Block Deletion and Alignment Update:")
    reduced_blocks = [b for i, b in enumerate(eng_blocks) if i != 2] # Delete Calories
    reduced_table = align_blocks_to_table([], reduced_blocks, 'ENG')
    print(f"Reduced table: {reduced_table}")
    assert len(reduced_table) == 2
    assert reduced_table[0]['ENG'] == "TIME: Set goals for Time."
    assert reduced_table[1]['ENG'] == "INCLINE: Adjust the treadmill incline."
    print("✅ Block Deletion and Alignment Update passed!")
    
    # 6. Test Keyword Collision and Scoring Match
    print("\nTesting Keyword Collision and Scoring Match (User's Scenario):")
    collision_eng = [
        {'ENG': "TIME: Set up your workout time. User could set up the speed."}, # Row 0 (contains TIME and word 'speed')
        {'ENG': "SPEED: Set up treadmill speed."}                             # Row 1 (contains SPEED)
    ]
    collision_ger = [
        {'text': "ZEIT (TIME): Stellen Sie Ihre Trainingszeit ein."},
        {'text': "GESCHWINDIGKEIT (SPEED): Wird in KM/H angezeigt."}
    ]
    aligned_collision = align_blocks_to_table(collision_eng, collision_ger, 'GER')
    print("Aligned collision table:")
    for i, r in enumerate(aligned_collision):
        print(f"  Row {i}: {r}")
    
    assert len(aligned_collision) == 2
    # GER 'ZEIT (TIME)' must go to Row 0
    assert aligned_collision[0]['GER'] == "ZEIT (TIME): Stellen Sie Ihre Trainingszeit ein."
    # GER 'GESCHWINDIGKEIT (SPEED)' must go to Row 1 (exact parenthetical tag match has higher score than substring mention)
    assert aligned_collision[1]['GER'] == "GESCHWINDIGKEIT (SPEED): Wird in KM/H angezeigt."
    # 7. Test Bidirectional Matching (German first, English second)
    print("\nTesting Bidirectional Matching (German first, English second):")
    initial_ger = [
        {'GER': "ZEIT (TIME): Stellen Sie Ihre Trainingszeit ein."},
        {'GER': "GESCHWINDIGKEIT (SPEED): Wird in KM/H angezeigt."}
    ]
    eng_blocks = [
        {'text': "TIME: Set up your workout time. User could set up the speed."},
        {'text': "SPEED: Set up treadmill speed."}
    ]
    aligned_bidirectional = align_blocks_to_table(initial_ger, eng_blocks, 'ENG')
    print("Aligned bidirectional table:")
    for i, r in enumerate(aligned_bidirectional):
        print(f"  Row {i}: {r}")
        
    assert len(aligned_bidirectional) == 2
    # ENG 'TIME' block should align to Row 0 ('ZEIT (TIME)')
    assert aligned_bidirectional[0]['ENG'] == "TIME: Set up your workout time. User could set up the speed."
    # ENG 'SPEED' block should align to Row 1 ('GESCHWINDIGKEIT (SPEED)')
    assert aligned_bidirectional[1]['ENG'] == "SPEED: Set up treadmill speed."
    print("✅ Bidirectional Matching passed!")
    
    print("\n🎉 ALL AUTOMATED ALIGNMENT TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == '__main__':
    run_test()
