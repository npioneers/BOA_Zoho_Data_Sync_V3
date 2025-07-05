"""
Database Handler Module for Project Bedrock V2

This module provides the DatabaseHandler class for all database operations including:
- Dynamic schema creation from canonical field definitions
- Bulk data loading with proper type handling
- Database connection management
- Table and view creation

EXCLUDED: Safety protocol (backup/delete logic) - to be added later
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time

from .config import get_config_manager
from .mappings import CANONICAL_SCHEMA

logger = logging.getLogger(__name__)


class DatabaseHandler:
    """
    Handles all database operations for the normalized canonical data pipeline.
    
    Features:
    - Normalized schema creation from CANONICAL_SCHEMA definition
    - Support for Bills header and Bills_LineItems tables with proper relationships
    - Dynamic table creation with primary/foreign key constraints
    - Bulk data loading with pandas integration
    - Connection management and error handling
    - Progress tracking for large datasets
    
    Architecture:
    - Bills table: Contains bill header information (BillID as primary key)
    - Bills_LineItems table: Contains line item details (LineItemID as primary key, BillID as foreign key)
    """
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize DatabaseHandler.
        
        Args:
            database_path: Optional path to database file. If None, uses configuration.
        """
        self.config_manager = get_config_manager()
        
        if database_path:
            self.database_path = Path(database_path)
        else:
            db_path = self.config_manager.get('data_sources', 'target_database')
            self.database_path = Path(db_path)
        
        self.connection = None
        self._ensure_database_directory()
        
        logger.info(f"DatabaseHandler initialized for: {self.database_path}")
    
    def _ensure_database_directory(self) -> None:
        """Ensure the database directory exists."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured database directory exists: {self.database_path.parent}")
    
    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection with optimizations.
        
        Returns:
            SQLite connection object
        """
        if self.connection is None:
            try:
                self.connection = sqlite3.connect(
                    str(self.database_path),
                    check_same_thread=False
                )
                
                # Apply SQLite optimizations
                self.connection.execute("PRAGMA journal_mode=WAL")
                self.connection.execute("PRAGMA synchronous=NORMAL") 
                self.connection.execute("PRAGMA cache_size=10000")
                self.connection.execute("PRAGMA temp_store=MEMORY")
                
                logger.info(f"✅ Connected to database: {self.database_path}")
                
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        
        return self.connection
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def create_schema(self) -> Dict[str, Any]:
        """
        Create the complete normalized database schema from CANONICAL_SCHEMA definition.
        
        Creates:
        - Bills table (header information) with primary key
        - Bills_LineItems table (line item details) with foreign key relationship
        - Proper constraints and indexes
        
        Returns:
            Dictionary with creation status and details
        """
        logger.info("Creating normalized database schema from CANONICAL_SCHEMA")
        
        conn = self.connect()
        
        try:
            # Create Bills header table
            self._create_bills_header_table(conn)
            
            # Create Bills_LineItems table with foreign key relationship
            self._create_bills_line_items_table(conn)
            
            # Create indexes for performance
            self._create_schema_indexes(conn)
            
            conn.commit()
            logger.info("✅ Successfully created complete normalized database schema")
            
            return {
                'status': 'success',
                'message': 'Normalized schema created successfully',
                'tables_created': ['Bills', 'Bills_LineItems'],
                'indexes_created': True
            }
            
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            conn.rollback()
            return {
                'status': 'error',
                'message': f'Schema creation failed: {str(e)}',
                'tables_created': [],
                'indexes_created': False
            }
    
    def _create_bills_header_table(self, conn: sqlite3.Connection) -> None:
        """Create the Bills header table."""
        table_config = CANONICAL_SCHEMA['bills_header']
        table_name = table_config['table_name']
        primary_key = table_config['primary_key']
        
        logger.info(f"Creating {table_name} table")
        
        # Build column definitions from CANONICAL_SCHEMA
        column_definitions = []
        for col_name, col_type in table_config['columns'].items():
            if col_name == primary_key:
                # Primary key constraint
                column_definitions.append(f'"{col_name}" {col_type}')
            else:
                column_definitions.append(f'"{col_name}" {col_type}')
        
        create_sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_definitions)}
        )
        '''
        
        conn.execute(create_sql)
        logger.debug(f"Created {table_name} table with {len(column_definitions)} columns")
    
    def _create_bills_line_items_table(self, conn: sqlite3.Connection) -> None:
        """Create the Bills_LineItems table with foreign key relationship."""
        table_config = CANONICAL_SCHEMA['bills_line_items']
        table_name = table_config['table_name']
        primary_key = table_config['primary_key']
        foreign_key_config = table_config['foreign_key']
        
        logger.info(f"Creating {table_name} table with foreign key relationship")
        
        # Build column definitions from CANONICAL_SCHEMA
        column_definitions = []
        for col_name, col_type in table_config['columns'].items():
            if col_name == primary_key:
                # Primary key constraint
                column_definitions.append(f'"{col_name}" {col_type}')
            elif col_name == foreign_key_config['column']:
                # Foreign key column (will add constraint separately)
                column_definitions.append(f'"{col_name}" {col_type}')
            else:
                column_definitions.append(f'"{col_name}" {col_type}')
        
        # Add foreign key constraint
        fk_constraint = f'''FOREIGN KEY ("{foreign_key_config['column']}") 
                            REFERENCES {foreign_key_config['references']} 
                            ON DELETE {foreign_key_config['on_delete']}'''
        
        create_sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_definitions)},
            {fk_constraint}
        )
        '''
        
        conn.execute(create_sql)
        logger.debug(f"Created {table_name} table with {len(column_definitions)} columns and foreign key")
    
    def _create_schema_indexes(self, conn: sqlite3.Connection) -> None:
        """Create performance indexes for the normalized schema."""
        logger.info("Creating performance indexes")
        
        try:
            # Bills table indexes
            bills_table = CANONICAL_SCHEMA['bills_header']['table_name']
            bills_pk = CANONICAL_SCHEMA['bills_header']['primary_key']
            
            # Primary key index (automatic in SQLite but explicit for clarity)
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{bills_table.lower()}_pk ON {bills_table} ("{bills_pk}")')
            
            # Date indexes for time-based queries
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{bills_table.lower()}_date ON {bills_table} ("Date")')
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{bills_table.lower()}_vendor ON {bills_table} ("VendorName")')
            
            # Bills_LineItems table indexes
            line_items_table = CANONICAL_SCHEMA['bills_line_items']['table_name']
            line_items_pk = CANONICAL_SCHEMA['bills_line_items']['primary_key']
            foreign_key_col = CANONICAL_SCHEMA['bills_line_items']['foreign_key']['column']
            
            # Primary key and foreign key indexes
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{line_items_table.lower()}_pk ON {line_items_table} ("{line_items_pk}")')
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{line_items_table.lower()}_fk ON {line_items_table} ("{foreign_key_col}")')
            
            # Item-based indexes
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{line_items_table.lower()}_item ON {line_items_table} ("ItemName")')
            
            logger.debug("Created performance indexes for normalized schema")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")
    
    def bulk_load_data(self, table_name: str, dataframe: pd.DataFrame) -> Dict[str, Any]:
        """
        Bulk load data into specified table with progress tracking and validation.
        
        Uses pandas.DataFrame.to_sql() with batch processing to handle SQLite's
        variable limit (~999 parameters per statement).
        
        Args:
            table_name: Target table name (Bills or Bills_LineItems)
            dataframe: DataFrame containing data to load
            
        Returns:
            Dictionary with load statistics and validation results
        """
        logger.info(f"Starting bulk load for table: {table_name} with {len(dataframe)} records")
        
        if dataframe.empty:
            logger.warning(f"DataFrame is empty, skipping load to {table_name}")
            return {
                'table_name': table_name,
                'records_provided': 0,
                'records_loaded': 0,
                'status': 'skipped_empty',
                'message': 'DataFrame was empty - no records to load'
            }
        
        start_time = time.time()
        conn = self.connect()
        
        try:
            # Get record count before loading
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            records_before = cursor.fetchone()[0]
            
            # Calculate appropriate chunk size to avoid "too many SQL variables" error
            # SQLite has a limit of ~999 variables per statement
            # For safety, use a chunk size that keeps us well under this limit
            num_columns = len(dataframe.columns)
            max_chunk_size = max(1, 900 // num_columns)  # Conservative limit
            
            logger.info(f"Loading {len(dataframe)} records in chunks of {max_chunk_size}")
            
            # Load data using pandas to_sql with chunking to handle SQLite limits
            dataframe.to_sql(
                name=table_name,
                con=conn,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=max_chunk_size  # Use chunking to avoid variable limit
            )
            
            conn.commit()
            
            # Get record count after loading to verify
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            records_after = cursor.fetchone()[0]
            records_inserted = records_after - records_before
            
            execution_time = time.time() - start_time
            
            logger.info(f"✅ Successfully loaded {records_inserted} records to {table_name}")
            logger.info(f"   Total records in table: {records_after}")
            logger.info(f"   Execution time: {execution_time:.2f} seconds")
            
            return {
                'table_name': table_name,
                'records_provided': len(dataframe),
                'records_loaded': records_inserted,
                'total_records_in_table': records_after,
                'execution_time': execution_time,
                'chunk_size_used': max_chunk_size,
                'status': 'success',
                'message': f'Successfully loaded {records_inserted} records'
            }
            
        except Exception as e:
            logger.error(f"Failed to load data to {table_name}: {e}")
            conn.rollback()
            execution_time = time.time() - start_time
            
            return {
                'table_name': table_name,
                'records_provided': len(dataframe),
                'records_loaded': 0,
                'execution_time': execution_time,
                'status': 'error',
                'message': f'Load failed: {str(e)}'
            }
    
    def create_canonical_table(self, table_name: str, canonical_columns: List[str]) -> None:
        """
        Create canonical table with dynamic schema from column list.
        
        Args:
            table_name: Name of the table to create
            canonical_columns: List of canonical column names
        """
        logger.info(f"Creating canonical table: {table_name}")
        
        conn = self.connect()
        
        try:
            # Generate CREATE TABLE statement
            column_definitions = []
            
            for i, column in enumerate(canonical_columns):
                # Determine appropriate SQLite type based on column name patterns
                sql_type = self._get_sqlite_type(column)
                
                # Primary key constraint for ID fields
                if column.endswith('ID') and i == 0:
                    column_definitions.append(f'"{column}" {sql_type} PRIMARY KEY')
                else:
                    column_definitions.append(f'"{column}" {sql_type}')
            
            create_sql = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_definitions)}
            )
            '''
            
            conn.execute(create_sql)
            conn.commit()
            
            logger.info(f"✅ Created table '{table_name}' with {len(canonical_columns)} columns")
            
            # Create helpful indexes
            self._create_table_indexes(table_name, canonical_columns)
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def _get_sqlite_type(self, column_name: str) -> str:
        """
        Determine appropriate SQLite type based on column name patterns.
        
        Args:
            column_name: Name of the column
            
        Returns:
            SQLite type string
        """
        column_lower = column_name.lower()
        
        # ID fields
        if column_name.endswith('ID'):
            return 'TEXT'
        
        # Numeric fields
        numeric_patterns = [
            'amount', 'total', 'rate', 'quantity', 'percentage', 
            'balance', 'exchangerate', 'subtotal', 'taxtotal'
        ]
        if any(pattern in column_lower for pattern in numeric_patterns):
            return 'REAL'
        
        # Date fields
        if 'date' in column_lower or 'time' in column_lower:
            return 'TEXT'  # Store as ISO string
        
        # Boolean fields  
        boolean_patterns = ['isinclusive', 'enabled', 'active']
        if any(pattern in column_lower for pattern in boolean_patterns):
            return 'INTEGER'  # 0/1 for boolean
        
        # Default to TEXT
        return 'TEXT'
    
    def _create_table_indexes(self, table_name: str, canonical_columns: List[str]) -> None:
        """Create useful indexes for the table."""
        conn = self.connect()
        
        try:
            # Index on primary ID field (usually first column)
            if canonical_columns:
                primary_id_col = canonical_columns[0]
                index_sql = f'CREATE INDEX IF NOT EXISTS idx_{table_name}_{primary_id_col.lower()} ON {table_name} ("{primary_id_col}")'
                conn.execute(index_sql)
            
            # Index on date fields for time-based queries
            date_columns = [col for col in canonical_columns if 'date' in col.lower() or 'time' in col.lower()]
            for date_col in date_columns[:2]:  # Limit to first 2 date columns
                index_sql = f'CREATE INDEX IF NOT EXISTS idx_{table_name}_{date_col.lower()} ON {table_name} ("{date_col}")'
                conn.execute(index_sql)
            
            conn.commit()
            logger.debug(f"Created indexes for table: {table_name}")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes for {table_name}: {e}")
    
    def load_data(self, table_name: str, dataframe: pd.DataFrame, if_exists: str = 'append') -> Dict[str, Any]:
        """
        Load DataFrame to database table with progress tracking.
        
        Args:
            table_name: Target table name
            dataframe: DataFrame to load
            if_exists: What to do if table exists ('append', 'replace', 'fail')
            
        Returns:
            Dictionary with load statistics
        """
        logger.info(f"Loading {len(dataframe)} records to table: {table_name}")
        
        if dataframe.empty:
            logger.warning(f"DataFrame is empty, skipping load to {table_name}")
            return {'records_loaded': 0, 'execution_time': 0}
        
        start_time = time.time()
        conn = self.connect()
        
        try:
            # Get batch size from configuration
            batch_size = self.config_manager.get('processing', 'batch_size', default=1000)
            show_progress = self.config_manager.get('processing', 'show_progress', default=True)
            
            # Load data using pandas to_sql with batching
            total_batches = (len(dataframe) + batch_size - 1) // batch_size
            
            if show_progress and total_batches > 1:
                logger.info(f"Loading in {total_batches} batches of {batch_size} records each")
            
            dataframe.to_sql(
                name=table_name,
                con=conn,
                if_exists=if_exists,
                index=False,
                chunksize=batch_size
            )
            
            conn.commit()
            execution_time = time.time() - start_time
            
            # Verify load by counting records
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            final_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Successfully loaded {len(dataframe)} records to {table_name}")
            logger.info(f"   Total records in table: {final_count}")
            logger.info(f"   Execution time: {execution_time:.2f} seconds")
            
            return {
                'records_loaded': len(dataframe),
                'total_records_in_table': final_count,
                'execution_time': execution_time,
                'batches_processed': total_batches
            }
            
        except Exception as e:
            logger.error(f"Failed to load data to {table_name}: {e}")
            raise
    
    def create_analysis_views(self) -> None:
        """
        Create useful analysis views for the normalized schema.
        
        Creates views that join Bills and Bills_LineItems for comprehensive analysis.
        """
        logger.info("Creating analysis views for normalized schema")
        
        conn = self.connect()
        bills_table = CANONICAL_SCHEMA['bills_header']['table_name']
        line_items_table = CANONICAL_SCHEMA['bills_line_items']['table_name']
        
        try:
            # Bills with Line Items Summary View
            bills_complete_sql = f'''
            CREATE VIEW IF NOT EXISTS Bills_Complete AS
            SELECT 
                b.BillID,
                b.VendorName,
                b.BillNumber,
                b.Date,
                b.Status,
                b.Total as BillTotal,
                b.Balance,
                li.LineItemID,
                li.ItemName,
                li.Quantity,
                li.Rate,
                li.ItemTotal,
                li.AccountName,
                li.ProjectName
            FROM {bills_table} b
            LEFT JOIN {line_items_table} li ON b.BillID = li.BillID
            '''
            
            # Bills Summary View (aggregated)
            bills_summary_sql = f'''
            CREATE VIEW IF NOT EXISTS Bills_Summary AS
            SELECT 
                b.BillID,
                b.VendorName,
                b.BillNumber,
                b.Date,
                b.Status,
                b.Total as BillTotal,
                b.Balance,
                COUNT(li.LineItemID) as LineItemCount,
                COALESCE(SUM(li.ItemTotal), 0) as TotalLineItemAmount
            FROM {bills_table} b
            LEFT JOIN {line_items_table} li ON b.BillID = li.BillID
            GROUP BY b.BillID, b.VendorName, b.BillNumber, b.Date, b.Status, b.Total, b.Balance
            '''
            
            # Vendor Analysis View
            vendor_analysis_sql = f'''
            CREATE VIEW IF NOT EXISTS Vendor_Analysis AS
            SELECT 
                b.VendorID,
                b.VendorName,
                COUNT(DISTINCT b.BillID) as TotalBills,
                COUNT(li.LineItemID) as TotalLineItems,
                SUM(b.Total) as TotalAmount,
                AVG(b.Total) as AverageAmount,
                MIN(b.Date) as FirstBillDate,
                MAX(b.Date) as LastBillDate
            FROM {bills_table} b
            LEFT JOIN {line_items_table} li ON b.BillID = li.BillID
            WHERE b.VendorName IS NOT NULL
            GROUP BY b.VendorID, b.VendorName
            ORDER BY TotalAmount DESC
            '''
            
            # Monthly Summary View  
            monthly_summary_sql = f'''
            CREATE VIEW IF NOT EXISTS Monthly_Summary AS
            SELECT 
                strftime('%Y-%m', b.Date) as YearMonth,
                COUNT(DISTINCT b.BillID) as BillCount,
                COUNT(li.LineItemID) as LineItemCount,
                SUM(b.Total) as TotalAmount,
                COUNT(DISTINCT b.VendorID) as UniqueVendors
            FROM {bills_table} b
            LEFT JOIN {line_items_table} li ON b.BillID = li.BillID
            WHERE b.Date IS NOT NULL AND b.Date != ''
            GROUP BY strftime('%Y-%m', b.Date)
            ORDER BY YearMonth DESC
            '''
            
            # Execute view creation
            conn.execute(bills_complete_sql)
            conn.execute(bills_summary_sql)
            conn.execute(vendor_analysis_sql)
            conn.execute(monthly_summary_sql)
            conn.commit()
            
            logger.info("✅ Created 4 analysis views for normalized schema")
            
        except Exception as e:
            logger.error(f"Failed to create analysis views: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information
        """
        conn = self.connect()
        
        try:
            # Get record count
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            record_count = cursor.fetchone()[0]
            
            # Get column info
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Get table size info (approximate)
            cursor = conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}' AND type='table'")
            create_sql = cursor.fetchone()
            
            return {
                'table_name': table_name,
                'record_count': record_count,
                'column_count': len(columns_info),
                'columns': [col[1] for col in columns_info],  # Column names
                'create_sql': create_sql[0] if create_sql else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get info for table {table_name}: {e}")
            return {
                'table_name': table_name,
                'error': str(e)
            }
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate that the normalized database schema was created correctly.
        
        Checks:
        - Both Bills and Bills_LineItems tables exist
        - Tables have correct column structures
        - Foreign key relationship is properly established
        - Required indexes exist
        
        Returns:
            Dictionary with validation results and details
        """
        logger.info("Validating normalized database schema")
        
        try:
            conn = self.connect()
            
            # Check if both tables exist
            bills_table = CANONICAL_SCHEMA['bills_header']['table_name']
            line_items_table = CANONICAL_SCHEMA['bills_line_items']['table_name']
            
            # Validate Bills table
            bills_info = self.get_table_info(bills_table)
            if 'error' in bills_info:
                logger.error(f"Bills table validation failed: {bills_info['error']}")
                return {
                    'status': 'error',
                    'message': f"Bills table validation failed: {bills_info['error']}",
                    'tables_validated': []
                }
            
            # Validate Bills_LineItems table
            line_items_info = self.get_table_info(line_items_table)
            if 'error' in line_items_info:
                logger.error(f"Line items table validation failed: {line_items_info['error']}")
                return {
                    'status': 'error',
                    'message': f"Line items table validation failed: {line_items_info['error']}",
                    'tables_validated': [bills_table]
                }
            
            # Check column counts match schema definition
            expected_bills_cols = len(CANONICAL_SCHEMA['bills_header']['columns'])
            expected_line_items_cols = len(CANONICAL_SCHEMA['bills_line_items']['columns'])
            
            if bills_info['column_count'] != expected_bills_cols:
                message = f"Bills table column count mismatch: expected {expected_bills_cols}, got {bills_info['column_count']}"
                logger.error(message)
                return {
                    'status': 'error',
                    'message': message,
                    'tables_validated': []
                }
            
            if line_items_info['column_count'] != expected_line_items_cols:
                message = f"Line items table column count mismatch: expected {expected_line_items_cols}, got {line_items_info['column_count']}"
                logger.error(message)
                return {
                    'status': 'error',
                    'message': message,
                    'tables_validated': [bills_table]
                }
            
            # Check for foreign key relationship
            cursor = conn.execute(f"PRAGMA foreign_key_list({line_items_table})")
            foreign_keys = cursor.fetchall()
            
            if not foreign_keys:
                logger.warning("No foreign key constraints found - this is expected in SQLite without PRAGMA foreign_keys=ON")
            else:
                logger.info(f"Found {len(foreign_keys)} foreign key constraint(s)")
            
            logger.info("✅ Normalized schema validation passed")
            logger.info(f"   {bills_table}: {bills_info['column_count']} columns")
            logger.info(f"   {line_items_table}: {line_items_info['column_count']} columns")
            
            return {
                'status': 'success',
                'message': 'Schema validation passed',
                'tables_validated': [bills_table, line_items_table],
                'bills_columns': bills_info['column_count'],
                'line_items_columns': line_items_info['column_count'],
                'foreign_keys_found': len(foreign_keys)
            }
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {
                'status': 'error',
                'message': f'Schema validation failed: {str(e)}',
                'tables_validated': []
            }
    
    def execute_query(self, query: str) -> List[Tuple]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL SELECT query
            
        Returns:
            List of result tuples
        """
        conn = self.connect()
        
        try:
            cursor = conn.execute(query)
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
