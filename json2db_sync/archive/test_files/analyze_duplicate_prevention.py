#!/usr/bin/env python3
"""
Duplicate Prevention Analysis and Testing Tool
Analyzes current duplicate prevention mechanisms and creates enhanced safeguards
"""

import sqlite3
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple

# Add the json2db_sync package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_table_constraints():
    """Analyze current table constraints and primary key definitions"""
    db_path = Path("../data/database/production.db")
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🔍 DUPLICATE PREVENTION ANALYSIS")
    print("=" * 80)
    print(f"📁 Database: {db_path.absolute()}")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all JSON tables (our main concern for duplicates)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%' ORDER BY name")
        json_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Analyzing {len(json_tables)} JSON tables for duplicate prevention...")
        print()
        
        for table_name in json_tables:
            print(f"🔍 Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Find primary keys
            primary_keys = []
            for col in columns:
                col_id, col_name, col_type, not_null, default, is_pk = col
                if is_pk:
                    primary_keys.append((col_name, col_type))
            
            if primary_keys:
                print(f"   ✅ Primary Keys: {', '.join([f'{name} ({type_})' for name, type_ in primary_keys])}")
            else:
                print(f"   ❌ No primary keys found!")
            
            # Get unique constraints
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            create_sql = result[0] if result else ""
            
            if "UNIQUE" in create_sql.upper():
                print(f"   ✅ Has UNIQUE constraints")
            else:
                print(f"   ⚠️ No UNIQUE constraints")
            
            # Check for potential duplicate indicators
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            
            if primary_keys and total_count > 0:
                # Test for actual duplicates by checking if distinct PK count matches total
                pk_names = [pk[0] for pk in primary_keys]
                pk_columns = ", ".join(pk_names)
                
                cursor.execute(f"SELECT COUNT(DISTINCT {pk_columns}) FROM {table_name}")
                distinct_pk_count = cursor.fetchone()[0]
                
                if distinct_pk_count == total_count:
                    print(f"   ✅ No duplicates: {total_count} total = {distinct_pk_count} distinct")
                else:
                    duplicates = total_count - distinct_pk_count
                    print(f"   ❌ Found {duplicates} duplicate records ({total_count} total vs {distinct_pk_count} distinct)")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

def test_insert_or_replace_behavior():
    """Test INSERT OR REPLACE behavior with sample data"""
    print("\n🧪 TESTING INSERT OR REPLACE BEHAVIOR")
    print("=" * 80)
    
    # Create a temporary test database
    test_db = Path("test_duplicate_prevention.db")
    
    try:
        # Clean up any existing test database
        if test_db.exists():
            test_db.unlink()
        
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        
        # Create a test table with composite primary key (similar to our JSON tables)
        cursor.execute("""
            CREATE TABLE test_invoices (
                invoice_id INTEGER,
                customer_id INTEGER,
                invoice_number VARCHAR(50),
                total DECIMAL(15,2),
                status VARCHAR(100),
                last_modified_time DATETIME,
                PRIMARY KEY (invoice_id, customer_id)
            )
        """)
        
        print("✅ Created test table with composite primary key")
        
        # Test 1: Insert initial records
        test_data = [
            (1001, 2001, "INV-001", 1500.00, "paid", "2025-07-11 10:00:00"),
            (1002, 2002, "INV-002", 2500.00, "pending", "2025-07-11 11:00:00"),
            (1003, 2003, "INV-003", 750.00, "draft", "2025-07-11 12:00:00")
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO test_invoices 
            (invoice_id, customer_id, invoice_number, total, status, last_modified_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, test_data)
        
        cursor.execute("SELECT COUNT(*) FROM test_invoices")
        count = cursor.fetchone()[0]
        print(f"✅ Inserted {count} initial records")
        
        # Test 2: Insert duplicate with updated data (should replace)
        updated_data = [
            (1001, 2001, "INV-001", 1750.00, "paid", "2025-07-11 15:00:00"),  # Same PK, updated amount and time
            (1004, 2004, "INV-004", 3000.00, "pending", "2025-07-11 16:00:00")  # New record
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO test_invoices 
            (invoice_id, customer_id, invoice_number, total, status, last_modified_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, updated_data)
        
        cursor.execute("SELECT COUNT(*) FROM test_invoices")
        count_after_update = cursor.fetchone()[0]
        print(f"✅ After update/insert: {count_after_update} records (should be 4, not 5)")
        
        # Check if the record was updated, not duplicated
        cursor.execute("SELECT total, last_modified_time FROM test_invoices WHERE invoice_id=1001 AND customer_id=2001")
        updated_record = cursor.fetchone()
        
        if updated_record and updated_record[0] == 1750.00:
            print(f"✅ Record properly updated: total={updated_record[0]}, time={updated_record[1]}")
        else:
            print(f"❌ Record update failed: {updated_record}")
        
        # Test 3: Attempt to insert same data again (should not increase count)
        cursor.executemany("""
            INSERT OR REPLACE INTO test_invoices 
            (invoice_id, customer_id, invoice_number, total, status, last_modified_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, test_data + updated_data)
        
        cursor.execute("SELECT COUNT(*) FROM test_invoices")
        final_count = cursor.fetchone()[0]
        print(f"✅ After re-running same inserts: {final_count} records (should still be 4)")
        
        if final_count == 4:
            print("🎉 INSERT OR REPLACE working correctly - no duplicates created!")
        else:
            print(f"❌ Unexpected count: {final_count} (expected 4)")
        
        conn.close()
        
        # Clean up test database
        test_db.unlink()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up on error
        if test_db.exists():
            test_db.unlink()

def analyze_session_tracking_gaps():
    """Analyze potential gaps in session tracking that could lead to duplicates"""
    print("\n📊 SESSION TRACKING ANALYSIS")
    print("=" * 80)
    
    # Check if we have session tracking in place
    try:
        from json2db_config import JSON2DBSyncConfig
        
        config = JSON2DBSyncConfig()
        latest_session = config.get_latest_session_folder()
        
        if latest_session:
            print(f"✅ Latest session detected: {latest_session}")
            
            # Check if we track which sessions have been processed
            print("🔍 Checking for session processing tracking...")
            
            # This would be in a tracking table or file
            db_path = Path(config.get_database_path())
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Check if we have a session tracking table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_tracking'")
                tracking_table = cursor.fetchone()
                
                if tracking_table:
                    print("✅ Session tracking table exists")
                    cursor.execute("SELECT COUNT(*) FROM session_tracking")
                    tracked_sessions = cursor.fetchone()[0]
                    print(f"   📊 {tracked_sessions} sessions tracked")
                else:
                    print("❌ No session tracking table found")
                    print("   ⚠️ This could lead to reprocessing same data multiple times")
                
                conn.close()
            
        else:
            print("❌ No sessions found")
            
    except Exception as e:
        print(f"❌ Session tracking analysis failed: {e}")

def create_enhanced_duplicate_prevention():
    """Create enhanced duplicate prevention mechanisms"""
    print("\n🛡️ ENHANCED DUPLICATE PREVENTION RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = [
        {
            "issue": "Session Reprocessing",
            "solution": "Implement session tracking table",
            "priority": "HIGH",
            "description": "Track which sessions have been processed to avoid reprocessing"
        },
        {
            "issue": "Data Source Identification",
            "solution": "Add data_source and session_id columns",
            "priority": "MEDIUM", 
            "description": "Track where each record came from for better debugging"
        },
        {
            "issue": "Last Modified Tracking",
            "solution": "Implement upsert logic based on last_modified_time",
            "priority": "MEDIUM",
            "description": "Only update records if source data is newer"
        },
        {
            "issue": "Batch Processing Safety",
            "solution": "Add transaction rollback on errors",
            "priority": "HIGH",
            "description": "Ensure partial failures don't leave corrupted state"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['issue']} [{rec['priority']}]")
        print(f"   Solution: {rec['solution']}")
        print(f"   Details: {rec['description']}")
        print()

def main():
    """Run comprehensive duplicate prevention analysis"""
    print("🛡️ DUPLICATE PREVENTION ANALYSIS AND ENHANCEMENT")
    print(f"⏰ Analysis run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all analysis functions
    analyze_table_constraints()
    test_insert_or_replace_behavior()
    analyze_session_tracking_gaps()
    create_enhanced_duplicate_prevention()
    
    print("\n✅ Duplicate prevention analysis completed!")

if __name__ == "__main__":
    main()
