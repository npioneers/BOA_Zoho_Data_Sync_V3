"""
Simple CSV to Database Populator
Populates database tables from CSV files with basic logging
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import re

# Simple table mappings (hardcoded for simplicity)
TABLE_MAPPINGS = {
    "csv_invoices": {"csv_file": "Invoice.csv"},
    "csv_items": {"csv_file": "Item.csv"},
    "csv_contacts": {"csv_file": "Contacts.csv"},
    "csv_bills": {"csv_file": "Bill.csv"},
    "csv_customer_payments": {"csv_file": "Customer_Payment.csv"},
    "csv_vendor_payments": {"csv_file": "Vendor_Payment.csv"},
    "csv_sales_orders": {"csv_file": "Sales_Order.csv"},
    "csv_purchase_orders": {"csv_file": "Purchase_Order.csv"},
    "csv_credit_notes": {"csv_file": "Credit_Note.csv"}
}


class SimpleCSVPopulator:
    """Simple CSV to database populator with basic logging"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 csv_dir: str = "data/csv/Nangsel Pioneers_Latest"):
        self.db_path = Path(db_path)
        self.csv_dir = Path(csv_dir)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup simple logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"csv_population_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',  # Simplified format for cleaner output
            handlers=[
                logging.FileHandler(log_file, mode='w'),  # Overwrite log file each time
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"CSV Population Log: {log_file}")
        self.logger.info("")

    def csv_to_db_column_name(self, csv_column: str) -> str:
        """Convert CSV column name to database column name (snake_case)"""
        # Convert spaces and special characters to underscores
        db_column = re.sub(r'[^a-zA-Z0-9]', '_', csv_column)
        # Convert to lowercase
        db_column = db_column.lower()
        # Remove multiple underscores
        db_column = re.sub(r'_+', '_', db_column)
        # Remove leading/trailing underscores
        db_column = db_column.strip('_')
        return db_column

    def get_database_columns(self, table_name: str) -> list:
        """Get the actual column names from the database table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            return columns
        except Exception as e:
            self.logger.error(f"Error getting columns for {table_name}: {str(e)}")
            return []

    def map_csv_to_db_columns(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Map CSV column names to database column names"""
        db_columns = self.get_database_columns(table_name)
        column_mapping = {}
        
        for csv_col in df.columns:
            db_col = self.csv_to_db_column_name(csv_col)
            if db_col in db_columns:
                column_mapping[csv_col] = db_col
            else:
                self.logger.warning(f"CSV column '{csv_col}' -> '{db_col}' not found in database table {table_name}")
        
        # Rename the DataFrame columns
        df_mapped = df.rename(columns=column_mapping)
        
        # Only keep columns that exist in the database
        valid_columns = [col for col in df_mapped.columns if col in db_columns]
        df_final = df_mapped[valid_columns]
        
        self.logger.info(f"Mapped {len(valid_columns)}/{len(df.columns)} columns for {table_name}")
        return df_final

    def clear_table(self, table_name: str) -> bool:
        """Clear all data from a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                self.logger.warning(f"Table {table_name} does not exist")
                conn.close()
                return False
            
            # Clear the table
            cursor.execute(f"DELETE FROM {table_name}")
            rows_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared {rows_deleted} existing records from {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing table {table_name}: {str(e)}")
            return False

    def clear_all_tables(self) -> dict:
        """Clear all mapped tables"""
        self.logger.info("Clearing all existing table data")
        results = {}
        
        for table_name in TABLE_MAPPINGS.keys():
            results[table_name] = self.clear_table(table_name)
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Cleared {successful}/{len(results)} tables successfully")
        
        return results

    def get_primary_key_columns(self, table_name: str) -> list:
        """Get primary key column names for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            pk_columns = [row[1] for row in cursor.fetchall() if row[5] > 0]  # pk column in position 5
            conn.close()
            return pk_columns
        except Exception as e:
            self.logger.error(f"Error getting primary keys for {table_name}: {str(e)}")
            return []

    def _insert_with_ignore(self, conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> int:
        """Insert records without primary key columns to avoid conflicts"""
        cursor = conn.cursor()
        inserted_count = 0
        
        # Remove primary key columns to avoid conflicts
        pk_columns = self.get_primary_key_columns(table_name)
        df_no_pk = df.copy()
        
        for pk_col in pk_columns:
            if pk_col in df_no_pk.columns:
                self.logger.info(f"Removing primary key column '{pk_col}' from {table_name} for insertion")
                df_no_pk = df_no_pk.drop(columns=[pk_col])
        
        # Add data_source column with value 'csv'
        df_no_pk['data_source'] = 'csv'
        self.logger.info(f"Added data_source='csv' column to {table_name} for insertion")
        
        if df_no_pk.empty or len(df_no_pk.columns) == 0:
            self.logger.warning(f"No columns left after removing primary keys for {table_name}")
            return 0
        
        # Create INSERT statement without primary key columns but with data_source
        columns = list(df_no_pk.columns)
        placeholders = ', '.join(['?' for _ in columns])
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert each row
        for _, row in df_no_pk.iterrows():
            try:
                cursor.execute(sql, tuple(row))
                inserted_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to insert row in {table_name}: {str(e)}")
        
        return inserted_count

    def populate_table(self, table_name: str) -> dict:
        """Populate a single table from CSV"""
        self.logger.info(f"Populating table: {table_name}")
        
        # Get CSV mapping
        if table_name not in TABLE_MAPPINGS:
            self.logger.warning(f"No mapping found for table: {table_name}")
            return {"success": False, "records": 0, "error": "No mapping found"}
            
        csv_file = TABLE_MAPPINGS[table_name]["csv_file"]
        csv_path = self.csv_dir / csv_file
        
        if not csv_path.exists():
            self.logger.warning(f"CSV file not found: {csv_path}")
            return {"success": False, "records": 0, "error": "CSV file not found"}
            
        try:
            # Clear existing data from table
            if not self.clear_table(table_name):
                self.logger.warning(f"Failed to clear table {table_name}, continuing anyway...")
            
            # Read CSV
            df = pd.read_csv(csv_path)
            self.logger.info(f"Read {len(df)} records from {csv_file}")
            
            # Map CSV columns to DB columns
            df_mapped = self.map_csv_to_db_columns(df, table_name)
            if df_mapped.empty or len(df_mapped.columns) == 0:
                self.logger.error(f"No valid columns mapped for {table_name}")
                return {"success": False, "records": 0, "error": "No valid columns mapped"}
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Always use primary key removal approach to avoid conflicts
            inserted_records = self._insert_with_ignore(conn, table_name, df_mapped)
            self.logger.info(f"Successfully inserted {inserted_records}/{len(df_mapped)} records into {table_name}")
            
            conn.commit()
            conn.close()
            
            return {"success": True, "records": inserted_records, "error": None}
            
        except Exception as e:
            self.logger.error(f"Error populating {table_name}: {str(e)}")
            return {"success": False, "records": 0, "error": str(e)}

    def populate_all_tables(self) -> dict:
        """Populate all mapped tables with detailed reporting"""
        start_time = datetime.now()
        self.logger.info("Starting population of all tables")
        self.logger.info("="*70)
        
        results = {}
        total_success = 0
        total_records = 0
        total_csv_records = 0
        failed_tables = []
        
        for table_name in TABLE_MAPPINGS.keys():
            result = self.populate_table(table_name)
            results[table_name] = result
            
            # Count CSV records for success rate calculation
            csv_file = TABLE_MAPPINGS[table_name]["csv_file"]
            csv_path = self.csv_dir / csv_file
            if csv_path.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_path)
                    csv_record_count = len(df)
                    total_csv_records += csv_record_count
                    results[table_name]["csv_records"] = csv_record_count
                except:
                    results[table_name]["csv_records"] = 0
            else:
                results[table_name]["csv_records"] = 0
            
            if result["success"]:
                total_success += 1
                total_records += result["records"]
                success_rate = (result["records"] / results[table_name]["csv_records"] * 100) if results[table_name]["csv_records"] > 0 else 0
                self.logger.info(f"SUCCESS {table_name}: {result['records']}/{results[table_name]['csv_records']} records ({success_rate:.1f}%)")
            else:
                failed_tables.append(table_name)
                self.logger.error(f"FAILED {table_name}: {result['error']}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Calculate overall success rate
        overall_success_rate = (total_records / total_csv_records * 100) if total_csv_records > 0 else 0
        table_success_rate = (total_success / len(TABLE_MAPPINGS) * 100)
        
        # Enhanced summary with detailed metrics
        summary = {
            "tables_attempted": len(TABLE_MAPPINGS),
            "tables_successful": total_success,
            "tables_failed": len(failed_tables),
            "table_success_rate": table_success_rate,
            "total_csv_records": total_csv_records,
            "total_records_inserted": total_records,
            "overall_success_rate": overall_success_rate,
            "processing_time_seconds": processing_time,
            "failed_tables": failed_tables,
            "results": results
        }
        
        # Print detailed success report in table format
        self.logger.info("="*70)
        self.logger.info("POPULATION SUCCESS REPORT")
        self.logger.info("="*70)
        self.logger.info(f"Overall Success Rate: {overall_success_rate:.1f}% ({total_records:,}/{total_csv_records:,} records)")
        self.logger.info(f"Table Success Rate: {table_success_rate:.1f}% ({total_success}/{len(TABLE_MAPPINGS)} tables)")
        self.logger.info(f"Processing Time: {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)")
        
        if failed_tables:
            self.logger.info(f"Failed Tables: {', '.join(failed_tables)}")
        else:
            self.logger.info("All tables populated successfully!")
        
        self.logger.info("="*70)
        self.logger.info("DETAILED SUCCESS RATE TABLE:")
        self.logger.info("="*70)
        self.logger.info(f"{'Table Name':<20} | {'CSV Records':<11} | {'DB Records':<10} | {'Success Rate':<12} | {'Status':<8}")
        self.logger.info("-" * 70)
        
        for table_name, result in results.items():
            if result["success"]:
                success_rate = (result["records"] / result["csv_records"] * 100) if result["csv_records"] > 0 else 0
                status = "PASS"
                self.logger.info(f"{table_name:<20} | {result['csv_records']:>11,} | {result['records']:>10,} | {success_rate:>11.1f}% | {status:<8}")
            else:
                status = "FAIL"
                self.logger.info(f"{table_name:<20} | {result['csv_records']:>11,} | {'0':>10} | {'0.0':>11}% | {status:<8}")
        
        self.logger.info("-" * 70)
        self.logger.info(f"{'TOTAL':<20} | {total_csv_records:>11,} | {total_records:>10,} | {overall_success_rate:>11.1f}% | {'':8}")
        self.logger.info("="*70)
        
        return summary

# Main execution function for command line usage
def main():
    """Main function for command line execution"""
    try:
        populator = SimpleCSVPopulator()
        result = populator.populate_all_tables()
        
        # The detailed table and summary are already printed by populate_all_tables()
        # Just return the result for programmatic access
        return result
        
    except Exception as e:
        print(f"Population failed: {e}")
        return None

if __name__ == "__main__":
    main()
