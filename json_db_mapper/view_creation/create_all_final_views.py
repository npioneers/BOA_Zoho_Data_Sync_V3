#!/usr/bin/env python3

import sqlite3
import yaml

def create_all_final_views():
    """Create FINAL_ prefixed views for all entities with both CSV and JSON data"""
    
    # Load config and connect
    with open('config/json_sync.yaml', 'r') as f:
        config = yaml.safe_load(f)
    conn = sqlite3.connect(config['json_sync']['database_path'])
    cursor = conn.cursor()
    
    print("=== CREATING FINAL VIEWS FOR ALL ENTITIES ===")
    
    # Get all CSV tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%'")
    csv_tables = [row[0].replace('csv_', '') for row in cursor.fetchall()]
    
    # Get all flattened JSON views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'view_flat_json_%'")
    flat_json_views = [row[0].replace('view_flat_json_', '') for row in cursor.fetchall()]
    
    # Find entities with both CSV and flattened JSON data
    entities_with_both = list(set(csv_tables) & set(flat_json_views))
    
    print(f"Found entities with both CSV and JSON data: {entities_with_both}")
    
    def create_entity_views(entity):
        """Create FINAL_ views for a specific entity"""
        print(f"\n--- Processing {entity} ---")
        
        try:
            # Get column info for the entity
            cursor.execute(f'PRAGMA table_info(csv_{entity})')
            csv_cols = [row[1] for row in cursor.fetchall()]
            
            cursor.execute(f'PRAGMA table_info(view_flat_json_{entity})')
            json_cols = [row[1] for row in cursor.fetchall()]
            
            # Find common columns and key field
            common_cols = set(csv_cols) & set(json_cols)
            key_field = f"{entity.rstrip('s')}_number"  # e.g., bill_number, invoice_number
            
            # Try alternative key patterns if standard doesn't exist
            if key_field not in common_cols:
                alt_keys = [f"{entity}_number", "number", "id", f"{entity}_id"]
                for alt_key in alt_keys:
                    if alt_key in common_cols:
                        key_field = alt_key
                        break
            
            print(f"  Key field: {key_field}")
            print(f"  Common columns: {len(common_cols)}")
            
            if key_field not in common_cols:
                print(f"  ⚠️  No suitable key field found, skipping {entity}")
                return False
            
            # Create enhanced view
            enhanced_view_name = f"FINAL_view_csv_json_{entity}"
            cursor.execute(f"DROP VIEW IF EXISTS {enhanced_view_name};")
            
            # Build COALESCE statements for common columns
            coalesce_stmts = []
            csv_only_stmts = []
            json_only_stmts = []
            
            # Handle key field first
            coalesce_stmts.append(f"COALESCE(flat.{key_field}, csv.{key_field}) AS {key_field}")
            
            # Add other common columns with COALESCE
            for col in sorted(common_cols):
                if col != key_field and col != 'data_source':  # Avoid conflicts
                    coalesce_stmts.append(f"COALESCE(flat.{col}, csv.{col}) AS {col}")
            
            # Add CSV-only columns
            for col in sorted(set(csv_cols) - set(json_cols)):
                if col != key_field:
                    csv_only_stmts.append(f"csv.{col}")
            
            # Add JSON-only columns (line items and additional fields)
            for col in sorted(set(json_cols) - set(csv_cols)):
                if not col.startswith('data_source'):  # Avoid conflicts
                    json_only_stmts.append(f"flat.{col}")
            
            # Combine all column statements
            all_columns = coalesce_stmts + csv_only_stmts + json_only_stmts
            all_columns.extend([
                f"""CASE 
                    WHEN flat.{key_field} IS NOT NULL THEN 'json_precedence'
                    ELSE 'csv_only' 
                END AS data_source""",
                f"""CASE 
                    WHEN flat.{key_field} IS NOT NULL THEN 1
                    ELSE 2 
                END AS source_priority"""
            ])
            
            enhanced_sql = f"""
            CREATE VIEW {enhanced_view_name} AS
            SELECT 
                {',\\n                '.join(all_columns)}
            FROM csv_{entity} csv
            LEFT JOIN view_flat_json_{entity} flat ON csv.{key_field} = flat.{key_field}
            WHERE COALESCE(flat.{key_field}, csv.{key_field}) IS NOT NULL
            """
            
            cursor.execute(enhanced_sql)
            
            # Test enhanced view
            cursor.execute(f"SELECT COUNT(*) FROM {enhanced_view_name}")
            enhanced_total = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {enhanced_view_name} WHERE data_source = 'json_precedence'")
            enhanced_json = cursor.fetchone()[0]
            
            enhancement_rate = (enhanced_json / enhanced_total * 100) if enhanced_total > 0 else 0
            
            print(f"  ✅ {enhanced_view_name}: {enhanced_total:,} total, {enhanced_json:,} JSON ({enhancement_rate:.1f}%)")
            
            # Create summary view
            summary_view_name = f"FINAL_view_{entity}_summary"
            cursor.execute(f"DROP VIEW IF EXISTS {summary_view_name};")
            
            # Get main entity fields (exclude line item fields for summary)
            main_fields = []
            for col in coalesce_stmts + csv_only_stmts:
                if 'line_item' not in col.lower():
                    main_fields.append(col.split(' AS ')[-1] if ' AS ' in col else col.replace('csv.', '').replace('flat.', ''))
            
            # Add data_source and source_priority
            main_fields.extend(['data_source', 'source_priority'])
            
            summary_sql = f"""
            CREATE VIEW {summary_view_name} AS
            SELECT 
                {', '.join(main_fields)},
                COUNT(CASE WHEN flat.{key_field} IS NOT NULL THEN 1 END) as line_item_count
            FROM {enhanced_view_name}
            WHERE {key_field} IS NOT NULL
            GROUP BY {', '.join(main_fields)}
            HAVING MIN(source_priority) = source_priority
            """
            
            cursor.execute(summary_sql)
            
            # Test summary view
            cursor.execute(f"SELECT COUNT(*) FROM {summary_view_name}")
            summary_total = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {summary_view_name} WHERE data_source = 'json_precedence'")
            summary_json = cursor.fetchone()[0]
            
            # Calculate reduction ratio
            reduction_ratio = enhanced_total / summary_total if summary_total > 0 else 0
            
            print(f"  ✅ {summary_view_name}: {summary_total:,} unique, {summary_json:,} JSON ({reduction_ratio:.0f}:1 reduction)")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error processing {entity}: {e}")
            return False
    
    # Process entities (skip bills and invoices as they're already done)
    processed_entities = ['bills', 'invoices']  # Already created
    success_count = 2  # Start with existing bills and invoices
    
    for entity in entities_with_both:
        if entity not in processed_entities:
            if create_entity_views(entity):
                success_count += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"✅ Successfully created FINAL_ views for {success_count}/{len(entities_with_both)} entities")
    print(f"📊 View types created for each entity:")
    print(f"   • FINAL_view_csv_json_{entity} - Enhanced with line items")
    print(f"   • FINAL_view_{entity}_summary - Deduplicated for reporting")
    print(f"🎯 All views use JSON precedence for duplicate resolution")
    print(f"📋 Easy identification with FINAL_ prefix")
    
    # List all FINAL_ views
    print(f"\n=== ALL FINAL VIEWS ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'FINAL_%' ORDER BY name")
    final_views = [row[0] for row in cursor.fetchall()]
    
    for view in final_views:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {view}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {view}: {count:,} records")
        except Exception as e:
            print(f"  ❌ {view}: {e}")
    
    conn.commit()
    conn.close()
    
    return success_count

if __name__ == "__main__":
    create_all_final_views()
