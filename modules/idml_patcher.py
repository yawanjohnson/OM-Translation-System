"""
idml_patcher.py - IDML 自動修正核心模組

功能：
  1. 在 IDML 的 Stories 中找到指定文字並替換
  2. 替換後套用紅色字元樣式（OM_RedMark），在 InDesign 中顯示為紅字
  3. 產生 Excel 比對報告（成功清單 + 未找到清單）

紅色標記原理：
  - 在 Resources/Graphic.xml 新增 CMYK 紅色（0,100,100,0）
  - 在 Resources/Styles.xml 新增字元樣式 "OM RedMark" 套用紅色
  - 修改的 CharacterStyleRange 改用此樣式

字串分割邏輯（Level 1）：
  若搜尋文字完整存在於單一 Content 元素中，則精確分割該
  CharacterStyleRange 為三段（前/替換/後），只有替換部分套紅色。

字串分割邏輯（Level 2）：
  若搜尋文字完整存在於一個 ParagraphStyleRange 的合併文字中，
  但跨越多個 CharacterStyleRange，則整段落重建（保留段落樣式，
  字元樣式簡化）。
"""

import zipfile
import copy
import os
from io import BytesIO
from lxml import etree
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ------------------------------------------------------------------ #
# 常數
# ------------------------------------------------------------------ #
RED_COLOR_SELF  = 'Color/OM_Red'
RED_COLOR_NAME  = 'OM_Red'
RED_STYLE_SELF  = 'CharacterStyle/OM_RedMark'
RED_STYLE_NAME  = 'OM RedMark'
NO_CHAR_STYLE   = 'CharacterStyle/$ID/[No character style]'

LANG_CODES = [
    'ENG','GER','DUT','DAN','FRE','SPA','ITA','GRK',
    'POL','PRB','RUS','CHT','JPN','KOR','VTM','THI','ARB','TRK','CHS'
]


def _local(tag) -> str:
    if not isinstance(tag, str):
        return ''
    return tag.split('}')[-1] if '}' in tag else tag


# ------------------------------------------------------------------ #
# 主入口
# ------------------------------------------------------------------ #

def patch_idml(
    idml_path: str,
    instructions: list,
    output_idml_path: str,
    output_excel_path: str,
) -> dict:
    """
    修正 IDML 並產生報告。

    Args:
        idml_path:        來源 IDML 路徑
        instructions:     [{'lang_code','find','replace','note'}, ...]
        output_idml_path: 輸出標記版 IDML 路徑
        output_excel_path:輸出 Excel 報告路徑

    Returns:
        {'changes': [...], 'not_found': [...]}
    """
    # 讀取所有 IDML 內容
    with zipfile.ZipFile(idml_path, 'r') as zf:
        file_map = {name: zf.read(name) for name in zf.namelist()}
        zip_infos = zf.infolist()

    # 注入紅色樣式資源
    file_map = _inject_red_style(file_map)

    # 逐條執行修改指示
    all_changes = []
    not_found   = []
    story_names = sorted(n for n in file_map if n.startswith('Stories/'))

    for instr in instructions:
        find_text    = (instr.get('find') or '').strip()
        replace_text = (instr.get('replace') or '').strip()
        lang_code    = instr.get('lang_code', '')
        note         = instr.get('note', '')
        mark_red     = instr.get('mark_red', True)

        if not find_text:
            continue

        instr_changes = []

        for sname in story_names:
            new_xml, story_changes = _process_story(
                file_map[sname], find_text, replace_text, mark_red
            )
            if story_changes:
                file_map[sname] = new_xml
                for sc in story_changes:
                    instr_changes.append({
                        'lang_code': lang_code,
                        'story':     sname,
                        'find':      find_text,
                        'replace':   replace_text,
                        'note':      note,
                        'count':     sc.get('count', 1),
                        'mark_red':  mark_red,
                    })

        if instr_changes:
            all_changes.extend(instr_changes)
        else:
            not_found.append({
                'lang_code': lang_code,
                'find':      find_text,
                'replace':   replace_text,
                'note':      note,
            })

    # 寫出標記版 IDML
    _write_idml(file_map, zip_infos, output_idml_path)

    # 寫出 Excel 報告
    _write_excel_report(all_changes, not_found, output_excel_path)

    return {'changes': all_changes, 'not_found': not_found}


