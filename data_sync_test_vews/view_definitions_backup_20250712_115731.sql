-- View Definitions Backup
-- Created: 2025-07-12 11:57:31.268524
-- Original views before fixing empty view issues

-- FINAL_view_csv_json_bills
DROP VIEW IF EXISTS FINAL_view_csv_json_bills;
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

-- FINAL_view_csv_json_contacts
DROP VIEW IF EXISTS FINAL_view_csv_json_contacts;
CREATE VIEW FINAL_view_csv_json_contacts AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.contact_id, csv.created_time, csv.last_modified_time, csv.display_name, csv.company_name, csv.salutation, csv.first_name, csv.last_name, csv.phone, csv.currency_code, csv.notes, csv.website, csv.status, csv.accounts_receivable, csv.opening_balance, csv.opening_balance_exchange_rate, csv.branch_id, csv.branch_name, csv.bank_account_payment, csv.portal_enabled, csv.credit_limit, csv.customer_sub_type, csv.billing_attention, csv.billing_address, csv.billing_street2, csv.billing_city, csv.billing_state, csv.billing_country, csv.billing_county, csv.billing_code, csv.billing_phone, csv.billing_fax, csv.shipping_attention, csv.shipping_address, csv.shipping_street2, csv.shipping_city, csv.shipping_state, csv.shipping_country, csv.shipping_county, csv.shipping_code, csv.shipping_phone, csv.shipping_fax, csv.skype_identity, csv.facebook, csv.twitter, csv.department, csv.designation, csv.price_list, csv.payment_terms, csv.payment_terms_label, csv.tax_type, csv.track_tds, csv.last_sync_time, csv.owner_name, csv.primary_contact_id, csv.email_id, csv.mobile_phone, csv.contact_name, csv.contact_type, csv.taxable, csv.tax_name, csv.tax_percentage, csv.contact_address_id, csv.source, csv.region, csv.vehicle, csv.siret, csv.company_id, csv.cf_market_region, csv.cf_customer_category, csv.cf_special_scheme_targets, csv.cf_customer_sales_executive, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_contacts csv
WHERE csv.contact_id IS NOT NULL;

-- FINAL_view_csv_json_credit_notes
DROP VIEW IF EXISTS FINAL_view_csv_json_credit_notes;
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

-- FINAL_view_csv_json_customer_payments
DROP VIEW IF EXISTS FINAL_view_csv_json_customer_payments;
CREATE VIEW FINAL_view_csv_json_customer_payments AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.customer_payment_id, csv.payment_number, csv.mode, csv.customer_id, csv.description, csv.exchange_rate, csv.amount, csv.unused_amount, csv.bank_charges, csv.reference_number, csv.currency_code, csv.branch_id, csv.payment_number_prefix, csv.payment_number_suffix, csv.customer_name, csv.payment_type, csv.branch_name, csv.date, csv.created_time, csv.deposit_to, csv.deposit_to_account_code, csv.tax_account, csv.invoice_payment_id, csv.amount_applied_to_invoice, csv.invoice_payment_applied_date, csv.early_payment_discount, csv.withholding_tax_amount, csv.invoice_number, csv.invoice_date, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_customer_payments csv
WHERE csv.payment_number IS NOT NULL;

