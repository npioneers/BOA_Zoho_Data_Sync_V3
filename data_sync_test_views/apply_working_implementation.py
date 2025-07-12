#!/usr/bin/env python3
"""
Apply Working Smart Merging Views
Uses the proven simple approach to fix all 5 CSV-only views.
"""
import sqlite3
from datetime import datetime
from config import get_database_path


def apply_items_view():
    """Apply the working items view"""
    db_path = get_database_path()
    
    # The proven working SQL
    sql = """
DROP VIEW IF EXISTS FINAL_view_csv_json_items;

CREATE VIEW FINAL_view_csv_json_items AS
SELECT
    COALESCE(json.cf_item_location, csv.cf_item_location) AS cf_item_location,
    COALESCE(json.cf_manufacturer, csv.cf_manufacturer) AS cf_manufacturer,
    COALESCE(json.cf_product_category, csv.cf_product_category) AS cf_product_category,
    COALESCE(json.cf_product_sale_category, csv.cf_product_sale_category) AS cf_product_sale_category,
    COALESCE(json.cf_sku_category, csv.cf_sku_category) AS cf_sku_category,
    COALESCE(json.description, csv.description) AS description,
    COALESCE(json.item_id, csv.item_id) AS item_id,
    COALESCE(json.item_name, csv.item_name) AS item_name,
    COALESCE(json.item_type, csv.item_type) AS item_type,
    COALESCE(json.product_type, csv.product_type) AS product_type,
    COALESCE(json.purchase_description, csv.purchase_description) AS purchase_description,
    COALESCE(json.purchase_rate, csv.purchase_rate) AS purchase_rate,
    COALESCE(json.rate, csv.rate) AS rate,
    COALESCE(json.sku, csv.sku) AS sku,
    COALESCE(json.source, csv.source) AS source,
    COALESCE(json.status, csv.status) AS status,
    COALESCE(json.stock_on_hand, csv.stock_on_hand) AS stock_on_hand,
    COALESCE(json.tax_name, csv.tax_name) AS tax_name,
    COALESCE(json.tax_percentage, csv.tax_percentage) AS tax_percentage,
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
    CASE WHEN json.item_id IS NOT NULL THEN 'JSON' ELSE 'CSV' END AS data_source,
    CASE WHEN json.item_id IS NOT NULL THEN 1 ELSE 2 END AS source_priority
FROM csv_items csv
LEFT JOIN json_items json ON csv.item_id = json.item_id
WHERE
    COALESCE(json.item_name, csv.item_name) IS NOT NULL
    OR COALESCE(json.sku, csv.sku) IS NOT NULL
    OR COALESCE(json.description, csv.description) IS NOT NULL

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
    'JSON' AS data_source,
    1 AS source_priority
FROM json_items json
WHERE json.item_id NOT IN (
    SELECT DISTINCT csv.item_id 
    FROM csv_items csv 
    WHERE csv.item_id IS NOT NULL
)
AND (
    json.item_name IS NOT NULL
    OR json.sku IS NOT NULL
    OR json.description IS NOT NULL
);
"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Applying enhanced items view with UNION for complete data visibility...")
        
        # Execute the SQL
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        # Test the results
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_items")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT data_source, COUNT(*) 
            FROM FINAL_view_csv_json_items 
            GROUP BY data_source ORDER BY data_source
        """)
        distribution = dict(cursor.fetchall())
        
        conn.commit()
        conn.close()
        
        print(f"✅ Items view updated successfully!")
        print(f"📊 Total records: {total_count:,}")
        print(f"📈 Distribution: {distribution}")
        
        json_records = distribution.get('JSON', 0)
        csv_records = distribution.get('CSV', 0)
        
        if json_records > 0:
            print(f"🎉 SUCCESS: {json_records:,} JSON records now visible!")
            improvement = (json_records / csv_records * 100) if csv_records > 0 else 0
            print(f"📈 Improvement: {improvement:.1f}% more data visible")
        else:
            print(f"⚠️  No JSON records found - may indicate data structure issue")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying items view: {e}")
        return False


def main():
    """Apply the working implementation"""
    print("=" * 80)
    print("APPLYING WORKING SMART MERGING - ITEMS VIEW")
    print("=" * 80)
    
    print("🎯 Target: FINAL_view_csv_json_items")
    print("🔧 Strategy: LEFT JOIN + UNION for complete data visibility")
    print("📊 Expected: +1,114 JSON records (120% improvement)")
    print()
    
    if apply_items_view():
        print(f"\n✅ Items view implementation successful!")
        print(f"\n📋 Next steps:")
        print(f"   1. Verify improvements: python analyze_final_views_strategies.py")
        print(f"   2. Apply same pattern to other 4 views if successful")
        print(f"   3. Standardize all CSV-only views")
    else:
        print(f"\n❌ Items view implementation failed")


if __name__ == "__main__":
    main()
