#!/usr/bin/env python3
"""
Check for mapping tables from json_db_mapper perspective
"""
import sqlite3
import os

# Change to json_db_mapper directory perspective
os.chdir(r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\json_db_mapper")

db_path = "../data/database/production.db"
print(f"DB exists: {os.path.exists(db_path)}")
print(f"Full path: {os.path.abspath(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all mapping tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_%'")
    tables = cursor.fetchall()
    print(f"Mapping tables found: {len(tables)}")
    
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check specifically for our target modules
    target_modules = ['contacts', 'items', 'sales_orders', 'salesorders']
    
    print(f"\nTarget module mappings:")
    for module in target_modules:
        for prefix in ['map_json_', 'map_csv_']:
            table_name = f"{prefix}{module}"
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table_name} ({count} rows)")
    
    conn.close()
else:
    print("Database not found!")
