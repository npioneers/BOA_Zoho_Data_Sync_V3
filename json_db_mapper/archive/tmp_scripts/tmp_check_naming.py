"""
Check current mapping table names
"""
import sqlite3

def check_mapping_tables():
    db_path = '../backups/json_sync_backup_20250707_222640.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%_map' OR name LIKE 'map_%') ORDER BY name")
    mapping_tables = [row[0] for row in cursor.fetchall()]
    
    print('Current mapping tables in database:')
    for table in mapping_tables:
        print(f'  {table}')
    
    print(f'\nTotal mapping tables: {len(mapping_tables)}')
    
    # Check if any start with map_
    map_prefix = [t for t in mapping_tables if t.startswith('map_')]
    map_suffix = [t for t in mapping_tables if t.endswith('_map')]
    
    print(f'Tables with map_ prefix: {len(map_prefix)}')
    print(f'Tables with _map suffix: {len(map_suffix)}')
    
    conn.close()

if __name__ == "__main__":
    check_mapping_tables()
