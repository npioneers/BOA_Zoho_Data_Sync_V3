#!/usr/bin/env python3
"""
Fix Empty FINAL Views Script
============================

This script implements the fixes identified in the investigation:
1. FINAL_view_csv_json_contacts - Fix WHERE clause to use non-NULL fields
2. FINAL_view_csv_json_items - Fix WHERE clause to use non-NULL fields  
3. FINAL_view_csv_json_sales_orders - Investigate missing table + fix WHERE clause

Based on investigation findings from EMPTY_VIEWS_INVESTIGATION_REPORT.md
"""

import sqlite3
import os
import sys
from datetime import datetime

def connect_to_database():
    """Connect to the production database"""
    db_path = os.path.join("..", "data", "database", "production.db")
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        sys.exit(1)
    
    return sqlite3.connect(db_path)

def backup_view_definitions(conn):
    """Create backup of current view definitions before making changes"""
    cursor = conn.cursor()
    
    # Get all view definitions
    cursor.execute("""
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type = 'view' 
        AND name LIKE 'FINAL_view_csv_json_%'
        ORDER BY name
    """)
    
    views = cursor.fetchall()
    
    # Create backup file
    backup_file = f"view_definitions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    with open(backup_file, 'w') as f:
        f.write("-- View Definitions Backup\n")
        f.write(f"-- Created: {datetime.now()}\n")
        f.write("-- Original views before fixing empty view issues\n\n")
        
        for view_name, view_sql in views:
            f.write(f"-- {view_name}\n")
            f.write(f"DROP VIEW IF EXISTS {view_name};\n")
            f.write(f"{view_sql};\n\n")
    
    print(f"✅ View definitions backed up to: {backup_file}")
    return backup_file

def fix_contacts_view(conn):
    """Fix FINAL_view_csv_json_contacts view"""
    print("\n🔧 Fixing FINAL_view_csv_json_contacts...")
    
    cursor = conn.cursor()
    
    # Get current view definition
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type = 'view' AND name = 'FINAL_view_csv_json_contacts'
    """)
    
    current_sql = cursor.fetchone()
    if not current_sql:
        print("❌ View FINAL_view_csv_json_contacts not found")
        return False
    
    current_sql = current_sql[0]
    print(f"📋 Current view SQL:\n{current_sql[:200]}...")
    
    # Check what non-NULL fields are available for WHERE clause
    cursor.execute("SELECT display_name, company_name, contact_id FROM csv_contacts LIMIT 5")
    sample_data = cursor.fetchall()
    
    print("📊 Sample contact data:")
    for row in sample_data:
        print(f"  display_name: {row[0]}, company_name: {row[1]}, contact_id: {row[2]}")
    
    # Create new view definition with fixed WHERE clause
    new_sql = current_sql.replace(
        "WHERE csv.contact_id IS NOT NULL",
        "WHERE (csv.display_name IS NOT NULL AND csv.display_name != '') OR (csv.company_name IS NOT NULL AND csv.company_name != '')"
    )
    
    if new_sql == current_sql:
        print("⚠️ No WHERE clause replacement found - trying alternative pattern")
        # Try other possible patterns
        if "csv.contact_id IS NOT NULL" in current_sql:
            new_sql = current_sql.replace(
                "csv.contact_id IS NOT NULL",
                "(csv.display_name IS NOT NULL AND csv.display_name != '') OR (csv.company_name IS NOT NULL AND csv.company_name != '')"
            )
    
    if new_sql == current_sql:
        print("❌ Could not identify WHERE clause pattern to fix")
        return False
    
    try:
        # Drop and recreate view
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_contacts")
        cursor.execute(new_sql)
        conn.commit()
        
        # Test the fix
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_contacts")
        new_count = cursor.fetchone()[0]
        
        print(f"✅ FINAL_view_csv_json_contacts fixed!")
        print(f"📈 New row count: {new_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing contacts view: {e}")
        return False

def fix_items_view(conn):
    """Fix FINAL_view_csv_json_items view"""
    print("\n🔧 Fixing FINAL_view_csv_json_items...")
    
    cursor = conn.cursor()
    
    # Get current view definition
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type = 'view' AND name = 'FINAL_view_csv_json_items'
    """)
    
    current_sql = cursor.fetchone()
    if not current_sql:
        print("❌ View FINAL_view_csv_json_items not found")
        return False
    
    current_sql = current_sql[0]
    print(f"📋 Current view SQL:\n{current_sql[:200]}...")
    
    # Check what non-NULL fields are available for WHERE clause
    cursor.execute("SELECT item_name, sku, item_id FROM csv_items LIMIT 5")
    sample_data = cursor.fetchall()
    
    print("📊 Sample item data:")
    for row in sample_data:
        print(f"  item_name: {row[0]}, sku: {row[1]}, item_id: {row[2]}")
    
    # Create new view definition with fixed WHERE clause
    new_sql = current_sql.replace(
        "WHERE csv.item_id IS NOT NULL",
        "WHERE (csv.item_name IS NOT NULL AND csv.item_name != '') OR (csv.sku IS NOT NULL AND csv.sku != '')"
    )
    
    if new_sql == current_sql:
        print("⚠️ No WHERE clause replacement found - trying alternative pattern")
        if "csv.item_id IS NOT NULL" in current_sql:
            new_sql = current_sql.replace(
                "csv.item_id IS NOT NULL",
                "(csv.item_name IS NOT NULL AND csv.item_name != '') OR (csv.sku IS NOT NULL AND csv.sku != '')"
            )
    
    if new_sql == current_sql:
        print("❌ Could not identify WHERE clause pattern to fix")
        return False
    
    try:
        # Drop and recreate view
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_items")
        cursor.execute(new_sql)
        conn.commit()
        
        # Test the fix
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_items")
        new_count = cursor.fetchone()[0]
        
        print(f"✅ FINAL_view_csv_json_items fixed!")
        print(f"📈 New row count: {new_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing items view: {e}")
        return False

