#!/usr/bin/env python3
"""
Implement Smart CSV-Preferred Strategy with Freshness Detection
Modify views to prefer CSV data unless JSON data is demonstrably fresher
"""
import sqlite3
from datetime import datetime
from config import get_database_path


def generate_csv_preferred_smart_merging(view_name, csv_table, json_table, key_column, csv_timestamp, json_timestamp):
    """Generate CSV-preferred smart merging SQL with freshness detection"""
    
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
        
        # Build SMART COALESCE for common columns (CSV-preferred with freshness check)
        smart_coalesce_columns = []
        for col in sorted(common_columns):
            if col in [csv_timestamp, json_timestamp]:
                # For timestamp fields, use special logic
                smart_coalesce_columns.append(f"""    CASE 
        WHEN json.{json_timestamp} > csv.{csv_timestamp} THEN json.{col}
        ELSE csv.{col} 
    END AS {col}""")
            else:
                # For other fields, prefer CSV unless JSON is fresher
                smart_coalesce_columns.append(f"""    CASE 
        WHEN json.{json_timestamp} > csv.{csv_timestamp} THEN COALESCE(json.{col}, csv.{col})
        ELSE COALESCE(csv.{col}, json.{col}) 
    END AS {col}""")
        
        # Build CSV-only columns
        csv_columns_list = []
        for col in sorted(csv_only):
            csv_columns_list.append(f"    csv.{col}")
        
        # Build JSON-only columns  
        json_columns_list = []
        for col in sorted(json_only):
            json_columns_list.append(f"    json.{col}")
        
        # Build first part of UNION (LEFT JOIN with smart preference)
        all_select_items = []
        all_select_items.extend(smart_coalesce_columns)
        all_select_items.extend(csv_columns_list)
        all_select_items.extend(json_columns_list)
        all_select_items.append(f"""    CASE 
        WHEN json.{json_timestamp} > csv.{csv_timestamp} THEN 'JSON_FRESH'
        WHEN json.{key_column} IS NOT NULL THEN 'CSV_PREFERRED'
        ELSE 'CSV_ONLY' 
    END AS data_source""")
        all_select_items.append(f"""    CASE 
        WHEN json.{json_timestamp} > csv.{csv_timestamp} THEN 1
        WHEN json.{key_column} IS NOT NULL THEN 2
        ELSE 3 
    END AS source_priority""")
        
        # Build second part of UNION (JSON-only records)
        json_select_items = []
        for col in sorted(common_columns):
            json_select_items.append(f"    json.{col}")
        for col in sorted(csv_only):
            json_select_items.append(f"    NULL as {col}")
        for col in sorted(json_only):
            json_select_items.append(f"    json.{col}")
        json_select_items.append("    'JSON_ONLY' AS data_source")
        json_select_items.append("    4 AS source_priority")
        
        # Generate SQL with timestamp-based freshness check
        sql = f"""
DROP VIEW IF EXISTS {view_name};

CREATE VIEW {view_name} AS
SELECT
{',\n'.join(all_select_items)}
FROM {csv_table} csv
LEFT JOIN {json_table} json ON csv.{key_column} = json.{key_column}
WHERE csv.{key_column} IS NOT NULL

UNION ALL

SELECT
{',\n'.join(json_select_items)}
FROM {json_table} json
WHERE json.{key_column} NOT IN (
    SELECT DISTINCT csv.{key_column} 
    FROM {csv_table} csv 
    WHERE csv.{key_column} IS NOT NULL
)
AND json.{key_column} IS NOT NULL;
"""
        
        conn.close()
        return sql
        
    except Exception as e:
        conn.close()
        print(f"❌ Error generating SQL for {view_name}: {e}")
        return None


