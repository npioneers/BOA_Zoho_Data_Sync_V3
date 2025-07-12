-- View: FINAL_view_csv_json_items
-- Generated: 2025-07-12 11:39:29.743677

CREATE VIEW FINAL_view_csv_json_items AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.item_id, csv.item_name, csv.sku, csv.description, csv.rate, csv.account, csv.account_code, csv.tax_name, csv.tax_percentage, csv.tax_type, csv.purchase_tax_name, csv.purchase_tax_percentage, csv.purchase_tax_type, csv.product_type, csv.source, csv.reference_id, csv.last_sync_time, csv.status, csv.usage_unit, csv.purchase_rate, csv.purchase_account, csv.purchase_account_code, csv.purchase_description, csv.inventory_account, csv.inventory_account_code, csv.inventory_valuation_method, csv.reorder_point, csv.vendor, csv.opening_stock, csv.opening_stock_value, csv.stock_on_hand, csv.item_type, csv.region, csv.vehicle, csv.cf_sku_category, csv.cf_product_sale_category, csv.cf_item_location, csv.cf_product_category, csv.cf_manufacturer, csv.cf_m_box, csv.cf_s_box_qty, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_items csv
WHERE csv.item_id IS NOT NULL;
