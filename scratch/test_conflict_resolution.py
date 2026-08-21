import json
import os
import openpyxl
from io import BytesIO
from app import app, db

def run_tests():
    print("=== STARTING CONFLICT RESOLUTION TESTS ===")
    
    # 1. Prepare initial data in the database
    # Let's ensure our test string exists
    test_eng = "Test Conflict Original String"
    
    # Clean up previous tests if any
    with db._get_conn() as conn:
        conn.execute('DELETE FROM translations WHERE "ENG" = ?', (test_eng,))
        conn.execute('DELETE FROM pending_conflicts WHERE eng_text = ?', (test_eng,))
        conn.execute('DELETE FROM conflict_logs WHERE eng_text = ?', (test_eng,))
        
    db.add({
        "ENG": test_eng,
        "GER": "Alter Deutscher Text",
        "FRE": "Ancien texte francais",
        "product": "TEST-PROD",
        "chapter": "TEST-CHAP"
    })
    print("1. Seeded initial DB record.")
    
    # Verify it exists
    existing = db.lookup_eng(test_eng)
    assert existing is not None
    assert existing["GER"] == "Alter Deutscher Text"
    assert existing["FRE"] == "Ancien texte francais"
    
    # 2. Generate conflicting Excel file
    # We will import:
    # GER: "Neuer deutscher Text" (Conflict!)
    # FRE: "Ancien texte francais" (No conflict)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ENG", "GER", "FRE", "product", "chapter"])
    ws.append([test_eng, "Neuer deutscher Text", "Ancien texte francais", "TEST-PROD", "TEST-CHAP"])
    
    excel_io = BytesIO()
    wb.save(excel_io)
    excel_io.seek(0)
    print("2. Created dummy conflicting Excel file in memory.")
    
    # 3. Request API to import with conflict detection
    client = app.test_client()
    response = client.post(
        '/api/import/excel-with-conflicts',
        data={'file': (excel_io, 'test_conflict.xlsx')},
        content_type='multipart/form-data'
    )
    
    print("3. Sent Excel import request. Status:", response.status_code)
    assert response.status_code == 200
    res_data = response.json
    print("   Response:", res_data)
    assert res_data["ok"] is True
    assert res_data["conflict_count"] == 1
    assert res_data["imported_count"] == 0 # because this row has a conflict
    
    # 4. Fetch pending conflicts via API
    pending_res = client.get('/api/import/pending-conflicts')
    print("4. Fetched pending conflicts. Status:", pending_res.status_code)
    assert pending_res.status_code == 200
    pending_data = pending_res.json
    assert pending_data["ok"] is True
    
    # Find our conflict row
    target_conflict = None
    for c in pending_data["conflicts"]:
        if c["eng_text"] == test_eng:
            target_conflict = c
            break
            
    assert target_conflict is not None
    assert target_conflict["lang_code"] == "GER"
    assert target_conflict["db_val"] == "Alter Deutscher Text"
    assert target_conflict["import_val"] == "Neuer deutscher Text"
    print("   Found correct pending conflict row:", target_conflict)
    
    pending_id = target_conflict["id"]
    
    # 5. Resolve conflict (Choose KEEP_IMPORT to update the DB)
    resolve_body = {
        "resolutions": [
            {
                "pending_id": pending_id,
                "decision": "KEEP_IMPORT"
            }
        ]
    }
    resolve_res = client.post(
        '/api/import/resolve-conflicts',
        data=json.dumps(resolve_body),
        content_type='application/json'
    )
    print("5. Resolved conflict (KEEP_IMPORT). Status:", resolve_res.status_code)
    assert resolve_res.status_code == 200
    resolve_data = resolve_res.json
    assert resolve_data["ok"] is True
    assert resolve_data["resolved_count"] == 1
    
    # 6. Verify database updates and logs
    # DB translation should now be updated to Neuer deutscher Text
    updated_db = db.lookup_eng(test_eng)
    assert updated_db["GER"] == "Neuer deutscher Text"
    print("6. Verified database updated to new translation.")
    
    # Pending conflict list should no longer contain this ID
    pending_res2 = client.get('/api/import/pending-conflicts')
    pending_data2 = pending_res2.json
    assert not any(c["id"] == pending_id for c in pending_data2["conflicts"])
    print("   Verified pending conflict removed.")
    
    # Conflict log should exist
    logs_res = client.get(f'/api/import/conflict-logs?q={test_eng}')
    logs_data = logs_res.json
    assert logs_data["ok"] is True
    assert logs_data["total"] == 1
    log_item = logs_data["items"][0]
    assert log_item["eng_text"] == test_eng
    assert log_item["lang_code"] == "GER"
    assert log_item["decision"] == "KEEP_IMPORT"
    assert log_item["chosen_val"] == "Neuer deutscher Text"
    print("   Verified conflict logs recorded correctly.")
    
    # Clean up test database changes
    with db._get_conn() as conn:
        conn.execute('DELETE FROM translations WHERE "ENG" = ?', (test_eng,))
        conn.execute('DELETE FROM pending_conflicts WHERE eng_text = ?', (test_eng,))
        conn.execute('DELETE FROM conflict_logs WHERE eng_text = ?', (test_eng,))
    print("7. Cleaned up seeded database records.")
    
    print("\n🎉 ALL CONFLICT RESOLUTION TESTS PASSED! 🎉")

if __name__ == '__main__':
    run_tests()
