#!/usr/bin/env python3
"""
Cross-check bills distribution - something doesn't match
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 CROSS-CHECKING BILLS DATA DISTRIBUTION")
print("=" * 50)

# Check multiple bills-related views
views_to_check = [
    'FINAL_view_csv_json_bills',
    'view_csv_json_bills',
    'view_csv_json_bills_v2',
    'view_csv_json_bills_v3',
    'view_csv_json_bills_deduplicated'
]

for view in views_to_check:
    print(f"\n📊 {view}:")
    try:
        # Total count
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        total = cursor.fetchone()[0]
        print(f"   Total records: {total:,}")
        
        # Distribution by data_source if column exists
        try:
            cursor.execute(f"SELECT data_source, COUNT(*) FROM {view} GROUP BY data_source")
            distribution = dict(cursor.fetchall())
            for source, count in distribution.items():
                print(f"   {source}: {count:,}")
        except:
            print("   (No data_source column)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Check if there are multiple bill tables or naming issues
print(f"\n🗃️ ALL TABLES WITH 'bill' IN NAME:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%bill%'")
bill_tables = [row[0] for row in cursor.fetchall()]
for table in bill_tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"   {table}: {count:,} records")

print(f"\n📋 ALL VIEWS WITH 'bill' IN NAME:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%bill%'")
bill_views = [row[0] for row in cursor.fetchall()]
for view in bill_views:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        count = cursor.fetchone()[0]
        print(f"   {view}: {count:,} records")
    except Exception as e:
        print(f"   {view}: ERROR - {e}")

conn.close()
