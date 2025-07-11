-- Restore Indexes Script
-- Generated on: 2025-07-08 10:35:23
-- Total indexes to restore: 43

-- Restore index on table: json_bills
CREATE INDEX idx_json_bills_date ON json_bills(date);

-- Restore index on table: json_bills
CREATE INDEX idx_json_bills_reference_number ON json_bills(reference_number);

-- Restore index on table: json_bills
CREATE INDEX idx_json_bills_status ON json_bills(status);

-- Restore index on table: json_bills_line_items
CREATE INDEX idx_json_bills_line_items_name ON json_bills_line_items(name);

-- Restore index on table: json_contacts
CREATE INDEX idx_json_contacts_email ON json_contacts(email);

-- Restore index on table: json_contacts
CREATE INDEX idx_json_contacts_phone ON json_contacts(phone);

-- Restore index on table: json_contacts
CREATE INDEX idx_json_contacts_status ON json_contacts(status);

-- Restore index on table: json_credit_notes
CREATE INDEX idx_json_credit_notes_date ON json_credit_notes(date);

-- Restore index on table: json_credit_notes
CREATE INDEX idx_json_credit_notes_reference_number ON json_credit_notes(reference_number);

-- Restore index on table: json_credit_notes
CREATE INDEX idx_json_credit_notes_status ON json_credit_notes(status);

-- Restore index on table: json_creditnotes_line_items
CREATE INDEX idx_json_creditnotes_line_items_name ON json_creditnotes_line_items(name);

-- Restore index on table: json_customer_payments
CREATE INDEX idx_json_customer_payments_date ON json_customer_payments(date);

-- Restore index on table: json_customer_payments
CREATE INDEX idx_json_customer_payments_reference_number ON json_customer_payments(reference_number);

-- Restore index on table: json_invoices
CREATE INDEX idx_json_invoices_date ON json_invoices(date);

-- Restore index on table: json_invoices
CREATE INDEX idx_json_invoices_email ON json_invoices(email);

-- Restore index on table: json_invoices
CREATE INDEX idx_json_invoices_phone ON json_invoices(phone);

-- Restore index on table: json_invoices
CREATE INDEX idx_json_invoices_reference_number ON json_invoices(reference_number);

-- Restore index on table: json_invoices
CREATE INDEX idx_json_invoices_status ON json_invoices(status);

-- Restore index on table: json_invoices_line_items
CREATE INDEX idx_json_invoices_line_items_name ON json_invoices_line_items(name);

-- Restore index on table: json_invoices_line_items
CREATE INDEX idx_json_invoices_line_items_time_entry_ids ON json_invoices_line_items(time_entry_ids);

-- Restore index on table: json_items
CREATE INDEX idx_json_items_name ON json_items(name);

-- Restore index on table: json_items
CREATE INDEX idx_json_items_status ON json_items(status);

-- Restore index on table: json_organizations
CREATE INDEX idx_json_organizations_email ON json_organizations(email);

-- Restore index on table: json_organizations
CREATE INDEX idx_json_organizations_is_scan_preference_enabled ON json_organizations(is_scan_preference_enabled);

-- Restore index on table: json_organizations
CREATE INDEX idx_json_organizations_name ON json_organizations(name);

-- Restore index on table: json_organizations
CREATE INDEX idx_json_organizations_phone ON json_organizations(phone);

-- Restore index on table: json_purchase_orders
CREATE INDEX idx_json_purchase_orders_date ON json_purchase_orders(date);

-- Restore index on table: json_purchase_orders
CREATE INDEX idx_json_purchase_orders_reference_number ON json_purchase_orders(reference_number);

-- Restore index on table: json_purchase_orders
CREATE INDEX idx_json_purchase_orders_status ON json_purchase_orders(status);

-- Restore index on table: json_purchase_orders
CREATE INDEX idx_json_purchase_orders_tax_override_preference ON json_purchase_orders(tax_override_preference);

-- Restore index on table: json_purchase_orders
CREATE INDEX idx_json_purchase_orders_tds_override_preference ON json_purchase_orders(tds_override_preference);

-- Restore index on table: json_purchaseorders_line_items
CREATE INDEX idx_json_purchaseorders_line_items_name ON json_purchaseorders_line_items(name);

-- Restore index on table: json_sales_orders
CREATE INDEX idx_json_sales_orders_date ON json_sales_orders(date);

-- Restore index on table: json_sales_orders
CREATE INDEX idx_json_sales_orders_email ON json_sales_orders(email);

-- Restore index on table: json_sales_orders
CREATE INDEX idx_json_sales_orders_paid_status ON json_sales_orders(paid_status);

-- Restore index on table: json_sales_orders
CREATE INDEX idx_json_sales_orders_reference_number ON json_sales_orders(reference_number);

-- Restore index on table: json_sales_orders
CREATE INDEX idx_json_sales_orders_status ON json_sales_orders(status);

-- Restore index on table: json_salesorders_line_items
CREATE INDEX idx_json_salesorders_line_items_name ON json_salesorders_line_items(name);

-- Restore index on table: json_vendor_payments
CREATE INDEX idx_json_vendor_payments_date ON json_vendor_payments(date);

-- Restore index on table: json_vendor_payments
CREATE INDEX idx_json_vendor_payments_is_paid_via_print_check ON json_vendor_payments(is_paid_via_print_check);

-- Restore index on table: json_vendor_payments
CREATE INDEX idx_json_vendor_payments_paid_through_account_name ON json_vendor_payments(paid_through_account_name);

-- Restore index on table: json_vendor_payments
CREATE INDEX idx_json_vendor_payments_reference_number ON json_vendor_payments(reference_number);

-- Restore index on table: json_vendor_payments
CREATE INDEX idx_json_vendor_payments_status ON json_vendor_payments(status);

