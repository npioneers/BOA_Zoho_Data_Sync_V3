#!/usr/bin/env python3
"""
Database Table Inspection Tool
Check what tables exist and their population status in the production database
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the json2db_sync package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_database_path():
    """Get the production database path"""
    return Path("../data/database/production.db")

def inspect_database():
    """Inspect database structure and content"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("🔍 DATABASE INSPECTION REPORT")
    print("=" * 80)
    print(f"📁 Database: {db_path.absolute()}")
    print(f"📊 Size: {db_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in database")
            return False
        
        print(f"📋 Found {len(tables)} tables:")
        print()
        
        table_info = []
        
        for (table_name,) in tables:
            if table_name.startswith('sqlite_'):
                continue  # Skip system tables
                
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get sample data (first 3 records)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = cursor.fetchall()
            
            table_info.append({
                'name': table_name,
                'columns': columns,
                'count': count,
                'sample': sample_data
            })
        
        # Sort by record count (descending)
        table_info.sort(key=lambda x: x['count'], reverse=True)
        
        # Display table summary
        print("📊 TABLE POPULATION SUMMARY")
        print("-" * 80)
        print(f"{'Table Name':<25} {'Records':<10} {'Columns':<8} {'Status'}")
        print("-" * 80)
        
        total_records = 0
        populated_tables = 0
        
        for info in table_info:
            status = "✅ Populated" if info['count'] > 0 else "❌ Empty"
            if info['count'] > 0:
                populated_tables += 1
            total_records += info['count']
            
            print(f"{info['name']:<25} {info['count']:<10} {len(info['columns']):<8} {status}")
        
        print("-" * 80)
        print(f"📈 Summary: {populated_tables}/{len(table_info)} tables populated, {total_records:,} total records")
        print()
        
        # Display detailed table information
        print("🔍 DETAILED TABLE ANALYSIS")
        print("=" * 80)
        
        for info in table_info:
            print(f"\n📋 Table: {info['name']}")
            print(f"   📊 Records: {info['count']:,}")
            print(f"   📝 Columns: {len(info['columns'])}")
            
            if info['columns']:
                print("   🏗️ Schema:")
                for col in info['columns'][:5]:  # Show first 5 columns
                    col_id, col_name, col_type, not_null, default, pk = col
                    pk_indicator = " (PK)" if pk else ""
                    null_indicator = " NOT NULL" if not_null else ""
                    print(f"      - {col_name}: {col_type}{pk_indicator}{null_indicator}")
                
                if len(info['columns']) > 5:
                    print(f"      ... and {len(info['columns']) - 5} more columns")
            
            if info['sample'] and info['count'] > 0:
                print("   📄 Sample Data:")
                col_names = [col[1] for col in info['columns']]
                
                for i, row in enumerate(info['sample'][:2]):  # Show first 2 rows
                    print(f"      Row {i+1}:")
                    for j, value in enumerate(row[:3]):  # Show first 3 columns
                        if j < len(col_names):
                            col_name = col_names[j]
                            # Truncate long values
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:47] + "..."
                            print(f"        {col_name}: {value}")
                    if len(row) > 3:
                        print(f"        ... and {len(row) - 3} more fields")
                    print()
        
        # Check for specific Zoho modules
        print("\n🎯 ZOHO MODULE ANALYSIS")
        print("=" * 80)
        
        zoho_modules = [
            'invoices', 'bills', 'contacts', 'items', 'salesorders', 
            'creditnotes', 'customerpayments', 'vendorpayments'
        ]
        
        found_modules = []
        missing_modules = []
        
        for module in zoho_modules:
            table_exists = any(info['name'].lower() == module.lower() for info in table_info)
            if table_exists:
                table_data = next((info for info in table_info if info['name'].lower() == module.lower()), None)
                if table_data:
                    found_modules.append((module, table_data['count']))
            else:
                missing_modules.append(module)
        
        if found_modules:
            print("✅ Found Zoho Module Tables:")
            for module, count in found_modules:
                print(f"   📊 {module}: {count:,} records")
        
        if missing_modules:
            print("\n❌ Missing Zoho Module Tables:")
            for module in missing_modules:
                print(f"   📭 {module}: Not found")
        
        # Check for line items tables
        print("\n📋 LINE ITEMS ANALYSIS")
        print("-" * 40)
        
        line_item_tables = [info for info in table_info if 'line_items' in info['name'].lower()]
        
        if line_item_tables:
            print("✅ Found Line Items Tables:")
            for info in line_item_tables:
                print(f"   📊 {info['name']}: {info['count']:,} records")
        else:
            print("❌ No line items tables found")
        
        # Check data freshness
        print("\n⏰ DATA FRESHNESS CHECK")
        print("-" * 40)
        
        # Look for timestamp columns in populated tables
        for info in table_info:
            if info['count'] > 0:
                # Check for common timestamp column names
                timestamp_cols = []
                for col in info['columns']:
                    col_name = col[1].lower()
                    if any(keyword in col_name for keyword in ['modified', 'updated', 'created', 'time', 'date']):
                        timestamp_cols.append(col[1])
                
                if timestamp_cols:
                    # Get latest timestamp from the first timestamp column
                    try:
                        cursor.execute(f"SELECT MAX({timestamp_cols[0]}) FROM {info['name']}")
                        latest = cursor.fetchone()[0]
                        if latest:
                            print(f"   📅 {info['name']}: Latest record - {latest}")
                    except:
                        pass  # Skip if there's an error with the timestamp column
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database inspection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main inspection function"""
    print("🔍 Production Database Table Inspection")
    print(f"⏰ Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = inspect_database()
    
    if success:
        print("\n✅ Database inspection completed successfully!")
    else:
        print("\n❌ Database inspection failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