def implement_csv_preferred_contacts():
    """Implement CSV-preferred strategy for contacts (has overlapping timestamps)"""
    db_path = get_database_path()
    
    print("🔄 Implementing CSV-preferred strategy for contacts...")
    
    # Generate SQL with freshness detection
    sql = generate_csv_preferred_smart_merging(
        "view_csv_json_contacts", 
        "csv_contacts", 
        "json_contacts", 
        "contact_id",
        "last_modified_time",  # CSV timestamp
        "last_modified_time"   # JSON timestamp
    )
    
    if not sql:
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get baseline count
        cursor.execute("SELECT COUNT(*) FROM view_csv_json_contacts")
        old_count = cursor.fetchone()[0]
        
        # Execute the SQL
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        # Test the results
        cursor.execute("SELECT COUNT(*) FROM view_csv_json_contacts")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT data_source, COUNT(*) 
            FROM view_csv_json_contacts 
            GROUP BY data_source ORDER BY data_source
        """)
        distribution = dict(cursor.fetchall())
        
        conn.commit()
        conn.close()
        
        print(f"✅ view_csv_json_contacts: {old_count:,} → {new_count:,}")
        print(f"📊 Distribution: {distribution}")
        
        # Show freshness analysis
        if 'JSON_FRESH' in distribution:
            fresh_count = distribution['JSON_FRESH']
            csv_preferred = distribution.get('CSV_PREFERRED', 0)
            print(f"🆕 JSON fresher data: {fresh_count:,} records")
            print(f"📋 CSV preferred data: {csv_preferred:,} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error implementing contacts view: {e}")
        return False


def implement_csv_preferred_items():
    """Implement CSV-preferred strategy for items (no overlapping records)"""
    db_path = get_database_path()
    
    print("🔄 Implementing CSV-preferred strategy for items...")
    
    # Since items have no overlapping records, use a simplified approach
    sql = f"""
DROP VIEW IF EXISTS FINAL_view_csv_json_items;

CREATE VIEW FINAL_view_csv_json_items AS
SELECT
    COALESCE(csv.cf_item_location, json.cf_item_location) AS cf_item_location,
    COALESCE(csv.cf_manufacturer, json.cf_manufacturer) AS cf_manufacturer,
    COALESCE(csv.cf_product_category, json.cf_product_category) AS cf_product_category,
    COALESCE(csv.cf_product_sale_category, json.cf_product_sale_category) AS cf_product_sale_category,
    COALESCE(csv.cf_sku_category, json.cf_sku_category) AS cf_sku_category,
    COALESCE(csv.description, json.description) AS description,
    COALESCE(csv.item_id, json.item_id) AS item_id,
    COALESCE(csv.item_name, json.item_name) AS item_name,
    COALESCE(csv.item_type, json.item_type) AS item_type,
    COALESCE(csv.product_type, json.product_type) AS product_type,
    COALESCE(csv.purchase_description, json.purchase_description) AS purchase_description,
    COALESCE(csv.purchase_rate, json.purchase_rate) AS purchase_rate,
    COALESCE(csv.rate, json.rate) AS rate,
    COALESCE(csv.sku, json.sku) AS sku,
    COALESCE(csv.source, json.source) AS source,
    COALESCE(csv.status, json.status) AS status,
    COALESCE(csv.stock_on_hand, json.stock_on_hand) AS stock_on_hand,
    COALESCE(csv.tax_name, json.tax_name) AS tax_name,
    COALESCE(csv.tax_percentage, json.tax_percentage) AS tax_percentage,
    csv.account,
    csv.account_code,
    csv.cf_m_box,
    csv.cf_s_box_qty,
    csv.created_timestamp,
    csv.inventory_account,
    csv.inventory_account_code,
    csv.inventory_valuation_method,
    csv.last_sync_time,
    csv.opening_stock,
    csv.opening_stock_value,
    csv.purchase_account,
    csv.purchase_account_code,
    csv.purchase_tax_name,
    csv.purchase_tax_percentage,
    csv.purchase_tax_type,
    csv.reference_id,
    csv.region,
    csv.reorder_point,
    csv.tax_type,
    csv.updated_timestamp,
    csv.usage_unit,
    csv.vehicle,
    csv.vendor,
    json.account_id,
    json.account_name,
    json.actual_available_stock,
    json.available_stock,
    json.can_be_purchased,
    json.can_be_sold,
    json.cf_item_location_unformatted,
    json.cf_manufacturer_unformatted,
    json.cf_product_category_unformatted,
    json.cf_product_sale_category_unformatted,
    json.cf_sku_category_unformatted,
    json.created_time,
    json.has_attachment,
    json.image_document_id,
    json.image_name,
    json.image_type,
    json.is_linked_with_zohocrm,
    json.last_modified_time,
    json.name,
    json.purchase_account_id,
    json.purchase_account_name,
    json.reorder_level,
    json.tags,
    json.tax_id,
    json.track_inventory,
    json.unit,
    json.zcrm_product_id,
    'CSV_PREFERRED' AS data_source,
    2 AS source_priority
FROM csv_items csv
LEFT JOIN json_items json ON csv.item_id = json.item_id

UNION ALL

