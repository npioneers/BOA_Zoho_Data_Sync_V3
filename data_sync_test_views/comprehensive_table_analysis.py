#!/usr/bin/env python3
"""
Comprehensive Analysis: Check All Tables for Distribution Patterns
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 COMPREHENSIVE TABLE ANALYSIS")
print("=" * 80)

# Get all CSV+JSON integration views
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='view' 
    AND name LIKE 'view_csv_json_%'
    AND name NOT LIKE '%_v2'
    AND name NOT LIKE '%_v3'
    AND name NOT LIKE '%_deduplicated'
    AND name NOT LIKE '%_summary'
    ORDER BY name
""")
integration_views = [row[0] for row in cursor.fetchall()]

print(f"📊 FOUND {len(integration_views)} INTEGRATION VIEWS TO ANALYZE:")
for view in integration_views:
    print(f"   • {view}")
print()

# Analyze each view
for view in integration_views:
    table_name = view.replace('view_csv_json_', '')
    csv_table = f"csv_{table_name}"
    json_table = f"json_{table_name}"
    
    print(f"🔍 ANALYZING: {view}")
    print(f"   Tables: {csv_table} + {json_table}")
    
    try:
        # Check if base tables exist
        cursor.execute(f"SELECT COUNT(*) FROM {csv_table}")
        csv_count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {json_table}")
        json_count = cursor.fetchone()[0]
        
        print(f"   📋 Base counts: CSV={csv_count:,}, JSON={json_count:,}")
        
        # Check view distribution
        try:
            cursor.execute(f"SELECT data_source, COUNT(*) FROM {view} GROUP BY data_source")
            distribution = dict(cursor.fetchall())
            
            total_view = sum(distribution.values())
            print(f"   📊 View total: {total_view:,}")
            
            for source, count in distribution.items():
                percentage = (count / total_view * 100) if total_view > 0 else 0
                print(f"      {source}: {count:,} ({percentage:.1f}%)")
            
            # Check for suspicious patterns
            source_base = csv_count + json_count
            if total_view > source_base * 2:
                expansion_ratio = total_view / source_base
                print(f"   ⚠️  MASSIVE EXPANSION: {expansion_ratio:.1f}x (likely line items)")
            
            # Check for "enhanced"/"json_precedence" patterns
            suspicious_sources = [s for s in distribution.keys() if 'enhanced' in s or 'json' in s and s != 'json']
            if suspicious_sources:
                print(f"   🤔 SUSPICIOUS SOURCES: {suspicious_sources}")
                
                # Get the view SQL to understand the join
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{view}'")
                view_sql = cursor.fetchone()[0]
                
                # Look for join conditions
                if 'LEFT JOIN' in view_sql.upper():
                    # Extract the join condition
                    lines = view_sql.split('\n')
                    join_lines = [line.strip() for line in lines if 'LEFT JOIN' in line.upper() or 'ON ' in line.upper()]
                    if join_lines:
                        print(f"   🔗 Join logic: {join_lines[-1][:60]}...")
        
        except Exception as view_error:
            print(f"   ❌ View error: {view_error}")
            
    except Exception as table_error:
        print(f"   ❌ Table error: {table_error}")
    
    print()

# Special check for flat JSON views that might be involved
print("🔍 CHECKING FLAT JSON VIEWS:")
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='view' 
    AND name LIKE 'view_flat_json_%'
    ORDER BY name
""")
flat_views = [row[0] for row in cursor.fetchall()]

for flat_view in flat_views:
    try:
        cursor.execute(f"SELECT COUNT(*), COUNT(DISTINCT bill_id) FROM {flat_view}")
        result = cursor.fetchone()
        total, unique = result
        if unique and unique > 0:
            expansion = total / unique
            print(f"   {flat_view}: {total:,} records, {unique:,} unique bills ({expansion:.1f}x expansion)")
    except:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {flat_view}")
            total = cursor.fetchone()[0]
            print(f"   {flat_view}: {total:,} records (no bill_id column)")
        except Exception as e:
            print(f"   {flat_view}: Error - {e}")

conn.close()

print("\n🎯 ANALYSIS COMPLETE!")
print("Look for patterns:")
print("✅ Normal: view records ≈ base table totals")
print("⚠️ Expansion: view records >> base tables (line items)")
print("🤔 Enhanced: 'enhanced'/'json_precedence' labels (investigate)")
print("❌ Errors: Missing tables or column mapping issues")
