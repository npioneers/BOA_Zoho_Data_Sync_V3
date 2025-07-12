import sqlite3
from pathlib import Path

db_path = Path('data/database/production.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("🔍 Checking existing tables in database...")
print("=" * 80)

# Get all JSON table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%' ORDER BY name")
json_tables = cursor.fetchall()

print(f"📊 JSON tables in database ({len(json_tables)} total):")
for table, in json_tables:
    print(f"  ✅ {table}")

print("\n" + "=" * 80)
print("🔍 Line item tables specifically:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%line_items' ORDER BY name")
line_item_tables = cursor.fetchall()
for table, in line_item_tables:
    print(f"  ✅ {table}")

print(f"\n📈 Line item tables count: {len(line_item_tables)}")

print("\n" + "=" * 80)
print("🔍 Tables the populator tried vs what exists:")

# Tables the populator tried to populate (from the error log)
attempted_tables = [
    'json_invoices',
    'json_invoices_line_items', 
    'json_items',
    'json_contacts',
    'json_customerpayments',  # Failed
    'json_bills',
    'json_bills_line_items',
    'json_vendorpayments',    # Failed
    'json_salesorders',       # Failed
    'json_salesorders_line_items',
    'json_creditnotes',       # Failed
    'json_creditnotes_line_items'
]

existing_table_names = [t[0] for t in json_tables]

print()
for attempted in attempted_tables:
    if attempted in existing_table_names:
        print(f"  ✅ {attempted} - EXISTS")
    else:
        print(f"  ❌ {attempted} - MISSING")

print("\n" + "=" * 80)
print("🔍 Looking for name variations...")

missing_tables = [t for t in attempted_tables if t not in existing_table_names]
for missing in missing_tables:
    print(f"\n❌ Missing: {missing}")
    # Look for similar names
    base_name = missing.replace('json_', '')
    
    similar = []
    for existing in existing_table_names:
        if base_name in existing or existing.replace('json_', '') in base_name:
            similar.append(existing)
    
    if similar:
        print(f"   🔍 Similar tables found: {similar}")
    else:
        print(f"   🚫 No similar tables found")

conn.close()
