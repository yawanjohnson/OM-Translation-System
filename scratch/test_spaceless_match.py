import os
import sys
from lxml import etree

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.idml_patcher import _replace_in_paragraph, _para_full_text

def run_test():
    print("=== TESTING SPACELESS / CASE-INSENSITIVE SUBSTRING MATCH ===")
    
    xml_str = """
    <ParagraphStyleRange xmlns="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
      <CharacterStyleRange>
        <Content>P3)&#x9;Time: Set goals for Time.</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
    """
    
    namespaces = {"ns": "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"}
    psr = etree.fromstring(xml_str)
    
    initial_text = _para_full_text(psr)
    print(f"Initial raw text: {repr(initial_text)}")
    assert "P3)\tTime: Set goals for Time." in initial_text
    
    find_text = "P3) TIME: Set goals for Time."
    replace_text = "P3) 時間：設定時間目標。"
    
    matches = _replace_in_paragraph(
        psr,
        find=find_text,
        replace=replace_text,
        mark_red=True,
        mark_green=False,
        exact_match=False,
        lang_code="CHT"
    )
    
    print(f"Matches replaced: {matches}")
    assert matches == 1, "Should have successfully matched 1 paragraph!"
    
    replaced_text = _para_full_text(psr)
    print(f"Replaced text: {repr(replaced_text)}")
    assert "時間" in replaced_text, "Replacement failed, CHT text not found!"
    
    # Check if RED style override is added
    csr = psr.find(".//ns:CharacterStyleRange", namespaces)
    assert csr is not None
    
    print("All children of CharacterStyleRange:")
    for child in csr:
        print(f"  Tag: {repr(child.tag)}")
        
    properties_el = csr.find("ns:Properties", namespaces)
    if properties_el is None:
        # Fallback to search without namespace in case tag has no namespace URI
        properties_el = csr.find("Properties")
        print(f"Namespace search failed, fallback search for 'Properties' result: {properties_el}")
        
    assert properties_el is not None
    
    fill_color_el = properties_el.find("ns:FillColor", namespaces)
    if fill_color_el is None:
        fill_color_el = properties_el.find("FillColor")
        print(f"Namespace search failed, fallback search for 'FillColor' result: {fill_color_el}")
        
    assert fill_color_el is not None
    
    fill_color = fill_color_el.text
    print(f"Applied FillColor text: {fill_color}")
    assert fill_color == "Color/OM_Red", "Red marker color was not applied!"
    
    print("\n🎉 SPACELESS SUBSTRING MATCH TEST PASSED! 🎉")

if __name__ == '__main__':
    run_test()
