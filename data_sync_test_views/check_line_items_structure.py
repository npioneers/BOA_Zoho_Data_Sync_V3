#!/usr/bin/env python3
"""
Check the structure of bills line items
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 BILLS LINE ITEMS STRUCTURE ANALYSIS")
print("=" * 50)

# Check the structure of json_bills_line_items
print("📋 json_bills_line_items columns:")
cursor.execute("PRAGMA table_info(json_bills_line_items)")
columns = cursor.fetchall()
for col in columns:
    print(f"   {col[1]} ({col[2]})")

print(f"\n📊 Sample records from json_bills_line_items:")
cursor.execute("SELECT * FROM json_bills_line_items LIMIT 3")
samples = cursor.fetchall()
for i, sample in enumerate(samples):
    print(f"   Record {i+1}: {sample[:5]}...")  # First 5 fields only

print(f"\n🔗 Checking view_flat_json_bills (likely the 'flat' table):")
cursor.execute("PRAGMA table_info(view_flat_json_bills)")
columns = cursor.fetchall()
key_columns = [col[1] for col in columns if 'bill' in col[1].lower() or 'id' in col[1].lower()]
print(f"   Key columns: {key_columns}")

# Sample from flat view
cursor.execute("SELECT * FROM view_flat_json_bills LIMIT 2")
samples = cursor.fetchall()
print(f"   Sample records: {len(samples)} found")

# Check the expansion ratio
cursor.execute("SELECT COUNT(*) FROM view_flat_json_bills")
flat_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT bill_id) FROM view_flat_json_bills")
unique_bills = cursor.fetchone()[0]

print(f"\n📈 EXPANSION ANALYSIS:")
print(f"   view_flat_json_bills total: {flat_count:,}")
print(f"   Unique bill_ids: {unique_bills:,}")
if unique_bills > 0:
    expansion = flat_count / unique_bills
    print(f"   Expansion ratio: {expansion:.1f}x")

# Now check what happens in the main view
print(f"\n🔍 MAIN VIEW JOIN ANALYSIS:")
cursor.execute("""
    SELECT 
        CASE 
            WHEN flat.bill_id IS NOT NULL THEN 'enhanced'
            ELSE 'csv_only'
        END as data_source,
        COUNT(*) as records
    FROM csv_bills csv
    LEFT JOIN view_flat_json_bills flat ON csv.bill_id = flat.bill_id
    GROUP BY 1
""")
join_analysis = cursor.fetchall()
for source, count in join_analysis:
    print(f"   {source}: {count:,}")

conn.close()

print(f"\n💡 UNDERSTANDING THE 'ENHANCED' MYSTERY:")
print("The massive record count likely comes from:")
print("1. CSV bills (headers) LEFT JOINed with flat JSON bills (line items)")
print("2. Each CSV bill header gets duplicated for each JSON line item")
print("3. 'enhanced' = CSV header data enhanced with JSON line item details")
print("4. This is data enrichment, not JSON precedence over CSV!")
