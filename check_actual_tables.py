#!/usr/bin/env python3
"""
Check what tables exist in the database
"""
import sqlite3

def check_tables():
    """Check what tables exist in the database"""
    
    conn = sqlite3.connect("production.db")
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=== ALL TABLES IN DATABASE ===")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")
    
    # Check specifically for csv_ tables
    csv_tables = [t for t in tables if t.startswith('csv_')]
    
    if csv_tables:
        print(f"\n=== CSV TABLES ({len(csv_tables)} found) ===")
        for table in csv_tables:
            print(f"\n📋 {table}")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Look for ID columns
            id_columns = [col for col in columns if 'id' in col[1].lower()]
            
            if id_columns:
                print("   ID Columns:")
                for col in id_columns:
                    col_name, data_type = col[1], col[2]
                    print(f"     {col_name}: {data_type}")
                    
                    # Check actual data
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NOT NULL AND {col_name} != ''")
                    populated = cursor.fetchone()[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    total = cursor.fetchone()[0]
                    print(f"       Populated: {populated}/{total} ({100*populated/total if total > 0 else 0:.1f}%)")
                    
                    if populated > 0:
                        cursor.execute(f"SELECT {col_name} FROM {table} WHERE {col_name} IS NOT NULL AND {col_name} != '' LIMIT 3")
                        samples = cursor.fetchall()
                        print(f"       Samples: {[row[0] for row in samples]}")
    else:
        print("\n❌ No csv_ tables found!")
    
    conn.close()

if __name__ == "__main__":
    check_tables()
