#!/usr/bin/env python3
"""
Analyze database schema and column mapping for csv_sales_orders table
"""
import sqlite3
import pandas as pd
from pathlib import Path

def analyze_database_schema():
    """Analyze the database schema and data mapping"""
    
    db_path = "../data/database/production.db"
    
    print("=== DATABASE SCHEMA ANALYSIS ===")
    print(f"Database: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema
        print("=== CSV_SALES_ORDERS TABLE SCHEMA ===")
        cursor.execute("PRAGMA table_info(csv_sales_orders)")
        columns = cursor.fetchall()
        
        print(f"Total columns in database table: {len(columns)}")
        print("Column mapping:")
        for i, (col_id, name, data_type, not_null, default_val, pk) in enumerate(columns):
            print(f"{i+1:2d}. {name} ({data_type})")
        print()
        
        # Check for sales order number related columns
        print("=== SALES ORDER NUMBER COLUMNS ===")
        so_columns = [col[1] for col in columns if 'order' in col[1].lower() or 'sales' in col[1].lower()]
        print(f"Columns containing 'order' or 'sales': {so_columns}")
        print()
        
        # Check actual data in the sales order number column
        print("=== DATA ANALYSIS ===")
        cursor.execute("SELECT COUNT(*) FROM csv_sales_orders")
        total_records = cursor.fetchone()[0]
        print(f"Total records: {total_records:,}")
        
        # Try different possible column names for sales order number
        possible_columns = ['sales_order_number', 'salesorder_number', 'so_number', 'order_number']
        for col_name in possible_columns:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM csv_sales_orders WHERE `{col_name}` IS NOT NULL AND `{col_name}` != ''")
                populated_count = cursor.fetchone()[0]
                print(f"Column '{col_name}': {populated_count:,} populated records ({(populated_count/total_records)*100:.1f}%)")
                
                # Show sample values
                cursor.execute(f"SELECT `{col_name}` FROM csv_sales_orders WHERE `{col_name}` IS NOT NULL AND `{col_name}` != '' LIMIT 5")
                samples = cursor.fetchall()
                if samples:
                    print(f"  Sample values: {[row[0] for row in samples]}")
                print()
                
            except sqlite3.OperationalError as e:
                if "no such column" in str(e):
                    print(f"Column '{col_name}': Not found")
                else:
                    print(f"Column '{col_name}': Error - {e}")
        
        # Check the actual column that should contain sales order numbers
        # Look for columns that might be mapped from "SalesOrder Number"
        print("=== CHECKING ALL COLUMNS FOR DATA ===")
        for col_id, name, data_type, not_null, default_val, pk in columns:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM csv_sales_orders WHERE `{name}` IS NOT NULL AND `{name}` != ''")
                populated = cursor.fetchone()[0]
                if populated > 0:
                    cursor.execute(f"SELECT `{name}` FROM csv_sales_orders WHERE `{name}` IS NOT NULL AND `{name}` != '' LIMIT 3")
                    samples = cursor.fetchall()
                    sample_values = [str(row[0])[:50] for row in samples]  # Limit to 50 chars
                    print(f"{name}: {populated:,} records ({(populated/total_records)*100:.1f}%) - Sample: {sample_values}")
            except Exception as e:
                print(f"{name}: Error - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database analysis failed: {e}")

if __name__ == "__main__":
    analyze_database_schema()
