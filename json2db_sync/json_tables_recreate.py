"""
JSON Tables Recreation Script
Purpose: Recreate JSON sync tables in existing database without touching database file
Primary Function: Table recreation (preserves database file and other tables)
Secondary Function: Full table creation (when needed)
Target: data/database/production.db
Generated: July 8, 2025
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Handle imports for both standalone and module usage
try:
    from .table_generator import TableGenerator
    from .json_analyzer import JSONAnalyzer
except ImportError:
    from table_generator import TableGenerator
    from json_analyzer import JSONAnalyzer


class JSONTablesRecreator:
    """Recreates JSON sync tables in existing database"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 json_analyzer: Optional[JSONAnalyzer] = None,
                 table_generator: Optional[TableGenerator] = None):
        self.db_path = Path(db_path)
        self.analyzer = json_analyzer or JSONAnalyzer()
        self.generator = table_generator or TableGenerator(self.analyzer)
        self.setup_logging()
        
        # Statistics tracking
        self.stats = {
            "tables_recreated": 0,
            "tables_created": 0,
            "indexes_created": 0,
            "tables_existed": 0,
            "errors": 0,
            "total_tables": 0,
            "total_indexes": 0
        }
        
        # Error tracking
        self.errors = []
        
    def setup_logging(self):
        """Setup logging for table recreation"""
        self.logger = logging.getLogger(__name__)

    def connect_database(self) -> sqlite3.Connection:
        """Connect to existing database"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}. Please create database first.")
        
        # Connect to existing database
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        self.logger.info(f"Connected to existing database: {self.db_path}")
        return conn

    def table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """Check if a table already exists in the database"""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def get_existing_json_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of existing JSON tables in the database"""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def add_data_source_column_to_json_tables(self, conn: sqlite3.Connection, table_sql: Dict[str, Any]) -> bool:
        """Add data_source column to JSON table SQL statements"""
        for table_name, sql_info in table_sql.items():
            create_sql = sql_info['create_table']
            
            # Check if data_source column is already in the SQL
            if 'data_source' not in create_sql.lower():
                # Find the PRIMARY KEY constraint position
                primary_key_pos = create_sql.rfind('PRIMARY KEY')
                
                if primary_key_pos > 0:
                    # Insert data_source column before the PRIMARY KEY constraint
                    # Find the comma before PRIMARY KEY
                    before_pk = create_sql[:primary_key_pos].rstrip()
                    if before_pk.endswith(','):
                        # Insert the data_source column before PRIMARY KEY
                        new_sql = (create_sql[:primary_key_pos] + 
                                 "\n    -- Data Source Tracking\n" +
                                 "    data_source TEXT DEFAULT 'json',\n    " + 
                                 create_sql[primary_key_pos:])
                    else:
                        # Add comma and then data_source column
                        new_sql = (create_sql[:primary_key_pos] + 
                                 ",\n    -- Data Source Tracking\n" +
                                 "    data_source TEXT DEFAULT 'json',\n    " + 
                                 create_sql[primary_key_pos:])
                        
                    sql_info['create_table'] = new_sql
                    self.logger.info(f"Added data_source column to {table_name}")
                else:
                    # No PRIMARY KEY constraint found, add data_source before closing parenthesis
                    if create_sql.strip().endswith(');'):
                        insert_pos = create_sql.rfind(')')
                        if insert_pos > 0:
                            new_sql = (create_sql[:insert_pos] + 
                                     ",\n    -- Data Source Tracking\n" +
                                     "    data_source TEXT DEFAULT 'json'\n" + 
                                     create_sql[insert_pos:])
                            sql_info['create_table'] = new_sql
                            self.logger.info(f"Added data_source column to {table_name}")
                        else:
                            self.logger.warning(f"Could not add data_source column to {table_name}")
                    else:
                        self.logger.warning(f"Unexpected SQL format for {table_name}")
        
        return True

    def recreate_table_from_sql(self, conn: sqlite3.Connection, table_name: str, 
                               create_sql: str) -> bool:
        """Recreate a single table from SQL DDL (drop and recreate)"""
        try:
            # Drop table if it exists
            if self.table_exists(conn, table_name):
                self.logger.info(f"Dropping existing table: {table_name}")
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                self.stats["tables_recreated"] += 1
            
            # Create table with new schema
            conn.execute(create_sql)
            conn.commit()
            
            self.logger.info(f"Successfully recreated table: {table_name}")
            if table_name not in [name for name in self.get_existing_json_tables(conn)]:
                self.stats["tables_created"] += 1
                
            return True
            
        except Exception as e:
            error_msg = f"Error recreating table {table_name}: {str(e)}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            self.stats["errors"] += 1
            return False

    def create_index_from_sql(self, conn: sqlite3.Connection, index_sql: str) -> bool:
        """Create an index from SQL DDL"""
        try:
            conn.execute(index_sql)
            conn.commit()
            
            self.logger.debug(f"Created index: {index_sql.split()[5] if len(index_sql.split()) > 5 else 'unknown'}")
            self.stats["indexes_created"] += 1
            return True
            
        except Exception as e:
            # Index creation failures are usually not critical (may already exist)
            self.logger.warning(f"Index creation warning: {str(e)}")
            return False

    def recreate_all_json_tables(self) -> Dict[str, Any]:
        """Recreate all JSON sync tables in the existing database (DEFAULT BEHAVIOR)"""
        self.logger.info("=== JSON Tables Recreation Process Started ===")
        
        # Generate table SQL
        self.logger.info("Generating JSON table schemas...")
        table_sql = self.generator.analyze_and_generate()
        
        if not table_sql:
            self.logger.error("No JSON table schemas generated")
            return {"success": False, "error": "No schemas generated"}
        
        # Add data_source column to all JSON tables
        self.add_data_source_column_to_json_tables(None, table_sql)
        
        self.stats["total_tables"] = len(table_sql)
        
        # Connect to database
        conn = None
        try:
            conn = self.connect_database()
            
            # Show existing JSON tables
            existing_tables = self.get_existing_json_tables(conn)
            if existing_tables:
                self.logger.info(f"Found {len(existing_tables)} existing JSON tables: {existing_tables}")
            else:
                self.logger.info("No existing JSON tables found")
            
            # Recreate tables in order: main entities first, then line items
            main_tables = [name for name in table_sql.keys() if '_line_items' not in name]
            line_item_tables = [name for name in table_sql.keys() if '_line_items' in name]
            
            # Process main entity tables first
            self.logger.info(f"Recreating {len(main_tables)} main entity tables...")
            for table_name in sorted(main_tables):
                sql_info = table_sql[table_name]
                success = self.recreate_table_from_sql(conn, table_name, sql_info['create_table'])
                if not success:
                    self.logger.warning(f"Failed to recreate {table_name}, continuing...")
            
            # Process line item tables
            if line_item_tables:
                self.logger.info(f"Recreating {len(line_item_tables)} line item tables...")
                for table_name in sorted(line_item_tables):
                    sql_info = table_sql[table_name]
                    success = self.recreate_table_from_sql(conn, table_name, sql_info['create_table'])
                    if not success:
                        self.logger.warning(f"Failed to recreate {table_name}, continuing...")
            
            # Create indexes
            self.logger.info("Creating indexes...")
            total_indexes = 0
            for table_name, sql_info in table_sql.items():
                indexes = sql_info.get('indexes', [])
                total_indexes += len(indexes)
                for index_sql in indexes:
                    self.create_index_from_sql(conn, index_sql)
            
            self.stats["total_indexes"] = total_indexes
            
            # Verify data_source column was added to each JSON table
            final_tables = self.get_existing_json_tables(conn)
            for table in final_tables:
                cursor = conn.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
                if 'data_source' in columns:
                    self.logger.info(f"SUCCESS: Table {table}: data_source column added successfully")
                else:
                    self.logger.warning(f"WARNING: Table {table}: data_source column not found")
            
            # Final verification
            self.logger.info(f"Database now contains {len(final_tables)} JSON tables")
            self.logger.info("=== JSON Tables Recreation Process Completed Successfully ===")
            
            return {
                "success": True,
                "stats": self.stats.copy(),
                "tables_created": final_tables,
                "errors": self.errors.copy()
            }
            
        except Exception as e:
            error_msg = f"JSON tables recreation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "stats": self.stats.copy(),
                "errors": self.errors.copy()
            }
        
        finally:
            if conn:
                conn.close()

    def create_all_tables_full(self) -> Dict[str, Any]:
        """Full table creation function (USE WITH CAUTION - MAY CREATE DATABASE)"""
        self.logger.info("=== Full JSON Database Creation Process Started ===")
        
        # Generate table SQL
        self.logger.info("Generating table schemas...")
        table_sql = self.generator.analyze_and_generate()
        
        if not table_sql:
            self.logger.error("No table schemas generated")
            return {"success": False, "error": "No schemas generated"}
        
        # Add data_source column to all JSON tables
        self.add_data_source_column_to_json_tables(None, table_sql)
        
        self.stats["total_tables"] = len(table_sql)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database (creates if doesn't exist)
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            self.logger.info(f"Connected to database: {self.db_path}")
            
            # Show existing JSON tables
            existing_tables = self.get_existing_json_tables(conn)
            if existing_tables:
                self.logger.info(f"Found {len(existing_tables)} existing JSON tables: {existing_tables}")
            
            # Create tables in order: main entities first, then line items
            main_tables = [name for name in table_sql.keys() if '_line_items' not in name]
            line_item_tables = [name for name in table_sql.keys() if '_line_items' in name]
            
            # Process main entity tables first
            self.logger.info(f"Creating {len(main_tables)} main entity tables...")
            for table_name in sorted(main_tables):
                sql_info = table_sql[table_name]
                success = self.recreate_table_from_sql(conn, table_name, sql_info['create_table'])
                if not success:
                    self.logger.warning(f"Failed to create {table_name}, continuing...")
            
            # Process line item tables
            if line_item_tables:
                self.logger.info(f"Creating {len(line_item_tables)} line item tables...")
                for table_name in sorted(line_item_tables):
                    sql_info = table_sql[table_name]
                    success = self.recreate_table_from_sql(conn, table_name, sql_info['create_table'])
                    if not success:
                        self.logger.warning(f"Failed to create {table_name}, continuing...")
            
            # Create indexes
            self.logger.info("Creating indexes...")
            total_indexes = 0
            for table_name, sql_info in table_sql.items():
                indexes = sql_info.get('indexes', [])
                total_indexes += len(indexes)
                for index_sql in indexes:
                    self.create_index_from_sql(conn, index_sql)
            
            self.stats["total_indexes"] = total_indexes
            
            # Final verification
            final_tables = self.get_existing_json_tables(conn)
            self.logger.info(f"Database now contains {len(final_tables)} JSON tables")
            
            return {
                "success": True,
                "stats": self.stats.copy(),
                "tables_created": final_tables,
                "errors": self.errors.copy()
            }
            
        except Exception as e:
            error_msg = f"Full database creation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "stats": self.stats.copy(),
                "errors": self.errors.copy()
            }
        
        finally:
            if conn:
                conn.close()

    def print_recreation_summary(self, result: Dict[str, Any]):
        """Print a formatted summary of table recreation results"""
        print("\n" + "="*70)
        print("JSON TABLES RECREATION SUMMARY")
        print("="*70)
        
        if result.get("success"):
            print("SUCCESS: JSON Tables Recreation Completed")
        else:
            print("FAILED: JSON Tables Recreation Failed")
            if "error" in result:
                print(f"Error: {result['error']}")
        
        stats = result.get("stats", {})
        print(f"\nSTATISTICS:")
        print(f"  Tables Recreated: {stats.get('tables_recreated', 0)}")
        print(f"  Tables Created: {stats.get('tables_created', 0)}")
        print(f"  Indexes Created: {stats.get('indexes_created', 0)}")
        print(f"  Total Errors: {stats.get('errors', 0)}")
        
        tables_created = result.get("tables_created", [])
        if tables_created:
            print(f"\nJSON TABLES IN DATABASE ({len(tables_created)}):")
            print("-" * 50)
            for table in sorted(tables_created):
                table_type = "Line Items" if "_line_items" in table else "Main Entity"
                print(f"  {table:<35} [{table_type}]")
        
        errors = result.get("errors", [])
        if errors:
            print(f"\nERRORS ({len(errors)}):")
            print("-" * 50)
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        print("="*70)


def main_recreate_tables():
    """Main function to recreate JSON sync tables (DEFAULT BEHAVIOR)"""
    recreator = JSONTablesRecreator()
    
    try:
        # Recreate all JSON tables
        result = recreator.recreate_all_json_tables()
        
        # Print summary
        recreator.print_recreation_summary(result)
        
        return result.get("success", False)
        
    except Exception as e:
        logging.error(f"JSON tables recreation failed: {str(e)}")
        return False


def main_create_tables():
    """Full table creation function (USE WITH CAUTION)"""
    recreator = JSONTablesRecreator()
    
    try:
        # Create all tables (full creation)
        result = recreator.create_all_tables_full()
        
        # Print summary
        recreator.print_recreation_summary(result)
        
        return result.get("success", False)
        
    except Exception as e:
        logging.error(f"JSON database creation failed: {str(e)}")
        return False


def main():
    """Main execution function"""
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--create-tables":
        # Full table creation (may create database)
        success = main_create_tables()
    else:
        # Default: recreate tables only (preserves database file)
        success = main_recreate_tables()
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
