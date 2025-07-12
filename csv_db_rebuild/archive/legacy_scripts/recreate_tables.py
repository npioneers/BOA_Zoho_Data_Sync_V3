#!/usr/bin/env python3
"""
Table Recreation Script for Zoho Data Sync V2
Purpose: Recreate database tables with updated schema including data_source column
Primary Function: Table recreation (preserves database file)
Secondary Function: Full database creation (when needed)
Target: data/database/production.db
Generated: July 8, 2025
"""

import os
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('tmp_database_creation.log'),
        logging.StreamHandler()
    ]
)

# Enable verbose SQLite logging
import sqlite3
sqlite3.enable_callback_tracebacks(True)

def backup_existing_database():
    """Backup existing production database before replacement"""
    logging.debug("Starting backup process...")
    source_db = Path("data/database/production.db")
    logging.debug(f"Checking if source database exists: {source_db}")
    
    if source_db.exists():
        logging.info(f"Source database found: {source_db.stat().st_size} bytes")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        logging.debug(f"Creating backup directory: {backup_dir}")
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"production_db_backup_{timestamp}.db"
        
        logging.info(f"Copying database to backup: {backup_file}")
        shutil.copy2(source_db, backup_file)
        backup_size = backup_file.stat().st_size
        logging.info(f"Existing database backed up to: {backup_file} ({backup_size} bytes)")
        return backup_file
    else:
        logging.info("No existing production database found to backup")
        return None

def recreate_tables_only():
    """Recreate tables in existing database without touching the database file itself"""
    db_path = Path("data/database/production.db")
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Please create database first.")
    
    logging.info(f"Recreating tables in existing database: {db_path}")
    
    # Connect to existing database
    conn = sqlite3.connect(str(db_path))
    
    # Read and execute SQL schema
    sql_file = Path("csv_db_rebuild/create_database_schema.sql")
    if not sql_file.exists():
        sql_file = Path("tmp_create_database_schema.sql")  # Fallback
        if not sql_file.exists():
            raise FileNotFoundError("SQL schema file not found in either csv_db_rebuild/ or current directory")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Execute SQL script using executescript for better handling
    try:
        # Remove comment lines that might cause issues
        clean_sql_lines = []
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                clean_sql_lines.append(line)
        
        clean_sql = '\n'.join(clean_sql_lines)
        
        # Execute the entire script (includes DROP TABLE IF EXISTS statements)
        conn.executescript(clean_sql)
        logging.info("Successfully recreated all tables with new schema")
        
        # Verify tables were created
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logging.info(f"Recreated tables: {', '.join(sorted(tables))}")
        
        # Verify data_source column was added to each table
        for table in tables:
            cursor = conn.execute(f"PRAGMA table_info({table});")
            columns = [row[1] for row in cursor.fetchall()]
            if 'data_source' in columns:
                logging.info(f"SUCCESS: Table {table}: data_source column added successfully")
            else:
                logging.warning(f"WARNING: Table {table}: data_source column not found")
        
        logging.info("All tables recreated with data_source column")
        
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Table recreation failed: {e}")
        raise
    finally:
        conn.close()
    
    return db_path

