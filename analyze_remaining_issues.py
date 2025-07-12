#!/usr/bin/env python3
"""
Analysis of remaining mapping issues after re-import
"""
import sqlite3
import pandas as pd
from pathlib import Path

def analyze_remaining_issues():
    """Analyze the remaining compound word fields that aren't mapping correctly"""
    
    print("=== ANALYSIS OF REMAINING MAPPING ISSUES ===")
    print()
    
    csv_dir = "data/csv/Nangsel Pioneers_Latest"
    db_path = "data/database/production.db"
    
    # Fields that are still failing
    failing_fields = {
        "csv_sales_orders": [
            ("SalesOrder ID", "sales_order_id")
        ],
        "csv_customer_payments": [
            ("CustomerPayment ID", "customer_payment_id")
        ],
        "csv_vendor_payments": [
            ("VendorPayment ID", "vendor_payment_id"),
            ("EmailID", "email_id")
        ]
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for table_name, fields in failing_fields.items():
            print(f"🔍 ANALYZING FAILING FIELDS IN: {table_name}")
            
            # Get all database columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            db_columns = [row[1] for row in cursor.fetchall()]
            
            # Get CSV info
            csv_file_map = {
                "csv_sales_orders": "Sales_Order.csv",
                "csv_customer_payments": "Customer_Payment.csv", 
                "csv_vendor_payments": "Vendor_Payment.csv"
            }
            
            csv_path = Path(csv_dir) / csv_file_map[table_name]
            df = pd.read_csv(csv_path, nrows=5)
            csv_columns = list(df.columns)
            
            print(f"   CSV File: {csv_file_map[table_name]}")
            print(f"   Database columns: {len(db_columns)}")
            print(f"   CSV columns: {len(csv_columns)}")
            print()
            
            for csv_field, expected_db_field in fields:
                print(f"   FIELD: '{csv_field}' -> '{expected_db_field}'")
                
                # Check if CSV field exists
                csv_exists = csv_field in csv_columns
                print(f"   ✅ CSV field exists: {csv_exists}")
                
                if csv_exists:
                    # Show CSV sample
                    sample_data = df[csv_field].dropna().head(3).tolist()
                    print(f"   📊 CSV sample data: {sample_data}")
                
                # Check if expected DB field exists
                db_exists = expected_db_field in db_columns
                print(f"   {'✅' if db_exists else '❌'} Expected DB field exists: {db_exists}")
                
                if not db_exists:
                    # Look for similar columns
                    similar_cols = [col for col in db_columns if 'id' in col.lower() and ('sales' in col.lower() or 'customer' in col.lower() or 'vendor' in col.lower() or 'payment' in col.lower())]
                    print(f"   🔍 Similar DB columns: {similar_cols[:5]}")
                    
                    # Test our transformation function
                    def csv_to_db_column_name(csv_column: str) -> str:
                        import re
                        column = csv_column
                        column = re.sub(r'([a-z])([A-Z])', r'\\1 \\2', column)
                        db_column = re.sub(r'[^a-zA-Z0-9]', '_', column)
                        db_column = db_column.lower()
                        db_column = re.sub(r'_+', '_', db_column)
                        db_column = db_column.strip('_')
                        return db_column
                    
                    transformed = csv_to_db_column_name(csv_field)
                    print(f"   🔧 Our transformation produces: '{transformed}'")
                    
                    # Check if our transformation exists in DB
                    our_exists = transformed in db_columns
                    print(f"   {'✅' if our_exists else '❌'} Our transformation exists in DB: {our_exists}")
                    
                    if our_exists:
                        # Check population of our transformed field
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE `{transformed}` IS NOT NULL AND `{transformed}` != ''")
                        populated = cursor.fetchone()[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        total = cursor.fetchone()[0]
                        rate = (populated/total*100) if total > 0 else 0
                        print(f"   📊 Population of '{transformed}': {populated}/{total} ({rate:.1f}%)")
                
                print()
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def check_exact_db_columns():
    """Check the exact database column names for ID fields"""
    
    print("=== EXACT DATABASE COLUMN ANALYSIS ===")
    
    db_path = "data/database/production.db"
    tables = ["csv_sales_orders", "csv_customer_payments", "csv_vendor_payments"]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for table in tables:
            print(f"\\n📋 TABLE: {table}")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Filter for ID-related columns
            id_columns = [col for col in columns if 'id' in col[1].lower()]
            
            print("   ID-related columns:")
            for col_info in id_columns:
                col_id, name, data_type, not_null, default_val, pk = col_info
                
                # Check population
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE `{name}` IS NOT NULL AND `{name}` != ''")
                populated = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total = cursor.fetchone()[0]
                rate = (populated/total*100) if total > 0 else 0
                
                status = "✅" if rate > 50 else "⚠️" if rate > 0 else "❌"
                print(f"   {status} {name}: {populated}/{total} ({rate:.1f}%)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Column analysis failed: {e}")

if __name__ == "__main__":
    analyze_remaining_issues()
    check_exact_db_columns()