# ------------------------------------------------------------------ #
# 注入紅色樣式
# ------------------------------------------------------------------ #

def _inject_red_style(file_map: dict) -> dict:
    """在 Graphic.xml 及 Styles.xml 中注入紅色資源（冪等）。"""

    # --- Graphic.xml：新增紅色色彩 ---
    if 'Resources/Graphic.xml' in file_map:
        tree = etree.fromstring(file_map['Resources/Graphic.xml'])
        if tree.find(f'.//*[@Self="{RED_COLOR_SELF}"]') is None:
            color = etree.SubElement(tree, 'Color')
            color.set('Self',                  RED_COLOR_SELF)
            color.set('Name',                  RED_COLOR_NAME)
            color.set('Space',                 'CMYK')
            color.set('ColorModel',            'Process')
            color.set('ColorValue',            '0 100 100 0')
            color.set('ColorOverride',         'Speciality')
            color.set('AlternateSpace',        'NoAlternateColorSpace')
            color.set('AlternateColorValue',   '')
            color.set('Visible',               'true')
            color.set('ColorEditable',         'true')
        file_map['Resources/Graphic.xml'] = _to_bytes(tree)

    # --- Styles.xml：新增字元樣式 ---
    if 'Resources/Styles.xml' in file_map:
        tree = etree.fromstring(file_map['Resources/Styles.xml'])
        csg = (
            tree.find('.//{http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging}RootCharacterStyleGroup')
            or tree.find('.//RootCharacterStyleGroup')
        )
        if csg is not None and csg.find(f'.//*[@Self="{RED_STYLE_SELF}"]') is None:
            cs = etree.SubElement(csg, 'CharacterStyle')
            cs.set('Self',       RED_STYLE_SELF)
            cs.set('Name',       RED_STYLE_NAME)
            cs.set('Imported',   'false')
            cs.set('FillColor',  RED_COLOR_SELF)
            cs.set('FillTint',   '100')
            props = etree.SubElement(cs, 'Properties')
            bo = etree.SubElement(props, 'BasedOn')
            bo.set('type', 'string')
            bo.text = '$ID/[No character style]'
        file_map['Resources/Styles.xml'] = _to_bytes(tree)

    return file_map


# ------------------------------------------------------------------ #
# 處理 Story
# ------------------------------------------------------------------ #

def _process_story(xml_bytes: bytes, find: str, replace: str, mark_red: bool = True):
    """
    在 Story XML 中搜尋並替換文字。
    回傳 (new_xml_bytes, [change_info, ...])
    """
    try:
        tree = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return xml_bytes, []

    changes = []

    # 找到 Story 根元素
    story_elem = None
    for el in tree.iter():
        if _local(el.tag) == 'Story':
            story_elem = el
            break
    if story_elem is None:
        return xml_bytes, []

    # 逐段落處理
    for psr in list(story_elem.iter()):
        if _local(psr.tag) != 'ParagraphStyleRange':
            continue
        c = _replace_in_paragraph(psr, find, replace, mark_red)
        if c:
            changes.append({'count': c})

    if not changes:
        return xml_bytes, []

    return _to_bytes(tree), changes


def _apply_red_color_override(csr):
    """在 CharacterStyleRange 中注入 FillColor=OM_Red 的本地樣式覆蓋，以保留原字型不跑版/變亂碼。"""
    properties_el = None
    for child in csr:
        if _local(child.tag) == 'Properties':
            properties_el = child
            break
    if properties_el is None:
        properties_el = etree.SubElement(csr, 'Properties')

    fill_color_el = None
    for child in properties_el:
        if _local(child.tag) == 'FillColor':
            fill_color_el = child
            break
    if fill_color_el is None:
        fill_color_el = etree.SubElement(properties_el, 'FillColor')
        fill_color_el.set('type', 'string')
    fill_color_el.text = RED_COLOR_SELF


