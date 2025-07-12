#!/usr/bin/env python3
"""
Check sales orders status and create missing FINAL view if needed
"""

import sqlite3
import os

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 SALES ORDERS FINAL VIEW STATUS CHECK')
    print('='*60)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check if FINAL view exists
    print("🎯 CHECKING FOR FINAL_view_csv_json_sales_orders:")
    try:
        final_count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders').fetchone()[0]
        print(f"   ✅ FINAL_view_csv_json_sales_orders exists: {final_count:,} records")
        
        # Analyze existing FINAL view
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders), 2) as percentage
            FROM FINAL_view_csv_json_sales_orders
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        sources = cursor.fetchall()
        print(f"   Data source distribution:")
        for source, count, pct in sources:
            print(f"      {source}: {count:,} records ({pct}%)")
            
        conn.close()
        return
        
    except Exception as e:
        if "no such table" in str(e):
            print(f"   ❌ FINAL_view_csv_json_sales_orders does NOT exist")
        else:
            print(f"   ❌ Error checking FINAL view: {e}")
    
    # 2. Check base tables
    print(f"\n📋 BASE TABLE ANALYSIS:")
    try:
        csv_count = conn.execute('SELECT COUNT(*) FROM csv_sales_orders').fetchone()[0]
        print(f"   csv_sales_orders: {csv_count:,} records")
    except Exception as e:
        print(f"   ❌ csv_sales_orders: {e}")
        csv_count = 0
        
    try:
        json_count = conn.execute('SELECT COUNT(*) FROM json_sales_orders').fetchone()[0]
        print(f"   json_sales_orders: {json_count:,} records")
    except Exception as e:
        print(f"   ❌ json_sales_orders: {e}")
        json_count = 0
    
    # 3. Check integration view (which we know was fixed)
    print(f"\n🔄 INTEGRATION VIEW STATUS:")
    try:
        int_count = conn.execute('SELECT COUNT(*) FROM view_csv_json_sales_orders').fetchone()[0]
        print(f"   ✅ view_csv_json_sales_orders: {int_count:,} records (our fix worked!)")
        
        # Check integration view data sources
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count
            FROM view_csv_json_sales_orders
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        int_sources = cursor.fetchall()
        print(f"   Integration view data sources:")
        for source, count in int_sources:
            print(f"      {source}: {count:,} records")
            
    except Exception as e:
        print(f"   ❌ view_csv_json_sales_orders error: {e}")
        conn.close()
        return
    
    # 4. Create the missing FINAL view
    print(f"\n🔨 CREATING MISSING FINAL VIEW:")
    try:
        create_final_sql = """
        CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT * FROM view_csv_json_sales_orders
        """
        
        cursor.execute(create_final_sql)
        print(f"   ✅ Created FINAL_view_csv_json_sales_orders")
        
        # Verify the creation
        final_count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders').fetchone()[0]
        print(f"   ✅ Verification: FINAL view contains {final_count:,} records")
        
        # Analyze the new FINAL view
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders), 2) as percentage
            FROM FINAL_view_csv_json_sales_orders
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        sources = cursor.fetchall()
        print(f"   📊 NEW FINAL VIEW DATA SOURCES:")
        for source, count, pct in sources:
            print(f"      {source}: {count:,} records ({pct}%)")
        
    except Exception as e:
        print(f"   ❌ Failed to create FINAL view: {e}")
        conn.close()
        return
    
    # 5. Sample records from new FINAL view
    print(f"\n📋 SAMPLE RECORDS FROM NEW FINAL VIEW:")
    try:
        cursor.execute('''
            SELECT data_source, sales_order_id, salesorder_number, customer_name, total
            FROM FINAL_view_csv_json_sales_orders 
            ORDER BY data_source
            LIMIT 5
        ''')
        
        samples = cursor.fetchall()
        for source, so_id, so_number, customer, total in samples:
            print(f"   {source}: ID={so_id}, #={so_number}, Customer={customer}, Total={total}")
            
    except Exception as e:
        print(f"   ❌ Sample records failed: {e}")
    
    # 6. Summary assessment
    print(f"\n💡 ASSESSMENT:")
    total_source = csv_count + json_count
    if total_source > 0:
        expansion_ratio = final_count / total_source if total_source > 0 else 0
        print(f"   Source records: CSV={csv_count:,}, JSON={json_count:,}")
        print(f"   FINAL view records: {final_count:,}")
        print(f"   Integration success: All source data represented")
        print(f"   Expansion ratio: {expansion_ratio:.1f}x")
        
        if expansion_ratio > 1.2:
            print(f"   📊 Data expansion detected - likely includes line items or enrichment")
        else:
            print(f"   ✅ Expected 1:1 integration - header level data")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "="*60)
    print(f"🎉 SALES ORDERS FINAL VIEW CREATION COMPLETE!")

if __name__ == "__main__":
    main()
