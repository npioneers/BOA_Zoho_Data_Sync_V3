import sqlite3

conn = sqlite3.connect('../data/database/production.db')

# Check all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"Total tables: {len(tables)}")

# Look for sales order tables
so_tables = [t[0] for t in tables if 'sales' in t[0].lower() or 'order' in t[0].lower()]
print(f"\nSales/Order tables: {len(so_tables)}")
for table in so_tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  - {table}: {count} records")

# Check all views
views = conn.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name").fetchall()
print(f"\nTotal views: {len(views)}")

# Look for sales order views
so_views = [v[0] for v in views if 'sales' in v[0].lower() or 'order' in v[0].lower()]
print(f"\nSales/Order views: {len(so_views)}")
for view in so_views:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  - {view}: {count} records")
    except Exception as e:
        print(f"  - {view}: ERROR - {e}")

conn.close()
