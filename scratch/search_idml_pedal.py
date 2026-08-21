import zipfile
from lxml import etree

idml_path = 'uploads/patch_028b1f39879844ea9aaf442661f73598.idml'

with zipfile.ZipFile(idml_path, 'r') as zf:
    for name in zf.namelist():
        if name.startswith('Stories/'):
            content = zf.read(name)
            if b'Insert Left Pedal' in content:
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
                        if 'Insert Left Pedal' in full_psr_text:
                            print(f"\nParagraph Text: {repr(full_psr_text)}")
                            # Show CSR elements
                            csrs = [c for c in psr if c.tag.split('}')[-1] == 'CharacterStyleRange']
                            print(f"Number of CSRs: {len(csrs)}")
                            for ci, csr in enumerate(csrs, 1):
                                contents = [c for c in csr if c.tag.split('}')[-1] == 'Content']
                                brs = [c for c in csr if c.tag.split('}')[-1] == 'Br']
                                print(f"  CSR {ci}: Contents={len(contents)}, Brs={len(brs)}")
                                for c in contents:
                                    print(f"    Content text: {repr(c.text)}")
