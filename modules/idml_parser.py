"""
idml_parser.py - 從 IDML 檔案萃取文字內容
IDML 本質上是 ZIP 壓縮的 XML 集合，文字儲存在 Stories/*.xml
"""
import zipfile
from lxml import etree


def _local(tag) -> str:
    """取得 XML 標籤的本地名稱（去除命名空間）。"""
    if not isinstance(tag, str):
        return ''
    return tag.split('}')[-1] if '}' in tag else tag


def extract_stories(idml_path: str) -> list[dict]:
    stories = []
    try:
        with zipfile.ZipFile(idml_path, 'r') as zf:
            story_names = sorted([n for n in zf.namelist() if n.startswith('Stories/')])
            for story_name in story_names:
                raw = zf.read(story_name)
                story_data = _parse_story_xml(raw, story_name)
                if story_data and story_data['paragraphs']:
                    stories.append(story_data)
    except Exception as e:
        raise RuntimeError(f'無法讀取 IDML：{e}')
    return stories


def _parse_story_xml(xml_bytes: bytes, story_name: str) -> dict:
    try:
        tree = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return None
    story_elem = None
    for elem in tree.iter():
        if _local(elem.tag) == 'Story':
            story_elem = elem
            break
    if story_elem is None:
        return None
    story_id = story_elem.get('Self', story_name)
    paragraphs = []
    for psr in story_elem.iter():
        if _local(psr.tag) != 'ParagraphStyleRange':
            continue
        para_text = _get_paragraph_text(psr)
        if para_text.strip():
            style = psr.get('AppliedParagraphStyle', '')
            if '/' in style:
                style = style.split('/')[-1]
            paragraphs.append({'text': para_text, 'style': style})
    return {'story_id': story_id, 'story_file': story_name, 'paragraphs': paragraphs}


def _get_paragraph_text(psr_elem) -> str:
    parts = []
    for elem in psr_elem.iter():
        local = _local(elem.tag)
        if local == 'Content' and elem.text:
            parts.append(elem.text)
        elif local == 'Br':
            parts.append('\n')
    return ''.join(parts)


def extract_flat_texts(idml_path: str) -> list[str]:
    texts = []
    stories = extract_stories(idml_path)
    for story in stories:
        for para in story['paragraphs']:
            text = para['text'].strip()
            if text:
                texts.append(text)
    return texts


def get_idml_info(idml_path: str) -> dict:
    try:
        with zipfile.ZipFile(idml_path, 'r') as zf:
            all_names = zf.namelist()
            story_count = len([n for n in all_names if n.startswith('Stories/')])
            spread_count = len([n for n in all_names if n.startswith('Spreads/')])
            dom_version = 'unknown'
            if 'designmap.xml' in all_names:
                dm_xml = zf.read('designmap.xml')
                dm_tree = etree.fromstring(dm_xml)
                dom_version = dm_tree.get('DOMVersion', 'unknown')
        return {'story_count': story_count, 'spread_count': spread_count,
                'dom_version': dom_version, 'files': len(all_names)}
    except Exception as e:
        return {'error': str(e)}


def _extract_story_style(story_elem) -> dict:
    """從 Story XML 元素中萃取代表性字型樣式。"""
    style = {'font_size': 9.0, 'font_family': '', 'justification': 'LeftAlign', 'leading': 0}
    for psr in story_elem.iter():
        if _local(psr.tag) != 'ParagraphStyleRange':
            continue
        just = psr.get('Justification')
        if just:
            style['justification'] = just
        for csr in psr:
            if _local(csr.tag) != 'CharacterStyleRange':
                continue
            ps = csr.get('PointSize')
            if ps:
                try:
                    style['font_size'] = float(ps)
                except ValueError:
                    pass
            af = csr.get('AppliedFont')
            if af:
                style['font_family'] = af.split('\t')[0].strip()
            lead = csr.get('Leading')
            if lead and lead != 'Auto':
                try:
                    style['leading'] = float(lead)
                except ValueError:
                    pass
            if style['font_size'] != 9.0 or style['font_family']:
                break
        if style['font_size'] != 9.0 or style['font_family']:
            break
    if style['leading'] <= 0:
        style['leading'] = round(style['font_size'] * 1.2, 2)
    return style


