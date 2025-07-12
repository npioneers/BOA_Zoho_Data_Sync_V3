import sqlite3
import pandas as pd

def investigate_sales_order_issues():
    """
    Investigate sales order data integrity issues:
    1. Check what sales order views exist
    2. Field mismatch between sales_order_number and salesorder_number
    3. Missing sales orders referenced in invoices
    4. Data structure analysis
    """
    
    # Connect to database
    conn = sqlite3.connect('../data/database/production.db')
    
    print("🔍 SALES ORDER DATA INTEGRITY INVESTIGATION")
    print("=" * 60)
    
    # 0. First check what sales order views exist
    print("\n📊 0. EXISTING SALES ORDER VIEWS:")
    print("-" * 40)
    
    existing_views = conn.execute("""
    SELECT name 
    FROM sqlite_master 
    WHERE type='view' AND name LIKE '%sales%order%' 
    ORDER BY name
    """).fetchall()
    
    print(f"📋 Found {len(existing_views)} sales order views:")
    for view in existing_views:
        print(f"  - {view[0]}")
    
    # Check if we have the integration view
    integration_view_exists = any('view_csv_json_sales_orders' in view[0] for view in existing_views)
    final_view_exists = any('FINAL_view_csv_json_sales_orders' in view[0] for view in existing_views)
    
    print(f"\n📋 View Status:")
    print(f"  Integration view exists: {integration_view_exists}")
    print(f"  FINAL view exists: {final_view_exists}")
    
    # 1. Examine sales order table structures
    print("\n📊 1. TABLE STRUCTURE ANALYSIS:")
    print("-" * 40)
    
    # Check CSV sales orders structure
    try:
        csv_columns = conn.execute("PRAGMA table_info(csv_sales_orders)").fetchall()
        print(f"\n📋 CSV Sales Orders Table Structure ({len(csv_columns)} columns):")
        for col in csv_columns:
            print(f"  - {col[1]} ({col[2]})")
    except Exception as e:
        print(f"\n❌ Error accessing csv_sales_orders: {e}")
    
    # Check JSON sales orders structure  
    try:
        json_columns = conn.execute("PRAGMA table_info(json_sales_orders)").fetchall()
        print(f"\n📋 JSON Sales Orders Table Structure ({len(json_columns)} columns):")
        for col in json_columns:
            print(f"  - {col[1]} ({col[2]})")
    except Exception as e:
        print(f"\n❌ Error accessing json_sales_orders: {e}")
    
    # 2. Check base table data
    print("\n📊 2. BASE TABLE DATA ANALYSIS:")
    print("-" * 40)
    
    # CSV table data sample
    try:
        csv_count = conn.execute("SELECT COUNT(*) FROM csv_sales_orders").fetchone()[0]
        print(f"\n📋 CSV Sales Orders: {csv_count} records")
        
        csv_sample = conn.execute("""
        SELECT sales_order_id, sales_order_number, salesorder_number, status
        FROM csv_sales_orders 
        LIMIT 5
        """).fetchall()
        
        print(f"Sample CSV data:")
        for row in csv_sample:
            print(f"  ID: '{row[0]}' | sales_order_number: '{row[1]}' | salesorder_number: '{row[2]}' | status: '{row[3]}'")
    except Exception as e:
        print(f"\n❌ Error accessing CSV data: {e}")
    
    # JSON table data sample
    try:
        json_count = conn.execute("SELECT COUNT(*) FROM json_sales_orders").fetchone()[0]
        print(f"\n📋 JSON Sales Orders: {json_count} records")
        
        json_sample = conn.execute("""
        SELECT salesorder_id, salesorder_number, status
        FROM json_sales_orders 
        LIMIT 5
        """).fetchall()
        
        print(f"Sample JSON data:")
        for row in json_sample:
            print(f"  ID: '{row[0]}' | salesorder_number: '{row[1]}' | status: '{row[2]}'")
    except Exception as e:
        print(f"\n❌ Error accessing JSON data: {e}")
    
    # 3. Analyze field naming patterns
    print("\n📊 3. FIELD NAMING PATTERN ANALYSIS:")
    print("-" * 40)
    
    try:
        # Check CSV field patterns
        csv_fields = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN sales_order_number IS NOT NULL AND sales_order_number != '' AND sales_order_number != 'None' THEN 1 ELSE 0 END) as sales_order_number_populated,
            SUM(CASE WHEN salesorder_number IS NOT NULL AND salesorder_number != '' AND salesorder_number != 'None' THEN 1 ELSE 0 END) as salesorder_number_populated
        FROM csv_sales_orders
        """).fetchone()
        
        print(f"\n📋 CSV Field Population:")
        print(f"  Total records: {csv_fields[0]}")
        print(f"  sales_order_number populated: {csv_fields[1]}")
        print(f"  salesorder_number populated: {csv_fields[2]}")
        
        # Show sample of field values
        csv_field_sample = conn.execute("""
        SELECT sales_order_number, salesorder_number
        FROM csv_sales_orders 
        WHERE salesorder_number IS NOT NULL AND salesorder_number != ''
        LIMIT 10
        """).fetchall()
        
        print(f"\n📋 CSV Field Value Samples:")
        for row in csv_field_sample:
            print(f"  sales_order_number: '{row[0]}' | salesorder_number: '{row[1]}'")
            
    except Exception as e:
        print(f"\n❌ Error analyzing CSV fields: {e}")
    
    # 4. Search for specific missing sales orders in base tables
    print("\n📊 4. MISSING SALES ORDERS SEARCH IN BASE TABLES:")
    print("-" * 40)
    
    missing_orders = ["SO-00572", "SO/25-26/00793"]
    
    for order_num in missing_orders:
        print(f"\n🔍 Searching for '{order_num}':")
        
        try:
            # Search in CSV source (check all possible fields)
            csv_search = conn.execute("""
            SELECT sales_order_id, sales_order_number, salesorder_number
            FROM csv_sales_orders 
            WHERE sales_order_id LIKE ? OR sales_order_number LIKE ? OR salesorder_number LIKE ?
            """, (f"%{order_num}%", f"%{order_num}%", f"%{order_num}%")).fetchall()
            
            print(f"  CSV source: {len(csv_search)} matches")
            for match in csv_search:
                print(f"    - ID: '{match[0]}' | sales_order_number: '{match[1]}' | salesorder_number: '{match[2]}'")
        except Exception as e:
            print(f"  CSV search error: {e}")
        
        try:
            # Search in JSON source
            json_search = conn.execute("""
            SELECT salesorder_id, salesorder_number
            FROM json_sales_orders 
            WHERE salesorder_id LIKE ? OR salesorder_number LIKE ?
            """, (f"%{order_num}%", f"%{order_num}%")).fetchall()
            
            print(f"  JSON source: {len(json_search)} matches")
            for match in json_search:
                print(f"    - ID: '{match[0]}' | salesorder_number: '{match[1]}'")
        except Exception as e:
            print(f"  JSON search error: {e}")
    
    # 5. Check if integration view exists and analyze it
    print("\n📊 5. INTEGRATION VIEW ANALYSIS:")
    print("-" * 40)
    
    if integration_view_exists:
        try:
            view_name = 'view_csv_json_sales_orders'
            view_count = conn.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
            print(f"\n📋 {view_name}: {view_count} records")
            
            # Sample integration view data
            view_sample = conn.execute(f"""
            SELECT sales_order_number, salesorder_number, data_source
            FROM {view_name}
            LIMIT 10
            """).fetchall()
            
            print(f"Sample integration view data:")
            for row in view_sample:
                print(f"  sales_order_number: '{row[0]}' | salesorder_number: '{row[1]}' | source: '{row[2]}'")
                
        except Exception as e:
            print(f"\n❌ Error analyzing integration view: {e}")
    else:
        print(f"\n❌ Integration view does not exist!")
    
    # 6. Check invoice references to sales orders
    print("\n📊 6. INVOICE REFERENCES TO SALES ORDERS:")
    print("-" * 40)
    
    try:
        # Check if missing orders are in invoices
        for order_num in missing_orders:
            invoice_refs = conn.execute("""
            SELECT COUNT(*), invoice_number, salesorder_number
            FROM FINAL_view_csv_json_invoices 
            WHERE salesorder_number LIKE ?
            GROUP BY invoice_number, salesorder_number
            """, (f"%{order_num}%",)).fetchall()
            
            print(f"\n🔍 '{order_num}' referenced in {len(invoice_refs)} invoice records:")
            for ref in invoice_refs:
                print(f"  Invoice: {ref[1]} | SO Reference: '{ref[2]}' | Count: {ref[0]}")
                
    except Exception as e:
        print(f"\n❌ Error checking invoice references: {e}")
    
    conn.close()
    
    print("\n✅ Investigation complete!")
    print("📋 Next step: Create missing FINAL view and fix field mapping issues")

if __name__ == "__main__":
    investigate_sales_order_issues()
