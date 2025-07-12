#!/usr/bin/env python3
"""
Check Contacts Overlap
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("CONTACTS OVERLAP ANALYSIS")
print("=" * 40)

# Check overlap
cursor.execute("SELECT contact_id FROM csv_contacts INTERSECT SELECT contact_id FROM json_contacts")
overlap = cursor.fetchall()
print(f"Overlapping contacts: {len(overlap)}")

# Show current view logic
cursor.execute("SELECT data_source, COUNT(*) FROM view_csv_json_contacts GROUP BY data_source")
view_distribution = dict(cursor.fetchall())
print(f"View distribution: {view_distribution}")

if len(overlap) == 0:
    print("✅ No overlap means JSON_ONLY is correct behavior")
    print("📋 CSV-preferred only applies when there's overlap to choose from")
else:
    print(f"❓ {len(overlap)} overlapping records - should see CSV_PREFERRED")

conn.close()
