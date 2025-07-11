"""
Schema Updater
Adds the mapped_CSV column to existing JSON mapping tables
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime


class SchemaUpdater:
    """Updates existing mapping tables to include mapped_CSV column"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for schema updater"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"schema_updater_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Schema Updater started - Logging to: {log_file}")

    def get_json_mapping_tables(self) -> list:
        """Get all JSON mapping tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_json_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            self.logger.error(f"Error getting JSON mapping tables: {e}")
            return []

    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            conn.close()
            return column_name in columns
            
        except Exception as e:
            self.logger.error(f"Error checking column {column_name} in {table_name}: {e}")
            return False

    def add_mapped_csv_column(self, table_name: str) -> bool:
        """Add mapped_CSV column to a table"""
        try:
            if self.check_column_exists(table_name, 'mapped_CSV'):
                self.logger.info(f"Column mapped_CSV already exists in {table_name}")
                return True
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN mapped_CSV TEXT")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added mapped_CSV column to {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding mapped_CSV column to {table_name}: {e}")
            return False

    def update_all_json_tables(self) -> dict:
        """Add mapped_CSV column to all JSON mapping tables"""
        self.logger.info("Starting schema update for JSON mapping tables...")
        
        results = {
            'updated_tables': [],
            'failed_tables': [],
            'already_updated': [],
            'summary': {
                'total_tables': 0,
                'successful_updates': 0,
                'failed_updates': 0,
                'already_had_column': 0
            }
        }
        
        json_tables = self.get_json_mapping_tables()
        results['summary']['total_tables'] = len(json_tables)
        
        for table in json_tables:
            self.logger.info(f"Processing {table}...")
            
            if self.check_column_exists(table, 'mapped_CSV'):
                results['already_updated'].append(table)
                results['summary']['already_had_column'] += 1
                continue
            
            if self.add_mapped_csv_column(table):
                results['updated_tables'].append(table)
                results['summary']['successful_updates'] += 1
            else:
                results['failed_tables'].append(table)
                results['summary']['failed_updates'] += 1
        
        self.logger.info(f"Schema update complete: {results['summary']['successful_updates']} updated, {results['summary']['already_had_column']} already had column")
        return results

    def print_update_results(self, results: dict):
        """Print formatted update results"""
        print("\n" + "="*80)
        print("SCHEMA UPDATE RESULTS")
        print("="*80)
        
        print(f"\nSUMMARY:")
        print(f"  Total tables: {results['summary']['total_tables']}")
        print(f"  Successfully updated: {results['summary']['successful_updates']}")
        print(f"  Already had column: {results['summary']['already_had_column']}")
        print(f"  Failed updates: {results['summary']['failed_updates']}")
        
        if results['updated_tables']:
            print(f"\nUPDATED TABLES ({len(results['updated_tables'])}):")
            for table in results['updated_tables']:
                print(f"  ✅ {table}")
        
        if results['already_updated']:
            print(f"\nALREADY HAD COLUMN ({len(results['already_updated'])}):")
            for table in results['already_updated']:
                print(f"  ℹ️  {table}")
        
        if results['failed_tables']:
            print(f"\nFAILED UPDATES ({len(results['failed_tables'])}):")
            for table in results['failed_tables']:
                print(f"  ❌ {table}")
        
        print("="*80)


def main():
    """Test the schema updater"""
    db_paths = [
        "../backups/production_db_refactor_complete_20250707_211611.db",
        "../backups/json_sync_backup_20250707_222640.db"
    ]
    
    for db_path in db_paths:
        print(f"\nUpdating schema for: {db_path}")
        print("-" * 60)
        
        try:
            updater = SchemaUpdater(db_path)
            results = updater.update_all_json_tables()
            updater.print_update_results(results)
        except Exception as e:
            print(f"Error processing {db_path}: {e}")


if __name__ == "__main__":
    main()
