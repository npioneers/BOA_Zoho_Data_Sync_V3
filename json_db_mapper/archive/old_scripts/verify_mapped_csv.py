"""
Verify mapped_CSV column values
"""
import sqlite3

def verify_mapped_csv():
    db_path = '../data/database/production.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print('Checking mapped_CSV values in JSON mapping tables:')
    print('=' * 60)
    
    # Get all JSON mapping tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_json_%'")
    json_tables = [row[0] for row in cursor.fetchall()]
    
    for table in json_tables:
        cursor.execute(f"SELECT DISTINCT mapped_CSV FROM {table} WHERE mapped_CSV IS NOT NULL LIMIT 1")
        result = cursor.fetchone()
        if result:
            print(f"{table:<35} -> {result[0]}")
        else:
            print(f"{table:<35} -> NULL")
    
    conn.close()

if __name__ == "__main__":
    verify_mapped_csv()
