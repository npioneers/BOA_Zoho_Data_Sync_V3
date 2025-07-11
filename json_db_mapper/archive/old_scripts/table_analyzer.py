"""
Table Analyzer - Analyzes CSV and JSON table structures
"""
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class TableAnalyzer:
    """Analyzes table structures for CSV and JSON tables in the database"""
    
    def __init__(self, db_path: str = "data/database/production.db"):
        self.db_path = Path(db_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for table analysis"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"table_analyzer_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Table Analyzer started - Logging to: {log_file}")

    def get_all_tables(self) -> Dict[str, List[str]]:
        """Get all tables categorized by CSV and JSON tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Categorize tables
            csv_tables = [table for table in all_tables if not table.startswith('json_') and not table.endswith('_map')]
            json_tables = [table for table in all_tables if table.startswith('json_')]
            mapping_tables = [table for table in all_tables if table.endswith('_map')]
            
            conn.close()
            
            result = {
                'csv_tables': csv_tables,
                'json_tables': json_tables,
                'mapping_tables': mapping_tables,
                'all_tables': all_tables
            }
            
            self.logger.info(f"Found {len(csv_tables)} CSV tables, {len(json_tables)} JSON tables, {len(mapping_tables)} mapping tables")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting tables: {e}")
            return {}

    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """Get detailed structure of a specific table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            record_count = cursor.fetchone()[0]
            
            # Structure column information
            columns = []
            for col_info in columns_info:
                columns.append({
                    'cid': col_info[0],
                    'name': col_info[1],
                    'type': col_info[2],
                    'notnull': bool(col_info[3]),
                    'default_value': col_info[4],
                    'pk': bool(col_info[5])
                })
            
            conn.close()
            
            result = {
                'table_name': table_name,
                'column_count': len(columns),
                'record_count': record_count,
                'columns': columns,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Analyzed table '{table_name}': {len(columns)} columns, {record_count} records")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing table '{table_name}': {e}")
            return {}

    def analyze_all_csv_tables(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all CSV tables in the database"""
        tables_info = self.get_all_tables()
        csv_tables = tables_info.get('csv_tables', [])
        
        results = {}
        for table_name in csv_tables:
            self.logger.info(f"Analyzing CSV table: {table_name}")
            results[table_name] = self.get_table_structure(table_name)
            
        self.logger.info(f"Completed analysis of {len(results)} CSV tables")
        return results

    def analyze_all_json_tables(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all JSON tables in the database"""
        tables_info = self.get_all_tables()
        json_tables = tables_info.get('json_tables', [])
        
        results = {}
        for table_name in json_tables:
            self.logger.info(f"Analyzing JSON table: {table_name}")
            results[table_name] = self.get_table_structure(table_name)
            
        self.logger.info(f"Completed analysis of {len(results)} JSON tables")
        return results

    def generate_table_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report for all tables"""
        self.logger.info("Generating comprehensive table analysis report...")
        
        # Get all table categories
        tables_info = self.get_all_tables()
        
        # Analyze CSV and JSON tables
        csv_analysis = self.analyze_all_csv_tables()
        json_analysis = self.analyze_all_json_tables()
        
        # Create summary
        report = {
            'generated_at': datetime.now().isoformat(),
            'database_path': str(self.db_path),
            'summary': {
                'total_tables': len(tables_info.get('all_tables', [])),
                'csv_tables_count': len(tables_info.get('csv_tables', [])),
                'json_tables_count': len(tables_info.get('json_tables', [])),
                'mapping_tables_count': len(tables_info.get('mapping_tables', []))
            },
            'table_categories': tables_info,
            'csv_table_analysis': csv_analysis,
            'json_table_analysis': json_analysis
        }
        
        self.logger.info("Table analysis report generated successfully")
        return report

    def identify_matching_tables(self) -> Dict[str, Dict[str, str]]:
        """Identify CSV and JSON tables that might represent the same entities"""
        tables_info = self.get_all_tables()
        csv_tables = tables_info.get('csv_tables', [])
        json_tables = tables_info.get('json_tables', [])
        
        matches = {}
        
        # Define common entity mappings
        entity_mappings = {
            'invoices': 'json_invoices',
            'contacts': 'json_contacts',
            'items': 'json_items',
            'bills': 'json_bills',
            'organizations': 'json_organizations',
            'customer_payments': 'json_customer_payments',
            'vendor_payments': 'json_vendor_payments',
            'sales_orders': 'json_sales_orders',
            'purchase_orders': 'json_purchase_orders',
            'credit_notes': 'json_credit_notes'
        }
        
        for csv_table in csv_tables:
            if csv_table in entity_mappings:
                json_equivalent = entity_mappings[csv_table]
                if json_equivalent in json_tables:
                    matches[csv_table] = {
                        'csv_table': csv_table,
                        'json_table': json_equivalent,
                        'entity_type': csv_table
                    }
        
        self.logger.info(f"Identified {len(matches)} matching table pairs")
        return matches
