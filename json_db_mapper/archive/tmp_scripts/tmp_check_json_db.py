"""
Check JSON database for tables
"""
import sqlite3

def check_json_database():
    db_path = '../backups/json_sync_backup_20250707_222640.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f'Tables in json_sync_backup database ({len(tables)}):')
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f'  {table:<40} {count:>6} records')
        
        # Check for JSON-prefixed tables specifically
        json_tables = [table for table in tables if table.startswith('json_')]
        print(f'\nJSON tables found: {len(json_tables)}')
        for table in json_tables:
            print(f'  - {table}')
            
        conn.close()
        
    except Exception as e:
        print(f'Error accessing database: {e}')

if __name__ == "__main__":
    check_json_database()
