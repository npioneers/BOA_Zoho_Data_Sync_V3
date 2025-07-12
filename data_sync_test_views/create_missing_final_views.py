#!/usr/bin/env python3
"""
Create the 4 missing FINAL views discovered in the audit
"""

import sqlite3
import os

def create_missing_final_view(conn, source_view_name, final_view_name):
    """Create a missing FINAL view from its source view"""
    
    cursor = conn.cursor()
    
    try:
        # Check if source exists and get count
        source_count = conn.execute(f'SELECT COUNT(*) FROM `{source_view_name}`').fetchone()[0]
        print(f"   Source: {source_view_name} ({source_count:,} records)")
        
        # Check if FINAL already exists
        try:
            final_count = conn.execute(f'SELECT COUNT(*) FROM `{final_view_name}`').fetchone()[0]
            print(f"   ✅ {final_view_name} already exists ({final_count:,} records)")
            return True
        except:
            pass  # FINAL view doesn't exist, proceed to create
        
        # Create the FINAL view
        create_sql = f"""
        CREATE VIEW {final_view_name} AS
        SELECT * FROM `{source_view_name}`
        """
        
        cursor.execute(create_sql)
        
        # Verify creation
        final_count = conn.execute(f'SELECT COUNT(*) FROM `{final_view_name}`').fetchone()[0]
        print(f"   🔨 Created {final_view_name} ({final_count:,} records)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create {final_view_name}: {e}")
        return False

def main():
    db_path = '../data/database/production.db'
    
    print('🔨 CREATING MISSING FINAL VIEWS FROM AUDIT')
    print('='*60)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # List of missing FINAL views to create
    missing_views = [
        ('view_csv_json_bills_deduplicated', 'FINAL_view_csv_json_bills_deduplicated'),
        ('view_csv_json_bills_summary', 'FINAL_view_csv_json_bills_summary'),
        ('view_csv_json_bills_v2', 'FINAL_view_csv_json_bills_v2'),
        ('view_csv_json_bills_v3', 'FINAL_view_csv_json_bills_v3')
    ]
    
    print(f"📋 CREATING {len(missing_views)} MISSING FINAL VIEWS:")
    
    created_count = 0
    for source_view, final_view in missing_views:
        print(f"\n🔍 Processing {final_view}:")
        
        success = create_missing_final_view(conn, source_view, final_view)
        if success:
            created_count += 1
    
    # Get updated count of all FINAL views
    print(f"\n📊 UPDATED FINAL VIEWS INVENTORY:")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'FINAL_%' ORDER BY name")
    all_final_views = cursor.fetchall()
    
    total_records = 0
    for view in all_final_views:
        view_name = view[0]
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
            total_records += count
            print(f"   ✅ {view_name}: {count:,} records")
        except Exception as e:
            print(f"   ❌ {view_name}: ERROR - {e}")
    
    print(f"\n🎯 CREATION SUMMARY:")
    print(f"   Successfully created: {created_count}/{len(missing_views)} FINAL views")
    print(f"   Total FINAL views now: {len(all_final_views)}")
    print(f"   Total records across all FINAL views: {total_records:,}")
    
    # Check if there are any remaining integration views without FINAL views
    print(f"\n🔍 FINAL COMPLETENESS CHECK:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'view_csv_json_%' ORDER BY name")
    integration_views = cursor.fetchall()
    
    missing_final_count = 0
    for integration_view in integration_views:
        integration_name = integration_view[0]
        expected_final_name = integration_name.replace('view_csv_json_', 'FINAL_view_csv_json_')
        
        try:
            conn.execute(f'SELECT 1 FROM `{expected_final_name}` LIMIT 1')
            # FINAL view exists
        except:
            missing_final_count += 1
            print(f"   ⚠️ Still missing: {expected_final_name}")
    
    if missing_final_count == 0:
        print(f"   ✅ PERFECT! All integration views now have corresponding FINAL views")
    else:
        print(f"   ⚠️ Still missing {missing_final_count} FINAL views")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "="*60)
    print(f"🎉 MISSING FINAL VIEWS CREATION COMPLETE!")

if __name__ == "__main__":
    main()
