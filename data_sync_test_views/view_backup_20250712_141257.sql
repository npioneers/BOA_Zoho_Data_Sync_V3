-- View Backup Created: 2025-07-12T14:15:06.569692
-- Original CSV-only views before smart merging conversion

-- FINAL_view_csv_json_contacts
DROP VIEW IF EXISTS FINAL_view_csv_json_contacts;
CREATE VIEW FINAL_view_csv_json_contacts AS
        SELECT 
            *,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_contacts
        WHERE 
            display_name IS NOT NULL 
            OR company_name IS NOT NULL
            OR first_name IS NOT NULL
            OR last_name IS NOT NULL;

-- FINAL_view_csv_json_customer_payments
DROP VIEW IF EXISTS FINAL_view_csv_json_customer_payments;
CREATE VIEW FINAL_view_csv_json_customer_payments AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.customer_payment_id, csv.payment_number, csv.mode, csv.customer_id, csv.description, csv.exchange_rate, csv.amount, csv.unused_amount, csv.bank_charges, csv.reference_number, csv.currency_code, csv.branch_id, csv.payment_number_prefix, csv.payment_number_suffix, csv.customer_name, csv.payment_type, csv.branch_name, csv.date, csv.created_time, csv.deposit_to, csv.deposit_to_account_code, csv.tax_account, csv.invoice_payment_id, csv.amount_applied_to_invoice, csv.invoice_payment_applied_date, csv.early_payment_discount, csv.withholding_tax_amount, csv.invoice_number, csv.invoice_date, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_customer_payments csv
WHERE csv.payment_number IS NOT NULL;

-- FINAL_view_csv_json_items
DROP VIEW IF EXISTS FINAL_view_csv_json_items;
CREATE VIEW FINAL_view_csv_json_items AS
        SELECT 
            *,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_items
        WHERE 
            item_name IS NOT NULL 
            OR sku IS NOT NULL
            OR description IS NOT NULL;

-- FINAL_view_csv_json_sales_orders
DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders;
CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT 
            *,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_sales_orders
        WHERE 
            sales_order_number IS NOT NULL 
            OR customer_name IS NOT NULL
            OR order_date IS NOT NULL;

-- FINAL_view_csv_json_vendor_payments
DROP VIEW IF EXISTS FINAL_view_csv_json_vendor_payments;
CREATE VIEW FINAL_view_csv_json_vendor_payments AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.vendor_payment_id, csv.payment_number, csv.payment_number_prefix, csv.payment_number_suffix, csv.mode, csv.description, csv.exchange_rate, csv.amount, csv.unused_amount, csv.reference_number, csv.currency_code, csv.branch_id, csv.payment_status, csv.date, csv.branch_name, csv.vendor_name, csv.email_id, csv.paid_through, csv.paid_through_account_code, csv.tax_account, csv.bank_reference_number, csv.pi_payment_id, csv.bill_amount, csv.bill_payment_applied_date, csv.bill_date, csv.bill_number, csv.withholding_tax_amount, csv.withholding_tax_amount_bcy, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_vendor_payments csv
WHERE csv.payment_number IS NOT NULL;
