import zipfile
from lxml import etree

idml_path = 'uploads/patch_028b1f39879844ea9aaf442661f73598.idml'

with zipfile.ZipFile(idml_path, 'r') as zf:
    content = zf.read('Stories/Story_ua3f1.xml')
    tree = etree.fromstring(content)
    
    for psr in tree.iter():
        local = psr.tag.split('}')[-1] if '}' in str(psr.tag) else psr.tag
        if local == 'ParagraphStyleRange':
            psr_text = []
            for child in psr.iter():
                lchild = child.tag.split('}')[-1] if '}' in str(child.tag) else child.tag
                if lchild == 'Content' and child.text:
                    psr_text.append(child.text)
                elif lchild == 'Br':
                    psr_text.append('\n')
            full_text = "".join(psr_text)
            
            if 'MOVING' in full_text:
                print("=== FOUND PARAGRAPH ===")
                print(f"Full Text: {repr(full_text)}")
                print("\nImmediate Children of ParagraphStyleRange:")
                for i, child in enumerate(psr):
                    clocal = child.tag.split('}')[-1] if '}' in str(child.tag) else child.tag
                    style = child.get('AppliedCharacterStyle', 'None')
                    print(f"  Child {i}: <{clocal}> AppliedCharacterStyle={repr(style)}")
                    if clocal == 'CharacterStyleRange':
                        # Print properties
                        props = [c for c in child if c.tag.split('}')[-1] == 'Properties']
                        if props:
                            print("    Properties XML:")
                            for p in props[0]:
                                plocal = p.tag.split('}')[-1]
                                print(f"      <{plocal}> text={repr(p.text or '')} attributes={dict(p.attrib)}")
                        # Print contents
                        for gchild in child:
                            glocal = gchild.tag.split('}')[-1]
                            if glocal == 'Content':
                                print(f"    Content: {repr(gchild.text)}")
                            elif glocal == 'Br':
                                print(f"    Br")
conn = None
