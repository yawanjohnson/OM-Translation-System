import zipfile
from lxml import etree

idml_path = 'uploads/patch_028b1f39879844ea9aaf442661f73598.idml'

with zipfile.ZipFile(idml_path, 'r') as zf:
    for name in zf.namelist():
        if name.startswith('Stories/'):
            content = zf.read(name)
            if b'edal' in content or b'EDAL' in content:
                print(f"Found in {name}")
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
                        full_psr_text = "".join(psr_text)
                        if 'pedal' in full_psr_text.lower():
                            print(f"  Paragraph Text: {repr(full_psr_text)}")
