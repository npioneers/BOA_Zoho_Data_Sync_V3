"""
JSON Data Populator
Populates JSON tables with data from consolidated JSON files, filtering by cutoff date
"""
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import time

# Handle imports for both standalone and module usage
try:
    from .json_analyzer import JSONAnalyzer
except ImportError:
    from json_analyzer import JSONAnalyzer


class SimpleDuplicatePreventionManager:
    """Simplified duplicate prevention manager built into data populator"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.processed_sessions = set()
        self.processed_files = set()
        
    def is_session_processed(self, session_id: str, session_path: str) -> bool:
        """Check if session was already processed"""
        return session_id in self.processed_sessions
        
    def start_session_processing(self, session_id: str, session_path: str) -> bool:
        """Mark session as being processed"""
        if session_id in self.processed_sessions:
            return False
        self.processed_sessions.add(session_id)
        return True
        
    def is_file_processed(self, table_name: str, file_path: str, session_id: str) -> bool:
        """Check if file was already processed"""
        file_key = f"{session_id}:{table_name}:{file_path}"
        return file_key in self.processed_files
        
    def track_file_processing(self, table_name: str, file_path: str, session_id: str, 
                             record_count: int, file_size: int):
        """Track file processing"""
        file_key = f"{session_id}:{table_name}:{file_path}"
        self.processed_files.add(file_key)
        
    def complete_session_processing(self, session_id: str, total_records: int, 
                                  processed_modules: list):
        """Mark session as completed"""
        pass
        
    def fail_session_processing(self, session_id: str, error_message: str):
        """Mark session as failed"""
        if session_id in self.processed_sessions:
            self.processed_sessions.remove(session_id)
            
    def get_processing_stats(self) -> dict:
        """Get processing statistics"""
        return {
            "sessions_processed": len(self.processed_sessions),
            "files_processed": len(self.processed_files)
        }


class JSONDataPopulator:
    """Populates JSON tables with filtered data from session-based or consolidated JSON files"""
    
    def __init__(self, db_path: str = None, 
                 json_dir: str = None):
        # Import configuration system
        try:
            from .config import get_config
        except ImportError:
            from config import get_config
        
        self.config = get_config()
        
        # Use provided paths or get from configuration
        if db_path is None:
            db_path = self.config.get_database_path()
        if json_dir is None:
            # For session-based, json_dir will be the session folder
            # For consolidated, it will be the consolidated path
            json_dir = str(self.config.get_effective_data_source_path())
            
        self.db_path = Path(db_path)
        self.json_dir = Path(json_dir)
        
        # Detect if we're working with session-based structure
        self.is_session_based = self._detect_session_structure()
        
        # Set up JSON analyzer based on structure type
        if self.is_session_based:
            # For session-based, we'll handle file discovery differently
            self.analyzer = None  # Will be set up dynamically
        else:
            # Traditional structure - direct JSON directory
            self.analyzer = JSONAnalyzer(str(json_dir))
            
        self.setup_logging()
        
        # Population statistics
        self.stats = {
            'tables_processed': 0,
            'tables_succeeded': 0,
            'tables_failed': 0,
            'total_records_inserted': 0,
            'errors': [],
            'cutoff_date': None,
            'start_time': None,
            'end_time': None
        }
        
        # Date field mappings for filtering - prioritizing last_modified_time
        self.date_fields = {
            'json_invoices': ['last_modified_time'],
            'json_bills': ['last_modified_time'],
            'json_sales_orders': ['last_modified_time'],
            'json_purchase_orders': ['last_modified_time'],
            'json_credit_notes': ['last_modified_time'],
            'json_customer_payments': ['last_modified_time'],
            'json_vendor_payments': ['last_modified_time'],
            'json_contacts': ['last_modified_time'],
            'json_items': ['last_modified_time'],
            'json_organizations': ['last_modified_time'],
            # Line item tables typically don't have direct dates, inherit from parent
            'json_invoices_line_items': [],
            'json_bills_line_items': [],
            'json_salesorders_line_items': [],
            'json_purchaseorders_line_items': [],
            'json_creditnotes_line_items': []
        }

        # Initialize duplicate prevention manager
        try:
            self.duplicate_manager = SimpleDuplicatePreventionManager(str(self.db_path))
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize duplicate prevention: {e}")
            self.duplicate_manager = None

    def setup_logging(self):
        """Setup logging for population process"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"json_data_population_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"JSON Data Population started - Logging to: {log_file}")

    def get_cutoff_date(self) -> Optional[str]:
        """Get cutoff date from max invoice date in CSV table minus 2 weeks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if invoices table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
            if not cursor.fetchone():
                self.logger.warning("CSV invoices table not found, using default cutoff")
                return (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
            
            # Find max date from various date columns
            date_columns = ['last_payment_date', 'invoice_date', 'due_date', 'updated_timestamp']
            max_date = None
            
            for date_col in date_columns:
                try:
                    cursor.execute(f"SELECT MAX({date_col}) FROM invoices WHERE {date_col} IS NOT NULL AND {date_col} != ''")
                    result = cursor.fetchone()
                    if result and result[0]:
                        # Try different date formats
                        for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                            try:
                                parsed_date = datetime.strptime(result[0][:10], date_format[:10])
                                if not max_date or parsed_date > max_date:
                                    max_date = parsed_date
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    self.logger.debug(f"Error checking {date_col}: {e}")
            
            conn.close()
            
            if max_date:
                cutoff_date = max_date - timedelta(weeks=2)
                cutoff_str = cutoff_date.strftime('%Y-%m-%d')
                self.logger.info(f"Max invoice date: {max_date.strftime('%Y-%m-%d')}")
                self.logger.info(f"Cutoff date (2 weeks before): {cutoff_str}")
                return cutoff_str
            else:
                self.logger.warning("No valid dates found, using default cutoff")
                return (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')
                
        except Exception as e:
            self.logger.error(f"Error getting cutoff date: {e}")
            return (datetime.now() - timedelta(weeks=4)).strftime('%Y-%m-%d')

    def filter_records_by_date(self, records: List[Dict], table_name: str, cutoff_date: str) -> List[Dict]:
        """Filter records based on cutoff date"""
        if not records:
            return records
        
        date_fields = self.date_fields.get(table_name, [])
        if not date_fields:
            # For line item tables or tables without date fields, return all records
            return records
        
        filtered_records = []
        cutoff_datetime = datetime.strptime(cutoff_date, '%Y-%m-%d')
        
        for record in records:
            include_record = False
            
            # Check each possible date field
            for date_field in date_fields:
                if date_field in record and record[date_field]:
                    try:
                        # Try different date formats
                        record_date = None
                        date_value = str(record[date_field])
                        
                        for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
                            try:
                                record_date = datetime.strptime(date_value[:10], date_format[:10])
                                break
                            except ValueError:
                                continue
                        
                        if record_date and record_date >= cutoff_datetime:
                            include_record = True
                            break
                            
                    except Exception as e:
                        self.logger.debug(f"Error parsing date {date_field}={record[date_field]}: {e}")
                        continue
            
            # If no valid date found, include the record (better safe than sorry)
            if include_record or not any(date_field in record for date_field in date_fields):
                filtered_records.append(record)
        
        self.logger.info(f"Filtered {table_name}: {len(records)} -> {len(filtered_records)} records")
        return filtered_records

    def clean_record_for_insert(self, record: Dict[str, Any], columns: Dict[str, Dict]) -> Dict[str, Any]:
        """Clean and prepare record for database insertion"""
        cleaned_record = {}
        
        for field_name, field_value in record.items():
            # Clean field name - handle case where analyzer is None (session-based operations)
            if self.analyzer is not None and hasattr(self.analyzer, 'clean_field_name'):
                clean_name = self.analyzer.clean_field_name(field_name)
            else:
                # Fallback field name cleaning for session-based operations
                clean_name = self._clean_field_name_fallback(field_name)
            
            # Skip if column doesn't exist in table
            if clean_name not in columns:
                continue
            
            # Handle different data types
            if field_value is None or field_value == "":
                cleaned_record[clean_name] = None
            elif isinstance(field_value, (list, dict)):
                # Convert complex objects to JSON strings
                cleaned_record[clean_name] = json.dumps(field_value)
            elif isinstance(field_value, bool):
                # Convert boolean to integer (SQLite standard)
                cleaned_record[clean_name] = 1 if field_value else 0
            else:
                # Convert to string and handle encoding
                cleaned_record[clean_name] = str(field_value)
        
        # Add import timestamp fields if they exist in the table schema
        current_timestamp = datetime.now().isoformat()
        import_timestamp_fields = [
            'import_timestamp', 'sync_timestamp', 'last_sync_time', 
            'data_import_time', 'table_sync_time'
        ]
        
        for timestamp_field in import_timestamp_fields:
            if timestamp_field in columns:
                cleaned_record[timestamp_field] = current_timestamp
        
        return cleaned_record

    def populate_table(self, table_name: str, json_filename: str, cutoff_date: str) -> Dict[str, Any]:
        """Populate a single table with filtered JSON data"""
        result = {
            'success': False,
            'records_inserted': 0,
            'records_filtered': 0,
            'total_records': 0,
            'error': None
        }
        
        try:
            # Load JSON data
            json_file = self.json_dir / json_filename
            if not json_file.exists():
                raise FileNotFoundError(f"JSON file not found: {json_file}")
            
            self.logger.info(f"Loading {json_filename} for table {table_name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
            
            if not isinstance(all_records, list):
                raise ValueError(f"Expected list in {json_filename}, got {type(all_records)}")
            
            result['total_records'] = len(all_records)
            
            # Filter records by date
            filtered_records = self.filter_records_by_date(all_records, table_name, cutoff_date)
            result['records_filtered'] = len(filtered_records)
            
            if not filtered_records:
                self.logger.info(f"No records to insert for {table_name} after filtering")
                result['success'] = True
                return result
            
            # Get table schema from analyzer
            if not self.analyzer.analysis_results:
                self.analyzer.analyze_all_json_files()
            
            if table_name not in self.analyzer.analysis_results:
                raise ValueError(f"Table {table_name} not found in analysis results")
            
            columns = self.analyzer.analysis_results[table_name]['analysis']['columns']
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare INSERT statement
            column_names = list(columns.keys())
            placeholders = ', '.join(['?' for _ in column_names])
            insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            # Process records in batches
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(filtered_records), batch_size):
                batch = filtered_records[i:i + batch_size]
                batch_data = []
                
                for record in batch:
                    cleaned_record = self.clean_record_for_insert(record, columns)
                    # Create tuple with values in column order
                    values = tuple(cleaned_record.get(col_name) for col_name in column_names)
                    batch_data.append(values)
                
                # Execute batch insert
                cursor.executemany(insert_sql, batch_data)
                total_inserted += len(batch_data)
                
                if total_inserted % 500 == 0:
                    self.logger.info(f"Inserted {total_inserted}/{len(filtered_records)} records into {table_name}")
            
            conn.commit()
            conn.close()
            
            result['records_inserted'] = total_inserted
            result['success'] = True
            
            # Track table population time for verification reports
            self._track_table_population(table_name, total_inserted)
            
            self.logger.info(f"Successfully populated {table_name}: {total_inserted} records")
            
        except Exception as e:
            error_msg = f"Error populating {table_name}: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
        
        return result

    def populate_table_from_path(self, table_name: str, json_file_path: Path, cutoff_date: str) -> Dict[str, Any]:
        """Populate a single table with filtered JSON data from specific file path"""
        result = {
            'success': False,
            'records_inserted': 0,
            'records_filtered': 0,
            'total_records': 0,
            'error': None
        }
        
        try:
            # Load JSON data from specified path
            if not json_file_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_file_path}")
            
            self.logger.info(f"Loading {json_file_path.name} from {json_file_path.parent.name} for table {table_name}")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                all_records = json.load(f)
            
            if not isinstance(all_records, list):
                raise ValueError(f"JSON file must contain an array of records")
            
            result['total_records'] = len(all_records)
            
            # Filter records by cutoff date if specified
            filtered_records = self.filter_records_by_date(all_records, table_name, cutoff_date)
            result['records_filtered'] = len(filtered_records)
            
            if not filtered_records:
                self.logger.info(f"No records found for {table_name} after date filtering")
                result['success'] = True
                return result
            
            # Insert records into database
            result['records_inserted'] = self.insert_records(table_name, filtered_records)
            result['success'] = True
            
            self.logger.info(f"✅ Successfully populated {table_name}: {result['records_inserted']}/{result['total_records']} records")
            
        except Exception as e:
            error_msg = f"Error populating {table_name}: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
            
        return result

    def insert_records(self, table_name: str, records: List[Dict]) -> int:
        """Insert a list of records into the specified table"""
        if not records:
            return 0
        
        try:
            # Get table schema - handle both session-based and traditional structures
            if self.analyzer is None or not hasattr(self.analyzer, 'analysis_results') or not self.analyzer.analysis_results:
                # For session-based operations, use database schema directly
                columns = self._get_table_columns_from_db(table_name)
            else:
                # Traditional structure with analyzer
                if table_name not in self.analyzer.analysis_results:
                    columns = self._get_table_columns_from_db(table_name)
                else:
                    columns = self.analyzer.analysis_results[table_name]['analysis']['columns']
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare INSERT statement
            column_names = list(columns.keys())
            placeholders = ', '.join(['?' for _ in column_names])
            insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            # Process records in batches
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                batch_data = []
                
                for record in batch:
                    cleaned_record = self.clean_record_for_insert(record, columns)
                    # Create tuple with values in column order
                    values = tuple(cleaned_record.get(col_name) for col_name in column_names)
                    batch_data.append(values)
                
                # Execute batch insert
                cursor.executemany(insert_sql, batch_data)
                total_inserted += len(batch_data)
                
                if total_inserted % 500 == 0:
                    self.logger.info(f"Inserted {total_inserted}/{len(records)} records into {table_name}")
            
            conn.commit()
            conn.close()
            
            return total_inserted
            
        except Exception as e:
            self.logger.error(f"Error inserting records into {table_name}: {e}")
            return 0

    def populate_all_tables(self, force_recreate: bool = False) -> Dict[str, Any]:
        """Populate all JSON tables with filtered data"""
        self.stats['start_time'] = datetime.now()
        self.logger.info(f"Starting JSON data population process (structure: {'session-based' if self.is_session_based else 'consolidated'})...")
        
        # Get cutoff date
        cutoff_date = self.get_cutoff_date()
        self.stats['cutoff_date'] = cutoff_date
        
        # Clear existing data if force recreate
        if force_recreate:
            self.logger.info("Force recreate enabled - clearing existing JSON data")
            self.clear_json_tables()
        
        # Get available JSON files and their mappings
        if self.is_session_based:
            # Session-based: Get files from session structure
            json_files = self.get_available_json_files()
            table_mappings = self._get_table_mappings_for_files(json_files)
        else:
            # Consolidated: Use existing analyzer approach
            if not self.analyzer.analysis_results:
                self.analyzer.analyze_all_json_files()
            table_mappings = self.analyzer.analysis_results
        
        results = {}
        
        # Process tables serially
        for table_name, table_info in table_mappings.items():
            self.stats['tables_processed'] += 1
            
            if self.is_session_based:
                json_file_path = table_info['json_file_path']
                json_filename = json_file_path.name
            else:
                json_filename = table_info['json_file']
                json_file_path = self.json_dir / json_filename
            
            total_tables = len(table_mappings)
            self.logger.info(f"Processing table {self.stats['tables_processed']}/{total_tables}: {table_name}")
            
            try:
                if self.is_session_based:
                    result = self.populate_table_from_path(table_name, json_file_path, cutoff_date)
                else:
                    result = self.populate_table(table_name, json_filename, cutoff_date)
                results[table_name] = result
                
                if result['success']:
                    self.stats['tables_succeeded'] += 1
                    self.stats['total_records_inserted'] += result['records_inserted']
                else:
                    self.stats['tables_failed'] += 1
                    self.stats['errors'].append(f"{table_name}: {result['error']}")
                    
            except Exception as e:
                error_msg = f"Fatal error processing {table_name}: {str(e)}"
                self.logger.error(error_msg)
                self.stats['tables_failed'] += 1
                self.stats['errors'].append(error_msg)
                results[table_name] = {
                    'success': False,
                    'error': error_msg,
                    'records_inserted': 0
                }
                # Continue to next table
                continue
        
        self.stats['end_time'] = datetime.now()
        self.logger.info("JSON data population completed")
        
        return {
            'success': self.stats['tables_failed'] == 0,
            'stats': self.stats,
            'table_results': results
        }

    def populate_all_tables_with_cutoff(self, cutoff_days: int) -> Dict[str, Any]:
        """
        Populate all JSON tables with data using custom cutoff days.
        
        Args:
            cutoff_days: Number of days back from today to filter data
            
        Returns:
            Dict containing population results and statistics
        """
        from datetime import datetime, timedelta
        
        self.stats['start_time'] = datetime.now()
        self.logger.info(f"Starting JSON data population with {cutoff_days} day cutoff...")
        
        # Calculate custom cutoff date
        cutoff_date = (datetime.now() - timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
        self.stats['cutoff_date'] = cutoff_date
        self.logger.info(f"Using custom cutoff date: {cutoff_date}")
        
        # Get available JSON files and their mappings
        if self.is_session_based:
            # Session-based: Get files from session structure
            json_files = self.get_available_json_files()
            table_mappings = self._get_table_mappings_for_files(json_files)
        else:
            # Consolidated: Use existing analyzer approach
            if not self.analyzer.analysis_results:
                self.analyzer.analyze_all_json_files()
            table_mappings = self.analyzer.analysis_results
        
        results = {}
        
        # Process tables serially
        for table_name, table_info in table_mappings.items():
            self.stats['tables_processed'] += 1
            
            if self.is_session_based:
                json_file_path = table_info['json_file_path']
                json_filename = json_file_path.name
            else:
                json_filename = table_info['json_file']
                json_file_path = self.json_dir / json_filename
            
            total_tables = len(table_mappings)
            self.logger.info(f"Processing table {self.stats['tables_processed']}/{total_tables}: {table_name}")
            
            try:
                if self.is_session_based:
                    result = self.populate_table_from_path(table_name, json_file_path, cutoff_date)
                else:
                    result = self.populate_table(table_name, json_filename, cutoff_date)
                results[table_name] = result
                
                if result['success']:
                    self.stats['tables_succeeded'] += 1
                    self.stats['total_records_inserted'] += result['records_inserted']
                else:
                    self.stats['tables_failed'] += 1
                    self.stats['errors'].append(f"{table_name}: {result['error']}")
                    
            except Exception as e:
                error_msg = f"Fatal error processing {table_name}: {str(e)}"
                self.logger.error(error_msg)
                self.stats['tables_failed'] += 1
                self.stats['errors'].append(error_msg)
                results[table_name] = {
                    'success': False,
                    'error': error_msg,
                    'records_inserted': 0
                }
                # Continue to next table
                continue
        
        self.stats['end_time'] = datetime.now()
        self.logger.info(f"JSON data population with {cutoff_days} day cutoff completed")
        
        # Add session information for reporting
        session_info = self._get_session_info()
        
        # Add detailed table statistics
        table_stats = {}
        total_records = 0
        for table_name, result in results.items():
            if result.get('success', False):
                records = result.get('records_inserted', 0)
                table_stats[table_name] = records
                total_records += records
        
        return {
            'success': self.stats['tables_failed'] == 0,
            'stats': self.stats,
            'table_results': results,
            'session_info': session_info,
            'table_statistics': table_stats,
            'total_records': total_records,
            'total_tables': len(table_mappings),
            'total_json_files': len(json_files) if 'json_files' in locals() else len(table_mappings)
        }

    def clear_json_tables(self):
        """Clear all JSON tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all JSON tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%'")
            json_tables = [row[0] for row in cursor.fetchall()]
            
            for table_name in json_tables:
                cursor.execute(f"DELETE FROM {table_name}")
                self.logger.info(f"Cleared table: {table_name}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error clearing JSON tables: {e}")

    def print_population_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of the population process"""
        stats = results['stats']
        
        print("\n" + "="*80)
        print("JSON DATA POPULATION SUMMARY")
        print("="*80)
        
        duration = stats['end_time'] - stats['start_time']
        
        print(f"Cutoff Date: {stats['cutoff_date']}")
        print(f"Duration: {duration}")
        print(f"Tables Processed: {stats['tables_processed']}")
        print(f"Tables Succeeded: {stats['tables_succeeded']}")
        print(f"Tables Failed: {stats['tables_failed']}")
        print(f"Total Records Inserted: {stats['total_records_inserted']:,}")
        
        if results['success']:
            print("\n✓ DATA POPULATION SUCCESSFUL")
        else:
            print("\n✗ DATA POPULATION COMPLETED WITH ERRORS")
        
        if stats['errors']:
            print(f"\nERRORS ({len(stats['errors'])}):")
            print("-" * 50)
            for i, error in enumerate(stats['errors'], 1):
                print(f"  {i}. {error}")
        
        print("\nTABLE DETAILS:")
        print("-" * 80)
        print(f"{'Table Name':<30} {'Records':<12} {'Status':<10} {'Filtered':<10}")
        print("-" * 80)
        
        for table_name, result in results['table_results'].items():
            status = "SUCCESS" if result['success'] else "FAILED"
            records = result.get('records_inserted', 0)
            filtered = result.get('records_filtered', 0)
            print(f"{table_name:<30} {records:<12,} {status:<10} {filtered:<10,}")
        
        print("="*80)

    def _detect_session_structure(self) -> bool:
        """Always return True - we always use session-based structure"""
        # Simplified: always treat as session-based structure
        return True
    
    def _get_session_json_files(self) -> Dict[str, Path]:
        """Get all JSON files from session-based structure"""
        json_files = {}
        
        if self.json_dir.name.startswith("sync_session_"):
            # We're in a session folder, look in raw_json subdirectories
            timestamp_dirs = self.config.get_session_json_directories(str(self.json_dir))
        else:
            # We might be in the main api_sync folder, find latest session
            latest_session = self.config.get_latest_session_folder()
            if latest_session:
                timestamp_dirs = self.config.get_session_json_directories(latest_session)
            else:
                # Fallback: try to get from current directory in case it's sync_sessions
                timestamp_dirs = self.config.get_session_json_directories(str(self.json_dir))
        
        # Collect all JSON files across timestamp directories, excluding metadata files
        for timestamp_dir in timestamp_dirs:
            for json_file in timestamp_dir.glob("*.json"):
                # Skip metadata files - they are not data arrays
                if json_file.name.startswith("sync_metadata_"):
                    self.logger.debug(f"Skipping metadata file: {json_file.name}")
                    continue
                    
                module_name = json_file.stem
                # Prefer newer timestamp files (first in list when sorted by name desc)
                if module_name not in json_files:
                    json_files[module_name] = json_file
        
        self.logger.info(f"Found {len(json_files)} JSON files in session structure: {list(json_files.keys())}")
        return json_files
    
    def _get_consolidated_json_files(self) -> Dict[str, Path]:
        """Get all JSON files from consolidated structure"""
        json_files = {}
        
        # Direct JSON files in the directory
        for json_file in self.json_dir.glob("*.json"):
            module_name = json_file.stem
            json_files[module_name] = json_file
        
        return json_files
    
    def get_available_json_files(self) -> Dict[str, Path]:
        """Get all available JSON files based on structure type"""
        if self.is_session_based:
            return self._get_session_json_files()
        else:
            return self._get_consolidated_json_files()
    
    def _get_table_mappings_for_files(self, json_files: Dict[str, Path]) -> Dict[str, Dict]:
        """Get table mappings for session-based JSON files"""
        table_mappings = {}
        
        # Database-driven mapping (preserving existing database table mapping system)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Get table mappings from database if they exist
            cursor.execute("""
                SELECT json_file, table_name, is_line_item_table 
                FROM json_table_mapping 
                WHERE json_file IN ({})
            """.format(','.join(['?' for _ in json_files.keys()])), list(json_files.keys()))
            
            db_mappings = cursor.fetchall()
            
            for json_file, table_name, is_line_item in db_mappings:
                if json_file in json_files:
                    table_mappings[table_name] = {
                        'json_file': json_file,
                        'json_file_path': json_files[json_file],
                        'is_line_item_table': bool(is_line_item),
                        'table_name': table_name
                    }
                    
        except sqlite3.OperationalError:
            # If json_table_mapping table doesn't exist, fall back to filename-based mapping
            # This is normal behavior - filename-based mapping works perfectly fine
            self.logger.info("Using filename-based table mapping (json_table_mapping table not present)")
            
            for module_name, file_path in json_files.items():
                # Apply json_ prefix to match standard table naming convention
                json_filename = module_name + '.json'
                
                # Use analyzer's mapping if available, otherwise construct with json_ prefix
                if hasattr(self.analyzer, 'json_to_table_map') and json_filename in self.analyzer.json_to_table_map:
                    table_name = self.analyzer.json_to_table_map[json_filename]
                else:
                    # Fallback: construct table name with json_ prefix
                    base_name = module_name.replace('_line_items', '')
                    is_line_item = module_name.endswith('_line_items')
                    
                    # Handle specific naming differences between JSON filenames and database table names
                    # Only apply mapping for non-line-item tables to preserve existing line item table names
                    if not is_line_item:
                        name_mappings = {
                            'customerpayments': 'customer_payments',
                            'vendorpayments': 'vendor_payments', 
                            'salesorders': 'sales_orders',
                            'creditnotes': 'credit_notes'
                        }
                        
                        # Apply name mapping if exists
                        if base_name in name_mappings:
                            base_name = name_mappings[base_name]
                    
                    table_name = f"json_{base_name}" + ('_line_items' if is_line_item else '')
                
                is_line_item = module_name.endswith('_line_items')
                
                table_mappings[table_name] = {
                    'json_file': json_filename,
                    'json_file_path': file_path,
                    'is_line_item_table': is_line_item,
                    'table_name': table_name
                }
        
        finally:
            conn.close()
        
        return table_mappings

    def populate_session_safely(self, session_path: str = None, modules: List[str] = None, force_reprocess: bool = False) -> Dict[str, Any]:
        """Safely populate data from a session with comprehensive duplicate prevention"""
        
        # Use current session if none specified
        if session_path is None:
            if self.is_session_based:
                session_path = str(self.json_dir)
            else:
                return {'success': False, 'error': 'No session path provided and not in session-based mode'}
        
        session_id = Path(session_path).name
        
        # Check duplicate prevention manager
        if not self.duplicate_manager:
            print("⚠️ Warning: No duplicate prevention - proceeding without session tracking")
            return self._populate_session_basic(session_path, modules)
        
        # Check if session already processed
        if not force_reprocess and self.duplicate_manager.is_session_processed(session_id, session_path):
            self.logger.info(f"Session {session_id} already processed successfully")
            return {
                'success': True,
                'skipped': True,
                'message': f'Session {session_id} already processed',
                'session_id': session_id,
                'records_processed': 0
            }
        
        # Start session processing
        if not force_reprocess and not self.duplicate_manager.start_session_processing(session_id, session_path):
            return {
                'success': False,
                'error': 'Session already being processed or completed',
                'session_id': session_id,
                'records_processed': 0
            }
        
        try:
            self.logger.info(f"Starting safe population of session: {session_id}")
            total_records = 0
            processed_modules = []
            files_processed = 0
            
            # Get JSON files from session
            if self.is_session_based:
                json_files_dict = self._get_session_json_files()
            else:
                # Handle traditional structure  
                json_files_dict = self._get_traditional_json_files()
            
            # Filter modules if specified
            if modules:
                filtered_dict = {}
                for k, v in json_files_dict.items():
                    if any(module.lower() in str(v).lower() for module in modules):
                        filtered_dict[k] = v
                json_files_dict = filtered_dict
            
            self.logger.info(f"Processing {len(json_files_dict)} files from session")
            
            for file_key, file_path in json_files_dict.items():
                try:
                    # Determine table name from file
                    table_name = f"json_{file_path.stem}"
                    
                    # Check if this specific file was already processed
                    if (not force_reprocess and 
                        self.duplicate_manager.is_file_processed(table_name, str(file_path), session_id)):
                        self.logger.info(f"File {file_path.name} already processed, skipping")
                        continue
                    
                    # Process the file
                    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                    result = self.populate_table_from_path(table_name, file_path, cutoff_date)
                    
                    if result.get('success'):
                        records_processed = result.get('records_inserted', 0)
                        total_records += records_processed
                        files_processed += 1
                        
                        # Track file processing
                        self.duplicate_manager.track_file_processing(
                            table_name, str(file_path), records_processed, session_id
                        )
                        
                        processed_modules.append(file_path.stem)
                        self.logger.info(f"✅ Processed {file_path.stem}: {records_processed} records")
                    else:
                        self.logger.error(f"❌ Failed to process {file_path.name}: {result.get('error')}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing file {file_path}: {e}")
                    continue
            
            # Mark session as completed
            if self.duplicate_manager:
                self.duplicate_manager.complete_session_processing(session_id, total_records, processed_modules)
            
            self.logger.info(f"✅ Session processing completed: {total_records} total records, {files_processed} files")
            
            return {
                'success': True,
                'session_id': session_id,
                'records_processed': total_records,
                'modules_processed': processed_modules,
                'files_processed': files_processed,
                'duplicate_prevention': True
            }
            
        except Exception as e:
            # Mark session as failed
            if self.duplicate_manager:
                self.duplicate_manager.fail_session_processing(session_id, str(e))
            
            self.logger.error(f"❌ Session processing failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'records_processed': total_records if 'total_records' in locals() else 0
            }
    
    def _populate_session_basic(self, session_path: str, modules: List[str] = None) -> Dict[str, Any]:
        """Basic session population without duplicate prevention (fallback)"""
        try:
            total_records = 0
            processed_modules = []
            
            # Get JSON files
            if self.is_session_based:
                json_files_dict = self._get_session_json_files()
            else:
                json_files_dict = self._get_traditional_json_files()
            
            # Filter modules if specified
            if modules:
                filtered_dict = {}
                for k, v in json_files_dict.items():
                    if any(module.lower() in str(v).lower() for module in modules):
                        filtered_dict[k] = v
                json_files_dict = filtered_dict
            
            for file_key, file_path in json_files_dict.items():
                table_name = f"json_{file_path.stem}"
                cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                result = self.populate_table_from_path(table_name, file_path, cutoff_date)
                
                if result.get('success'):
                    records_processed = result.get('records_inserted', 0)
                    total_records += records_processed
                    processed_modules.append(file_path.stem)
            
            return {
                'success': True,
                'records_processed': total_records,
                'modules_processed': processed_modules,
                'files_processed': len(json_files_dict),
                'duplicate_prevention': False
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_traditional_json_files(self) -> Dict[str, Path]:
        """Get JSON files from traditional structure"""
        json_files = {}
        
        if self.json_dir.exists():
            for json_file in self.json_dir.glob("*.json"):
                json_files[json_file.stem] = json_file
        
        return json_files
    
    def get_duplicate_prevention_stats(self) -> Dict[str, Any]:
        """Get duplicate prevention statistics"""
        if not self.duplicate_manager:
            return {'error': 'Duplicate prevention not initialized'}
        
        return self.duplicate_manager.get_processing_stats()
    
    def _get_table_columns_from_db(self, table_name: str) -> Dict[str, Dict]:
        """Get table column information directly from database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema_info = cursor.fetchall()
            
            if not schema_info:
                conn.close()
                raise ValueError(f"Table {table_name} not found in database")
            
            # Convert to format expected by the rest of the code
            columns = {}
            for row in schema_info:
                col_name = row[1]  # column name
                col_type = row[2]  # column type
                columns[col_name] = {
                    'type': col_type,
                    'nullable': not bool(row[3])  # not null flag
                }
            
            conn.close()
            return columns
            
        except Exception as e:
            self.logger.error(f"Error getting columns for table {table_name}: {e}")
            return {}

    def _clean_field_name_fallback(self, field_name: str) -> str:
        """Clean field name when analyzer is not available"""
        import re
        # Basic field name cleaning similar to JSONAnalyzer
        clean_name = field_name.lower()
        clean_name = re.sub(r'[^a-z0-9_]', '_', clean_name)
        clean_name = re.sub(r'_+', '_', clean_name)
        clean_name = clean_name.strip('_')
        return clean_name
    
    def _track_table_population(self, table_name: str, records_inserted: int):
        """Track when a table was last populated for verification reports"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tracking table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS table_population_tracking (
                    table_name TEXT PRIMARY KEY,
                    last_populated_time TEXT NOT NULL,
                    records_count INTEGER,
                    data_source TEXT
                )
            """)
            
            # Insert or update the tracking record
            current_time = datetime.now().isoformat()
            data_source = "json" if table_name.startswith("json_") else "csv"
            
            cursor.execute("""
                INSERT OR REPLACE INTO table_population_tracking 
                (table_name, last_populated_time, records_count, data_source)
                VALUES (?, ?, ?, ?)
            """, (table_name, current_time, records_inserted, data_source))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # Don't fail the main operation if tracking fails
            self.logger.warning(f"Failed to track table population for {table_name}: {e}")

    def _get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session being used"""
        session_info = {
            "selected_session": "Unknown",
            "session_has_data": False,
            "all_sessions": [],
            "rejected_sessions": []
        }
        
        try:
            if self.is_session_based and hasattr(self, 'config'):
                # Get the selected session
                latest_session = self.config.get_latest_session_folder()
                if latest_session:
                    session_path = Path(latest_session)
                    session_info["selected_session"] = session_path.name
                    session_info["session_has_data"] = self.config._session_has_data_files(session_path)
                
                # Get all available sessions for comparison
                api_sync_path = Path(self.config.get_api_sync_path())
                if api_sync_path.exists():
                    all_sessions = [
                        f for f in api_sync_path.iterdir() 
                        if f.is_dir() and f.name.startswith("sync_session_")
                    ]
                    
                    # Sort by modification time (newest first)
                    sorted_sessions = sorted(all_sessions, key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    for session in sorted_sessions:
                        has_data = self.config._session_has_data_files(session)
                        session_entry = {
                            "name": session.name,
                            "has_data": has_data,
                            "selected": session.name == session_info["selected_session"]
                        }
                        
                        if has_data:
                            session_info["all_sessions"].append(session_entry)
                        else:
                            session_info["rejected_sessions"].append(session_entry)
        
        except Exception as e:
            session_info["error"] = str(e)
        
        return session_info
