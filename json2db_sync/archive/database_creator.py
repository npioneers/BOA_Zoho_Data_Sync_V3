"""
Database Creator
Creates the JSON sync tables in the database based on generated SQL schema.
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from .table_generator import TableGenerator
from .json_analyzer import JSONAnalyzer


class DatabaseCreator:
    """Creates database tables for JSON sync based on analysis"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 json_analyzer: Optional[JSONAnalyzer] = None,
                 table_generator: Optional[TableGenerator] = None):
        self.db_path = Path(db_path)
        self.analyzer = json_analyzer or JSONAnalyzer()
        self.generator = table_generator or TableGenerator(self.analyzer)
        self.setup_logging()
        
        # Statistics tracking
        self.stats = {
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
        """Setup logging for database creation"""
        self.logger = logging.getLogger(__name__)

    def create_database_backup(self) -> Optional[str]:
        """Create a backup of the database before modifications"""
        if not self.db_path.exists():
            self.logger.info("Database doesn't exist yet, no backup needed")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"json_sync_backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"Failed to create backup: {str(e)}")
            return None

    def connect_database(self) -> sqlite3.Connection:
        """Connect to the database and ensure it exists"""
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database (creates if doesn't exist)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        self.logger.info(f"Connected to database: {self.db_path}")
        return conn

    def table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """Check if a table already exists in the database"""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def get_existing_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of existing tables in the database"""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def create_table_from_sql(self, conn: sqlite3.Connection, table_name: str, 
                             create_sql: str) -> bool:
        """Create a single table from SQL DDL"""
        try:
            # Check if table already exists
            if self.table_exists(conn, table_name):
                self.logger.info(f"Table {table_name} already exists, skipping creation")
                self.stats["tables_existed"] += 1
                return True
            
            # Execute CREATE TABLE statement
            conn.execute(create_sql)
            conn.commit()
            
            self.logger.info(f"Successfully created table: {table_name}")
            self.stats["tables_created"] += 1
            return True
            
        except Exception as e:
            error_msg = f"Error creating table {table_name}: {str(e)}"
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

    def create_all_tables(self, force_recreate: bool = False) -> Dict[str, Any]:
        """Create all JSON sync tables in the database"""
        self.logger.info("Starting database table creation process...")
        
        # Create backup
        backup_path = self.create_database_backup()
        
        # Generate table SQL
        self.logger.info("Generating table schemas...")
        table_sql = self.generator.analyze_and_generate()
        
        if not table_sql:
            self.logger.error("No table schemas generated")
            return {"success": False, "error": "No schemas generated"}
        
        self.stats["total_tables"] = len(table_sql)
        
        # Connect to database
        conn = None
        try:
            conn = self.connect_database()
            
            # Show existing JSON tables
            existing_tables = self.get_existing_tables(conn)
            if existing_tables:
                self.logger.info(f"Found {len(existing_tables)} existing JSON tables: {existing_tables}")
            
            # Create tables in order: main entities first, then line items
            main_tables = [name for name in table_sql.keys() if '_line_items' not in name]
            line_item_tables = [name for name in table_sql.keys() if '_line_items' in name]
            
            # Process main entity tables first
            self.logger.info(f"Creating {len(main_tables)} main entity tables...")
            for table_name in sorted(main_tables):
                sql_info = table_sql[table_name]
                
                if force_recreate and self.table_exists(conn, table_name):
                    self.logger.info(f"Force recreate: dropping existing table {table_name}")
                    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    conn.commit()
                
                success = self.create_table_from_sql(conn, table_name, sql_info['create_table'])
                if not success and not force_recreate:
                    self.logger.warning(f"Failed to create {table_name}, continuing...")
            
            # Process line item tables
            if line_item_tables:
                self.logger.info(f"Creating {len(line_item_tables)} line item tables...")
                for table_name in sorted(line_item_tables):
                    sql_info = table_sql[table_name]
                    
                    if force_recreate and self.table_exists(conn, table_name):
                        self.logger.info(f"Force recreate: dropping existing table {table_name}")
                        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                        conn.commit()
                    
                    success = self.create_table_from_sql(conn, table_name, sql_info['create_table'])
                    if not success and not force_recreate:
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
            final_tables = self.get_existing_tables(conn)
            self.logger.info(f"Database now contains {len(final_tables)} JSON tables")
            
            return {
                "success": True,
                "backup_path": backup_path,
                "stats": self.stats.copy(),
                "tables_created": final_tables,
                "errors": self.errors.copy()
            }
            
        except Exception as e:
            error_msg = f"Database creation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "backup_path": backup_path,
                "stats": self.stats.copy(),
                "errors": self.errors.copy()
            }
        
        finally:
            if conn:
                conn.close()

    def verify_tables(self) -> Dict[str, Any]:
        """Verify that all expected tables were created"""
        self.logger.info("Verifying created tables...")
        
        conn = None
        try:
            conn = self.connect_database()
            
            # Get all JSON tables
            json_tables = self.get_existing_tables(conn)
            
            # Get expected tables from analyzer
            if not self.analyzer.analysis_results:
                self.analyzer.analyze_all_json_files()
            
            expected_tables = set(self.analyzer.analysis_results.keys())
            created_tables = set(json_tables)
            
            missing_tables = expected_tables - created_tables
            extra_tables = created_tables - expected_tables
            
            # Check table structures
            table_info = {}
            for table_name in json_tables:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                table_info[table_name] = {
                    "column_count": len(columns),
                    "columns": [col[1] for col in columns]  # Column names
                }
            
            verification_result = {
                "success": len(missing_tables) == 0,
                "expected_tables": len(expected_tables),
                "created_tables": len(created_tables),
                "missing_tables": list(missing_tables),
                "extra_tables": list(extra_tables),
                "table_details": table_info
            }
            
            if missing_tables:
                self.logger.error(f"Missing tables: {missing_tables}")
            else:
                self.logger.info("✓ All expected tables created successfully")
            
            if extra_tables:
                self.logger.info(f"Extra tables found: {extra_tables}")
            
            return verification_result
            
        except Exception as e:
            self.logger.error(f"Table verification failed: {str(e)}")
            return {"success": False, "error": str(e)}
        
        finally:
            if conn:
                conn.close()

    def print_creation_summary(self, result: Dict[str, Any]):
        """Print a formatted summary of table creation results"""
        print("\n" + "="*70)
        print("JSON DATABASE TABLE CREATION SUMMARY")
        print("="*70)
        
        if result.get("success"):
            print("✓ DATABASE CREATION SUCCESSFUL")
        else:
            print("✗ DATABASE CREATION FAILED")
            if "error" in result:
                print(f"Error: {result['error']}")
        
        stats = result.get("stats", {})
        print(f"\nSTATISTICS:")
        print(f"  Tables Created: {stats.get('tables_created', 0)}")
        print(f"  Tables Existed: {stats.get('tables_existed', 0)}")
        print(f"  Indexes Created: {stats.get('indexes_created', 0)}")
        print(f"  Total Errors: {stats.get('errors', 0)}")
        
        if result.get("backup_path"):
            print(f"\nBackup Created: {result['backup_path']}")
        
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


def main():
    """Main function to create JSON sync tables"""
    creator = DatabaseCreator()
    
    try:
        # Create all tables
        result = creator.create_all_tables()
        
        # Print summary
        creator.print_creation_summary(result)
        
        # Verify tables
        if result.get("success"):
            verification = creator.verify_tables()
            if verification.get("success"):
                print("\n✓ Table verification passed - all tables created correctly")
            else:
                print(f"\n✗ Table verification failed: {verification.get('error', 'Unknown error')}")
        
    except Exception as e:
        logging.error(f"Database creation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
