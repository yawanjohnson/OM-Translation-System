import zipfile
import os
import re
from lxml import etree

def clean_text(text: str) -> str:
    if not text:
        return ""
    t = text.replace('\xa0', ' ').replace('\u2002', ' ').replace('\u2003', ' ').replace('\u2009', ' ')
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def search_idml_broad(idml_path):
    print(f"=== Broad Scan for: {os.path.basename(idml_path)} ===")
    try:
        with zipfile.ZipFile(idml_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('Stories/Story_'):
                    content = z.read(name)
                    tree = etree.fromstring(content)
                    for psr in tree.findall('.//ParagraphStyleRange'):
                        texts = []
                        for csr in psr.findall('.//CharacterStyleRange'):
                            for c in csr.findall('.//Content'):
                                if c.text:
                                    texts.append(c.text)
                        full_text = "".join(texts)
                        if any(k in full_text for k in ["P1)", "P2)", "P3)", "P4)", "P5)", "WORKOUT PROFILES"]):
                            print(f"  Story: {name}")
                            print(f"    Raw: {repr(full_text)}")
    except Exception as e:
        print(f"  Error: {e}")

idml_file = "uploads/patch_68cc0633a7b94347b1707369ed6d0599.idml"
if os.path.exists(idml_file):
    search_idml_broad(idml_file)
else:
    print(f"File not found: {idml_file}")
