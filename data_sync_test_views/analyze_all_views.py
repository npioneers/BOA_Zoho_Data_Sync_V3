#!/usr/bin/env python3
"""
Analyze All CSV+JSON Views
Check both FINAL_ and regular view_ patterns to identify which need smart merging.
"""
import sqlite3
import re
from config import get_database_path


def analyze_view_strategy(cursor, view_name):
    """Analyze a view's duplicate handling strategy"""
    try:
        # Get view definition
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='view' AND name='{view_name}'")
        result = cursor.fetchone()
        if not result:
            return "UNKNOWN", "View not found"
        
        sql = result[0].upper()
        
        # Check for different patterns
        has_left_join = 'LEFT JOIN' in sql
        has_coalesce = 'COALESCE' in sql
        has_union = 'UNION' in sql
        has_csv_table = any(table in sql for table in ['CSV_CONTACTS', 'CSV_CUSTOMER_PAYMENTS', 'CSV_ITEMS', 'CSV_SALES_ORDERS', 'CSV_VENDOR_PAYMENTS'])
        has_json_table = any(table in sql for table in ['JSON_CONTACTS', 'JSON_CUSTOMER_PAYMENTS', 'JSON_ITEMS', 'JSON_SALES_ORDERS', 'JSON_VENDOR_PAYMENTS'])
        
        # Classify strategy
        if has_left_join and has_coalesce:
            if has_union:
                return "LEFT_JOIN_UNION_COALESCE", "Advanced smart merging with UNION"
            else:
                return "LEFT_JOIN_COALESCE", "Uses LEFT JOIN with COALESCE"
        elif has_csv_table and not has_json_table:
            return "CSV_ONLY", "Only uses CSV table"
        elif has_json_table and not has_csv_table:
            return "JSON_ONLY", "Only uses JSON table"
        elif has_union:
            return "UNION_BASED", "Uses UNION without COALESCE"
        else:
            return "UNKNOWN", "Cannot determine strategy"
            
    except Exception as e:
        return "ERROR", str(e)


def get_view_record_counts(cursor, view_name):
    """Get record counts and data source distribution"""
    try:
        # Total count
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        total_count = cursor.fetchone()[0]
        
        # Try to get data source distribution
        try:
            cursor.execute(f"SELECT data_source, COUNT(*) FROM {view_name} GROUP BY data_source")
            distribution = dict(cursor.fetchall())
        except:
            distribution = {}
        
        return total_count, distribution
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    """Analyze all views to find opportunities for improvement"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
    all_views = [row[0] for row in cursor.fetchall()]
    
    # Filter for views that likely combine CSV and JSON
    csv_json_views = [v for v in all_views if 'csv' in v.lower() and 'json' in v.lower()]
    
    print("=" * 100)
    print("COMPREHENSIVE CSV+JSON VIEW ANALYSIS")
    print("=" * 100)
    print(f"Total views found: {len(all_views)}")
    print(f"CSV+JSON views found: {len(csv_json_views)}")
    print()
    
    strategy_summary = {}
    improvement_opportunities = []
    
    for view_name in csv_json_views:
        print(f"🔍 Analyzing: {view_name}")
        
        # Analyze strategy
        strategy, evidence = analyze_view_strategy(cursor, view_name)
        
        # Get counts
        total_count, distribution = get_view_record_counts(cursor, view_name)
        
        print(f"   📋 Strategy: {strategy}")
        print(f"   📊 Records: {total_count:,}")
        if distribution:
            for source, count in distribution.items():
                print(f"      📈 {source}: {count:,}")
        print(f"   ✅ Evidence: {evidence}")
        print()
        
        # Track for summary
        if strategy not in strategy_summary:
            strategy_summary[strategy] = []
        strategy_summary[strategy].append({
            'name': view_name,
            'count': total_count,
            'distribution': distribution,
            'evidence': evidence
        })
        
        # Check for improvement opportunities
        if strategy == "CSV_ONLY" and total_count > 0:
            improvement_opportunities.append(view_name)
    
    # Summary
    print("=" * 100)
    print("STRATEGY SUMMARY")
    print("=" * 100)
    
    for strategy, views in strategy_summary.items():
        print(f"\n📋 {strategy}: {len(views)} views")
        for view in views:
            count_info = f"({view['count']:,} records)"
            if view['distribution']:
                sources = ", ".join([f"{k}:{v:,}" for k, v in view['distribution'].items()])
                count_info = f"({sources})"
            print(f"   - {view['name']} {count_info}")
    
    # Improvement opportunities
    if improvement_opportunities:
        print(f"\n⚠️  IMPROVEMENT OPPORTUNITIES")
        print(f"   {len(improvement_opportunities)} views only use CSV data:")
        for view in improvement_opportunities:
            print(f"   - {view}")
            
        # Check if these views have corresponding JSON tables
        print(f"\n🔍 Checking for corresponding JSON tables:")
        for view in improvement_opportunities:
            # Extract table name pattern
            if 'contacts' in view:
                json_table = 'json_contacts'
            elif 'customer_payments' in view:
                json_table = 'json_customer_payments'  
            elif 'items' in view:
                json_table = 'json_items'
            elif 'sales_orders' in view:
                json_table = 'json_sales_orders'
            elif 'vendor_payments' in view:
                json_table = 'json_vendor_payments'
            else:
                continue
                
            cursor.execute(f"SELECT COUNT(*) FROM {json_table}")
            json_count = cursor.fetchone()[0]
            print(f"   - {view} → {json_table}: {json_count:,} JSON records available")
    else:
        print(f"\n✅ No improvement opportunities found - all views use optimal strategies!")
    
    conn.close()


if __name__ == "__main__":
    main()
