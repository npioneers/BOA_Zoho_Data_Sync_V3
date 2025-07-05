"""
JSON-to-Database Field Mappings

Independent mappings for JSON API data to database canonical schema.
These mappings are separate from CSV mappings and handle JSON field structures.

Configuration-driven design: All mappings externalized from application logic.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# JSON Entity to Database Table Mappings
JSON_ENTITY_MAPPINGS = {
    'items': {
        'json_endpoint': 'items',
        'database_table': 'Items',
        'primary_key_field': 'ItemID',
        'json_primary_key': 'item_id',
        'field_mappings': {
            'item_id': 'ItemID',
            'name': 'ItemName', 
            'description': 'Description',
            'rate': 'Rate',
            'sku': 'SKU',
            'item_type': 'ItemType',
            'category_name': 'CategoryName',
            'unit': 'Unit',
            'status': 'Status',
            'account_id': 'AccountID',
            'account_name': 'AccountName',
            'inventory_account_id': 'InventoryAccountID',
            'inventory_account_name': 'InventoryAccountName',
            'purchase_account_id': 'PurchaseAccountID',
            'purchase_account_name': 'PurchaseAccountName',
            'purchase_description': 'PurchaseDescription',
            'tax_id': 'TaxID',
            'tax_name': 'TaxName',
            'tax_percentage': 'TaxPercentage',
            'opening_stock': 'OpeningStock',
            'opening_stock_value': 'OpeningStockValue',
            'stock_on_hand': 'StockOnHand',
            'reorder_level': 'ReorderPoint',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },
    
    'contacts': {
        'json_endpoint': 'contacts',
        'database_table': 'Contacts',
        'primary_key_field': 'ContactID',
        'json_primary_key': 'contact_id',
        'field_mappings': {
            'contact_id': 'ContactID',
            'contact_name': 'ContactName',
            'company_name': 'CompanyName',
            'contact_type': 'ContactType',
            'customer_sub_type': 'CustomerSubType',
            'email': 'Email',
            'phone': 'Phone',
            'mobile': 'Mobile',
            'website': 'Website',
            'status': 'Status',
            'payment_terms': 'PaymentTerms',
            'currency_code': 'CurrencyCode',
            'outstanding_receivable_amount': 'OutstandingReceivableAmount',
            'outstanding_payable_amount': 'OutstandingPayableAmount',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'bills': {
        'json_endpoint': 'bills',
        'database_table': 'Bills',
        'primary_key_field': 'BillID',
        'json_primary_key': 'bill_id',
        'field_mappings': {
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
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'invoices': {
        'json_endpoint': 'invoices',
        'database_table': 'Invoices',
        'primary_key_field': 'InvoiceID',
        'json_primary_key': 'invoice_id',
        'field_mappings': {
            'invoice_id': 'InvoiceID',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'invoice_number': 'InvoiceNumber',
            'reference_number': 'ReferenceNumber',
            'date': 'Date',
            'due_date': 'DueDate',
            'payment_terms': 'PaymentTerms',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'balance': 'Balance',
            'is_inclusive_tax': 'IsInclusiveTax',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'salesorders': {
        'json_endpoint': 'salesorders',
        'database_table': 'SalesOrders',
        'primary_key_field': 'SalesOrderID',
        'json_primary_key': 'salesorder_id',
        'field_mappings': {
            'salesorder_id': 'SalesOrderID',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'salesorder_number': 'SalesOrderNumber',
            'reference_number': 'ReferenceNumber',
            'date': 'Date',
            'shipment_date': 'ShipmentDate',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'balance': 'Balance',
            'is_inclusive_tax': 'IsInclusiveTax',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'purchaseorders': {
        'json_endpoint': 'purchaseorders',
        'database_table': 'PurchaseOrders',
        'primary_key_field': 'PurchaseOrderID',
        'json_primary_key': 'purchaseorder_id',
        'field_mappings': {
            'purchaseorder_id': 'PurchaseOrderID',
            'vendor_id': 'VendorID',
            'vendor_name': 'VendorName',
            'purchaseorder_number': 'PurchaseOrderNumber',
            'reference_number': 'ReferenceNumber',
            'date': 'Date',
            'delivery_date': 'DeliveryDate',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'balance': 'Balance',
            'is_inclusive_tax': 'IsInclusiveTax',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'creditnotes': {
        'json_endpoint': 'creditnotes',
        'database_table': 'CreditNotes',
        'primary_key_field': 'CreditNoteID',
        'json_primary_key': 'creditnote_id',
        'field_mappings': {
            'creditnote_id': 'CreditNoteID',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'creditnote_number': 'CreditNoteNumber',
            'reference_number': 'ReferenceNumber',
            'date': 'Date',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'balance': 'Balance',
            'is_inclusive_tax': 'IsInclusiveTax',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'customerpayments': {
        'json_endpoint': 'customerpayments',
        'database_table': 'CustomerPayments',
        'primary_key_field': 'PaymentID',
        'json_primary_key': 'payment_id',
        'field_mappings': {
            'payment_id': 'PaymentID',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'payment_number': 'PaymentNumber',
            'date': 'Date',
            'payment_mode': 'PaymentMode',
            'amount': 'Amount',
            'unused_amount': 'UnusedAmount',
            'bank_charges': 'BankCharges',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'reference_number': 'ReferenceNumber',
            'description': 'Description',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    },

    'vendorpayments': {
        'json_endpoint': 'vendorpayments',
        'database_table': 'VendorPayments',
        'primary_key_field': 'PaymentID',
        'json_primary_key': 'payment_id',
        'field_mappings': {
            'payment_id': 'PaymentID',
            'vendor_id': 'VendorID',
            'vendor_name': 'VendorName',
            'payment_number': 'PaymentNumber',
            'date': 'Date',
            'payment_mode': 'PaymentMode',
            'amount': 'Amount',
            'unused_amount': 'UnusedAmount',
            'bank_charges': 'BankCharges',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'reference_number': 'ReferenceNumber',
            'description': 'Description',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    }
}

def get_json_mapping(entity_name: str) -> Dict[str, Any]:
    """
    Get JSON mapping configuration for an entity.
    
    Args:
        entity_name: Name of the entity (e.g., 'bills', 'invoices')
        
    Returns:
        Dictionary containing mapping configuration
        
    Raises:
        KeyError: If entity mapping not found
    """
    entity_key = entity_name.lower()
    
    if entity_key not in JSON_ENTITY_MAPPINGS:
        available = list(JSON_ENTITY_MAPPINGS.keys())
        raise KeyError(f"No JSON mapping found for entity '{entity_name}'. Available: {available}")
    
    logger.debug(f"Retrieved JSON mapping for entity: {entity_name}")
    return JSON_ENTITY_MAPPINGS[entity_key]

def get_field_mapping(entity_name: str) -> Dict[str, str]:
    """
    Get just the field mappings for an entity.
    
    Args:
        entity_name: Name of the entity
        
    Returns:
        Dictionary mapping JSON fields to database fields
    """
    mapping = get_json_mapping(entity_name)
    return mapping['field_mappings']

def get_primary_key_info(entity_name: str) -> tuple[str, str]:
    """
    Get primary key field names for an entity.
    
    Args:
        entity_name: Name of the entity
        
    Returns:
        Tuple of (json_primary_key, database_primary_key)
    """
    mapping = get_json_mapping(entity_name)
    return mapping['json_primary_key'], mapping['primary_key_field']
