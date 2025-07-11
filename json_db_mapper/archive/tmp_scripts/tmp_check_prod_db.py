"""
Check main production database
"""
import sqlite3

def check_production_db():
    db_path = '../data/database/production.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f'Tables in main production database ({len(tables)}):')
    for i, table in enumerate(tables):
        if i < 20:  # Show first 20 tables
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f'  {table:<40} {count:>6} records')
        elif i == 20:
            print(f'  ... and {len(tables) - 20} more tables')
    
    # Check for mapping tables specifically
    mapping_tables = [t for t in tables if 'map' in t.lower()]
    print(f'\nMapping tables found: {len(mapping_tables)}')
    for table in mapping_tables[:10]:
        print(f'  - {table}')
    if len(mapping_tables) > 10:
        print(f'  ... and {len(mapping_tables) - 10} more')
    
    conn.close()

if __name__ == "__main__":
    check_production_db()
