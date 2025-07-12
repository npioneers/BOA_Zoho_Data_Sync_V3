#!/usr/bin/env python3
"""
Check CSV table structure and timestamps
"""

import sqlite3

def check_csv_tables():
    conn = sqlite3.connect('../data/database/production.db')
    
    # Get all table names that start with csv_
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print('CSV Tables found:')
    print(f"{'Table Name':<25} | {'Records':<8} | {'Time Columns'}")
    print("-" * 80)
    
    for table in tables:
        try:
            count_result = conn.execute(f'SELECT COUNT(*) FROM `{table}`').fetchone()
            count = count_result[0] if count_result else 0
            
            columns_result = conn.execute(f'PRAGMA table_info(`{table}`)')
            all_columns = [row[1] for row in columns_result.fetchall()]
            
            time_columns = [col for col in all_columns if any(term in col.lower() for term in ['time', 'date', 'created', 'updated', 'modified'])]
            
            print(f'{table:<25} | {count:>8} | {time_columns}')
            
            # If this table has timestamp columns, show sample data
            if time_columns:
                print(f"    Sample timestamps from {time_columns[0]}:")
                sample_query = f'SELECT `{time_columns[0]}` FROM `{table}` WHERE `{time_columns[0]}` IS NOT NULL LIMIT 3'
                samples = conn.execute(sample_query).fetchall()
                for sample in samples:
                    print(f"      {sample[0]}")
                print()
            
        except Exception as e:
            print(f'{table:<25} | Error: {e}')
    
    conn.close()

if __name__ == "__main__":
    check_csv_tables()
