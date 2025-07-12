#!/usr/bin/env python3
"""
Analyze Sales Order CSV data to understand the sales_order_number field population
"""
import pandas as pd
import sqlite3
from pathlib import Path

def analyze_sales_order_csv():
    """Analyze the Sales_Order.csv file"""
    
    csv_path = "../data/csv/Nangsel Pioneers_Latest/Sales_Order.csv"
    db_path = "../data/database/production.db"
    
    print("=== SALES ORDER CSV ANALYSIS ===")
    print(f"CSV File: {csv_path}")
    print(f"Database: {db_path}")
    print()
    
    # Read CSV file
    try:
        print("Reading CSV file...")
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"✅ CSV loaded successfully")
        print(f"Total rows in CSV: {len(df):,}")
        print(f"Total columns in CSV: {len(df.columns)}")
        print()
        
        # Print column names to see the exact structure
        print("=== CSV COLUMNS ===")
        for i, col in enumerate(df.columns):
            print(f"{i+1:2d}. {col}")
        print()
        
        # Analyze SalesOrder Number column
        sales_order_col = 'SalesOrder Number'
        if sales_order_col in df.columns:
            print(f"=== ANALYZING '{sales_order_col}' COLUMN ===")
            
            # Count non-null values
            non_null_count = df[sales_order_col].notna().sum()
            null_count = df[sales_order_col].isna().sum()
            empty_count = (df[sales_order_col] == '').sum()
            
            print(f"Non-null values: {non_null_count:,}")
            print(f"Null values: {null_count:,}")
            print(f"Empty string values: {empty_count:,}")
            print(f"Population rate: {(non_null_count / len(df)) * 100:.1f}%")
            print()
            
            # Show unique values (first 20)
            print("=== UNIQUE SALES ORDER NUMBERS (First 20) ===")
            unique_values = df[sales_order_col].dropna().unique()
            print(f"Total unique values: {len(unique_values):,}")
            for i, value in enumerate(unique_values[:20]):
                print(f"{i+1:2d}. '{value}'")
            print()
            
            # Show sample records with sales order numbers
            print("=== SAMPLE RECORDS WITH SALES ORDER NUMBERS ===")
            sample_with_numbers = df[df[sales_order_col].notna()].head(5)
            for idx, row in sample_with_numbers.iterrows():
                print(f"Row {idx}: SalesOrder ID='{row['SalesOrder ID']}', Number='{row[sales_order_col]}', Date='{row.get('Order Date', 'N/A')}'")
            print()
            
        else:
            print(f"❌ Column '{sales_order_col}' not found in CSV")
            print("Available columns with 'order' or 'sales':")
            for col in df.columns:
                if 'order' in col.lower() or 'sales' in col.lower():
                    print(f"  - {col}")
        
        # Check database comparison
        print("=== DATABASE COMPARISON ===")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check csv_sales_orders table
            cursor.execute("SELECT COUNT(*) FROM csv_sales_orders")
            db_count = cursor.fetchone()[0]
            print(f"Records in database table 'csv_sales_orders': {db_count:,}")
            
            # Check sales_order_number field in database
            cursor.execute("SELECT COUNT(*) FROM csv_sales_orders WHERE sales_order_number IS NOT NULL AND sales_order_number != ''")
            db_populated_count = cursor.fetchone()[0]
            print(f"Records with populated sales_order_number: {db_populated_count:,}")
            print(f"Database population rate: {(db_populated_count / db_count) * 100:.1f}%")
            
            # Show sample records from database
            print("\\n=== SAMPLE DATABASE RECORDS ===")
            cursor.execute("""
                SELECT salesorder_id, sales_order_number, order_date, status 
                FROM csv_sales_orders 
                WHERE sales_order_number IS NOT NULL AND sales_order_number != ''
                LIMIT 5
            """)
            db_samples = cursor.fetchall()
            for row in db_samples:
                print(f"DB: ID='{row[0]}', Number='{row[1]}', Date='{row[2]}', Status='{row[3]}'")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Database analysis failed: {e}")
        
        # Check for specific sales order numbers mentioned in the issue
        print("\\n=== CHECKING FOR SPECIFIC SALES ORDERS ===")
        target_numbers = ['SO/25-26/00808', 'SO-00009', 'SO-00010', 'SO-00011']
        for target in target_numbers:
            found = df[df[sales_order_col].str.contains(target, na=False)].shape[0] if sales_order_col in df.columns else 0
            print(f"'{target}': {found} matches found in CSV")
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

if __name__ == "__main__":
    analyze_sales_order_csv()
