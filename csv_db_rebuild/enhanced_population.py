#!/usr/bin/env python3
"""
Enhanced CSV to Database Population Script for Zoho Data Sync V2
Purpose: Load CSV data with comprehensive logging and error handling
Features:
- Individual record logging for every insert/update
- Table-level error isolation (skip table if too many failures)
- Comprehensive error reporting and recovery
- Multiple log files for different purposes
- Real-time progress tracking

Target: data/database/production.db
Enhanced: July 7, 2025
"""

import os
import sqlite3
import pandas as pd
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

class DatabasePopulationLogger:
    """Enhanced logging system for database population operations"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamp for this session
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize multiple loggers
        self.setup_loggers()
        
        # Statistics tracking
        self.stats = {
            'tables_processed': 0,
            'tables_successful': 0,
            'tables_failed': 0,
            'total_records_attempted': 0,
            'total_records_successful': 0,
            'total_records_failed': 0,
            'table_stats': {},
            'failed_records': [],
            'session_start': datetime.now(),
            'session_end': None
        }
    
    def setup_loggers(self):
        """Setup multiple specialized loggers"""
        # Main process logger
        self.main_logger = self._create_logger(
            'main_population',
            f'tmp_enhanced_population_{self.session_timestamp}.log',
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Error-specific logger
        self.error_logger = self._create_logger(
            'population_errors',
            f'tmp_population_errors_{self.session_timestamp}.log',
            '%(asctime)s - ERROR - %(message)s'
        )
        
        # Success audit logger
        self.success_logger = self._create_logger(
            'population_success',
            f'tmp_population_success_{self.session_timestamp}.log',
            '%(asctime)s - SUCCESS - %(message)s'
        )
        
        # Progress logger (console + file)
        self.progress_logger = self._create_logger(
            'population_progress',
            f'tmp_population_progress_{self.session_timestamp}.log',
            '%(asctime)s - PROGRESS - %(message)s',
            console=True
        )
    
    def _create_logger(self, name: str, filename: str, format_str: str, console: bool = False):
        """Create a specialized logger"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_dir / filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(file_handler)
        
        # Console handler if requested
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(format_str))
            logger.addHandler(console_handler)
        
        return logger
    
    def log_table_start(self, table_name: str, csv_file: str, record_count: int):
        """Log the start of table processing"""
        self.main_logger.info(f"Starting table {table_name} from {csv_file} ({record_count} records)")
        self.progress_logger.info(f"Processing {table_name}: {record_count} records to process")
        
        self.stats['table_stats'][table_name] = {
            'csv_file': csv_file,
            'total_records': record_count,
            'successful_records': 0,
            'failed_records': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'status': 'processing'
        }
    
    def log_record_success(self, table_name: str, record_index: int, record_id: str = None):
        """Log successful record insertion"""
        self.stats['table_stats'][table_name]['successful_records'] += 1
        self.stats['total_records_successful'] += 1
        
        # Only log every 100th record to avoid excessive logging
        if record_index % 100 == 0 or record_index == 1:
            id_info = f" (ID: {record_id})" if record_id else ""
            self.success_logger.info(f"Table {table_name} - Record {record_index}{id_info}")
            self.progress_logger.info(f"  SUCCESS {table_name}: {record_index}/{self.stats['table_stats'][table_name]['total_records']} records processed")
    
    def log_record_failure(self, table_name: str, record_index: int, error: Exception, record_data: Dict = None):
        """Log failed record insertion with full details"""
        self.stats['table_stats'][table_name]['failed_records'] += 1
        self.stats['total_records_failed'] += 1
        
        # Create detailed error record
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'table': table_name,
            'record_index': record_index,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_traceback': traceback.format_exc(),
            'record_data': list(record_data.values())[:3] if record_data else None  # First 3 fields only
        }
        
        self.stats['failed_records'].append(error_record)
        
        # Log detailed error
        self.error_logger.error(f"Table {table_name} - Record {record_index}: {error}")
        self.error_logger.error(f"Error details: {traceback.format_exc()}")
        
        # Log progress update
        self.progress_logger.info(f"  ERROR {table_name}: Failed record {record_index} - {str(error)[:100]}...")
    
    def log_table_complete(self, table_name: str, success: bool, skip_reason: str = None):
        """Log completion of table processing"""
        table_stats = self.stats['table_stats'][table_name]
        table_stats['end_time'] = datetime.now()
        table_stats['status'] = 'completed' if success else 'failed'
        
        if success:
            self.stats['tables_successful'] += 1
            self.main_logger.info(f"COMPLETED table {table_name}: {table_stats['successful_records']}/{table_stats['total_records']} records successful")
            self.progress_logger.info(f"COMPLETED {table_name}: {table_stats['successful_records']}/{table_stats['total_records']} records successful")
        else:
            self.stats['tables_failed'] += 1
            reason = f" - {skip_reason}" if skip_reason else ""
            self.main_logger.error(f"FAILED table {table_name}: {table_stats['successful_records']}/{table_stats['total_records']} records successful{reason}")
            self.progress_logger.info(f"FAILED {table_name}: {table_stats['successful_records']}/{table_stats['total_records']} records successful{reason}")
        
        self.stats['tables_processed'] += 1
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        self.stats['session_end'] = datetime.now()
        duration = self.stats['session_end'] - self.stats['session_start']
        
        # Create summary report
        report = {
            'session_info': {
                'start_time': self.stats['session_start'].isoformat(),
                'end_time': self.stats['session_end'].isoformat(),
                'duration_seconds': duration.total_seconds(),
                'duration_formatted': str(duration)
            },
            'overall_stats': {
                'tables_processed': self.stats['tables_processed'],
                'tables_successful': self.stats['tables_successful'],
                'tables_failed': self.stats['tables_failed'],
                'success_rate_tables': f"{(self.stats['tables_successful']/max(1,self.stats['tables_processed'])*100):.1f}%",
                'total_records_attempted': self.stats['total_records_attempted'],
                'total_records_successful': self.stats['total_records_successful'],
                'total_records_failed': self.stats['total_records_failed'],
                'success_rate_records': f"{(self.stats['total_records_successful']/max(1,self.stats['total_records_attempted'])*100):.1f}%"
            },
            'table_details': self.stats['table_stats'],
            'failed_records_count': len(self.stats['failed_records'])
        }
        
        # Save detailed report
        report_file = self.log_dir / f'tmp_population_report_{self.session_timestamp}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Log summary to main logger
        self.main_logger.info("=" * 80)
        self.main_logger.info("FINAL POPULATION REPORT")
        self.main_logger.info("=" * 80)
        self.main_logger.info(f"Duration: {duration}")
        self.main_logger.info(f"Tables: {self.stats['tables_successful']}/{self.stats['tables_processed']} successful ({report['overall_stats']['success_rate_tables']})")
        self.main_logger.info(f"Records: {self.stats['total_records_successful']}/{self.stats['total_records_attempted']} successful ({report['overall_stats']['success_rate_records']})")
        self.main_logger.info(f"Failed records: {len(self.stats['failed_records'])}")
        self.main_logger.info(f"Detailed report saved: {report_file}")
        
        # Log to progress logger
        self.progress_logger.info("=" * 60)
        self.progress_logger.info("FINAL RESULTS")
        self.progress_logger.info("=" * 60)
        self.progress_logger.info(f"Tables: {self.stats['tables_successful']}/{self.stats['tables_processed']} successful")
        self.progress_logger.info(f"Records: {self.stats['total_records_successful']}/{self.stats['total_records_attempted']} successful")
        if self.stats['total_records_failed'] > 0:
            self.progress_logger.info(f"WARNING Failed records: {self.stats['total_records_failed']} (saved in {report_file})")
        self.progress_logger.info(f"Full report: {report_file}")
        
        return report


