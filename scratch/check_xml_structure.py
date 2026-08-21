import zipfile
from lxml import etree

idml_path = 'uploads/patch_028b1f39879844ea9aaf442661f73598.idml'

with zipfile.ZipFile(idml_path, 'r') as zf:
    content = zf.read('Stories/Story_ucc84.xml')
    tree = etree.fromstring(content)
    
    # Let's find ParagraphStyleRange containing Br
    for psr in tree.iter():
        local = psr.tag.split('}')[-1] if '}' in str(psr.tag) else psr.tag
        if local == 'ParagraphStyleRange':
            # check if it has Br
            brs = [c for c in psr.iter() if (c.tag.split('}')[-1] if '}' in str(c.tag) else c.tag) == 'Br']
            if brs:
                print("\nFound ParagraphStyleRange with Br!")
                # Print immediate children of this ParagraphStyleRange
                for i, child in enumerate(psr):
                    clocal = child.tag.split('}')[-1] if '}' in str(child.tag) else child.tag
                    print(f"  Child {i}: <{clocal}> (Self attribute: {child.get('Self', 'none')})")
                    if clocal == 'CharacterStyleRange':
                        # Print children of this CSR
                        for j, gchild in enumerate(child):
                            glocal = gchild.tag.split('}')[-1] if '}' in str(gchild.tag) else gchild.tag
                            print(f"    G-Child {j}: <{glocal}>, text={repr(gchild.text or '')}")
                break
