#!/usr/bin/env python3
"""
Check all tables in the database
"""
import sqlite3

def check_all_tables():
    """Check all tables in the database"""
    
    conn = sqlite3.connect("production.db")
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"=== ALL TABLES IN DATABASE ({len(tables)} total) ===")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")
    
    # Check if database is empty
    if not tables:
        print("\n❌ Database is completely empty!")
    else:
        print(f"\n✅ Database has {len(tables)} tables with data")
    
    conn.close()

if __name__ == "__main__":
    check_all_tables()
