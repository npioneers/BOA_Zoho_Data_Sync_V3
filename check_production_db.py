"""
Check production database tables
"""
import sqlite3
from pathlib import Path

def check_production_database():
    """Check what tables exist in the production database"""
    
    # Use the correct production database path
    db_path = Path("data/database/production.db")
    
    if not db_path.exists():
        print(f"❌ Production database not found at: {db_path}")
        return
    
    print(f"📊 Checking Production Database: {db_path}")
    print(f"Database size: {db_path.stat().st_size:,} bytes")
    print("="*60)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Total tables: {len(tables)}")
        print("\nTables with record counts:")
        
        total_records = 0
        json_tables = []
        other_tables = []
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                
                if table.startswith('json_'):
                    json_tables.append((table, count))
                else:
                    other_tables.append((table, count))
                    
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
        
        # Show JSON tables (our main data)
        print(f"\nJSON Data Tables ({len(json_tables)}):")
        for table, count in sorted(json_tables, key=lambda x: x[1], reverse=True):
            print(f"  ✅ {table}: {count:,} records")
        
        # Show other tables
        print(f"\nOther Tables ({len(other_tables)}):")
        for table, count in sorted(other_tables, key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"  ✅ {table}: {count:,} records")
            else:
                print(f"  ⚪ {table}: {count} records")
        
        print(f"\n📊 TOTAL RECORDS: {total_records:,}")
        
        conn.close()
        
        # Check if this is the main production database
        if total_records > 40000:
            print("\n🎯 This appears to be the MAIN PRODUCTION DATABASE")
        elif total_records > 1000:
            print("\n📋 This appears to be a secondary database")
        else:
            print("\n🔧 This appears to be a test or empty database")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_production_database()
