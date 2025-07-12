#!/usr/bin/env python3
"""
Investigate the remaining 0% populated ID fields
"""
import sqlite3
import pandas as pd
from pathlib import Path

def investigate_id_fields():
    """Check what's happening with the ID fields that are still 0%"""
    
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    
    print("=== ID FIELD INVESTIGATION ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check sales_order_id field
        print("🔍 INVESTIGATING: sales_order_id")
        cursor.execute("PRAGMA table_info(csv_sales_orders)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Available columns: {[col for col in columns if 'id' in col.lower()]}")
        
        # Check what we actually have for ID-like fields
        cursor.execute("SELECT * FROM csv_sales_orders LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("PRAGMA table_info(csv_sales_orders)")
            col_info = cursor.fetchall()
            for i, (_, col_name, _, _, _, _) in enumerate(col_info):
                if 'id' in col_name.lower():
                    value = row[i] if i < len(row) else 'N/A'
                    print(f"   {col_name}: {value}")
        
        print()
        
        # Check customer_payment_id field  
        print("🔍 INVESTIGATING: customer_payment_id")
        cursor.execute("PRAGMA table_info(csv_customer_payments)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Available columns: {[col for col in columns if 'id' in col.lower()]}")
        
        cursor.execute("SELECT * FROM csv_customer_payments LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("PRAGMA table_info(csv_customer_payments)")
            col_info = cursor.fetchall()
            for i, (_, col_name, _, _, _, _) in enumerate(col_info):
                if 'id' in col_name.lower():
                    value = row[i] if i < len(row) else 'N/A'
                    print(f"   {col_name}: {value}")
        
        print()
        
        # Let's also check the CSV source to understand the original column names
        csv_dir = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\csv\Nangsel Pioneers_Latest"
        sales_order_csv = Path(csv_dir) / "Sales_Order.csv"
        
        if sales_order_csv.exists():
            print("🔍 CHECKING CSV SOURCE: Sales_Order.csv")
            df = pd.read_csv(sales_order_csv, nrows=1)
            id_columns = [col for col in df.columns if 'ID' in col or 'Id' in col]
            print(f"   CSV ID columns: {id_columns}")
            if id_columns:
                for col in id_columns:
                    print(f"   {col}: {df[col].iloc[0]}")
        
        print()
        
        # Check customer payment CSV
        customer_payment_csv = Path(csv_dir) / "Customer_Payment.csv"
        if customer_payment_csv.exists():
            print("🔍 CHECKING CSV SOURCE: Customer_Payment.csv")
            df = pd.read_csv(customer_payment_csv, nrows=1)
            id_columns = [col for col in df.columns if 'ID' in col or 'Id' in col]
            print(f"   CSV ID columns: {id_columns}")
            if id_columns:
                for col in id_columns:
                    print(f"   {col}: {df[col].iloc[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Investigation error: {e}")

if __name__ == "__main__":
    investigate_id_fields()
