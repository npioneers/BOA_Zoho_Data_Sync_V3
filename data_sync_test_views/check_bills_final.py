#!/usr/bin/env python3
"""
Check production database for bills FINAL view
"""

import sqlite3
import os

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 EVALUATING BILLS FINAL VIEW STATUS')
    print('='*60)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
        
    print(f"📂 Database: {db_path}")
    print(f"📏 Size: {os.path.getsize(db_path):,} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for FINAL bills view specifically
        print(f"\n🎯 CHECKING FOR FINAL_view_csv_json_bills:")
        try:
            count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_bills').fetchone()[0]
            print(f"   ✅ FINAL_view_csv_json_bills: {count:,} records")
            
            # Get data source distribution
            cursor.execute('''
                SELECT 
                    data_source,
                    COUNT(*) as count
                FROM FINAL_view_csv_json_bills 
                GROUP BY data_source 
                ORDER BY count DESC
            ''')
            distribution = cursor.fetchall()
            
            print(f"   📊 Data Source Distribution:")
            for source, count in distribution:
                print(f"      {source}: {count:,} records")
                
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                print(f"   ❌ FINAL_view_csv_json_bills does not exist")
            else:
                print(f"   ❌ Error accessing FINAL_view_csv_json_bills: {e}")
        
        # Check what FINAL views DO exist
        print(f"\n📊 ALL FINAL VIEWS:")
        cursor.execute('SELECT name FROM sqlite_master WHERE type="view" AND name LIKE "FINAL_%" ORDER BY name')
        final_views = cursor.fetchall()
        
        if final_views:
            for (view_name,) in final_views:
                try:
                    count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
                    print(f"   ✅ {view_name}: {count:,} records")
                except Exception as e:
                    print(f"   ❌ {view_name}: ERROR - {e}")
        else:
            print(f"   ❌ No FINAL views found in database")
        
        # Check what bills views exist
        print(f"\n📋 ALL BILLS VIEWS:")
        cursor.execute('SELECT name FROM sqlite_master WHERE type="view" AND name LIKE "%bills%" ORDER BY name')
        bills_views = cursor.fetchall()
        
        if bills_views:
            for (view_name,) in bills_views:
                try:
                    count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
                    print(f"   ✅ {view_name}: {count:,} records")
                except Exception as e:
                    print(f"   ❌ {view_name}: ERROR - {e}")
        else:
            print(f"   ❌ No bills views found in database")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    main()
