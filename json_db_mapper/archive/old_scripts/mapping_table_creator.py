"""
Mapping Table Creator
Creates skeleton mapping tables for CSV and JSON field mappings
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class MappingTableCreator:
    """Creates and manages mapping tables for CSV and JSON field mappings"""
    
    def __init__(self, db_path: str = "data/database/production.db"):
        self.db_path = Path(db_path)
        self.setup_logging()
        
        # Define table entities that will have mapping tables
        self.csv_entities = [
            'bills', 'contacts', 'credit_notes', 'customer_payments', 
            'invoices', 'items', 'organizations', 'purchase_orders', 
            'sales_orders', 'vendor_payments'
        ]
        
        self.json_entities = [
            'json_bills', 'json_contacts', 'json_credit_notes', 'json_customer_payments',
            'json_invoices', 'json_items', 'json_organizations', 'json_purchase_orders',
            'json_sales_orders', 'json_vendor_payments', 'json_bills_line_items',
            'json_creditnotes_line_items', 'json_invoices_line_items',
            'json_purchaseorders_line_items', 'json_salesorders_line_items'
        ]

    def setup_logging(self):
        """Setup logging for mapping table creation"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"mapping_table_creator_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Mapping Table Creator started - Logging to: {log_file}")

    def create_csv_mapping_table_schema(self, entity_name: str) -> str:
        """Generate CREATE TABLE SQL for CSV mapping table"""
        table_name = f"csv_{entity_name}_map"
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name VARCHAR(255) NOT NULL,
            field_order INTEGER NOT NULL,
            data_type VARCHAR(50),
            max_length INTEGER,
            is_nullable BOOLEAN DEFAULT 1,
            is_primary_key BOOLEAN DEFAULT 0,
            sample_values TEXT,
            description TEXT,
            created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(field_name)
        );
        """
        return sql

    def create_json_mapping_table_schema(self, entity_name: str) -> str:
        """Generate CREATE TABLE SQL for JSON mapping table"""
        table_name = f"{entity_name}_map"
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name VARCHAR(255) NOT NULL,
            field_order INTEGER NOT NULL,
            data_type VARCHAR(50),
            max_length INTEGER,
            is_nullable BOOLEAN DEFAULT 1,
            is_primary_key BOOLEAN DEFAULT 0,
            sample_values TEXT,
            description TEXT,
            created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(field_name)
        );
        """
        return sql

    def create_indexes_for_mapping_table(self, table_name: str) -> List[str]:
        """Generate index SQL statements for mapping table"""
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_field_name ON {table_name}(field_name);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_field_order ON {table_name}(field_order);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_data_type ON {table_name}(data_type);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_primary_key ON {table_name}(is_primary_key);"
        ]
        return indexes

    def create_all_csv_mapping_tables(self) -> Dict[str, Any]:
        """Create all CSV mapping tables"""
        results = {
            'success': True,
            'tables_created': [],
            'tables_failed': [],
            'indexes_created': 0,
            'errors': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for entity in self.csv_entities:
                try:
                    self.logger.info(f"Creating CSV mapping table for: {entity}")
                    
                    # Create the mapping table
                    table_sql = self.create_csv_mapping_table_schema(entity)
                    cursor.execute(table_sql)
                    
                    # Create indexes
                    table_name = f"csv_{entity}_map"
                    index_sqls = self.create_indexes_for_mapping_table(table_name)
                    for index_sql in index_sqls:
                        cursor.execute(index_sql)
                        results['indexes_created'] += 1
                    
                    results['tables_created'].append(table_name)
                    self.logger.info(f"Successfully created CSV mapping table: {table_name}")
                    
                except Exception as e:
                    error_msg = f"Error creating CSV mapping table for {entity}: {str(e)}"
                    self.logger.error(error_msg)
                    results['tables_failed'].append(entity)
                    results['errors'].append(error_msg)
                    results['success'] = False
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
        
        return results

    def create_all_json_mapping_tables(self) -> Dict[str, Any]:
        """Create all JSON mapping tables"""
        results = {
            'success': True,
            'tables_created': [],
            'tables_failed': [],
            'indexes_created': 0,
            'errors': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for entity in self.json_entities:
                try:
                    self.logger.info(f"Creating JSON mapping table for: {entity}")
                    
                    # Create the mapping table
                    table_sql = self.create_json_mapping_table_schema(entity)
                    cursor.execute(table_sql)
                    
                    # Create indexes
                    table_name = f"{entity}_map"
                    index_sqls = self.create_indexes_for_mapping_table(table_name)
                    for index_sql in index_sqls:
                        cursor.execute(index_sql)
                        results['indexes_created'] += 1
                    
                    results['tables_created'].append(table_name)
                    self.logger.info(f"Successfully created JSON mapping table: {table_name}")
                    
                except Exception as e:
                    error_msg = f"Error creating JSON mapping table for {entity}: {str(e)}"
                    self.logger.error(error_msg)
                    results['tables_failed'].append(entity)
                    results['errors'].append(error_msg)
                    results['success'] = False
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
        
        return results

    def create_all_mapping_tables(self) -> Dict[str, Any]:
        """Create all mapping tables (both CSV and JSON)"""
        self.logger.info("Starting creation of all mapping tables...")
        
        # Create CSV mapping tables
        csv_results = self.create_all_csv_mapping_tables()
        
        # Create JSON mapping tables  
        json_results = self.create_all_json_mapping_tables()
        
        # Combine results
        combined_results = {
            'success': csv_results['success'] and json_results['success'],
            'csv_tables_created': csv_results['tables_created'],
            'json_tables_created': json_results['tables_created'],
            'total_tables_created': len(csv_results['tables_created']) + len(json_results['tables_created']),
            'csv_tables_failed': csv_results['tables_failed'],
            'json_tables_failed': json_results['tables_failed'],
            'total_indexes_created': csv_results['indexes_created'] + json_results['indexes_created'],
            'errors': csv_results['errors'] + json_results['errors']
        }
        
        # Log summary
        if combined_results['success']:
            self.logger.info(f"Successfully created all mapping tables:")
            self.logger.info(f"- CSV mapping tables: {len(csv_results['tables_created'])}")
            self.logger.info(f"- JSON mapping tables: {len(json_results['tables_created'])}")
            self.logger.info(f"- Total indexes created: {combined_results['total_indexes_created']}")
        else:
            self.logger.error(f"Some mapping tables failed to create:")
            for error in combined_results['errors']:
                self.logger.error(f"- {error}")
        
        return combined_results

    def verify_mapping_tables(self) -> Dict[str, Any]:
        """Verify that all mapping tables were created successfully"""
        results = {
            'csv_tables_verified': [],
            'json_tables_verified': [],
            'missing_tables': [],
            'total_verified': 0
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check CSV mapping tables
            for entity in self.csv_entities:
                table_name = f"csv_{entity}_map"
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    results['csv_tables_verified'].append(table_name)
                else:
                    results['missing_tables'].append(table_name)
            
            # Check JSON mapping tables
            for entity in self.json_entities:
                table_name = f"{entity}_map"
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    results['json_tables_verified'].append(table_name)
                else:
                    results['missing_tables'].append(table_name)
            
            results['total_verified'] = len(results['csv_tables_verified']) + len(results['json_tables_verified'])
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error verifying mapping tables: {str(e)}")
        
        return results

    def print_mapping_tables_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of mapping tables created"""
        print("\n" + "="*80)
        print("MAPPING TABLES CREATION SUMMARY")
        print("="*80)
        
        if results['success']:
            print(f"✓ SUCCESS: All mapping tables created successfully")
        else:
            print(f"✗ PARTIAL SUCCESS: Some tables failed to create")
        
        print(f"\nCSV MAPPING TABLES ({len(results['csv_tables_created'])}):")
        print("-" * 50)
        for table in results['csv_tables_created']:
            print(f"✓ {table}")
        
        print(f"\nJSON MAPPING TABLES ({len(results['json_tables_created'])}):")
        print("-" * 50)
        for table in results['json_tables_created']:
            print(f"✓ {table}")
        
        print(f"\nSUMMARY:")
        print(f"- Total mapping tables created: {results['total_tables_created']}")
        print(f"- Total indexes created: {results['total_indexes_created']}")
        
        if results['errors']:
            print(f"\nERRORS ({len(results['errors'])}):")
            print("-" * 30)
            for error in results['errors']:
                print(f"✗ {error}")
        
        print("="*80)


def main():
    """Main function to create all mapping tables"""
    creator = MappingTableCreator()
    
    # Create all mapping tables
    results = creator.create_all_mapping_tables()
    
    # Print summary
    creator.print_mapping_tables_summary(results)
    
    # Verify tables were created
    verification = creator.verify_mapping_tables()
    print(f"\nVERIFICATION: {verification['total_verified']} tables verified in database")
    
    if verification['missing_tables']:
        print("Missing tables:")
        for table in verification['missing_tables']:
            print(f"- {table}")


if __name__ == "__main__":
    main()
