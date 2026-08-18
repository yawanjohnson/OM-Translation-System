"""
idml_importer.py - 從 IDML 批次萃取文字，匯入多語言資料庫

使用方式：
    upload IDML 並指定語言代碼，
    系統萃取所有段落文字，存入指定語言欄位。
"""
from modules.idml_parser import extract_stories


def extract_for_import(idml_path: str, lang_code: str) -> list[dict]:
    """
    從 IDML 萃取段落，轉換為可匯入資料庫的格式。

    Args:
        idml_path: IDML 檔案路徑
        lang_code: 語言代碼（如 'CHT', 'ENG'）

    Returns:
        list of {lang_code: text, 'product': '', 'chapter': style_name}
    """
    stories = extract_stories(idml_path)
    rows = []
    for story in stories:
        for para in story['paragraphs']:
            text = para['text'].strip()
            if not text:
                continue
            rows.append({
                lang_code: text,
                'product': '',
                'chapter': para.get('style', ''),
            })
    return rows


def preview_extract(idml_path: str, lang_code: str, max_rows: int = 100) -> dict:
    """
    預覽萃取結果（只回傳前 max_rows 筆）。
    """
    rows = extract_for_import(idml_path, lang_code)
    return {
        'total': len(rows),
        'preview': rows[:max_rows],
        'lang_code': lang_code,
    }