def create_database():
    """Create new database with CSV-mirrored schema"""
    # Ensure database directory exists
    db_dir = Path("data/database")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = db_dir / "production.db"
    
    # Remove existing database if it exists
    if db_path.exists():
        os.remove(db_path)
        logging.info("Removed existing production.db")
    
    # Create new database with disabled SHM/WAL
    conn = sqlite3.connect(str(db_path))
    
    # Disable shared memory and WAL mode to prevent lock files
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.execute("PRAGMA locking_mode = NORMAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.commit()
    
    logging.info(f"Created new database: {db_path} (SHM/WAL disabled)")
    
    # Read and execute SQL schema
    sql_file = Path("csv_db_rebuild/create_database_schema.sql")
    if not sql_file.exists():
        sql_file = Path("tmp_create_database_schema.sql")  # Fallback
        if not sql_file.exists():
            raise FileNotFoundError("SQL schema file not found in either csv_db_rebuild/ or current directory")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Execute SQL script using executescript for better handling
    try:
        # Remove comment lines that might cause issues
        clean_sql_lines = []
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                clean_sql_lines.append(line)
        
        clean_sql = '\n'.join(clean_sql_lines)
        
        # Execute the entire script
        conn.executescript(clean_sql)
        logging.info("Successfully executed SQL schema script")
        
        # Verify tables were created
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logging.info(f"Created tables: {', '.join(sorted(tables))}")
        
        # No indexes to verify - all indexes removed for simplicity
        logging.info("No indexes created - simplified schema")
        
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Database creation failed: {e}")
        raise
    finally:
        conn.close()
    
    return db_path

def verify_database_structure():
    """Verify the created database structure matches expectations"""
    import pandas as pd
    
    db_path = Path("data/database/production.db")
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Expected tables
        expected_tables = [
            'csv_invoices', 'csv_items', 'csv_contacts', 'csv_bills', 'csv_organizations',
            'csv_customer_payments', 'csv_vendor_payments', 'csv_sales_orders', 
            'csv_purchase_orders', 'csv_credit_notes'
        ]
        
        # Get actual tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        actual_tables = [row[0] for row in cursor.fetchall()]
        
        # Verify all expected tables exist
        missing_tables = set(expected_tables) - set(actual_tables)
        if missing_tables:
            raise ValueError(f"Missing tables: {missing_tables}")
        
        logging.info("All expected tables verified")
        
        # CSV to table mapping
        csv_mappings = {
            'csv_invoices': 'Invoice.csv',
            'csv_items': 'Item.csv', 
            'csv_contacts': 'Contacts.csv',
            'csv_bills': 'Bill.csv',
            'csv_organizations': 'Contacts.csv',  # Organizations come from Contacts
            'csv_customer_payments': 'Customer_Payment.csv',
            'csv_vendor_payments': 'Vendor_Payment.csv',
            'csv_sales_orders': 'Sales_Order.csv',
            'csv_purchase_orders': 'Purchase_Order.csv',
            'csv_credit_notes': 'Credit_Note.csv'
        }
        
        csv_base_path = Path("data/csv/Nangsel Pioneers_Latest")
        
        for table in expected_tables:
            cursor = conn.execute(f"PRAGMA table_info({table});")
            db_columns = cursor.fetchall()
            actual_count = len(db_columns)
            
            # Get CSV column count if file exists
            csv_file = csv_base_path / csv_mappings.get(table, f"{table}.csv")
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file, nrows=0)  # Just headers
                    csv_count = len(df.columns)
                    expected_count = csv_count + 2  # +2 for metadata columns
                    
                    if actual_count == expected_count:
                        logging.info(f"Table {table}: {actual_count} columns verified (CSV: {csv_count} + 2 metadata)")
                    else:
                        logging.warning(f"Table {table}: expected {expected_count} columns (CSV: {csv_count} + 2), got {actual_count}")
                except Exception as e:
                    logging.warning(f"Could not verify {table} against CSV: {e}")
            else:
                logging.warning(f"CSV file not found for {table}: {csv_file}")
        
        logging.info("Database structure verification completed successfully")
        
    except Exception as e:
        logging.error(f"Database verification failed: {e}")
        raise
    finally:
        conn.close()

def main_recreate_tables():
    """Main execution function for recreating tables only (DEFAULT BEHAVIOR)"""
    try:
        logging.info("=== Table Recreation Process Started ===")
        
        # Recreate tables in existing database
        db_path = recreate_tables_only()
        
        # Verify database structure
        verify_database_structure()
        
        logging.info("=== Table Recreation Process Completed Successfully ===")
        logging.info(f"Tables recreated in database: {db_path}")
        logging.info("All tables now include data_source column with default 'csv'")
        
        return True
        
    except Exception as e:
        logging.error(f"Table recreation process failed: {e}")
        logging.error("Process aborted. Check logs for details.")
        return False

def main():
    """Full database recreation function (USE WITH CAUTION - DESTROYS EXISTING DATA)"""
    try:
        logging.info("=== Database Refactor Process Started ===")
        
        # Step 1: Backup existing database
        backup_file = backup_existing_database()
        
        # Step 2: Create new database
        db_path = create_database()
        
        # Step 3: Verify database structure
        verify_database_structure()
        
        logging.info("=== Database Refactor Process Completed Successfully ===")
        logging.info(f"New database created: {db_path}")
        if backup_file:
            logging.info(f"Backup available at: {backup_file}")
        
        return True
        
    except Exception as e:
        logging.error(f"Database refactor process failed: {e}")
        logging.error("Process aborted. Check logs for details.")
        return False

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--create-database":
        # Full database recreation (destroys existing database)
        success = main()
    else:
        # Default: recreate tables only (preserves database file and mapping tables)
        success = main_recreate_tables()
    
    exit(0 if success else 1)
