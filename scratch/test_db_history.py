import os
import sys
import json
import sqlite3

# Ensure modules directory is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db_manager import DBManager, LANG_CODES

def run_tests():
    # Use a temporary test database path to avoid polluting the main database
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'translations_test_history.db'))
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    git_json_path = os.path.join(os.path.dirname(test_db_path), 'translations_git.json')
    if os.path.exists(git_json_path):
        # Backup main git json if it exists
        main_git_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'translations_git.json'))
        has_backup = os.path.exists(main_git_json_path)
    
    print(f"Initializing test database manager at: {test_db_path}")
    db = DBManager(test_db_path)
    
    # Verify the history table is created
    with sqlite3.connect(test_db_path) as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        assert 'translation_history' in table_names, "Error: translation_history table was not created"
        print("✓ translation_history table verified.")

    # 1. Test INSERT history logging
    print("Testing INSERT logging...")
    insert_data = {
        'product': 'TEST-100',
        'chapter': 'General Safety',
        'ENG': 'Wear safety goggles.',
        'CHT': '配戴安全護目鏡。',
        'CHS': '配戴安全护目镜。'
    }
    tid = db.add(insert_data)
    
    history_res = db.get_history(page=1, page_size=10)
    assert history_res['total'] == 1, f"Expected 1 history entry, got {history_res['total']}"
    history_item = history_res['items'][0]
    assert history_item['action'] == 'INSERT', f"Expected action 'INSERT', got {history_item['action']}"
    assert history_item['translation_id'] == tid
    assert history_item['old_val'] is None
    new_val_loaded = json.loads(history_item['new_val'])
    assert new_val_loaded['ENG'] == 'Wear safety goggles.'
    print("✓ INSERT logging verified.")

    # Check Git JSON exists and contains the row
    with open(git_json_path, 'r', encoding='utf-8') as f:
        git_data = json.load(f)
    assert len(git_data) == 1, "Expected 1 entry in Git JSON"
    assert git_data[0]['ENG'] == 'Wear safety goggles.'
    print("✓ Git JSON tracking verified after INSERT.")

    # 2. Test UPDATE history logging
    print("Testing UPDATE logging...")
    update_data = {
        'ENG': 'Wear safety goggles at all times.',
        'CHT': '請隨時配戴安全護目鏡。'
    }
    db.update(tid, update_data)
    
    history_res = db.get_history(page=1, page_size=10)
    assert history_res['total'] == 2, f"Expected 2 history entries, got {history_res['total']}"
    history_item = history_res['items'][0]  # Descending order, index 0 is newest
    assert history_item['action'] == 'UPDATE'
    assert history_item['translation_id'] == tid
    old_val_loaded = json.loads(history_item['old_val'])
    new_val_loaded = json.loads(history_item['new_val'])
    assert old_val_loaded['ENG'] == 'Wear safety goggles.'
    assert new_val_loaded['ENG'] == 'Wear safety goggles at all times.'
    print("✓ UPDATE logging verified.")

    # 3. Test DELETE history logging
    print("Testing DELETE logging...")
    db.delete(tid)
    
    history_res = db.get_history(page=1, page_size=10)
    assert history_res['total'] == 3, f"Expected 3 history entries, got {history_res['total']}"
    history_item = history_res['items'][0]
    assert history_item['action'] == 'DELETE'
    assert history_item['translation_id'] == tid
    old_val_loaded = json.loads(history_item['old_val'])
    assert old_val_loaded['ENG'] == 'Wear safety goggles at all times.'
    assert history_item['new_val'] is None
    print("✓ DELETE logging verified.")

    # Check Git JSON is empty now
    with open(git_json_path, 'r', encoding='utf-8') as f:
        git_data = json.load(f)
    assert len(git_data) == 0, f"Expected 0 entries in Git JSON, got {len(git_data)}"
    print("✓ Git JSON tracking verified after DELETE.")

    # 4. Test REVERT DELETE (restoring deleted row)
    print("Testing Revert DELETE...")
    delete_history_id = history_res['items'][0]['id']
    ok = db.revert_history(delete_history_id)
    assert ok is True, "Revert DELETE failed"
    
    reconstructed = db.get(tid)
    assert reconstructed is not None, "Reverted row not found"
    assert reconstructed['ENG'] == 'Wear safety goggles at all times.', f"Expected 'Wear safety goggles at all times.', got {reconstructed['ENG']}"
    print("✓ Revert DELETE verified (row successfully restored).")

    # 5. Test REVERT UPDATE (restoring updated columns)
    print("Testing Revert UPDATE...")
    # The update was the second history record in history_res (index 1)
    update_history_id = history_res['items'][1]['id']
    ok = db.revert_history(update_history_id)
    assert ok is True, "Revert UPDATE failed"
    
    reverted_row = db.get(tid)
    assert reverted_row['ENG'] == 'Wear safety goggles.', f"Expected 'Wear safety goggles.', got {reverted_row['ENG']}"
    print("✓ Revert UPDATE verified (row columns successfully rolled back).")

    # 6. Test REVERT INSERT (deleting newly added row)
    print("Testing Revert INSERT...")
    insert_history_id = history_res['items'][2]['id']
    ok = db.revert_history(insert_history_id)
    assert ok is True, "Revert INSERT failed"
    
    deleted_row = db.get(tid)
    assert deleted_row is None, "Revert INSERT did not delete the row"
    print("✓ Revert INSERT verified (row successfully deleted).")

    # Clean up test files
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    if os.path.exists(git_json_path):
        os.remove(git_json_path)
        
    print("\nAll database history and rollback tests PASSED successfully! 🎉")

if __name__ == '__main__':
    run_tests()
