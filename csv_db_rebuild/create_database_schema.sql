-- Database Creation Script for Zoho Data Sync V2
-- Generated: July 7, 2025
-- Purpose: Complete mirror of CSV files structure
-- Target: data/database/production.db (will replace existing)

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS csv_invoices;
DROP TABLE IF EXISTS csv_items;
DROP TABLE IF EXISTS csv_contacts;
DROP TABLE IF EXISTS csv_bills;
DROP TABLE IF EXISTS csv_organizations;
DROP TABLE IF EXISTS csv_customer_payments;
DROP TABLE IF EXISTS csv_vendor_payments;
DROP TABLE IF EXISTS csv_sales_orders;
DROP TABLE IF EXISTS csv_purchase_orders;
DROP TABLE IF EXISTS csv_credit_notes;

-- ==================================================
-- CSV_INVOICES TABLE (107 columns)
-- ==================================================
CREATE TABLE csv_invoices (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    -- Core Invoice Fields
    invoice_date TEXT,
    invoice_id TEXT PRIMARY KEY,
    invoice_number TEXT,
    invoice_status TEXT,
    accounts_receivable TEXT,
    customer_id TEXT,
    customer_name TEXT,
    company_id TEXT,
    is_inclusive_tax TEXT,
    due_date TEXT,
    purchase_order TEXT,
    currency_code TEXT,
    exchange_rate TEXT,
    
    -- Discount and Pricing
    discount_type TEXT,
    is_discount_before_tax TEXT,
    template_name TEXT,
    entity_discount_percent TEXT,
    subtotal TEXT,
    total TEXT,
    balance TEXT,
    adjustment TEXT,
    adjustment_description TEXT,
    adjustment_account TEXT,
    
    -- Payment Information
    expected_payment_date TEXT,
    last_payment_date TEXT,
    payment_terms TEXT,
    payment_terms_label TEXT,
    early_payment_discount_percentage TEXT,
    early_payment_discount_amount TEXT,
    early_payment_discount_due_days TEXT,
    
    -- Notes and Terms
    notes TEXT,
    terms_conditions TEXT,
    entity_discount_amount TEXT,
    
    -- Branch Information
    branch_id TEXT,
    branch_name TEXT,
    
    -- Shipping Information
    shipping_charge TEXT,
    shipping_charge_tax_id TEXT,
    shipping_charge_tax_amount TEXT,
    shipping_charge_tax_name TEXT,
    shipping_charge_tax_percent TEXT,
    shipping_charge_tax_type TEXT,
    shipping_charge_account TEXT,
    
    -- Item Line Details
    item_name TEXT,
    item_desc TEXT,
    quantity TEXT,
    discount TEXT,
    discount_amount TEXT,
    item_total TEXT,
    usage_unit TEXT,
    item_price TEXT,
    product_id TEXT,
    brand TEXT,
    sales_order_number TEXT,
    subscription_id TEXT,
    expense_reference_id TEXT,
    recurrence_name TEXT,
    
    -- Payment Gateways
    paypal TEXT,
    authorize_net TEXT,
    google_checkout TEXT,
    payflow_pro TEXT,
    stripe TEXT,
    paytm TEXT,
    two_checkout TEXT,
    braintree TEXT,
    forte TEXT,
    worldpay TEXT,
    payments_pro TEXT,
    square TEXT,
    wepay TEXT,
    razorpay TEXT,
    icici_eazypay TEXT,
    gocardless TEXT,
    partial_payments TEXT,
    
    -- Billing Address
    billing_attention TEXT,
    billing_address TEXT,
    billing_street2 TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_country TEXT,
    billing_code TEXT,
    billing_phone TEXT,
    billing_fax TEXT,
    
    -- Shipping Address
    shipping_attention TEXT,
    shipping_address TEXT,
    shipping_street2 TEXT,
    shipping_city TEXT,
    shipping_state TEXT,
    shipping_country TEXT,
    shipping_code TEXT,
    shipping_fax TEXT,
    shipping_phone_number TEXT,
    
    -- Tax Information
    tds_name TEXT,
    tds_percentage TEXT,
    tds_amount TEXT,
    tds_type TEXT,
    sku TEXT,
    
    -- Project Information
    project_id TEXT,
    project_name TEXT,
    round_off TEXT,
    
    -- Additional Fields
    sales_person TEXT,
    subject TEXT,
    primary_contact_email_id TEXT,
    primary_contact_mobile TEXT,
    primary_contact_phone TEXT,
    estimate_number TEXT,
    region TEXT,
    vehicle TEXT,
    custom_charges TEXT,
    shipping_bill_number TEXT,
    shipping_bill_date TEXT,
    shipping_bill_total TEXT,
    port_code TEXT,
    account TEXT,
    account_code TEXT,
    tax_id TEXT,
    item_tax TEXT,
    item_tax_percent TEXT,
    item_tax_amount TEXT,
    item_tax_type TEXT,
    kit_combo_item_name TEXT,
    item_cf_sku_category TEXT,
    cf_reason_to_void TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- ITEMS TABLE (42 columns)
-- ==================================================
CREATE TABLE csv_items (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    item_id TEXT PRIMARY KEY,
    item_name TEXT,
    sku TEXT,
    description TEXT,
    rate TEXT,
    account TEXT,
    account_code TEXT,
    tax_name TEXT,
    tax_percentage TEXT,
    tax_type TEXT,
    purchase_tax_name TEXT,
    purchase_tax_percentage TEXT,
    purchase_tax_type TEXT,
    product_type TEXT,
    source TEXT,
    reference_id TEXT,
    last_sync_time TEXT,
    status TEXT,
    usage_unit TEXT,
    purchase_rate TEXT,
    purchase_account TEXT,
    purchase_account_code TEXT,
    purchase_description TEXT,
    inventory_account TEXT,
    inventory_account_code TEXT,
    inventory_valuation_method TEXT,
    reorder_point TEXT,
    vendor TEXT,
    opening_stock TEXT,
    opening_stock_value TEXT,
    stock_on_hand TEXT,
    item_type TEXT,
    region TEXT,
    vehicle TEXT,
    cf_sku_category TEXT,
    cf_product_sale_category TEXT,
    cf_item_location TEXT,
    cf_product_category TEXT,
    cf_manufacturer TEXT,
    cf_m_box TEXT,
    cf_s_box_qty TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- CONTACTS TABLE (70 columns)
-- ==================================================
CREATE TABLE csv_contacts (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    contact_id TEXT PRIMARY KEY,
    created_time TEXT,
    last_modified_time TEXT,
    display_name TEXT,
    company_name TEXT,
    salutation TEXT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    currency_code TEXT,
    notes TEXT,
    website TEXT,
    status TEXT,
    accounts_receivable TEXT,
    opening_balance TEXT,
    opening_balance_exchange_rate TEXT,
    branch_id TEXT,
    branch_name TEXT,
    bank_account_payment TEXT,
    portal_enabled TEXT,
    credit_limit TEXT,
    customer_sub_type TEXT,
    
    -- Billing Address
    billing_attention TEXT,
    billing_address TEXT,
    billing_street2 TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_country TEXT,
    billing_county TEXT,
    billing_code TEXT,
    billing_phone TEXT,
    billing_fax TEXT,
    
    -- Shipping Address
    shipping_attention TEXT,
    shipping_address TEXT,
    shipping_street2 TEXT,
    shipping_city TEXT,
    shipping_state TEXT,
    shipping_country TEXT,
    shipping_county TEXT,
    shipping_code TEXT,
    shipping_phone TEXT,
    shipping_fax TEXT,
    
    -- Social and Professional
    skype_identity TEXT,
    facebook TEXT,
    twitter TEXT,
    department TEXT,
    designation TEXT,
    price_list TEXT,
    payment_terms TEXT,
    payment_terms_label TEXT,
    tax_type TEXT,
    track_tds TEXT,
    last_sync_time TEXT,
    owner_name TEXT,
    primary_contact_id TEXT,
    email_id TEXT,
    mobile_phone TEXT,
    contact_name TEXT,
    contact_type TEXT,
    taxable TEXT,
    tax_name TEXT,
    tax_percentage TEXT,
    contact_address_id TEXT,
    source TEXT,
    region TEXT,
    vehicle TEXT,
    siret TEXT,
    company_id TEXT,
    cf_market_region TEXT,
    cf_customer_category TEXT,
    cf_special_scheme_targets TEXT,
    cf_customer_sales_executive TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- BILLS TABLE (68 columns)
-- ==================================================
CREATE TABLE csv_bills (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    bill_id TEXT PRIMARY KEY,
    bill_date TEXT,
    due_date TEXT,
    accounts_payable TEXT,
    vendor_name TEXT,
    entity_discount_percent TEXT,
    payment_terms TEXT,
    payment_terms_label TEXT,
    bill_number TEXT,
    purchase_order TEXT,
    currency_code TEXT,
    exchange_rate TEXT,
    subtotal TEXT,
    total TEXT,
    balance TEXT,
    vendor_notes TEXT,
    terms_conditions TEXT,
    adjustment TEXT,
    adjustment_description TEXT,
    adjustment_account TEXT,
    bill_type TEXT,
    branch_id TEXT,
    branch_name TEXT,
    is_inclusive_tax TEXT,
    submitted_by TEXT,
    approved_by TEXT,
    submitted_date TEXT,
    approved_date TEXT,
    bill_status TEXT,
    created_by TEXT,
    product_id TEXT,
    item_name TEXT,
    account TEXT,
    account_code TEXT,
    description TEXT,
    quantity TEXT,
    usage_unit TEXT,
    tax_amount TEXT,
    item_total TEXT,
    is_billable TEXT,
    sku TEXT,
    rate TEXT,
    discount_type TEXT,
    is_discount_before_tax TEXT,
    discount TEXT,
    discount_amount TEXT,
    purchase_order_number TEXT,
    tax_id TEXT,
    tax_name TEXT,
    tax_percentage TEXT,
    tax_type TEXT,
    tds_name TEXT,
    tds_percentage TEXT,
    tds_amount TEXT,
    tds_type TEXT,
    entity_discount_amount TEXT,
    discount_account TEXT,
    discount_account_code TEXT,
    is_landed_cost TEXT,
    customer_name TEXT,
    project_name TEXT,
    region TEXT,
    vehicle TEXT,
    cf_chp_scheme_settlement_period TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- ORGANIZATIONS TABLE (62 columns) - Based on Vendors.csv
-- ==================================================
CREATE TABLE csv_organizations (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    contact_id TEXT PRIMARY KEY,
    created_time TEXT,
    last_modified_time TEXT,
    contact_name TEXT,
    company_name TEXT,
    display_name TEXT,
    salutation TEXT,
    first_name TEXT,
    last_name TEXT,
    email_id TEXT,
    phone TEXT,
    mobile_phone TEXT,
    payment_terms TEXT,
    currency_code TEXT,
    notes TEXT,
    website TEXT,
    status TEXT,
    opening_balance TEXT,
    branch_id TEXT,
    branch_name TEXT,
    accounts_payable TEXT,
    payment_terms_label TEXT,
    taxable TEXT,
    skype_identity TEXT,
    department TEXT,
    designation TEXT,
    facebook TEXT,
    twitter TEXT,
    track_tds TEXT,
    tds_name TEXT,
    tds_percentage TEXT,
    tds_type TEXT,
    price_list TEXT,
    tax_name TEXT,
    tax_percentage TEXT,
    tax_type TEXT,
    contact_address_id TEXT,
    
    -- Billing Address
    billing_attention TEXT,
    billing_address TEXT,
    billing_street2 TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_country TEXT,
    billing_code TEXT,
    billing_phone TEXT,
    billing_fax TEXT,
    
    -- Shipping Address
    shipping_attention TEXT,
    shipping_address TEXT,
    shipping_street2 TEXT,
    shipping_city TEXT,
    shipping_state TEXT,
    shipping_country TEXT,
    shipping_code TEXT,
    shipping_phone TEXT,
    shipping_fax TEXT,
    
    source TEXT,
    last_sync_time TEXT,
    region TEXT,
    vehicle TEXT,
    exchange_rate TEXT,
    owner_name TEXT,
    primary_contact_id TEXT,
    company_id TEXT,
    cf_market_region TEXT,
    cf_customer_category TEXT,
    cf_special_scheme_targets TEXT,
    cf_customer_sales_executive TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- CUSTOMER_PAYMENTS TABLE (29 columns)
-- ==================================================
CREATE TABLE csv_customer_payments (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    customer_payment_id TEXT PRIMARY KEY,
    payment_number TEXT,
    mode TEXT,
    customer_id TEXT,
    description TEXT,
    exchange_rate TEXT,
    amount TEXT,
    unused_amount TEXT,
    bank_charges TEXT,
    reference_number TEXT,
    currency_code TEXT,
    branch_id TEXT,
    payment_number_prefix TEXT,
    payment_number_suffix TEXT,
    customer_name TEXT,
    payment_type TEXT,
    branch_name TEXT,
    date TEXT,
    created_time TEXT,
    deposit_to TEXT,
    deposit_to_account_code TEXT,
    tax_account TEXT,
    invoice_payment_id TEXT,
    amount_applied_to_invoice TEXT,
    invoice_payment_applied_date TEXT,
    early_payment_discount TEXT,
    withholding_tax_amount TEXT,
    invoice_number TEXT,
    invoice_date TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- VENDOR_PAYMENTS TABLE (28 columns)
-- ==================================================
CREATE TABLE csv_vendor_payments (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    vendor_payment_id TEXT PRIMARY KEY,
    payment_number TEXT,
    payment_number_prefix TEXT,
    payment_number_suffix TEXT,
    mode TEXT,
    description TEXT,
    exchange_rate TEXT,
    amount TEXT,
    unused_amount TEXT,
    reference_number TEXT,
    currency_code TEXT,
    branch_id TEXT,
    payment_status TEXT,
    date TEXT,
    branch_name TEXT,
    vendor_name TEXT,
    email_id TEXT,
    paid_through TEXT,
    paid_through_account_code TEXT,
    tax_account TEXT,
    bank_reference_number TEXT,
    pi_payment_id TEXT,
    bill_amount TEXT,
    bill_payment_applied_date TEXT,
    bill_date TEXT,
    bill_number TEXT,
    withholding_tax_amount TEXT,
    withholding_tax_amount_bcy TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- SALES_ORDERS TABLE (84 columns)
-- ==================================================
CREATE TABLE csv_sales_orders (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    sales_order_id TEXT PRIMARY KEY,
    order_date TEXT,
    expected_shipment_date TEXT,
    sales_order_number TEXT,
    status TEXT,
    custom_status TEXT,
    customer_id TEXT,
    customer_name TEXT,
    branch_id TEXT,
    branch_name TEXT,
    is_inclusive_tax TEXT,
    reference_number TEXT,
    template_name TEXT,
    currency_code TEXT,
    exchange_rate TEXT,
    discount_type TEXT,
    is_discount_before_tax TEXT,
    entity_discount_amount TEXT,
    entity_discount_percent TEXT,
    item_name TEXT,
    product_id TEXT,
    sku TEXT,
    kit_combo_item_name TEXT,
    account TEXT,
    account_code TEXT,
    item_desc TEXT,
    quantity_ordered TEXT,
    quantity_invoiced TEXT,
    quantity_cancelled TEXT,
    usage_unit TEXT,
    item_price TEXT,
    discount TEXT,
    discount_amount TEXT,
    tax_id TEXT,
    item_tax TEXT,
    item_tax_percent TEXT,
    item_tax_amount TEXT,
    item_tax_type TEXT,
    tds_name TEXT,
    tds_percentage TEXT,
    tds_amount TEXT,
    tds_type TEXT,
    region TEXT,
    vehicle TEXT,
    project_id TEXT,
    project_name TEXT,
    item_total TEXT,
    subtotal TEXT,
    total TEXT,
    shipping_charge TEXT,
    shipping_charge_tax_id TEXT,
    shipping_charge_tax_amount TEXT,
    shipping_charge_tax_name TEXT,
    shipping_charge_tax_percent TEXT,
    shipping_charge_tax_type TEXT,
    adjustment TEXT,
    adjustment_description TEXT,
    sales_person TEXT,
    payment_terms TEXT,
    payment_terms_label TEXT,
    notes TEXT,
    terms_conditions TEXT,
    delivery_method TEXT,
    source TEXT,
    
    -- Billing Address
    billing_address TEXT,
    billing_street2 TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_country TEXT,
    billing_code TEXT,
    billing_fax TEXT,
    billing_phone TEXT,
    
    -- Shipping Address
    shipping_address TEXT,
    shipping_street2 TEXT,
    shipping_city TEXT,
    shipping_state TEXT,
    shipping_country TEXT,
    shipping_code TEXT,
    shipping_fax TEXT,
    shipping_phone TEXT,
    
    item_cf_sku_category TEXT,
    cf_region TEXT,
    cf_pending_items_delivery TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- PURCHASE_ORDERS TABLE (87 columns)
-- ==================================================
CREATE TABLE csv_purchase_orders (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    purchase_order_id TEXT PRIMARY KEY,
    purchase_order_date TEXT,
    branch_id TEXT,
    branch_name TEXT,
    delivery_date TEXT,
    purchase_order_number TEXT,
    reference_number TEXT,
    purchase_order_status TEXT,
    vendor_name TEXT,
    is_inclusive_tax TEXT,
    currency_code TEXT,
    exchange_rate TEXT,
    template_name TEXT,
    reference_no TEXT,
    delivery_instructions TEXT,
    terms_conditions TEXT,
    shipment_preference TEXT,
    expected_arrival_date TEXT,
    account TEXT,
    account_code TEXT,
    item_price TEXT,
    item_name TEXT,
    product_id TEXT,
    sku TEXT,
    item_desc TEXT,
    quantity_ordered TEXT,
    quantity_cancelled TEXT,
    quantity_received TEXT,
    quantity_billed TEXT,
    usage_unit TEXT,
    discount_type TEXT,
    is_discount_before_tax TEXT,
    discount TEXT,
    discount_amount TEXT,
    tax_id TEXT,
    item_tax TEXT,
    item_tax_percent TEXT,
    item_tax_amount TEXT,
    item_tax_type TEXT,
    item_total TEXT,
    total TEXT,
    adjustment TEXT,
    adjustment_description TEXT,
    entity_discount_percent TEXT,
    entity_discount_amount TEXT,
    discount_account TEXT,
    discount_account_code TEXT,
    tds_name TEXT,
    tds_percentage TEXT,
    tds_amount TEXT,
    tds_type TEXT,
    region TEXT,
    vehicle TEXT,
    project_id TEXT,
    project_name TEXT,
    payment_terms TEXT,
    payment_terms_label TEXT,
    attention TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    code TEXT,
    phone TEXT,
    deliver_to_customer TEXT,
    recipient_address TEXT,
    recipient_city TEXT,
    recipient_state TEXT,
    recipient_country TEXT,
    recipient_postal_code TEXT,
    recipient_phone TEXT,
    submitted_by TEXT,
    approved_by TEXT,
    submitted_date TEXT,
    approved_date TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- CREDIT_NOTES TABLE (81 columns)
-- ==================================================
CREATE TABLE csv_credit_notes (
    -- System Fields
    created_timestamp TEXT DEFAULT (datetime('now')),
    updated_timestamp TEXT DEFAULT (datetime('now')),
    
    credit_notes_id TEXT PRIMARY KEY,
    credit_note_date TEXT,
    product_id TEXT,
    credit_note_number TEXT,
    credit_note_status TEXT,
    accounts_receivable TEXT,
    customer_name TEXT,
    
    -- Billing Address
    billing_attention TEXT,
    billing_address TEXT,
    billing_street_2 TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_country TEXT,
    billing_code TEXT,
    billing_phone TEXT,
    billing_fax TEXT,
    
    -- Shipping Address
    shipping_attention TEXT,
    shipping_address TEXT,
    shipping_street_2 TEXT,
    shipping_city TEXT,
    shipping_state TEXT,
    shipping_country TEXT,
    shipping_phone TEXT,
    shipping_code TEXT,
    shipping_fax TEXT,
    
    customer_id TEXT,
    currency_code TEXT,
    exchange_rate TEXT,
    is_inclusive_tax TEXT,
    total TEXT,
    balance TEXT,
    entity_discount_percent TEXT,
    notes TEXT,
    terms_conditions TEXT,
    reference_number TEXT,
    shipping_charge TEXT,
    shipping_charge_tax_id TEXT,
    shipping_charge_tax_amount TEXT,
    shipping_charge_tax_name TEXT,
    shipping_charge_tax_percent TEXT,
    shipping_charge_tax_type TEXT,
    shipping_charge_account TEXT,
    adjustment TEXT,
    adjustment_account TEXT,
    branch_id TEXT,
    is_discount_before_tax TEXT,
    item_name TEXT,
    discount TEXT,
    discount_amount TEXT,
    quantity TEXT,
    item_desc TEXT,
    item_tax_amount TEXT,
    item_total TEXT,
    applied_invoice_number TEXT,
    branch_name TEXT,
    project_id TEXT,
    project_name TEXT,
    tax1_id TEXT,
    item_tax TEXT,
    item_tax_percent TEXT,
    item_tax_type TEXT,
    tds_name TEXT,
    tds_percentage TEXT,
    tds_amount TEXT,
    tds_type TEXT,
    sales_person TEXT,
    discount_type TEXT,
    subtotal TEXT,
    round_off TEXT,
    adjustment_description TEXT,
    subject TEXT,
    template_name TEXT,
    usage_unit TEXT,
    item_price TEXT,
    account TEXT,
    account_code TEXT,
    sku TEXT,
    region TEXT,
    vehicle TEXT,
    entity_discount_amount TEXT,
    kit_combo_item_name TEXT,
    item_cf_sku_category TEXT,
    cf_region TEXT,
    cf_scheme_type TEXT,
    cf_scheme_settlement_period TEXT,
    cf_modified TEXT,
    cf_dispatch_incomplete_but_scheme_passed TEXT,
    
    -- Data Source Tracking
    data_source TEXT DEFAULT 'csv'
);

-- ==================================================
-- COMPLETION MESSAGE
-- ==================================================
-- Database schema creation completed successfully
-- Total tables created: 10
-- All CSV structures mirrored exactly
-- Indexes removed for simplicity
