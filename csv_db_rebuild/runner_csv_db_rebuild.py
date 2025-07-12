"""
CSV Database Rebuild Runner
Pure business logic for CSV to database rebuild operations
No user interaction - designed for programmatic access
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import re
from typing import Dict, List, Optional, Any


class CSVDatabaseRebuildRunner:
    """
    Pure business logic runner for CSV database rebuild operations.
    No user interaction - all operations are programmatic.
    """
    
    # Default table mappings
    DEFAULT_TABLE_MAPPINGS = {
        "csv_invoices": {"csv_file": "Invoice.csv"},
        "csv_items": {"csv_file": "Item.csv"},
        "csv_contacts": {"csv_file": "Contacts.csv"},
        "csv_bills": {"csv_file": "Bill.csv"},
        "csv_customer_payments": {"csv_file": "Customer_Payment.csv"},
        "csv_vendor_payments": {"csv_file": "Vendor_Payment.csv"},
        "csv_sales_orders": {"csv_file": "Sales_Order.csv"},
        "csv_purchase_orders": {"csv_file": "Purchase_Order.csv"},
        "csv_credit_notes": {"csv_file": "Credit_Note.csv"}
    }
    
    def __init__(self, 
                 db_path: str = "../data/database/production.db",
                 csv_dir: str = "../data/csv/Nangsel Pioneers_Latest",
                 table_mappings: Optional[Dict] = None,
                 enable_logging: bool = True,
                 log_dir: str = "../logs"):
        """
        Initialize the CSV database rebuild runner.
        
        Args:
            db_path: Path to SQLite database
            csv_dir: Directory containing CSV files
            table_mappings: Custom table to CSV file mappings
            enable_logging: Whether to enable logging
            log_dir: Directory for log files
        """
        self.db_path = Path(db_path)
        self.csv_dir = Path(csv_dir)
        self.table_mappings = table_mappings or self.DEFAULT_TABLE_MAPPINGS
        self.enable_logging = enable_logging
        self.log_dir = Path(log_dir)
        self.logger = None
        
        if self.enable_logging:
            self._setup_logging()
    
    def _validate_csv_table_safety(self, tables: List[str]) -> List[str]:
        """
        Validate that all table names have csv_ prefix for safety
        Returns only tables with csv_ prefix, logs warnings for others
        """
        safe_tables = []
        for table_name in tables:
            if table_name.startswith('csv_'):
                safe_tables.append(table_name)
            else:
                self._log(f"SAFETY WARNING: Skipping table '{table_name}' - only 'csv_' prefixed tables are allowed for operations")
        return safe_tables
    
    def _get_business_date_column(self, table_name: str, columns: List[str]) -> Optional[str]:
        """
        Get the most appropriate business date column for a table.
        Prioritizes business document dates over system sync dates.
        
        Args:
            table_name: Name of the database table
            columns: List of column names in the table
            
        Returns:
            The best date column to use for oldest/latest date calculation, or None
        """
        table_lower = table_name.lower()
        
        # 1. Document-specific business dates (HIGHEST PRIORITY)
        if 'invoice' in table_lower:
            for col in ['invoice_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'bill' in table_lower:
            for col in ['bill_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'salesorder' in table_lower or 'sales_order' in table_lower:
            for col in ['salesorder_date', 'order_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'purchaseorder' in table_lower or 'purchase_order' in table_lower:
            for col in ['purchaseorder_date', 'purchase_order_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'creditnote' in table_lower or 'credit_note' in table_lower:
            for col in ['creditnote_date', 'credit_note_date', 'date']:
                if col in columns: 
                    return col
                    
        elif any(term in table_lower for term in ['payment', 'customerpayment', 'vendorpayment']):
            for col in ['payment_date', 'date']:
                if col in columns: 
                    return col
        
        # Special handling for master data tables (items, contacts) - these typically don't have business dates
        elif 'item' in table_lower:
            # Items table is master data - check for item-specific dates first, avoid system timestamps
            for col in ['created_date', 'item_date', 'date']:
                if col in columns:
                    return col
            # For items table, prefer not to show dates since they're master data
            return None
            
        elif 'contact' in table_lower:
            # Contacts table - look for contact-specific business dates
            for col in ['created_date', 'contact_date', 'date']:
                if col in columns:
                    return col
        
        # 2. Generic business date (MEDIUM PRIORITY)
        if 'date' in columns:
            return 'date'
        
        # 3. System dates (LOWEST PRIORITY - only if no business date available)
        for sys_date in ['created_time', 'last_modified_time', 'updated_time', 'modified_time', 'created_timestamp', 'updated_timestamp']:
            if sys_date in columns:
                return sys_date
                
        return None
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        self.log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"csv_rebuild_{timestamp}.log"
        
        # Create logger for this instance
        self.logger = logging.getLogger(f"csv_rebuild_{timestamp}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Simplified format for cleaner output
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self._log(f"CSV Rebuild Log: {log_file}")
        self._log("")
    
    def _log(self, message: str) -> None:
        """Log message if logging is enabled"""
        if self.logger:
            self.logger.info(message)
    
    def csv_to_db_column_name(self, csv_column: str) -> str:
        """Convert CSV column name to database column name (snake_case)"""
        # Convert spaces and special characters to underscores
        db_column = re.sub(r'[^a-zA-Z0-9]', '_', csv_column)
        # Convert to lowercase
        db_column = db_column.lower()
        # Remove multiple underscores
        db_column = re.sub(r'_+', '_', db_column)
        # Remove leading/trailing underscores
        db_column = db_column.strip('_')
        return db_column
    
    def get_database_columns(self, table_name: str) -> List[str]:
        """Get the actual column names from the database table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            return columns
        except Exception as e:
            self._log(f"Error getting columns for {table_name}: {str(e)}")
            return []
    
    def map_csv_to_db_columns(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Map CSV column names to database column names"""
        db_columns = self.get_database_columns(table_name)
        column_mapping = {}
        
        for csv_col in df.columns:
            db_col = self.csv_to_db_column_name(csv_col)
            if db_col in db_columns:
                column_mapping[csv_col] = db_col
            else:
                self._log(f"CSV column '{csv_col}' -> '{db_col}' not found in database table {table_name}")
        
        # Rename the DataFrame columns
        df_mapped = df.rename(columns=column_mapping)
        
        # Only keep columns that exist in the database
        valid_columns = [col for col in df_mapped.columns if col in db_columns]
        df_final = df_mapped[valid_columns]
        
        self._log(f"Mapped {len(valid_columns)}/{len(df.columns)} columns for {table_name}")
        return df_final
    
    def clear_table(self, table_name: str) -> Dict[str, Any]:
        """
        Clear all data from a table
        
        SAFETY: Only clears tables with 'csv_' prefix to prevent accidental data loss
        """
        try:
            # Safety check: Only allow clearing csv_ prefixed tables
            if not table_name.startswith('csv_'):
                error_msg = f"SAFETY: Cannot clear table '{table_name}' - only 'csv_' prefixed tables are allowed"
                self._log(error_msg)
                return {"success": False, "rows_deleted": 0, "error": error_msg}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                self._log(f"Table {table_name} does not exist")
                conn.close()
                return {"success": False, "rows_deleted": 0, "error": "Table does not exist"}
            
            # Clear the table
            cursor.execute(f"DELETE FROM {table_name}")
            rows_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            self._log(f"Cleared {rows_deleted} existing records from {table_name}")
            return {"success": True, "rows_deleted": rows_deleted, "error": None}
            
        except Exception as e:
            error_msg = f"Error clearing table {table_name}: {str(e)}"
            self._log(error_msg)
            return {"success": False, "rows_deleted": 0, "error": error_msg}
    
    def get_primary_key_columns(self, table_name: str) -> List[str]:
        """Get primary key column names for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            pk_columns = [row[1] for row in cursor.fetchall() if row[5] > 0]  # pk column in position 5
            conn.close()
            return pk_columns
        except Exception as e:
            self._log(f"Error getting primary keys for {table_name}: {str(e)}")
            return []
    
    def insert_records_without_pk(self, table_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Insert records without primary key columns to avoid conflicts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            inserted_count = 0
            
            # Remove primary key columns to avoid conflicts
            pk_columns = self.get_primary_key_columns(table_name)
            df_no_pk = df.copy()
            
            for pk_col in pk_columns:
                if pk_col in df_no_pk.columns:
                    self._log(f"Removing primary key column '{pk_col}' from {table_name} for insertion")
                    df_no_pk = df_no_pk.drop(columns=[pk_col])
            
            # Add data_source column with value 'csv'
            df_no_pk['data_source'] = 'csv'
            self._log(f"Added data_source='csv' column to {table_name} for insertion")
            
            if df_no_pk.empty or len(df_no_pk.columns) == 0:
                self._log(f"No columns left after removing primary keys for {table_name}")
                return {"success": False, "records_inserted": 0, "error": "No valid columns"}
            
            # Create INSERT statement without primary key columns but with data_source
            columns = list(df_no_pk.columns)
            placeholders = ', '.join(['?' for _ in columns])
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Insert each row
            for _, row in df_no_pk.iterrows():
                try:
                    cursor.execute(sql, tuple(row))
                    inserted_count += 1
                except Exception as e:
                    self._log(f"Failed to insert row in {table_name}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return {"success": True, "records_inserted": inserted_count, "error": None}
            
        except Exception as e:
            error_msg = f"Error inserting records into {table_name}: {str(e)}"
            self._log(error_msg)
            return {"success": False, "records_inserted": 0, "error": error_msg}
    
    def populate_single_table(self, table_name: str) -> Dict[str, Any]:
        """Populate a single table from CSV"""
        self._log(f"Populating table: {table_name}")
        
        # Get CSV mapping
        if table_name not in self.table_mappings:
            error_msg = f"No mapping found for table: {table_name}"
            self._log(error_msg)
            return {"success": False, "records": 0, "csv_records": 0, "error": error_msg}
        
        csv_file = self.table_mappings[table_name]["csv_file"]
        csv_path = self.csv_dir / csv_file
        
        if not csv_path.exists():
            error_msg = f"CSV file not found: {csv_path}"
            self._log(error_msg)
            return {"success": False, "records": 0, "csv_records": 0, "error": error_msg}
        
        try:
            # Clear existing data from table
            clear_result = self.clear_table(table_name)
            if not clear_result["success"]:
                self._log(f"Failed to clear table {table_name}, continuing anyway...")
            
            # Read CSV
            df = pd.read_csv(csv_path)
            csv_record_count = len(df)
            self._log(f"Read {csv_record_count} records from {csv_file}")
            
            # Map CSV columns to DB columns
            df_mapped = self.map_csv_to_db_columns(df, table_name)
            if df_mapped.empty or len(df_mapped.columns) == 0:
                error_msg = f"No valid columns mapped for {table_name}"
                self._log(error_msg)
                return {"success": False, "records": 0, "csv_records": csv_record_count, "error": error_msg}
            
            # Insert records without primary keys
            insert_result = self.insert_records_without_pk(table_name, df_mapped)
            
            if insert_result["success"]:
                self._log(f"Successfully inserted {insert_result['records_inserted']}/{len(df_mapped)} records into {table_name}")
                return {
                    "success": True, 
                    "records": insert_result["records_inserted"], 
                    "csv_records": csv_record_count, 
                    "error": None
                }
            else:
                return {
                    "success": False, 
                    "records": 0, 
                    "csv_records": csv_record_count, 
                    "error": insert_result["error"]
                }
            
        except Exception as e:
            error_msg = f"Error populating {table_name}: {str(e)}"
            self._log(error_msg)
            return {"success": False, "records": 0, "csv_records": 0, "error": error_msg}
    
    def populate_all_tables(self, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Populate all mapped tables or specified tables
        
        Args:
            tables: Optional list of specific tables to populate. If None, populates all mapped tables.
            
        Returns:
            Dictionary with detailed results and statistics
        """
        start_time = datetime.now()
        tables_to_process = tables or list(self.table_mappings.keys())
        
        # Safety validation: Only allow csv_ prefixed tables
        safe_tables = self._validate_csv_table_safety(tables_to_process)
        if len(safe_tables) != len(tables_to_process):
            self._log(f"SAFETY: Filtered {len(tables_to_process) - len(safe_tables)} non-csv tables from operation")
        
        self._log("Starting population of tables")
        self._log("="*70)
        self._log(f"SAFETY: Processing only csv_ prefixed tables: {len(safe_tables)} tables")
        
        results = {}
        total_success = 0
        total_records = 0
        total_csv_records = 0
        failed_tables = []
        
        for table_name in safe_tables:
            if table_name not in self.table_mappings:
                self._log(f"Skipping {table_name} - no mapping found")
                continue
                
            result = self.populate_single_table(table_name)
            results[table_name] = result
            
            total_csv_records += result["csv_records"]
            
            if result["success"]:
                total_success += 1
                total_records += result["records"]
                success_rate = (result["records"] / result["csv_records"] * 100) if result["csv_records"] > 0 else 0
                self._log(f"SUCCESS {table_name}: {result['records']}/{result['csv_records']} records ({success_rate:.1f}%)")
            else:
                failed_tables.append(table_name)
                self._log(f"FAILED {table_name}: {result['error']}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Calculate overall success rates
        overall_success_rate = (total_records / total_csv_records * 100) if total_csv_records > 0 else 0
        table_success_rate = (total_success / len(safe_tables) * 100) if safe_tables else 0
        
        # Create summary
        summary = {
            "tables_attempted": len(safe_tables),
            "tables_successful": total_success,
            "tables_failed": len(failed_tables),
            "table_success_rate": table_success_rate,
            "total_csv_records": total_csv_records,
            "total_records_inserted": total_records,
            "overall_success_rate": overall_success_rate,
            "processing_time_seconds": processing_time,
            "failed_tables": failed_tables,
            "results": results
        }
        
        # Log detailed success report
        self._log_success_report(summary)
        
        return summary
    
    def clear_and_populate_all_tables(self, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Clear all tables and then populate them from CSV files
        
        Args:
            tables: Optional list of specific tables to process. If None, processes all mapped tables.
            
        Returns:
            Dictionary with detailed results and statistics including clear and populate results
        """
        start_time = datetime.now()
        tables_to_process = tables or list(self.table_mappings.keys())
        
        # Safety validation: Only allow csv_ prefixed tables
        safe_tables = self._validate_csv_table_safety(tables_to_process)
        if len(safe_tables) != len(tables_to_process):
            self._log(f"SAFETY: Filtered {len(tables_to_process) - len(safe_tables)} non-csv tables from operation")
        
        self._log("Starting clear and populate operation for all tables")
        self._log("="*70)
        self._log(f"SAFETY: Processing only csv_ prefixed tables: {len(safe_tables)} tables")
        
        # Phase 1: Clear all tables
        self._log("PHASE 1: Clearing csv_* tables only...")
        clear_results = {}
        tables_cleared = 0
        total_rows_cleared = 0
        
        for table_name in safe_tables:
            if table_name not in self.table_mappings:
                self._log(f"Skipping {table_name} - no mapping found")
                continue
                
            clear_result = self.clear_table(table_name)
            clear_results[table_name] = clear_result
            
            if clear_result["success"]:
                tables_cleared += 1
                total_rows_cleared += clear_result["rows_deleted"]
                self._log(f"Cleared {table_name}: {clear_result['rows_deleted']} rows deleted")
            else:
                self._log(f"Failed to clear {table_name}: {clear_result['error']}")
        
        self._log(f"Clear phase complete: {tables_cleared}/{len(safe_tables)} tables cleared, {total_rows_cleared:,} total rows deleted")
        self._log("")
        
        # Phase 2: Populate all tables
        self._log("PHASE 2: Populating all tables from CSV...")
        populate_results = self.populate_all_tables(safe_tables)
        
        end_time = datetime.now()
        total_processing_time = (end_time - start_time).total_seconds()
        
        # Create combined summary
        combined_summary = {
            "operation": "clear_and_populate",
            "tables_attempted": len(safe_tables),
            "tables_cleared": tables_cleared,
            "total_rows_cleared": total_rows_cleared,
            "tables_populated": populate_results["tables_successful"],
            "tables_failed": populate_results["tables_failed"],
            "total_csv_records": populate_results["total_csv_records"],
            "total_records_inserted": populate_results["total_records_inserted"],
            "overall_success_rate": populate_results["overall_success_rate"],
            "table_success_rate": populate_results["table_success_rate"],
            "total_processing_time_seconds": total_processing_time,
            "clear_time_seconds": populate_results["processing_time_seconds"] - total_processing_time,
            "populate_time_seconds": populate_results["processing_time_seconds"],
            "failed_tables": populate_results["failed_tables"],
            "clear_results": clear_results,
            "populate_results": populate_results["results"]
        }
        
        # Log combined success report
        self._log_clear_and_populate_report(combined_summary)
        
        return combined_summary
    
    def _log_clear_and_populate_report(self, summary: Dict[str, Any]) -> None:
        """Log detailed clear and populate report"""
        self._log("="*70)
        self._log("CLEAR AND POPULATE SUCCESS REPORT")
        self._log("="*70)
        self._log(f"Operation: Clear and populate all tables")
        self._log(f"Tables Processed: {summary['tables_attempted']}")
        self._log(f"Tables Cleared: {summary['tables_cleared']}")
        self._log(f"Total Rows Cleared: {summary['total_rows_cleared']:,}")
        self._log(f"Tables Populated: {summary['tables_populated']}")
        self._log(f"Overall Success Rate: {summary['overall_success_rate']:.1f}% ({summary['total_records_inserted']:,}/{summary['total_csv_records']:,} records)")
        self._log(f"Table Success Rate: {summary['table_success_rate']:.1f}% ({summary['tables_populated']}/{summary['tables_attempted']} tables)")
        self._log(f"Total Processing Time: {summary['total_processing_time_seconds']:.1f} seconds ({summary['total_processing_time_seconds']/60:.1f} minutes)")
        
        if summary['failed_tables']:
            self._log(f"Failed Tables: {', '.join(summary['failed_tables'])}")
        else:
            self._log("All tables cleared and populated successfully!")
        
        self._log("="*70)

    def _log_success_report(self, summary: Dict[str, Any]) -> None:
        """Log detailed success report in table format"""
        self._log("="*70)
        self._log("POPULATION SUCCESS REPORT")
        self._log("="*70)
        self._log(f"Overall Success Rate: {summary['overall_success_rate']:.1f}% ({summary['total_records_inserted']:,}/{summary['total_csv_records']:,} records)")
        self._log(f"Table Success Rate: {summary['table_success_rate']:.1f}% ({summary['tables_successful']}/{summary['tables_attempted']} tables)")
        self._log(f"Processing Time: {summary['processing_time_seconds']:.1f} seconds ({summary['processing_time_seconds']/60:.1f} minutes)")
        
        if summary['failed_tables']:
            self._log(f"Failed Tables: {', '.join(summary['failed_tables'])}")
        else:
            self._log("All tables populated successfully!")
        
        self._log("="*70)
        self._log("DETAILED SUCCESS RATE TABLE:")
        self._log("="*70)
        self._log(f"{'Table Name':<20} | {'CSV Records':<11} | {'DB Records':<10} | {'Success Rate':<12} | {'Status':<8}")
        self._log("-" * 70)
        
        for table_name, result in summary['results'].items():
            if result["success"]:
                success_rate = (result["records"] / result["csv_records"] * 100) if result["csv_records"] > 0 else 0
                status = "PASS"
                self._log(f"{table_name:<20} | {result['csv_records']:>11,} | {result['records']:>10,} | {success_rate:>11.1f}% | {status:<8}")
            else:
                status = "FAIL"
                self._log(f"{table_name:<20} | {result['csv_records']:>11,} | {'0':>10} | {'0.0':>11}% | {status:<8}")
        
        self._log("-" * 70)
        self._log(f"{'TOTAL':<20} | {summary['total_csv_records']:>11,} | {summary['total_records_inserted']:>10,} | {summary['overall_success_rate']:>11.1f}% | {'':8}")
        self._log("="*70)
    
    def verify_table_population(self, table_name: str) -> Dict[str, Any]:
        """
        Verify that a table has been populated correctly and get date range information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return {
                    "success": False, 
                    "error": "Table does not exist", 
                    "record_count": 0,
                    "column_count": 0,
                    "oldest_date": None,
                    "latest_date": None,
                    "date_column": None,
                    "table_created_timestamp": None
                }
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            record_count = cursor.fetchone()[0]
            
            # Get column information
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            column_info = cursor.fetchall()
            column_count = len(column_info)
            columns = [row[1] for row in column_info]  # Column names are in position 1
            
            # Initialize date-related results
            oldest_date = None
            latest_date = None
            date_column = None
            table_created_timestamp = None
            
            # Get table creation timestamp (when CSV data was loaded)
            if 'created_timestamp' in columns and record_count > 0:
                try:
                    cursor.execute(f"SELECT MIN(`created_timestamp`) FROM `{table_name}` WHERE `created_timestamp` IS NOT NULL")
                    created_result = cursor.fetchone()
                    table_created_timestamp = created_result[0] if created_result and created_result[0] else None
                except Exception as e:
                    self._log(f"Warning: Could not extract table creation timestamp from {table_name}: {str(e)}")
                    table_created_timestamp = None
            
            # If table has data, try to get date range
            if record_count > 0:
                # Find the best business date column
                date_column = self._get_business_date_column(table_name, columns)
                
                if date_column:
                    try:
                        # Get oldest date
                        cursor.execute(f"SELECT MIN(`{date_column}`) FROM `{table_name}` WHERE `{date_column}` IS NOT NULL")
                        oldest_result = cursor.fetchone()
                        oldest_date = oldest_result[0] if oldest_result and oldest_result[0] else None
                        
                        # Get latest date
                        cursor.execute(f"SELECT MAX(`{date_column}`) FROM `{table_name}` WHERE `{date_column}` IS NOT NULL")
                        latest_result = cursor.fetchone()
                        latest_date = latest_result[0] if latest_result and latest_result[0] else None
                        
                    except Exception as date_error:
                        self._log(f"Warning: Could not extract date range from {table_name}.{date_column}: {str(date_error)}")
                        oldest_date = None
                        latest_date = None
            
            conn.close()
            
            return {
                "success": True,
                "error": None,
                "record_count": record_count,
                "column_count": column_count,
                "oldest_date": oldest_date,
                "latest_date": latest_date,
                "date_column": date_column,
                "table_created_timestamp": table_created_timestamp
            }
            
        except Exception as e:
            error_msg = f"Error verifying table {table_name}: {str(e)}"
            return {
                "success": False, 
                "error": error_msg, 
                "record_count": 0,
                "column_count": 0,
                "oldest_date": None,
                "latest_date": None,
                "date_column": None,
                "table_created_timestamp": None
            }
    
    def get_table_status_summary(self) -> Dict[str, Any]:
        """Get status summary for all mapped tables"""
        summary = {
            "total_tables": len(self.table_mappings),
            "table_status": {},
            "total_records": 0,
            "populated_tables": 0
        }
        
        for table_name in self.table_mappings.keys():
            status = self.verify_table_population(table_name)
            summary["table_status"][table_name] = status
            
            if status["success"] and status["record_count"] > 0:
                summary["populated_tables"] += 1
                summary["total_records"] += status["record_count"]
        
        summary["population_rate"] = (summary["populated_tables"] / summary["total_tables"] * 100) if summary["total_tables"] > 0 else 0
        
        return summary
