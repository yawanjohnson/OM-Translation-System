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
    aligned_rows = list(table_rows)
    
    for block in new_blocks:
        text = block['text']
        matched_idx = -1
        
        if len(aligned_rows) > 0:
            keywords = extract_keywords(text)
            for i, row in enumerate(aligned_rows):
                eng_text = row.get('ENG', '').upper()
                # Check if any keyword matches the English row
                has_match = any(kw in eng_text for kw in keywords)
                if has_match:
                    matched_idx = i
                    break
                    
        if matched_idx != -1:
            aligned_rows[matched_idx][lang_code] = text
        else:
            new_row = {}
            new_row[lang_code] = text
            aligned_rows.append(new_row)
            
    return aligned_rows

def run_test():
    print("=== STARTING SMART EXTRACTION E2E AUTOMATED ALIGNMENT TEST ===")
    
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
    
    print("\n🎉 ALL AUTOMATED ALIGNMENT TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == '__main__':
    run_test()
