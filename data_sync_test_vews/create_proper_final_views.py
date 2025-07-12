#!/usr/bin/env python3
"""
Create proper FINAL views using mapping table information
"""

import sqlite3
import sys
import os

def get_mapped_columns(cursor, entity):
    """Get the column mappings for CSV and JSON tables for a given entity"""
    
    # Check for CSV mapping table (might be different naming pattern)
    csv_patterns = [f'map_csv_{entity}', f'csv_{entity}_map', f'mapping_csv_{entity}']
    json_patterns = [f'map_json_{entity}', f'json_{entity}_map', f'mapping_json_{entity}']
    
    csv_mapping = None
    json_mapping = None
    
    # Try to find CSV mapping
    for pattern in csv_patterns:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{pattern}'")
        if cursor.fetchone():
            cursor.execute(f"SELECT field_name, field_type FROM {pattern} ORDER BY field_position")
            csv_mapping = cursor.fetchall()
            print(f"✅ Found CSV mapping table: {pattern}")
            break
    
    # Try to find JSON mapping  
    for pattern in json_patterns:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{pattern}'")
        if cursor.fetchone():
            cursor.execute(f"SELECT field_name, field_type FROM {pattern} ORDER BY field_position")
            json_mapping = cursor.fetchall()
            print(f"✅ Found JSON mapping table: {pattern}")
            break
    
    return csv_mapping, json_mapping

def examine_working_view(cursor, view_name):
    """Examine a working FINAL view to understand the pattern"""
    print(f"\n🔍 EXAMINING WORKING VIEW: {view_name}")
    print("-" * 50)
    
    # Get view definition
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{view_name}' AND type='view'")
    view_sql = cursor.fetchone()
    
    if view_sql:
        sql_text = view_sql[0]
        print("View SQL:")
        print(sql_text[:1000] + "..." if len(sql_text) > 1000 else sql_text)
        return sql_text
    return None

def create_proper_final_views():
    """Create properly mapped FINAL views for the empty entities"""
    
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 CREATING PROPER FINAL VIEWS")
        print("=" * 50)
        
        # First, examine a working view to understand the pattern
        working_views = ['FINAL_view_csv_json_invoices', 'FINAL_view_csv_json_bills']
        sample_sql = None
        
        for view in working_views:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE name='{view}' AND type='view'")
            if cursor.fetchone():
                sample_sql = examine_working_view(cursor, view)
                if sample_sql:
                    break
        
        if not sample_sql:
            print("❌ Could not find any working FINAL views to examine")
            return
        
        # Now work on the three problematic entities
        entities = ['contacts', 'items', 'sales_orders']
        
        for entity in entities:
            print(f"\n📋 PROCESSING {entity.upper()}")
            print("-" * 40)
            
            # Get mapping information
            csv_mapping, json_mapping = get_mapped_columns(cursor, entity)
            
            if not csv_mapping and not json_mapping:
                print(f"❌ No mapping tables found for {entity}")
                continue
            
            # Check if source tables exist
            cursor.execute(f"SELECT name FROM sqlite_master WHERE name='csv_{entity}' AND type='table'")
            csv_exists = cursor.fetchone() is not None
            
            cursor.execute(f"SELECT name FROM sqlite_master WHERE name='json_{entity}' AND type='table'")
            json_exists = cursor.fetchone() is not None
            
            print(f"📊 Source tables: CSV={csv_exists}, JSON={json_exists}")
            
            if not csv_exists and not json_exists:
                print(f"❌ No source tables found for {entity}")
                continue
            
            # Get common columns that exist in both sources (if both exist)
            common_columns = []
            csv_only_columns = []
            json_only_columns = []
            
            if csv_mapping and json_mapping:
                csv_fields = {field[0]: field[1] for field in csv_mapping}
                json_fields = {field[0]: field[1] for field in json_mapping}
                
                # Find common fields
                for field_name in csv_fields:
                    if field_name in json_fields:
                        common_columns.append((field_name, csv_fields[field_name]))
                    else:
                        csv_only_columns.append((field_name, csv_fields[field_name]))
                
                for field_name in json_fields:
                    if field_name not in csv_fields:
                        json_only_columns.append((field_name, json_fields[field_name]))
            
            elif csv_mapping:
                csv_only_columns = csv_mapping
            elif json_mapping:
                json_only_columns = json_mapping
            
            print(f"📈 Column analysis:")
            print(f"  - Common: {len(common_columns)}")
            print(f"  - CSV only: {len(csv_only_columns)}")
            print(f"  - JSON only: {len(json_only_columns)}")
            
            # Show first few fields of each type
            if common_columns[:5]:
                print(f"  - Common fields (first 5): {[c[0] for c in common_columns[:5]]}")
            if csv_only_columns[:5]:
                print(f"  - CSV fields (first 5): {[c[0] for c in csv_only_columns[:5]]}")
            if json_only_columns[:5]:
                print(f"  - JSON fields (first 5): {[c[0] for c in json_only_columns[:5]]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_proper_final_views()
