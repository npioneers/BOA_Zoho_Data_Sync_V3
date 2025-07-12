#!/usr/bin/env python3
"""
Query and evaluate all FINAL views from production database
"""
import sqlite3
import os
from pathlib import Path

def query_final_views():
    """Query all views starting with FINAL from production database"""
    
    # Database path relative to this script
    db_path = Path("../data/database/production.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path.absolute()}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all views that start with FINAL
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='view' AND name LIKE 'FINAL%' 
            ORDER BY name
        """)
        views = cursor.fetchall()
        
        print(f"🔍 Found {len(views)} views starting with 'FINAL' in production database")
        print("=" * 80)
        
        if not views:
            print("❌ No views found starting with 'FINAL'")
            return
        
        # Process each view
        for i, (view_name, view_sql) in enumerate(views, 1):
            print(f"\n📋 VIEW {i}: {view_name}")
            print("-" * 60)
            
            # Query the view data instead of showing SQL
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{view_name}`")
                row_count = cursor.fetchone()[0]
                print(f"📊 Total Rows: {row_count:,}")
                
                if row_count > 0:
                    # Get column info
                    cursor.execute(f"PRAGMA table_info(`{view_name}`)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    print(f"📋 Columns ({len(columns)}): {', '.join(column_names)}")
                    
                    # Get sample rows with better formatting
                    cursor.execute(f"SELECT * FROM `{view_name}` LIMIT 5")
                    sample_rows = cursor.fetchall()
                    
                    if sample_rows:
                        print(f"\n� Sample Data (first 5 rows):")
                        print("-" * 40)
                        
                        # Print header
                        header = " | ".join([f"{col[:15]:<15}" for col in column_names[:6]])  # Limit to 6 columns for readability
                        print(f"  {header}")
                        print(f"  {'-' * len(header)}")
                        
                        # Print data rows
                        for j, row in enumerate(sample_rows, 1):
                            # Limit to first 6 columns and truncate long values
                            formatted_row = []
                            for k, value in enumerate(row[:6]):
                                if value is None:
                                    formatted_row.append("NULL".ljust(15))
                                else:
                                    str_val = str(value)[:15]
                                    formatted_row.append(str_val.ljust(15))
                            row_str = " | ".join(formatted_row)
                            print(f"  {row_str}")
                        
                        if len(column_names) > 6:
                            print(f"  ... ({len(column_names) - 6} more columns)")
                    
                    # Get some statistics if numeric columns exist
                    print(f"\n📊 Data Analysis:")
                    for col_name in column_names[:3]:  # Check first 3 columns for stats
                        try:
                            cursor.execute(f"SELECT MIN(`{col_name}`), MAX(`{col_name}`), COUNT(DISTINCT `{col_name}`) FROM `{view_name}` WHERE `{col_name}` IS NOT NULL")
                            min_val, max_val, distinct_count = cursor.fetchone()
                            if min_val is not None:
                                print(f"  {col_name}: Min={min_val}, Max={max_val}, Distinct={distinct_count}")
                        except:
                            pass  # Skip if column is not numeric or has issues
                            
                else:
                    print("📭 View is empty")
                    
            except Exception as e:
                print(f"⚠️  Error querying view: {e}")
            
            print("=" * 80)
        
        # Create summary
        print(f"\n📊 SUMMARY:")
        print(f"- Total FINAL views found: {len(views)}")
        print(f"- Database location: {db_path.absolute()}")
        
        conn.close()
        return views
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def analyze_view_patterns(views):
    """Analyze patterns in the FINAL views"""
    if not views:
        return
    
    print(f"\n🔍 VIEW PATTERN ANALYSIS:")
    print("-" * 40)
    
    # Analyze naming patterns
    view_names = [view[0] for view in views]
    print(f"📋 View Names:")
    for name in view_names:
        print(f"  - {name}")
    
    # Analyze SQL patterns
    print(f"\n🔧 SQL Pattern Analysis:")
    join_count = sum(1 for _, sql in views if 'JOIN' in sql.upper())
    where_count = sum(1 for _, sql in views if 'WHERE' in sql.upper())
    group_count = sum(1 for _, sql in views if 'GROUP BY' in sql.upper())
    order_count = sum(1 for _, sql in views if 'ORDER BY' in sql.upper())
    
    print(f"  - Views with JOINs: {join_count}")
    print(f"  - Views with WHERE clauses: {where_count}")
    print(f"  - Views with GROUP BY: {group_count}")
    print(f"  - Views with ORDER BY: {order_count}")

if __name__ == "__main__":
    print("🚀 Querying FINAL views from production database...")
    views = query_final_views()
    
    if views:
        analyze_view_patterns(views)
    
    print(f"\n✅ Analysis complete!")
