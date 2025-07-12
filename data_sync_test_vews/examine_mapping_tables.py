#!/usr/bin/env python3
"""
Examine mapping tables (map_json*) in production.db to understand 
how to properly create UNION operations for empty views.
"""

import sqlite3
import os

def examine_mapping_tables():
    """Examine all map_json* tables to understand the mapping structure."""
    
    # Try multiple database paths to find mapping tables
    db_paths = [
        r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db",
        r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\backups\production_backup_2025-07-07_19-44-17.db",
        r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\output\database\production.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            print(f"📁 Using database: {path}")
            break
    
    if not db_path:
        print(f"❌ No database found in any of the expected locations")
        return
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 EXAMINING MAPPING TABLES IN PRODUCTION DATABASE")
        print("=" * 60)
        
        # Get all tables starting with map_json
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'map_json%'
            ORDER BY name
        """)
        
        mapping_tables = cursor.fetchall()
        
        if not mapping_tables:
            print("❌ No map_json* tables found!")
            
            # Let's see what tables do exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
            all_tables = cursor.fetchall()
            print(f"\n📋 All tables in database ({len(all_tables)}):")
            for table in all_tables:
                print(f"  - {table[0]}")
            
            conn.close()
            return
        
        print(f"📋 Found {len(mapping_tables)} mapping tables:")
        for table in mapping_tables:
            print(f"  - {table[0]}")
        
        # Examine each mapping table in detail
        for table_name in [t[0] for t in mapping_tables]:
            print(f"\n🔍 EXAMINING: {table_name}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"📊 Columns ({len(columns)}):")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get sample data
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"📈 Total rows: {row_count}")
            
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_rows = cursor.fetchall()
                
                print(f"📝 Sample data:")
                column_names = [col[1] for col in columns]
                print(f"   {' | '.join(column_names)}")
                print(f"   {'-' * (len(' | '.join(column_names)))}")
                
                for row in sample_rows:
                    row_str = ' | '.join([str(val) if val is not None else 'NULL' for val in row])
                    if len(row_str) > 100:
                        row_str = row_str[:97] + "..."
                    print(f"   {row_str}")
        
        # Now let's specifically look for contacts, items, and sales_orders mappings
        print(f"\n🎯 FOCUSING ON EMPTY VIEWS MAPPINGS")
        print("=" * 50)
        
        target_modules = ['contacts', 'items', 'sales_orders', 'salesorders']
        
        for module in target_modules:
            table_name = f"map_json_{module}"
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name = ?
            """, (table_name,))
            
            if cursor.fetchone():
                print(f"\n✅ Found mapping table: {table_name}")
                
                # Get detailed mapping information
                cursor.execute(f"SELECT * FROM {table_name}")
                mappings = cursor.fetchall()
                
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                print(f"📋 Column mappings for {module}:")
                for mapping in mappings:
                    mapping_dict = dict(zip(column_names, mapping))
                    csv_col = mapping_dict.get('csv_column', 'N/A')
                    json_col = mapping_dict.get('json_column', 'N/A')
                    final_col = mapping_dict.get('final_column', 'N/A')
                    print(f"  CSV: {csv_col} -> JSON: {json_col} -> FINAL: {final_col}")
            else:
                print(f"❌ No mapping table found: {table_name}")
        
        conn.close()
        print(f"\n✅ Mapping table examination complete!")
        
    except Exception as e:
        print(f"❌ Error examining mapping tables: {e}")

if __name__ == "__main__":
    examine_mapping_tables()
