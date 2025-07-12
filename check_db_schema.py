#!/usr/bin/env python3
"""
Check database schema for ID fields
"""
import sqlite3

def check_database_schemas():
    """Check the schema for ID field definitions"""
    
    conn = sqlite3.connect("production.db")
    cursor = conn.cursor()
    
    # Get all csv_ tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=== DATABASE SCHEMA ANALYSIS ===")
    
    for table in tables:
        print(f"\n📋 TABLE: {table}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Look for ID columns
        id_columns = [col for col in columns if 'id' in col[1].lower()]
        
        if id_columns:
            print("   ID Columns:")
            for col in id_columns:
                col_name, data_type, not_null, default_val, primary_key = col[1], col[2], col[3], col[4], col[5]
                print(f"     {col_name}: {data_type} (NOT NULL: {bool(not_null)}, DEFAULT: {default_val})")
        else:
            print("   No ID columns found")
    
    conn.close()

def test_large_integer_insert():
    """Test if large integers can be inserted into the database"""
    
    print("\n" + "=" * 60)
    print("🧪 LARGE INTEGER INSERT TEST")
    print("=" * 60)
    
    conn = sqlite3.connect(":memory:")  # Use in-memory database for test
    cursor = conn.cursor()
    
    # Create a test table similar to our schema
    cursor.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            sales_order_id INTEGER,
            sales_order_id_text TEXT
        )
    """)
    
    # Test values from CSV
    test_values = [
        3990265000000897001,
        3990265000000910001,
        3990265000000912001
    ]
    
    for i, value in enumerate(test_values):
        print(f"\nTesting value: {value} (length: {len(str(value))})")
        
        try:
            # Try inserting as INTEGER
            cursor.execute("INSERT INTO test_table (id, sales_order_id, sales_order_id_text) VALUES (?, ?, ?)", 
                          (i+1, value, str(value)))
            
            # Check what was stored
            cursor.execute("SELECT sales_order_id, sales_order_id_text FROM test_table WHERE id = ?", (i+1,))
            result = cursor.fetchone()
            
            if result:
                stored_int, stored_text = result
                print(f"   Stored as INTEGER: {stored_int}")
                print(f"   Stored as TEXT: {stored_text}")
                print(f"   Values match: {str(stored_int) == str(value)}")
            
        except Exception as e:
            print(f"   ❌ Error inserting: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_database_schemas()
    test_large_integer_insert()
