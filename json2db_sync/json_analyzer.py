"""
JSON Analyzer
Analyzes consolidated JSON files to determine database table structure requirements.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set, Optional
from collections import defaultdict


class JSONAnalyzer:
    """Analyzes JSON files to determine database table requirements"""
    
    def __init__(self, json_dir: str = None):
        # Import here to avoid circular imports
        if json_dir is None:
            try:
                from .config import get_config
            except ImportError:
                from config import get_config
            
            config = get_config()
            json_dir = config.get_api_sync_path()
        
        self.json_dir = Path(json_dir)
        self.setup_logging()
        
        # Check if this is a session-based structure
        self.session_based = self._is_session_based_structure()
        
        # Target tables (main entities and their line item tables) with json_ prefix
        self.target_tables = {
            'json_invoices', 'json_items', 'json_contacts', 'json_bills', 'json_organizations',
            'json_customer_payments', 'json_vendor_payments', 'json_sales_orders', 
            'json_purchase_orders', 'json_credit_notes',
            # Line item tables
            'json_invoices_line_items', 'json_bills_line_items', 'json_salesorders_line_items',
            'json_purchaseorders_line_items', 'json_creditnotes_line_items'
        }
        
        # Map JSON file names to standardized table names (with json_ prefix)
        self.json_to_table_map = {
            'invoices.json': 'json_invoices',
            'items.json': 'json_items', 
            'contacts.json': 'json_contacts',
            'bills.json': 'json_bills',
            'organizations.json': 'json_organizations',
            'customerpayments.json': 'json_customer_payments',
            'vendorpayments.json': 'json_vendor_payments',
            'salesorders.json': 'json_sales_orders',
            'purchaseorders.json': 'json_purchase_orders',
            'creditnotes.json': 'json_credit_notes',
            # Line item files
            'invoices_line_items.json': 'json_invoices_line_items',
            'bills_line_items.json': 'json_bills_line_items',
            'salesorders_line_items.json': 'json_salesorders_line_items',
            'purchaseorders_line_items.json': 'json_purchaseorders_line_items',
            'creditnotes_line_items.json': 'json_creditnotes_line_items'
        }
        
        # Analysis results
        self.analysis_results = {}
        self.table_schemas = {}
    
    def _is_session_based_structure(self) -> bool:
        """Check if the data follows session-based structure"""
        # Look for sync_sessions directory
        sessions_dir = self.json_dir / "data" / "sync_sessions"
        return sessions_dir.exists() and sessions_dir.is_dir()
    
    def _get_latest_session_data_path(self) -> Optional[Path]:
        """Get the path to the latest session data following the Data Consumer Guide pattern"""
        if not self.session_based:
            return None
            
        sessions_dir = self.json_dir / "data" / "sync_sessions"
        
        if not sessions_dir.exists():
            return None
        
        # Find latest session folder
        session_folders = [
            f for f in sessions_dir.iterdir() 
            if f.is_dir() and f.name.startswith("sync_session_")
        ]
        
        if not session_folders:
            return None
        
        # Sort by timestamp (newest first)
        latest_session = sorted(session_folders, key=lambda x: x.name, reverse=True)[0]
        
        # Return the raw_json directory within the latest session
        raw_json_dir = latest_session / "raw_json"
        return raw_json_dir if raw_json_dir.exists() else None
    
    def _find_json_files_in_session(self, raw_json_dir: Path) -> List[Path]:
        """Find JSON files in session-based timestamp directories"""
        json_files = []
        
        # Find timestamp directories within the session
        timestamp_dirs = [
            d for d in raw_json_dir.iterdir() 
            if d.is_dir() and d.name.count('-') >= 4  # timestamp format like 2025-07-11_13-54-38
        ]
        
        # Look for JSON files in timestamp directories
        for timestamp_dir in sorted(timestamp_dirs, reverse=True):
            for json_file in timestamp_dir.glob("*.json"):
                # Only add if we haven't already found this file type
                if not any(existing.name == json_file.name for existing in json_files):
                    json_files.append(json_file)
        
        return json_files

    def setup_logging(self):
        """Setup logging for analysis process"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"json_analysis_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"JSON Analysis started - Logging to: {log_file}")

    def analyze_json_file(self, json_file: Path) -> Dict[str, Any]:
        """Analyze a single JSON file to determine its structure"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                self.logger.warning(f"Expected list in {json_file.name}, got {type(data)}")
                return {}
            
            if not data:
                self.logger.warning(f"Empty data in {json_file.name}")
                return {'record_count': 0, 'columns': {}, 'sample_record': None}
            
            # Analyze first record for column structure
            sample_record = data[0]
            columns = self.analyze_record_structure(sample_record)
            
            # Check data consistency across multiple records (sample up to 100)
            sample_size = min(100, len(data))
            for i in range(1, sample_size):
                record_columns = self.analyze_record_structure(data[i])
                # Merge column information
                for col_name, col_info in record_columns.items():
                    if col_name in columns:
                        # Update data type if we find more specific type
                        if columns[col_name]['data_type'] == 'TEXT' and col_info['data_type'] != 'TEXT':
                            columns[col_name]['data_type'] = col_info['data_type']
                        # Track if nullable
                        if col_info['nullable']:
                            columns[col_name]['nullable'] = True
                    else:
                        # New column found in later records
                        columns[col_name] = col_info
                        columns[col_name]['nullable'] = True  # Must be nullable since missing in first record
            
            # Extract date range information
            date_info = self._extract_date_range(data, json_file.name)
            
            result = {
                'record_count': len(data),
                'columns': columns,
                'sample_record': sample_record,
                'date_range': date_info
            }
            
            self.logger.info(f"Analyzed {json_file.name}: {len(data)} records, {len(columns)} columns")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {json_file}: {str(e)}")
            return {}

    def analyze_record_structure(self, record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze the structure of a single record"""
        columns = {}
        
        for field_name, field_value in record.items():
            # Clean field name for database compatibility
            clean_name = self.clean_field_name(field_name)
            
            # Determine data type and constraints
            data_type, max_length = self.determine_data_type(field_value)
            nullable = field_value is None or field_value == ""
            
            columns[clean_name] = {
                'original_name': field_name,
                'data_type': data_type,
                'max_length': max_length,
                'nullable': nullable,
                'is_primary_key': self.is_primary_key_field(field_name),
                'is_foreign_key': self.is_foreign_key_field(field_name)
            }
        
        return columns

    def _extract_date_range(self, data: list, json_filename: str) -> dict:
        """Extract date range information from JSON data"""
        if not data:
            return {'earliest_date': None, 'latest_date': None, 'date_field': None, 'total_records': 0}
        
        # Business date fields to look for (prioritize business dates over system dates)
        business_date_fields = [
            'invoice_date', 'bill_date', 'payment_date', 'order_date', 
            'creditnote_date', 'date', 'transaction_date'
        ]
        
        # System date fields as fallback
        system_date_fields = [
            'created_time', 'last_modified_time', 'updated_time', 
            'created_date', 'modified_date'
        ]
        
        # All possible date fields in priority order
        all_date_fields = business_date_fields + system_date_fields
        
        # Find the first available date field
        date_field = None
        for field in all_date_fields:
            if any(field in record for record in data):
                date_field = field
                break
        
        if not date_field:
            return {'earliest_date': None, 'latest_date': None, 'date_field': None, 'total_records': len(data)}
        
        # Extract all valid dates
        valid_dates = []
        for record in data:
            if date_field in record and record[date_field]:
                date_str = str(record[date_field])
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    valid_dates.append(parsed_date)
        
        if not valid_dates:
            return {'earliest_date': None, 'latest_date': None, 'date_field': date_field, 'total_records': len(data)}
        
        # Find min and max dates
        earliest_date = min(valid_dates)
        latest_date = max(valid_dates)
        
        return {
            'earliest_date': earliest_date.strftime('%Y-%m-%d'),
            'latest_date': latest_date.strftime('%Y-%m-%d'),
            'date_field': date_field,
            'total_records': len(data),
            'records_with_dates': len(valid_dates)
        }
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse various date string formats"""
        if not date_str or date_str.lower() in ['null', 'none', '']:
            return None
        
        # Common date formats in Zoho data
        date_formats = [
            '%Y-%m-%d',           # 2025-07-12
            '%Y-%m-%d %H:%M:%S',  # 2025-07-12 10:30:00
            '%d-%m-%Y',           # 12-07-2025
            '%d/%m/%Y',           # 12/07/2025
            '%m/%d/%Y',           # 07/12/2025
            '%Y-%m-%dT%H:%M:%S',  # 2025-07-12T10:30:00
            '%Y-%m-%dT%H:%M:%SZ', # 2025-07-12T10:30:00Z
            '%Y-%m-%dT%H:%M:%S+00:00', # 2025-07-12T10:30:00+00:00
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str[:len(fmt.replace('%f', '000000'))], fmt)
            except ValueError:
                continue
        
        # Try to handle ISO format with timezone
        try:
            from dateutil.parser import parse
            return parse(date_str)
        except:
            pass
        
        return None

    def clean_field_name(self, field_name: str) -> str:
        """Clean field name for database compatibility"""
        # Replace spaces and special characters with underscores
        clean_name = field_name.lower()
        clean_name = ''.join(c if c.isalnum() else '_' for c in clean_name)
        clean_name = '_'.join(filter(None, clean_name.split('_')))  # Remove consecutive underscores
        
        # Handle reserved words and ensure it starts with letter
        if clean_name in ['order', 'group', 'where', 'select', 'from', 'table']:
            clean_name = f"field_{clean_name}"
        
        if clean_name and clean_name[0].isdigit():
            clean_name = f"field_{clean_name}"
        
        return clean_name or 'unknown_field'

    def determine_data_type(self, value: Any) -> tuple[str, Optional[int]]:
        """Determine appropriate SQLite data type for a value"""
        if value is None:
            return 'TEXT', None
        
        if isinstance(value, bool):
            return 'INTEGER', None  # SQLite uses 0/1 for boolean
        
        if isinstance(value, int):
            return 'INTEGER', None
        
        if isinstance(value, float):
            return 'REAL', None
        
        if isinstance(value, str):
            length = len(value)
            # For very long text, use TEXT without length limit
            if length > 1000:
                return 'TEXT', None
            # For shorter strings, track max length for optimization
            return 'TEXT', length
        
        if isinstance(value, (list, dict)):
            # Store complex objects as JSON text
            json_str = json.dumps(value)
            return 'TEXT', len(json_str)
        
        # Default to TEXT for unknown types
        return 'TEXT', None

    def is_primary_key_field(self, field_name: str) -> bool:
        """Check if field is likely a primary key"""
        pk_patterns = ['id', '_id', 'key', '_key']
        field_lower = field_name.lower()
        
        # Exact matches for common ID fields
        if field_lower in ['id', 'uuid', 'guid']:
            return True
        
        # Pattern matches
        for pattern in pk_patterns:
            if field_lower.endswith(pattern):
                return True
        
        return False

    def is_foreign_key_field(self, field_name: str) -> bool:
        """Check if field is likely a foreign key"""
        fk_patterns = ['_id', 'id_', 'reference', 'ref_']
        field_lower = field_name.lower()
        
        # Skip if it's a primary key
        if self.is_primary_key_field(field_name):
            return False
        
        # Pattern matches for foreign keys
        for pattern in fk_patterns:
            if pattern in field_lower:
                return True
        
        return False

    def analyze_all_json_files(self) -> Dict[str, Any]:
        """Analyze all target JSON files in the directory"""
        self.logger.info("Starting analysis of JSON files...")
        
        results = {}
        
        if self.session_based:
            # Handle session-based structure
            self.logger.info("Using session-based structure")
            latest_session_path = self._get_latest_session_data_path()
            
            if not latest_session_path:
                self.logger.warning("No session data found in session-based structure")
                return results
            
            self.logger.info(f"Using latest session data from: {latest_session_path}")
            json_files = self._find_json_files_in_session(latest_session_path)
            
            for json_file in json_files:
                json_filename = json_file.name
                table_name = self.json_to_table_map.get(json_filename)
                
                if not table_name:
                    self.logger.info(f"Skipping non-target file: {json_filename}")
                    continue
                
                self.logger.info(f"Analyzing {json_filename} -> {table_name}")
                analysis = self.analyze_json_file(json_file)
                
                if analysis:
                    results[table_name] = {
                        'json_file': json_filename,
                        'table_name': table_name,
                        'analysis': analysis,
                        'file_path': str(json_file)
                    }
        else:
            # Handle traditional flat structure
            self.logger.info("Using traditional flat structure")
            for json_filename, table_name in self.json_to_table_map.items():
                json_file = self.json_dir / json_filename
                
                if not json_file.exists():
                    self.logger.warning(f"JSON file not found: {json_file}")
                    continue
                
                self.logger.info(f"Analyzing {json_filename} -> {table_name}")
                analysis = self.analyze_json_file(json_file)
                
                if analysis:
                    results[table_name] = {
                        'json_file': json_filename,
                        'table_name': table_name,
                        'analysis': analysis,
                        'file_path': str(json_file)
                    }
        
        self.analysis_results = results
        self.logger.info(f"Analysis complete. Found {len(results)} valid JSON files.")
        
        return results

    def generate_table_summary(self) -> Dict[str, Any]:
        """Generate a summary of tables required"""
        if not self.analysis_results:
            self.analyze_all_json_files()
        
        summary = {
            'total_tables': len(self.analysis_results),
            'total_records': 0,
            'tables': {},
            'main_entities': {},
            'line_item_tables': {}
        }
        
        for table_name, table_info in self.analysis_results.items():
            record_count = table_info['analysis'].get('record_count', 0)
            column_count = len(table_info['analysis'].get('columns', {}))
            
            table_summary = {
                'record_count': record_count,
                'column_count': column_count,
                'json_file': table_info['json_file'],
                'has_data': record_count > 0
            }
            
            summary['tables'][table_name] = table_summary
            summary['total_records'] += record_count
            
            # Categorize tables
            if '_line_items' in table_name:
                summary['line_item_tables'][table_name] = table_summary
            else:
                summary['main_entities'][table_name] = table_summary
        
        return summary

    def print_analysis_summary(self):
        """Print a formatted summary of the analysis"""
        summary = self.generate_table_summary()
        
        print("\n" + "="*80)
        print("JSON TO DATABASE SYNC - TABLE ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"Total Tables Required: {summary['total_tables']}")
        print(f"Total Records to Sync: {summary['total_records']:,}")
        
        print(f"\nMAIN ENTITY TABLES ({len(summary['main_entities'])}):")
        print("-" * 60)
        print(f"{'Table Name':<25} {'Records':<12} {'Columns':<10} {'JSON File'}")
        print("-" * 60)
        
        for table_name, info in summary['main_entities'].items():
            status = "✓" if info['has_data'] else "✗"
            print(f"{table_name:<25} {info['record_count']:<12,} {info['column_count']:<10} {info['json_file']} {status}")
        
        print(f"\nLINE ITEM TABLES ({len(summary['line_item_tables'])}):")
        print("-" * 60)
        print(f"{'Table Name':<25} {'Records':<12} {'Columns':<10} {'JSON File'}")
        print("-" * 60)
        
        for table_name, info in summary['line_item_tables'].items():
            status = "✓" if info['has_data'] else "✗"
            print(f"{table_name:<25} {info['record_count']:<12,} {info['column_count']:<10} {info['json_file']} {status}")
        
        print("\n" + "="*80)

    def save_analysis_report(self, output_file: Optional[str] = None) -> str:
        """Save detailed analysis report to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"logs/json_analysis_report_{timestamp}.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'json_directory': str(self.json_dir),
            'summary': self.generate_table_summary(),
            'detailed_analysis': self.analysis_results
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Analysis report saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error saving analysis report: {str(e)}")
            return ""


def main():
    """Main function to run JSON analysis"""
    analyzer = JSONAnalyzer()
    
    try:
        # Run analysis
        results = analyzer.analyze_all_json_files()
        
        # Print summary
        analyzer.print_analysis_summary()
        
        # Save detailed report
        report_file = analyzer.save_analysis_report()
        
        print(f"\nDetailed analysis report saved to: {report_file}")
        
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
