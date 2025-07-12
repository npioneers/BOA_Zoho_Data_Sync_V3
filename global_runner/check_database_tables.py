#!/usr/bin/env python3
"""
Check what tables actually exist in the database
"""
import sqlite3
from pathlib import Path

def check_database_tables():
    db_path = Path("../data/database/production.db")
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Database: {db_path}")
    print(f"Total tables: {len(tables)}")
    print("\nAll tables:")
    for i, table in enumerate(tables, 1):
        print(f"{i:2}. {table}")
    
    # Check for json_ prefixed tables
    json_tables = [t for t in tables if t.startswith('json_')]
    non_json_tables = [t for t in tables if not t.startswith('json_')]
    
    print(f"\nJSON tables ({len(json_tables)}):")
    for table in json_tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        count = cursor.fetchone()[0]
        cursor.execute(f"SELECT MAX(last_modified_time) FROM `{table}` WHERE last_modified_time IS NOT NULL")
        latest = cursor.fetchone()[0]
        print(f"  {table}: {count:,} records, latest: {latest}")
    
    print(f"\nNon-JSON tables ({len(non_json_tables)}):")
    for table in non_json_tables[:10]:  # Show first 10
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count:,} records")
    
    if len(non_json_tables) > 10:
        print(f"  ... and {len(non_json_tables) - 10} more tables")
    
    conn.close()

if __name__ == "__main__":
    check_database_tables()
