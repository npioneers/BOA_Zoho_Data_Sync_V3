#!/usr/bin/env python3
"""
Database Tables Explorer
Explores what tables exist in the production database.
"""
import sqlite3
from config import get_database_path


def explore_database():
    """Explore the database structure"""
    db_path = get_database_path()
    print(f"=== Exploring Database: {db_path} ===\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Total tables found: {len(all_tables)}\n")
        
        # Categorize tables
        final_tables = [t for t in all_tables if 'FINAL' in t.upper()]
        csv_tables = [t for t in all_tables if t.startswith('csv_')]
        json_tables = [t for t in all_tables if t.startswith('json_')]
        other_tables = [t for t in all_tables if not any([
            'FINAL' in t.upper(), 
            t.startswith('csv_'), 
            t.startswith('json_')
        ])]
        
        print("=== Table Categories ===")
        print(f"FINAL tables: {len(final_tables)}")
        if final_tables:
            for table in final_tables:
                print(f"  - {table}")
        
        print(f"\nCSV tables: {len(csv_tables)}")
        if csv_tables:
            for table in csv_tables[:10]:  # Show first 10
                print(f"  - {table}")
            if len(csv_tables) > 10:
                print(f"  ... and {len(csv_tables) - 10} more")
        
        print(f"\nJSON tables: {len(json_tables)}")
        if json_tables:
            for table in json_tables[:10]:  # Show first 10
                print(f"  - {table}")
            if len(json_tables) > 10:
                print(f"  ... and {len(json_tables) - 10} more")
        
        print(f"\nOther tables: {len(other_tables)}")
        if other_tables:
            for table in other_tables:
                print(f"  - {table}")
        
        # Check for views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        views = [row[0] for row in cursor.fetchall()]
        
        print(f"\n=== Views Found: {len(views)} ===")
        final_views = [v for v in views if 'FINAL' in v.upper()]
        other_views = [v for v in views if 'FINAL' not in v.upper()]
        
        if final_views:
            print("FINAL views:")
            for view in final_views:
                cursor.execute(f"SELECT COUNT(*) FROM `{view}`")
                count = cursor.fetchone()[0]
                print(f"  - {view}: {count:,} records")
        
        if other_views:
            print("Other views:")
            for view in other_views:
                print(f"  - {view}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exploring database: {e}")


if __name__ == "__main__":
    explore_database()
