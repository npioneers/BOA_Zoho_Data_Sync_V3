import sqlite3
import pandas as pd

def investigate_sales_order_issues():
    """
    Investigate sales order data integrity issues:
    1. Field mismatch between sales_order_number and salesorder_number
    2. Missing sales orders referenced in invoices
    3. Data structure analysis
    """
    
    # Connect to database
    conn = sqlite3.connect('../production.db')
    
    print("🔍 SALES ORDER DATA INTEGRITY INVESTIGATION")
    print("=" * 60)
    
    # 1. Examine sales order table structures
    print("\n📊 1. TABLE STRUCTURE ANALYSIS:")
    print("-" * 40)
    
    # Check CSV sales orders structure
    csv_columns = conn.execute("PRAGMA table_info(csv_sales_orders)").fetchall()
    print(f"\n📋 CSV Sales Orders Table Structure:")
    for col in csv_columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check JSON sales orders structure  
    json_columns = conn.execute("PRAGMA table_info(json_sales_orders)").fetchall()
    print(f"\n📋 JSON Sales Orders Table Structure:")
    for col in json_columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # 2. Analyze field data distribution
    print("\n📊 2. FIELD DATA DISTRIBUTION ANALYSIS:")
    print("-" * 40)
    
    # Check integration view structure
    integration_view_query = """
    SELECT 
        sales_order_number,
        salesorder_number,
        data_source,
        COUNT(*) as count
    FROM FINAL_view_csv_json_sales_orders 
    GROUP BY sales_order_number, salesorder_number, data_source
    LIMIT 20
    """
    
    print(f"\n🔍 Sample Integration View Data:")
    result = conn.execute(integration_view_query).fetchall()
    for row in result:
        print(f"  sales_order_number: '{row[0]}' | salesorder_number: '{row[1]}' | source: {row[2]} | count: {row[3]}")
    
    # 3. Check for NULL/None patterns
    print("\n📊 3. NULL/NONE PATTERN ANALYSIS:")
    print("-" * 40)
    
    null_analysis_query = """
    SELECT 
        data_source,
        COUNT(*) as total_records,
        SUM(CASE WHEN sales_order_number IS NULL OR sales_order_number = 'None' THEN 1 ELSE 0 END) as sales_order_number_nulls,
        SUM(CASE WHEN salesorder_number IS NULL OR salesorder_number = 'None' THEN 1 ELSE 0 END) as salesorder_number_nulls,
        SUM(CASE WHEN sales_order_number IS NOT NULL AND sales_order_number != 'None' THEN 1 ELSE 0 END) as sales_order_number_populated,
        SUM(CASE WHEN salesorder_number IS NOT NULL AND salesorder_number != 'None' THEN 1 ELSE 0 END) as salesorder_number_populated
    FROM FINAL_view_csv_json_sales_orders 
    GROUP BY data_source
    """
    
    result = conn.execute(null_analysis_query).fetchall()
    for row in result:
        print(f"\n📋 {row[0].upper()} Source:")
        print(f"  Total records: {row[1]}")
        print(f"  sales_order_number nulls: {row[2]} | populated: {row[4]}")
        print(f"  salesorder_number nulls: {row[3]} | populated: {row[5]}")
    
    # 4. Search for specific missing sales orders
    print("\n📊 4. SPECIFIC MISSING SALES ORDERS SEARCH:")
    print("-" * 40)
    
    missing_orders = ["SO-00572", "SO/25-26/00793"]
    
    for order_num in missing_orders:
        print(f"\n🔍 Searching for '{order_num}':")
        
        # Search in CSV source
        csv_search = conn.execute("""
        SELECT COUNT(*) 
        FROM csv_sales_orders 
        WHERE sales_order_id LIKE ? OR sales_order_number LIKE ? OR salesorder_number LIKE ?
        """, (f"%{order_num}%", f"%{order_num}%", f"%{order_num}%")).fetchone()[0]
        
        # Search in JSON source
        json_search = conn.execute("""
        SELECT COUNT(*) 
        FROM json_sales_orders 
        WHERE salesorder_id LIKE ? OR salesorder_number LIKE ?
        """, (f"%{order_num}%", f"%{order_num}%")).fetchone()[0]
        
        # Search in integration view
        view_search = conn.execute("""
        SELECT COUNT(*) 
        FROM FINAL_view_csv_json_sales_orders 
        WHERE sales_order_id LIKE ? OR sales_order_number LIKE ? OR salesorder_number LIKE ?
        """, (f"%{order_num}%", f"%{order_num}%", f"%{order_num}%")).fetchone()[0]
        
        print(f"  CSV source: {csv_search} matches")
        print(f"  JSON source: {json_search} matches")
        print(f"  Integration view: {view_search} matches")
    
    # 5. Check invoice references to sales orders
    print("\n📊 5. INVOICE REFERENCES TO SALES ORDERS:")
    print("-" * 40)
    
    invoice_so_refs = conn.execute("""
    SELECT DISTINCT 
        salesorder_number,
        COUNT(*) as invoice_count
    FROM FINAL_view_csv_json_invoices 
    WHERE salesorder_number IS NOT NULL 
    AND salesorder_number != '' 
    AND salesorder_number != 'None'
    GROUP BY salesorder_number
    ORDER BY invoice_count DESC
    LIMIT 10
    """).fetchall()
    
    print(f"\n📋 Top Sales Orders Referenced in Invoices:")
    for row in invoice_so_refs:
        print(f"  {row[0]}: {row[1]} invoices")
    
    # Check if missing orders are in invoices
    for order_num in missing_orders:
        invoice_refs = conn.execute("""
        SELECT COUNT(*) 
        FROM FINAL_view_csv_json_invoices 
        WHERE salesorder_number LIKE ?
        """, (f"%{order_num}%",)).fetchone()[0]
        print(f"\n🔍 '{order_num}' referenced in {invoice_refs} invoices")
    
    # 6. Examine view definition
    print("\n📊 6. INTEGRATION VIEW DEFINITION ANALYSIS:")
    print("-" * 40)
    
    try:
        view_def = conn.execute("""
        SELECT sql 
        FROM sqlite_master 
        WHERE type='view' AND name='FINAL_view_csv_json_sales_orders'
        """).fetchone()
        
        if view_def:
            print(f"\n📋 Current View Definition:")
            print(view_def[0])
        else:
            print("\n❌ Could not retrieve view definition")
    except Exception as e:
        print(f"\n❌ Error retrieving view definition: {e}")
    
    # 7. Sample data from both sources
    print("\n📊 7. SAMPLE DATA FROM BOTH SOURCES:")
    print("-" * 40)
    
    print(f"\n📋 Sample CSV Sales Orders (first 5):")
    csv_sample = conn.execute("""
    SELECT sales_order_id, sales_order_number, salesorder_number, status
    FROM csv_sales_orders 
    LIMIT 5
    """).fetchall()
    
    for row in csv_sample:
        print(f"  ID: {row[0]} | sales_order_number: '{row[1]}' | salesorder_number: '{row[2]}' | status: {row[3]}")
    
    print(f"\n📋 Sample JSON Sales Orders (first 5):")
    json_sample = conn.execute("""
    SELECT salesorder_id, salesorder_number, status
    FROM json_sales_orders 
    LIMIT 5
    """).fetchall()
    
    for row in json_sample:
        print(f"  ID: {row[0]} | salesorder_number: '{row[1]}' | status: {row[2]}")
    
    conn.close()
    
    print("\n✅ Investigation complete!")
    print("Check COPILOT_SALES_ORDER_INVESTIGATION_NOTES.md for analysis summary")

if __name__ == "__main__":
    investigate_sales_order_issues()