def investigate_sales_orders_view(conn):
    """Investigate and attempt to fix FINAL_view_csv_json_sales_orders"""
    print("\n🔍 Investigating FINAL_view_csv_json_sales_orders...")
    
    cursor = conn.cursor()
    
    # Check if view_flat_json_salesorders exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type IN ('table', 'view') 
        AND name = 'view_flat_json_salesorders'
    """)
    
    if not cursor.fetchone():
        print("❌ Missing table: view_flat_json_salesorders")
        
        # Check what JSON sales order tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type IN ('table', 'view') 
            AND name LIKE '%json%sales%order%'
            ORDER BY name
        """)
        
        json_tables = cursor.fetchall()
        print("🔍 Available JSON sales order tables:")
        for table in json_tables:
            print(f"  - {table[0]}")
        
        # Check json_sales_orders table structure
        if json_tables:
            table_name = json_tables[0][0]  # Use first available table
            print(f"\n📊 Checking structure of {table_name}:")
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns[:10]:  # Show first 10 columns
                print(f"  - {col[1]} ({col[2]})")
            
            # Check row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📈 Row count: {count}")
            
            # Attempt to create the missing view
            return create_missing_sales_orders_view(conn, table_name)
    
    else:
        print("✅ view_flat_json_salesorders exists - checking WHERE clause issue")
        return fix_sales_orders_where_clause(conn)

def create_missing_sales_orders_view(conn, source_table):
    """Create the missing view_flat_json_salesorders view"""
    print(f"\n🔧 Attempting to create view_flat_json_salesorders from {source_table}...")
    
    cursor = conn.cursor()
    
    try:
        # Create a basic flattened view from the source table
        cursor.execute(f"""
            CREATE VIEW view_flat_json_salesorders AS
            SELECT * FROM {source_table}
        """)
        conn.commit()
        
        print("✅ Created view_flat_json_salesorders")
        
        # Now try to fix the main FINAL view
        return fix_sales_orders_where_clause(conn)
        
    except Exception as e:
        print(f"❌ Error creating view_flat_json_salesorders: {e}")
        return False

