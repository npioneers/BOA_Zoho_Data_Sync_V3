#!/usr/bin/env python3
"""
Verify the fixed FINAL views and generate status report
"""

import sqlite3
import os
from datetime import datetime

def verify_fixed_views():
    """Verify that the FINAL views are now working and populated"""
    
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 FINAL VIEWS STATUS VERIFICATION")
        print("=" * 50)
        print(f"📅 Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get all FINAL views
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view' AND name LIKE 'FINAL_view_%' 
            ORDER BY name
        """)
        
        final_views = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Found {len(final_views)} FINAL views")
        print("-" * 30)
        
        total_records = 0
        populated_views = 0
        empty_views = 0
        
        for view_name in final_views:
            try:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM `{view_name}`")
                row_count = cursor.fetchone()[0]
                
                # Status indicator
                if row_count > 0:
                    status = "✅"
                    populated_views += 1
                    total_records += row_count
                else:
                    status = "❌"
                    empty_views += 1
                
                # Format row count
                formatted_count = f"{row_count:,}" if row_count > 0 else "0"
                
                print(f"{status} {view_name}: {formatted_count} rows")
                
                # Show sample data for populated views
                if row_count > 0 and row_count <= 10:
                    cursor.execute(f"SELECT * FROM `{view_name}` LIMIT 3")
                    samples = cursor.fetchall()
                    if samples:
                        print(f"    📋 Sample: {len(samples)} record(s)")
                        for i, sample in enumerate(samples[:2], 1):
                            # Show first few fields only
                            sample_str = str(sample[:5]) + "..." if len(sample) > 5 else str(sample)
                            print(f"      {i}. {sample_str}")
                        print()
                
            except Exception as e:
                print(f"❌ {view_name}: Error - {str(e)}")
                empty_views += 1
        
        print("\n🎯 SUMMARY STATISTICS")
        print("=" * 30)
        print(f"📊 Total FINAL views: {len(final_views)}")
        print(f"✅ Populated views: {populated_views}")
        print(f"❌ Empty views: {empty_views}")
        print(f"📈 Total records: {total_records:,}")
        
        if empty_views == 0:
            print("\n🎉 SUCCESS: All FINAL views are now populated!")
        elif empty_views < len(final_views):
            print(f"\n⚠️  PARTIAL SUCCESS: {populated_views}/{len(final_views)} views populated")
        else:
            print("\n❌ ISSUE: All views are still empty")
        
        # Check for specific previously empty views
        print("\n📋 PREVIOUSLY EMPTY VIEWS STATUS:")
        print("-" * 40)
        
        key_views = [
            'FINAL_view_csv_json_contacts',
            'FINAL_view_csv_json_items', 
            'FINAL_view_csv_json_sales_orders'
        ]
        
        for view in key_views:
            if view in final_views:
                cursor.execute(f"SELECT COUNT(*) FROM `{view}`")
                count = cursor.fetchone()[0]
                status = "✅ FIXED" if count > 0 else "❌ STILL EMPTY"
                print(f"{status} {view}: {count:,} rows")
            else:
                print(f"❓ {view}: View not found")
        
        conn.close()
        
        print(f"\n✅ Verification completed at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    verify_fixed_views()
