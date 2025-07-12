#!/usr/bin/env python3
"""
Check for any other missing FINAL views and create them
"""

import sqlite3
import os

def check_and_create_final_view(conn, table_name):
    """Check if FINAL view exists for a table and create if missing"""
    
    cursor = conn.cursor()
    final_view_name = f"FINAL_view_csv_json_{table_name}"
    integration_view_name = f"view_csv_json_{table_name}"
    
    print(f"\n🔍 CHECKING {table_name}:")
    
    # Check if FINAL view exists
    try:
        final_count = conn.execute(f'SELECT COUNT(*) FROM {final_view_name}').fetchone()[0]
        print(f"   ✅ {final_view_name} exists: {final_count:,} records")
        return True
    except:
        print(f"   ❌ {final_view_name} missing")
    
    # Check if integration view exists to create FINAL from
    try:
        int_count = conn.execute(f'SELECT COUNT(*) FROM {integration_view_name}').fetchone()[0]
        print(f"   ✅ {integration_view_name} exists: {int_count:,} records")
        
        # Create the FINAL view
        create_sql = f"""
        CREATE VIEW {final_view_name} AS
        SELECT * FROM {integration_view_name}
        """
        
        cursor.execute(create_sql)
        print(f"   🔨 Created {final_view_name}")
        
        # Verify
        final_count = conn.execute(f'SELECT COUNT(*) FROM {final_view_name}').fetchone()[0]
        print(f"   ✅ Verified: {final_count:,} records")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Cannot create - {integration_view_name} error: {e}")
        return False

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 COMPREHENSIVE FINAL VIEWS CHECK & CREATION')
    print('='*60)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # List of all tables that should have FINAL views
    tables_to_check = [
        'bills',
        'credit_notes', 
        'customer_payments',
        'invoices',
        'items',
        'purchase_orders',
        'sales_orders',
        'vendor_payments',
        'contacts',
        'organizations'
    ]
    
    created_count = 0
    existing_count = 0
    failed_count = 0
    
    print(f"📋 CHECKING {len(tables_to_check)} POTENTIAL FINAL VIEWS:")
    
    for table in tables_to_check:
        result = check_and_create_final_view(conn, table)
        if result:
            # Check if it was created or already existed
            final_view_name = f"FINAL_view_csv_json_{table}"
            try:
                # If we can count it, it exists now
                count = conn.execute(f'SELECT COUNT(*) FROM {final_view_name}').fetchone()[0]
                if "Created" in locals():
                    created_count += 1
                else:
                    existing_count += 1
            except:
                pass
        else:
            failed_count += 1
    
    # Get final count of all FINAL views
    print(f"\n📊 FINAL VIEWS SUMMARY:")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'FINAL_%' ORDER BY name")
    all_final_views = cursor.fetchall()
    
    print(f"   Total FINAL views now: {len(all_final_views)}")
    for view in all_final_views:
        view_name = view[0]
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
            print(f"   ✅ {view_name}: {count:,} records")
        except Exception as e:
            print(f"   ❌ {view_name}: ERROR - {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎯 CREATION SUMMARY:")
    print(f"   Already existed: {existing_count}")
    print(f"   Newly created: {created_count}")  
    print(f"   Failed to create: {failed_count}")
    print(f"   Total FINAL views: {len(all_final_views)}")
    
    print(f"\n" + "="*60)
    print(f"🎉 FINAL VIEWS COMPREHENSIVE CHECK COMPLETE!")

if __name__ == "__main__":
    main()
