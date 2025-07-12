-- View: FINAL_view_csv_json_sales_orders
-- Generated: 2025-07-12 11:39:29.745365

CREATE VIEW FINAL_view_csv_json_sales_orders AS
SELECT 
    COALESCE(flat.status, csv.status) AS status, COALESCE(flat.customer_id, csv.customer_id) AS customer_id, COALESCE(flat.customer_name, csv.customer_name) AS customer_name, COALESCE(flat.total, csv.total) AS total, csv.created_timestamp, csv.updated_timestamp, csv.sales_order_id, csv.order_date, csv.expected_shipment_date, csv.sales_order_number, csv.custom_status, csv.branch_id, csv.branch_name, csv.is_inclusive_tax, csv.reference_number, csv.template_name, csv.currency_code, csv.exchange_rate, csv.discount_type, csv.is_discount_before_tax, csv.entity_discount_amount, csv.entity_discount_percent, csv.item_name, csv.product_id, csv.sku, csv.kit_combo_item_name, csv.account, csv.account_code, csv.item_desc, csv.quantity_ordered, csv.quantity_invoiced, csv.quantity_cancelled, csv.usage_unit, csv.item_price, csv.discount, csv.discount_amount, csv.tax_id, csv.item_tax, csv.item_tax_percent, csv.item_tax_amount, csv.item_tax_type, csv.tds_name, csv.tds_percentage, csv.tds_amount, csv.tds_type, csv.region, csv.vehicle, csv.project_id, csv.project_name, csv.item_total, csv.subtotal, csv.shipping_charge, csv.shipping_charge_tax_id, csv.shipping_charge_tax_amount, csv.shipping_charge_tax_name, csv.shipping_charge_tax_percent, csv.shipping_charge_tax_type, csv.adjustment, csv.adjustment_description, csv.sales_person, csv.payment_terms, csv.payment_terms_label, csv.notes, csv.terms_conditions, csv.delivery_method, csv.source, csv.billing_address, csv.billing_street2, csv.billing_city, csv.billing_state, csv.billing_country, csv.billing_code, csv.billing_fax, csv.billing_phone, csv.shipping_address, csv.shipping_street2, csv.shipping_city, csv.shipping_state, csv.shipping_country, csv.shipping_code, csv.shipping_fax, csv.shipping_phone, csv.item_cf_sku_category, csv.cf_region, csv.cf_pending_items_delivery, csv.data_source, flat.salesorder_id, flat.salesorder_number, flat.date, flat.line_item_id, flat.item_id, flat.line_item_name, flat.line_item_quantity, flat.line_item_rate, flat.line_item_item_total, flat.line_item_account_name, flat.line_item_description, flat.line_item_unit, flat.line_item_tax_name, flat.line_item_tax_percentage,
    CASE 
        WHEN flat.salesorder_number IS NOT NULL THEN 'json_precedence'
        ELSE 'csv_only' 
    END AS data_source,
    CASE 
        WHEN flat.salesorder_number IS NOT NULL THEN 1  -- JSON priority
        ELSE 2  -- CSV backup
    END AS source_priority
FROM csv_sales_orders csv
LEFT JOIN view_flat_json_salesorders flat ON csv.sales_order_number = flat.salesorder_number
WHERE COALESCE(flat.salesorder_number, csv.sales_order_number) IS NOT NULL;
