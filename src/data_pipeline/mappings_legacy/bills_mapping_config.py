"""
Bills Mapping Configuration for Project Bedrock V3 - Normalized Schema

This module contains the normalized mapping configurations based exclusively on 
the official Zoho Books Bills API documentation. These configurations define the 
proper relational structure with separate Bills header and line items tables.

Based on: Zoho Books Bills API Documentation (https://www.zoho.com/books/api/v3/bills/)
Architecture: Normalized relational schema (Bills + Bills_LineItems tables)
Version: V3 - Normalized Schema Re-architecture
Date: 2025-07-05
"""

# �️ NORMALIZED CANONICAL SCHEMA - RELATIONAL STRUCTURE
# Based exclusively on Zoho Books Bills API documentation
# Separates Bills header from line items for proper normalization

CANONICAL_SCHEMA = {
    'bills_header': {
        'table_name': 'Bills',
        'primary_key': 'BillID',
        'columns': {
            # Core Bill Identity (from API: bill_id, vendor_id, vendor_name)
            'BillID': 'TEXT PRIMARY KEY',
            'VendorID': 'TEXT',
            'VendorName': 'TEXT',
            
            # Bill Document Info (from API: bill_number, reference_number, status)
            'BillNumber': 'TEXT',
            'ReferenceNumber': 'TEXT', 
            'Status': 'TEXT',
            
            # Bill Dates (from API: date, due_date, due_days)
            'Date': 'TEXT',
            'DueDate': 'TEXT',
            'DueDays': 'INTEGER',
            
            # Currency & Exchange (from API: currency_code, currency_id, exchange_rate)
            'CurrencyCode': 'TEXT',
            'CurrencyID': 'TEXT',
            'ExchangeRate': 'REAL',
            
            # Financial Totals (from API: sub_total, tax_total, total, balance)
            'SubTotal': 'REAL',
            'TaxTotal': 'REAL',
            'Total': 'REAL',
            'Balance': 'REAL',
            
            # Tax Settings (from API: is_inclusive_tax)
            'IsInclusiveTax': 'INTEGER',
            
            # Bill Content (from API: notes, terms)
            'Notes': 'TEXT',
            'Terms': 'TEXT',
            
            # Audit Trail (from API: created_time, last_modified_time)
            'CreatedTime': 'TEXT',
            'LastModifiedTime': 'TEXT',
            
            # Data Pipeline Metadata
            'DataSource': 'TEXT',
            'ProcessedTime': 'TEXT'
        }
    },
    
    'bills_line_items': {
        'table_name': 'Bills_LineItems',
        'primary_key': 'LineItemID',
        'foreign_key': {
            'column': 'BillID',
            'references': 'Bills(BillID)',
            'on_delete': 'CASCADE'
        },
        'columns': {
            # Line Item Identity (from API: line_item_id, item_id)
            'LineItemID': 'TEXT PRIMARY KEY',
            'BillID': 'TEXT',  # Foreign key to Bills table
            'ItemID': 'TEXT',
            
            # Item Details (from API: name, description, sku)
            'ItemName': 'TEXT',
            'ItemDescription': 'TEXT',
            'SKU': 'TEXT',
            
            # Quantities & Rates (from API: quantity, rate, unit)
            'Quantity': 'REAL',
            'Rate': 'REAL',
            'Unit': 'TEXT',
            
            # Line Item Financial (from API: item_total, bcy_rate)
            'ItemTotal': 'REAL',
            'BCYRate': 'REAL',
            
            # Account Assignment (from API: account_id, account_name)
            'AccountID': 'TEXT',
            'AccountName': 'TEXT',
            
            # Tax Information (from API: tax_id, tax_name, tax_percentage, tax_type)
            'TaxID': 'TEXT',
            'TaxName': 'TEXT',
            'TaxPercentage': 'REAL',
            'TaxType': 'TEXT',
            
            # Project Assignment (from API: project_id, project_name)
            'ProjectID': 'TEXT',
            'ProjectName': 'TEXT',
            
            # Line Item Order (from API: item_order)
            'ItemOrder': 'INTEGER',
            
            # Data Pipeline Metadata
            'DataSource': 'TEXT',
            'ProcessedTime': 'TEXT'
        }
    }
}

# 📋 HELPER FUNCTIONS FOR SCHEMA ACCESS
def get_bills_header_columns():
    """Get list of Bills header table column names"""
    return list(CANONICAL_SCHEMA['bills_header']['columns'].keys())

