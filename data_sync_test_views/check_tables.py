#!/usr/bin/env python3
"""
Check Table Structures
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all JSON tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%'")
json_tables = [row[0] for row in cursor.fetchall()]

print("JSON tables available:")
for table in json_tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count:,} records")

# Check specific tables we need
target_tables = ['json_customer_payments', 'json_sales_orders', 'json_vendor_payments']
for table in target_tables:
    if table in json_tables:
        print(f"\n{table} columns:")
        cursor.execute(f"PRAGMA table_info({table})")
        for row in cursor.fetchall():
            col_name = row[1]
            if any(word in col_name.lower() for word in ['id', 'payment', 'order']):
                print(f"  🔑 {col_name}")
    else:
        print(f"\n❌ {table} does not exist")

conn.close()
