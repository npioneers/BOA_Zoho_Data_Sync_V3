#!/usr/bin/env python3
"""
Discover and examine all views and tables to understand mapping patterns
"""

import sqlite3
import json

def discover_database_structure(db_path):
    """Discover all views and tables to understand the mapping structure"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== DATABASE STRUCTURE DISCOVERY ===\n")
        
        # List all tables and views
        cursor.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY type, name")
        objects = cursor.fetchall()
        
        tables = [obj for obj in objects if obj[1] == 'table']
        views = [obj for obj in objects if obj[1] == 'view']
        
        print(f"Found {len(tables)} tables and {len(views)} views\n")
        
        # Show FINAL views
        final_views = [obj for obj in objects if obj[0].startswith('FINAL_view')]
        print(f"=== FINAL VIEWS ({len(final_views)}) ===")
        for view in final_views:
            name, view_type, sql = view
            print(f"\n{name}:")
            if sql:
                # Try to make the SQL more readable
                print("  SQL Definition (first 200 chars):")
                print(f"  {sql[:200]}...")
            else:
                print("  No SQL definition found")
                
        # Look for mapping-related tables
        print(f"\n=== MAPPING-RELATED TABLES ===")
        mapping_tables = [obj for obj in objects if 'mapping' in obj[0].lower() or 'map' in obj[0].lower()]
        
        if mapping_tables:
            for table in mapping_tables:
                name, table_type, sql = table
                print(f"\n{name} ({table_type}):")
                print(f"  SQL: {sql}")
                
                # Show sample data
                try:
                    cursor.execute(f"SELECT * FROM {name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    if sample_data:
                        print(f"  Sample data: {sample_data}")
                except Exception as e:
                    print(f"  Error reading data: {e}")
        else:
            print("No explicit mapping tables found")
            
        # Look for json_db_mappings pattern in file system
        print(f"\n=== CHECKING FOR EXTERNAL MAPPING FILES ===")
        import os
        
        # Look in parent directories for mapping files
        base_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3"
        mapping_files = []
        
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if 'mapping' in file.lower() and file.endswith('.py'):
                    mapping_files.append(os.path.join(root, file))
                    
        if mapping_files:
            print("Found mapping files:")
            for file in mapping_files:
                print(f"  - {file}")
        else:
            print("No mapping files found")
            
        # Examine one working view in detail to understand structure
        print(f"\n=== DETAILED VIEW EXAMINATION ===")
        
        # Find a working view
        working_views = ['FINAL_view_csv_json_invoices', 'FINAL_view_csv_json_bills', 'FINAL_view_csv_json_purchase_orders']
        
        for view_name in working_views:
            cursor.execute("SELECT name FROM sqlite_master WHERE name = ? AND type = 'view'", (view_name,))
            if cursor.fetchone():
                print(f"\nExamining {view_name}:")
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({view_name})")
                columns = cursor.fetchall()
                print(f"  Columns ({len(columns)}): {[col[1] for col in columns[:10]]}...")
                
                # Try to get a sample row to understand data structure
                try:
                    cursor.execute(f"SELECT * FROM {view_name} LIMIT 1")
                    sample = cursor.fetchone()
                    if sample:
                        print(f"  Sample data shows {len(sample)} fields")
                        # Show first few fields with column names
                        for i, (col_info, value) in enumerate(zip(columns[:5], sample[:5])):
                            col_name = col_info[1]
                            print(f"    {col_name}: {value}")
                except Exception as e:
                    print(f"  Error getting sample: {e}")
                break
        
        conn.close()
        
    except Exception as e:
        print(f"Error discovering database structure: {e}")

if __name__ == "__main__":
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\data\database\production.db"
    discover_database_structure(db_path)
