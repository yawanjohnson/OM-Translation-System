import copy
from lxml import etree

# Helper to strip namespace
def _local(tag) -> str:
    if not isinstance(tag, str):
        return ''
    return tag.split('}')[-1] if '}' in tag else tag

def _split_csr_by_br(psr):
    """將 ParagraphStyleRange 中的 CharacterStyleRange 依照 Br (軟換行) 拆分為多個獨立的 CharacterStyleRange。"""
    children = list(psr)
    for child in children:
        psr.remove(child)
        
    for child in children:
        if _local(child.tag) != 'CharacterStyleRange':
            psr.append(child)
            continue
            
        # For CharacterStyleRange, we split it by Br
        current_csr = copy.deepcopy(child)
        for sub in list(current_csr):
            current_csr.remove(sub)
            
        properties_el = None
        for sub in child:
            if _local(sub.tag) == 'Properties':
                properties_el = copy.deepcopy(sub)
                break
        if properties_el is not None:
            current_csr.append(properties_el)
            
        for sub in child:
            if _local(sub.tag) == 'Properties':
                continue
            elif _local(sub.tag) == 'Br':
                if len([c for c in current_csr if _local(c.tag) != 'Properties']) > 0:
                    psr.append(current_csr)
                
                psr.append(sub)
                
                current_csr = copy.deepcopy(child)
                for c in list(current_csr):
                    current_csr.remove(c)
                if properties_el is not None:
                    current_csr.append(copy.deepcopy(properties_el))
            else:
                current_csr.append(sub)
                
        if len([c for c in current_csr if _local(c.tag) != 'Properties']) > 0:
            psr.append(current_csr)

# Create a test XML block mimicking ParagraphStyleRange
xml_data = """
<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Normal">
    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Properties>
            <FillColor type="string">Color/Black</FillColor>
        </Properties>
        <Content>Line 1 text</Content>
        <Br />
        <Content>Line 2 text</Content>
        <Br />
        <Content>Line 3 text</Content>
    </CharacterStyleRange>
</ParagraphStyleRange>
"""

tree = etree.fromstring(xml_data)
print("Before split:")
print(etree.tostring(tree, encoding='utf-8').decode('utf-8'))

_split_csr_by_br(tree)

print("\nAfter split:")
print(etree.tostring(tree, encoding='utf-8').decode('utf-8'))
