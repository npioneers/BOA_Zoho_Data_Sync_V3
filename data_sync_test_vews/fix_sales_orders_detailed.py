#!/usr/bin/env python3
"""
Targeted fix for sales orders view
"""
import sqlite3
import os

def fix_sales_orders_detailed():
    """Detailed fix for sales orders view"""
    db_path = os.path.join("..", "data", "database", "production.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Detailed Sales Orders Investigation")
    print("="*40)
    
    # Check CSV sales orders data more thoroughly
    cursor.execute("""
        SELECT customer_name, COUNT(*) as count,
               COUNT(CASE WHEN sales_order_number IS NOT NULL THEN 1 END) as with_number,
               COUNT(CASE WHEN sales_order_id IS NOT NULL THEN 1 END) as with_id
        FROM csv_sales_orders 
        GROUP BY customer_name 
        ORDER BY count DESC 
        LIMIT 10
    """)
    
    print("📊 CSV Sales Orders by Customer:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} total, {row[2]} with_number, {row[3]} with_id")
    
    # Check JSON sales orders  
    cursor.execute("SELECT COUNT(*) FROM json_sales_orders")
    json_count = cursor.fetchone()[0]
    print(f"\n📊 JSON Sales Orders: {json_count} rows")
    
    if json_count > 0:
        cursor.execute("SELECT customer_name, sales_order_number FROM json_sales_orders LIMIT 5")
        print("📊 Sample JSON sales orders:")
        for row in cursor.fetchall():
            print(f"  customer: {row[0]}, number: {row[1]}")
    
    # Get current view definition
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type = 'view' AND name = 'FINAL_view_csv_json_sales_orders'
    """)
    
    current_sql = cursor.fetchone()[0]
    print(f"\n📋 Current WHERE clause analysis:")
    
    # Find all WHERE conditions
    where_start = current_sql.upper().find('WHERE')
    if where_start != -1:
        where_clause = current_sql[where_start:where_start+200]
        print(f"WHERE clause: {where_clause}")
    
    # Create a more permissive WHERE clause
    print("\n🔧 Creating more permissive WHERE clause...")
    
    # Replace with a much more permissive condition
    new_sql = current_sql.replace(
        "WHERE csv.sales_order_id IS NOT NULL",
        "WHERE csv.customer_name IS NOT NULL"
    )
    
    # Also handle other potential WHERE patterns
    if "WHERE " in new_sql and "csv.sales_order_id" in new_sql:
        # More aggressive replacement
        lines = new_sql.split('\n')
        new_lines = []
        for line in lines:
            if 'WHERE' in line and 'csv.sales_order_id IS NOT NULL' in line:
                new_lines.append(line.replace('csv.sales_order_id IS NOT NULL', 'csv.customer_name IS NOT NULL'))
            else:
                new_lines.append(line)
        new_sql = '\n'.join(new_lines)
    
    print("🔄 Applying new view definition...")
    
    try:
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        cursor.execute(new_sql)
        conn.commit()
        
        # Test
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
        count = cursor.fetchone()[0]
        print(f"✅ New count: {count}")
        
        if count > 0:
            # Show sample
            cursor.execute("SELECT customer_name, data_source FROM FINAL_view_csv_json_sales_orders LIMIT 5")
            print("📊 Sample results:")
            for row in cursor.fetchall():
                print(f"  {row[0]} ({row[1]})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # If that fails, try even more basic approach
        print("🔧 Trying basic approach...")
        
        basic_sql = f"""
        CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT 
            csv.*,
            'CSV' as data_source,
            1 as source_priority
        FROM csv_sales_orders csv
        WHERE csv.customer_name IS NOT NULL
        
        UNION ALL
        
        SELECT 
            json.*,
            'JSON' as data_source,
            2 as source_priority  
        FROM json_sales_orders json
        WHERE json.customer_name IS NOT NULL
        """
        
        try:
            cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
            cursor.execute(basic_sql)
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
            count = cursor.fetchone()[0]
            print(f"✅ Basic approach count: {count}")
            
        except Exception as e2:
            print(f"❌ Basic approach also failed: {e2}")
    
    conn.close()

if __name__ == "__main__":
    fix_sales_orders_detailed()
