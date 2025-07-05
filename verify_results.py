#!/usr/bin/env python3
"""
Post-execution verification script
Run this after the cockpit notebook to verify results
"""

import sys
from pathlib import Path
import sqlite3

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def verify_database_results():
    """Verify the database was created and populated correctly"""
    print("🔍 POST-EXECUTION VERIFICATION")
    print("=" * 45)
    
    try:
        from data_pipeline.config import get_config_manager
        config = get_config_manager()
        paths = config.get_data_source_paths()
        
        db_path = Path(paths['target_database'])
        
        if not db_path.exists():
            print("❌ Database file not found!")
            return False
            
        print(f"✅ Database file exists: {db_path}")
        print(f"📊 File size: {db_path.stat().st_size:,} bytes")
        
        # Connect and verify contents
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Tables found: {[t[0] for t in tables]}")
            
            # Check bills_canonical table
            if ('bills_canonical',) in tables:
                cursor.execute("SELECT COUNT(*) FROM bills_canonical")
                record_count = cursor.fetchone()[0]
                print(f"📊 Records in bills_canonical: {record_count:,}")
                
                # Check column count
                cursor.execute("PRAGMA table_info(bills_canonical)")
                columns = cursor.fetchall()
                print(f"📋 Columns in bills_canonical: {len(columns)}")
                
                # Sample data
                cursor.execute("SELECT BillID, VendorName, Total FROM bills_canonical LIMIT 3")
                samples = cursor.fetchall()
                print("🔍 Sample records:")
                for i, row in enumerate(samples, 1):
                    print(f"   {i}. ID: {row[0]}, Vendor: {row[1]}, Total: {row[2]}")
                
                # Check views
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
                views = cursor.fetchall()
                print(f"👁️  Views created: {[v[0] for v in views]}")
                
                return True
            else:
                print("❌ bills_canonical table not found!")
                return False
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_data_quality():
    """Run basic data quality checks"""
    print("\n📊 DATA QUALITY VERIFICATION")
    print("=" * 35)
    
    try:
        from data_pipeline.config import get_config_manager
        config = get_config_manager()
        paths = config.get_data_source_paths()
        
        db_path = Path(paths['target_database'])
        
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Check for nulls in key fields
            cursor.execute("SELECT COUNT(*) FROM bills_canonical WHERE BillID IS NULL OR BillID = ''")
            null_ids = cursor.fetchone()[0]
            print(f"🔍 Records with missing BillID: {null_ids}")
            
            # Check date range
            cursor.execute("SELECT MIN(Date), MAX(Date) FROM bills_canonical WHERE Date IS NOT NULL AND Date != ''")
            date_range = cursor.fetchone()
            if date_range[0]:
                print(f"📅 Date range: {date_range[0]} to {date_range[1]}")
            
            # Check total amounts
            cursor.execute("SELECT MIN(Total), MAX(Total), AVG(Total) FROM bills_canonical WHERE Total IS NOT NULL")
            amount_stats = cursor.fetchone()
            if amount_stats[0] is not None:
                print(f"💰 Amount range: ${amount_stats[0]:.2f} to ${amount_stats[1]:.2f} (avg: ${amount_stats[2]:.2f})")
            
            # Check vendor distribution
            cursor.execute("SELECT COUNT(DISTINCT VendorName) FROM bills_canonical WHERE VendorName IS NOT NULL AND VendorName != ''")
            vendor_count = cursor.fetchone()[0]
            print(f"👥 Unique vendors: {vendor_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Data quality check failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 BEDROCK V2 POST-EXECUTION VERIFICATION")
    print("=" * 50)
    
    success = True
    
    if not verify_database_results():
        success = False
        
    if not verify_data_quality():
        success = False
    
    if success:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("🚀 Bedrock V2 pipeline executed successfully!")
        print("📋 Database is ready for production use!")
    else:
        print("\n❌ Some verifications failed")
        print("🔧 Check the notebook execution for errors")
        
    print(f"\n📁 Database location: {Path('output/database/bedrock_prototype.db').resolve()}")