def get_bills_line_items_columns():
    """Get list of Bills line items table column names"""
    return list(CANONICAL_SCHEMA['bills_line_items']['columns'].keys())

def get_all_canonical_columns():
    """Get combined list of all canonical column names (for backward compatibility)"""
    return get_bills_header_columns() + get_bills_line_items_columns()

# 🔄 BACKWARD COMPATIBILITY - Legacy flat column list
# This maintains compatibility with existing code during transition
CANONICAL_BILLS_COLUMNS = get_all_canonical_columns()

# 📊 CSV BACKUP COLUMN MAPPING
# Maps CSV backup columns (PascalCase with spaces) to canonical schema
CSV_COLUMN_MAPPING = {
    # Bill header mappings
    'Bill ID': 'BillID',
    'Vendor ID': 'VendorID', 
    'Vendor Name': 'VendorName',
    'Bill Number': 'BillNumber',
    'Reference Number': 'ReferenceNumber',
    'Bill Date': 'Date',
    'Due Date': 'DueDate',
    'Total Amount': 'Total',
    'Status': 'Status',
    'Currency Code': 'CurrencyCode',
    'Created Time': 'CreatedTime',
    'Last Modified Time': 'LastModifiedTime',
    
    # Line item mappings
    'Line Item ID': 'LineItemID',
    'Item Name': 'ItemName',
    'Item Description': 'ItemDescription',
    'Quantity': 'Quantity',
    'Rate': 'Rate',
    'Amount': 'Amount',
    'Account ID': 'AccountID',
    'Account Name': 'AccountName',
    'Tax ID': 'TaxID',
    'Tax Name': 'TaxName',
    'Tax Percentage': 'TaxPercentage'
}

# 🌐 JSON API HEADER MAPPING  
# Maps JSON API bill header fields (snake_case) to canonical schema
JSON_HEADER_MAPPING = {
    'bill_id': 'BillID',
    'vendor_id': 'VendorID',
    'vendor_name': 'VendorName', 
    'bill_number': 'BillNumber',
    'reference_number': 'ReferenceNumber',
    'date': 'Date',
    'due_date': 'DueDate',
    'due_days': 'DueDays',
    'status': 'Status',
    'currency_code': 'CurrencyCode',
    'exchange_rate': 'ExchangeRate',
    'sub_total': 'SubTotal',
    'tax_total': 'TaxTotal',
    'total': 'Total',
    'balance': 'Balance',
    'is_inclusive_tax': 'IsInclusiveTax',
    'notes': 'Notes',
    'terms': 'Terms',
    'created_time': 'CreatedTime',
    'last_modified_time': 'LastModifiedTime'
}

# 📦 JSON API LINE ITEM MAPPING
# Maps JSON API line item fields (snake_case) to canonical schema
JSON_LINE_ITEM_MAPPING = {
    'line_item_id': 'LineItemID',
    'item_name': 'ItemName',
    'item_description': 'ItemDescription',
    'quantity': 'Quantity',
    'rate': 'Rate',
    'amount': 'Amount',
    'tax_total': 'LineItemTaxTotal',
    'account_id': 'AccountID',
    'account_name': 'AccountName',
    'tax_id': 'TaxID',
    'tax_name': 'TaxName',
    'tax_percentage': 'TaxPercentage'
}

# 🎯 DEFAULT VALUES FOR MISSING FIELDS
# Used to fill missing canonical fields during transformation
CANONICAL_FIELD_DEFAULTS = {
    'DueDays': '',
    'ExchangeRate': 1.0,
    'SubTotal': 0.0,
    'TaxTotal': 0.0,
    'Balance': 0.0,
    'IsInclusiveTax': 0,
    'Notes': '',
    'Terms': '',
    'ItemDescription': '',
    'LineItemTaxTotal': 0.0,
    'AccountID': '',
    'AccountName': '',
    'TaxID': '',
    'TaxName': '',
    'TaxPercentage': 0.0
}

# 📋 SCHEMA METADATA
SCHEMA_INFO = {
    'total_fields': len(CANONICAL_BILLS_COLUMNS),
    'bill_header_fields': 20,  # First 20 fields are bill headers
    'line_item_fields': 11,    # Last 11 fields are line item specific
    'source_documentation': 'ZOHO_API_DOCUMENTATION_COMPILED.md',
    'validation_date': '2025-07-05',
    'workbench_notebook': '1_mapping_workbench.ipynb'
}