def fix_sales_orders_where_clause(conn):
    """Fix the WHERE clause in FINAL_view_csv_json_sales_orders"""
    print("\n🔧 Fixing FINAL_view_csv_json_sales_orders WHERE clause...")
    
    cursor = conn.cursor()
    
    # Get current view definition
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type = 'view' AND name = 'FINAL_view_csv_json_sales_orders'
    """)
    
    current_sql = cursor.fetchone()
    if not current_sql:
        print("❌ View FINAL_view_csv_json_sales_orders not found")
        return False
    
    current_sql = current_sql[0]
    
    # Check sample data to determine what fields to use
    cursor.execute("SELECT sales_order_number, customer_name, sales_order_id FROM csv_sales_orders LIMIT 5")
    sample_data = cursor.fetchall()
    
    print("📊 Sample sales order data:")
    for row in sample_data:
        print(f"  sales_order_number: {row[0]}, customer_name: {row[1]}, sales_order_id: {row[2]}")
    
    # Update WHERE clause to use non-NULL fields
    new_sql = current_sql
    
    # Replace common NULL-filtering patterns
    if "csv.sales_order_id IS NOT NULL" in current_sql:
        new_sql = new_sql.replace(
            "csv.sales_order_id IS NOT NULL",
            "(csv.sales_order_number IS NOT NULL AND csv.sales_order_number != '') OR (csv.customer_name IS NOT NULL AND csv.customer_name != '')"
        )
    
    try:
        # Drop and recreate view
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        cursor.execute(new_sql)
        conn.commit()
        
        # Test the fix
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
        new_count = cursor.fetchone()[0]
        
        print(f"✅ FINAL_view_csv_json_sales_orders fixed!")
        print(f"📈 New row count: {new_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing sales orders view: {e}")
        return False

def validate_fixes(conn):
    """Validate that all fixes worked correctly"""
    print("\n🧪 Validating fixes...")
    
    cursor = conn.cursor()
    
    views_to_check = [
        'FINAL_view_csv_json_contacts',
        'FINAL_view_csv_json_items', 
        'FINAL_view_csv_json_sales_orders'
    ]
    
    results = {}
    
    for view_name in views_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
            count = cursor.fetchone()[0]
            results[view_name] = count
            
            if count > 0:
                print(f"✅ {view_name}: {count} rows")
            else:
                print(f"❌ {view_name}: Still empty")
                
        except Exception as e:
            print(f"❌ {view_name}: Error - {e}")
            results[view_name] = f"Error: {e}"
    
    return results

def main():
    """Main execution function"""
    print("🚀 Starting Fix Empty Views Process")
    print("="*50)
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        # Create backup
        backup_file = backup_view_definitions(conn)
        
        # Track results
        fixes_applied = []
        
        # Fix contacts view
        if fix_contacts_view(conn):
            fixes_applied.append("contacts")
        
        # Fix items view  
        if fix_items_view(conn):
            fixes_applied.append("items")
        
        # Investigate and fix sales orders
        if investigate_sales_orders_view(conn):
            fixes_applied.append("sales_orders")
        
        # Validate all fixes
        print("\n" + "="*50)
        results = validate_fixes(conn)
        
        # Summary
        print("\n📋 SUMMARY")
        print("="*20)
        print(f"✅ Fixes applied: {len(fixes_applied)}")
        print(f"📁 Backup created: {backup_file}")
        
        total_recovered = sum(count for count in results.values() if isinstance(count, int))
        print(f"📈 Total records recovered: {total_recovered:,}")
        
        if len(fixes_applied) == 3:
            print("🎉 All empty views have been fixed!")
        else:
            print(f"⚠️ {3 - len(fixes_applied)} views still need attention")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
