"""
db_manager.py - SQLite 多語言資料庫管理
支援 19 語言代碼：ENG GER DUT DAN FRE SPA ITA GRK POL PRB RUS CHT JPN KOR VTM THI ARB TRK CHS
"""
import sqlite3
import os
from datetime import datetime

LANG_CODES = [
    'ENG', 'GER', 'DUT', 'DAN', 'FRE', 'SPA', 'ITA', 'GRK',
    'POL', 'PRB', 'RUS', 'CHT', 'JPN', 'KOR', 'VTM', 'THI',
    'ARB', 'TRK', 'CHS'
]

LANG_NAMES = {
    'ENG': 'English',
    'GER': 'Deutsch',
    'DUT': 'Nederlands',
    'DAN': 'Dansk',
    'FRE': 'Français',
    'SPA': 'Español',
    'ITA': 'Italiano',
    'GRK': 'Ελληνικά',
    'POL': 'Polski',
    'PRB': 'Português',
    'RUS': 'Русский',
    'CHT': '繁體中文',
    'JPN': '日本語',
    'KOR': '한국어',
    'VTM': 'Tiếng Việt',
    'THI': 'ภาษาไทย',
    'ARB': 'العربية',
    'TRK': 'Türkçe',
    'CHS': '简体中文',
}


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """建立資料表（如不存在）"""
        lang_cols = ',\n    '.join(f'"{code}" TEXT DEFAULT ""' for code in LANG_CODES)
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS translations (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            product  TEXT DEFAULT "",
            chapter  TEXT DEFAULT "",
            {lang_cols},
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_eng ON translations ("ENG");
        """
        with self._get_conn() as conn:
            conn.executescript(create_sql)

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    def add(self, data: dict) -> int:
        """新增一筆翻譯。data 可含任意語言欄位 + product/chapter。"""
        cols = []
        vals = []
        for key in ['product', 'chapter'] + LANG_CODES:
            if key in data and data[key] is not None:
                cols.append(f'"{key}"')
                vals.append(data[key])
        if not cols:
            raise ValueError('No data to insert')
        sql = f"INSERT INTO translations ({', '.join(cols)}) VALUES ({', '.join('?' * len(vals))})"
        with self._get_conn() as conn:
            cur = conn.execute(sql, vals)
            return cur.lastrowid

    def update(self, tid: int, data: dict) -> bool:
        """更新指定 id 的欄位。"""
        allowed = set(['product', 'chapter'] + LANG_CODES)
        sets = []
        vals = []
        for key, val in data.items():
            if key in allowed:
                sets.append(f'"{key}" = ?')
                vals.append(val)
        if not sets:
            return False
        sets.append('updated_at = datetime("now","localtime")')
        vals.append(tid)
        sql = f"UPDATE translations SET {', '.join(sets)} WHERE id = ?"
        with self._get_conn() as conn:
            cur = conn.execute(sql, vals)
            return cur.rowcount > 0

    def delete(self, tid: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute('DELETE FROM translations WHERE id = ?', (tid,))
            return cur.rowcount > 0

    def get(self, tid: int) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute('SELECT * FROM translations WHERE id = ?', (tid,)).fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------ #
    # 搜尋
    # ------------------------------------------------------------------ #

    def search(self, query: str = '', lang: str = 'ENG',
               product: str = '', chapter: str = '',
               page: int = 1, page_size: int = 50) -> dict:
        """
        全文搜尋：在指定語言欄位中搜尋 query 字串。
        回傳 {'total': N, 'page': P, 'items': [...]}
        """
        where_clauses = []
        params = []

        if query:
            if lang and lang in LANG_CODES:
                where_clauses.append(f'"{lang}" LIKE ?')
                params.append(f'%{query}%')
            else:
                # 搜尋所有語言
                lang_conds = ' OR '.join(f'"{c}" LIKE ?' for c in LANG_CODES)
                where_clauses.append(f'({lang_conds})')
                params.extend([f'%{query}%'] * len(LANG_CODES))

        if product:
            where_clauses.append('product LIKE ?')
            params.append(f'%{product}%')
        if chapter:
            where_clauses.append('chapter LIKE ?')
            params.append(f'%{chapter}%')

        where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

        with self._get_conn() as conn:
            total = conn.execute(
                f'SELECT COUNT(*) FROM translations {where_sql}', params
            ).fetchone()[0]

            offset = (page - 1) * page_size
            rows = conn.execute(
                f'SELECT * FROM translations {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?',
                params + [page_size, offset]
            ).fetchall()

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': [dict(r) for r in rows]
        }

    def get_all(self) -> list:
        with self._get_conn() as conn:
            rows = conn.execute('SELECT * FROM translations ORDER BY id').fetchall()
            return [dict(r) for r in rows]

    def lookup_eng(self, eng_text: str) -> dict | None:
        """用英文原文查詢一筆完整翻譯（精確比對）。"""
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM translations WHERE "ENG" = ? LIMIT 1', (eng_text,)
            ).fetchone()
            return dict(row) if row else None

    def bulk_upsert(self, rows: list) -> dict:
        """
        批次新增/更新。
        rows: list of dicts，每個 dict 含語言欄位。
        若 ENG 欄位已存在，則更新；否則新增。
        回傳 {'added': N, 'updated': N, 'skipped': N, 'skipped_details': [...]}
        """
        added = updated = skipped = 0
        skipped_details = []

        # 檢查是否有任何一列包含 ENG 欄位，若是所有資料都沒有 ENG，代表表頭未正確對照到 ENG
        has_eng_column = False
        for data in rows:
            if 'ENG' in data:
                has_eng_column = True
                break

        if rows and not has_eng_column:
            return {
                'added': 0,
                'updated': 0,
                'skipped': len(rows),
                'skipped_details': ['檔案中未偵測到「英文 (ENG)」欄位，無法進行翻譯對照與匯入。請確認表頭是否包含「ENG」或「英文」。']
            }

        for data in rows:
            row_num = data.get('_row_num')
            eng_val = data.get('ENG', '').strip() if 'ENG' in data and data['ENG'] is not None else ''
            if not eng_val:
                skipped += 1
                row_label = f"第 {row_num} 列" if row_num else "未知列"
                # 檢查是否有填寫其他非英文的欄位
                other_fields = [k for k, v in data.items() if k not in ('ENG', '_row_num') and v and str(v).strip()]
                if other_fields:
                    field_desc = ", ".join(other_fields)
                    skipped_details.append(f"{row_label}：英文 (ENG) 欄位空白，但其他欄位有資料 ({field_desc})，已被略過。")
                else:
                    skipped_details.append(f"{row_label}：無有效翻譯內容，已被略過。")
                continue
            existing = self.lookup_eng(eng_val)
            if existing:
                self.update(existing['id'], data)
                updated += 1
            else:
                self.add(data)
                added += 1
        return {'added': added, 'updated': updated, 'skipped': skipped, 'skipped_details': skipped_details}

    def get_stats(self) -> dict:
        """取得資料庫統計資訊。"""
        with self._get_conn() as conn:
            total = conn.execute('SELECT COUNT(*) FROM translations').fetchone()[0]
            lang_counts = {}
            for code in LANG_CODES:
                count = conn.execute(
                    f'SELECT COUNT(*) FROM translations WHERE "{code}" != "" AND "{code}" IS NOT NULL'
                ).fetchone()[0]
                lang_counts[code] = count
        return {'total': total, 'by_language': lang_counts}
