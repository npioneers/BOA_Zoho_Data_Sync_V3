#!/usr/bin/env python3
"""
Comprehensive scan to find any missing FINAL views we might have overlooked
"""

import sqlite3
import os

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 COMPREHENSIVE FINAL VIEWS COMPLETENESS AUDIT')
    print('='*70)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Get all integration views that should have corresponding FINAL views
    print("📋 STEP 1: FINDING ALL INTEGRATION VIEWS")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'view_csv_json_%' ORDER BY name")
    integration_views = cursor.fetchall()
    
    print(f"   Found {len(integration_views)} integration views:")
    for view in integration_views:
        view_name = view[0]
        table_name = view_name.replace('view_csv_json_', '')
        print(f"   • {view_name} → should have FINAL_view_csv_json_{table_name}")
    
    # 2. Get all existing FINAL views
    print(f"\n📊 STEP 2: CHECKING EXISTING FINAL VIEWS")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'FINAL_view_csv_json_%' ORDER BY name")
    final_views = cursor.fetchall()
    
    print(f"   Found {len(final_views)} existing FINAL views:")
    for view in final_views:
        view_name = view[0]
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
            print(f"   ✅ {view_name}: {count:,} records")
        except Exception as e:
            print(f"   ❌ {view_name}: ERROR - {e}")
    
    # 3. Cross-reference to find missing FINAL views
    print(f"\n🔍 STEP 3: CROSS-REFERENCE ANALYSIS")
    
    expected_final_views = []
    existing_final_view_names = [view[0] for view in final_views]
    
    missing_final_views = []
    
    for integration_view in integration_views:
        integration_name = integration_view[0]
        table_name = integration_name.replace('view_csv_json_', '')
        expected_final_name = f"FINAL_view_csv_json_{table_name}"
        expected_final_views.append(expected_final_name)
        
        if expected_final_name not in existing_final_view_names:
            missing_final_views.append((table_name, integration_name, expected_final_name))
    
    print(f"   Expected FINAL views: {len(expected_final_views)}")
    print(f"   Existing FINAL views: {len(existing_final_view_names)}")
    print(f"   Missing FINAL views: {len(missing_final_views)}")
    
    # 4. Report missing FINAL views
    if missing_final_views:
        print(f"\n❌ STEP 4: MISSING FINAL VIEWS FOUND")
        for table_name, integration_name, expected_final_name in missing_final_views:
            print(f"   Missing: {expected_final_name}")
            print(f"   Source: {integration_name}")
            
            # Check if integration view has records
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM `{integration_name}`').fetchone()[0]
                print(f"   Source records: {count:,}")
                print(f"   🔨 Should create this FINAL view!")
            except Exception as e:
                print(f"   ❌ Source view error: {e}")
            print()
    else:
        print(f"\n✅ STEP 4: NO MISSING FINAL VIEWS FOUND!")
        print(f"   All integration views have corresponding FINAL views")
    
    # 5. Check for any other potential patterns
    print(f"\n🔍 STEP 5: CHECKING FOR OTHER VIEW PATTERNS")
    
    # Check for any versioned integration views (v2, v3, etc.)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND (name LIKE 'view_csv_json_%_v%' OR name LIKE 'view_csv_json_%_deduplicated') ORDER BY name")
    versioned_views = cursor.fetchall()
    
    if versioned_views:
        print(f"   Found {len(versioned_views)} versioned integration views:")
        for view in versioned_views:
            view_name = view[0]
            # Extract table name from versioned view
            if '_v' in view_name:
                base_name = view_name.split('_v')[0]
                table_name = base_name.replace('view_csv_json_', '')
            elif '_deduplicated' in view_name:
                base_name = view_name.replace('_deduplicated', '')
                table_name = base_name.replace('view_csv_json_', '')
            
            expected_final_name = f"FINAL_view_csv_json_{table_name}"
            
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM `{view_name}`').fetchone()[0]
                print(f"   • {view_name}: {count:,} records")
                
                # Check if this might be a better source than the base integration view
                if expected_final_name in existing_final_view_names:
                    final_count = conn.execute(f'SELECT COUNT(*) FROM `{expected_final_name}`').fetchone()[0]
                    if count != final_count:
                        print(f"     ⚠️ FINAL view has {final_count:,} records - different from this version!")
                else:
                    print(f"     💡 Could create {expected_final_name} from this version")
                    
            except Exception as e:
                print(f"   ❌ {view_name}: ERROR - {e}")
    else:
        print(f"   No versioned integration views found")
    
    # 6. Check for any tables that might need FINAL views but don't have integration views
    print(f"\n🔍 STEP 6: CHECKING BASE TABLES WITHOUT INTEGRATION VIEWS")
    
    # Get all CSV tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%' ORDER BY name")
    csv_tables = cursor.fetchall()
    
    # Get all JSON tables  
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%' ORDER BY name")
    json_tables = cursor.fetchall()
    
    csv_table_names = [table[0].replace('csv_', '') for table in csv_tables]
    json_table_names = [table[0].replace('json_', '') for table in json_tables]
    
    # Find tables that exist but don't have integration views
    all_table_names = set(csv_table_names + json_table_names)
    integration_table_names = [view[0].replace('view_csv_json_', '') for view in integration_views]
    
    missing_integration_tables = all_table_names - set(integration_table_names)
    
    if missing_integration_tables:
        print(f"   Found {len(missing_integration_tables)} tables without integration views:")
        for table_name in sorted(missing_integration_tables):
            csv_exists = f'csv_{table_name}' in [table[0] for table in csv_tables]
            json_exists = f'json_{table_name}' in [table[0] for table in json_tables]
            
            csv_count = 0
            json_count = 0
            
            if csv_exists:
                try:
                    csv_count = conn.execute(f'SELECT COUNT(*) FROM csv_{table_name}').fetchone()[0]
                except:
                    pass
                    
            if json_exists:
                try:
                    json_count = conn.execute(f'SELECT COUNT(*) FROM json_{table_name}').fetchone()[0]
                except:
                    pass
            
            print(f"   • {table_name}: CSV={csv_count:,}, JSON={json_count:,}")
            if csv_count > 0 or json_count > 0:
                print(f"     💡 This table has data but no integration view!")
    else:
        print(f"   All tables with data have integration views")
    
    # 7. Final summary
    print(f"\n🎯 FINAL AUDIT SUMMARY:")
    print(f"   Integration views: {len(integration_views)}")
    print(f"   Existing FINAL views: {len(final_views)}")
    print(f"   Missing FINAL views: {len(missing_final_views)}")
    print(f"   Versioned views: {len(versioned_views)}")
    print(f"   Tables without integration: {len(missing_integration_tables) if 'missing_integration_tables' in locals() else 0}")
    
    if missing_final_views:
        print(f"\n🔨 ACTION REQUIRED:")
        print(f"   Need to create {len(missing_final_views)} missing FINAL views")
    else:
        print(f"\n✅ AUDIT RESULT: COMPLETE!")
        print(f"   All expected FINAL views exist")
    
    conn.close()
    
    print(f"\n" + "="*70)
    print(f"🎉 COMPREHENSIVE FINAL VIEWS AUDIT COMPLETE!")

if __name__ == "__main__":
    main()