class EnhancedDatabasePopulator:
    """Enhanced database population class with robust error handling"""
    
    def __init__(self, failure_threshold: int = 10):
        self.failure_threshold = failure_threshold  # Skip table after this many consecutive failures
        self.logger = DatabasePopulationLogger()
        
        # CSV file mappings to database tables
        self.csv_table_mapping = {
            'Invoice.csv': 'csv_invoices',
            'Item.csv': 'csv_items',
            'Contacts.csv': 'csv_contacts',
            'Bill.csv': 'csv_bills',
            'Vendors.csv': 'csv_organizations',
            'Customer_Payment.csv': 'csv_customer_payments',
            'Vendor_Payment.csv': 'csv_vendor_payments',
            'Sales_Order.csv': 'csv_sales_orders',
            'Purchase_Order.csv': 'csv_purchase_orders',
            'Credit_Note.csv': 'csv_credit_notes'
        }
    
    def normalize_column_name(self, col_name: str) -> str:
        """Normalize column names to match database schema"""
        # Convert to lowercase and replace spaces/special chars with underscores
        normalized = col_name.lower()
        normalized = normalized.replace(' ', '_')
        normalized = normalized.replace('.', '_')
        normalized = normalized.replace('&', '_')
        normalized = normalized.replace('#', '_number')
        normalized = normalized.replace('%', '_percent')
        normalized = normalized.replace('(', '_')
        normalized = normalized.replace(')', '')
        normalized = normalized.replace('-', '_')
        normalized = normalized.replace('/', '_')
        normalized = normalized.replace('__', '_')
        
        # Handle special cases
        if normalized.startswith('cf_'):
            pass  # Keep CF (Custom Field) prefix
        elif normalized.startswith('item_cf_'):
            pass  # Keep Item CF prefix
        elif normalized.startswith('2checkout'):
            normalized = 'two_checkout'
        
        return normalized.strip('_')
    
    def get_database_columns(self, conn: sqlite3.Connection, table_name: str) -> List[str]:
        """Get column names from database table"""
        cursor = conn.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in cursor.fetchall()]
        return columns
    
    def create_column_mapping(self, csv_columns: List[str], db_columns: List[str]) -> Dict[str, str]:
        """Create mapping between CSV and database columns"""
        csv_columns_normalized = [self.normalize_column_name(col) for col in csv_columns]
        
        column_mapping = {}
        for i, csv_col_norm in enumerate(csv_columns_normalized):
            if csv_col_norm in db_columns:
                column_mapping[csv_columns[i]] = csv_col_norm
        
        return column_mapping
    
    def insert_single_record(self, conn: sqlite3.Connection, table_name: str, 
                           record_data: Dict, record_index: int) -> bool:
        """Insert a single record with individual error handling"""
        try:
            # Create INSERT statement
            columns = list(record_data.keys())
            values = list(record_data.values())
            
            placeholders = ', '.join(['?'] * len(columns))
            columns_str = ', '.join(columns)
            
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Execute insert
            conn.execute(sql, values)
            
            # Get primary key for logging if available
            record_id = None
            if 'id' in record_data:
                record_id = record_data['id']
            elif table_name == 'csv_invoices' and 'invoice_id' in record_data:
                record_id = record_data['invoice_id']
            elif table_name == 'csv_items' and 'item_id' in record_data:
                record_id = record_data['item_id']
            elif table_name == 'csv_contacts' and 'contact_id' in record_data:
                record_id = record_data['contact_id']
            
            self.logger.log_record_success(table_name, record_index, record_id)
            return True
            
        except Exception as e:
            self.logger.log_record_failure(table_name, record_index, e, record_data)
            return False
    
    def process_table(self, csv_path: Path, table_name: str, conn: sqlite3.Connection) -> bool:
        """Process a single table with enhanced error handling"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_path, encoding='utf-8', dtype=str, na_values=[''])
            df = df.fillna('')  # Replace NaN with empty string
            
            self.logger.log_table_start(table_name, csv_path.name, len(df))
            
            # Get database columns
            db_columns = self.get_database_columns(conn, table_name)
            
            # Create column mapping
            column_mapping = self.create_column_mapping(df.columns.tolist(), db_columns)
            
            if not column_mapping:
                self.logger.log_table_complete(table_name, False, "No column mappings found")
                return False
            
            # Clear existing data
            conn.execute(f"DELETE FROM {table_name}")
            self.logger.main_logger.info(f"Cleared existing data from {table_name}")
            
            # Process records individually
            consecutive_failures = 0
            total_successful = 0
            
            for i, (_, row) in enumerate(df.iterrows(), 1):
                # Prepare record data
                record_data = {}
                for csv_col, db_col in column_mapping.items():
                    record_data[db_col] = row[csv_col]
                
                # Track total attempts
                self.logger.stats['total_records_attempted'] += 1
                
                # Insert record
                if self.insert_single_record(conn, table_name, record_data, i):
                    total_successful += 1
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    
                    # Check if we should skip remaining records
                    if consecutive_failures >= self.failure_threshold:
                        skip_reason = f"Too many consecutive failures ({consecutive_failures}), skipping remaining {len(df) - i} records"
                        self.logger.main_logger.warning(skip_reason)
                        self.logger.log_table_complete(table_name, False, skip_reason)
                        return False
                
                # Commit every 100 records for better error recovery
                if i % 100 == 0:
                    conn.commit()
            
            # Final commit
            conn.commit()
            
            # Mark table as successful if we got at least some records
            success = total_successful > 0
            self.logger.log_table_complete(table_name, success)
            
            return success
            
        except Exception as e:
            self.logger.log_table_complete(table_name, False, f"Table processing error: {str(e)}")
            self.logger.error_logger.error(f"Table {table_name} processing failed: {traceback.format_exc()}")
            return False
    
    def populate_database(self, db_path: Path, csv_dir: Path) -> bool:
        """Main function to populate database with enhanced error handling"""
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        if not csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found: {csv_dir}")
        
        # Connect to database with disabled SHM/WAL
        conn = sqlite3.connect(str(db_path))
        
        # Disable shared memory and WAL mode to prevent lock files
        conn.execute("PRAGMA journal_mode = DELETE")
        conn.execute("PRAGMA locking_mode = NORMAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.commit()
        
        try:
            self.logger.main_logger.info("=== Enhanced Database Population Started ===")
            self.logger.progress_logger.info("Starting enhanced database population process")
            
            # Process each CSV file
            for csv_file, table_name in self.csv_table_mapping.items():
                csv_path = csv_dir / csv_file
                
                if not csv_path.exists():
                    self.logger.main_logger.warning(f"CSV file not found: {csv_path}")
                    self.logger.progress_logger.info(f"WARNING Skipping {table_name}: CSV file {csv_file} not found")
                    continue
                
                self.logger.progress_logger.info(f"Processing {csv_file} -> {table_name}")
                self.process_table(csv_path, table_name, conn)
                self.logger.progress_logger.info("")  # Add spacing
            
            # Generate final report
            final_report = self.logger.generate_final_report()
            
            # Determine overall success
            overall_success = (self.logger.stats['tables_successful'] > 0 and 
                             self.logger.stats['total_records_successful'] > 0)
            
            return overall_success
            
        except Exception as e:
            conn.rollback()
            self.logger.main_logger.error(f"Database population failed: {e}")
            self.logger.error_logger.error(f"Critical error: {traceback.format_exc()}")
            raise
        finally:
            conn.close()


def main():
    """Main execution function"""
    try:
        # Database path
        db_path = Path("data/database/production.db")
        
        # CSV directory - use the direct path since files are in the Latest folder
        csv_dir = Path("data/csv/Nangsel Pioneers_Latest")
        
        # Verify CSV files exist
        csv_files = list(csv_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {csv_dir}")
        
        print(f"Enhanced Database Population")
        print(f"Database: {db_path}")
        print(f"CSV Source: {csv_dir}")
        print(f"Found {len(csv_files)} CSV files")
        print(f"Failure threshold: 10 consecutive failures per table")
        print("="*60)
        
        # Create populator
        populator = EnhancedDatabasePopulator(failure_threshold=10)
        
        # Populate database
        success = populator.populate_database(db_path, csv_dir)
        
        if success:
            print("\nDatabase population completed successfully!")
        else:
            print("\nDatabase population completed with issues. Check logs for details.")
        
        return success
        
    except Exception as e:
        print(f"\nDatabase population failed: {e}")
        print("Check logs for detailed error information.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
