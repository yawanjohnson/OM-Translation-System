"""
db_manager.py - SQLite 多語言資料庫管理
支援 19 語言代碼：ENG GER DUT DAN FRE SPA ITA GRK POL PRB RUS CHT JPN KOR VTM THI ARB TRK CHS
"""
import re
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


def clean_text(text: str) -> str:
    """文字清洗規則：
    1. 移除控制字元：\r, \n, \t 以及控制字元區間（\\x00-\\x1f）
    1. 移除控制字元：\r, \n, \t 以及控制字元區間（\x00-\x1f）
    2. 正規化排版空白：\u00a0, \u2028, \u2029, \u3000 轉為一般空格
    3. 連續空格縮減：多個連續空格合併為單一空格，並清除前後端餘白
    """
    if not text:
        return ''
    text = str(text)
    # 將 \r, \n, \t 轉為空格，並移除 \x00-\x1f 控制字元
    text = re.sub(r'[\r\n\t]', ' ', text)
    text = re.sub(r'[\x00-\x1f]', '', text)
    # 轉換 NBSP, Unicode分行符和全形空白為普通空白
    text = (text.replace('\u00a0', ' ')
                .replace('\u2028', ' ')
                .replace('\u2029', ' ')
                .replace('\u3000', ' '))
    # 合併多個連續空格為單一空格
    text = re.sub(r' +', ' ', text)
    # 清除首尾空白
    return text.strip()


def should_skip_translation(text: str) -> bool:
    """過濾條件：若內容長度 <= 1 或為純數字/純符號，則跳過比對，避免誤替換符號或頁碼。"""
    cleaned = clean_text(text)
    if not cleaned:
        return True
    if len(cleaned) <= 1:
        return True
    # 判斷是否為純數字或符號 (去除正負號、小數點、逗號、百分號後，若只剩數字則當作純數字)
    num_test = re.sub(r'[-+.,%\s]', '', cleaned)
    if num_test.isdigit() or not num_test:
        return True
    return False


def _normalize(text: str) -> str:
    """比對用正規化"""
    return clean_text(text)


def split_prefix_suffix(text: str):
    """將字串拆分為前綴符號、核心文字與尾綴符號。
    例如："• Service should only be done..." -> ("• ", "Service should only be done...", "")
          ": Do not remove..." -> (": ", "Do not remove...", "")
          "WARNING:" -> ("", "WARNING", ":")
          "□ Handlebar Set (30)" -> ("□ ", "Handlebar Set", " (30)")
    """
    if not text:
        return '', '', ''
    text_str = str(text)
    # 匹配開頭的符號：空白、子彈點 (•, \u2022, \u2023, \u2043, \u2219)、星號 (*)、減號 (-)、冒號 (:)、點 (.)、常用符號如 □■○●✔✓
    prefix_match = re.match(r'^([\s\u2022•\u2023\u2043\u2219*\-:\.□■○●✔✓]*)', text_str)
    prefix = prefix_match.group(1) if prefix_match else ''
    core_and_suffix = text_str[len(prefix):]
    
    # 1. 匹配結尾的標點與空白符號
    suffix_match = re.search(r'([\s:\.]*)$', core_and_suffix)
    suffix = suffix_match.group(1) if suffix_match else ''
    
    if suffix:
        core = core_and_suffix[:-len(suffix)]
    else:
        core = core_and_suffix
        
    # 2. 匹配 core 尾端的零件/括號數字（例如 (30), (38L), (4,5) 等不需翻譯的零件編號或標籤）
    paren_match = re.search(r'(\s*\([\d\s,a-zA-Z&/-]+\))$', core)
    if paren_match:
        paren_part = paren_match.group(1)
        core = core[:-len(paren_part)]
        suffix = paren_part + suffix
        
    return prefix, core, suffix


