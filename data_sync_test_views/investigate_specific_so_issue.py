import sqlite3

def investigate_specific_sales_order_issue():
    """
    Investigate the specific case of SO/25-26/00808 and the broader 
    NULL sales order number issue identified by the user
    """
    
    # Connect to database
    conn = sqlite3.connect('../data/database/production.db')
    
    print("🔍 INVESTIGATING SPECIFIC SALES ORDER ISSUE: SO/25-26/00808")
    print("=" * 70)
    
    # 1. Check for SO/25-26/00808 specifically
    print("\n📊 1. SEARCHING FOR SO/25-26/00808:")
    print("-" * 50)
    
    # Search in sales order views
    so_search = conn.execute("""
    SELECT unified_sales_order_number, sales_order_number, salesorder_number, 
           data_source, customer_name, status
    FROM FINAL_view_csv_json_sales_orders
    WHERE unified_sales_order_number LIKE '%SO/25-26/00808%' 
       OR sales_order_number LIKE '%SO/25-26/00808%'
       OR salesorder_number LIKE '%SO/25-26/00808%'
    """).fetchall()
    
    print(f"📋 Sales Order View Results: {len(so_search)} matches")
    for row in so_search:
        print(f"  Unified: '{row[0]}' | CSV: '{row[1]}' | JSON: '{row[2]}' | Source: {row[3]} | Customer: '{row[4]}' | Status: '{row[5]}'")
    
    # Search in invoice references
    invoice_search = conn.execute("""
    SELECT invoice_number, sales_order_number, customer_name, invoice_date, total
    FROM FINAL_view_csv_json_invoices
    WHERE sales_order_number LIKE '%SO/25-26/00808%'
    """).fetchall()
    
    print(f"\n📋 Invoice References: {len(invoice_search)} matches")
    for row in invoice_search:
        print(f"  Invoice: {row[0]} | SO Ref: '{row[1]}' | Customer: '{row[2]}' | Date: {row[3]} | Total: {row[4]}")
    
    # 2. Analyze NULL sales order number problem
    print("\n📊 2. NULL SALES ORDER NUMBER ANALYSIS:")
    print("-" * 50)
    
    null_analysis = conn.execute("""
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN unified_sales_order_number IS NOT NULL AND unified_sales_order_number != '' AND unified_sales_order_number != 'None' THEN 1 ELSE 0 END) as unified_populated,
        SUM(CASE WHEN sales_order_number IS NOT NULL AND sales_order_number != '' AND sales_order_number != 'None' THEN 1 ELSE 0 END) as csv_populated,
        SUM(CASE WHEN salesorder_number IS NOT NULL AND salesorder_number != '' AND salesorder_number != 'None' THEN 1 ELSE 0 END) as json_populated
    FROM FINAL_view_csv_json_sales_orders
    """).fetchone()
    
    print(f"📋 Sales Order Number Population:")
    print(f"  Total records: {null_analysis[0]}")
    print(f"  unified_sales_order_number populated: {null_analysis[1]} ({null_analysis[1]/null_analysis[0]*100:.1f}%)")
    print(f"  sales_order_number (CSV) populated: {null_analysis[2]} ({null_analysis[2]/null_analysis[0]*100:.1f}%)")
    print(f"  salesorder_number (JSON) populated: {null_analysis[3]} ({null_analysis[3]/null_analysis[0]*100:.1f}%)")
    
    # 3. Check Norlha Enterprise specifically
    print("\n📊 3. NORLHA ENTERPRISE SALES ORDER ANALYSIS:")
    print("-" * 50)
    
    norlha_search = conn.execute("""
    SELECT 
        unified_sales_order_number, 
        sales_order_number, 
        salesorder_number, 
        data_source, 
        status,
        COUNT(*) as frequency
    FROM FINAL_view_csv_json_sales_orders
    WHERE customer_name LIKE '%Norlha%'
    GROUP BY unified_sales_order_number, sales_order_number, salesorder_number, data_source, status
    ORDER BY frequency DESC
    """).fetchall()
    
    print(f"📋 Norlha Enterprise Records: {len(norlha_search)} unique combinations")
    for row in norlha_search:
        print(f"  Unified: '{row[0]}' | CSV: '{row[1]}' | JSON: '{row[2]}' | Source: {row[3]} | Status: '{row[4]}' | Count: {row[5]}")
    
    # 4. Check if SO/25-26/00808 might be in JSON data with different ID mapping
    print("\n📊 4. DEEP SEARCH IN BASE TABLES:")
    print("-" * 50)
    
    # Search CSV base table
    csv_search = conn.execute("""
    SELECT sales_order_id, sales_order_number, customer_name, status
    FROM csv_sales_orders
    WHERE sales_order_id LIKE '%808%' OR sales_order_number LIKE '%808%'
    """).fetchall()
    
    print(f"📋 CSV Base Table Search: {len(csv_search)} matches")
    for row in csv_search:
        print(f"  ID: '{row[0]}' | Number: '{row[1]}' | Customer: '{row[2]}' | Status: '{row[3]}'")
    
    # Search JSON base table
    json_search = conn.execute("""
    SELECT salesorder_id, salesorder_number, customer_name, status
    FROM json_sales_orders
    WHERE salesorder_id LIKE '%808%' OR salesorder_number LIKE '%808%'
    """).fetchall()
    
    print(f"📋 JSON Base Table Search: {len(json_search)} matches")
    for row in json_search:
        print(f"  ID: '{row[0]}' | Number: '{row[1]}' | Customer: '{row[2]}' | Status: '{row[3]}'")
    
    # 5. Check for pattern in missing sales orders from invoices
    print("\n📊 5. PATTERN ANALYSIS OF MISSING SALES ORDERS:")
    print("-" * 50)
    
    # Get all unique sales order references from invoices
    invoice_so_refs = conn.execute("""
    SELECT DISTINCT sales_order_number, COUNT(*) as invoice_count
    FROM FINAL_view_csv_json_invoices
    WHERE sales_order_number IS NOT NULL 
    AND sales_order_number != '' 
    AND sales_order_number != 'None'
    GROUP BY sales_order_number
    ORDER BY sales_order_number
    """).fetchall()
    
    print(f"📋 Total unique SO references in invoices: {len(invoice_so_refs)}")
    
    # Check how many of these exist in sales order views
    missing_count = 0
    sample_missing = []
    
    for so_ref, count in invoice_so_refs:
        exists_in_so = conn.execute("""
        SELECT COUNT(*) 
        FROM FINAL_view_csv_json_sales_orders
        WHERE unified_sales_order_number = ?
        """, (so_ref,)).fetchone()[0]
        
        if exists_in_so == 0:
            missing_count += 1
            if len(sample_missing) < 10:  # Collect sample
                sample_missing.append((so_ref, count))
    
    print(f"📋 Missing Sales Orders Analysis:")
    print(f"  Total SO references in invoices: {len(invoice_so_refs)}")
    print(f"  Missing from sales order views: {missing_count}")
    print(f"  Coverage rate: {(len(invoice_so_refs) - missing_count)/len(invoice_so_refs)*100:.1f}%")
    
    print(f"\n📋 Sample Missing Sales Orders:")
    for so_ref, count in sample_missing:
        print(f"  {so_ref}: referenced in {count} invoice line items")
    
    # 6. Check data source timestamps to understand the gap
    print("\n📊 6. DATA SOURCE TIMESTAMP ANALYSIS:")
    print("-" * 50)
    
    # Check latest data in each source
    csv_latest = conn.execute("""
    SELECT MAX(created_timestamp), MAX(updated_timestamp)
    FROM csv_sales_orders
    WHERE created_timestamp IS NOT NULL
    """).fetchone()
    
    json_latest = conn.execute("""
    SELECT MAX(created_time), MAX(last_modified_time)
    FROM json_sales_orders
    WHERE created_time IS NOT NULL
    """).fetchone()
    
    print(f"📋 Data Timestamps:")
    print(f"  CSV latest created: {csv_latest[0]} | updated: {csv_latest[1]}")
    print(f"  JSON latest created: {json_latest[0]} | modified: {json_latest[1]}")
    
    # Check if SO/25-26/00808 pattern suggests timing issue
    pattern_analysis = conn.execute("""
    SELECT sales_order_number, invoice_date, customer_name
    FROM FINAL_view_csv_json_invoices
    WHERE sales_order_number LIKE 'SO/25-26/00808'
    ORDER BY invoice_date
    """).fetchall()
    
    print(f"\n📋 SO/25-26/00808 Invoice Timeline:")
    for row in pattern_analysis:
        print(f"  SO: {row[0]} | Invoice Date: {row[1]} | Customer: {row[2]}")
    
    conn.close()
    
    print("\n✅ Specific Sales Order Investigation Complete!")
    print("📋 Key findings identified for user-reported issue")

if __name__ == "__main__":
    investigate_specific_sales_order_issue()
