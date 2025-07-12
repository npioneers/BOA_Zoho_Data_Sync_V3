#!/usr/bin/env python3
"""
Examine mapping tables to understand how to create proper UNION statements
for the empty views (contacts, items, sales_orders).
"""
import sqlite3
import os

def examine_mapping_structure():
    """Examine the mapping tables structure for our target modules."""
    
    # Change to json_db_mapper directory perspective
    os.chdir(r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\json_db_mapper")
    db_path = "../data/database/production.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 EXAMINING MAPPING TABLE STRUCTURE")
    print("=" * 60)
    
    target_modules = ['contacts', 'items', 'sales_orders']
    
    for module in target_modules:
        print(f"\n📋 MODULE: {module.upper()}")
        print("-" * 40)
        
        # Check CSV mapping
        csv_table = f"map_csv_{module}"
        json_table = f"map_json_{module}"
        
        for table_name, table_type in [(csv_table, "CSV"), (json_table, "JSON")]:
            print(f"\n🔍 {table_type} Mapping Table: {table_name}")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"📊 Schema:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get sample mappings
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
            mappings = cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            
            print(f"📝 Sample mappings:")
            for mapping in mappings[:5]:  # Show first 5
                mapping_dict = dict(zip(column_names, mapping))
                
                # Extract key columns
                source_col = mapping_dict.get('csv_column' if table_type == 'CSV' else 'json_column', 'N/A')
                final_col = mapping_dict.get('final_column', 'N/A')
                data_type = mapping_dict.get('data_type', 'N/A')
                
                print(f"    {source_col} -> {final_col} ({data_type})")
    
    print(f"\n🎯 CREATING UNION QUERY TEMPLATES")
    print("=" * 50)
    
    # Now create proper UNION templates based on mappings
    for module in target_modules:
        print(f"\n📝 {module.upper()} UNION Template:")
        
        # Get CSV mappings
        cursor.execute(f"""
            SELECT csv_column, final_column, data_type 
            FROM map_csv_{module} 
            ORDER BY final_column
        """)
        csv_mappings = cursor.fetchall()
        
        # Get JSON mappings
        cursor.execute(f"""
            SELECT json_column, final_column, data_type 
            FROM map_json_{module} 
            ORDER BY final_column
        """)
        json_mappings = cursor.fetchall()
        
        # Create mapping dictionaries
        csv_map = {final_col: csv_col for csv_col, final_col, _ in csv_mappings}
        json_map = {final_col: json_col for json_col, final_col, _ in json_mappings}
        
        # Get all final columns
        all_final_cols = set(csv_map.keys()) | set(json_map.keys())
        all_final_cols = sorted(all_final_cols)
        
        print(f"CREATE VIEW FINAL_view_csv_json_{module} AS")
        print(f"SELECT")
        
        # CSV part
        csv_selects = []
        for final_col in all_final_cols:
            csv_col = csv_map.get(final_col, 'NULL')
            if csv_col and csv_col != 'NULL':
                csv_selects.append(f"    csv.{csv_col} AS {final_col}")
            else:
                csv_selects.append(f"    NULL AS {final_col}")
        
        csv_selects.append("    'CSV' AS data_source")
        csv_selects.append("    1 AS source_priority")
        
        print(",\n".join(csv_selects))
        print(f"FROM csv_{module} csv")
        
        # Determine appropriate WHERE clause
        if module == 'contacts':
            print("WHERE csv.display_name IS NOT NULL OR csv.company_name IS NOT NULL")
        elif module == 'items':
            print("WHERE csv.item_name IS NOT NULL OR csv.sku IS NOT NULL")
        elif module == 'sales_orders':
            print("WHERE csv.sales_order_number IS NOT NULL OR csv.salesorder_id IS NOT NULL")
        
        print("UNION ALL")
        print("SELECT")
        
        # JSON part
        json_selects = []
        for final_col in all_final_cols:
            json_col = json_map.get(final_col, 'NULL')
            if json_col and json_col != 'NULL':
                json_selects.append(f"    json.{json_col} AS {final_col}")
            else:
                json_selects.append(f"    NULL AS {final_col}")
        
        json_selects.append("    'JSON' AS data_source")
        json_selects.append("    2 AS source_priority")
        
        print(",\n".join(json_selects))
        print(f"FROM json_{module} json")
        
        # Determine appropriate WHERE clause for JSON
        if module == 'contacts':
            print("WHERE json.display_name IS NOT NULL OR json.company_name IS NOT NULL;")
        elif module == 'items':
            print("WHERE json.name IS NOT NULL OR json.sku IS NOT NULL;")
        elif module == 'sales_orders':
            print("WHERE json.salesorder_number IS NOT NULL OR json.salesorder_id IS NOT NULL;")
        
        print()
    
    conn.close()

if __name__ == "__main__":
    examine_mapping_structure()
