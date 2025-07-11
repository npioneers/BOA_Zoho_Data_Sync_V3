#!/usr/bin/env python3
"""
Table Report Generator for CSV Database Rebuild
Generates detailed table-format reports showing database population status
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

class TableReportGenerator:
    """Generate detailed table reports for database population status"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 csv_dir: str = "data/csv/Nangsel Pioneers_Latest"):
        self.db_path = Path(db_path)
        self.csv_dir = Path(csv_dir)
        
        # Table mappings
        self.table_mappings = {
            "csv_invoices": {"csv_file": "Invoice.csv", "description": "Invoice records from Zoho"},
            "csv_items": {"csv_file": "Item.csv", "description": "Product/service catalog"},
            "csv_contacts": {"csv_file": "Contacts.csv", "description": "Customer information"},
            "csv_bills": {"csv_file": "Bill.csv", "description": "Bill records"},
            "csv_customer_payments": {"csv_file": "Customer_Payment.csv", "description": "Customer payment records"},
            "csv_vendor_payments": {"csv_file": "Vendor_Payment.csv", "description": "Vendor payment records"},
            "csv_sales_orders": {"csv_file": "Sales_Order.csv", "description": "Sales order data"},
            "csv_purchase_orders": {"csv_file": "Purchase_Order.csv", "description": "Purchase order records"},
            "csv_credit_notes": {"csv_file": "Credit_Note.csv", "description": "Credit note records"},
            "csv_organizations": {"csv_file": "Contacts.csv", "description": "Organization data (filtered)"}
        }
    
    def get_database_counts(self):
        """Get record counts from database tables"""
        if not self.db_path.exists():
            return {}
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            counts = {}
            for table_name in self.table_mappings.keys():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    counts[table_name] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    counts[table_name] = 0  # Table doesn't exist
            
            conn.close()
            return counts
            
        except Exception as e:
            print(f"Error accessing database: {e}")
            return {}
    
    def get_csv_counts(self):
        """Get record counts from CSV files"""
        csv_counts = {}
        
        for table_name, info in self.table_mappings.items():
            csv_file = self.csv_dir / info["csv_file"]
            
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file)
                    if table_name == "csv_organizations":
                        # Organizations are filtered from contacts
                        csv_counts[table_name] = len(df[df['Contact Type'] == 'organization']) if 'Contact Type' in df.columns else 0
                    else:
                        csv_counts[table_name] = len(df)
                except Exception as e:
                    print(f"Error reading {csv_file}: {e}")
                    csv_counts[table_name] = 0
            else:
                csv_counts[table_name] = 0
        
        return csv_counts
    
    def get_table_column_info(self):
        """Get column information for each table"""
        if not self.db_path.exists():
            return {}
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            column_info = {}
            for table_name in self.table_mappings.keys():
                try:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    column_info[table_name] = len(columns)
                except sqlite3.OperationalError:
                    column_info[table_name] = 0
            
            conn.close()
            return column_info
            
        except Exception as e:
            print(f"Error getting column info: {e}")
            return {}
    
    def generate_report(self):
        """Generate comprehensive table report"""
        print("=" * 120)
        print("CSV DATABASE REBUILD - TABLE POPULATION REPORT")
        print("=" * 120)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.db_path}")
        print(f"CSV Source: {self.csv_dir}")
        print()
        
        # Get data
        db_counts = self.get_database_counts()
        csv_counts = self.get_csv_counts()
        column_info = self.get_table_column_info()
        
        if not db_counts:
            print("❌ Database not found or inaccessible!")
            return
        
        # Calculate totals
        total_db_records = sum(db_counts.values())
        total_csv_records = sum(csv_counts.values())
        total_tables = len(self.table_mappings)
        populated_tables = sum(1 for count in db_counts.values() if count > 0)
        
        # Summary
        print("📊 SUMMARY")
        print("-" * 50)
        print(f"Total Tables: {total_tables}")
        print(f"Populated Tables: {populated_tables}")
        print(f"Success Rate: {(populated_tables/total_tables)*100:.1f}%")
        print(f"Total Records in Database: {total_db_records:,}")
        print(f"Total Records in CSV Files: {total_csv_records:,}")
        print(f"Population Efficiency: {(total_db_records/total_csv_records)*100:.1f}%" if total_csv_records > 0 else "N/A")
        print()
        
        # Detailed table report
        print("📋 DETAILED TABLE REPORT")
        print("-" * 120)
        
        # Table header
        header = f"{'Table Name':<20} {'Description':<25} {'CSV Records':<12} {'DB Records':<11} {'Success Rate':<12} {'Columns':<8} {'Status':<10}"
        print(header)
        print("-" * 120)
        
        # Table rows
        for table_name, info in self.table_mappings.items():
            description = info["description"][:24]  # Truncate if too long
            csv_count = csv_counts.get(table_name, 0)
            db_count = db_counts.get(table_name, 0)
            columns = column_info.get(table_name, 0)
            
            if csv_count > 0:
                success_rate = f"{(db_count/csv_count)*100:.1f}%"
            else:
                success_rate = "N/A"
            
            if db_count > 0:
                status = "✅ Complete"
            elif csv_count > 0:
                status = "❌ Failed"
            else:
                status = "⚠️ No CSV"
            
            row = f"{table_name:<20} {description:<25} {csv_count:<12,} {db_count:<11,} {success_rate:<12} {columns:<8} {status:<10}"
            print(row)
        
        print("-" * 120)
        print(f"{'TOTALS':<20} {'':<25} {total_csv_records:<12,} {total_db_records:<11,} {((total_db_records/total_csv_records)*100):.1f}%{'':<4} {'':<8} {populated_tables}/{total_tables}")
        print()
        
        # Performance metrics
        db_size = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        print("⚡ PERFORMANCE METRICS")
        print("-" * 50)
        print(f"Database Size: {db_size:.1f} MB")
        print(f"Average Records per Table: {total_db_records/populated_tables:.0f}" if populated_tables > 0 else "N/A")
        print(f"Largest Table: {max(db_counts.items(), key=lambda x: x[1])[0]} ({max(db_counts.values()):,} records)" if db_counts else "N/A")
        print(f"Smallest Table: {min(db_counts.items(), key=lambda x: x[1])[0]} ({min(db_counts.values()):,} records)" if db_counts else "N/A")
        print()
        
        # Recommendations
        failed_tables = [name for name, count in db_counts.items() if count == 0 and csv_counts.get(name, 0) > 0]
        if failed_tables:
            print("⚠️ RECOMMENDATIONS")
            print("-" * 50)
            print(f"Failed tables detected: {', '.join(failed_tables)}")
            print("Run population script to populate missing tables.")
            print()
        
        print("=" * 120)

def main():
    """Main execution function"""
    generator = TableReportGenerator()
    generator.generate_report()

if __name__ == "__main__":
    main()
