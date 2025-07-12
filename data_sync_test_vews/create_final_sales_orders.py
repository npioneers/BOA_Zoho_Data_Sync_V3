#!/usr/bin/env python3
"""
Create proper FINAL sales orders view with column mapping
"""
import sqlite3
import os

def create_proper_sales_orders_view():
    db_path = os.path.join("..", "data", "database", "production.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Creating Proper FINAL Sales Orders View")
    print("="*45)
    
    # Create view with mapped columns from both sources
    mapped_view = """
    CREATE VIEW FINAL_view_csv_json_sales_orders AS
    SELECT 
        -- Common identification fields
        csv.customer_name,
        csv.customer_id,
        csv.sales_order_id,
        csv.sales_order_number,
        csv.order_date,
        csv.status,
        csv.expected_shipment_date,
        
        -- Source tracking
        'CSV' as data_source,
        1 as source_priority,
        
        -- Timestamps
        csv.created_timestamp,
        csv.updated_timestamp,
        
        -- Additional CSV fields
        csv.custom_status,
        csv.created_timestamp as sync_timestamp
        
    FROM csv_sales_orders csv
    WHERE csv.customer_name IS NOT NULL AND csv.customer_name != ''
    
    UNION ALL
    
    SELECT 
        -- Map JSON fields to common structure
        json.customer_name,
        CAST(json.customer_id AS TEXT) as customer_id,
        CAST(json.salesorder_id AS TEXT) as sales_order_id,
        NULL as sales_order_number,  -- JSON doesn't have this field
        json.delivery_date as order_date,
        json.current_sub_status_id as status,
        json.delivery_date as expected_shipment_date,
        
        -- Source tracking  
        'JSON' as data_source,
        2 as source_priority,
        
        -- Timestamps (JSON doesn't have these, use NULL)
        NULL as created_timestamp,
        NULL as updated_timestamp,
        
        -- Additional fields
        NULL as custom_status,
        datetime('now') as sync_timestamp
        
    FROM json_sales_orders json
    WHERE json.customer_name IS NOT NULL AND json.customer_name != ''
    """
    
    try:
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        cursor.execute(mapped_view)
        conn.commit()
        
        # Test the new view
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT data_source, COUNT(*) FROM FINAL_view_csv_json_sales_orders GROUP BY data_source")
        source_counts = cursor.fetchall()
        
        print(f"✅ FINAL_view_csv_json_sales_orders created successfully!")
        print(f"📈 Total rows: {total_count:,}")
        print("📊 By source:")
        for source, count in source_counts:
            print(f"  - {source}: {count:,} rows")
        
        # Show sample data
        cursor.execute("""
            SELECT customer_name, sales_order_id, data_source, order_date 
            FROM FINAL_view_csv_json_sales_orders 
            LIMIT 10
        """)
        
        print("\n📋 Sample data:")
        for row in cursor.fetchall():
            print(f"  {row[0]} | ID: {row[1]} | Source: {row[2]} | Date: {row[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating view: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_proper_sales_orders_view()
