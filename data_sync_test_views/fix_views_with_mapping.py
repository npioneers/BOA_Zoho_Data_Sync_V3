#!/usr/bin/env python3
"""
Fix Views with Proper Column Mapping
Use the correct key column mappings between CSV and JSON tables.
"""
import sqlite3
from config import get_database_path


def apply_smart_merging_with_mapping(view_name, csv_table, json_table, csv_key, json_key):
    """Apply smart merging with different key column names"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"\n🔄 Processing {view_name}...")
        print(f"   🔗 Key mapping: CSV.{csv_key} ↔ JSON.{json_key}")
        
        # Get baseline count
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        old_count = cursor.fetchone()[0]
        
        # Get CSV columns
        cursor.execute(f"PRAGMA table_info({csv_table})")
        csv_columns = [row[1] for row in cursor.fetchall()]
        
        # Get JSON columns  
        cursor.execute(f"PRAGMA table_info({json_table})")
        json_columns = [row[1] for row in cursor.fetchall()]
        
        # Find common columns (excluding key columns which might have different names)
        csv_non_key = set(csv_columns) - {csv_key}
        json_non_key = set(json_columns) - {json_key}
        common_columns = csv_non_key & json_non_key
        csv_only = csv_non_key - json_non_key
        json_only = json_non_key - common_columns
        
        print(f"   📊 Schema: {len(common_columns)} common, {len(csv_only)} CSV-only, {len(json_only)} JSON-only")
        
        # Build COALESCE for common columns
        coalesce_columns = []
        for col in sorted(common_columns):
            coalesce_columns.append(f"    COALESCE(json.{col}, csv.{col}) AS {col}")
        
        # Handle key columns specially
        coalesce_columns.append(f"    COALESCE(json.{json_key}, csv.{csv_key}) AS {csv_key}")
        
        # Build CSV-only columns
        csv_columns_list = []
        for col in sorted(csv_only):
            csv_columns_list.append(f"    csv.{col}")
        
        # Build JSON-only columns  
        json_columns_list = []
        for col in sorted(json_only):
            if col != json_key:  # Don't duplicate the key
                json_columns_list.append(f"    json.{col}")
        
        # Build first part of UNION (LEFT JOIN)
        all_select_items = []
        all_select_items.extend(coalesce_columns)
        all_select_items.extend(csv_columns_list)
        all_select_items.extend(json_columns_list)
        all_select_items.append(f"    CASE WHEN json.{json_key} IS NOT NULL THEN 'JSON' ELSE 'CSV' END AS data_source")
        all_select_items.append(f"    CASE WHEN json.{json_key} IS NOT NULL THEN 1 ELSE 2 END AS source_priority")
        
        # Build second part of UNION (JSON-only records)
        json_select_items = []
        for col in sorted(common_columns):
            json_select_items.append(f"    json.{col}")
        json_select_items.append(f"    json.{json_key} AS {csv_key}")  # Map JSON key to CSV key name
        for col in sorted(csv_only):
            json_select_items.append(f"    NULL as {col}")
        for col in sorted(json_only):
            if col != json_key:  # Don't duplicate the key
                json_select_items.append(f"    json.{col}")
        json_select_items.append("    'JSON' AS data_source")
        json_select_items.append("    1 AS source_priority")
        
        # Generate SQL
        sql = f"""
DROP VIEW IF EXISTS {view_name};

CREATE VIEW {view_name} AS
SELECT
{',\n'.join(all_select_items)}
FROM {csv_table} csv
LEFT JOIN {json_table} json ON csv.{csv_key} = json.{json_key}

UNION ALL

SELECT
{',\n'.join(json_select_items)}
FROM {json_table} json
WHERE json.{json_key} NOT IN (
    SELECT DISTINCT csv.{csv_key} 
    FROM {csv_table} csv 
    WHERE csv.{csv_key} IS NOT NULL
);
"""
        
        # Apply SQL
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        # Test the results
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        new_count = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT data_source, COUNT(*) 
            FROM {view_name} 
            GROUP BY data_source ORDER BY data_source
        """)
        distribution = dict(cursor.fetchall())
        
        conn.commit()
        
        improvement = new_count - old_count
        json_records = distribution.get('JSON', 0)
        csv_records = distribution.get('CSV', 0)
        
        print(f"   ✅ {view_name}: {old_count:,} → {new_count:,} (+{improvement:,})")
        print(f"   📊 Distribution: CSV={csv_records:,}, JSON={json_records:,}")
        
        if improvement > 0:
            percentage = (improvement / old_count * 100) if old_count > 0 else 0
            print(f"   🎉 Improvement: {percentage:.1f}% more data visible!")
        
        return {
            'old_count': old_count,
            'new_count': new_count,
            'improvement': improvement,
            'json_records': json_records,
            'csv_records': csv_records
        }
        
    except Exception as e:
        print(f"   ❌ Error with {view_name}: {e}")
        return {'error': str(e)}
    finally:
        conn.close()


def main():
    """Fix views with proper column mapping"""
    print("=" * 80)
    print("FIXING VIEWS WITH PROPER KEY COLUMN MAPPING")
    print("=" * 80)
    
    # Correct mappings between CSV and JSON key columns
    views_to_fix = [
        ("view_csv_json_customer_payments", "csv_customer_payments", "json_customer_payments", "customer_payment_id", "payment_id"),
        ("view_csv_json_sales_orders", "csv_sales_orders", "json_sales_orders", "sales_order_id", "salesorder_id"),
        ("view_csv_json_vendor_payments", "csv_vendor_payments", "json_vendor_payments", "vendor_payment_id", "payment_id")
    ]
    
    print(f"🎯 Target: {len(views_to_fix)} views with key mapping")
    print("🔧 Strategy: LEFT JOIN + UNION with proper key column mapping")
    print()
    
    results = {}
    total_improvement = 0
    successful_views = 0
    
    for view_name, csv_table, json_table, csv_key, json_key in views_to_fix:
        result = apply_smart_merging_with_mapping(view_name, csv_table, json_table, csv_key, json_key)
        results[view_name] = result
        
        if 'error' not in result:
            total_improvement += result['improvement']
            if result['improvement'] > 0:
                successful_views += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY - KEY MAPPING IMPROVEMENTS")
    print("=" * 80)
    
    for view_name, result in results.items():
        if 'error' in result:
            print(f"❌ {view_name}: {result['error']}")
        else:
            improvement = result['improvement']
            if improvement > 0:
                percentage = (improvement / result['old_count'] * 100) if result['old_count'] > 0 else 0
                print(f"✅ {view_name}: +{improvement:,} records ({percentage:.1f}% improvement)")
            else:
                print(f"⚪ {view_name}: No improvement (no overlapping data)")
    
    print(f"\n🎉 Additional improvement: +{total_improvement:,} records")
    print(f"📈 Successfully improved: {successful_views}/{len(views_to_fix)} views")
    
    if total_improvement > 0:
        print(f"\n🎯 All views now have comprehensive CSV+JSON visibility!")


if __name__ == "__main__":
    main()
