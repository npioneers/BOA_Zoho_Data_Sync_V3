"""
JSON Data Sync Summary Report Generator
Creates comprehensive reports on the JSON data sync process and table contents
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import csv


class SyncSummaryReporter:
    """Generates comprehensive summary reports for JSON data sync process"""
    
    def __init__(self, db_path: str = "data/database/production.db"):
        self.db_path = Path(db_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for report generation"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"sync_summary_report_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Sync Summary Report started - Logging to: {log_file}")

    def get_database_info(self) -> Dict[str, Any]:
        """Get general database information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database file size
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024)
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Separate JSON and CSV tables
            json_tables = [t for t in all_tables if t.startswith('json_')]
            csv_tables = [t for t in all_tables if not t.startswith('json_') and not t.startswith('sqlite_')]
            
            conn.close()
            
            return {
                'database_size_mb': round(db_size_mb, 2),
                'total_tables': len(all_tables),
                'json_tables_count': len(json_tables),
                'csv_tables_count': len(csv_tables),
                'json_tables': json_tables,
                'csv_tables': csv_tables
            }
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {e}")
            return {}

    def get_table_record_counts(self) -> Dict[str, int]:
        """Get record counts for all tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            record_counts = {}
            for table in tables:
                if table.startswith('sqlite_'):
                    continue
                    
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    record_counts[table] = count
                except Exception as e:
                    self.logger.warning(f"Error counting records in {table}: {e}")
                    record_counts[table] = 0
            
            conn.close()
            return record_counts
            
        except Exception as e:
            self.logger.error(f"Error getting record counts: {e}")
            return {}

    def get_json_table_details(self) -> Dict[str, Dict]:
        """Get detailed information about JSON tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get JSON tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%'")
            json_tables = [row[0] for row in cursor.fetchall()]
            
            table_details = {}
            
            for table in json_tables:
                try:
                    # Get record count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    record_count = cursor.fetchone()[0]
                    
                    # Get column count
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    column_count = len(columns)
                    
                    # Get sample of data to check for recent records
                    cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                    sample_data = cursor.fetchall()
                    
                    # Check for date columns and get date range
                    date_range = self.get_date_range_for_table(cursor, table, columns)
                    
                    table_details[table] = {
                        'record_count': record_count,
                        'column_count': column_count,
                        'columns': [col[1] for col in columns],  # Column names
                        'date_range': date_range,
                        'has_data': record_count > 0
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing table {table}: {e}")
                    table_details[table] = {
                        'record_count': 0,
                        'column_count': 0,
                        'columns': [],
                        'date_range': None,
                        'has_data': False,
                        'error': str(e)
                    }
            
            conn.close()
            return table_details
            
        except Exception as e:
            self.logger.error(f"Error getting JSON table details: {e}")
            return {}

    def get_date_range_for_table(self, cursor, table_name: str, columns: List) -> Optional[Dict]:
        """Get date range for a table if it has date columns"""
        date_columns = []
        for col in columns:
            col_name = col[1].lower()
            if any(date_word in col_name for date_word in ['date', 'time', 'created', 'modified', 'updated']):
                date_columns.append(col[1])
        
        if not date_columns:
            return None
        
        date_info = {}
        for date_col in date_columns[:3]:  # Check first 3 date columns
            try:
                cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name} WHERE {date_col} IS NOT NULL AND {date_col} != ''")
                result = cursor.fetchone()
                if result and result[0] and result[1]:
                    date_info[date_col] = {
                        'min_date': result[0],
                        'max_date': result[1]
                    }
            except Exception:
                continue
        
        return date_info if date_info else None

    def get_csv_vs_json_comparison(self) -> Dict[str, Any]:
        """Compare CSV and JSON table record counts for similar entities"""
        record_counts = self.get_table_record_counts()
        
        # Define mappings between CSV and JSON tables
        comparisons = {
            'invoices': {
                'csv_table': 'invoices',
                'json_table': 'json_invoices',
                'csv_count': record_counts.get('invoices', 0),
                'json_count': record_counts.get('json_invoices', 0)
            },
            'items': {
                'csv_table': 'items',
                'json_table': 'json_items', 
                'csv_count': record_counts.get('items', 0),
                'json_count': record_counts.get('json_items', 0)
            },
            'contacts': {
                'csv_table': 'contacts',
                'json_table': 'json_contacts',
                'csv_count': record_counts.get('contacts', 0),
                'json_count': record_counts.get('json_contacts', 0)
            }
        }
        
        # Calculate differences
        for entity, data in comparisons.items():
            csv_count = data['csv_count']
            json_count = data['json_count']
            if csv_count > 0:
                data['percentage_in_json'] = round((json_count / csv_count) * 100, 1)
                data['difference'] = csv_count - json_count
            else:
                data['percentage_in_json'] = 0
                data['difference'] = 0
        
        return comparisons

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive sync summary report"""
        self.logger.info("Generating comprehensive sync summary report...")
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'database_info': self.get_database_info(),
            'record_counts': self.get_table_record_counts(),
            'json_table_details': self.get_json_table_details(),
            'csv_vs_json_comparison': self.get_csv_vs_json_comparison()
        }
        
        # Calculate summary statistics
        json_counts = {k: v for k, v in report['record_counts'].items() if k.startswith('json_')}
        csv_counts = {k: v for k, v in report['record_counts'].items() if not k.startswith('json_') and not k.startswith('sqlite_')}
        
        report['summary_statistics'] = {
            'total_json_records': sum(json_counts.values()),
            'total_csv_records': sum(csv_counts.values()),
            'json_tables_populated': len([k for k, v in json_counts.items() if v > 0]),
            'csv_tables_available': len(csv_counts),
            'largest_json_table': max(json_counts.items(), key=lambda x: x[1]) if json_counts else None,
            'smallest_json_table': min([item for item in json_counts.items() if item[1] > 0], key=lambda x: x[1]) if json_counts else None
        }
        
        return report

    def print_summary_report(self, report: Dict[str, Any]):
        """Print a formatted summary report"""
        print("\n" + "="*100)
        print("ZOHO DATA SYNC - COMPREHENSIVE SUMMARY REPORT")
        print("="*100)
        print(f"Generated: {report['report_timestamp']}")
        print(f"Database: {self.db_path}")
        print(f"Database Size: {report['database_info'].get('database_size_mb', 0)} MB")
        
        print(f"\n📊 OVERVIEW")
        print("-" * 50)
        stats = report['summary_statistics']
        print(f"Total JSON Records: {stats['total_json_records']:,}")
        print(f"Total CSV Records: {stats['total_csv_records']:,}")
        print(f"JSON Tables Populated: {stats['json_tables_populated']}/15")
        print(f"CSV Tables Available: {stats['csv_tables_available']}")
        
        if stats['largest_json_table']:
            print(f"Largest JSON Table: {stats['largest_json_table'][0]} ({stats['largest_json_table'][1]:,} records)")
        if stats['smallest_json_table']:
            print(f"Smallest JSON Table: {stats['smallest_json_table'][0]} ({stats['smallest_json_table'][1]:,} records)")
        
        print(f"\n📋 JSON TABLES DETAILED BREAKDOWN")
        print("-" * 80)
        print(f"{'Table Name':<30} {'Records':<12} {'Columns':<10} {'Status':<10} {'Date Range'}")
        print("-" * 80)
        
        json_details = report['json_table_details']
        main_entities = []
        line_items = []
        
        for table_name, details in json_details.items():
            if '_line_items' in table_name:
                line_items.append((table_name, details))
            else:
                main_entities.append((table_name, details))
        
        print("MAIN ENTITIES:")
        for table_name, details in sorted(main_entities):
            status = "✓" if details['has_data'] else "✗"
            date_info = ""
            if details.get('date_range'):
                date_ranges = list(details['date_range'].values())
                if date_ranges:
                    # Get the latest date, handling different formats
                    max_dates = []
                    for dr in date_ranges:
                        max_date = dr['max_date']
                        if isinstance(max_date, str) and len(max_date) >= 10:
                            max_dates.append(max_date)
                    
                    if max_dates:
                        # Sort and get the latest date string
                        max_dates.sort()
                        date_info = max_dates[-1][:10]
            
            print(f"{table_name:<30} {details['record_count']:<12,} {details['column_count']:<10} {status:<10} {date_info}")
        
        print("\nLINE ITEM TABLES:")
        for table_name, details in sorted(line_items):
            status = "✓" if details['has_data'] else "✗"
            print(f"{table_name:<30} {details['record_count']:<12,} {details['column_count']:<10} {status:<10}")
        
        print(f"\n🔄 CSV vs JSON COMPARISON")
        print("-" * 60)
        print(f"{'Entity':<15} {'CSV Records':<12} {'JSON Records':<12} {'Filtered %':<12} {'Difference'}")
        print("-" * 60)
        
        comparison = report['csv_vs_json_comparison']
        for entity, data in comparison.items():
            if data['csv_count'] > 0:  # Only show entities that exist in CSV
                print(f"{entity:<15} {data['csv_count']:<12,} {data['json_count']:<12,} {data['percentage_in_json']:<11}% {data['difference']:,}")
        
        print("="*100)

    def save_report_to_file(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save the report to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/sync_summary_report_{timestamp}.json"
        
        report_path = Path(filename)
        report_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Summary report saved to: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            return ""

    def export_table_summary_csv(self, report: Dict[str, Any]) -> str:
        """Export table summary to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = Path(f"reports/table_summary_{timestamp}.csv")
        csv_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Table Name', 'Table Type', 'Record Count', 'Column Count', 'Has Data', 'Latest Date'])
                
                # Write JSON table data
                json_details = report['json_table_details']
                for table_name, details in sorted(json_details.items()):
                    table_type = "Line Items" if '_line_items' in table_name else "Main Entity"
                    latest_date = ""
                    if details.get('date_range'):
                        date_ranges = list(details['date_range'].values())
                        if date_ranges:
                            # Get the latest date, handling different formats
                            max_dates = []
                            for dr in date_ranges:
                                max_date = dr['max_date']
                                if isinstance(max_date, str) and len(max_date) >= 10:
                                    max_dates.append(max_date)
                            
                            if max_dates:
                                max_dates.sort()
                                latest_date = max_dates[-1]
                    
                    writer.writerow([
                        table_name,
                        table_type,
                        details['record_count'],
                        details['column_count'],
                        'Yes' if details['has_data'] else 'No',
                        latest_date
                    ])
            
            self.logger.info(f"Table summary CSV exported to: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            return ""


def main():
    """Main function to generate summary report"""
    reporter = SyncSummaryReporter()
    
    try:
        # Generate comprehensive report
        report = reporter.generate_comprehensive_report()
        
        # Print summary to console
        reporter.print_summary_report(report)
        
        # Save detailed report
        json_file = reporter.save_report_to_file(report)
        
        # Export CSV summary
        csv_file = reporter.export_table_summary_csv(report)
        
        print(f"\n📁 FILES GENERATED:")
        print(f"  JSON Report: {json_file}")
        print(f"  CSV Summary: {csv_file}")
        
    except Exception as e:
        logging.error(f"Report generation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