def _replace_in_paragraph(psr, find: str, replace: str, mark_red: bool = True) -> int:
    """
    在一個 ParagraphStyleRange 中執行非破壞性的搜尋與替換。
    100% 保留所有原本字元樣式（CharacterStyleRange）與各國語言字型設定，絕不跑版或產生亂碼（豆腐框）。
    """
    # 1. 建立字元對應表，將整個段落的字元與對應的 CSR/Content 節點綁定
    char_map = []
    csrs = [c for c in psr if _local(c.tag) == 'CharacterStyleRange']
    for csr in csrs:
        contents = [child for child in csr if _local(child.tag) == 'Content']
        if not contents:
            continue
        content = contents[0]
        text = content.text or ''
        for i, char in enumerate(text):
            char_map.append({
                'char': char,
                'csr': csr,
                'content': content,
                'index': i
            })

    full_text = "".join([item['char'] for item in char_map])
    
    if find not in full_text:
        return 0

    # 2. 尋找所有非重疊的匹配位置
    match_indices = []
    start = 0
    while True:
        idx = full_text.find(find, start)
        if idx == -1:
            break
        match_indices.append(idx)
        start = idx + len(find)

    if not match_indices:
        return 0

    # 3. 準備儲存每個 Content 的字元列表，以便進行非破壞性修改
    # content_chars 格式: {content_node: {char_index: char_string}}
    content_chars = {}
    for item in char_map:
        content = item['content']
        if content not in content_chars:
            content_chars[content] = {}
        content_chars[content][item['index']] = item['char']

    # 4. 對每個匹配的字元區間進行替換
    red_csrs = set()
    for idx in match_indices:
        # 該匹配範圍的所有字元
        match_items = char_map[idx : idx + len(find)]
        
        # 第一個字元
        first_item = match_items[0]
        first_content = first_item['content']
        first_idx = first_item['index']
        
        # 將第一個字元替換成完整的 replace 文字，並標記該 CSR 需要變紅字
        content_chars[first_content][first_idx] = replace
        red_csrs.add(first_item['csr'])
        
        # 匹配範圍內的其他所有字元，在各自的 Content 中設為空字串（刪除）
        for item in match_items[1:]:
            content_chars[item['content']][item['index']] = ""

    # 5. 將修改後的文字寫回 XML Content 節點，保留其他未被替換之 CSR 及其原有字型樣式
    for content, char_dict in content_chars.items():
        # 依照原始索引排序並組合成新字串
        sorted_indices = sorted(char_dict.keys())
        new_text = "".join([char_dict[i] for i in sorted_indices])
        content.text = new_text

    # 6. 套用紅色色彩覆蓋至有修改的 CSR 節點（僅變顏色，不變字型）
    if mark_red:
        for csr in red_csrs:
            _apply_red_color_override(csr)

    return len(match_indices)


def _para_full_text(psr) -> str:
    """萃取段落全文。"""
    parts = []
    for el in psr.iter():
        local = _local(el.tag)
        if local == 'Content' and el.text:
            parts.append(el.text)
        elif local == 'Br':
            parts.append('\n')
    return ''.join(parts)


# ------------------------------------------------------------------ #
# 寫出 IDML
# ------------------------------------------------------------------ #

