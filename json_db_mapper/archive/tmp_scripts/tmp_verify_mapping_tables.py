"""
Quick verification script for mapping tables
"""
import sqlite3

def verify_mapping_tables():
    db_path = '../backups/production_db_refactor_complete_20250707_211611.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all mapping tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_map' ORDER BY name")
    mapping_tables = [row[0] for row in cursor.fetchall()]
    
    print(f'Found {len(mapping_tables)} mapping tables:')
    for table in mapping_tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'  {table:<35} {count:>5} fields')
    
    # Sample a few fields from one mapping table
    if mapping_tables:
        print(f'\nSample from {mapping_tables[0]}:')
        cursor.execute(f'SELECT field_name, field_type, is_primary_key FROM {mapping_tables[0]} LIMIT 10')
        for row in cursor.fetchall():
            print(f'  {row[0]:<30} {row[1]:<15} PK: {bool(row[2])}')
    
    conn.close()

if __name__ == "__main__":
    verify_mapping_tables()
