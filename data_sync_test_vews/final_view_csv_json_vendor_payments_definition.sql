-- View: FINAL_view_csv_json_vendor_payments
-- Generated: 2025-07-12 11:39:29.745365

CREATE VIEW FINAL_view_csv_json_vendor_payments AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.vendor_payment_id, csv.payment_number, csv.payment_number_prefix, csv.payment_number_suffix, csv.mode, csv.description, csv.exchange_rate, csv.amount, csv.unused_amount, csv.reference_number, csv.currency_code, csv.branch_id, csv.payment_status, csv.date, csv.branch_name, csv.vendor_name, csv.email_id, csv.paid_through, csv.paid_through_account_code, csv.tax_account, csv.bank_reference_number, csv.pi_payment_id, csv.bill_amount, csv.bill_payment_applied_date, csv.bill_date, csv.bill_number, csv.withholding_tax_amount, csv.withholding_tax_amount_bcy, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_vendor_payments csv
WHERE csv.payment_number IS NOT NULL;
