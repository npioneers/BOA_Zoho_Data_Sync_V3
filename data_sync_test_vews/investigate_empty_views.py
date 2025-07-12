#!/usr/bin/env python3
"""
Deep investigation of empty FINAL views to identify root causes
"""
import sqlite3
import os
from pathlib import Path

def investigate_empty_views():
    """Investigate why certain FINAL views are empty"""
    
    # Database path relative to this script
    db_path = Path("../data/database/production.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path.absolute()}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Empty views to investigate
        empty_views = [
            'FINAL_view_csv_json_contacts',
            'FINAL_view_csv_json_items', 
            'FINAL_view_csv_json_sales_orders'
        ]
        
        print("🔍 INVESTIGATING EMPTY FINAL VIEWS")
        print("=" * 80)
        
        for view_name in empty_views:
            print(f"\n📋 INVESTIGATING: {view_name}")
            print("-" * 60)
            
            # 1. Get the view definition
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (view_name,))
                view_sql = cursor.fetchone()
                
                if view_sql:
                    print(f"✅ View exists in database")
                    
                    # Extract and clean the SQL
                    sql_definition = view_sql[0]
                    
                    # Print formatted SQL for analysis
                    print(f"\n📝 View SQL Definition:")
                    formatted_sql = sql_definition.replace(" SELECT ", "\nSELECT ")
                    formatted_sql = formatted_sql.replace(" FROM ", "\nFROM ")
                    formatted_sql = formatted_sql.replace(" LEFT JOIN ", "\nLEFT JOIN ")
                    formatted_sql = formatted_sql.replace(" WHERE ", "\nWHERE ")
                    formatted_sql = formatted_sql.replace(" UNION ", "\nUNION ")
                    print(f"{formatted_sql}")
                    
                    # 2. Identify source tables from the view definition
                    source_tables = extract_table_names(sql_definition)
                    print(f"\n📊 Source Tables Identified: {source_tables}")
                    
                    # 3. Check if source tables exist and have data
                    for table_name in source_tables:
                        check_source_table(cursor, table_name)
                    
                    # 4. Try to understand why the view returns no data
                    analyze_view_logic(cursor, view_name, sql_definition)
                    
                else:
                    print(f"❌ View does not exist in database!")
                    
            except Exception as e:
                print(f"❌ Error investigating view: {e}")
            
            print("=" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

def extract_table_names(sql_definition):
    """Extract table names from SQL definition"""
    import re
    
    # Remove CREATE VIEW portion
    sql_upper = sql_definition.upper()
    
    # Find all table references after FROM and JOIN
    table_pattern = r'(?:FROM|JOIN)\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?'
    matches = re.findall(table_pattern, sql_upper)
    
    # Filter out duplicates and common SQL keywords
    tables = []
    for match in matches:
        if match.lower() not in ['select', 'where', 'order', 'group', 'having', 'union']:
            tables.append(match.lower())
    
    return list(set(tables))

def check_source_table(cursor, table_name):
    """Check if source table exists and has data"""
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            if row_count > 0:
                print(f"  ✅ {table_name}: {row_count:,} rows")
                
                # Get column info for understanding
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"     Columns: {', '.join(column_names[:10])}{'...' if len(column_names) > 10 else ''}")
                
                # Sample some data to understand content
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 2")
                sample_rows = cursor.fetchall()
                if sample_rows:
                    print(f"     Sample: {sample_rows[0][:5]}{'...' if len(sample_rows[0]) > 5 else ''}")
                    
            else:
                print(f"  ⚠️  {table_name}: EXISTS but EMPTY (0 rows)")
        else:
            print(f"  ❌ {table_name}: TABLE DOES NOT EXIST")
            
    except Exception as e:
        print(f"  ❌ {table_name}: Error checking table - {e}")

def analyze_view_logic(cursor, view_name, sql_definition):
    """Analyze why the view might be returning no data"""
    print(f"\n🔍 Logic Analysis for {view_name}:")
    
    try:
        # Check for WHERE conditions that might be filtering out all data
        if "WHERE" in sql_definition.upper():
            print("  📝 View contains WHERE conditions - potential filtering issue")
            
        # Check for JOINs that might be causing data loss
        join_types = []
        if "LEFT JOIN" in sql_definition.upper():
            join_types.append("LEFT JOIN")
        if "INNER JOIN" in sql_definition.upper() or " JOIN " in sql_definition.upper():
            join_types.append("INNER JOIN")
            
        if join_types:
            print(f"  🔗 View contains {', '.join(join_types)} - potential JOIN issues")
            
        # Check for UNION that might be causing issues
        if "UNION" in sql_definition.upper():
            print("  🔄 View contains UNION - check if all parts return data")
            
        # Try to execute parts of the query to isolate the issue
        print("  🧪 Testing query execution...")
        
        # Simple test - try to get EXPLAIN QUERY PLAN
        try:
            cursor.execute(f"EXPLAIN QUERY PLAN SELECT * FROM `{view_name}` LIMIT 1")
            query_plan = cursor.fetchall()
            print("  ✅ Query plan generated successfully - syntax is valid")
            for step in query_plan:
                print(f"     {step}")
        except Exception as e:
            print(f"  ❌ Query plan failed: {e}")
            
    except Exception as e:
        print(f"  ❌ Logic analysis failed: {e}")

def check_related_patterns():
    """Check for patterns across all tables that might explain empty views"""
    db_path = Path("../data/database/production.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print(f"\n🔍 CHECKING RELATED DATA PATTERNS")
        print("=" * 80)
        
        # Check all tables that might be related to contacts, items, sales_orders
        related_patterns = {
            'contacts': ['contact', 'customer', 'vendor'],
            'items': ['item', 'product', 'inventory'],
            'sales_orders': ['sales', 'order', 'salesorder']
        }
        
        for category, patterns in related_patterns.items():
            print(f"\n📊 Tables related to {category.upper()}:")
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Find matching tables
            matching_tables = []
            for table in all_tables:
                for pattern in patterns:
                    if pattern.lower() in table.lower():
                        matching_tables.append(table)
                        break
            
            if matching_tables:
                for table in matching_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = cursor.fetchone()[0]
                    status = "✅" if count > 0 else "❌"
                    print(f"  {status} {table}: {count:,} rows")
            else:
                print(f"  ❌ No tables found matching patterns: {patterns}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking related patterns: {e}")

if __name__ == "__main__":
    print("🚀 DEEP INVESTIGATION: Empty FINAL Views")
    print("=" * 80)
    
    investigate_empty_views()
    check_related_patterns()
    
    print(f"\n✅ Investigation complete!")