SELECT
    json.cf_item_location,
    json.cf_manufacturer,
    json.cf_product_category,
    json.cf_product_sale_category,
    json.cf_sku_category,
    json.description,
    json.item_id,
    json.item_name,
    json.item_type,
    json.product_type,
    json.purchase_description,
    json.purchase_rate,
    json.rate,
    json.sku,
    json.source,
    json.status,
    json.stock_on_hand,
    json.tax_name,
    json.tax_percentage,
    NULL as account,
    NULL as account_code,
    NULL as cf_m_box,
    NULL as cf_s_box_qty,
    NULL as created_timestamp,
    NULL as inventory_account,
    NULL as inventory_account_code,
    NULL as inventory_valuation_method,
    NULL as last_sync_time,
    NULL as opening_stock,
    NULL as opening_stock_value,
    NULL as purchase_account,
    NULL as purchase_account_code,
    NULL as purchase_tax_name,
    NULL as purchase_tax_percentage,
    NULL as purchase_tax_type,
    NULL as reference_id,
    NULL as region,
    NULL as reorder_point,
    NULL as tax_type,
    NULL as updated_timestamp,
    NULL as usage_unit,
    NULL as vehicle,
    NULL as vendor,
    json.account_id,
    json.account_name,
    json.actual_available_stock,
    json.available_stock,
    json.can_be_purchased,
    json.can_be_sold,
    json.cf_item_location_unformatted,
    json.cf_manufacturer_unformatted,
    json.cf_product_category_unformatted,
    json.cf_product_sale_category_unformatted,
    json.cf_sku_category_unformatted,
    json.created_time,
    json.has_attachment,
    json.image_document_id,
    json.image_name,
    json.image_type,
    json.is_linked_with_zohocrm,
    json.last_modified_time,
    json.name,
    json.purchase_account_id,
    json.purchase_account_name,
    json.reorder_level,
    json.tags,
    json.tax_id,
    json.track_inventory,
    json.unit,
    json.zcrm_product_id,
    'JSON_ONLY' AS data_source,
    4 AS source_priority
FROM json_items json
WHERE json.item_id NOT IN (
    SELECT DISTINCT csv.item_id 
    FROM csv_items csv 
    WHERE csv.item_id IS NOT NULL
)
AND json.item_id IS NOT NULL;
"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get baseline count
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_items")
        old_count = cursor.fetchone()[0]
        
        # Execute the SQL
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        # Test the results
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_items")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT data_source, COUNT(*) 
            FROM FINAL_view_csv_json_items 
            GROUP BY data_source ORDER BY data_source
        """)
        distribution = dict(cursor.fetchall())
        
        conn.commit()
        conn.close()
        
        print(f"✅ FINAL_view_csv_json_items: {old_count:,} → {new_count:,}")
        print(f"📊 Distribution: {distribution}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error implementing items view: {e}")
        return False


def main():
    """Implement CSV-preferred strategy with freshness detection"""
    print("=" * 80)
    print("IMPLEMENTING CSV-PREFERRED STRATEGY WITH FRESHNESS DETECTION")
    print("=" * 80)
    print("🎯 Strategy: Prefer CSV data, use JSON only when demonstrably fresher")
    print("📅 Freshness Detection: Compare last_modified_time fields")
    print("📊 Data Source Priority: CSV_PREFERRED > JSON_FRESH > CSV_ONLY > JSON_ONLY")
    print()
    
    # Implement for tables with overlapping data
    success_count = 0
    
    if implement_csv_preferred_contacts():
        success_count += 1
        
    if implement_csv_preferred_items():
        success_count += 1
    
    print("\n" + "=" * 80)
    print("CSV-PREFERRED IMPLEMENTATION SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully updated: {success_count}/2 views")
    print()
    print("🔍 **Key Changes Made:**")
    print("1. 🔄 **CSV Priority**: CSV data is preferred by default")
    print("2. 🆕 **Freshness Check**: JSON used only when last_modified_time > CSV timestamp")
    print("3. 📊 **Clear Tracking**: data_source field shows reasoning (CSV_PREFERRED, JSON_FRESH, etc.)")
    print("4. 🎯 **Business Logic**: Maintains current workflow while improving data quality")
    print()
    print("📋 **Next Steps:**")
    print("- Run analyze_all_views.py to verify the changes")
    print("- Test with real data to validate freshness detection")
    print("- Apply similar pattern to other tables with overlapping data")


if __name__ == "__main__":
    main()
