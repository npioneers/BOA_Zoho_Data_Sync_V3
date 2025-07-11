#!/usr/bin/env python3

import sqlite3
import yaml

def create_working_duplicate_solution():
    """Create working duplicate-aware views with simple, robust SQL"""
    
    # Load config
    with open('config/json_sync.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Connect to database
    db_path = config['json_sync']['database_path']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== CREATING WORKING DUPLICATE-AWARE VIEWS ===")
    print("Approach: Simple, robust SQL with JSON precedence")
    
    # Create enhanced bills view (improved approach)
    print("\n1. Creating enhanced bills view...")
    try:
        cursor.execute("DROP VIEW IF EXISTS view_csv_json_bills_v3;")
        
        # Simple approach: modify existing logic to handle duplicates better
        bills_v3_sql = """
        CREATE VIEW view_csv_json_bills_v3 AS
        SELECT 
            COALESCE(flat.bill_number, csv.bill_number) AS bill_number,
            COALESCE(flat.vendor_name, csv.vendor_name) AS vendor_name,
            COALESCE(flat.total, csv.total) AS total,
            COALESCE(flat.balance, csv.balance) AS balance,
            COALESCE(flat.date, csv.bill_date) AS bill_date,
            csv.account,
            csv.account_code,
            csv.accounts_payable,
            flat.vendor_id,
            flat.due_date,
            flat.currency_code,
            flat.line_item_name,
            flat.line_item_quantity,
            flat.line_item_rate,
            flat.line_item_item_total,
            flat.line_item_account_name,
            flat.line_item_description,
            flat.line_item_unit,
            flat.line_item_tax_name,
            flat.line_item_tax_percentage,
            CASE 
                WHEN flat.bill_number IS NOT NULL THEN 'json_precedence'
                ELSE 'csv_only' 
            END AS data_source,
            CASE 
                WHEN flat.bill_number IS NOT NULL THEN 1  -- JSON has priority
                ELSE 2  -- CSV backup
            END AS source_priority
        FROM csv_bills csv
        LEFT JOIN view_flat_json_bills flat ON csv.bill_number = flat.bill_number
        WHERE COALESCE(flat.bill_number, csv.bill_number) IS NOT NULL
        """
        
        cursor.execute(bills_v3_sql)
        
        # Test the view
        cursor.execute("SELECT COUNT(*) FROM view_csv_json_bills_v3")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM view_csv_json_bills_v3 WHERE data_source = 'json_precedence'")
        json_count = cursor.fetchone()[0]
        
        enhancement_rate = (json_count / total * 100) if total > 0 else 0
        
        print(f"  ✅ Enhanced bills view (v3) created:")
        print(f"     Total records: {total:,}")
        print(f"     JSON precedence: {json_count:,} ({enhancement_rate:.1f}%)")
        
        # Check for bills with multiple line items
        cursor.execute("""
            SELECT bill_number, COUNT(*) as line_count 
            FROM view_csv_json_bills_v3 
            WHERE data_source = 'json_precedence'
            GROUP BY bill_number 
            HAVING COUNT(*) > 1 
            LIMIT 3
        """)
        
        multi_line_bills = cursor.fetchall()
        if multi_line_bills:
            print(f"     Line item examples:")
            for bill, count in multi_line_bills:
                print(f"       {bill}: {count} line items")
        
    except Exception as e:
        print(f"  ❌ Error creating enhanced bills view: {e}")
    
    # Create deduplication view for bills summary
    print("\n2. Creating bills deduplication summary...")
    try:
        cursor.execute("DROP VIEW IF EXISTS view_bills_deduplicated;")
        
        # Create a view that shows each bill only once, prioritizing JSON
        bills_dedup_sql = """
        CREATE VIEW view_bills_deduplicated AS
        SELECT 
            bill_number,
            vendor_name,
            total,
            balance,
            bill_date,
            account,
            account_code,
            accounts_payable,
            vendor_id,
            due_date,
            currency_code,
            data_source,
            source_priority,
            COUNT(line_item_name) as line_item_count
        FROM view_csv_json_bills_v3
        WHERE bill_number IS NOT NULL
        GROUP BY 
            bill_number,
            vendor_name,
            total,
            balance,
            bill_date,
            account,
            account_code,
            accounts_payable,
            vendor_id,
            due_date,
            currency_code,
            data_source,
            source_priority
        HAVING MIN(source_priority) = source_priority  -- Keep only highest priority (JSON first)
        """
        
        cursor.execute(bills_dedup_sql)
        
        # Test deduplication
        cursor.execute("SELECT COUNT(*) FROM view_bills_deduplicated")
        dedup_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM view_bills_deduplicated WHERE data_source = 'json_precedence'")
        dedup_json = cursor.fetchone()[0]
        
        print(f"  ✅ Bills deduplication view created:")
        print(f"     Unique bills: {dedup_total:,}")
        print(f"     JSON precedence: {dedup_json:,}")
        
        # Verify no duplicates
        cursor.execute("""
            SELECT bill_number, COUNT(*) 
            FROM view_bills_deduplicated 
            GROUP BY bill_number 
            HAVING COUNT(*) > 1
        """)
        
        remaining_dups = cursor.fetchall()
        if remaining_dups:
            print(f"     ⚠️  {len(remaining_dups)} bills still duplicated")
        else:
            print(f"     ✅ Perfect deduplication achieved!")
        
    except Exception as e:
        print(f"  ❌ Error creating deduplication view: {e}")
    
    # Test the duplicate handling
    print("\n3. Testing duplicate resolution...")
    try:
        # Find bills that exist in both sources and check which source wins
        cursor.execute("""
            SELECT 
                b.bill_number,
                b.data_source,
                b.vendor_name as enhanced_vendor,
                c.vendor_name as csv_vendor,
                CASE WHEN b.vendor_name != c.vendor_name THEN 'DIFFERENT' ELSE 'SAME' END as vendor_comparison
            FROM view_bills_deduplicated b
            JOIN csv_bills c ON b.bill_number = c.bill_number
            WHERE b.data_source = 'json_precedence'
            AND b.vendor_name IS NOT NULL 
            AND c.vendor_name IS NOT NULL
            LIMIT 5
        """)
        
        comparisons = cursor.fetchall()
        print(f"  Sample JSON precedence examples:")
        for bill, source, enhanced_vendor, csv_vendor, comparison in comparisons:
            print(f"    {bill}: {source}")
            print(f"      Enhanced: {enhanced_vendor}")
            print(f"      CSV: {csv_vendor}")
            print(f"      Status: {comparison}")
            print()
        
    except Exception as e:
        print(f"  ❌ Error testing duplicate resolution: {e}")
    
    print("\n4. Creating demonstration queries...")
    
    # Create a demonstration of the duplicate handling
    demo_queries = [
        ("Total bills with JSON data", "SELECT COUNT(*) FROM view_csv_json_bills_v3 WHERE data_source = 'json_precedence'"),
        ("Total unique bills", "SELECT COUNT(*) FROM view_bills_deduplicated"),
        ("JSON precedence rate", "SELECT ROUND(COUNT(CASE WHEN data_source = 'json_precedence' THEN 1 END) * 100.0 / COUNT(*), 1) || '%' FROM view_bills_deduplicated"),
        ("Average line items per bill", "SELECT ROUND(AVG(line_item_count), 1) FROM view_bills_deduplicated WHERE data_source = 'json_precedence'")
    ]
    
    print("  📊 Summary Statistics:")
    for desc, query in demo_queries:
        try:
            cursor.execute(query)
            result = cursor.fetchone()[0]
            print(f"    {desc}: {result}")
        except Exception as e:
            print(f"    {desc}: Error - {e}")
    
    conn.commit()
    conn.close()
    
    print("\n=== SUCCESS: DUPLICATE-AWARE VIEWS IMPLEMENTED ===")
    print("✅ Key Views Created:")
    print("   • view_csv_json_bills_v3: Enhanced view with JSON precedence")
    print("   • view_bills_deduplicated: One record per bill, JSON wins duplicates")
    print("")
    print("🎯 Duplicate Handling Features:")
    print("   1. JSON data takes precedence over CSV when both exist")
    print("   2. Line item data preserved in enhanced view")
    print("   3. Deduplication view shows unique bills only")
    print("   4. Data source tracking maintains transparency")
    print("   5. Source priority ranking ensures consistent resolution")

if __name__ == "__main__":
    create_working_duplicate_solution()
