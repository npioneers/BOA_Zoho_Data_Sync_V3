import sqlite3
import pandas as pd

def deep_sales_order_investigation():
    """
    Deep investigation and fix for sales order data integrity issues:
    1. Analyze field mapping errors in integration view
    2. Search for missing sales orders in correct fields
    3. Check invoice references with proper field names
    4. Propose and implement fixes
    """
    
    # Connect to database
    conn = sqlite3.connect('../data/database/production.db')
    
    print("🔍 DEEP SALES ORDER INVESTIGATION & FIX")
    print("=" * 60)
    
    # 1. Examine current view definition
    print("\n📊 1. CURRENT VIEW DEFINITION ANALYSIS:")
    print("-" * 50)
    
    try:
        view_def = conn.execute("""
        SELECT sql 
        FROM sqlite_master 
        WHERE type='view' AND name='view_csv_json_sales_orders'
        """).fetchone()
        
        if view_def:
            print(f"📋 Current Integration View Definition:")
            print(view_def[0])
            print()
        else:
            print("❌ Could not retrieve view definition")
    except Exception as e:
        print(f"❌ Error retrieving view definition: {e}")
    
    # 2. Analyze field populations in base tables
    print("\n📊 2. BASE TABLE FIELD POPULATION ANALYSIS:")
    print("-" * 50)
    
    # CSV table analysis
    try:
        csv_analysis = conn.execute("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN sales_order_number IS NOT NULL AND sales_order_number != '' AND sales_order_number != 'None' THEN 1 ELSE 0 END) as sales_order_number_populated,
            SUM(CASE WHEN sales_order_id IS NOT NULL AND sales_order_id != '' THEN 1 ELSE 0 END) as sales_order_id_populated
        FROM csv_sales_orders
        """).fetchone()
        
        print(f"📋 CSV Sales Orders Field Analysis:")
        print(f"  Total records: {csv_analysis[0]}")
        print(f"  sales_order_number populated: {csv_analysis[1]} ({csv_analysis[1]/csv_analysis[0]*100:.1f}%)")
        print(f"  sales_order_id populated: {csv_analysis[2]} ({csv_analysis[2]/csv_analysis[0]*100:.1f}%)")
        
        # Sample CSV data with actual field
        csv_sample = conn.execute("""
        SELECT sales_order_id, sales_order_number, status, customer_name
        FROM csv_sales_orders 
        WHERE sales_order_number IS NOT NULL AND sales_order_number != '' AND sales_order_number != 'None'
        LIMIT 10
        """).fetchall()
        
        print(f"\n📋 CSV Sample Data (sales_order_number populated):")
        for row in csv_sample:
            print(f"  ID: '{row[0]}' | sales_order_number: '{row[1]}' | status: '{row[2]}' | customer: '{row[3]}'")
            
    except Exception as e:
        print(f"❌ Error analyzing CSV fields: {e}")
    
    # JSON table analysis
    try:
        json_analysis = conn.execute("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN salesorder_number IS NOT NULL AND salesorder_number != '' THEN 1 ELSE 0 END) as salesorder_number_populated,
            SUM(CASE WHEN salesorder_id IS NOT NULL THEN 1 ELSE 0 END) as salesorder_id_populated
        FROM json_sales_orders
        """).fetchone()
        
        print(f"\n📋 JSON Sales Orders Field Analysis:")
        print(f"  Total records: {json_analysis[0]}")
        print(f"  salesorder_number populated: {json_analysis[1]} ({json_analysis[1]/json_analysis[0]*100:.1f}%)")
        print(f"  salesorder_id populated: {json_analysis[2]} ({json_analysis[2]/json_analysis[0]*100:.1f}%)")
        
        # Sample JSON data
        json_sample = conn.execute("""
        SELECT salesorder_id, salesorder_number, status, customer_name
        FROM json_sales_orders 
        WHERE salesorder_number IS NOT NULL AND salesorder_number != ''
        LIMIT 10
        """).fetchall()
        
        print(f"\n📋 JSON Sample Data:")
        for row in json_sample:
            print(f"  ID: '{row[0]}' | salesorder_number: '{row[1]}' | status: '{row[2]}' | customer: '{row[3]}'")
            
    except Exception as e:
        print(f"❌ Error analyzing JSON fields: {e}")
    
    # 3. Search for specific missing sales orders in correct fields
    print("\n📊 3. MISSING SALES ORDERS COMPREHENSIVE SEARCH:")
    print("-" * 50)
    
    missing_orders = ["SO-00572", "SO/25-26/00793"]
    
    for order_num in missing_orders:
        print(f"\n🔍 Comprehensive search for '{order_num}':")
        
        # Search CSV with correct field name
        try:
            csv_matches = conn.execute("""
            SELECT sales_order_id, sales_order_number, status, customer_name
            FROM csv_sales_orders 
            WHERE sales_order_number LIKE ? OR sales_order_id LIKE ?
            """, (f"%{order_num}%", f"%{order_num}%")).fetchall()
            
            print(f"  📋 CSV matches: {len(csv_matches)}")
            for match in csv_matches:
                print(f"    - ID: '{match[0]}' | sales_order_number: '{match[1]}' | status: '{match[2]}' | customer: '{match[3]}'")
        except Exception as e:
            print(f"  ❌ CSV search error: {e}")
        
        # Search JSON with correct field name
        try:
            json_matches = conn.execute("""
            SELECT salesorder_id, salesorder_number, status, customer_name
            FROM json_sales_orders 
            WHERE salesorder_number LIKE ? OR salesorder_id LIKE ?
            """, (f"%{order_num}%", f"%{order_num}%")).fetchall()
            
            print(f"  📋 JSON matches: {len(json_matches)}")
            for match in json_matches:
                print(f"    - ID: '{match[0]}' | salesorder_number: '{match[1]}' | status: '{match[2]}' | customer: '{match[3]}'")
        except Exception as e:
            print(f"  ❌ JSON search error: {e}")
    
    # 4. Check invoice references with proper field handling
    print("\n📊 4. INVOICE REFERENCES TO SALES ORDERS:")
    print("-" * 50)
    
    try:
        # First check what field names exist in invoice tables
        invoice_columns = conn.execute("PRAGMA table_info(FINAL_view_csv_json_invoices)").fetchall()
        so_ref_fields = [col[1] for col in invoice_columns if 'sales' in col[1].lower() and 'order' in col[1].lower()]
        
        print(f"📋 Sales order reference fields in invoices: {so_ref_fields}")
        
        if so_ref_fields:
            # Use the first sales order reference field found
            so_field = so_ref_fields[0]
            
            # Check missing orders in invoices
            for order_num in missing_orders:
                invoice_refs = conn.execute(f"""
                SELECT COUNT(*), invoice_number, {so_field}
                FROM FINAL_view_csv_json_invoices 
                WHERE {so_field} LIKE ?
                GROUP BY invoice_number, {so_field}
                """, (f"%{order_num}%",)).fetchall()
                
                print(f"\n🔍 '{order_num}' referenced in {len(invoice_refs)} invoice records:")
                for ref in invoice_refs:
                    print(f"  Invoice: {ref[1]} | SO Reference: '{ref[2]}' | Count: {ref[0]}")
                    
            # Show top sales order references in invoices
            top_so_refs = conn.execute(f"""
            SELECT {so_field}, COUNT(*) as invoice_count
            FROM FINAL_view_csv_json_invoices 
            WHERE {so_field} IS NOT NULL AND {so_field} != '' AND {so_field} != 'None'
            GROUP BY {so_field}
            ORDER BY invoice_count DESC
            LIMIT 10
            """).fetchall()
            
            print(f"\n📋 Top Sales Orders Referenced in Invoices:")
            for ref in top_so_refs:
                print(f"  {ref[0]}: {ref[1]} invoices")
                
    except Exception as e:
        print(f"❌ Error checking invoice references: {e}")
    
    # 5. Analyze integration view field mapping
    print("\n📊 5. INTEGRATION VIEW FIELD MAPPING ANALYSIS:")
    print("-" * 50)
    
    try:
        # Check how fields are being mapped in the view
        view_sample = conn.execute("""
        SELECT 
            sales_order_number,
            salesorder_number, 
            data_source,
            COUNT(*) as count
        FROM view_csv_json_sales_orders
        GROUP BY sales_order_number, salesorder_number, data_source
        ORDER BY count DESC
        LIMIT 20
        """).fetchall()
        
        print(f"📋 Integration View Field Mapping Patterns:")
        for row in view_sample:
            print(f"  sales_order_number: '{row[0]}' | salesorder_number: '{row[1]}' | source: '{row[2]}' | count: {row[3]}")
        
        # Check for any non-None values
        non_none_count = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN sales_order_number IS NOT NULL AND sales_order_number != 'None' AND sales_order_number != '' THEN 1 ELSE 0 END) as sales_order_number_populated,
            SUM(CASE WHEN salesorder_number IS NOT NULL AND salesorder_number != 'None' AND salesorder_number != '' THEN 1 ELSE 0 END) as salesorder_number_populated
        FROM view_csv_json_sales_orders
        """).fetchone()
        
        print(f"\n📋 Integration View Field Population:")
        print(f"  Total records: {non_none_count[0]}")
        print(f"  sales_order_number populated: {non_none_count[1]}")
        print(f"  salesorder_number populated: {non_none_count[2]}")
        
    except Exception as e:
        print(f"❌ Error analyzing integration view: {e}")
    
    # 6. Check FINAL view as well
    print("\n📊 6. FINAL VIEW FIELD MAPPING ANALYSIS:")
    print("-" * 50)
    
    try:
        final_view_sample = conn.execute("""
        SELECT 
            sales_order_number,
            salesorder_number, 
            data_source,
            COUNT(*) as count
        FROM FINAL_view_csv_json_sales_orders
        GROUP BY sales_order_number, salesorder_number, data_source
        ORDER BY count DESC
        LIMIT 20
        """).fetchall()
        
        print(f"📋 FINAL View Field Mapping Patterns:")
        for row in final_view_sample:
            print(f"  sales_order_number: '{row[0]}' | salesorder_number: '{row[1]}' | source: '{row[2]}' | count: {row[3]}")
            
    except Exception as e:
        print(f"❌ Error analyzing FINAL view: {e}")
    
    conn.close()
    
    print("\n✅ Deep investigation complete!")
    print("📋 Ready to implement fixes for field mapping issues")

if __name__ == "__main__":
    deep_sales_order_investigation()
