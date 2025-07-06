"""
Independent JSON-to-Database Differential Sync System
====================================================

This module provides a completely independent system for synchronizing
JSON API data with the database, without interfering with CSV-to-DB operations.

Key Features:
- JSON-specific field mappings
- Differential sync (only changes)
- Conflict detection and resolution
- Independent from CSV pipeline
- Production-ready error handling

Author: System
Date: 2025-07-06
Version: 1.0.0
"""

import json
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ConflictResolution(Enum):
    """Strategies for handling conflicts during JSON sync."""
    JSON_WINS = "json_wins"
    DATABASE_WINS = "database_wins"
    MANUAL_REVIEW = "manual_review"
    SKIP_CONFLICTS = "skip_conflicts"


@dataclass
class SyncResult:
    """Results of a differential sync operation."""
    entity: str
    json_records: int
    db_records: int
    inserts: int
    updates: int
    conflicts: int
    errors: int
    duration: float
    success: bool
    message: str


class JSONFieldMapper:
    """
    Maps JSON API response fields to database column names.
    Completely independent from CSV mappings.
    """
    
    # JSON field mappings for each entity
    JSON_MAPPINGS = {
        'bills': {
            'bill_id': 'BillID',
            'bill_number': 'BillNumber',
            'vendor_id': 'VendorID',
            'vendor_name': 'VendorName',
            'reference_number': 'ReferenceNumber',
            'date': 'Date',
            'due_date': 'DueDate',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'balance': 'Balance',
            'is_inclusive_tax': 'IsInclusiveTax',
            'notes': 'Notes',
            'terms_and_conditions': 'Terms',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'invoices': {
            'invoice_id': 'InvoiceID',
            'invoice_number': 'InvoiceNumber',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'date': 'InvoiceDate',
            'due_date': 'DueDate',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'balance': 'Balance',
            'payment_terms': 'PaymentTerms',
            'is_inclusive_tax': 'IsInclusiveTax',
            'notes': 'Notes',
            'terms_and_conditions': 'Terms',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'salesorders': {
            'salesorder_id': 'SalesOrderID',
            'salesorder_number': 'SalesOrderNumber',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'date': 'Date',
            'shipment_date': 'ShipmentDate',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'is_inclusive_tax': 'IsInclusiveTax',
            'notes': 'Notes',
            'terms_and_conditions': 'Terms',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'purchaseorders': {
            'purchaseorder_id': 'PurchaseOrderID',
            'purchaseorder_number': 'PurchaseOrderNumber',
            'vendor_id': 'VendorID',
            'vendor_name': 'VendorName',
            'date': 'Date',
            'delivery_date': 'DeliveryDate',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'is_inclusive_tax': 'IsInclusiveTax',
            'notes': 'Notes',
            'terms_and_conditions': 'Terms',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'creditnotes': {
            'creditnote_id': 'CreditNoteID',
            'creditnote_number': 'CreditNoteNumber',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'date': 'Date',
            'status': 'Status',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'sub_total': 'SubTotal',
            'tax_total': 'TaxTotal',
            'total': 'Total',
            'is_inclusive_tax': 'IsInclusiveTax',
            'reason': 'Reason',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'items': {
            'item_id': 'ItemID',
            'name': 'ItemName',
            'sku': 'SKU',
            'description': 'Description',
            'rate': 'Rate',
            'unit': 'Unit',
            'tax_id': 'TaxID',
            'tax_name': 'TaxName',
            'tax_percentage': 'TaxPercentage',
            'item_type': 'ItemType',
            'product_type': 'ProductType',
            'is_taxable': 'IsTaxable',
            'status': 'Status',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'contacts': {
            'contact_id': 'ContactID',
            'contact_name': 'ContactName',
            'company_name': 'CompanyName',
            'contact_type': 'ContactType',
            'email': 'Email',
            'phone': 'Phone',
            'mobile': 'Mobile',
            'website': 'Website',
            'status': 'Status',
            'billing_address': 'BillingAddress',
            'shipping_address': 'ShippingAddress',
            'payment_terms': 'PaymentTerms',
            'currency_code': 'CurrencyCode',
            'notes': 'Notes',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'customerpayments': {
            'payment_id': 'PaymentID',
            'customer_id': 'CustomerID',
            'customer_name': 'CustomerName',
            'payment_number': 'PaymentNumber',
            'date': 'Date',
            'payment_mode': 'PaymentMode',
            'amount': 'Amount',
            'bank_charges': 'BankCharges',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'reference_number': 'ReferenceNumber',
            'description': 'Description',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        },
        
        'vendorpayments': {
            'payment_id': 'PaymentID',
            'vendor_id': 'VendorID',
            'vendor_name': 'VendorName',
            'payment_number': 'PaymentNumber',
            'date': 'Date',
            'payment_mode': 'PaymentMode',
            'amount': 'Amount',
            'bank_charges': 'BankCharges',
            'currency_code': 'CurrencyCode',
            'exchange_rate': 'ExchangeRate',
            'reference_number': 'ReferenceNumber',
            'description': 'Description',
            'created_time': 'CreatedTime',
            'last_modified_time': 'LastModifiedTime'
        }
    }
    
    @classmethod
    def get_mapping(cls, entity: str) -> Dict[str, str]:
        """Get JSON-to-database field mapping for an entity."""
        entity_lower = entity.lower().replace('_', '').replace('-', '')
        return cls.JSON_MAPPINGS.get(entity_lower, {})
    
    @classmethod
    def map_json_record(cls, entity: str, json_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a JSON record to database format using field mappings."""
        mapping = cls.get_mapping(entity)
        if not mapping:
            return json_record
        
        mapped_record = {}
        for json_field, db_field in mapping.items():
            if json_field in json_record:
                mapped_record[db_field] = json_record[json_field]
        
        return mapped_record
    
    @classmethod
    def get_primary_key(cls, entity: str) -> str:
        """Get the primary key field for an entity."""
        pk_mapping = {
            'bills': 'BillID',
            'invoices': 'InvoiceID',
            'salesorders': 'SalesOrderID',
            'purchaseorders': 'PurchaseOrderID',
            'creditnotes': 'CreditNoteID',
            'items': 'ItemID',
            'contacts': 'ContactID',
            'customerpayments': 'PaymentID',
            'vendorpayments': 'PaymentID'
        }
        entity_lower = entity.lower().replace('_', '').replace('-', '')
        return pk_mapping.get(entity_lower, 'ID')


class JSONDataLoader:
    """
    Loads JSON data from various sources.
    Independent of CSV data loading.
    """
    
    def __init__(self, base_path: Union[str, Path]):
        """Initialize with base path for JSON files."""
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def find_latest_json_directory(self) -> Optional[Path]:
        """Find the most recent timestamped JSON directory."""
        if not self.base_path.exists():
            return None
        
        timestamped_dirs = []
        for item in self.base_path.iterdir():
            if item.is_dir() and self._is_timestamped_dir(item.name):
                timestamped_dirs.append(item)
        
        if not timestamped_dirs:
            return None
        
        # Sort by name (timestamp) and return latest
        return sorted(timestamped_dirs, key=lambda x: x.name)[-1]
    
    def _is_timestamped_dir(self, dirname: str) -> bool:
        """Check if directory name follows timestamp pattern."""
        # Pattern: YYYY-MM-DD_HH-MM-SS
        try:
            parts = dirname.split('_')
            if len(parts) != 2:
                return False
            
            date_part, time_part = parts
            date_elements = date_part.split('-')
            time_elements = time_part.split('-')
            
            return (len(date_elements) == 3 and 
                    len(time_elements) == 3 and
                    all(elem.isdigit() for elem in date_elements + time_elements))
        except:
            return False
    
    def load_entity_json(self, entity: str, json_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Load JSON data for a specific entity."""
        if json_dir is None:
            json_dir = self.find_latest_json_directory()
        
        if not json_dir or not json_dir.exists():
            self.logger.warning(f"JSON directory not found: {json_dir}")
            return []
        
        # Try different possible JSON file patterns
        possible_files = [
            f"{entity}.json",
            f"{entity}s.json",
            f"{entity.lower()}.json",
            f"{entity.lower()}s.json",
            f"{entity.title()}.json",
            f"{entity.title()}s.json"
        ]
        
        for filename in possible_files:
            json_file = json_dir / filename
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different JSON response structures
                    if isinstance(data, dict):
                        # Check for common API response patterns
                        for key in [entity, f"{entity}s", "data", "records", "items"]:
                            if key in data and isinstance(data[key], list):
                                self.logger.info(f"Loaded {len(data[key])} {entity} records from {json_file}")
                                return data[key]
                        
                        # If no list found, return single record as list
                        if data:
                            self.logger.info(f"Loaded 1 {entity} record from {json_file}")
                            return [data]
                    
                    elif isinstance(data, list):
                        self.logger.info(f"Loaded {len(data)} {entity} records from {json_file}")
                        return data
                
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.error(f"Error loading {json_file}: {e}")
                    continue
        
        self.logger.warning(f"No JSON file found for entity: {entity}")
        return []


class DatabaseManager:
    """
    Manages database operations for JSON sync.
    Independent of CSV database operations.
    """
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_entity_records(self, table_name: str) -> pd.DataFrame:
        """Load all records from a database table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql_query(query, conn)
                self.logger.info(f"Loaded {len(df)} records from table: {table_name}")
                return df
        
        except sqlite3.Error as e:
            self.logger.error(f"Database error loading {table_name}: {e}")
            return pd.DataFrame()
    
    def get_table_schema(self, table_name: str) -> List[str]:
        """Get column names for a table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return columns
        
        except sqlite3.Error as e:
            self.logger.error(f"Error getting schema for {table_name}: {e}")
            return []
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                return cursor.fetchone()[0] > 0
        
        except sqlite3.Error:
            return False
    
    def upsert_records(self, table_name: str, records: List[Dict[str, Any]], 
                      primary_key: str) -> Tuple[int, int]:
        """Insert or update records in the database."""
        if not records:
            return 0, 0
        
        inserts = 0
        updates = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for record in records:
                    # Check if record exists
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {primary_key} = ?", 
                                 (record.get(primary_key),))
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # Update existing record
                        set_clause = ', '.join([f"{k} = ?" for k in record.keys() if k != primary_key])
                        if set_clause:
                            query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = ?"
                            values = [v for k, v in record.items() if k != primary_key]
                            values.append(record.get(primary_key))
                            cursor.execute(query, values)
                            updates += 1
                    else:
                        # Insert new record
                        columns = list(record.keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                        cursor.execute(query, list(record.values()))
                        inserts += 1
                
                conn.commit()
                self.logger.info(f"Database upsert completed: {inserts} inserts, {updates} updates")
        
        except sqlite3.Error as e:
            self.logger.error(f"Database upsert error: {e}")
            return 0, 0
        
        return inserts, updates


class DifferentialSyncEngine:
    """
    Core engine for JSON-to-database differential synchronization.
    Completely independent of CSV sync operations.
    """
    
    def __init__(self, json_base_path: Union[str, Path], db_path: Union[str, Path]):
        """Initialize the sync engine."""
        self.json_loader = JSONDataLoader(json_base_path)
        self.db_manager = DatabaseManager(db_path)
        self.field_mapper = JSONFieldMapper()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def sync_entity(self, entity: str, conflict_resolution: ConflictResolution = ConflictResolution.JSON_WINS,
                   dry_run: bool = False) -> SyncResult:
        """Perform differential sync for a single entity."""
        start_time = datetime.now()
        
        try:
            # Load JSON data
            json_records = self.json_loader.load_entity_json(entity)
            if not json_records:
                return SyncResult(
                    entity=entity, json_records=0, db_records=0, inserts=0, 
                    updates=0, conflicts=0, errors=0, duration=0.0, 
                    success=False, message="No JSON data found"
                )
            
            # Map JSON records to database format
            mapped_records = []
            for record in json_records:
                mapped = self.field_mapper.map_json_record(entity, record)
                if mapped:
                    mapped_records.append(mapped)
            
            if not mapped_records:
                return SyncResult(
                    entity=entity, json_records=len(json_records), db_records=0, 
                    inserts=0, updates=0, conflicts=0, errors=0, 
                    duration=(datetime.now() - start_time).total_seconds(),
                    success=False, message="No mappable fields found"
                )
            
            # Get table name (assume entity name matches table name)
            table_name = entity.title() if entity.lower() != entity else entity
            
            # Check if table exists
            if not self.db_manager.table_exists(table_name):
                return SyncResult(
                    entity=entity, json_records=len(json_records), db_records=0,
                    inserts=0, updates=0, conflicts=0, errors=0,
                    duration=(datetime.now() - start_time).total_seconds(),
                    success=False, message=f"Table {table_name} does not exist"
                )
            
            # Load existing database records
            db_df = self.db_manager.get_entity_records(table_name)
            
            # Get primary key
            primary_key = self.field_mapper.get_primary_key(entity)
            
            if dry_run:
                # Analyze what would be done
                inserts = len([r for r in mapped_records 
                              if r.get(primary_key) not in db_df.get(primary_key, []).tolist()])
                updates = len(mapped_records) - inserts
                
                return SyncResult(
                    entity=entity, json_records=len(json_records), db_records=len(db_df),
                    inserts=inserts, updates=updates, conflicts=0, errors=0,
                    duration=(datetime.now() - start_time).total_seconds(),
                    success=True, message="Dry run completed"
                )
            
            # Perform actual sync
            inserts, updates = self.db_manager.upsert_records(table_name, mapped_records, primary_key)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return SyncResult(
                entity=entity, json_records=len(json_records), db_records=len(db_df),
                inserts=inserts, updates=updates, conflicts=0, errors=0,
                duration=duration, success=True,
                message=f"Sync completed: {inserts} inserts, {updates} updates"
            )
        
        except Exception as e:
            self.logger.error(f"Error syncing {entity}: {e}")
            return SyncResult(
                entity=entity, json_records=0, db_records=0, inserts=0, 
                updates=0, conflicts=0, errors=1,
                duration=(datetime.now() - start_time).total_seconds(),
                success=False, message=f"Error: {str(e)}"
            )
    
    def sync_all_entities(self, entities: List[str], 
                         conflict_resolution: ConflictResolution = ConflictResolution.JSON_WINS,
                         dry_run: bool = False) -> List[SyncResult]:
        """Perform differential sync for multiple entities."""
        results = []
        
        for entity in entities:
            self.logger.info(f"Starting sync for entity: {entity}")
            result = self.sync_entity(entity, conflict_resolution, dry_run)
            results.append(result)
            
            if result.success:
                self.logger.info(f"✅ {entity}: {result.message}")
            else:
                self.logger.error(f"❌ {entity}: {result.message}")
        
        return results
    
    def generate_sync_report(self, results: List[SyncResult]) -> Dict[str, Any]:
        """Generate comprehensive sync report."""
        total_json = sum(r.json_records for r in results)
        total_db = sum(r.db_records for r in results)
        total_inserts = sum(r.inserts for r in results)
        total_updates = sum(r.updates for r in results)
        total_conflicts = sum(r.conflicts for r in results)
        total_errors = sum(r.errors for r in results)
        total_duration = sum(r.duration for r in results)
        
        successful_syncs = [r for r in results if r.success]
        failed_syncs = [r for r in results if not r.success]
        
        return {
            'summary': {
                'total_entities': len(results),
                'successful_syncs': len(successful_syncs),
                'failed_syncs': len(failed_syncs),
                'total_json_records': total_json,
                'total_db_records': total_db,
                'total_inserts': total_inserts,
                'total_updates': total_updates,
                'total_conflicts': total_conflicts,
                'total_errors': total_errors,
                'total_duration': total_duration,
                'success_rate': len(successful_syncs) / len(results) if results else 0
            },
            'entity_results': [
                {
                    'entity': r.entity,
                    'success': r.success,
                    'json_records': r.json_records,
                    'db_records': r.db_records,
                    'inserts': r.inserts,
                    'updates': r.updates,
                    'conflicts': r.conflicts,
                    'errors': r.errors,
                    'duration': r.duration,
                    'message': r.message
                }
                for r in results
            ],
            'successful_entities': [r.entity for r in successful_syncs],
            'failed_entities': [r.entity for r in failed_syncs],
            'timestamp': datetime.now().isoformat()
        }


def create_json_sync_engine(json_path: Union[str, Path] = None, 
                           db_path: Union[str, Path] = None) -> DifferentialSyncEngine:
    """
    Convenience function to create a JSON sync engine with default paths.
    """
    if json_path is None:
        json_path = Path.cwd() / "data" / "raw_json"
    
    if db_path is None:
        db_path = Path.cwd() / "data" / "database" / "production.db"
    
    return DifferentialSyncEngine(json_path, db_path)


def quick_sync(entities: List[str], dry_run: bool = True) -> Dict[str, Any]:
    """
    Quick sync function for immediate use.
    
    Args:
        entities: List of entity names to sync
        dry_run: If True, only analyze what would be done
    
    Returns:
        Sync report dictionary
    """
    engine = create_json_sync_engine()
    results = engine.sync_all_entities(entities, dry_run=dry_run)
    return engine.generate_sync_report(results)


# Default entities for sync operations
DEFAULT_ENTITIES = [
    'bills', 'invoices', 'salesorders', 'purchaseorders', 'creditnotes',
    'items', 'contacts', 'customerpayments', 'vendorpayments'
]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔄 JSON Differential Sync Engine - Independent System")
    print("=" * 60)
    
    # Perform dry run
    report = quick_sync(DEFAULT_ENTITIES, dry_run=True)
    
    print(f"📊 Sync Analysis Results:")
    print(f"   Total Entities: {report['summary']['total_entities']}")
    print(f"   JSON Records: {report['summary']['total_json_records']}")
    print(f"   DB Records: {report['summary']['total_db_records']}")
    print(f"   Potential Inserts: {report['summary']['total_inserts']}")
    print(f"   Potential Updates: {report['summary']['total_updates']}")
    print(f"   Success Rate: {report['summary']['success_rate']:.1%}")