def extract_layout(idml_path: str) -> dict:
    """
    萃取 IDML 的版面編排資訊（Spread, Page, TextFrame, ImageFrame）與 Story 文字及字型樣式。

    座標換算：
      - Page.GeometricBounds  = 頁面本地邊界 [top, left, bottom, right]
      - Page.ItemTransform tx,ty = 頁面原點在 Spread 座標中的位置
      - TextFrame/Rectangle 角點由 PathPointType.Anchor + ItemTransform 計算（Spread 座標）
      - 最終透過 _spread_to_page 轉換為頁面本地座標
    """
    layout = {
        'spreads': [],
        'stories': {},
        'story_styles': {},
    }

    def _parse_tr(s):
        try:
            return [float(x) for x in s.split()]
        except Exception:
            return [1, 0, 0, 1, 0, 0]

    def _tr_pt(x, y, tr):
        a, b, c, d, e, f = tr
        return a * x + c * y + e, b * x + d * y + f

    def _get_path_bounds(el, tr):
        """由 PathPointType Anchor + 仿射矩陣計算 Spread 座標邊界 [top,left,bottom,right]"""
        xs, ys = [], []
        for ppt in el.iter():
            if _local(ppt.tag) == 'PathPointType':
                anchor = ppt.get('Anchor')
                if anchor:
                    try:
                        cx, cy = [float(v) for v in anchor.split()]
                        sx, sy = _tr_pt(cx, cy, tr)
                        xs.append(sx)
                        ys.append(sy)
                    except Exception:
                        pass
        if xs and ys:
            return [min(ys), min(xs), max(ys), max(xs)]
        return None

    def _spread_to_page(bs, page):
        """將 Spread 座標邊界轉換為頁面本地座標"""
        ox = page.get('spread_ox', 0)
        oy = page.get('spread_oy', 0)
        pt, pl = page['bounds'][0], page['bounds'][1]
        return [bs[0] - oy - pt, bs[1] - ox - pl, bs[2] - oy - pt, bs[3] - ox - pl]

    def _find_best_page(bs, pages):
        """找到 bounds 中心點最接近的頁面"""
        cy = (bs[0] + bs[2]) / 2.0
        cx = (bs[1] + bs[3]) / 2.0
        best = pages[0]
        for pg in pages:
            ox, oy = pg.get('spread_ox', 0), pg.get('spread_oy', 0)
            gb = pg['bounds']
            if (ox + gb[1] - 10 <= cx <= ox + gb[3] + 10 and
                    oy + gb[0] - 10 <= cy <= oy + gb[2] + 10):
                best = pg
                break
        return best

    try:
        with zipfile.ZipFile(idml_path, 'r') as zf:
            # 1. Stories
            story_names = [n for n in zf.namelist() if n.startswith('Stories/')]
            for sname in story_names:
                story_id = sname.replace('Stories/', '').replace('.xml', '')
                raw = zf.read(sname)
                try:
                    tree = etree.fromstring(raw)
                    story_elem = None
                    for elem in tree.iter():
                        if _local(elem.tag) == 'Story':
                            story_elem = elem
                            break
                    if story_elem is not None:
                        paras = []
                        for psr in story_elem.iter():
                            if _local(psr.tag) == 'ParagraphStyleRange':
                                txt = _get_paragraph_text(psr)
                                if txt.strip():
                                    paras.append(txt)
                        layout['stories'][story_id] = '\n'.join(paras)
                        layout['story_styles'][story_id] = _extract_story_style(story_elem)
                except Exception:
                    pass

            # 2. Spreads
            spread_names = sorted([n for n in zf.namelist() if n.startswith('Spreads/')])
            page_num_counter = 1
            for spname in spread_names:
                raw = zf.read(spname)
                try:
                    tree = etree.fromstring(raw)
                    spread_id = spname.replace('Spreads/', '').replace('.xml', '')

                    pages = []
                    frames = []
                    image_frames = []

                    # 收集 Pages
                    for el in tree.iter():
                        if _local(el.tag) != 'Page':
                            continue
                        gb_str = el.get('GeometricBounds', '')
                        it_str = el.get('ItemTransform', '1 0 0 1 0 0')
                        if not gb_str:
                            continue
                        try:
                            gb = [float(x) for x in gb_str.split()]
                            it = _parse_tr(it_str)
                            pages.append({
                                'id':        el.get('Self', ''),
                                'bounds':    gb,
                                'width':     gb[3] - gb[1],
                                'height':    gb[2] - gb[0],
                                'page_num':  page_num_counter,
                                'spread_ox': it[4],
                                'spread_oy': it[5],
                            })
                            page_num_counter += 1
                        except Exception:
                            pass

                    if not pages:
                        continue

                    # TextFrame
                    for el in tree.iter():
                        if _local(el.tag) != 'TextFrame':
                            continue
                        parent_story = el.get('ParentStory')
                        if not parent_story:
                            continue
                        tr = _parse_tr(el.get('ItemTransform', '1 0 0 1 0 0'))
                        bs = _get_path_bounds(el, tr)
                        if bs is None:
                            continue
                        pg = _find_best_page(bs, pages)
                        bp = _spread_to_page(bs, pg)
                        w, h = bp[3] - bp[1], bp[2] - bp[0]
                        if abs(w) < 1 and abs(h) < 1:
                            continue
                        frames.append({
                            'id':       el.get('Self', ''),
                            'story_id': parent_story,
                            'bounds':   bp,
                            'width':    abs(w),
                            'height':   abs(h),
                            'page_id':  pg['id'],
                        })

                    # 圖片框
                    for el in tree.iter():
                        if _local(el.tag) not in ('Rectangle', 'GraphicFrame', 'Oval', 'Polygon'):
                            continue
                        tr = _parse_tr(el.get('ItemTransform', '1 0 0 1 0 0'))
                        bs = _get_path_bounds(el, tr)
                        if bs is None:
                            continue
                        pg = _find_best_page(bs, pages)
                        bp = _spread_to_page(bs, pg)
                        w, h = bp[3] - bp[1], bp[2] - bp[0]
                        if abs(w) < 1 and abs(h) < 1:
                            continue
                        has_image = any(
                            _local(child.tag) in ('Image', 'EPS', 'PDF', 'WMF', 'PICT', 'ImportedPage')
                            for child in el
                        )
                        image_frames.append({
                            'id':        el.get('Self', ''),
                            'type':      _local(el.tag),
                            'has_image': has_image,
                            'bounds':    bp,
                            'width':     abs(w),
                            'height':    abs(h),
                            'page_id':   pg['id'],
                        })

                    layout['spreads'].append({
                        'id':           spread_id,
                        'pages':        pages,
                        'text_frames':  frames,
                        'image_frames': image_frames,
                    })
                except Exception:
                    pass
    except Exception:
        pass

    return layout