-- FINAL_view_csv_json_invoices
DROP VIEW IF EXISTS FINAL_view_csv_json_invoices;
CREATE VIEW FINAL_view_csv_json_invoices AS
SELECT 
    COALESCE(flat.invoice_id, csv.invoice_id) AS invoice_id, COALESCE(flat.invoice_number, csv.invoice_number) AS invoice_number, COALESCE(flat.customer_id, csv.customer_id) AS customer_id, COALESCE(flat.customer_name, csv.customer_name) AS customer_name, COALESCE(flat.due_date, csv.due_date) AS due_date, COALESCE(flat.total, csv.total) AS total, COALESCE(flat.balance, csv.balance) AS balance, csv.created_timestamp, csv.updated_timestamp, csv.invoice_date, csv.invoice_status, csv.accounts_receivable, csv.company_id, csv.is_inclusive_tax, csv.purchase_order, csv.currency_code, csv.exchange_rate, csv.discount_type, csv.is_discount_before_tax, csv.template_name, csv.entity_discount_percent, csv.subtotal, csv.adjustment, csv.adjustment_description, csv.adjustment_account, csv.expected_payment_date, csv.last_payment_date, csv.payment_terms, csv.payment_terms_label, csv.early_payment_discount_percentage, csv.early_payment_discount_amount, csv.early_payment_discount_due_days, csv.notes, csv.terms_conditions, csv.entity_discount_amount, csv.branch_id, csv.branch_name, csv.shipping_charge, csv.shipping_charge_tax_id, csv.shipping_charge_tax_amount, csv.shipping_charge_tax_name, csv.shipping_charge_tax_percent, csv.shipping_charge_tax_type, csv.shipping_charge_account, csv.item_name, csv.item_desc, csv.quantity, csv.discount, csv.discount_amount, csv.item_total, csv.usage_unit, csv.item_price, csv.product_id, csv.brand, csv.sales_order_number, csv.subscription_id, csv.expense_reference_id, csv.recurrence_name, csv.paypal, csv.authorize_net, csv.google_checkout, csv.payflow_pro, csv.stripe, csv.paytm, csv.two_checkout, csv.braintree, csv.forte, csv.worldpay, csv.payments_pro, csv.square, csv.wepay, csv.razorpay, csv.icici_eazypay, csv.gocardless, csv.partial_payments, csv.billing_attention, csv.billing_address, csv.billing_street2, csv.billing_city, csv.billing_state, csv.billing_country, csv.billing_code, csv.billing_phone, csv.billing_fax, csv.shipping_attention, csv.shipping_address, csv.shipping_street2, csv.shipping_city, csv.shipping_state, csv.shipping_country, csv.shipping_code, csv.shipping_fax, csv.shipping_phone_number, csv.tds_name, csv.tds_percentage, csv.tds_amount, csv.tds_type, csv.sku, csv.project_id, csv.project_name, csv.round_off, csv.sales_person, csv.subject, csv.primary_contact_email_id, csv.primary_contact_mobile, csv.primary_contact_phone, csv.estimate_number, csv.region, csv.vehicle, csv.custom_charges, csv.shipping_bill_number, csv.shipping_bill_date, csv.shipping_bill_total, csv.port_code, csv.account, csv.account_code, csv.tax_id, csv.item_tax, csv.item_tax_percent, csv.item_tax_amount, csv.item_tax_type, csv.kit_combo_item_name, csv.item_cf_sku_category, csv.cf_reason_to_void, csv.data_source, flat.date, flat.status, flat.line_item_id, flat.item_id, flat.line_item_name, flat.line_item_quantity, flat.line_item_rate, flat.line_item_item_total, flat.line_item_account_name, flat.line_item_description, flat.line_item_unit, flat.line_item_tax_name, flat.line_item_tax_percentage,
    CASE 
        WHEN flat.invoice_number IS NOT NULL THEN 'json_precedence'
        ELSE 'csv_only' 
    END AS data_source,
    CASE 
        WHEN flat.invoice_number IS NOT NULL THEN 1  -- JSON priority
        ELSE 2  -- CSV backup
    END AS source_priority
FROM csv_invoices csv
LEFT JOIN view_flat_json_invoices flat ON csv.invoice_number = flat.invoice_number
WHERE COALESCE(flat.invoice_number, csv.invoice_number) IS NOT NULL;

-- FINAL_view_csv_json_items
DROP VIEW IF EXISTS FINAL_view_csv_json_items;
CREATE VIEW FINAL_view_csv_json_items AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.item_id, csv.item_name, csv.sku, csv.description, csv.rate, csv.account, csv.account_code, csv.tax_name, csv.tax_percentage, csv.tax_type, csv.purchase_tax_name, csv.purchase_tax_percentage, csv.purchase_tax_type, csv.product_type, csv.source, csv.reference_id, csv.last_sync_time, csv.status, csv.usage_unit, csv.purchase_rate, csv.purchase_account, csv.purchase_account_code, csv.purchase_description, csv.inventory_account, csv.inventory_account_code, csv.inventory_valuation_method, csv.reorder_point, csv.vendor, csv.opening_stock, csv.opening_stock_value, csv.stock_on_hand, csv.item_type, csv.region, csv.vehicle, csv.cf_sku_category, csv.cf_product_sale_category, csv.cf_item_location, csv.cf_product_category, csv.cf_manufacturer, csv.cf_m_box, csv.cf_s_box_qty, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_items csv
WHERE csv.item_id IS NOT NULL;

-- FINAL_view_csv_json_purchase_orders
DROP VIEW IF EXISTS FINAL_view_csv_json_purchase_orders;
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

-- FINAL_view_csv_json_sales_orders
DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders;
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

-- FINAL_view_csv_json_vendor_payments
DROP VIEW IF EXISTS FINAL_view_csv_json_vendor_payments;
CREATE VIEW FINAL_view_csv_json_vendor_payments AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.vendor_payment_id, csv.payment_number, csv.payment_number_prefix, csv.payment_number_suffix, csv.mode, csv.description, csv.exchange_rate, csv.amount, csv.unused_amount, csv.reference_number, csv.currency_code, csv.branch_id, csv.payment_status, csv.date, csv.branch_name, csv.vendor_name, csv.email_id, csv.paid_through, csv.paid_through_account_code, csv.tax_account, csv.bank_reference_number, csv.pi_payment_id, csv.bill_amount, csv.bill_payment_applied_date, csv.bill_date, csv.bill_number, csv.withholding_tax_amount, csv.withholding_tax_amount_bcy, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_vendor_payments csv
WHERE csv.payment_number IS NOT NULL;

