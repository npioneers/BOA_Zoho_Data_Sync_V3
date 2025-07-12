#!/usr/bin/env python3
"""Quick script to check JSON tables in the database"""

import sqlite3
from pathlib import Path

def check_json_tables():
    db_path = Path("../data/database/production.db")
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    try:
        # Get JSON tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%' ORDER BY name")
        json_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"JSON Tables in Database: {len(json_tables)}")
        print("-" * 50)
        for table in json_tables:
            # Get column count
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            # Check for data_source column
            column_names = [col[1] for col in columns]
            has_data_source = 'data_source' in column_names
            print(f"  {table:<35} ({len(columns)} cols) [data_source: {has_data_source}]")
        
        if not json_tables:
            print("  No JSON tables found")
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_json_tables()
