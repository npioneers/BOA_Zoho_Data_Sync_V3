#!/usr/bin/env python3
"""
Check multiple database files for mapping tables (map_json*).
"""

import sqlite3
import os

def check_database_for_mappings(db_path, db_name):
    """Check a specific database for mapping tables."""
    
    if not os.path.exists(db_path):
        print(f"❌ {db_name}: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n🔍 CHECKING: {db_name}")
        print(f"📍 Path: {db_path}")
        print("-" * 60)
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)
        all_tables = cursor.fetchall()
        
        print(f"📋 Total tables: {len(all_tables)}")
        
        # Look for mapping tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'map_%'
            ORDER BY name
        """)
        mapping_tables = cursor.fetchall()
        
        if mapping_tables:
            print(f"✅ Found {len(mapping_tables)} mapping tables:")
            for table in mapping_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]} ({count} rows)")
            
            conn.close()
            return True
        else:
            # Show some table names to understand structure
            table_names = [t[0] for t in all_tables[:10]]
            if table_names:
                print(f"📝 Sample tables: {', '.join(table_names)}")
            else:
                print("❌ No tables found")
            
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error checking {db_name}: {e}")
        return False

def main():
    """Check multiple databases for mapping tables."""
    
    databases_to_check = [
        (r"C:\Users\User\Documents\Projects\Automated_Operations\data\database\production.db", "Current Production"),
        (r"C:\Users\User\Documents\Projects\Automated_Operations\data\database\production_1751737137.db", "Backup Production"),
        (r"C:\Users\User\Documents\Projects\Automated_Operations\data_sync_app\zoho_books_data.db", "Main App Database"),
    ]
    
    print("🔍 SEARCHING FOR MAPPING TABLES ACROSS DATABASES")
    print("=" * 70)
    
    found_mappings = False
    
    for db_path, db_name in databases_to_check:
        if check_database_for_mappings(db_path, db_name):
            found_mappings = True
            
            # If we found mappings, examine them in detail
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            print(f"\n🎯 DETAILED MAPPING ANALYSIS FOR: {db_name}")
            print("=" * 50)
            
            # Get mapping tables for our target modules
            target_modules = ['contacts', 'items', 'sales_orders', 'salesorders']
            
            for module in target_modules:
                for prefix in ['map_json_', 'map_csv_']:
                    table_name = f"{prefix}{module}"
                    
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name = ?
                    """, (table_name,))
                    
                    if cursor.fetchone():
                        print(f"\n✅ Found: {table_name}")
                        
                        # Get schema
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = cursor.fetchall()
                        column_names = [col[1] for col in columns]
                        
                        # Get all mappings
                        cursor.execute(f"SELECT * FROM {table_name}")
                        mappings = cursor.fetchall()
                        
                        print(f"📋 Mappings ({len(mappings)} rows):")
                        print(f"   Columns: {', '.join(column_names)}")
                        
                        for mapping in mappings[:10]:  # Show first 10
                            mapping_dict = dict(zip(column_names, mapping))
                            print(f"   {mapping_dict}")
            
            conn.close()
            break  # Stop after finding the first database with mappings
    
    if not found_mappings:
        print(f"\n❌ No mapping tables found in any database!")
        print("💡 Mapping tables might be created dynamically or stored elsewhere.")

if __name__ == "__main__":
    main()
