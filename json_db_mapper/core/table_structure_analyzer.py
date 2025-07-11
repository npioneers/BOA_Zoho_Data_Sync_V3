"""
Table Structure Analyzer
Analyzes database table structures and extracts field information for mapping
"""
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class TableStructureAnalyzer:
    """Analyzes database table structures to extract field information"""
    
    def __init__(self, db_path: str = "data/database/production.db"):
        self.db_path = Path(db_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for analyzer"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"table_structure_analyzer_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Table Structure Analyzer started - Logging to: {log_file}")

    def get_all_tables(self) -> Dict[str, List[str]]:
        """Get all tables categorized by CSV and JSON"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Categorize tables
            csv_tables = [table for table in all_tables if not table.startswith('json_') and not table.endswith('_map') and not table.startswith('map_')]
            json_tables = [table for table in all_tables if table.startswith('json_') and not table.startswith('map_')]
            
            conn.close()
            
            self.logger.info(f"Found {len(csv_tables)} CSV tables and {len(json_tables)} JSON tables")
            
            return {
                'csv_tables': csv_tables,
                'json_tables': json_tables,
                'all_tables': all_tables
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tables: {e}")
            return {'csv_tables': [], 'json_tables': [], 'all_tables': []}

    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """Get detailed structure information for a specific table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table info using PRAGMA
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            record_count = cursor.fetchone()[0]
            
            # Process column information
            columns = []
            for col_info in columns_info:
                column = {
                    'name': col_info[1],
                    'type': col_info[2],
                    'not_null': bool(col_info[3]),
                    'default_value': col_info[4],
                    'primary_key': bool(col_info[5]),
                    'position': col_info[0]
                }
                columns.append(column)
            
            conn.close()
            
            table_structure = {
                'table_name': table_name,
                'column_count': len(columns),
                'record_count': record_count,
                'columns': columns,
                'table_type': 'json' if table_name.startswith('json_') else 'csv'
            }
            
            self.logger.info(f"Analyzed table {table_name}: {len(columns)} columns, {record_count} records")
            return table_structure
            
        except Exception as e:
            self.logger.error(f"Error analyzing table {table_name}: {e}")
            return {}

    def analyze_all_tables(self) -> Dict[str, Any]:
        """Analyze all tables and return comprehensive structure information"""
        self.logger.info("Starting comprehensive table analysis...")
        
        # Get all tables
        tables_info = self.get_all_tables()
        
        analysis_results = {
            'csv_tables': {},
            'json_tables': {},
            'summary': {
                'total_csv_tables': len(tables_info['csv_tables']),
                'total_json_tables': len(tables_info['json_tables']),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
        # Analyze CSV tables
        self.logger.info("Analyzing CSV tables...")
        for table_name in tables_info['csv_tables']:
            structure = self.get_table_structure(table_name)
            if structure:
                analysis_results['csv_tables'][table_name] = structure
        
        # Analyze JSON tables
        self.logger.info("Analyzing JSON tables...")
        for table_name in tables_info['json_tables']:
            structure = self.get_table_structure(table_name)
            if structure:
                analysis_results['json_tables'][table_name] = structure
        
        self.logger.info(f"Analysis complete: {len(analysis_results['csv_tables'])} CSV tables, {len(analysis_results['json_tables'])} JSON tables")
        return analysis_results

    def print_table_summary(self, analysis_results: Dict[str, Any]):
        """Print a formatted summary of table analysis"""
        print("\n" + "="*80)
        print("TABLE STRUCTURE ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"\nCSV TABLES ({analysis_results['summary']['total_csv_tables']}):")
        print("-" * 60)
        print(f"{'Table Name':<30} {'Columns':<10} {'Records':<15}")
        print("-" * 60)
        
        for table_name, info in analysis_results['csv_tables'].items():
            print(f"{table_name:<30} {info['column_count']:<10} {info['record_count']:<15}")
        
        print(f"\nJSON TABLES ({analysis_results['summary']['total_json_tables']}):")
        print("-" * 60)
        print(f"{'Table Name':<30} {'Columns':<10} {'Records':<15}")
        print("-" * 60)
        
        for table_name, info in analysis_results['json_tables'].items():
            print(f"{table_name:<30} {info['column_count']:<10} {info['record_count']:<15}")
        
        print("="*80)

    def get_table_fields_list(self, table_name: str) -> List[str]:
        """Get a simple list of field names for a table"""
        structure = self.get_table_structure(table_name)
        if structure and 'columns' in structure:
            return [col['name'] for col in structure['columns']]
        return []


def main():
    """Test the table structure analyzer"""
    analyzer = TableStructureAnalyzer()
    
    # Analyze all tables
    results = analyzer.analyze_all_tables()
    
    # Print summary
    analyzer.print_table_summary(results)
    
    # Test specific table analysis
    print("\nTesting specific table analysis:")
    if results['csv_tables']:
        first_csv_table = list(results['csv_tables'].keys())[0]
        fields = analyzer.get_table_fields_list(first_csv_table)
        print(f"{first_csv_table} fields: {fields[:5]}..." if len(fields) > 5 else f"{first_csv_table} fields: {fields}")
    
    if results['json_tables']:
        first_json_table = list(results['json_tables'].keys())[0]
        fields = analyzer.get_table_fields_list(first_json_table)
        print(f"{first_json_table} fields: {fields[:5]}..." if len(fields) > 5 else f"{first_json_table} fields: {fields}")


if __name__ == "__main__":
    main()
