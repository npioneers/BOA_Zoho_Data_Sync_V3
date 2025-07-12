#!/usr/bin/env python3
"""
Show Exact SQL Changes Needed for Each Broken View
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 EXACT SQL CORRECTIONS NEEDED")
print("=" * 80)

views_to_fix = [
    "view_csv_json_customer_payments",
    "view_csv_json_vendor_payments", 
    "view_csv_json_sales_orders"
]

for view_name in views_to_fix:
    print(f"\n{'='*60}")
    print(f"📋 {view_name.upper()}")
    print(f"{'='*60}")
    
    try:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{view_name}'")
        current_sql = cursor.fetchone()[0]
        
        print("🔧 CURRENT SQL (BROKEN):")
        print("-" * 40)
        print(current_sql)
        print()
        
        # Create corrected version
        print("✅ CORRECTED SQL:")
        print("-" * 40)
        
        if "customer_payments" in view_name:
            corrected_sql = current_sql.replace("csv.payment_id", "csv.customer_payment_id")
            print(corrected_sql)
            print("\n🔍 KEY CHANGE:")
            print("   csv.payment_id = json.payment_id")
            print("   ↓ BECOMES ↓")
            print("   csv.customer_payment_id = json.payment_id")
            
        elif "vendor_payments" in view_name:
            corrected_sql = current_sql.replace("csv.payment_id", "csv.vendor_payment_id")
            print(corrected_sql)
            print("\n🔍 KEY CHANGE:")
            print("   csv.payment_id = json.payment_id")
            print("   ↓ BECOMES ↓")
            print("   csv.vendor_payment_id = json.payment_id")
            
        elif "sales_orders" in view_name:
            corrected_sql = current_sql.replace("csv.salesorder_id", "csv.sales_order_id")
            print(corrected_sql)
            print("\n🔍 KEY CHANGE:")
            print("   csv.salesorder_id = json.salesorder_id")
            print("   ↓ BECOMES ↓")
            print("   csv.sales_order_id = json.salesorder_id")
        
    except Exception as e:
        print(f"❌ Error getting SQL for {view_name}: {e}")

print(f"\n🎯 IMPLEMENTATION COMMANDS:")
print("=" * 60)
print("To fix these views, you would run:")
print()
print("1. DROP VIEW view_csv_json_customer_payments;")
print("2. CREATE VIEW view_csv_json_customer_payments AS [corrected SQL];")
print()
print("3. DROP VIEW view_csv_json_vendor_payments;")
print("4. CREATE VIEW view_csv_json_vendor_payments AS [corrected SQL];")
print()
print("5. DROP VIEW view_csv_json_sales_orders;") 
print("6. CREATE VIEW view_csv_json_sales_orders AS [corrected SQL];")

print(f"\n💡 ROOT CAUSE SUMMARY:")
print("=" * 60)
print("The views were created assuming CSV and JSON tables use the same")
print("column names, but they don't:")
print()
print("CSV Tables           JSON Tables")
print("---------------      ---------------")
print("customer_payment_id  payment_id")
print("vendor_payment_id    payment_id")
print("sales_order_id       salesorder_id")
print()
print("The JOIN conditions need to account for these naming differences.")

conn.close()
