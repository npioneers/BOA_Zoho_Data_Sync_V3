#!/usr/bin/env python3
"""
Find and analyze mapping tables (map_json*) in the production database
"""

import sqlite3
import sys
import os

def find_mapping_tables():
    """Find all map_json* tables in the production database"""
    
    # Database path
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\data\database\production.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    # Connect to production database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all table names that start with map_json
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_json%' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} mapping tables:")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            print(f"   Columns ({len(col_names)}): {col_names}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Rows: {count}")
            
            # Show sample data if any exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample = cursor.fetchall()
                print(f"   Sample data:")
                for i, row in enumerate(sample, 1):
                    print(f"     Row {i}: {row}")
            
            print("-" * 40)
            
        if not tables:
            print("No mapping tables found starting with 'map_json'")
            
            # Let's see what tables do exist
            print("\nLet's check what tables exist in the database:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            all_tables = cursor.fetchall()
            
            print(f"\nAll tables in database ({len(all_tables)}):")
            for table in all_tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name} ({count} rows)")
                
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    find_mapping_tables()
