#!/usr/bin/env python3
"""
Debug the freshness check step by step
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add global_runner to path
sys.path.append(str(Path(__file__).parent))

from runner_zoho_data_sync import GlobalSyncRunner

def debug_freshness_check():
    print("DEBUGGING FRESHNESS CHECK STEP BY STEP")
    print("=" * 60)
    
    runner = GlobalSyncRunner(enable_logging=False)
    
    # Manually recreate the freshness check logic with debug info
    db_path = runner.config.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables_to_check = runner.config.get_freshness_tables()
    threshold_days = runner.config.get('sync_pipeline.freshness_threshold_days', 1)
    cutoff_date = datetime.now() - timedelta(days=threshold_days)
    
    print(f"Database: {db_path}")
    print(f"Threshold days: {threshold_days}")
    print(f"Cutoff date: {cutoff_date}")
    print(f"Tables to check: {tables_to_check}")
    
    for table_name in tables_to_check:
        print(f"\n{'='*20} {table_name} {'='*20}")
        
        try:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"❌ Table does not exist")
                continue
            
            print(f"✅ Table exists")
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            record_count = cursor.fetchone()[0]
            print(f"📊 Record count: {record_count:,}")
            
            if record_count == 0:
                print(f"⚠️ Table is empty")
                continue
            
            # Get date column from config
            date_column = runner.config.get_date_column_for_table(table_name)
            print(f"🔧 Config date column: {date_column}")
            
            columns = None
            if not date_column:
                # Try common date columns
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"📋 Table columns: {columns[:5]}{'...' if len(columns) > 5 else ''}")
                date_column = runner._find_best_date_column(columns)
                print(f"🎯 Best date column detected: {date_column}")
            
            # If we still don't have columns, get them now
            if not columns:
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"📋 Retrieved columns: {columns[:5]}{'...' if len(columns) > 5 else ''}")
            
            print(f"🔍 Final date column: {date_column}")
            print(f"🔍 Date column in table: {date_column in columns if date_column and columns else 'N/A'}")
            
            if date_column and date_column in columns:
                print(f"✅ Date column '{date_column}' found in table")
                
                # Get latest date
                cursor.execute(f"SELECT MAX(`{date_column}`) FROM `{table_name}` WHERE `{date_column}` IS NOT NULL")
                latest_date_str = cursor.fetchone()[0]
                print(f"📅 Latest date string: '{latest_date_str}'")
                
                if latest_date_str:
                    try:
                        # Handle different date formats
                        latest_date = runner._parse_date(latest_date_str)
                        days_old = (datetime.now() - latest_date).days
                        print(f"✅ Date parsed successfully: {latest_date}")
                        print(f"📆 Days old: {days_old}")
                        
                        status = "fresh" if latest_date >= cutoff_date else "stale"
                        print(f"🏷️ Status: {status}")
                        
                    except Exception as e:
                        print(f"❌ Date parsing failed: {e}")
                        print(f"🏷️ Status: date_error")
                else:
                    print(f"⚠️ No date values found")
                    print(f"🏷️ Status: no_dates")
            else:
                print(f"❌ No suitable date column found")
                print(f"🏷️ Status: no_date_column")
                
        except Exception as e:
            print(f"💥 Error processing {table_name}: {e}")
    
    conn.close()

if __name__ == "__main__":
    debug_freshness_check()
