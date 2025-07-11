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


class JSONDataPopulator:
    """Populates JSON tables with filtered data from consolidated JSON files"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 json_dir: str = "data/raw_json/json_compiled"):
        self.db_path = Path(db_path)
        self.json_dir = Path(json_dir)
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
            # Clean field name
            clean_name = self.analyzer.clean_field_name(field_name)
            
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
            self.logger.info(f"Successfully populated {table_name}: {total_inserted} records")
            
        except Exception as e:
            error_msg = f"Error populating {table_name}: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
        
        return result

    def populate_all_tables(self, force_recreate: bool = False) -> Dict[str, Any]:
        """Populate all JSON tables with filtered data"""
        self.stats['start_time'] = datetime.now()
        self.logger.info("Starting JSON data population process...")
        
        # Get cutoff date
        cutoff_date = self.get_cutoff_date()
        self.stats['cutoff_date'] = cutoff_date
        
        # Clear existing data if force recreate
        if force_recreate:
            self.logger.info("Force recreate enabled - clearing existing JSON data")
            self.clear_json_tables()
        
        # Get table mapping from analyzer
        if not self.analyzer.analysis_results:
            self.analyzer.analyze_all_json_files()
        
        results = {}
        
        # Process tables serially
        for table_name, table_info in self.analyzer.analysis_results.items():
            self.stats['tables_processed'] += 1
            json_filename = table_info['json_file']
            
            self.logger.info(f"Processing table {self.stats['tables_processed']}/{len(self.analyzer.analysis_results)}: {table_name}")
            
            try:
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


def main():
    """Main function for data population"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JSON Data Population Tool")
    parser.add_argument("--db-path", default="data/database/production.db",
                       help="Path to the database file")
    parser.add_argument("--json-dir", default="data/raw_json/json_compiled",
                       help="Path to consolidated JSON directory")
    parser.add_argument("--force-recreate", action="store_true",
                       help="Clear existing data before population")
    
    args = parser.parse_args()
    
    populator = JSONDataPopulator(args.db_path, args.json_dir)
    
    try:
        results = populator.populate_all_tables(args.force_recreate)
        populator.print_population_summary(results)
        
    except Exception as e:
        logging.error(f"Data population failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
