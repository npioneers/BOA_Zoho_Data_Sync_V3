#!/usr/bin/env python3
"""
Apply Column Mapping Fixes for Broken Views
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 APPLYING COLUMN MAPPING FIXES")
print("=" * 60)

# Define the fixes needed
fixes = {
    "view_csv_json_customer_payments": {
        "old_join": "csv.payment_id = json.payment_id",
        "new_join": "csv.customer_payment_id = json.payment_id",
        "description": "Customer Payments: csv.payment_id → csv.customer_payment_id"
    },
    "view_csv_json_vendor_payments": {
        "old_join": "csv.payment_id = json.payment_id", 
        "new_join": "csv.vendor_payment_id = json.payment_id",
        "description": "Vendor Payments: csv.payment_id → csv.vendor_payment_id"
    },
    "view_csv_json_sales_orders": {
        "old_join": "csv.salesorder_id = json.salesorder_id",
        "new_join": "csv.sales_order_id = json.salesorder_id", 
        "description": "Sales Orders: csv.salesorder_id → csv.sales_order_id"
    }
}

success_count = 0
total_fixes = len(fixes)

for view_name, fix_info in fixes.items():
    print(f"\n🔧 FIXING: {view_name}")
    print(f"   {fix_info['description']}")
    
    try:
        # Get the current view SQL
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{view_name}'")
        result = cursor.fetchone()
        
        if not result:
            print(f"   ❌ View {view_name} not found!")
            continue
            
        current_sql = result[0]
        
        # Apply the fix
        old_pattern = fix_info["old_join"]
        new_pattern = fix_info["new_join"]
        
        if old_pattern not in current_sql:
            print(f"   ⚠️  Pattern '{old_pattern}' not found in SQL")
            continue
            
        # Create corrected SQL
        corrected_sql = current_sql.replace(old_pattern, new_pattern)
        
        # Also fix the UNION part where needed
        if "customer_payments" in view_name:
            corrected_sql = corrected_sql.replace(
                "SELECT DISTINCT csv.payment_id",
                "SELECT DISTINCT csv.customer_payment_id"
            )
        elif "vendor_payments" in view_name:
            corrected_sql = corrected_sql.replace(
                "SELECT DISTINCT csv.payment_id", 
                "SELECT DISTINCT csv.vendor_payment_id"
            )
        elif "sales_orders" in view_name:
            corrected_sql = corrected_sql.replace(
                "SELECT DISTINCT csv.salesorder_id",
                "SELECT DISTINCT csv.sales_order_id"
            )
        
        # Drop the old view and create the corrected one
        print(f"   📝 Dropping old view...")
        cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
        
        print(f"   ✨ Creating corrected view...")
        cursor.execute(corrected_sql)
        
        # Test the new view
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        record_count = cursor.fetchone()[0]
        
        print(f"   ✅ SUCCESS! View now has {record_count:,} records")
        success_count += 1
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        continue

# Commit all changes
conn.commit()

print(f"\n🎯 FIX SUMMARY:")
print(f"   ✅ Successfully fixed: {success_count}/{total_fixes} views")
print(f"   🎉 Success rate: {(success_count/total_fixes)*100:.0f}%")

if success_count == total_fixes:
    print(f"\n🏆 ALL FIXES APPLIED SUCCESSFULLY!")
    print(f"   Your integration view success rate is now 100%!")
else:
    print(f"\n⚠️  Some fixes failed. Check errors above.")

# Verify the fixes by checking each view
print(f"\n📊 POST-FIX VERIFICATION:")
for view_name in fixes.keys():
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT data_source, COUNT(*) FROM {view_name} GROUP BY data_source")
        distribution = dict(cursor.fetchall())
        
        print(f"   {view_name}: {count:,} total records")
        for source, cnt in distribution.items():
            print(f"      {source}: {cnt:,}")
            
    except Exception as e:
        print(f"   {view_name}: ❌ ERROR - {e}")

conn.close()

print(f"\n🎉 COLUMN MAPPING FIXES COMPLETE!")
print(f"All broken views should now be working with proper CSV+JSON integration!")
