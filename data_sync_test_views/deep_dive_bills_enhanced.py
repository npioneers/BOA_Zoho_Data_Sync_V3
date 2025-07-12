#!/usr/bin/env python3
"""
Deep dive into bills "enhanced" vs "csv_only" distinction
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 DEEP DIVE: BILLS 'ENHANCED' LOGIC")
print("=" * 50)

# Look at the view_csv_json_bills SQL to understand "enhanced" vs "csv_only"
cursor.execute("SELECT sql FROM sqlite_master WHERE name = 'view_csv_json_bills'")
view_sql = cursor.fetchone()[0]
print("📋 view_csv_json_bills SQL (key parts):")
print(view_sql[:800] + "...")
print()

# Check the json_bills_line_items table - this might be the key!
print("🔗 INVESTIGATING json_bills_line_items:")
cursor.execute("SELECT COUNT(*) FROM json_bills_line_items")
line_items_count = cursor.fetchone()[0]
print(f"   json_bills_line_items: {line_items_count:,} records")

# Sample some line items
cursor.execute("SELECT bill_id, line_item_id, description FROM json_bills_line_items LIMIT 5")
samples = cursor.fetchall()
print("   Sample line items:")
for sample in samples:
    print(f"     {sample}")
print()

# Check if the "enhanced" records are actually line items being joined
print("🔍 ANALYZING 'enhanced' RECORDS:")
cursor.execute("""
    SELECT data_source, COUNT(*) as count,
           COUNT(DISTINCT bill_id) as unique_bills
    FROM view_csv_json_bills 
    GROUP BY data_source
""")
results = cursor.fetchall()
for source, count, unique_bills in results:
    print(f"   {source}: {count:,} records from {unique_bills:,} unique bills")
    if count > unique_bills:
        expansion_ratio = count / unique_bills
        print(f"     → {expansion_ratio:.1f}x expansion (likely line items)")

print()

# Check a specific bill to see the expansion
cursor.execute("""
    SELECT bill_id, data_source, 
           SUBSTR(COALESCE(description, bill_number), 1, 30) as description_sample
    FROM view_csv_json_bills 
    WHERE bill_id IS NOT NULL
    ORDER BY bill_id
    LIMIT 10
""")
samples = cursor.fetchall()
print("📝 SAMPLE EXPANDED RECORDS:")
for sample in samples:
    print(f"   {sample}")

conn.close()

print("\n💡 HYPOTHESIS:")
print("The 'enhanced' records likely represent line items from json_bills_line_items")
print("joined to CSV bill headers, creating massive expansion (151k from ~3k bills)")
print("This means JSON isn't 'winning' - it's adding detailed line items to CSV headers!")
