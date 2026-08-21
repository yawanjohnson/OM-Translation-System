import sqlite3

conn = sqlite3.connect('data/translations.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(translations)")
columns = [row['name'] for row in cursor.fetchall()]
print("Columns in translations table:", columns)

# Check total count
cursor.execute("SELECT COUNT(*) as cnt FROM translations")
total = cursor.fetchone()['cnt']
print("Total rows in database:", total)

# Show first 10 rows
cursor.execute("SELECT * FROM translations LIMIT 10")
rows = cursor.fetchall()
for i, row in enumerate(rows, 1):
    print(f"\nRow {i}:")
    for col in columns:
        if row[col]:
            print(f"  {col}: {repr(row[col])}")

conn.close()
