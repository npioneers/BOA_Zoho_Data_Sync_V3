-- Complete Flattened Views Implementation
-- Generated on: 2025-07-08 11:13:23
-- This script creates flattened views and merged views

DROP VIEW IF EXISTS view_flat_json_bills;


        -- Flattened bills view (main + line items)
        CREATE VIEW IF NOT EXISTS view_flat_json_bills AS
        SELECT 
            m.bill_id,
            m.bill_number,
            m.vendor_name,
            m.vendor_id,
            m.total,
            m.balance,
            m.date,
            m.due_date,
            m.currency_code,
            li.line_item_id,
            li.item_id,
            li.name as line_item_name,
            li.quantity as line_item_quantity,
            li.rate as line_item_rate,
            li.item_total as line_item_item_total,
            li.account_name as line_item_account_name,
            li.description as line_item_description,
            li.unit as line_item_unit,
            li.tax_name as line_item_tax_name,
            li.tax_percentage as line_item_tax_percentage,
            'flattened' as data_source
        FROM json_bills m
        JOIN json_bills_line_items li ON m.bill_id = li.parent_id 
        WHERE li.parent_type = 'bill';
        

DROP VIEW IF EXISTS view_csv_json_bills;


        -- Merged bills view (CSV + flattened JSON)
        CREATE VIEW IF NOT EXISTS view_csv_json_bills AS
        SELECT 
            COALESCE(flat.bill_number, csv.bill_number) AS bill_number,
            COALESCE(flat.vendor_name, csv.vendor_name) AS vendor_name,
            COALESCE(flat.total, csv.total) AS total,
            COALESCE(flat.balance, csv.balance) AS balance,
            COALESCE(flat.date, csv.bill_date) AS bill_date,
            csv.account,
            csv.account_code,
            csv.accounts_payable,
            flat.vendor_id,
            flat.due_date,
            flat.currency_code,
            flat.line_item_name,
            flat.line_item_quantity,
            flat.line_item_rate,
            flat.line_item_item_total,
            flat.line_item_account_name,
            flat.line_item_description,
            flat.line_item_unit,
            flat.line_item_tax_name,
            flat.line_item_tax_percentage,
            CASE WHEN flat.bill_number IS NOT NULL THEN 'enhanced' ELSE 'csv_only' END AS data_source
        FROM csv_bills csv
        LEFT JOIN view_flat_json_bills flat ON csv.bill_number = flat.bill_number;
        

DROP VIEW IF EXISTS view_flat_json_invoices;


        -- Flattened invoices view (main + line items)
        CREATE VIEW IF NOT EXISTS view_flat_json_invoices AS
        SELECT 
            m.invoice_id,
            m.invoice_number,
            m.customer_name,
            m.customer_id,
            m.total,
            m.balance,
            m.date,
            m.due_date,
            m.status,
            li.line_item_id,
            li.item_id,
            li.name as line_item_name,
            li.quantity as line_item_quantity,
            li.rate as line_item_rate,
            li.item_total as line_item_item_total,
            li.account_name as line_item_account_name,
            li.description as line_item_description,
            li.unit as line_item_unit,
            li.tax_name as line_item_tax_name,
            li.tax_percentage as line_item_tax_percentage,
            'flattened' as data_source
        FROM json_invoices m
        JOIN json_invoices_line_items li ON m.invoice_id = li.parent_id 
        WHERE li.parent_type = 'invoice';
        

DROP VIEW IF EXISTS view_csv_json_invoices;


        -- Merged invoices view (CSV + flattened JSON)
        CREATE VIEW IF NOT EXISTS view_csv_json_invoices AS
        SELECT 
            COALESCE(flat.invoice_number, csv.invoice_number) AS invoice_number,
            COALESCE(flat.customer_name, csv.customer_name) AS customer_name,
            COALESCE(flat.total, csv.total) AS total,
            COALESCE(flat.balance, csv.balance) AS balance,
            COALESCE(flat.date, csv.invoice_date) AS invoice_date,
            COALESCE(flat.status, csv.invoice_status) AS invoice_status,
            csv.account,
            csv.account_code,
            csv.accounts_receivable,
            flat.customer_id,
            flat.due_date,
            flat.line_item_name,
            flat.line_item_quantity,
            flat.line_item_rate,
            flat.line_item_item_total,
            flat.line_item_account_name,
            flat.line_item_description,
            flat.line_item_unit,
            flat.line_item_tax_name,
            flat.line_item_tax_percentage,
            CASE WHEN flat.invoice_number IS NOT NULL THEN 'enhanced' ELSE 'csv_only' END AS data_source
        FROM csv_invoices csv
        LEFT JOIN view_flat_json_invoices flat ON csv.invoice_number = flat.invoice_number;
        

