#!/usr/bin/env python3
"""
Quick sales orders structure check and fix
"""
import sqlite3
import os

def check_and_fix_sales_orders():
    db_path = os.path.join("..", "data", "database", "production.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Sales Orders Structure Analysis")
    print("="*40)
    
    # Check JSON sales orders structure
    cursor.execute("PRAGMA table_info(json_sales_orders)")
    json_columns = cursor.fetchall()
    print("📊 JSON Sales Orders columns:")
    for col in json_columns[:10]:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check CSV sales orders structure  
    cursor.execute("PRAGMA table_info(csv_sales_orders)")
    csv_columns = cursor.fetchall()
    print("\n📊 CSV Sales Orders columns:")
    for col in csv_columns[:10]:
        print(f"  - {col[1]} ({col[2]})")
    
    # Sample JSON data
    json_col_names = [col[1] for col in json_columns]
    if 'customer_name' in json_col_names:
        cursor.execute("SELECT customer_name FROM json_sales_orders LIMIT 5")
        print("\n📊 Sample JSON customer names:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}")
    
    # Create a simple working view
    print("\n🔧 Creating simple working view...")
    
    try:
        simple_view = """
        CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT 
            *,
            'CSV' as data_source,
            1 as source_priority
        FROM csv_sales_orders
        WHERE customer_name IS NOT NULL AND customer_name != ''
        
        UNION ALL
        
        SELECT 
            *,
            'JSON' as data_source,
            2 as source_priority  
        FROM json_sales_orders
        WHERE customer_name IS NOT NULL AND customer_name != ''
        """
        
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        cursor.execute(simple_view)
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
        count = cursor.fetchone()[0]
        print(f"✅ Simple view created with {count} rows")
        
        if count > 0:
            cursor.execute("SELECT customer_name, data_source FROM FINAL_view_csv_json_sales_orders LIMIT 5")
            print("📊 Sample results:")
            for row in cursor.fetchall():
                print(f"  {row[0]} ({row[1]})")
        
    except Exception as e:
        print(f"❌ Union failed (likely different schemas): {e}")
        
        # Try CSV only
        print("🔧 Trying CSV-only view...")
        try:
            csv_only_view = """
            CREATE VIEW FINAL_view_csv_json_sales_orders AS
            SELECT 
                *,
                'CSV' as data_source,
                1 as source_priority
            FROM csv_sales_orders
            WHERE customer_name IS NOT NULL AND customer_name != ''
            """
            
            cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
            cursor.execute(csv_only_view)
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
            count = cursor.fetchone()[0]
            print(f"✅ CSV-only view created with {count} rows")
            
        except Exception as e2:
            print(f"❌ Even CSV-only failed: {e2}")
    
    conn.close()

if __name__ == "__main__":
    check_and_fix_sales_orders()
