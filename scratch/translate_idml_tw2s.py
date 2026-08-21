import os
import zipfile
from lxml import etree
import opencc

# Initialize OpenCC translator (Taiwan Traditional Chinese to Simplified Chinese)
converter = opencc.OpenCC('tw2s')

def _local(tag) -> str:
    """Get the local name of an XML tag (strip namespace)."""
    if not isinstance(tag, str):
        return ''
    return tag.split('}')[-1] if '}' in tag else tag

def translate_story_xml(xml_bytes: bytes) -> tuple[bytes, int, int]:
    """
    Parses a story XML file, translates all <Content> tag values,
    and returns (modified_xml_bytes, element_count, character_count).
    """
    try:
        tree = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return xml_bytes, 0, 0
        
    modified_elements = 0
    modified_chars = 0
    
    # Iterate through all elements and translate text inside <Content> tags
    for elem in tree.iter():
        if _local(elem.tag) == 'Content':
            if elem.text:
                orig_text = elem.text
                translated_text = converter.convert(orig_text)
                if translated_text != orig_text:
                    elem.text = translated_text
                    modified_elements += 1
                    modified_chars += len(orig_text)
                    
    if modified_elements > 0:
        new_xml = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
        return new_xml, modified_elements, modified_chars
        
    return xml_bytes, 0, 0

def main():
    src_idml = 'uploads/VF20_VST600-FW82_OM_r1_1_D_web 簡體中文.idml'
    dest_dir = 'outputs'
    dest_idml = os.path.join(dest_dir, 'VF20_VST600-FW82_OM_r1_1_D_web_translated.idml')
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    print(f"Reading from: {src_idml}")
    print(f"Writing to: {dest_idml}")
    
    total_elements = 0
    total_chars = 0
    stories_processed = 0
    
    with zipfile.ZipFile(src_idml, 'r') as zin:
        with zipfile.ZipFile(dest_idml, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                
                # Check if it is a story XML file
                if item.filename.startswith('Stories/') and item.filename.endswith('.xml'):
                    translated_data, elem_cnt, char_cnt = translate_story_xml(data)
                    zout.writestr(item, translated_data)
                    if elem_cnt > 0:
                        stories_processed += 1
                        total_elements += elem_cnt
                        total_chars += char_cnt
                        print(f"  Processed {item.filename}: translated {elem_cnt} elements ({char_cnt} chars)")
                else:
                    # Copy other files unchanged
                    zout.writestr(item, data)
                    
    print("\nTranslation Completed!")
    print(f"Total Stories modified: {stories_processed}")
    print(f"Total <Content> elements translated: {total_elements}")
    print(f"Total characters converted: {total_chars}")

if __name__ == '__main__':
    main()
