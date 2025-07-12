#!/usr/bin/env python3
"""
Check Existing View Definitions
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing view definitions
views = ['view_csv_json_customer_payments', 'view_csv_json_sales_orders', 'view_csv_json_vendor_payments']
for view in views:
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='view' AND name='{view}'")
    result = cursor.fetchone()
    if result:
        print(f"{view}:")
        sql = result[0]
        print(sql[:500] + "..." if len(sql) > 500 else sql)
        print("\n" + "="*80 + "\n")

conn.close()
