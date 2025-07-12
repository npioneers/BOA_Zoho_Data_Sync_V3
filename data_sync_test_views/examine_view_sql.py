#!/usr/bin/env python3
"""
Get the full view SQL to understand the complex logic
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 EXAMINING FULL VIEW SQL")
print("=" * 50)

# Get the full view SQL
cursor.execute("SELECT sql FROM sqlite_master WHERE name = 'view_csv_json_bills'")
view_sql = cursor.fetchone()[0]

print("📋 COMPLETE view_csv_json_bills SQL:")
print(view_sql)
print()

# Also check if there are multiple parts (UNION, etc.)
lines = view_sql.split('\n')
key_lines = [line.strip() for line in lines if any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'LEFT JOIN', 'UNION', 'WHERE', 'CASE WHEN'])]

print("🔍 KEY SQL COMPONENTS:")
for i, line in enumerate(key_lines):
    print(f"   {i+1:2d}. {line}")

conn.close()

print("\n💡 LIKELY EXPLANATION:")
print("The view probably uses UNION to combine:")
print("1. CSV records (labeled 'csv_only')")
print("2. CSV+JSON enriched records (labeled 'enhanced')")
print("This would explain the 151k records!")
