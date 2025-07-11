"""
JSON-DB Mapper CLI Runner
Main entry point for JSON-DB mapping operations
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from table_structure_analyzer import TableStructureAnalyzer
from mapping_table_creator_new import MappingTableCreator
from field_mapper import FieldMapper
from schema_updater import SchemaUpdater


class JSONDBMapperCLI:
    """Command line interface for JSON-DB mapping operations"""
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for CLI operations"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"json_db_mapper_cli_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"JSON-DB Mapper CLI started - Logging to: {log_file}")

    def analyze_tables(self, db_path: str) -> Dict[str, Any]:
        """Analyze table structures in a database"""
        self.logger.info(f"Analyzing tables in database: {db_path}")
        
        analyzer = TableStructureAnalyzer(db_path)
        return analyzer.analyze_all_tables()

    def create_mapping_tables(self, db_path: str, table_structures: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create mapping tables for CSV and JSON tables"""
        self.logger.info(f"Creating mapping tables for database: {db_path}")
        
        if table_structures is None:
            table_structures = self.analyze_tables(db_path)
        
        creator = MappingTableCreator(db_path)
        return creator.create_all_mapping_tables(table_structures)

    def print_analysis_summary(self, analysis: Dict[str, Any]):
        """Print a formatted summary of table analysis"""
        print("\n" + "="*80)
        print("TABLE STRUCTURE ANALYSIS SUMMARY")
        print("="*80)
        
        csv_count = len(analysis.get('csv_tables', {}))
        json_count = len(analysis.get('json_tables', {}))
        
        print(f"\nDatabase contains:")
        print(f"  CSV Tables:  {csv_count}")
        print(f"  JSON Tables: {json_count}")
        
        if csv_count > 0:
            print(f"\nCSV TABLES ({csv_count}):")
            print("-" * 60)
            for table_name, info in analysis.get('csv_tables', {}).items():
                record_count = info.get('record_count', 0)
                column_count = len(info.get('columns', []))
                print(f"  {table_name:<30} {column_count:>3} cols  {record_count:>6} records")
        
        if json_count > 0:
            print(f"\nJSON TABLES ({json_count}):")
            print("-" * 60)
            for table_name, info in analysis.get('json_tables', {}).items():
                record_count = info.get('record_count', 0)
                column_count = len(info.get('columns', []))
                print(f"  {table_name:<30} {column_count:>3} cols  {record_count:>6} records")
        
        print("="*80)

    def get_default_database_paths(self) -> Dict[str, str]:
        """Get default database paths"""
        return {
            'production': "../data/database/production.db",
            'json_sync': "../backups/json_sync_backup_20250707_222640.db"
        }

    def update_schema(self, db_path: str) -> Dict[str, Any]:
        """Update schema to add mapped_CSV column to JSON tables"""
        self.logger.info(f"Updating schema for database: {db_path}")
        
        updater = SchemaUpdater(db_path)
        return updater.update_all_json_tables()

    def map_fields(self, db_path: str, min_similarity: float = 0.3) -> Dict[str, Any]:
        """Map JSON tables to CSV tables based on field similarity"""
        self.logger.info(f"Mapping fields for database: {db_path}")
        
        mapper = FieldMapper(db_path)
        return mapper.map_all_json_tables(min_similarity)

    def run_full_analysis(self, production_db: str = None, json_db: str = None):
        """Run full analysis on both databases"""
        default_paths = self.get_default_database_paths()
        
        production_db = production_db or default_paths['production']
        json_db = json_db or default_paths['json_sync']
        
        print("JSON-DB MAPPER - FULL ANALYSIS")
        print("="*80)
        print(f"Production DB: {production_db}")
        print(f"JSON Sync DB:  {json_db}")
        print("="*80)
        
        # Analyze production database (CSV tables)
        print("\n1. ANALYZING PRODUCTION DATABASE (CSV TABLES)")
        print("-" * 50)
        try:
            prod_analysis = self.analyze_tables(production_db)
            self.print_analysis_summary(prod_analysis)
        except Exception as e:
            print(f"Error analyzing production database: {e}")
            return
        
        # Analyze JSON database
        print("\n2. ANALYZING JSON SYNC DATABASE")
        print("-" * 50)
        try:
            json_analysis = self.analyze_tables(json_db)
            self.print_analysis_summary(json_analysis)
        except Exception as e:
            print(f"Error analyzing JSON database: {e}")
            return
        
        print("\n3. CREATING MAPPING TABLES")
        print("-" * 50)
        
        # Create mapping tables for production database
        try:
            print("\nCreating CSV mapping tables...")
            prod_results = self.create_mapping_tables(production_db, prod_analysis)
            print(f"✅ Created {prod_results['summary']['csv_tables_success']}/{prod_results['summary']['csv_tables_processed']} CSV mapping tables")
        except Exception as e:
            print(f"❌ Error creating CSV mapping tables: {e}")
        
        # Create mapping tables for JSON database
        try:
            print("\nCreating JSON mapping tables...")
            json_results = self.create_mapping_tables(json_db, json_analysis)
            print(f"✅ Created {json_results['summary']['json_tables_success']}/{json_results['summary']['json_tables_processed']} JSON mapping tables")
        except Exception as e:
            print(f"❌ Error creating JSON mapping tables: {e}")
        
        print("\n✅ FULL ANALYSIS COMPLETE")
        print("="*80)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='JSON-DB Mapper CLI')
    parser.add_argument('command', choices=['analyze', 'create-maps', 'map-fields', 'update-schema', 'full'], 
                       help='Command to execute')
    parser.add_argument('--production-db', help='Path to production database')
    parser.add_argument('--json-db', help='Path to JSON sync database')
    parser.add_argument('--db', help='Path to specific database (for analyze/create-maps/map-fields/update-schema)')
    parser.add_argument('--min-similarity', type=float, default=0.3, help='Minimum similarity score for field mapping')
    
    args = parser.parse_args()
    
    cli = JSONDBMapperCLI()
    
    if args.command == 'analyze':
        if not args.db:
            print("Error: --db argument required for analyze command")
            sys.exit(1)
        
        analysis = cli.analyze_tables(args.db)
        cli.print_analysis_summary(analysis)
        
    elif args.command == 'create-maps':
        if not args.db:
            print("Error: --db argument required for create-maps command")
            sys.exit(1)
        
        results = cli.create_mapping_tables(args.db)
        creator = MappingTableCreator(args.db)
        creator.print_mapping_summary(results)
        
    elif args.command == 'update-schema':
        if not args.db:
            print("Error: --db argument required for update-schema command")
            sys.exit(1)
        
        results = cli.update_schema(args.db)
        updater = SchemaUpdater(args.db)
        updater.print_update_results(results)
        
    elif args.command == 'map-fields':
        if not args.db:
            print("Error: --db argument required for map-fields command")
            sys.exit(1)
        
        results = cli.map_fields(args.db, args.min_similarity)
        mapper = FieldMapper(args.db)
        mapper.print_mapping_results(results)
        
    elif args.command == 'full':
        cli.run_full_analysis(args.production_db, args.json_db)


if __name__ == "__main__":
    main()
