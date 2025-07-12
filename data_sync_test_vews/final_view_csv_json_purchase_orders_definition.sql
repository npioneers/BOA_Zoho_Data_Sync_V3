-- View: FINAL_view_csv_json_purchase_orders
-- Generated: 2025-07-12 11:39:29.743677

CREATE VIEW FINAL_view_csv_json_purchase_orders AS
SELECT 
    COALESCE(flat.vendor_name, csv.vendor_name) AS vendor_name, COALESCE(flat.total, csv.total) AS total, csv.created_timestamp, csv.updated_timestamp, csv.purchase_order_id, csv.purchase_order_date, csv.branch_id, csv.branch_name, csv.delivery_date, csv.purchase_order_number, csv.reference_number, csv.purchase_order_status, csv.is_inclusive_tax, csv.currency_code, csv.exchange_rate, csv.template_name, csv.reference_no, csv.delivery_instructions, csv.terms_conditions, csv.shipment_preference, csv.expected_arrival_date, csv.account, csv.account_code, csv.item_price, csv.item_name, csv.product_id, csv.sku, csv.item_desc, csv.quantity_ordered, csv.quantity_cancelled, csv.quantity_received, csv.quantity_billed, csv.usage_unit, csv.discount_type, csv.is_discount_before_tax, csv.discount, csv.discount_amount, csv.tax_id, csv.item_tax, csv.item_tax_percent, csv.item_tax_amount, csv.item_tax_type, csv.item_total, csv.adjustment, csv.adjustment_description, csv.entity_discount_percent, csv.entity_discount_amount, csv.discount_account, csv.discount_account_code, csv.tds_name, csv.tds_percentage, csv.tds_amount, csv.tds_type, csv.region, csv.vehicle, csv.project_id, csv.project_name, csv.payment_terms, csv.payment_terms_label, csv.attention, csv.address, csv.city, csv.state, csv.country, csv.code, csv.phone, csv.deliver_to_customer, csv.recipient_address, csv.recipient_city, csv.recipient_state, csv.recipient_country, csv.recipient_postal_code, csv.recipient_phone, csv.submitted_by, csv.approved_by, csv.submitted_date, csv.approved_date, csv.data_source, flat.purchaseorder_id, flat.purchaseorder_number, flat.vendor_id, flat.date, flat.status, flat.line_item_id, flat.item_id, flat.line_item_name, flat.line_item_quantity, flat.line_item_rate, flat.line_item_item_total, flat.line_item_account_name, flat.line_item_description, flat.line_item_unit, flat.line_item_tax_name, flat.line_item_tax_percentage,
    CASE 
        WHEN flat.purchaseorder_number IS NOT NULL THEN 'json_precedence'
        ELSE 'csv_only' 
    END AS data_source,
    CASE 
        WHEN flat.purchaseorder_number IS NOT NULL THEN 1  -- JSON priority
        ELSE 2  -- CSV backup
    END AS source_priority
FROM csv_purchase_orders csv
LEFT JOIN view_flat_json_purchaseorders flat ON csv.purchase_order_number = flat.purchaseorder_number
WHERE COALESCE(flat.purchaseorder_number, csv.purchase_order_number) IS NOT NULL;
