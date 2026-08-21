import os
import zipfile
from lxml import etree

uploads_dir = 'uploads'
idml_files = [f for f in os.listdir(uploads_dir) if f.endswith('.idml')]

print("=== SEARCHING IDML FILES FOR 'grease' ===")

for filename in idml_files:
    filepath = os.path.join(uploads_dir, filename)
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            for name in zf.namelist():
                if name.startswith('Stories/'):
                    xml_content = zf.read(name)
                    if b'grease' in xml_content or b'Grease' in xml_content:
                        print(f"\nFound in file: {filename}, Story file: {name}")
                        # Parse the XML to extract the exact text
                        tree = etree.fromstring(xml_content)
                        # Let's find character style ranges and contents
                        for psr in tree.iter():
                            local = psr.tag.split('}')[-1] if '}' in str(psr.tag) else psr.tag
                            if local == 'ParagraphStyleRange':
                                # Let's show character style ranges inside it
                                csrs = [c for c in psr.iter() if (c.tag.split('}')[-1] if '}' in str(c.tag) else c.tag) == 'CharacterStyleRange']
                                for csr in csrs:
                                    contents = [child.text for child in csr if (child.tag.split('}')[-1] if '}' in str(child.tag) else child.tag) == 'Content']
                                    contents_text = "".join([c for c in contents if c])
                                    if 'grease' in contents_text.lower():
                                        print(f"  CharacterStyleRange Text: {repr(contents_text)}")
    except Exception as e:
        print(f"  Error reading {filename}: {e}")
