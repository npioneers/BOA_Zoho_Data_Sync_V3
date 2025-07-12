#!/usr/bin/env python3
"""
Detailed SQL Analysis of Unknown Strategy Views
Examines the actual SQL definitions of views with unknown strategies.
"""
import sqlite3
import re
from config import get_database_path


def analyze_unknown_views():
    """Analyze the 5 views with unknown strategies in detail"""
    db_path = get_database_path()
    
    unknown_views = [
        "FINAL_view_csv_json_contacts",
        "FINAL_view_csv_json_customer_payments", 
        "FINAL_view_csv_json_items",
        "FINAL_view_csv_json_sales_orders",
        "FINAL_view_csv_json_vendor_payments"
    ]
    
    print("=" * 100)
    print("DETAILED SQL ANALYSIS OF UNKNOWN STRATEGY VIEWS")
    print("=" * 100)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for view_name in unknown_views:
            print(f"\n🔍 ANALYZING: {view_name}")
            print("-" * 80)
            
            # Get SQL definition
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='view' AND name = ?
            """, (view_name,))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ Could not find SQL definition for {view_name}")
                continue
            
            sql = result[0]
            print("📄 SQL DEFINITION:")
            print(sql)
            print()
            
            # Analyze strategy
            strategy_analysis = analyze_sql_strategy(sql)
            print("📊 STRATEGY ANALYSIS:")
            for key, value in strategy_analysis.items():
                print(f"   {key}: {value}")
            print()
            
            # Check record count and sources
            cursor.execute(f"SELECT COUNT(*) FROM `{view_name}`")
            total_count = cursor.fetchone()[0]
            print(f"📈 RECORD COUNT: {total_count:,}")
            
            # Try to identify source data counts if possible
            try:
                # Extract table names from SQL
                table_names = extract_table_names(sql)
                print(f"📋 SOURCE TABLES: {', '.join(table_names)}")
                
                for table_name in table_names:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                        source_count = cursor.fetchone()[0]
                        print(f"   {table_name}: {source_count:,} records")
                    except:
                        print(f"   {table_name}: Could not count")
                        
            except Exception as e:
                print(f"   Could not analyze source tables: {e}")
            
            print("\n" + "=" * 100)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")


def analyze_sql_strategy(sql: str) -> dict:
    """Analyze SQL to determine strategy"""
    sql_lower = sql.lower()
    
    analysis = {
        "has_csv_tables": "csv_" in sql_lower,
        "has_json_tables": "json_" in sql_lower,
        "uses_union": "union" in sql_lower,
        "uses_union_all": "union all" in sql_lower,
        "uses_left_join": "left join" in sql_lower,
        "uses_inner_join": "inner join" in sql_lower,
        "uses_coalesce": "coalesce" in sql_lower,
        "uses_distinct": "distinct" in sql_lower,
        "join_count": sql_lower.count("join"),
        "where_clause": "where" in sql_lower,
        "group_by": "group by" in sql_lower,
        "order_by": "order by" in sql_lower
    }
    
    # Determine likely strategy
    if analysis["has_csv_tables"] and not analysis["has_json_tables"]:
        analysis["likely_strategy"] = "CSV_ONLY"
    elif analysis["uses_union"]:
        if analysis["uses_union_all"]:
            analysis["likely_strategy"] = "UNION_ALL (potential duplicates)"
        else:
            analysis["likely_strategy"] = "UNION (deduplicates)"
    elif analysis["uses_left_join"] and analysis["uses_coalesce"]:
        analysis["likely_strategy"] = "LEFT_JOIN_COALESCE"
    elif analysis["uses_left_join"]:
        analysis["likely_strategy"] = "LEFT_JOIN (basic)"
    elif analysis["uses_inner_join"]:
        analysis["likely_strategy"] = "INNER_JOIN"
    elif analysis["has_csv_tables"] and analysis["has_json_tables"]:
        analysis["likely_strategy"] = "MULTI_SOURCE (unknown method)"
    else:
        analysis["likely_strategy"] = "UNKNOWN"
    
    return analysis


def extract_table_names(sql: str) -> list:
    """Extract table names from SQL"""
    # Simple regex to find table names after FROM and JOIN
    table_pattern = r'(?:from|join)\s+[`"]?(\w+)[`"]?'
    matches = re.findall(table_pattern, sql.lower())
    
    # Remove duplicates and return
    return list(set(matches))


if __name__ == "__main__":
    analyze_unknown_views()
