#!/usr/bin/env python3
"""
Apply Smart Merging to Non-FINAL Views
Fix the regular view_csv_json_* views that only show CSV data.
"""
import sqlite3
from config import get_database_path


def check_json_availability():
    """Check what JSON data is available for improvement"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check JSON table counts
    json_tables = [
        'json_contacts',
        'json_customer_payments', 
        'json_items',
        'json_sales_orders',
        'json_vendor_payments'
    ]
    
    print("🔍 Checking JSON data availability:")
    for table in json_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table}: {count:,} records")
        except Exception as e:
            print(f"   ❌ {table}: {e}")
    
    conn.close()


def apply_smart_merging_to_view(view_name, csv_table, json_table, key_column):
    """Apply smart merging to a specific view"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"\n🔄 Processing {view_name}...")
        
        # Get baseline count
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        old_count = cursor.fetchone()[0]
        
        # Get CSV columns
        cursor.execute(f"PRAGMA table_info({csv_table})")
        csv_columns = [row[1] for row in cursor.fetchall()]
        
        # Get JSON columns  
        cursor.execute(f"PRAGMA table_info({json_table})")
        json_columns = [row[1] for row in cursor.fetchall()]
        
        # Find common columns
        common_columns = set(csv_columns) & set(json_columns)
        csv_only = set(csv_columns) - set(json_columns)
        json_only = set(json_columns) - set(csv_columns)
        
        print(f"   📊 Schema: {len(common_columns)} common, {len(csv_only)} CSV-only, {len(json_only)} JSON-only")
        
        # Build COALESCE for common columns
        coalesce_columns = []
        for col in sorted(common_columns):
            coalesce_columns.append(f"    COALESCE(json.{col}, csv.{col}) AS {col}")
        
        # Build CSV-only columns
        csv_columns_list = []
        for col in sorted(csv_only):
            csv_columns_list.append(f"    csv.{col}")
        
        # Build JSON-only columns  
        json_columns_list = []
        for col in sorted(json_only):
            json_columns_list.append(f"    json.{col}")
        
        # Build first part of UNION (LEFT JOIN)
        all_select_items = []
        all_select_items.extend(coalesce_columns)
        all_select_items.extend(csv_columns_list)
        all_select_items.extend(json_columns_list)
        all_select_items.append(f"    CASE WHEN json.{key_column} IS NOT NULL THEN 'JSON' ELSE 'CSV' END AS data_source")
        all_select_items.append(f"    CASE WHEN json.{key_column} IS NOT NULL THEN 1 ELSE 2 END AS source_priority")
        
        # Build second part of UNION (JSON-only records)
        json_select_items = []
        for col in sorted(common_columns):
            json_select_items.append(f"    json.{col}")
        for col in sorted(csv_only):
            json_select_items.append(f"    NULL as {col}")
        for col in sorted(json_only):
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
LEFT JOIN {json_table} json ON csv.{key_column} = json.{key_column}

UNION ALL

SELECT
{',\n'.join(json_select_items)}
FROM {json_table} json
WHERE json.{key_column} NOT IN (
    SELECT DISTINCT csv.{key_column} 
    FROM {csv_table} csv 
    WHERE csv.{key_column} IS NOT NULL
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
    """Apply smart merging to all non-FINAL views that need it"""
    print("=" * 80)
    print("APPLYING SMART MERGING TO NON-FINAL VIEWS")
    print("=" * 80)
    
    check_json_availability()
    
    # Views that need smart merging (based on analysis showing CSV-only data)
    views_to_fix = [
        ("view_csv_json_contacts", "csv_contacts", "json_contacts", "contact_id"),
        ("view_csv_json_customer_payments", "csv_customer_payments", "json_customer_payments", "payment_id"),
        ("view_csv_json_items", "csv_items", "json_items", "item_id"),
        ("view_csv_json_sales_orders", "csv_sales_orders", "json_sales_orders", "salesorder_id"),
        ("view_csv_json_vendor_payments", "csv_vendor_payments", "json_vendor_payments", "payment_id")
    ]
    
    print(f"\n🎯 Target: {len(views_to_fix)} non-FINAL views")
    print("🔧 Strategy: LEFT JOIN + UNION for complete data visibility")
    print()
    
    results = {}
    total_improvement = 0
    successful_views = 0
    
    for view_name, csv_table, json_table, key_column in views_to_fix:
        result = apply_smart_merging_to_view(view_name, csv_table, json_table, key_column)
        results[view_name] = result
        
        if 'error' not in result:
            total_improvement += result['improvement']
            if result['improvement'] > 0:
                successful_views += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF NON-FINAL VIEW IMPROVEMENTS")
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
                print(f"⚪ {view_name}: No improvement (already optimal or no JSON overlap)")
    
    print(f"\n🎉 Total improvement: +{total_improvement:,} records")
    print(f"📈 Successfully improved: {successful_views}/{len(views_to_fix)} views")
    
    if successful_views > 0:
        print(f"\n🎯 Views now have comprehensive CSV+JSON visibility!")
        print(f"📋 Run analyze_all_views.py to verify improvements")


if __name__ == "__main__":
    main()
