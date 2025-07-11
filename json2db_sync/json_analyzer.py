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
            json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                       else config.get_consolidated_path())
        
        self.json_dir = Path(json_dir)
        self.setup_logging()
        
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
            'invoices_line_items.json': 'json_invoices_line_items',
            'bills_line_items.json': 'json_bills_line_items',
            'salesorders_line_items.json': 'json_salesorders_line_items',
            'purchaseorders_line_items.json': 'json_purchaseorders_line_items',
            'creditnotes_line_items.json': 'json_creditnotes_line_items'
        }
        
        # Analysis results
        self.analysis_results = {}
        self.table_schemas = {}
        
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
            
            result = {
                'record_count': len(data),
                'columns': columns,
                'sample_record': sample_record
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
        self.logger.info("Starting analysis of consolidated JSON files...")
        
        results = {}
        
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
                    'analysis': analysis
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
