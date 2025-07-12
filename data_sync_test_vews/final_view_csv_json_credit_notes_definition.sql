-- View: FINAL_view_csv_json_credit_notes
-- Generated: 2025-07-12 11:39:29.742312

CREATE VIEW FINAL_view_csv_json_credit_notes AS
SELECT 
    COALESCE(flat.customer_name, csv.customer_name) AS customer_name, COALESCE(flat.customer_id, csv.customer_id) AS customer_id, COALESCE(flat.total, csv.total) AS total, COALESCE(flat.balance, csv.balance) AS balance, csv.created_timestamp, csv.updated_timestamp, csv.credit_notes_id, csv.credit_note_date, csv.product_id, csv.credit_note_number, csv.credit_note_status, csv.accounts_receivable, csv.billing_attention, csv.billing_address, csv.billing_street_2, csv.billing_city, csv.billing_state, csv.billing_country, csv.billing_code, csv.billing_phone, csv.billing_fax, csv.shipping_attention, csv.shipping_address, csv.shipping_street_2, csv.shipping_city, csv.shipping_state, csv.shipping_country, csv.shipping_phone, csv.shipping_code, csv.shipping_fax, csv.currency_code, csv.exchange_rate, csv.is_inclusive_tax, csv.entity_discount_percent, csv.notes, csv.terms_conditions, csv.reference_number, csv.shipping_charge, csv.shipping_charge_tax_id, csv.shipping_charge_tax_amount, csv.shipping_charge_tax_name, csv.shipping_charge_tax_percent, csv.shipping_charge_tax_type, csv.shipping_charge_account, csv.adjustment, csv.adjustment_account, csv.branch_id, csv.is_discount_before_tax, csv.item_name, csv.discount, csv.discount_amount, csv.quantity, csv.item_desc, csv.item_tax_amount, csv.item_total, csv.applied_invoice_number, csv.branch_name, csv.project_id, csv.project_name, csv.tax1_id, csv.item_tax, csv.item_tax_percent, csv.item_tax_type, csv.tds_name, csv.tds_percentage, csv.tds_amount, csv.tds_type, csv.sales_person, csv.discount_type, csv.subtotal, csv.round_off, csv.adjustment_description, csv.subject, csv.template_name, csv.usage_unit, csv.item_price, csv.account, csv.account_code, csv.sku, csv.region, csv.vehicle, csv.entity_discount_amount, csv.kit_combo_item_name, csv.item_cf_sku_category, csv.cf_region, csv.cf_scheme_type, csv.cf_scheme_settlement_period, csv.cf_modified, csv.cf_dispatch_incomplete_but_scheme_passed, csv.data_source, flat.creditnote_id, flat.creditnote_number, flat.date, flat.status, flat.line_item_id, flat.item_id, flat.line_item_name, flat.line_item_quantity, flat.line_item_rate, flat.line_item_item_total, flat.line_item_account_name, flat.line_item_description, flat.line_item_unit, flat.line_item_tax_name, flat.line_item_tax_percentage,
    CASE 
        WHEN flat.creditnote_number IS NOT NULL THEN 'json_precedence'
        ELSE 'csv_only' 
    END AS data_source,
    CASE 
        WHEN flat.creditnote_number IS NOT NULL THEN 1  -- JSON priority
        ELSE 2  -- CSV backup
    END AS source_priority
FROM csv_credit_notes csv
LEFT JOIN view_flat_json_creditnotes flat ON csv.credit_note_number = flat.creditnote_number
WHERE COALESCE(flat.creditnote_number, csv.credit_note_number) IS NOT NULL;
