import sqlite3
import os

def check_database_tables(db_path, db_name):
    """Check what tables exist in a database"""
    print(f"\n{'='*60}")
    print(f"Checking tables in: {db_name}")
    print(f"Database path: {db_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file does not exist: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in database")
        else:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                table_name = table[0]
                # Get row count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  📊 {table_name}: {count:,} records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    # Check main database
    check_database_tables("database.db", "database.db")
    
    # Check production database
    check_database_tables("data/database/production.db", "production.db")
