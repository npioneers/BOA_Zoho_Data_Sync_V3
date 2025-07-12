#!/usr/bin/env python3

import sqlite3
from pathlib import Path

db_path = Path('data/database/production.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check a few JSON tables to see their import_timestamp
tables_to_check = ['json_invoices', 'json_bills', 'json_contacts']

for table in tables_to_check:
    print(f'\n📋 {table}:')
    
    try:
        # Check if import_timestamp column exists
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        has_import_timestamp = any(col[1] == 'import_timestamp' for col in columns)
        print(f'  Has import_timestamp column: {has_import_timestamp}')
        
        if has_import_timestamp:
            cursor.execute(f'SELECT MAX(import_timestamp) FROM {table}')
            max_import = cursor.fetchone()[0]
            print(f'  Latest import_timestamp: {max_import}')
            
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE import_timestamp LIKE '2025-07-12%'")
            today_count = cursor.fetchone()[0]
            print(f'  Records imported today: {today_count}')
        else:
            # Check row count
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f'  Total records: {count}')
            
    except Exception as e:
        print(f'  Error checking {table}: {e}')

conn.close()
