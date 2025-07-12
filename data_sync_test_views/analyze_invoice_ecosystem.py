#!/usr/bin/env python3
"""
Invoice Table Ecosystem Analysis
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== INVOICE TABLE ECOSYSTEM ANALYSIS ===")
print()

# Check base tables
tables = ['csv_invoices', 'json_invoices']
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"📊 {table}: {count:,} records")
    except Exception as e:
        print(f"❌ {table}: {e}")

print()

# Check invoice-related views
invoice_views = [
    'view_csv_json_invoices',
    'FINAL_view_csv_json_invoices', 
    'view_invoices_summary',
    'view_flat_json_invoices'
]

for view in invoice_views:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        count = cursor.fetchone()[0]
        print(f"📋 {view}: {count:,} records")
        
        # Try to get data source distribution
        try:
            cursor.execute(f"SELECT data_source, COUNT(*) FROM {view} GROUP BY data_source")
            dist = dict(cursor.fetchall())
            if dist:
                sources = ", ".join([f"{k}:{v:,}" for k, v in dist.items()])
                print(f"    Distribution: {sources}")
        except:
            pass
            
    except Exception as e:
        print(f"❌ {view}: {e}")

print()

# Check for any enhanced versions
enhanced_views = [
    'view_csv_json_invoices_v2',
    'view_csv_json_invoices_v3',
    'view_csv_json_invoices_deduplicated'
]

print("=== ENHANCED INVOICE VIEWS ===")
for view in enhanced_views:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        count = cursor.fetchone()[0]
        print(f"📋 {view}: {count:,} records")
    except:
        print(f"⚪ {view}: Does not exist")

conn.close()
