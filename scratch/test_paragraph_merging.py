def merge_lines(raw_lines):
    paragraphs = []
    current = ""
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        if not current:
            current = line
        else:
            ends_with_punctuation = current[-1] in ('.', '?', '!', ':', ';')
            starts_with_capital = line[0].isupper() if line else False
            
            should_merge = not ends_with_punctuation
            if starts_with_capital:
                if len(line) > 1 and line[1].islower():
                    should_merge = False
                    
            if should_merge:
                if current.endswith('-'):
                    current = current[:-1] + line
                else:
                    current += " " + line
            else:
                paragraphs.append(current)
                current = line
    if current:
        paragraphs.append(current)
    return paragraphs

def run_test():
    print("=== TESTING PARAGRAPH MERGING ALGORITHM ===")
    
    # Test case 1: Wrapped sentence (starts with lowercase)
    test_lines_1 = [
        "TIME: Set goals for Time. User",
        "could set up the speed and Incline to start."
    ]
    res_1 = merge_lines(test_lines_1)
    print("Test 1 Result:", res_1)
    assert len(res_1) == 1
    assert res_1[0] == "TIME: Set goals for Time. User could set up the speed and Incline to start."
    print("✅ Test 1 Passed: Merged lowercase start wrapped line.")
    
    # Test case 2: Separate sentences (ends with punctuation)
    test_lines_2 = [
        "First sentence ended.",
        "Second sentence started."
    ]
    res_2 = merge_lines(test_lines_2)
    print("Test 2 Result:", res_2)
    assert len(res_2) == 2
    assert res_2[0] == "First sentence ended."
    assert res_2[1] == "Second sentence started."
    print("✅ Test 2 Passed: Did not merge punctuated sentence boundaries.")
    
    # Test case 3: Hyphenated word break
    test_lines_3 = [
        "The machine is fully compa-",
        "tible with heart rate sensors."
    ]
    res_3 = merge_lines(test_lines_3)
    print("Test 3 Result:", res_3)
    assert len(res_3) == 1
    assert res_3[0] == "The machine is fully compatible with heart rate sensors."
    print("✅ Test 3 Passed: Re-aligned hyphenated word breaks.")
    
    print("\n🎉 ALL PARAGRAPH MERGING TESTS PASSED! 🎉")

if __name__ == '__main__':
    run_test()
