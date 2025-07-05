"""
Canonical Schema and CSV-to-Canonical Mapping Definitions

This module contains the master CANONICAL_SCHEMA dictionary and CSV-to-canonical
mapping dictionaries for all 10 core Zoho Books entities. This serves as the
unchanging blueprint for the entire data pipeline.

Entities covered:
1. Invoices (with line items)
2. Items (standalone) 
3. Contacts (with contact persons)
4. Bills (with line items)
5. Organizations (standalone)
6. CustomerPayments (with invoice applications)
7. VendorPayments (with bill applications)
8. SalesOrders (with line items)
9. PurchaseOrders (with line items)
10. CreditNotes (with line items)

Author: Data Pipeline Team
Generated: Auto-generated from canonical schema development notebook
Version: 1.0.0
"""
# ============================================================================
# MAPPINGS UPDATE - 2025-07-05 16:42:43
# ============================================================================
# Added 469 additional CSV fields (likely custom fields)
# across 9 entities. Fields maintain original CSV names.
# Original backup: mappings_backup_2025-07-05_16-37-59.py
# ============================================================================



from typing import Dict, List, Optional, Any, Union

# ============================================================================
# CANONICAL_SCHEMA: Master Schema Definition for All 10 Entities
# ============================================================================

CANONICAL_SCHEMA = {
    'Invoices': {
        'header_table': 'Invoices',
        'primary_key': 'InvoiceID',
        'header_columns': {
            'InvoiceID': 'TEXT PRIMARY KEY',
            'InvoiceNumber': 'TEXT',
            'CustomerID': 'TEXT',
            'CustomerName': 'TEXT',
            'Date': 'TEXT',
            'DueDate': 'TEXT',
            'Status': 'TEXT',
            'SubTotal': 'REAL',
            'TaxTotal': 'REAL',
            'Total': 'REAL',
            'Balance': 'REAL',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'Notes': 'TEXT',
            'Terms': 'TEXT',
            'ReferenceNumber': 'TEXT',
            'SalesPersonName': 'TEXT',
            'BillingAddress': 'TEXT',
            'ShippingAddress': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'InvoiceLineItems',
        'line_item_pk': 'LineItemID',
        'foreign_key': 'InvoiceID',
        'line_items_columns': {
            'LineItemID': 'TEXT PRIMARY KEY',
            'InvoiceID': 'TEXT',
            'ItemID': 'TEXT',
            'ItemName': 'TEXT',
            'ItemDescription': 'TEXT',
            'SKU': 'TEXT',
            'Quantity': 'REAL',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            'ItemTotal': 'REAL',
            'DiscountAmount': 'REAL',
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'TaxType': 'TEXT',
            'ProjectID': 'TEXT',
            'ProjectName': 'TEXT',
        }
    },

    'Items': {
        'header_table': 'Items',
        'primary_key': 'ItemID',
        'header_columns': {
            'ItemID': 'TEXT PRIMARY KEY',
            'ItemName': 'TEXT',
            'SKU': 'TEXT',
            'ItemType': 'TEXT',
            'Category': 'TEXT',
            'Description': 'TEXT',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            'PurchaseRate': 'REAL',
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'PurchaseTaxID': 'TEXT',
            'PurchaseTaxName': 'TEXT',
            'PurchaseTaxPercentage': 'REAL',
            'InventoryAccountID': 'TEXT',
            'InventoryAccountName': 'TEXT',
            'AccountID': 'TEXT',
            'AccountName': 'TEXT',
            'PurchaseAccountID': 'TEXT',
            'PurchaseAccountName': 'TEXT',
            'IsActive': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': False,
        'line_items_table': None,
        'line_item_pk': None,
        'foreign_key': None,
        'line_items_columns': {
        }
    },

    'Contacts': {
        'header_table': 'Contacts',
        'primary_key': 'ContactID',
        'header_columns': {
            'ContactID': 'TEXT PRIMARY KEY',
            'ContactName': 'TEXT',
            'CompanyName': 'TEXT',
            'ContactType': 'TEXT',
            'Email': 'TEXT',
            'Phone': 'TEXT',
            'Mobile': 'TEXT',
            'Website': 'TEXT',
            'BillingAddress': 'TEXT',
            'ShippingAddress': 'TEXT',
            'CurrencyCode': 'TEXT',
            'PaymentTerms': 'TEXT',
            'CreditLimit': 'REAL',
            'VendorDisplayName': 'TEXT',
            'IsActive': 'TEXT',
            'Notes': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'ContactPersons',
        'line_item_pk': 'ContactPersonID',
        'foreign_key': 'ContactID',
        'line_items_columns': {
            'ContactPersonID': 'TEXT PRIMARY KEY',
            'ContactID': 'TEXT',
            'FirstName': 'TEXT',
            'LastName': 'TEXT',
            'Email': 'TEXT',
            'Phone': 'TEXT',
            'Mobile': 'TEXT',
            'Designation': 'TEXT',
            'Department': 'TEXT',
            'IsActive': 'TEXT',
        }
    },

    'Bills': {
        'header_table': 'Bills',
        'primary_key': 'BillID',
        'header_columns': {
            'BillID': 'TEXT PRIMARY KEY',
            'VendorID': 'TEXT',
            'VendorName': 'TEXT',
            'BillNumber': 'TEXT',
            'ReferenceNumber': 'TEXT',
            'Status': 'TEXT',
            'BillDate': 'TEXT',
            'DueDate': 'TEXT',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'SubTotal': 'REAL',
            'TaxTotal': 'REAL',
            'Total': 'REAL',
            'Balance': 'REAL',
            'Notes': 'TEXT',
            'Terms': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'BillLineItems',
        'line_item_pk': 'LineItemID',
        'foreign_key': 'BillID',
        'line_items_columns': {
            'LineItemID': 'TEXT PRIMARY KEY',
            'BillID': 'TEXT',
            'ItemID': 'TEXT',
            'ItemName': 'TEXT',
            'ItemDescription': 'TEXT',
            'SKU': 'TEXT',
            'Quantity': 'REAL',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            'ItemTotal': 'REAL',
            'AccountID': 'TEXT',
            'AccountName': 'TEXT',
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'TaxType': 'TEXT',
            'ProjectID': 'TEXT',
            'ProjectName': 'TEXT',
        }
    },

    'Organizations': {
        'header_table': 'Organizations',
        'primary_key': 'OrganizationID',
        'header_columns': {
            'OrganizationID': 'TEXT PRIMARY KEY',
            'OrganizationName': 'TEXT',
            'Email': 'TEXT',
            'Phone': 'TEXT',
            'Fax': 'TEXT',
            'Website': 'TEXT',
            'Address': 'TEXT',
            'City': 'TEXT',
            'State': 'TEXT',
            'Country': 'TEXT',
            'ZipCode': 'TEXT',
            'CurrencyCode': 'TEXT',
            'TimeZone': 'TEXT',
            'FiscalYearStart': 'TEXT',
            'TaxBasis': 'TEXT',
            'IsActive': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': False,
        'line_items_table': None,
        'line_item_pk': None,
        'foreign_key': None,
        'line_items_columns': {
        }
    },

    'CustomerPayments': {
        'header_table': 'CustomerPayments',
        'primary_key': 'PaymentID',
        'header_columns': {
            'PaymentID': 'TEXT PRIMARY KEY',
            'CustomerID': 'TEXT',
            'CustomerName': 'TEXT',
            'PaymentNumber': 'TEXT',
            'Date': 'TEXT',
            'PaymentMode': 'TEXT',
            'ReferenceNumber': 'TEXT',
            'Amount': 'REAL',
            'BankCharges': 'REAL',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'Description': 'TEXT',
            'Notes': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'InvoiceApplications',
        'line_item_pk': 'ApplicationID',
        'foreign_key': 'PaymentID',
        'line_items_columns': {
            'ApplicationID': 'TEXT PRIMARY KEY',
            'PaymentID': 'TEXT',
            'InvoiceID': 'TEXT',
            'InvoiceNumber': 'TEXT',
            'AmountApplied': 'REAL',
            'TaxAmountWithheld': 'REAL',
        }
    },

    'VendorPayments': {
        'header_table': 'VendorPayments',
        'primary_key': 'PaymentID',
        'header_columns': {
            'PaymentID': 'TEXT PRIMARY KEY',
            'VendorID': 'TEXT',
            'VendorName': 'TEXT',
            'PaymentNumber': 'TEXT',
            'Date': 'TEXT',
            'PaymentMode': 'TEXT',
            'ReferenceNumber': 'TEXT',
            'Amount': 'REAL',
            'BankCharges': 'REAL',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'Description': 'TEXT',
            'Notes': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'BillApplications',
        'line_item_pk': 'ApplicationID',
        'foreign_key': 'PaymentID',
        'line_items_columns': {
            'ApplicationID': 'TEXT PRIMARY KEY',
            'PaymentID': 'TEXT',
            'BillID': 'TEXT',
            'BillNumber': 'TEXT',
            'AmountApplied': 'REAL',
            'TaxAmountWithheld': 'REAL',
        }
    },

    'SalesOrders': {
        'header_table': 'SalesOrders',
        'primary_key': 'SalesOrderID',
        'header_columns': {
            'SalesOrderID': 'TEXT PRIMARY KEY',
            'SalesOrderNumber': 'TEXT',
            'CustomerID': 'TEXT',
            'CustomerName': 'TEXT',
            'Date': 'TEXT',
            'ExpectedShipmentDate': 'TEXT',
            'Status': 'TEXT',
            'SubTotal': 'REAL',
            'TaxTotal': 'REAL',
            'Total': 'REAL',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'Notes': 'TEXT',
            'Terms': 'TEXT',
            'BillingAddress': 'TEXT',
            'ShippingAddress': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'SalesOrderLineItems',
        'line_item_pk': 'LineItemID',
        'foreign_key': 'SalesOrderID',
        'line_items_columns': {
            'LineItemID': 'TEXT PRIMARY KEY',
            'SalesOrderID': 'TEXT',
            'ItemID': 'TEXT',
            'ItemName': 'TEXT',
            'ItemDescription': 'TEXT',
            'SKU': 'TEXT',
            'Quantity': 'REAL',
            'QuantityShipped': 'REAL',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            'ItemTotal': 'REAL',
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'TaxType': 'TEXT',
        }
    },

    'PurchaseOrders': {
        'header_table': 'PurchaseOrders',
        'primary_key': 'PurchaseOrderID',
        'header_columns': {
            'PurchaseOrderID': 'TEXT PRIMARY KEY',
            'PurchaseOrderNumber': 'TEXT',
            'VendorID': 'TEXT',
            'VendorName': 'TEXT',
            'Date': 'TEXT',
            'ExpectedDeliveryDate': 'TEXT',
            'Status': 'TEXT',
            'SubTotal': 'REAL',
            'TaxTotal': 'REAL',
            'Total': 'REAL',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'Notes': 'TEXT',
            'Terms': 'TEXT',
            'BillingAddress': 'TEXT',
            'DeliveryAddress': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'PurchaseOrderLineItems',
        'line_item_pk': 'LineItemID',
        'foreign_key': 'PurchaseOrderID',
        'line_items_columns': {
            'LineItemID': 'TEXT PRIMARY KEY',
            'PurchaseOrderID': 'TEXT',
            'ItemID': 'TEXT',
            'ItemName': 'TEXT',
            'ItemDescription': 'TEXT',
            'SKU': 'TEXT',
            'Quantity': 'REAL',
            'QuantityReceived': 'REAL',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            'ItemTotal': 'REAL',
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'TaxType': 'TEXT',
        }
    },

    'CreditNotes': {
        'header_table': 'CreditNotes',
        'primary_key': 'CreditNoteID',
        'header_columns': {
            'CreditNoteID': 'TEXT PRIMARY KEY',
            'CreditNoteNumber': 'TEXT',
            'CustomerID': 'TEXT',
            'CustomerName': 'TEXT',
            'Date': 'TEXT',
            'Status': 'TEXT',
            'SubTotal': 'REAL',
            'TaxTotal': 'REAL',
            'Total': 'REAL',
            'Balance': 'REAL',
            'CurrencyCode': 'TEXT',
            'ExchangeRate': 'REAL',
            'ReferenceNumber': 'TEXT',
            'Reason': 'TEXT',
            'Notes': 'TEXT',
            'Terms': 'TEXT',
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
        },
        'has_line_items': True,
        'line_items_table': 'CreditNoteLineItems',
        'line_item_pk': 'LineItemID',
        'foreign_key': 'CreditNoteID',
        'line_items_columns': {
            'LineItemID': 'TEXT PRIMARY KEY',
            'CreditNoteID': 'TEXT',
            'ItemID': 'TEXT',
            'ItemName': 'TEXT',
            'ItemDescription': 'TEXT',
            'SKU': 'TEXT',
            'Quantity': 'REAL',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            'ItemTotal': 'REAL',
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'TaxType': 'TEXT',
        }
    },

}


# ============================================================================
# CSV-to-Canonical Mapping Dictionaries
# ============================================================================

# Invoices CSV-to-Canonical Mapping
INVOICE_CSV_MAP = {
    'Invoice ID': 'InvoiceID',
    'Invoice Number': 'InvoiceNumber',
    'Customer ID': 'CustomerID',
    'Customer Name': 'CustomerName',
    'Invoice Date': 'Date',
    'Due Date': 'DueDate',
    'Status': 'Status',
    'Sub Total': 'SubTotal',
    'Tax Total': 'TaxTotal',
    'Total': 'Total',
    'Balance': 'Balance',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Notes': 'Notes',
    'Terms & Conditions': 'Terms',
    'Reference Number': 'ReferenceNumber',
    'Sales Person Name': 'SalesPersonName',
    'Billing Address': 'BillingAddress',
    'Shipping Address': 'ShippingAddress',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Line Item ID': 'LineItemID',
    'Item ID': 'ItemID',
    'Item Name': 'ItemName',
    'Item Description': 'ItemDescription',
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Rate': 'Rate',
    'Unit': 'Unit',
    'Item Total': 'ItemTotal',
    'Discount Amount': 'DiscountAmount',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage',
    'Tax Type': 'TaxType',
    'Project ID': 'ProjectID',
    'Project Name': 'ProjectName',

    # Additional fields from CSV analysis
    '2Checkout': '2Checkout',
    'Account': 'Account',
    'Account Code': 'Account Code',
    'Accounts Receivable': 'Accounts Receivable',
    'Adjustment': 'Adjustment',
    'Adjustment Account': 'Adjustment Account',
    'Adjustment Description': 'Adjustment Description',
    'Authorize.Net': 'Authorize.Net',
    'Billing Attention': 'Billing Attention',
    'Billing City': 'Billing City',
    'Billing Code': 'Billing Code',
    'Billing Country': 'Billing Country',
    'Billing Fax': 'Billing Fax',
    'Billing Phone': 'Billing Phone',
    'Billing State': 'Billing State',
    'Billing Street2': 'Billing Street2',
    'Braintree': 'Braintree',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'Brand': 'Brand',
    'CF.Reason to Void': 'CF.Reason to Void',
    'Company ID': 'Company ID',
    'Custom Charges': 'Custom Charges',
    'Discount': 'Discount',
    'Discount Type': 'Discount Type',
    'Early Payment Discount Amount': 'Early Payment Discount Amount',
    'Early Payment Discount Due Days': 'Early Payment Discount Due Days',
    'Early Payment Discount Percentage': 'Early Payment Discount Percentage',
    'Entity Discount Amount': 'Entity Discount Amount',
    'Entity Discount Percent': 'Entity Discount Percent',
    'Estimate Number': 'Estimate Number',
    'Expected Payment Date': 'Expected Payment Date',
    'Expense Reference ID': 'Expense Reference ID',
    'Forte': 'Forte',
    'GoCardless': 'GoCardless',
    'Google Checkout': 'Google Checkout',
    'ICICI EazyPay': 'ICICI EazyPay',
    'Invoice Status': 'Invoice Status',
    'Is Discount Before Tax': 'Is Discount Before Tax',
    'Is Inclusive Tax': 'Is Inclusive Tax',
    'Item Desc': 'Item Desc',
    'Item Price': 'Item Price',
    'Item Tax': 'Item Tax',
    'Item Tax %': 'Item Tax %',
    'Item Tax Amount': 'Item Tax Amount',
    'Item Tax Type': 'Item Tax Type',
    'Item.CF.SKU category': 'Item.CF.SKU category',
    'Kit Combo Item Name': 'Kit Combo Item Name',
    'Last Payment Date': 'Last Payment Date',
    'Partial Payments': 'Partial Payments',
    'PayPal': 'PayPal',
    'Payflow Pro': 'Payflow Pro',
    'Payment Terms': 'Payment Terms',
    'Payment Terms Label': 'Payment Terms Label',
    'Payments Pro': 'Payments Pro',
    'Paytm': 'Paytm',
    'PortCode': 'PortCode',
    'Primary Contact EmailID': 'Primary Contact EmailID',
    'Primary Contact Mobile': 'Primary Contact Mobile',
    'Primary Contact Phone': 'Primary Contact Phone',
    'Product ID': 'Product ID',
    'PurchaseOrder': 'PurchaseOrder',
    'Razorpay': 'Razorpay',
    'Recurrence Name': 'Recurrence Name',
    'Region': 'Region',
    'Round Off': 'Round Off',
    'Sales Order Number': 'Sales Order Number',
    'Sales person': 'Sales person',
    'Shipping Attention': 'Shipping Attention',
    'Shipping Bill Date': 'Shipping Bill Date',
    'Shipping Bill Total': 'Shipping Bill Total',
    'Shipping Bill#': 'Shipping Bill#',
    'Shipping Charge': 'Shipping Charge',
    'Shipping Charge Account': 'Shipping Charge Account',
    'Shipping Charge Tax %': 'Shipping Charge Tax %',
    'Shipping Charge Tax Amount': 'Shipping Charge Tax Amount',
    'Shipping Charge Tax ID': 'Shipping Charge Tax ID',
    'Shipping Charge Tax Name': 'Shipping Charge Tax Name',
    'Shipping Charge Tax Type': 'Shipping Charge Tax Type',
    'Shipping City': 'Shipping City',
    'Shipping Code': 'Shipping Code',
    'Shipping Country': 'Shipping Country',
    'Shipping Fax': 'Shipping Fax',
    'Shipping Phone Number': 'Shipping Phone Number',
    'Shipping State': 'Shipping State',
    'Shipping Street2': 'Shipping Street2',
    'Square': 'Square',
    'Stripe': 'Stripe',
    'SubTotal': 'SubTotal',
    'Subject': 'Subject',
    'TDS Amount': 'TDS Amount',
    'TDS Name': 'TDS Name',
    'TDS Percentage': 'TDS Percentage',
    'TDS Type': 'TDS Type',
    'Template Name': 'Template Name',
    'Usage unit': 'Usage unit',
    'Vehicle': 'Vehicle',
    'WePay': 'WePay',
    'WorldPay': 'WorldPay',
    'subscription_id': 'subscription_id',
}

# Items CSV-to-Canonical Mapping
ITEMS_CSV_MAP = {
    'Item ID': 'ItemID',
    'Item Name': 'ItemName',
    'SKU': 'SKU',
    'Item Type': 'ItemType',
    'Category': 'Category',
    'Description': 'Description',
    'Rate': 'Rate',
    'Unit': 'Unit',
    'Purchase Rate': 'PurchaseRate',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage',
    'Purchase Tax ID': 'PurchaseTaxID',
    'Purchase Tax Name': 'PurchaseTaxName',
    'Purchase Tax Percentage': 'PurchaseTaxPercentage',
    'Inventory Account ID': 'InventoryAccountID',
    'Inventory Account Name': 'InventoryAccountName',
    'Account ID': 'AccountID',
    'Account Name': 'AccountName',
    'Purchase Account ID': 'PurchaseAccountID',
    'Purchase Account Name': 'PurchaseAccountName',
    'Status': 'IsActive',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',

    # Additional fields from CSV analysis
    'Account': 'Account',
    'Account Code': 'Account Code',
    'CF.Item Location': 'CF.Item Location',
    'CF.M Box': 'CF.M Box',
    'CF.Manufacturer': 'CF.Manufacturer',
    'CF.Product Category': 'CF.Product Category',
    'CF.Product Sale Category': 'CF.Product Sale Category',
    'CF.S Box Qty': 'CF.S Box Qty',
    'CF.SKU category': 'CF.SKU category',
    'Inventory Account': 'Inventory Account',
    'Inventory Account Code': 'Inventory Account Code',
    'Inventory Valuation Method': 'Inventory Valuation Method',
    'Last Sync Time': 'Last Sync Time',
    'Opening Stock': 'Opening Stock',
    'Opening Stock Value': 'Opening Stock Value',
    'Product Type': 'Product Type',
    'Purchase Account': 'Purchase Account',
    'Purchase Account Code': 'Purchase Account Code',
    'Purchase Description': 'Purchase Description',
    'Purchase Tax Type': 'Purchase Tax Type',
    'Reference ID': 'Reference ID',
    'Region': 'Region',
    'Reorder Point': 'Reorder Point',
    'Source': 'Source',
    'Stock On Hand': 'Stock On Hand',
    'Tax Type': 'Tax Type',
    'Usage unit': 'Usage unit',
    'Vehicle': 'Vehicle',
    'Vendor': 'Vendor',
}

# Contacts CSV-to-Canonical Mapping
CONTACTS_CSV_MAP = {
    'Contact ID': 'ContactID',
    'Contact Name': 'ContactName',
    'Company Name': 'CompanyName',
    'Contact Type': 'ContactType',
    'Email': 'Email',
    'Phone': 'Phone',
    'Mobile': 'Mobile',
    'Website': 'Website',
    'Billing Address': 'BillingAddress',
    'Shipping Address': 'ShippingAddress',
    'Currency Code': 'CurrencyCode',
    'Payment Terms': 'PaymentTerms',
    'Credit Limit': 'CreditLimit',
    'Vendor Display Name': 'VendorDisplayName',
    'Status': 'IsActive',
    'Notes': 'Notes',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Contact Person ID': 'ContactPersonID',
    'First Name': 'FirstName',
    'Last Name': 'LastName',
    'Designation': 'Designation',
    'Department': 'Department',

    # Additional fields from CSV analysis
    'Accounts Receivable': 'Accounts Receivable',
    'Bank Account Payment': 'Bank Account Payment',
    'Billing Attention': 'Billing Attention',
    'Billing City': 'Billing City',
    'Billing Code': 'Billing Code',
    'Billing Country': 'Billing Country',
    'Billing County': 'Billing County',
    'Billing Fax': 'Billing Fax',
    'Billing Phone': 'Billing Phone',
    'Billing State': 'Billing State',
    'Billing Street2': 'Billing Street2',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'CF.Customer Category': 'CF.Customer Category',
    'CF.Customer Sales Executive': 'CF.Customer Sales Executive',
    'CF.Market Region': 'CF.Market Region',
    'CF.Special Scheme & Targets': 'CF.Special Scheme & Targets',
    'Company ID': 'Company ID',
    'Contact Address ID': 'Contact Address ID',
    'Customer Sub Type': 'Customer Sub Type',
    'Display Name': 'Display Name',
    'EmailID': 'EmailID',
    'Facebook': 'Facebook',
    'Last Sync Time': 'Last Sync Time',
    'MobilePhone': 'MobilePhone',
    'Opening Balance': 'Opening Balance',
    'Opening Balance Exchange Rate': 'Opening Balance Exchange Rate',
    'Owner Name': 'Owner Name',
    'Payment Terms Label': 'Payment Terms Label',
    'Portal Enabled': 'Portal Enabled',
    'Price List': 'Price List',
    'Primary Contact ID': 'Primary Contact ID',
    'Region': 'Region',
    'SIRET': 'SIRET',
    'Salutation': 'Salutation',
    'Shipping Attention': 'Shipping Attention',
    'Shipping City': 'Shipping City',
    'Shipping Code': 'Shipping Code',
    'Shipping Country': 'Shipping Country',
    'Shipping County': 'Shipping County',
    'Shipping Fax': 'Shipping Fax',
    'Shipping Phone': 'Shipping Phone',
    'Shipping State': 'Shipping State',
    'Shipping Street2': 'Shipping Street2',
    'Skype Identity': 'Skype Identity',
    'Source': 'Source',
    'Tax Name': 'Tax Name',
    'Tax Percentage': 'Tax Percentage',
    'Tax Type': 'Tax Type',
    'Taxable': 'Taxable',
    'Track TDS': 'Track TDS',
    'Twitter': 'Twitter',
    'Vehicle': 'Vehicle',
}

# Bills CSV-to-Canonical Mapping
BILLS_CSV_MAP = {
    'Bill ID': 'BillID',
    'Vendor ID': 'VendorID',
    'Vendor Name': 'VendorName',
    'Bill Number': 'BillNumber',
    'Reference Number': 'ReferenceNumber',
    'Status': 'Status',
    'Bill Date': 'BillDate',
    'Due Date': 'DueDate',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Sub Total': 'SubTotal',
    'Tax Total': 'TaxTotal',
    'Total': 'Total',
    'Balance': 'Balance',
    'Notes': 'Notes',
    'Terms & Conditions': 'Terms',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Line Item ID': 'LineItemID',
    'Item ID': 'ItemID',
    'Item Name': 'ItemName',
    'Item Description': 'ItemDescription',
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Rate': 'Rate',
    'Unit': 'Unit',
    'Item Total': 'ItemTotal',
    'Account ID': 'AccountID',
    'Account Name': 'AccountName',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage',
    'Tax Type': 'TaxType',
    'Project ID': 'ProjectID',
    'Project Name': 'ProjectName',

    # Additional fields from CSV analysis
    'Account': 'Account',
    'Account Code': 'Account Code',
    'Accounts Payable': 'Accounts Payable',
    'Adjustment': 'Adjustment',
    'Adjustment Account': 'Adjustment Account',
    'Adjustment Description': 'Adjustment Description',
    'Approved By': 'Approved By',
    'Approved Date': 'Approved Date',
    'Bill Status': 'Bill Status',
    'Bill Type': 'Bill Type',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'CF.ChP Scheme Settlement Period': 'CF.ChP Scheme Settlement Period',
    'Created By': 'Created By',
    'Customer Name': 'Customer Name',
    'Description': 'Description',
    'Discount': 'Discount',
    'Discount Account': 'Discount Account',
    'Discount Account Code': 'Discount Account Code',
    'Discount Amount': 'Discount Amount',
    'Discount Type': 'Discount Type',
    'Entity Discount Amount': 'Entity Discount Amount',
    'Entity Discount Percent': 'Entity Discount Percent',
    'Is Billable': 'Is Billable',
    'Is Discount Before Tax': 'Is Discount Before Tax',
    'Is Inclusive Tax': 'Is Inclusive Tax',
    'Is Landed Cost': 'Is Landed Cost',
    'Payment Terms': 'Payment Terms',
    'Payment Terms Label': 'Payment Terms Label',
    'Product ID': 'Product ID',
    'Purchase Order Number': 'Purchase Order Number',
    'PurchaseOrder': 'PurchaseOrder',
    'Region': 'Region',
    'SubTotal': 'SubTotal',
    'Submitted By': 'Submitted By',
    'Submitted Date': 'Submitted Date',
    'TDS Amount': 'TDS Amount',
    'TDS Name': 'TDS Name',
    'TDS Percentage': 'TDS Percentage',
    'TDS Type': 'TDS Type',
    'Tax Amount': 'Tax Amount',
    'Usage unit': 'Usage unit',
    'Vehicle': 'Vehicle',
    'Vendor Notes': 'Vendor Notes',
}

# CustomerPayments CSV-to-Canonical Mapping
CUSTOMER_PAYMENTS_CSV_MAP = {
    'Payment ID': 'PaymentID',
    'Customer ID': 'CustomerID',
    'Customer Name': 'CustomerName',
    'Payment Number': 'PaymentNumber',
    'Date': 'Date',
    'Payment Mode': 'PaymentMode',
    'Reference Number': 'ReferenceNumber',
    'Amount': 'Amount',
    'Bank Charges': 'BankCharges',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Description': 'Description',
    'Notes': 'Notes',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Application ID': 'ApplicationID',
    'Invoice ID': 'InvoiceID',
    'Invoice Number': 'InvoiceNumber',
    'Amount Applied': 'AmountApplied',
    'Tax Amount Withheld': 'TaxAmountWithheld',

    # Additional fields from CSV analysis
    'Amount Applied to Invoice': 'Amount Applied to Invoice',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'CustomerID': 'CustomerID',
    'CustomerPayment ID': 'CustomerPayment ID',
    'Deposit To': 'Deposit To',
    'Deposit To Account Code': 'Deposit To Account Code',
    'Early Payment Discount': 'Early Payment Discount',
    'Invoice Date': 'Invoice Date',
    'Invoice Payment Applied Date': 'Invoice Payment Applied Date',
    'InvoicePayment ID': 'InvoicePayment ID',
    'Mode': 'Mode',
    'Payment Number Prefix': 'Payment Number Prefix',
    'Payment Number Suffix': 'Payment Number Suffix',
    'Payment Type': 'Payment Type',
    'Tax Account': 'Tax Account',
    'Unused Amount': 'Unused Amount',
    'Withholding Tax Amount': 'Withholding Tax Amount',
}

# VendorPayments CSV-to-Canonical Mapping
VENDOR_PAYMENTS_CSV_MAP = {
    'Payment ID': 'PaymentID',
    'Vendor ID': 'VendorID',
    'Vendor Name': 'VendorName',
    'Payment Number': 'PaymentNumber',
    'Date': 'Date',
    'Payment Mode': 'PaymentMode',
    'Reference Number': 'ReferenceNumber',
    'Amount': 'Amount',
    'Bank Charges': 'BankCharges',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Description': 'Description',
    'Notes': 'Notes',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Application ID': 'ApplicationID',
    'Bill ID': 'BillID',
    'Bill Number': 'BillNumber',
    'Amount Applied': 'AmountApplied',
    'Tax Amount Withheld': 'TaxAmountWithheld',

    # Additional fields from CSV analysis
    'Bank Reference Number': 'Bank Reference Number',
    'Bill Amount': 'Bill Amount',
    'Bill Date': 'Bill Date',
    'Bill Payment Applied Date': 'Bill Payment Applied Date',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'EmailID': 'EmailID',
    'Mode': 'Mode',
    'PIPayment ID': 'PIPayment ID',
    'Paid Through': 'Paid Through',
    'Paid Through Account Code': 'Paid Through Account Code',
    'Payment Number Prefix': 'Payment Number Prefix',
    'Payment Number Suffix': 'Payment Number Suffix',
    'Payment Status': 'Payment Status',
    'Tax Account': 'Tax Account',
    'Unused Amount': 'Unused Amount',
    'VendorPayment ID': 'VendorPayment ID',
    'Withholding Tax Amount': 'Withholding Tax Amount',
    'Withholding Tax Amount (BCY)': 'Withholding Tax Amount (BCY)',
}

# SalesOrders CSV-to-Canonical Mapping
SALES_ORDERS_CSV_MAP = {
    'Sales Order ID': 'SalesOrderID',
    'Sales Order Number': 'SalesOrderNumber',
    'Customer ID': 'CustomerID',
    'Customer Name': 'CustomerName',
    'Date': 'Date',
    'Expected Shipment Date': 'ExpectedShipmentDate',
    'Status': 'Status',
    'Sub Total': 'SubTotal',
    'Tax Total': 'TaxTotal',
    'Total': 'Total',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Notes': 'Notes',
    'Terms & Conditions': 'Terms',
    'Billing Address': 'BillingAddress',
    'Shipping Address': 'ShippingAddress',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Line Item ID': 'LineItemID',
    'Item ID': 'ItemID',
    'Item Name': 'ItemName',
    'Item Description': 'ItemDescription',
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Quantity Shipped': 'QuantityShipped',
    'Rate': 'Rate',
    'Unit': 'Unit',
    'Item Total': 'ItemTotal',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage',
    'Tax Type': 'TaxType',

    # Additional fields from CSV analysis
    'Account': 'Account',
    'Account Code': 'Account Code',
    'Adjustment': 'Adjustment',
    'Adjustment Description': 'Adjustment Description',
    'Billing City': 'Billing City',
    'Billing Code': 'Billing Code',
    'Billing Country': 'Billing Country',
    'Billing Fax': 'Billing Fax',
    'Billing Phone': 'Billing Phone',
    'Billing State': 'Billing State',
    'Billing Street2': 'Billing Street2',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'CF.Pending Items Delivery': 'CF.Pending Items Delivery',
    'CF.Region': 'CF.Region',
    'Custom Status': 'Custom Status',
    'Delivery Method': 'Delivery Method',
    'Discount': 'Discount',
    'Discount Amount': 'Discount Amount',
    'Discount Type': 'Discount Type',
    'Entity Discount Amount': 'Entity Discount Amount',
    'Entity Discount Percent': 'Entity Discount Percent',
    'Is Discount Before Tax': 'Is Discount Before Tax',
    'Is Inclusive Tax': 'Is Inclusive Tax',
    'Item Desc': 'Item Desc',
    'Item Price': 'Item Price',
    'Item Tax': 'Item Tax',
    'Item Tax %': 'Item Tax %',
    'Item Tax Amount': 'Item Tax Amount',
    'Item Tax Type': 'Item Tax Type',
    'Item.CF.SKU category': 'Item.CF.SKU category',
    'Kit Combo Item Name': 'Kit Combo Item Name',
    'Order Date': 'Order Date',
    'Payment Terms': 'Payment Terms',
    'Payment Terms Label': 'Payment Terms Label',
    'Product ID': 'Product ID',
    'Project ID': 'Project ID',
    'Project Name': 'Project Name',
    'QuantityCancelled': 'QuantityCancelled',
    'QuantityInvoiced': 'QuantityInvoiced',
    'QuantityOrdered': 'QuantityOrdered',
    'Reference#': 'Reference#',
    'Region': 'Region',
    'Sales person': 'Sales person',
    'SalesOrder ID': 'SalesOrder ID',
    'SalesOrder Number': 'SalesOrder Number',
    'Shipping Charge': 'Shipping Charge',
    'Shipping Charge Tax %': 'Shipping Charge Tax %',
    'Shipping Charge Tax Amount': 'Shipping Charge Tax Amount',
    'Shipping Charge Tax ID': 'Shipping Charge Tax ID',
    'Shipping Charge Tax Name': 'Shipping Charge Tax Name',
    'Shipping Charge Tax Type': 'Shipping Charge Tax Type',
    'Shipping City': 'Shipping City',
    'Shipping Code': 'Shipping Code',
    'Shipping Country': 'Shipping Country',
    'Shipping Fax': 'Shipping Fax',
    'Shipping Phone': 'Shipping Phone',
    'Shipping State': 'Shipping State',
    'Shipping Street2': 'Shipping Street2',
    'Source': 'Source',
    'SubTotal': 'SubTotal',
    'TDS Amount': 'TDS Amount',
    'TDS Name': 'TDS Name',
    'TDS Percentage': 'TDS Percentage',
    'TDS Type': 'TDS Type',
    'Template Name': 'Template Name',
    'Usage unit': 'Usage unit',
    'Vehicle': 'Vehicle',
}

# PurchaseOrders CSV-to-Canonical Mapping
PURCHASE_ORDERS_CSV_MAP = {
    'Purchase Order ID': 'PurchaseOrderID',
    'Purchase Order Number': 'PurchaseOrderNumber',
    'Vendor ID': 'VendorID',
    'Vendor Name': 'VendorName',
    'Date': 'Date',
    'Expected Delivery Date': 'ExpectedDeliveryDate',
    'Status': 'Status',
    'Sub Total': 'SubTotal',
    'Tax Total': 'TaxTotal',
    'Total': 'Total',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Notes': 'Notes',
    'Terms & Conditions': 'Terms',
    'Billing Address': 'BillingAddress',
    'Delivery Address': 'DeliveryAddress',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Line Item ID': 'LineItemID',
    'Item ID': 'ItemID',
    'Item Name': 'ItemName',
    'Item Description': 'ItemDescription',
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Quantity Received': 'QuantityReceived',
    'Rate': 'Rate',
    'Unit': 'Unit',
    'Item Total': 'ItemTotal',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage',
    'Tax Type': 'TaxType',

    # Additional fields from CSV analysis
    'Account': 'Account',
    'Account Code': 'Account Code',
    'Address': 'Address',
    'Adjustment': 'Adjustment',
    'Adjustment Description': 'Adjustment Description',
    'Approved By': 'Approved By',
    'Approved Date': 'Approved Date',
    'Attention': 'Attention',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'City': 'City',
    'Code': 'Code',
    'Country': 'Country',
    'Deliver To Customer': 'Deliver To Customer',
    'Delivery Date': 'Delivery Date',
    'Delivery Instructions': 'Delivery Instructions',
    'Discount': 'Discount',
    'Discount Account': 'Discount Account',
    'Discount Account Code': 'Discount Account Code',
    'Discount Amount': 'Discount Amount',
    'Discount Type': 'Discount Type',
    'Entity Discount Amount': 'Entity Discount Amount',
    'Entity Discount Percent': 'Entity Discount Percent',
    'Expected Arrival Date': 'Expected Arrival Date',
    'Is Discount Before Tax': 'Is Discount Before Tax',
    'Is Inclusive Tax': 'Is Inclusive Tax',
    'Item Desc': 'Item Desc',
    'Item Price': 'Item Price',
    'Item Tax': 'Item Tax',
    'Item Tax %': 'Item Tax %',
    'Item Tax Amount': 'Item Tax Amount',
    'Item Tax Type': 'Item Tax Type',
    'Payment Terms': 'Payment Terms',
    'Payment Terms Label': 'Payment Terms Label',
    'Phone': 'Phone',
    'Product ID': 'Product ID',
    'Project ID': 'Project ID',
    'Project Name': 'Project Name',
    'Purchase Order Date': 'Purchase Order Date',
    'Purchase Order Status': 'Purchase Order Status',
    'QuantityBilled': 'QuantityBilled',
    'QuantityCancelled': 'QuantityCancelled',
    'QuantityOrdered': 'QuantityOrdered',
    'QuantityReceived': 'QuantityReceived',
    'Recipient Address': 'Recipient Address',
    'Recipient City': 'Recipient City',
    'Recipient Country': 'Recipient Country',
    'Recipient Phone': 'Recipient Phone',
    'Recipient Postal Code': 'Recipient Postal Code',
    'Recipient State': 'Recipient State',
    'Reference No': 'Reference No',
    'Reference#': 'Reference#',
    'Region': 'Region',
    'Shipment preference': 'Shipment preference',
    'State': 'State',
    'Submitted By': 'Submitted By',
    'Submitted Date': 'Submitted Date',
    'TDS Amount': 'TDS Amount',
    'TDS Name': 'TDS Name',
    'TDS Percentage': 'TDS Percentage',
    'TDS Type': 'TDS Type',
    'Template Name': 'Template Name',
    'Usage unit': 'Usage unit',
    'Vehicle': 'Vehicle',
}

# CreditNotes CSV-to-Canonical Mapping
CREDIT_NOTES_CSV_MAP = {
    'Credit Note ID': 'CreditNoteID',
    'Credit Note Number': 'CreditNoteNumber',
    'Customer ID': 'CustomerID',
    'Customer Name': 'CustomerName',
    'Date': 'Date',
    'Status': 'Status',
    'Sub Total': 'SubTotal',
    'Tax Total': 'TaxTotal',
    'Total': 'Total',
    'Balance': 'Balance',
    'Currency Code': 'CurrencyCode',
    'Exchange Rate': 'ExchangeRate',
    'Reference Number': 'ReferenceNumber',
    'Reason': 'Reason',
    'Notes': 'Notes',
    'Terms & Conditions': 'Terms',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    'Line Item ID': 'LineItemID',
    'Item ID': 'ItemID',
    'Item Name': 'ItemName',
    'Item Description': 'ItemDescription',
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Rate': 'Rate',
    'Unit': 'Unit',
    'Item Total': 'ItemTotal',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage',
    'Tax Type': 'TaxType',

    # Additional fields from CSV analysis
    'Account': 'Account',
    'Account Code': 'Account Code',
    'Accounts Receivable': 'Accounts Receivable',
    'Adjustment': 'Adjustment',
    'Adjustment Account': 'Adjustment Account',
    'Adjustment Description': 'Adjustment Description',
    'Applied Invoice Number': 'Applied Invoice Number',
    'Billing Address': 'Billing Address',
    'Billing Attention': 'Billing Attention',
    'Billing City': 'Billing City',
    'Billing Code': 'Billing Code',
    'Billing Country': 'Billing Country',
    'Billing Fax': 'Billing Fax',
    'Billing Phone': 'Billing Phone',
    'Billing State': 'Billing State',
    'Billing Street 2': 'Billing Street 2',
    'Branch ID': 'Branch ID',
    'Branch Name': 'Branch Name',
    'CF.Dispatch Incomplete but Scheme Passed': 'CF.Dispatch Incomplete but Scheme Passed',
    'CF.Modified': 'CF.Modified',
    'CF.Region': 'CF.Region',
    'CF.Scheme Settlement Period': 'CF.Scheme Settlement Period',
    'CF.Scheme Type': 'CF.Scheme Type',
    'Credit Note Date': 'Credit Note Date',
    'Credit Note Status': 'Credit Note Status',
    'CreditNotes ID': 'CreditNotes ID',
    'Discount': 'Discount',
    'Discount Amount': 'Discount Amount',
    'Discount Type': 'Discount Type',
    'Entity Discount Amount': 'Entity Discount Amount',
    'Entity Discount Percent': 'Entity Discount Percent',
    'Is Discount Before Tax': 'Is Discount Before Tax',
    'Is Inclusive Tax': 'Is Inclusive Tax',
    'Item Desc': 'Item Desc',
    'Item Price': 'Item Price',
    'Item Tax': 'Item Tax',
    'Item Tax %': 'Item Tax %',
    'Item Tax Amount': 'Item Tax Amount',
    'Item Tax Type': 'Item Tax Type',
    'Item.CF.SKU category': 'Item.CF.SKU category',
    'Kit Combo Item Name': 'Kit Combo Item Name',
    'Product ID': 'Product ID',
    'Project ID': 'Project ID',
    'Project Name': 'Project Name',
    'Reference#': 'Reference#',
    'Region': 'Region',
    'Round Off': 'Round Off',
    'Sales person': 'Sales person',
    'Shipping Address': 'Shipping Address',
    'Shipping Attention': 'Shipping Attention',
    'Shipping Charge': 'Shipping Charge',
    'Shipping Charge Account': 'Shipping Charge Account',
    'Shipping Charge Tax %': 'Shipping Charge Tax %',
    'Shipping Charge Tax Amount': 'Shipping Charge Tax Amount',
    'Shipping Charge Tax ID': 'Shipping Charge Tax ID',
    'Shipping Charge Tax Name': 'Shipping Charge Tax Name',
    'Shipping Charge Tax Type': 'Shipping Charge Tax Type',
    'Shipping City': 'Shipping City',
    'Shipping Code': 'Shipping Code',
    'Shipping Country': 'Shipping Country',
    'Shipping Fax': 'Shipping Fax',
    'Shipping Phone': 'Shipping Phone',
    'Shipping State': 'Shipping State',
    'Shipping Street 2': 'Shipping Street 2',
    'SubTotal': 'SubTotal',
    'Subject': 'Subject',
    'TDS Amount': 'TDS Amount',
    'TDS Name': 'TDS Name',
    'TDS Percentage': 'TDS Percentage',
    'TDS Type': 'TDS Type',
    'Tax1 ID': 'Tax1 ID',
    'Template Name': 'Template Name',
    'Usage unit': 'Usage unit',
    'Vehicle': 'Vehicle',
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_entity_schema(entity_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the canonical schema for a specific entity.

    Args:
        entity_name: Name of the entity (e.g., 'Invoices', 'Bills')

    Returns:
        Dictionary containing the entity schema or None if not found
    """
    return CANONICAL_SCHEMA.get(entity_name)

def get_entity_csv_mapping(entity_name: str) -> Optional[Dict[str, str]]:
    """
    Get the CSV-to-canonical mapping for a specific entity.

    Args:
        entity_name: Name of the entity (e.g., 'Invoices', 'Bills')

    Returns:
        Dictionary containing CSV column to canonical column mappings
    """
    mapping_map = {
        'Invoices': INVOICE_CSV_MAP,
        'Items': ITEMS_CSV_MAP,
        'Contacts': CONTACTS_CSV_MAP,
        'Bills': BILLS_CSV_MAP,
        'CustomerPayments': CUSTOMER_PAYMENTS_CSV_MAP,
        'VendorPayments': VENDOR_PAYMENTS_CSV_MAP,
        'SalesOrders': SALES_ORDERS_CSV_MAP,
        'PurchaseOrders': PURCHASE_ORDERS_CSV_MAP,
        'CreditNotes': CREDIT_NOTES_CSV_MAP
    }
    return mapping_map.get(entity_name)

def get_all_entities() -> List[str]:
    """
    Get a list of all supported entity names.

    Returns:
        List of entity names
    """
    return list(CANONICAL_SCHEMA.keys())

def get_entities_with_line_items() -> List[str]:
    """
    Get a list of entities that have line items.

    Returns:
        List of entity names that have line items
    """
    return [
        entity_name for entity_name, config in CANONICAL_SCHEMA.items()
        if config['has_line_items']
    ]

def get_header_columns(entity_name: str) -> List[str]:
    """
    Get the header columns for a specific entity.

    Args:
        entity_name: Name of the entity

    Returns:
        List of header column names
    """
    schema = get_entity_schema(entity_name)
    return list(schema['header_columns'].keys()) if schema else []

def get_line_item_columns(entity_name: str) -> List[str]:
    """
    Get the line item columns for a specific entity.

    Args:
        entity_name: Name of the entity

    Returns:
        List of line item column names (empty if no line items)
    """
    schema = get_entity_schema(entity_name)
    if not schema:
        return []
    
    # Check if entity actually has line items before accessing line_items_columns
    if not schema.get('has_line_items', False):
        return []
    
    return list(schema.get('line_items_columns', {}).keys())

def validate_mapping_coverage(entity_name: str, csv_columns: List[str]) -> Dict[str, List[str]]:
    """
    Validate the mapping coverage for an entity's CSV columns.

    Args:
        entity_name: Name of the entity
        csv_columns: List of CSV column names

    Returns:
        Dictionary with 'mapped' and 'unmapped' lists
    """
    mapping = get_entity_csv_mapping(entity_name)
    if not mapping:
        return {'mapped': [], 'unmapped': csv_columns}

    mapped_columns = [col for col in csv_columns if col in mapping]
    unmapped_columns = [col for col in csv_columns if col not in mapping]

    return {
        'mapped': mapped_columns,
        'unmapped': unmapped_columns
    }

# ============================================================================
# Schema Statistics
# ============================================================================

def get_schema_statistics() -> Dict[str, Any]:
    """
    Get statistics about the canonical schema.

    Returns:
        Dictionary containing schema statistics
    """
    total_entities = len(CANONICAL_SCHEMA)
    entities_with_line_items = len(get_entities_with_line_items())
    entities_standalone = total_entities - entities_with_line_items

    total_header_columns = sum(
        len(config['header_columns']) for config in CANONICAL_SCHEMA.values()
    )
    total_line_item_columns = sum(
        len(config['line_items_columns']) for config in CANONICAL_SCHEMA.values()
    )

    return {
        'total_entities': total_entities,
        'entities_with_line_items': entities_with_line_items,
        'entities_standalone': entities_standalone,
        'total_header_columns': total_header_columns,
        'total_line_item_columns': total_line_item_columns,
        'total_columns': total_header_columns + total_line_item_columns
    }

# Module constants
__version__ = "1.0.0"
__all__ = [
    'CANONICAL_SCHEMA',
    'INVOICE_CSV_MAP',
    'ITEMS_CSV_MAP', 
    'CONTACTS_CSV_MAP',
    'BILLS_CSV_MAP',
    'CUSTOMER_PAYMENTS_CSV_MAP',
    'VENDOR_PAYMENTS_CSV_MAP',
    'SALES_ORDERS_CSV_MAP',
    'PURCHASE_ORDERS_CSV_MAP',
    'CREDIT_NOTES_CSV_MAP',
    'get_entity_schema',
    'get_entity_csv_mapping',
    'get_all_entities',
    'get_entities_with_line_items',
    'get_header_columns',
    'get_line_item_columns',
    'validate_mapping_coverage',
    'get_schema_statistics'
]
