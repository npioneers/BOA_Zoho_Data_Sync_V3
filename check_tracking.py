#!/usr/bin/env python3

import sqlite3
from pathlib import Path

try:
    db_path = Path('data/database/production.db')
    print(f'Database path: {db_path.absolute()}')
    print(f'Database exists: {db_path.exists()}')
    
    if not db_path.exists():
        print('Exiting - database not found')
        exit()
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table_population_tracking exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='table_population_tracking'")
    table_exists = cursor.fetchone()
    print(f'table_population_tracking exists: {table_exists is not None}')
    
    if table_exists:
        # Get all records
        cursor.execute('SELECT COUNT(*) FROM table_population_tracking')
        count = cursor.fetchone()[0]
        print(f'Records in tracking table: {count}')
        
        if count > 0:
            print('\n📋 Recent population times:')
            cursor.execute('SELECT table_name, last_population_time FROM table_population_tracking ORDER BY last_population_time DESC LIMIT 15')
            rows = cursor.fetchall()
            for table_name, timestamp in rows:
                print(f'  {table_name}: {timestamp}')
                
            print('\n🔍 Tables populated today (2025-07-12):')
            cursor.execute("SELECT table_name, last_population_time FROM table_population_tracking WHERE last_population_time LIKE '2025-07-12%' ORDER BY last_population_time DESC")
            today_rows = cursor.fetchall()
            if today_rows:
                for table_name, timestamp in today_rows:
                    print(f'  {table_name}: {timestamp}')
            else:
                print('  No tables populated today')
    else:
        print('❌ table_population_tracking table does not exist')
        print('This means the enhanced tracking system is not set up yet.')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
