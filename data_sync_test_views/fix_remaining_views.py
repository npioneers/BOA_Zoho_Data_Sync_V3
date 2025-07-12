#!/usr/bin/env python3
"""
Fix the Remaining Non-FINAL Views with Correct Column Names
"""
import sqlite3
from config import get_database_path


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
    """Fix the remaining views with correct column names"""
    print("=" * 80)
    print("FIXING REMAINING NON-FINAL VIEWS WITH CORRECT COLUMN NAMES")
    print("=" * 80)
    
    # Corrected views with proper key column names  
    views_to_fix = [
        ("view_csv_json_customer_payments", "csv_customer_payments", "json_customer_payments", "customer_payment_id"),
        ("view_csv_json_sales_orders", "csv_sales_orders", "json_sales_orders", "sales_order_id"),
        ("view_csv_json_vendor_payments", "csv_vendor_payments", "json_vendor_payments", "vendor_payment_id")
    ]
    
    print(f"🎯 Target: {len(views_to_fix)} remaining views")
    print("🔧 Strategy: LEFT JOIN + UNION with correct key columns")
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
    print("FINAL SUMMARY - REMAINING VIEW IMPROVEMENTS")
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
                print(f"⚪ {view_name}: No improvement (no JSON overlap)")
    
    print(f"\n🎉 Additional improvement: +{total_improvement:,} records")
    print(f"📈 Successfully improved: {successful_views}/{len(views_to_fix)} views")
    
    if total_improvement > 0:
        print(f"\n🎯 All views now have comprehensive CSV+JSON visibility!")
        print(f"📋 Run analyze_all_views.py to verify final state")


if __name__ == "__main__":
    main()
