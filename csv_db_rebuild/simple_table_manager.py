"""
Simple Table Manager
Manages database tables - clearing, stats, etc.
"""
import sqlite3
import logging
from pathlib import Path
import sys

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


class SimpleTableManager:
    """Simple table management operations"""
    
    def __init__(self, db_path: str = "data/database/production.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)

    def clear_table(self, table_name: str) -> bool:
        """Clear all data from a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                self.logger.warning(f"Table {table_name} does not exist")
                return False
            
            # Clear the table
            cursor.execute(f"DELETE FROM {table_name}")
            rows_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared {rows_deleted} rows from {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing table {table_name}: {str(e)}")
            return False

    def clear_all_tables(self) -> dict:
        """Clear all mapped tables"""
        self.logger.info("Clearing all tables")
        results = {}
        
        for table_name in TABLE_MAPPINGS.keys():
            results[table_name] = self.clear_table(table_name)
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Cleared {successful}/{len(results)} tables successfully")
        
        return results

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error getting count for {table_name}: {str(e)}")
            return -1

    def get_all_table_counts(self) -> dict:
        """Get row counts for all tables"""
        counts = {}
        
        for table_name in TABLE_MAPPINGS.keys():
            counts[table_name] = self.get_table_count(table_name)
        
        return counts
