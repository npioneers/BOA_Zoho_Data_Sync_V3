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
    return list(schema['line_items_columns'].keys()) if schema else []

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
