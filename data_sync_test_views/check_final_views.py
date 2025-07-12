#!/usr/bin/env python3
"""
Check status of FINAL views in the database
"""

import sqlite3
import sys
import os

def check_final_views():
    """Check all FINAL views and specifically look for bills FINAL view"""
    
    db_path = '../data/business_data.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        print('🔍 CHECKING ALL FINAL VIEWS STATUS')
        print('='*50)

        # Get all views that start with FINAL
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'FINAL_%' ORDER BY name")
        final_views = cursor.fetchall()

        print(f'📊 FOUND {len(final_views)} FINAL VIEWS:')
        for view in final_views:
            view_name = view[0]
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
                print(f'   ✅ {view_name}: {count:,} records')
            except Exception as e:
                print(f'   ❌ {view_name}: ERROR - {e}')

        print(f'\n🔍 SPECIFICALLY CHECKING FOR BILLS FINAL VIEW:')
        # Check if any FINAL bills view exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%bills%' AND name LIKE 'FINAL%'")
        bills_finals = cursor.fetchall()
        if bills_finals:
            for view in bills_finals:
                print(f'   Found: {view[0]}')
        else:
            print('   ❌ No FINAL bills view found!')
            
        # Check what bills views DO exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%bills%' ORDER BY name")
        all_bills_views = cursor.fetchall()
        print(f'\n📋 ALL BILLS VIEWS THAT EXIST ({len(all_bills_views)} total):')
        for view in all_bills_views:
            view_name = view[0]
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
                print(f'   ✅ {view_name}: {count:,} records')
            except Exception as e:
                print(f'   ❌ {view_name}: ERROR - {e}')
                
        # Check if we need to create FINAL_view_csv_json_bills
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name = 'view_csv_json_bills'")
        base_view = cursor.fetchone()
        
        if base_view:
            print(f'\n💡 RECOMMENDATION:')
            print(f'   The base integration view "view_csv_json_bills" exists')
            print(f'   We should create "FINAL_view_csv_json_bills" based on it')
            print(f'   This would implement our CSV-preferred strategy for bills')
        else:
            print(f'\n⚠️ WARNING: Base view "view_csv_json_bills" not found!')

        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_final_views()
