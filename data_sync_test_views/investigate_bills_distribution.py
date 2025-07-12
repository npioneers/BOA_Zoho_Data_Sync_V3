#!/usr/bin/env python3
"""
Investigate FINAL_view_csv_json_bills Distribution
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 INVESTIGATING FINAL_view_csv_json_bills")
print("=" * 60)

# Check the current view distribution
print("📊 CURRENT DISTRIBUTION:")
cursor.execute("SELECT data_source, COUNT(*) FROM FINAL_view_csv_json_bills GROUP BY data_source")
distribution = dict(cursor.fetchall())
for source, count in distribution.items():
    print(f"   {source}: {count:,}")

total = sum(distribution.values())
print(f"   TOTAL: {total:,}")
print()

# Check base table counts
print("📋 BASE TABLE COUNTS:")
cursor.execute("SELECT COUNT(*) FROM csv_bills")
csv_count = cursor.fetchone()[0]
print(f"   csv_bills: {csv_count:,}")

cursor.execute("SELECT COUNT(*) FROM json_bills")
json_count = cursor.fetchone()[0]
print(f"   json_bills: {json_count:,}")
print()

# Check for overlap
print("🔗 OVERLAP ANALYSIS:")
cursor.execute("""
    SELECT COUNT(*) as overlap_count
    FROM csv_bills csv
    INNER JOIN json_bills json ON csv.bill_id = json.bill_id
""")
overlap = cursor.fetchone()[0]
print(f"   Overlapping bill_ids: {overlap:,}")

# Calculate expected distribution
csv_only = csv_count - overlap
json_only = json_count - overlap
print(f"   Expected CSV_ONLY: {csv_only:,}")
print(f"   Expected JSON_ONLY: {json_only:,}")
print(f"   Expected OVERLAP (could be either): {overlap:,}")
print()

# Check actual view logic
print("🔧 CURRENT VIEW LOGIC:")
cursor.execute("SELECT sql FROM sqlite_master WHERE name = 'FINAL_view_csv_json_bills'")
view_sql = cursor.fetchone()[0]
print("View SQL:")
print(view_sql[:500] + "..." if len(view_sql) > 500 else view_sql)
print()

# Sample some records to see the pattern
print("📝 SAMPLE RECORDS (first 5):")
cursor.execute("""
    SELECT bill_id, data_source, 
           SUBSTR(bill_number, 1, 20) as bill_number_sample
    FROM FINAL_view_csv_json_bills 
    LIMIT 5
""")
samples = cursor.fetchall()
for sample in samples:
    print(f"   {sample}")

conn.close()

print("\n🤔 ANALYSIS:")
print("If most records show JSON precedence, possible causes:")
print("1. View uses JSON-priority COALESCE: COALESCE(json.field, csv.field)")
print("2. Most overlapping records have JSON data, making JSON 'win'") 
print("3. View logic incorrectly labels overlapping records as 'json'")
print("4. CSV data quality issues causing JSON to be preferred")
