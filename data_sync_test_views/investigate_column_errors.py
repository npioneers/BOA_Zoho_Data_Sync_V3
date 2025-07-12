#!/usr/bin/env python3
"""
Investigate Column Mapping Errors
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 INVESTIGATING COLUMN MAPPING ERRORS")
print("=" * 60)

error_tables = [
    "customer_payments",
    "sales_orders", 
    "vendor_payments"
]

for table in error_tables:
    csv_table = f"csv_{table}"
    json_table = f"json_{table}"
    view_name = f"view_csv_json_{table}"
    
    print(f"\n📋 ANALYZING: {table}")
    print(f"   Tables: {csv_table} + {json_table}")
    
    # Check CSV table structure
    try:
        cursor.execute(f"PRAGMA table_info({csv_table})")
        csv_columns = [col[1] for col in cursor.fetchall()]
        
        # Look for ID columns
        csv_id_columns = [col for col in csv_columns if 'id' in col.lower()]
        print(f"   📊 CSV ID columns: {csv_id_columns}")
        
    except Exception as e:
        print(f"   ❌ CSV table error: {e}")
        continue
    
    # Check JSON table structure
    try:
        cursor.execute(f"PRAGMA table_info({json_table})")
        json_columns = [col[1] for col in cursor.fetchall()]
        
        # Look for ID columns
        json_id_columns = [col for col in json_columns if 'id' in col.lower()]
        print(f"   📊 JSON ID columns: {json_id_columns}")
        
    except Exception as e:
        print(f"   ❌ JSON table error: {e}")
        continue
    
    # Check the view SQL to see what's expected
    try:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{view_name}'")
        view_sql = cursor.fetchone()[0]
        
        # Extract the problematic line
        lines = view_sql.split('\n')
        problem_lines = [line.strip() for line in lines if 'csv.' in line and ('payment_id' in line or 'salesorder_id' in line)]
        
        if problem_lines:
            print(f"   🔧 Problematic SQL: {problem_lines[0][:80]}...")
        
        # Extract the JOIN condition
        join_lines = [line.strip() for line in lines if 'LEFT JOIN' in line.upper() or ('ON ' in line.upper() and '=' in line)]
        if join_lines:
            print(f"   🔗 JOIN condition: {join_lines[-1][:80]}...")
            
    except Exception as e:
        print(f"   ❌ View SQL error: {e}")
    
    # Suggest the correct mapping
    if table == "customer_payments" or table == "vendor_payments":
        print(f"   💡 LIKELY FIX: Use 'customer_payment_id' or 'vendor_payment_id' instead of 'payment_id'")
    elif table == "sales_orders":
        print(f"   💡 LIKELY FIX: Use 'sales_order_id' instead of 'salesorder_id'")

print(f"\n🎯 COLUMN MAPPING ERROR SUMMARY:")
print("The views are trying to use simplified column names that don't exist")
print("in the CSV tables. The CSV tables use compound names like:")
print("   • customer_payment_id (not payment_id)")
print("   • vendor_payment_id (not payment_id)")  
print("   • sales_order_id (not salesorder_id)")
print()
print("🔧 SOLUTION: Update view definitions to use correct CSV column names")

conn.close()
