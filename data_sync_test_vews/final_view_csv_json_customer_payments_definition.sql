-- View: FINAL_view_csv_json_customer_payments
-- Generated: 2025-07-12 11:39:29.742312

CREATE VIEW FINAL_view_csv_json_customer_payments AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.customer_payment_id, csv.payment_number, csv.mode, csv.customer_id, csv.description, csv.exchange_rate, csv.amount, csv.unused_amount, csv.bank_charges, csv.reference_number, csv.currency_code, csv.branch_id, csv.payment_number_prefix, csv.payment_number_suffix, csv.customer_name, csv.payment_type, csv.branch_name, csv.date, csv.created_time, csv.deposit_to, csv.deposit_to_account_code, csv.tax_account, csv.invoice_payment_id, csv.amount_applied_to_invoice, csv.invoice_payment_applied_date, csv.early_payment_discount, csv.withholding_tax_amount, csv.invoice_number, csv.invoice_date, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_customer_payments csv
WHERE csv.payment_number IS NOT NULL;
