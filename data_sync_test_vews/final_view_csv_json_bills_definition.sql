-- View: FINAL_view_csv_json_bills
-- Generated: 2025-07-12 11:39:29.739362

CREATE VIEW FINAL_view_csv_json_bills AS
SELECT 
    COALESCE(flat.bill_id, csv.bill_id) AS bill_id, COALESCE(flat.due_date, csv.due_date) AS due_date, COALESCE(flat.vendor_name, csv.vendor_name) AS vendor_name, COALESCE(flat.bill_number, csv.bill_number) AS bill_number, COALESCE(flat.currency_code, csv.currency_code) AS currency_code, COALESCE(flat.total, csv.total) AS total, COALESCE(flat.balance, csv.balance) AS balance, csv.created_timestamp, csv.updated_timestamp, csv.bill_date, csv.accounts_payable, csv.entity_discount_percent, csv.payment_terms, csv.payment_terms_label, csv.purchase_order, csv.exchange_rate, csv.subtotal, csv.vendor_notes, csv.terms_conditions, csv.adjustment, csv.adjustment_description, csv.adjustment_account, csv.bill_type, csv.branch_id, csv.branch_name, csv.is_inclusive_tax, csv.submitted_by, csv.approved_by, csv.submitted_date, csv.approved_date, csv.bill_status, csv.created_by, csv.product_id, csv.item_name, csv.account, csv.account_code, csv.description, csv.quantity, csv.usage_unit, csv.tax_amount, csv.item_total, csv.is_billable, csv.sku, csv.rate, csv.discount_type, csv.is_discount_before_tax, csv.discount, csv.discount_amount, csv.purchase_order_number, csv.tax_id, csv.tax_name, csv.tax_percentage, csv.tax_type, csv.tds_name, csv.tds_percentage, csv.tds_amount, csv.tds_type, csv.entity_discount_amount, csv.discount_account, csv.discount_account_code, csv.is_landed_cost, csv.customer_name, csv.project_name, csv.region, csv.vehicle, csv.cf_chp_scheme_settlement_period, csv.data_source, flat.vendor_id, flat.date, flat.line_item_id, flat.item_id, flat.line_item_name, flat.line_item_quantity, flat.line_item_rate, flat.line_item_item_total, flat.line_item_account_name, flat.line_item_description, flat.line_item_unit, flat.line_item_tax_name, flat.line_item_tax_percentage,
    CASE 
        WHEN flat.bill_number IS NOT NULL THEN 'json_precedence'
        ELSE 'csv_only' 
    END AS data_source,
    CASE 
        WHEN flat.bill_number IS NOT NULL THEN 1  -- JSON priority
        ELSE 2  -- CSV backup
    END AS source_priority
FROM csv_bills csv
LEFT JOIN view_flat_json_bills flat ON csv.bill_number = flat.bill_number
WHERE COALESCE(flat.bill_number, csv.bill_number) IS NOT NULL;
