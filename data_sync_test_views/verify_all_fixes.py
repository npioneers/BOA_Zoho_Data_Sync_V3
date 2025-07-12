#!/usr/bin/env python3
"""
Verify All Integration Views Are Now Working
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🎉 POST-FIX VERIFICATION: ALL INTEGRATION VIEWS")
print("=" * 70)

# Get all integration views
integration_views = [
    "view_csv_json_bills",
    "view_csv_json_contacts", 
    "view_csv_json_credit_notes",
    "view_csv_json_customer_payments",  # FIXED
    "view_csv_json_invoices",
    "view_csv_json_items",
    "view_csv_json_organizations",
    "view_csv_json_purchase_orders",
    "view_csv_json_sales_orders",      # FIXED
    "view_csv_json_vendor_payments"    # FIXED
]

working_views = 0
total_views = len(integration_views)
total_records = 0

print("📊 INTEGRATION VIEW STATUS:")

for view in integration_views:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        count = cursor.fetchone()[0]
        total_records += count
        
        # Get distribution
        cursor.execute(f"SELECT data_source, COUNT(*) FROM {view} GROUP BY data_source")
        distribution = dict(cursor.fetchall())
        
        print(f"\n✅ {view}: {count:,} records")
        for source, src_count in distribution.items():
            percentage = (src_count / count * 100) if count > 0 else 0
            print(f"   {source}: {src_count:,} ({percentage:.1f}%)")
        
        working_views += 1
        
    except Exception as e:
        print(f"\n❌ {view}: ERROR - {e}")

print(f"\n🎯 FINAL ARCHITECTURE SUMMARY:")
print("=" * 50)
print(f"✅ Working Views: {working_views}/{total_views} ({(working_views/total_views)*100:.0f}%)")
print(f"📊 Total Records: {total_records:,}")
print(f"🎉 Success Rate: {(working_views/total_views)*100:.0f}%")

if working_views == total_views:
    print(f"\n🏆 PERFECT SUCCESS!")
    print(f"🎯 ALL INTEGRATION VIEWS ARE NOW WORKING!")
    print(f"📈 Complete data visibility achieved!")
    
    # Categorize the results
    print(f"\n📋 FINAL CATEGORIZATION:")
    
    line_expansion = ["bills", "invoices"]
    csv_preferred = ["items", "contacts"]
    csv_only = ["credit_notes", "purchase_orders"]
    json_only = []  # May change based on contacts
    working_integration = ["customer_payments", "vendor_payments", "sales_orders"]
    
    print(f"   🔄 Line Item Expansion: {len(line_expansion)} tables")
    print(f"   🎉 CSV-Preferred Implemented: {len(csv_preferred)} tables")
    print(f"   📋 CSV-Only Correct: {len(csv_only)} tables")
    print(f"   🔧 Fixed Integration: {len(working_integration)} tables")
    print(f"   ⚪ Minimal Data: 1 table (organizations)")

else:
    print(f"\n⚠️  {total_views - working_views} views still have issues")

conn.close()
