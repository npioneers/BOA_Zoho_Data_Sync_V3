#!/usr/bin/env python3
"""
Database View Analysis - Comprehensive Overview
Analyze all view types and their relationships
"""
import sqlite3
from config import get_database_path


def analyze_view_patterns():
    """Analyze all views and categorize them by patterns"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
    all_views = [row[0] for row in cursor.fetchall()]
    
    print("=" * 80)
    print("DATABASE VIEW ANALYSIS - COMPREHENSIVE OVERVIEW")
    print("=" * 80)
    print(f"Total views found: {len(all_views)}")
    print()
    
    # Categorize views by patterns
    categories = {}
    for view in all_views:
        if view.startswith('FINAL_'):
            key = 'FINAL_views'
        elif view.startswith('view_') and '_summary' in view:
            key = 'Summary_views'
        elif view.startswith('view_') and 'csv_json' in view:
            key = 'CSV_JSON_integration_views'
        elif view.startswith('view_') and '_deduplicated' in view:
            key = 'Deduplicated_views'
        elif view.startswith('view_') and view.count('_') == 1:
            key = 'Simple_table_views'
        elif view.startswith('view_'):
            key = 'Other_complex_views'
        else:
            key = 'Uncategorized_views'
        
        if key not in categories:
            categories[key] = []
        categories[key].append(view)
    
    # Display categories with analysis
    for category, views in sorted(categories.items()):
        print(f"📊 {category}: {len(views)} views")
        for view in sorted(views):
            # Get record count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {view}")
                count = cursor.fetchone()[0]
                print(f"   - {view} ({count:,} records)")
            except Exception as e:
                print(f"   - {view} (ERROR: {e})")
        print()
    
    conn.close()
    return categories


def analyze_view_relationships():
    """Analyze relationships between different view types"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VIEW RELATIONSHIPS AND HIERARCHY ANALYSIS")
    print("=" * 80)
    
    # Focus on specific patterns
    table_groups = {}
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
    all_views = [row[0] for row in cursor.fetchall()]
    
    # Group by table name
    for view in all_views:
        # Extract table name
        table_name = None
        if view.startswith('FINAL_view_csv_json_'):
            table_name = view.replace('FINAL_view_csv_json_', '')
        elif view.startswith('view_csv_json_'):
            table_name = view.replace('view_csv_json_', '')
        elif view.startswith('view_') and not 'csv_json' in view:
            parts = view.split('_')
            if len(parts) >= 2:
                table_name = parts[1]
        
        if table_name:
            if table_name not in table_groups:
                table_groups[table_name] = []
            table_groups[table_name].append(view)
    
    # Analyze each table group
    for table_name, views in sorted(table_groups.items()):
        if len(views) > 1:  # Only show tables with multiple views
            print(f"🗂️ Table: {table_name}")
            print(f"   Related views: {len(views)}")
            
            for view in sorted(views):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {view}")
                    count = cursor.fetchone()[0]
                    
                    # Determine view type
                    if view.startswith('FINAL_'):
                        view_type = "FINAL (Production)"
                    elif 'csv_json' in view and '_summary' in view:
                        view_type = "CSV+JSON Summary"
                    elif 'csv_json' in view and '_deduplicated' in view:
                        view_type = "CSV+JSON Deduplicated"
                    elif 'csv_json' in view and ('_v2' in view or '_v3' in view):
                        view_type = f"CSV+JSON Version {view[-1] if view[-1].isdigit() else '?'}"
                    elif 'csv_json' in view:
                        view_type = "CSV+JSON Integration"
                    elif '_summary' in view:
                        view_type = "Summary"
                    elif '_deduplicated' in view:
                        view_type = "Deduplicated"
                    else:
                        view_type = "Standard"
                    
                    print(f"     ✅ {view}")
                    print(f"        Type: {view_type}")
                    print(f"        Records: {count:,}")
                    
                except Exception as e:
                    print(f"     ❌ {view} (ERROR: {e})")
            print()
    
    conn.close()


def analyze_view_definitions_sample():
    """Analyze a few view definitions to understand the patterns"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VIEW DEFINITION ANALYSIS - UNDERSTANDING THE PATTERNS")
    print("=" * 80)
    
    # Sample views from different categories
    sample_views = [
        'FINAL_view_csv_json_items',  # Our successful improvement
        'view_csv_json_items',        # Regular integration view
        'view_csv_json_bills_summary', # Summary view
        'view_csv_json_bills_deduplicated', # Deduplicated view
    ]
    
    for view in sample_views:
        print(f"🔍 Analyzing: {view}")
        try:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='view' AND name='{view}'")
            result = cursor.fetchone()
            if result:
                sql = result[0]
                
                # Analyze SQL patterns
                has_coalesce = 'COALESCE' in sql.upper()
                has_left_join = 'LEFT JOIN' in sql.upper()
                has_union = 'UNION' in sql.upper()
                has_distinct = 'DISTINCT' in sql.upper()
                has_data_source = 'data_source' in sql.lower()
                
                print(f"   📋 SQL Features:")
                print(f"      COALESCE: {'✅' if has_coalesce else '❌'}")
                print(f"      LEFT JOIN: {'✅' if has_left_join else '❌'}")
                print(f"      UNION: {'✅' if has_union else '❌'}")
                print(f"      DISTINCT: {'✅' if has_distinct else '❌'}")
                print(f"      data_source tracking: {'✅' if has_data_source else '❌'}")
                
                # Show first 200 chars
                print(f"   📄 SQL Preview: {sql[:200]}...")
                
            else:
                print(f"   ❌ View not found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
    
    conn.close()


def main():
    """Main analysis function"""
    categories = analyze_view_patterns()
    print()
    analyze_view_relationships()
    print()
    analyze_view_definitions_sample()
    
    print("=" * 80)
    print("SUMMARY - VIEW ARCHITECTURE EXPLANATION")
    print("=" * 80)
    print("🏗️ VIEW HIERARCHY EXPLAINED:")
    print()
    print("1️⃣ BASE TABLES: csv_<table> and json_<table>")
    print("   - Raw data from CSV files and JSON API responses")
    print()
    print("2️⃣ INTEGRATION VIEWS: view_csv_json_<table>")
    print("   - Combine CSV and JSON data using LEFT JOIN + COALESCE")
    print("   - Handle duplicates by prioritizing one source over another")
    print()
    print("3️⃣ ENHANCED VIEWS: view_csv_json_<table>_v2, _v3")
    print("   - Iterative improvements to integration logic")
    print("   - Different approaches to handling conflicts")
    print()
    print("4️⃣ SPECIALIZED VIEWS:")
    print("   - view_csv_json_<table>_summary: Aggregated/summarized data")
    print("   - view_csv_json_<table>_deduplicated: Explicit deduplication")
    print()
    print("5️⃣ FINAL VIEWS: FINAL_view_csv_json_<table>")
    print("   - Production-ready views for end users")
    print("   - Should represent the 'gold standard' data")
    print("   - What we improved with smart merging!")
    print()
    print("🎯 OUR IMPROVEMENT: Enhanced FINAL views with UNION strategy")
    print("   to show both CSV and JSON records with proper prioritization!")


if __name__ == "__main__":
    main()