def split_step_number(text: str) -> tuple[str, str] | None:
    """
    將步驟字串拆分為「基礎文字」與「末尾數字」。
    例如："ASSEMBLY STEP 3" -> ("ASSEMBLY STEP", "3")
          "STEP 12" -> ("STEP", "12")
    """
    match = re.match(r'^(.+?)\s+(\d+)$', text.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _clean_row_translations(self, row) -> dict:
        """
        將回傳的資料庫字典中的各語言翻譯，自動剝離尾端的括號與零件編號（例如 (21R)、(11) 等），
        以利動態套用 InDesign 端的零件代碼或保持無代碼狀態。
        """
        cleaned_row = dict(row)
        for lang_col in cleaned_row.keys():
            if lang_col == 'id' or lang_col == 'ENG':
                continue
            val = cleaned_row[lang_col]
            if val and isinstance(val, str):
                # 剝離尾端的括號編號，保留純翻譯主體
                _, val_core, _ = split_prefix_suffix(val)
                cleaned_row[lang_col] = val_core
        return cleaned_row

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

        CREATE TABLE IF NOT EXISTS pending_conflicts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            import_time   TEXT DEFAULT (datetime('now','localtime')),
            product       TEXT DEFAULT "",
            chapter       TEXT DEFAULT "",
            eng_text      TEXT,
            lang_code     TEXT,
            db_val        TEXT,
            import_val    TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_pending_eng ON pending_conflicts (eng_text);

        CREATE TABLE IF NOT EXISTS conflict_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id      TEXT,
            eng_text      TEXT,
            lang_code     TEXT,
            db_val        TEXT,
            import_val    TEXT,
            chosen_val    TEXT,
            decision      TEXT,
            resolved_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_log_eng ON conflict_logs (eng_text);

        CREATE TABLE IF NOT EXISTS translation_history (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            translation_id INTEGER,
            action         TEXT,
            old_val        TEXT,
            new_val        TEXT,
            created_at     TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_history_tid ON translation_history (translation_id);
        """
        with self._get_conn() as conn:
            conn.executescript(create_sql)

    def _get_row_by_id(self, conn, tid) -> dict | None:
        row = conn.execute('SELECT * FROM translations WHERE id = ?', (tid,)).fetchone()
        return dict(row) if row else None

    def _has_changes(self, old_row, new_row) -> bool:
        for key in ['product', 'chapter'] + LANG_CODES:
            if old_row.get(key) != new_row.get(key):
                return True
        return False

    def _log_history(self, conn, translation_id, action, old_val, new_val):
        import json
        sql = """
        INSERT INTO translation_history (translation_id, action, old_val, new_val)
        VALUES (?, ?, ?, ?)
        """
        old_str = json.dumps(old_val, ensure_ascii=False) if old_val else None
        new_str = json.dumps(new_val, ensure_ascii=False) if new_val else None
        conn.execute(sql, (translation_id, action, old_str, new_str))

    def export_to_git_json(self):
        import json
        with self._get_conn() as conn:
            rows = conn.execute('SELECT * FROM translations ORDER BY id').fetchall()
            data_list = [dict(r) for r in rows]
        target_path = os.path.join(os.path.dirname(self.db_path), 'translations_git.json')
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2, sort_keys=True)

    def export_conflict_logs_to_git_json(self):
        import json
        with self._get_conn() as conn:
            rows = conn.execute('SELECT * FROM conflict_logs ORDER BY id').fetchall()
            data_list = [dict(r) for r in rows]
        target_path = os.path.join(os.path.dirname(self.db_path), 'conflict_logs_git.json')
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2, sort_keys=True)

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    def add(self, data: dict, suppress_export=False) -> int:
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
            tid = cur.lastrowid
            new_row = self._get_row_by_id(conn, tid)
            self._log_history(conn, tid, 'INSERT', None, new_row)
        if not suppress_export:
            self.export_to_git_json()
        return tid

    def update(self, tid: int, data: dict, suppress_export=False) -> bool:
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
            old_row = self._get_row_by_id(conn, tid)
            if not old_row:
                return False
            cur = conn.execute(sql, vals)
            if cur.rowcount > 0:
                new_row = self._get_row_by_id(conn, tid)
                if self._has_changes(old_row, new_row):
                    self._log_history(conn, tid, 'UPDATE', old_row, new_row)
                updated = True
            else:
                updated = False
        if updated and not suppress_export:
            self.export_to_git_json()
        return updated

    def delete(self, tid: int, suppress_export=False) -> bool:
        with self._get_conn() as conn:
            old_row = self._get_row_by_id(conn, tid)
            if not old_row:
                return False
            cur = conn.execute('DELETE FROM translations WHERE id = ?', (tid,))
            if cur.rowcount > 0:
                self._log_history(conn, tid, 'DELETE', old_row, None)
                deleted = True
            else:
                deleted = False
        if deleted and not suppress_export:
            self.export_to_git_json()
        return deleted

    def get(self, tid: int) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute('SELECT * FROM translations WHERE id = ?', (tid,)).fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------ #
    # 歷史紀錄與回復 (History & Revert)
    # ------------------------------------------------------------------ #

    def get_history(self, page: int = 1, page_size: int = 50, translation_id: int = None) -> dict:
        where_clauses = []
        params = []
        if translation_id:
            where_clauses.append("translation_id = ?")
            params.append(translation_id)
            
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        
        with self._get_conn() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM translation_history {where_sql}", params).fetchone()[0]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM translation_history {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
            
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': [dict(r) for r in rows]
        }

    def revert_history(self, history_id: int) -> bool:
        import json
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM translation_history WHERE id = ?", (history_id,)).fetchone()
            if not row:
                raise ValueError(f"History entry #{history_id} not found")
                
            history_item = dict(row)
            action = history_item['action']
            tid = history_item['translation_id']
            old_val = json.loads(history_item['old_val']) if history_item['old_val'] else None
            new_val = json.loads(history_item['new_val']) if history_item['new_val'] else None
            
            reverted = False
            if action == 'INSERT':
                current = self._get_row_by_id(conn, tid)
                if current:
                    conn.execute("DELETE FROM translations WHERE id = ?", (tid,))
                    self._log_history(conn, tid, 'DELETE', current, None)
                    reverted = True
                
            elif action == 'DELETE':
                current = self._get_row_by_id(conn, tid)
                if current:
                    conn.execute("DELETE FROM translations WHERE id = ?", (tid,))
                
                cols = []
                vals = []
                for key in ['id', 'product', 'chapter'] + LANG_CODES:
                    if key in old_val:
                        cols.append(f'"{key}"')
                        vals.append(old_val[key])
                sql = f"INSERT INTO translations ({', '.join(cols)}) VALUES ({', '.join('?' * len(vals))})"
                conn.execute(sql, vals)
                new_row = self._get_row_by_id(conn, tid)
                self._log_history(conn, tid, 'INSERT', None, new_row)
                reverted = True
                
            elif action == 'UPDATE':
                current = self._get_row_by_id(conn, tid)
                if not current:
                    cols = []
                    vals = []
                    for key in ['id', 'product', 'chapter'] + LANG_CODES:
                        if key in old_val:
                            cols.append(f'"{key}"')
                            vals.append(old_val[key])
                    sql = f"INSERT INTO translations ({', '.join(cols)}) VALUES ({', '.join('?' * len(vals))})"
                    conn.execute(sql, vals)
                    new_row = self._get_row_by_id(conn, tid)
                    self._log_history(conn, tid, 'INSERT', None, new_row)
                    reverted = True
                else:
                    sets = []
                    vals = []
                    for key in ['product', 'chapter'] + LANG_CODES:
                        if key in old_val:
                            sets.append(f'"{key}" = ?')
                            vals.append(old_val[key])
                    sets.append('updated_at = datetime("now","localtime")')
                    vals.append(tid)
                    sql = f"UPDATE translations SET {', '.join(sets)} WHERE id = ?"
                    conn.execute(sql, vals)
                    new_row = self._get_row_by_id(conn, tid)
                    if self._has_changes(current, new_row):
                        self._log_history(conn, tid, 'UPDATE', current, new_row)
                    reverted = True
                    
        if reverted:
            self.export_to_git_json()
        return reverted

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
        """
        用英文原文查詢一筆完整翻譯。
        比對規則：去除首尾標點/符號（Core 比對）+ 大小寫不敏感 + 空白正規化。
        查詢成功回傳完整資料庫列，find 由呼叫方自行決定是用 IDML 原文還是 DB 版本。
        """
        normalized = _normalize(eng_text).lower()
        if not normalized:
            return None
        # 取得搜尋文字的核心部分
        _, search_core, _ = split_prefix_suffix(normalized)
        search_core_norm = _normalize(search_core).lower()

        with self._get_conn() as conn:
            # 在 Python 層處理正規化（SQLite 的 LOWER() 對非 ASCII 支援有限）
            rows = conn.execute(
                'SELECT * FROM translations WHERE "ENG" != "" AND "ENG" IS NOT NULL'
            ).fetchall()
            for row in rows:
                db_eng = row['ENG'] or ''
                # 取得資料庫列的核心部分
                _, db_core, _ = split_prefix_suffix(db_eng)
                if _normalize(db_core).lower() == search_core_norm:
                    return self._clean_row_translations(row)
                    
        # 2. 精準比對失敗時，嘗試進行步驟數字的動態匹配與套用
        step_row = self.lookup_step_translation(eng_text)
        if step_row:
            return step_row

        return None

    def lookup_step_translation(self, eng_text: str) -> dict | None:
        """
        嘗試進行步驟數字的動態匹配與套用。
        例如：InDesign 是 "ASSEMBLY STEP 3"，但 DB 只有 "ASSEMBLY STEP 1" -> "組裝步驟 1"。
        系統會將所有目標語言中結尾的 "1" 替換成 "3"，產生新的動態翻譯字典。
        """
        res = split_step_number(eng_text)
        if not res:
            return None
        search_base, search_num = res
        search_base_norm = search_base.lower()

        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM translations WHERE "ENG" != "" AND "ENG" IS NOT NULL'
            ).fetchall()
            for row in rows:
                db_eng = row['ENG'] or ''
                db_res = split_step_number(db_eng)
                if db_res:
                    db_base, db_num = db_res
                    if db_base.lower() == search_base_norm:
                        # 複製整列資料，並針對每個語言欄位動態替換數字
                        remapped_row = dict(row)
                        remapped_row['id'] = f"{row['id']}-step-remap"
                        remapped_row['ENG'] = eng_text
                        
                        for lang_col in remapped_row.keys():
                            if lang_col == 'id' or lang_col == 'ENG':
                                continue
                            val = row[lang_col]
                            if val and isinstance(val, str):
                                val_res = split_step_number(val)
                                if val_res:
                                    val_base, val_num = val_res
                                    if val_num == db_num:
                                        remapped_row[lang_col] = val_base + " " + search_num
                                        continue
                                if val.endswith(db_num):
                                    remapped_row[lang_col] = val[:-len(db_num)] + search_num
                        return remapped_row
        return None

    def find_similar_eng(self, eng_text: str, threshold: float = 0.85) -> dict | None:
        """
        在資料庫中比對尋找與給定英文原文「最相似」的條目（模糊比對，排除 100% 完全相同者）。
        用於主動抓出 InDesign 原文中的拼字錯誤（Typo）。
        """
        import difflib
        normalized = _normalize(eng_text).lower()
        if not normalized:
            return None
        # 取得搜尋文字的核心部分
        _, search_core, _ = split_prefix_suffix(normalized)
        search_core_norm = _normalize(search_core).lower()

        best_match = None
        best_ratio = 0.0

        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM translations WHERE "ENG" != "" AND "ENG" IS NOT NULL'
            ).fetchall()
            for row in rows:
                db_eng = row['ENG'] or ''
                # 取得資料庫列的核心部分
                _, db_core, _ = split_prefix_suffix(db_eng)
                db_core_norm = _normalize(db_core).lower()
                
                # 計算字串相似比率
                ratio = difflib.SequenceMatcher(None, search_core_norm, db_core_norm).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = row

        # 相似度在 [threshold, 0.999] 區間內，判定為疑似錯字/極相似句型
        if best_match and threshold <= best_ratio < 0.999:
            res = dict(best_match)
            res['similarity'] = best_ratio
            return res
        return None


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
                self.update(existing['id'], data, suppress_export=True)
                updated += 1
            else:
                self.add(data, suppress_export=True)
                added += 1
        if added > 0 or updated > 0:
            self.export_to_git_json()
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

    # ------------------------------------------------------------------ #
    # 待處理衝突 (Pending Conflicts) 與 衝突歷史紀錄 (Conflict Logs) 方法
    # ------------------------------------------------------------------ #

    def add_pending_conflict(self, product: str, chapter: str, eng_text: str,
                             lang_code: str, db_val: str, import_val: str) -> int:
        sql = """
        INSERT INTO pending_conflicts (product, chapter, eng_text, lang_code, db_val, import_val)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with self._get_conn() as conn:
            cur = conn.execute(sql, (product, chapter, eng_text, lang_code, db_val, import_val))
            return cur.lastrowid

    def get_pending_conflicts(self) -> list:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM pending_conflicts ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def get_pending_conflict(self, pending_id: int) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM pending_conflicts WHERE id = ?", (pending_id,)).fetchone()
            return dict(row) if row else None

    def delete_pending_conflict(self, pending_id: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM pending_conflicts WHERE id = ?", (pending_id,))
            return cur.rowcount > 0

    def add_conflict_log(self, batch_id: str, eng_text: str, lang_code: str,
                         db_val: str, import_val: str, chosen_val: str, decision: str, suppress_export=False) -> int:
        sql = """
        INSERT INTO conflict_logs (batch_id, eng_text, lang_code, db_val, import_val, chosen_val, decision)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_conn() as conn:
            cur = conn.execute(sql, (batch_id, eng_text, lang_code, db_val, import_val, chosen_val, decision))
            tid = cur.lastrowid
        if not suppress_export:
            self.export_conflict_logs_to_git_json()
        return tid

    def get_conflict_logs(self, query: str = '', lang_code: str = '', page: int = 1, per_page: int = 50) -> dict:
        where_clauses = []
        params = []
        if query:
            where_clauses.append("(eng_text LIKE ? OR db_val LIKE ? OR import_val LIKE ? OR chosen_val LIKE ?)")
            params.extend([f"%{query}%"] * 4)
        if lang_code:
            where_clauses.append("lang_code = ?")
            params.append(lang_code)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        
        with self._get_conn() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM conflict_logs {where_sql}", params).fetchone()[0]
            offset = (page - 1) * per_page
            rows = conn.execute(
                f"SELECT * FROM conflict_logs {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [per_page, offset]
            ).fetchall()
            
        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'items': [dict(r) for r in rows]
        }

    # ------------------------------------------------------------------ #
    # 重複項合併與整理
    # ------------------------------------------------------------------ #

    def find_duplicate_groups(self) -> dict:
        """
        掃描資料庫中所有的重複英文原文 (ENG)。
        比對條件：去除空白與大小寫後 (LOWER(TRIM(ENG))) 相同的資料列。
        回傳:
        {
            'auto_mergeable': [
                {
                    'eng': 'Speed (kph)',
                    'rows': [row1, row2, ...],
                    'merged_preview': {'GER': 'Geschwindigkeit (km/h)', 'DUT': 'Snelheid (kph)', ...}
                },
                ...
            ],
            'conflicting': [
                {
                    'eng': 'Speed (kph)',
                    'rows': [row1, row2, ...],
                    'conflicts': {
                        'GER': ['Geschwindigkeit (km/h)', 'Geschwindigkeit']
                    },
                    'non_conflicting': {
                        'DUT': 'Snelheid (kph)'
                    }
                },
                ...
            ]
        }
        """
        with self._get_conn() as conn:
            # 1. 找出有重複的 ENG 條目 (去除前後空白、轉小寫比對)
            dup_query = """
            SELECT LOWER(TRIM("ENG")) as eng_clean, COUNT(*) as cnt
            FROM translations
            WHERE "ENG" IS NOT NULL AND "ENG" != ""
            GROUP BY eng_clean
            HAVING cnt > 1
            """
            dup_entries = conn.execute(dup_query).fetchall()
            
            auto_mergeable = []
            conflicting = []
            
            for entry in dup_entries:
                eng_clean = entry['eng_clean']
                # 撈出該組所有重複行
                rows = conn.execute(
                    'SELECT * FROM translations WHERE LOWER(TRIM("ENG")) = ? ORDER BY id ASC',
                    (eng_clean,)
                ).fetchall()
                
                rows_dict = [dict(r) for r in rows]
                if not rows_dict:
                    continue
                
                # 分析各語言翻譯值
                lang_vals = {lang: set() for lang in LANG_CODES}
                
                # 用於記錄每筆 Row 填了哪些語言
                for r in rows_dict:
                    for lang in LANG_CODES:
                        val = (r.get(lang) or '').strip()
                        if val:
                            lang_vals[lang].add(val)
                
                # 判斷有無衝突
                has_conflict = False
                conflicts_summary = {}
                non_conflicting_summary = {}
                merged_preview = {}
                
                # 英文不用算衝突，以第一個非空為準
                merged_preview['ENG'] = rows_dict[0]['ENG']
                
                for lang in LANG_CODES:
                    if lang == 'ENG':
                        continue
                    unique_vals = list(lang_vals[lang])
                    if len(unique_vals) > 1:
                        has_conflict = True
                        conflicts_summary[lang] = unique_vals
                    elif len(unique_vals) == 1:
                        non_conflicting_summary[lang] = unique_vals[0]
                        merged_preview[lang] = unique_vals[0]
                    else:
                        merged_preview[lang] = ""
                
                if has_conflict:
                    conflicting.append({
                        'eng': rows_dict[0]['ENG'],
                        'rows': rows_dict,
                        'conflicts': conflicts_summary,
                        'non_conflicting': non_conflicting_summary
                    })
                else:
                    auto_mergeable.append({
                        'eng': rows_dict[0]['ENG'],
                        'rows': rows_dict,
                        'merged_preview': merged_preview
                    })
                    
            return {
                'auto_mergeable': auto_mergeable,
                'conflicting': conflicting
            }

    def merge_duplicate_groups(self, resolutions=None) -> dict:
        """
        執行重複原文列的合併與清理。
        resolutions: list of dicts, 對於衝突組的解決方案。
          格式如: [
            {
               'eng': 'Speed (kph)', 
               'selected_values': {'GER': 'Geschwindigkeit (km/h)'}
            },
            ...
          ]
        回傳:
        {'ok': True, 'merged_auto_count': N, 'merged_conflict_count': M, 'deleted_rows_count': D}
        """
        if resolutions is None:
            resolutions = []
            
        # 轉換 resolutions 為 map，以便查詢
        res_map = {res['eng'].lower().strip(): res['selected_values'] for res in resolutions if 'eng' in res}
        
        # 1. 掃描目前的重複組
        groups = self.find_duplicate_groups()
        
        merged_auto_count = 0
        merged_conflict_count = 0
        deleted_rows_count = 0
        
        with self._get_conn() as conn:
            # A. 處理自動合併 (無衝突)
            for group in groups['auto_mergeable']:
                rows = group['rows']
                preview = group['merged_preview']
                
                # 挑選主列 (ID 最小的)
                master_row = rows[0]
                master_id = master_row['id']
                other_ids = [r['id'] for r in rows[1:]]
                
                # 彙整所有要寫入 master_row 的欄位
                update_data = {}
                # 補齊 product 和 chapter (如有)
                for r in rows:
                    if r.get('product') and not update_data.get('product'):
                        update_data['product'] = r['product']
                    if r.get('chapter') and not update_data.get('chapter'):
                        update_data['chapter'] = r['chapter']
                
                # 寫入合併後的語系翻譯
                for lang in LANG_CODES:
                    if lang == 'ENG':
                        continue
                    val = preview.get(lang) or ""
                    # 只有當 preview 有值且與 master_row 不同時才寫入
                    if val and (master_row.get(lang) or "") != val:
                        update_data[lang] = val
                
                # 更新 master_row
                if update_data:
                    old_master = self._get_row_by_id(conn, master_id)
                    sets = [f'"{k}" = ?' for k in update_data.keys()]
                    vals = list(update_data.values()) + [master_id]
                    conn.execute(f"UPDATE translations SET {', '.join(sets)} WHERE id = ?", vals)
                    new_master = self._get_row_by_id(conn, master_id)
                    if old_master and new_master and self._has_changes(old_master, new_master):
                        self._log_history(conn, master_id, 'UPDATE', old_master, new_master)
                
                # 刪除其他重複行
                if other_ids:
                    for oid in other_ids:
                        old_row = self._get_row_by_id(conn, oid)
                        if old_row:
                            self._log_history(conn, oid, 'DELETE', old_row, None)
                    placeholders = ', '.join('?' * len(other_ids))
                    conn.execute(f"DELETE FROM translations WHERE id IN ({placeholders})", other_ids)
                    deleted_rows_count += len(other_ids)
                    
                merged_auto_count += 1
                
            # B. 處理手動合併 (有衝突)
            for group in groups['conflicting']:
                eng_key = group['eng']
                eng_key_norm = eng_key.lower().strip()
                rows = group['rows']
                
                # 如果使用者提供了該衝突組的決策
                if eng_key_norm in res_map:
                    decision = res_map[eng_key_norm]
                    
                    master_row = rows[0]
                    master_id = master_row['id']
                    other_ids = [r['id'] for r in rows[1:]]
                    
                    update_data = {}
                    
                    # 補齊 product / chapter
                    for r in rows:
                        if r.get('product') and not update_data.get('product'):
                            update_data['product'] = r['product']
                        if r.get('chapter') and not update_data.get('chapter'):
                            update_data['chapter'] = r['chapter']
                            
                    # 對於每個語系
                    for lang in LANG_CODES:
                        if lang == 'ENG':
                            continue
                        
                        # 如果有衝突，使用使用者的決策
                        if lang in group['conflicts']:
                            val = decision.get(lang) or ""
                        else:
                            # 無衝突語系，直接取非空的值
                            val = group['non_conflicting'].get(lang) or ""
                            
                        if val:
                            update_data[lang] = val
                            
                    # 更新主列
                    if update_data:
                        old_master = self._get_row_by_id(conn, master_id)
                        sets = [f'"{k}" = ?' for k in update_data.keys()]
                        vals = list(update_data.values()) + [master_id]
                        conn.execute(f"UPDATE translations SET {', '.join(sets)} WHERE id = ?", vals)
                        new_master = self._get_row_by_id(conn, master_id)
                        if old_master and new_master and self._has_changes(old_master, new_master):
                            self._log_history(conn, master_id, 'UPDATE', old_master, new_master)
                        
                    # 刪除其他列
                    if other_ids:
                        for oid in other_ids:
                            old_row = self._get_row_by_id(conn, oid)
                            if old_row:
                                self._log_history(conn, oid, 'DELETE', old_row, None)
                        placeholders = ', '.join('?' * len(other_ids))
                        conn.execute(f"DELETE FROM translations WHERE id IN ({placeholders})", other_ids)
                        deleted_rows_count += len(other_ids)
                        
                    merged_conflict_count += 1
        
        if merged_auto_count > 0 or merged_conflict_count > 0:
            self.export_to_git_json()
            
        return {
            'ok': True,
            'merged_auto_count': merged_auto_count,
            'merged_conflict_count': merged_conflict_count,
            'deleted_rows_count': deleted_rows_count
        }

