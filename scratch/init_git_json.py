import os
import sys

# Ensure modules directory is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db_manager import DBManager

def main():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'translations.db'))
    print(f"Connecting to database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file does not exist at {db_path}")
        return
        
    db = DBManager(db_path)
    print("Database manager initialized (schema tables ensured).")
    
    print("Exporting current translations to translations_git.json...")
    db.export_to_git_json()
    
    print("Exporting current conflict logs to conflict_logs_git.json...")
    db.export_conflict_logs_to_git_json()
    
    json_path = os.path.join(os.path.dirname(db_path), 'translations_git.json')
    if os.path.exists(json_path):
        size = os.path.getsize(json_path)
        print(f"Success! Git-trackable JSON exported to {json_path} (size: {size} bytes).")
    else:
        print("Error: JSON file was not generated.")

if __name__ == '__main__':
    main()
