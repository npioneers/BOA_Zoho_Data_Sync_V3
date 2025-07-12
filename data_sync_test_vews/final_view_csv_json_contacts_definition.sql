-- View: FINAL_view_csv_json_contacts
-- Generated: 2025-07-12 11:39:29.739362

CREATE VIEW FINAL_view_csv_json_contacts AS
SELECT 
    csv.created_timestamp, csv.updated_timestamp, csv.contact_id, csv.created_time, csv.last_modified_time, csv.display_name, csv.company_name, csv.salutation, csv.first_name, csv.last_name, csv.phone, csv.currency_code, csv.notes, csv.website, csv.status, csv.accounts_receivable, csv.opening_balance, csv.opening_balance_exchange_rate, csv.branch_id, csv.branch_name, csv.bank_account_payment, csv.portal_enabled, csv.credit_limit, csv.customer_sub_type, csv.billing_attention, csv.billing_address, csv.billing_street2, csv.billing_city, csv.billing_state, csv.billing_country, csv.billing_county, csv.billing_code, csv.billing_phone, csv.billing_fax, csv.shipping_attention, csv.shipping_address, csv.shipping_street2, csv.shipping_city, csv.shipping_state, csv.shipping_country, csv.shipping_county, csv.shipping_code, csv.shipping_phone, csv.shipping_fax, csv.skype_identity, csv.facebook, csv.twitter, csv.department, csv.designation, csv.price_list, csv.payment_terms, csv.payment_terms_label, csv.tax_type, csv.track_tds, csv.last_sync_time, csv.owner_name, csv.primary_contact_id, csv.email_id, csv.mobile_phone, csv.contact_name, csv.contact_type, csv.taxable, csv.tax_name, csv.tax_percentage, csv.contact_address_id, csv.source, csv.region, csv.vehicle, csv.siret, csv.company_id, csv.cf_market_region, csv.cf_customer_category, csv.cf_special_scheme_targets, csv.cf_customer_sales_executive, csv.data_source,
    'csv_only' AS data_source,
    2 AS source_priority
FROM csv_contacts csv
WHERE csv.contact_id IS NOT NULL;
