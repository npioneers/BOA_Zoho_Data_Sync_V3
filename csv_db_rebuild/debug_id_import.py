#!/usr/bin/env python3
"""
Debug why specific ID fields are NULL during import
Focus on sales_order_id and customer_payment_id vs working customer_id
"""
import sqlite3
import pandas as pd
from pathlib import Path

def debug_id_import_issue():
    """Investigate the import process for ID fields"""
    
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    csv_dir = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\csv\Nangsel Pioneers_Latest"
    
    print("=" * 80)
    print("🔍 DEBUGGING ID FIELD IMPORT ISSUES")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test Case 1: Sales Order ID vs Customer ID (same table)
        print("📋 CASE 1: SALES ORDERS TABLE - ID Field Comparison")
        print("-" * 60)
        
        # Get database schema for sales orders
        cursor.execute("PRAGMA table_info(csv_sales_orders)")
        sales_order_schema = cursor.fetchall()
        
        print("Database schema for ID fields:")
        for col_info in sales_order_schema:
            col_name = col_info[1]
            if 'id' in col_name.lower():
                col_type = col_info[2]
                not_null = col_info[3]
                default_val = col_info[4]
                primary_key = col_info[5]
                print(f"  {col_name}: {col_type}, NOT NULL={not_null}, DEFAULT={default_val}, PK={primary_key}")
        
        print()
        
        # Check CSV source columns
        sales_csv = Path(csv_dir) / "Sales_Order.csv"
        if sales_csv.exists():
            print("CSV source ID columns:")
            df = pd.read_csv(sales_csv, nrows=5)
            id_cols = [col for col in df.columns if 'ID' in col or 'Id' in col]
            for col in id_cols:
                sample_values = df[col].dropna().head(3).tolist()
                null_count = df[col].isnull().sum()
                print(f"  {col}: Sample={sample_values}, NULLs={null_count}/5")
        
        print()
        
        # Check data mapping - what actually made it to database
        print("Database population for ID fields (first 3 records):")
        cursor.execute("SELECT sales_order_id, customer_id, sales_order_number FROM csv_sales_orders LIMIT 3")
        db_records = cursor.fetchall()
        for i, (so_id, cust_id, so_num) in enumerate(db_records, 1):
            print(f"  Record {i}: sales_order_id={so_id}, customer_id={cust_id}, sales_order_number={so_num}")
        
        print()
        print("=" * 80)
        
        # Test Case 2: Customer Payment ID 
        print("📋 CASE 2: CUSTOMER PAYMENTS TABLE - ID Field Analysis")
        print("-" * 60)
        
        # Database schema
        cursor.execute("PRAGMA table_info(csv_customer_payments)")
        payment_schema = cursor.fetchall()
        
        print("Database schema for ID fields:")
        for col_info in payment_schema:
            col_name = col_info[1]
            if 'id' in col_name.lower():
                col_type = col_info[2]
                not_null = col_info[3]
                default_val = col_info[4]
                primary_key = col_info[5]
                print(f"  {col_name}: {col_type}, NOT NULL={not_null}, DEFAULT={default_val}, PK={primary_key}")
        
        print()
        
        # Check CSV source
        payment_csv = Path(csv_dir) / "Customer_Payment.csv"
        if payment_csv.exists():
            print("CSV source ID columns:")
            df = pd.read_csv(payment_csv, nrows=5)
            id_cols = [col for col in df.columns if 'ID' in col or 'Id' in col]
            for col in id_cols:
                sample_values = df[col].dropna().head(3).tolist()
                null_count = df[col].isnull().sum()
                print(f"  {col}: Sample={sample_values}, NULLs={null_count}/5")
        
        print()
        
        # Check database population
        print("Database population for ID fields (first 3 records):")
        cursor.execute("SELECT customer_payment_id, customer_id, amount FROM csv_customer_payments LIMIT 3")
        db_records = cursor.fetchall()
        for i, (cp_id, cust_id, amount) in enumerate(db_records, 1):
            print(f"  Record {i}: customer_payment_id={cp_id}, customer_id={cust_id}, amount={amount}")
        
        print()
        print("=" * 80)
        
        # Test Case 3: Check column name transformation
        print("📋 CASE 3: COLUMN NAME TRANSFORMATION DEBUG")
        print("-" * 60)
        
        # Test the transformation function manually
        from runner_csv_db_rebuild import csv_to_db_column_name
        
        test_columns = [
            "SalesOrder ID",      # This fails
            "Customer ID",        # This works  
            "CustomerPayment ID", # This fails
            "CustomerID",         # This works
            "SalesOrder Number",  # This works
        ]
        
        print("Column name transformations:")
        for csv_col in test_columns:
            db_col = csv_to_db_column_name(csv_col)
            print(f"  '{csv_col}' -> '{db_col}'")
        
        print()
        
        # Test Case 4: Check if these columns exist in database but with different names
        print("📋 CASE 4: COLUMN EXISTENCE CHECK")
        print("-" * 60)
        
        # Sales order table columns
        cursor.execute("PRAGMA table_info(csv_sales_orders)")
        so_columns = [row[1] for row in cursor.fetchall()]
        print("Sales order table columns containing 'order' or 'sales':")
        for col in so_columns:
            if 'order' in col.lower() or 'sales' in col.lower():
                print(f"  {col}")
        
        print()
        
        # Customer payment table columns  
        cursor.execute("PRAGMA table_info(csv_customer_payments)")
        cp_columns = [row[1] for row in cursor.fetchall()]
        print("Customer payment table columns containing 'payment' or 'customer':")
        for col in cp_columns:
            if 'payment' in col.lower() or 'customer' in col.lower():
                print(f"  {col}")
        
        print()
        print("=" * 80)
        
        # Test Case 5: Check if data is going to a different column
        print("📋 CASE 5: DATA LOCATION CHECK")
        print("-" * 60)
        
        # Look for any column that has the expected ID values
        print("Searching for SalesOrder ID value '3990265000000897001' in all sales order columns:")
        cursor.execute("PRAGMA table_info(csv_sales_orders)")
        all_so_cols = [row[1] for row in cursor.fetchall()]
        
        for col in all_so_cols:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM csv_sales_orders WHERE {col} = '3990265000000897001'")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  ✅ FOUND in column '{col}': {count} records")
            except Exception as e:
                # Skip columns that can't be searched (wrong data type, etc.)
                pass
        
        print()
        
        print("Searching for CustomerPayment ID value '3990265000000091091' in all customer payment columns:")
        cursor.execute("PRAGMA table_info(csv_customer_payments)")
        all_cp_cols = [row[1] for row in cursor.fetchall()]
        
        for col in all_cp_cols:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM csv_customer_payments WHERE {col} = '3990265000000091091'")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  ✅ FOUND in column '{col}': {count} records")
            except Exception as e:
                pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_id_import_issue()
