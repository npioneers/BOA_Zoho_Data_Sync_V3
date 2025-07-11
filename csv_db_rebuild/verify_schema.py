#!/usr/bin/env python3
"""
Temporary script to verify database schema after dropping organizations table
"""

import sqlite3
import os

def verify_schema():
    db_path = "data/database/production.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"\nRemaining tables ({len(tables)}):")
    for table in tables:
        table_name = table[0]
        print(f"  - {table_name}")
        
        # Get column count for each table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"    Columns: {len(columns)}")
    
    conn.close()
    print("\nSchema verification complete.")

if __name__ == "__main__":
    verify_schema()
