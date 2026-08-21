import sys
import os
from lxml import etree

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.idml_patcher import _replace_in_paragraph, _para_full_text

# ==========================================
# TEST CASE 1: exact_match = True
# ==========================================
print("=== RUNNING TEST CASE 1 (exact_match=True) ===")
xml_string1 = """
<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
  <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/Bold">
    <Content>CALORIES: </Content>
  </CharacterStyleRange>
  <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/Regular">
    <Content>Total calories burned or calories remaining left to burn during your workout.</Content>
  </CharacterStyleRange>
</ParagraphStyleRange>
"""

psr1 = etree.fromstring(xml_string1)
find_text1 = "CALORIES: Total calories burned or calories remaining left to burn during your workout"
replace_text1 = "KALORIEN: Gesamtkalorien verbrannt oder verbleibende Kalorien während des Trainings"

changed1 = _replace_in_paragraph(psr1, find_text1, replace_text1, exact_match=True)
print(f"Changed: {changed1}")

title_content1 = psr1.findall('CharacterStyleRange')[0].find('Content')
body_content1 = psr1.findall('CharacterStyleRange')[1].find('Content')

print(f"Title content: {repr(title_content1.text)}")
print(f"Body content: {repr(body_content1.text)}")

assert title_content1.text == "KALORIEN:", f"Expected 'KALORIEN:', got {repr(title_content1.text)}"
assert body_content1.text == " Gesamtkalorien verbrannt oder verbleibende Kalorien während des Trainings.", f"Expected body text, got {repr(body_content1.text)}"


# ==========================================
# TEST CASE 2: exact_match = False (substring replace)
# ==========================================
print("\n=== RUNNING TEST CASE 2 (exact_match=False) ===")
xml_string2 = """
<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
  <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/Bold">
    <Content>CALORIES: </Content>
  </CharacterStyleRange>
  <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/Regular">
    <Content>Total calories burned or calories remaining left to burn during your workout.</Content>
  </CharacterStyleRange>
</ParagraphStyleRange>
"""

psr2 = etree.fromstring(xml_string2)
# Here, we pass the same text but running under exact_match=False
find_text2 = "CALORIES: Total calories burned or calories remaining left to burn during your workout."
replace_text2 = "KALORIEN: Gesamtkalorien verbrannt oder verbleibende Kalorien während des Trainings."

changed2 = _replace_in_paragraph(psr2, find_text2, replace_text2, exact_match=False)
print(f"Changed: {changed2}")

title_content2 = psr2.findall('CharacterStyleRange')[0].find('Content')
body_content2 = psr2.findall('CharacterStyleRange')[1].find('Content')

print(f"Title content: {repr(title_content2.text)}")
print(f"Body content: {repr(body_content2.text)}")

# Let's assert both parts are split correctly
assert title_content2.text == "KALORIEN:", f"Expected 'KALORIEN:', got {repr(title_content2.text)}"
# Note: in substring replacement, there is no new_suffix logic, so the period is part of replace_body
assert body_content2.text == " Gesamtkalorien verbrannt oder verbleibende Kalorien während des Trainings.", f"Expected body text, got {repr(body_content2.text)}"

print("\nSUCCESS! Both exact_match and non-exact_match style preservation split tests passed!")
