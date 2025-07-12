#!/usr/bin/env python3
"""
Simple fix for FINAL views using CSV data with proper WHERE clauses
"""

import sqlite3
import sys
import os

def simple_fix_final_views():
    """Fix the empty FINAL views using CSV data with proper WHERE clauses"""
    
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 SIMPLE FIX FOR FINAL VIEWS")
        print("=" * 50)
        
        # Fix 1: Contacts view - use non-NULL display_name or company_name
        print("\n1️⃣ FIXING FINAL_view_csv_json_contacts")
        print("-" * 40)
        
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_contacts")
        
        contacts_fix = """
        CREATE VIEW FINAL_view_csv_json_contacts AS
        SELECT 
            *,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_contacts
        WHERE 
            display_name IS NOT NULL 
            OR company_name IS NOT NULL
            OR first_name IS NOT NULL
            OR last_name IS NOT NULL
        """
        
        cursor.execute(contacts_fix)
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_contacts")
        contacts_count = cursor.fetchone()[0]
        print(f"✅ Fixed contacts view: {contacts_count:,} rows")
        
        # Fix 2: Items view - use non-NULL item_name or sku  
        print("\n2️⃣ FIXING FINAL_view_csv_json_items")
        print("-" * 40)
        
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_items")
        
        items_fix = """
        CREATE VIEW FINAL_view_csv_json_items AS
        SELECT 
            *,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_items
        WHERE 
            item_name IS NOT NULL 
            OR sku IS NOT NULL
            OR description IS NOT NULL
        """
        
        cursor.execute(items_fix)
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_items")
        items_count = cursor.fetchone()[0]
        print(f"✅ Fixed items view: {items_count:,} rows")
        
        # Fix 3: Sales orders view - use non-NULL sales_order_number or customer_name
        print("\n3️⃣ FIXING FINAL_view_csv_json_sales_orders")
        print("-" * 40)
        
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        
        sales_orders_fix = """
        CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT 
            *,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_sales_orders
        WHERE 
            sales_order_number IS NOT NULL 
            OR customer_name IS NOT NULL
            OR order_date IS NOT NULL
        """
        
        cursor.execute(sales_orders_fix)
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
        sales_orders_count = cursor.fetchone()[0]
        print(f"✅ Fixed sales orders view: {sales_orders_count:,} rows")
        
        # Show summary
        print(f"\n🎉 SUMMARY OF FIXES")
        print("=" * 30)
        print(f"📊 FINAL_view_csv_json_contacts: {contacts_count:,} rows (was 0)")
        print(f"📊 FINAL_view_csv_json_items: {items_count:,} rows (was 0)")
        print(f"📊 FINAL_view_csv_json_sales_orders: {sales_orders_count:,} rows (was 0)")
        
        total_recovered = contacts_count + items_count + sales_orders_count
        print(f"\n✅ TOTAL RECOVERED: {total_recovered:,} business records!")
        
        # Test the views work
        print(f"\n🔍 TESTING VIEW FUNCTIONALITY")
        print("-" * 30)
        
        # Test contacts
        cursor.execute("SELECT display_name, company_name FROM FINAL_view_csv_json_contacts LIMIT 3")
        contact_samples = cursor.fetchall()
        print(f"📋 Sample contacts:")
        for contact in contact_samples:
            print(f"  - {contact[0] or 'N/A'} ({contact[1] or 'No company'})")
        
        # Test items
        cursor.execute("SELECT item_name, sku FROM FINAL_view_csv_json_items LIMIT 3")
        item_samples = cursor.fetchall()
        print(f"📋 Sample items:")
        for item in item_samples:
            print(f"  - {item[0] or 'N/A'} (SKU: {item[1] or 'No SKU'})")
        
        # Test sales orders
        cursor.execute("SELECT sales_order_number, customer_name FROM FINAL_view_csv_json_sales_orders LIMIT 3")
        so_samples = cursor.fetchall()
        print(f"📋 Sample sales orders:")
        for so in so_samples:
            print(f"  - {so[0] or 'N/A'} (Customer: {so[1] or 'No customer'})")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
        print("The three empty FINAL views now have data accessible.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    simple_fix_final_views()
