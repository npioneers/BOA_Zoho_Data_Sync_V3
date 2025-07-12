#!/usr/bin/env python3
"""
Apply Smart Merging to All CSV-Only Views
Uses the proven UNION approach to fix all 5 CSV-only views.
"""
import sqlite3
from datetime import datetime
from config import get_database_path


def generate_smart_view_sql(view_name, csv_table, json_table, key_column):
    """Generate UNION-based smart merging SQL for any view"""
    
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
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
        
        print(f"📊 {view_name}: {len(common_columns)} common, {len(csv_only)} CSV-only, {len(json_only)} JSON-only")
        
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
        all_select_items.append("    CASE WHEN json.{} IS NOT NULL THEN 'JSON' ELSE 'CSV' END AS data_source".format(key_column))
        all_select_items.append("    CASE WHEN json.{} IS NOT NULL THEN 1 ELSE 2 END AS source_priority".format(key_column))
        
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
        
        conn.close()
        return sql
        
    except Exception as e:
        conn.close()
        print(f"❌ Error generating SQL for {view_name}: {e}")
        return None


def apply_all_smart_views():
    """Apply smart merging to all CSV-only views"""
    
    # Configuration for all views that need fixing
    views_to_fix = [
        ("FINAL_view_csv_json_contacts", "csv_contacts", "json_contacts", "contact_id"),
        ("FINAL_view_csv_json_customer_payments", "csv_customer_payments", "json_customer_payments", "payment_id"),
        ("FINAL_view_csv_json_sales_orders", "csv_sales_orders", "json_sales_orders", "salesorder_id"),
        ("FINAL_view_csv_json_vendor_payments", "csv_vendor_payments", "json_vendor_payments", "payment_id")
    ]
    
    db_path = get_database_path()
    results = {}
    
    for view_name, csv_table, json_table, key_column in views_to_fix:
        print(f"\n🔄 Processing {view_name}...")
        
        try:
            # Generate SQL
            sql = generate_smart_view_sql(view_name, csv_table, json_table, key_column)
            if not sql:
                continue
                
            # Apply SQL
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get baseline count
            cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
            old_count = cursor.fetchone()[0]
            
            # Execute the SQL
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
            conn.close()
            
            improvement = new_count - old_count
            json_records = distribution.get('JSON', 0)
            csv_records = distribution.get('CSV', 0)
            
            results[view_name] = {
                'old_count': old_count,
                'new_count': new_count,
                'improvement': improvement,
                'json_records': json_records,
                'csv_records': csv_records
            }
            
            print(f"✅ {view_name}: {old_count:,} → {new_count:,} (+{improvement:,})")
            print(f"📊 Distribution: CSV={csv_records:,}, JSON={json_records:,}")
            
        except Exception as e:
            print(f"❌ Error with {view_name}: {e}")
            results[view_name] = {'error': str(e)}
    
    return results


def main():
    """Apply smart merging to all views"""
    print("=" * 80)
    print("APPLYING SMART MERGING TO ALL CSV-ONLY VIEWS")
    print("=" * 80)
    
    print("🎯 Target: 4 remaining CSV-only views")
    print("🔧 Strategy: LEFT JOIN + UNION for complete data visibility")
    print("📊 Expected total improvement: +498 JSON records")
    print()
    
    results = apply_all_smart_views()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF ALL IMPROVEMENTS")
    print("=" * 80)
    
    total_improvement = 0
    successful_views = 0
    
    for view_name, result in results.items():
        if 'error' in result:
            print(f"❌ {view_name}: {result['error']}")
        else:
            improvement = result['improvement']
            total_improvement += improvement
            successful_views += 1
            
            percentage = (improvement / result['old_count'] * 100) if result['old_count'] > 0 else 0
            print(f"✅ {view_name}: +{improvement:,} records ({percentage:.1f}% improvement)")
    
    print(f"\n🎉 Total improvement: +{total_improvement:,} records")
    print(f"📈 Successfully updated: {successful_views}/4 views")
    
    if successful_views == 4:
        print(f"\n🎯 Next step: Run analyze_final_views_strategies.py to verify all views now use consistent smart merging")


if __name__ == "__main__":
    main()
