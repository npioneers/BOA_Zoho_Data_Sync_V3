import sqlite3

def check_database_tables():
    """
    Check what tables and views actually exist in the database
    """
    
    # Connect to database
    conn = sqlite3.connect('../production.db')
    
    print("🔍 DATABASE INVENTORY CHECK")
    print("=" * 50)
    
    # List all tables
    print("\n📊 ALL TABLES:")
    print("-" * 30)
    
    tables = conn.execute("""
    SELECT name 
    FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name
    """).fetchall()
    
    print(f"📋 Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # List all views
    print("\n📊 ALL VIEWS:")
    print("-" * 30)
    
    views = conn.execute("""
    SELECT name 
    FROM sqlite_master 
    WHERE type='view' 
    ORDER BY name
    """).fetchall()
    
    print(f"📋 Found {len(views)} views:")
    for view in views:
        print(f"  - {view[0]}")
    
    # Look for sales order related items
    print("\n📊 SALES ORDER RELATED ITEMS:")
    print("-" * 30)
    
    so_items = conn.execute("""
    SELECT type, name 
    FROM sqlite_master 
    WHERE name LIKE '%sales%' OR name LIKE '%order%'
    ORDER BY type, name
    """).fetchall()
    
    print(f"📋 Found {len(so_items)} sales/order related items:")
    for item in so_items:
        print(f"  - {item[0].upper()}: {item[1]}")
    
    # Check if we have invoice tables to verify database content
    print("\n📊 INVOICE TABLE CHECK:")
    print("-" * 30)
    
    invoice_items = conn.execute("""
    SELECT type, name 
    FROM sqlite_master 
    WHERE name LIKE '%invoice%'
    ORDER BY type, name
    """).fetchall()
    
    print(f"📋 Found {len(invoice_items)} invoice related items:")
    for item in invoice_items:
        print(f"  - {item[0].upper()}: {item[1]}")
        
        # If it's a table, show record count
        if item[0] == 'table':
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {item[1]}").fetchone()[0]
                print(f"    Records: {count}")
            except Exception as e:
                print(f"    Error counting: {e}")
    
    conn.close()
    
    print("\n✅ Database inventory complete!")

if __name__ == "__main__":
    check_database_tables()
