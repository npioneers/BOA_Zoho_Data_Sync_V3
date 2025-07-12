#!/usr/bin/env python3
"""
Resolve the 151k enhanced records mystery
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 RESOLVING THE 151K 'ENHANCED' MYSTERY")
print("=" * 50)

# Let's trace exactly how view_csv_json_bills gets to 154k records
print("📋 TRACING THE DATA FLOW:")

# Check if the join is actually different
cursor.execute("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(CASE WHEN flat.bill_id IS NOT NULL THEN 1 END) as with_flat_data,
        COUNT(CASE WHEN flat.bill_id IS NULL THEN 1 END) as csv_only,
        COUNT(DISTINCT csv.bill_id) as unique_csv_bills,
        COUNT(DISTINCT flat.bill_id) as unique_flat_bills
    FROM csv_bills csv
    LEFT JOIN view_flat_json_bills flat ON csv.bill_id = flat.bill_id
""")
result = cursor.fetchone()
total, with_flat, csv_only, unique_csv, unique_flat = result

print(f"   Total rows from LEFT JOIN: {total:,}")
print(f"   Rows with flat data: {with_flat:,}")
print(f"   CSV-only rows: {csv_only:,}")
print(f"   Unique CSV bills: {unique_csv:,}")
print(f"   Unique flat bills: {unique_flat or 0:,}")
print()

# Check what's in view_flat_json_bills
cursor.execute("SELECT COUNT(*), COUNT(DISTINCT bill_id) FROM view_flat_json_bills")
flat_total, flat_unique = cursor.fetchone()
print(f"📊 view_flat_json_bills breakdown:")
print(f"   Total records: {flat_total:,}")
print(f"   Unique bill_ids: {flat_unique:,}")
print(f"   Average line items per bill: {flat_total/flat_unique:.1f}")
print()

# Now let's see what bill_ids are actually in both
cursor.execute("""
    SELECT DISTINCT csv.bill_id 
    FROM csv_bills csv 
    INNER JOIN view_flat_json_bills flat ON csv.bill_id = flat.bill_id
    LIMIT 5
""")
matching_bills = cursor.fetchall()
print(f"🔗 Sample bills that DO match:")
for bill in matching_bills:
    print(f"   {bill[0]}")

if not matching_bills:
    print("   ❌ NO MATCHING BILLS FOUND")
    
    # Check the actual bill_id values
    cursor.execute("SELECT DISTINCT bill_id FROM csv_bills WHERE bill_id IS NOT NULL LIMIT 5")
    csv_ids = cursor.fetchall()
    print(f"   Sample CSV bill_ids: {[x[0] for x in csv_ids]}")
    
    cursor.execute("SELECT DISTINCT bill_id FROM view_flat_json_bills WHERE bill_id IS NOT NULL LIMIT 5")
    flat_ids = cursor.fetchall()
    print(f"   Sample flat bill_ids: {[x[0] for x in flat_ids]}")

# Check the actual view logic
cursor.execute("""
    SELECT 
        CASE 
            WHEN flat.bill_id IS NOT NULL THEN 'enhanced'
            ELSE 'csv_only'
        END as data_source,
        COUNT(*) as count
    FROM csv_bills csv
    LEFT JOIN view_flat_json_bills flat ON csv.bill_id = flat.bill_id
    GROUP BY 1
""")
manual_distribution = dict(cursor.fetchall())
print(f"\n🔧 MANUAL JOIN RESULT:")
for source, count in manual_distribution.items():
    print(f"   {source}: {count:,}")

# Compare with actual view
cursor.execute("SELECT data_source, COUNT(*) FROM view_csv_json_bills GROUP BY data_source")
view_distribution = dict(cursor.fetchall())
print(f"\n📊 ACTUAL VIEW RESULT:")
for source, count in view_distribution.items():
    print(f"   {source}: {count:,}")

print(f"\n💡 IF THEY DON'T MATCH:")
print("The view might be using a different join condition or logic")
print("than what we're testing manually!")

conn.close()