def _write_idml(file_map: dict, zip_infos, output_path: str):
    """將修改後的 IDML 寫出為 ZIP（保留 mimetype 不壓縮）。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with zipfile.ZipFile(output_path, 'w') as zout:
        for info in zip_infos:
            content = file_map.get(info.filename)
            if content is None:
                continue
            compress = zipfile.ZIP_STORED if info.filename == 'mimetype' else zipfile.ZIP_DEFLATED
            zout.writestr(info.filename, content, compress)


# ------------------------------------------------------------------ #
# Excel 報告
# ------------------------------------------------------------------ #

def _write_excel_report(changes: list, not_found: list, output_path: str):
    """產生修改比對報告 Excel（兩個分頁）。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb = openpyxl.Workbook()

    # ── 分頁 1：修改成功 ─────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = '✅ 修改成功'
    ws1.sheet_view.showGridLines = False

    HDR_FILL  = PatternFill('solid', fgColor='1B2A4A')
    HDR_FONT  = Font(bold=True, color='FFFFFF', name='Arial', size=10)
    ORIG_FONT = Font(color='CC2200', name='Arial', size=10, strike=True)
    NEW_FONT  = Font(color='006622', name='Arial', size=10, bold=True)
    NORM_FONT = Font(name='Arial', size=10)
    ALT_FILL  = PatternFill('solid', fgColor='F4F6FB')
    CENTER    = Alignment(horizontal='center', vertical='center', wrap_text=True)
    LEFT      = Alignment(horizontal='left',   vertical='center', wrap_text=True)

    headers = ['#', '語言', '原文（修改前）', '修改後文字', '備註', 'Story 位置']
    col_widths = [5, 8, 48, 48, 20, 35]

    ws1.row_dimensions[1].height = 22
    ws1.append(headers)
    for ci, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws1.cell(1, ci)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = CENTER
        ws1.column_dimensions[get_column_letter(ci)].width = w

    for i, ch in enumerate(changes, 1):
        row_idx = i + 1
        ws1.append([
            i,
            ch.get('lang_code', ''),
            ch.get('find', ''),
            ch.get('replace', ''),
            ch.get('note', ''),
            ch.get('story', '').replace('Stories/', ''),
        ])
        ws1.row_dimensions[row_idx].height = 36
        if i % 2 == 0:
            for ci in range(1, 7):
                ws1.cell(row_idx, ci).fill = ALT_FILL
        ws1.cell(row_idx, 1).alignment = CENTER
        ws1.cell(row_idx, 1).font = NORM_FONT
        ws1.cell(row_idx, 2).alignment = CENTER
        ws1.cell(row_idx, 2).font = NORM_FONT
        if ch.get('find') == ch.get('replace'):
            # 翻譯缺失（標記紅字）
            ws1.cell(row_idx, 3).font = NORM_FONT  # 原文不加刪除線，正常顯示
            ws1.cell(row_idx, 4).font = Font(color='CC2200', name='Arial', size=10, bold=True)  # 修改後（紅字粗體）
        else:
            ws1.cell(row_idx, 3).font = ORIG_FONT      # 原文：紅色刪除線
            ws1.cell(row_idx, 4).font = NEW_FONT        # 修改後：綠色粗體
        ws1.cell(row_idx, 3).alignment = LEFT
        ws1.cell(row_idx, 4).alignment = LEFT
        ws1.cell(row_idx, 5).font = NORM_FONT
        ws1.cell(row_idx, 5).alignment = LEFT
        ws1.cell(row_idx, 6).font = NORM_FONT
        ws1.cell(row_idx, 6).alignment = LEFT

    # 凍結首列
    ws1.freeze_panes = 'A2'

    # 摘要列
    ws1.append([])
    ws1.append(['', f'共修改 {len(changes)} 處'])
    ws1.cell(ws1.max_row, 2).font = Font(bold=True, name='Arial', size=10)

    # ── 分頁 2：未找到 ───────────────────────────────────────────────
    ws2 = wb.create_sheet('❌ 未找到')
    ws2.sheet_view.showGridLines = False

    ERR_FILL = PatternFill('solid', fgColor='7B1A1A')
    ERR_FONT = Font(bold=True, color='FFFFFF', name='Arial', size=10)
    RED_FONT = Font(color='CC2200', name='Arial', size=10)
    col_widths2 = [5, 8, 48, 48, 20]
    headers2 = ['#', '語言', '搜尋原文（未找到）', '預計修改為', '備註']

    ws2.row_dimensions[1].height = 22
    ws2.append(headers2)
    for ci, (h, w) in enumerate(zip(headers2, col_widths2), 1):
        cell = ws2.cell(1, ci)
        cell.fill = ERR_FILL
        cell.font = ERR_FONT
        cell.alignment = CENTER
        ws2.column_dimensions[get_column_letter(ci)].width = w

    for i, nf in enumerate(not_found, 1):
        row_idx = i + 1
        ws2.append([
            i,
            nf.get('lang_code', ''),
            nf.get('find', ''),
            nf.get('replace', ''),
            nf.get('note', ''),
        ])
        ws2.row_dimensions[row_idx].height = 32
        for ci in range(1, 6):
            ws2.cell(row_idx, ci).font = RED_FONT
            ws2.cell(row_idx, ci).alignment = LEFT
        ws2.cell(row_idx, 1).alignment = CENTER

    ws2.freeze_panes = 'A2'
    if not not_found:
        ws2.append(['', '🎉 所有指示均成功套用！'])

    wb.save(output_path)


# ------------------------------------------------------------------ #
# 工具函式
# ------------------------------------------------------------------ #

def _to_bytes(tree) -> bytes:
    return etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
