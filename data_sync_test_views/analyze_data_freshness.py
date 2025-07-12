#!/usr/bin/env python3
"""
Data Freshness Field Analysis
Analyze CSV and JSON tables to identify fields that indicate data freshness/update timestamps
"""
import sqlite3
from datetime import datetime
from config import get_database_path


def analyze_timestamp_fields():
    """Analyze tables to find timestamp fields that indicate data freshness"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DATA FRESHNESS FIELD ANALYSIS")
    print("=" * 80)
    print("🎯 Goal: Identify fields to determine when JSON data is fresher than CSV")
    print()
    
    # Tables to analyze
    table_pairs = [
        ('csv_items', 'json_items'),
        ('csv_invoices', 'json_invoices'),
        ('csv_bills', 'json_bills'),
        ('csv_contacts', 'json_contacts'),
        ('csv_sales_orders', 'json_sales_orders')
    ]
    
    for csv_table, json_table in table_pairs:
        print(f"🔍 Analyzing: {csv_table} vs {json_table}")
        
        # Get CSV timestamp fields
        cursor.execute(f"PRAGMA table_info({csv_table})")
        csv_columns = [row[1] for row in cursor.fetchall()]
        csv_timestamp_fields = [col for col in csv_columns if any(keyword in col.lower() 
                               for keyword in ['time', 'date', 'created', 'updated', 'modified', 'last_sync'])]
        
        # Get JSON timestamp fields
        try:
            cursor.execute(f"PRAGMA table_info({json_table})")
            json_columns = [row[1] for row in cursor.fetchall()]
            json_timestamp_fields = [col for col in json_columns if any(keyword in col.lower() 
                                   for keyword in ['time', 'date', 'created', 'updated', 'modified', 'last_sync'])]
        except:
            json_timestamp_fields = []
            print(f"   ❌ {json_table} not found")
            continue
        
        print(f"   📊 CSV timestamp fields: {csv_timestamp_fields}")
        print(f"   📊 JSON timestamp fields: {json_timestamp_fields}")
        
        # Find common timestamp fields
        common_fields = set(csv_timestamp_fields) & set(json_timestamp_fields)
        if common_fields:
            print(f"   ✅ Common timestamp fields: {list(common_fields)}")
            
            # Sample data from common fields
            for field in list(common_fields)[:2]:  # Check first 2 common fields
                try:
                    # Get sample CSV values
                    cursor.execute(f"SELECT {field} FROM {csv_table} WHERE {field} IS NOT NULL LIMIT 3")
                    csv_samples = [row[0] for row in cursor.fetchall()]
                    
                    # Get sample JSON values
                    cursor.execute(f"SELECT {field} FROM {json_table} WHERE {field} IS NOT NULL LIMIT 3")
                    json_samples = [row[0] for row in cursor.fetchall()]
                    
                    print(f"      🔍 {field}:")
                    print(f"         CSV samples: {csv_samples}")
                    print(f"         JSON samples: {json_samples}")
                    
                except Exception as e:
                    print(f"      ❌ Error sampling {field}: {e}")
        else:
            print(f"   ⚠️  No common timestamp fields found")
        
        print()
    
    conn.close()


def analyze_specific_items_timestamps():
    """Deep dive into items table timestamp analysis"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ITEMS TABLE TIMESTAMP DEEP DIVE")
    print("=" * 80)
    
    # Get overlapping records (same item_id in both tables)
    try:
        cursor.execute("""
            SELECT 
                csv.item_id,
                csv.created_timestamp as csv_created,
                csv.updated_timestamp as csv_updated,
                csv.last_sync_time as csv_sync,
                json.created_time as json_created,
                json.last_modified_time as json_modified
            FROM csv_items csv
            INNER JOIN json_items json ON csv.item_id = json.item_id
            LIMIT 10
        """)
        
        overlapping = cursor.fetchall()
        
        if overlapping:
            print(f"📊 Found {len(overlapping)} overlapping records. Sample comparison:")
            print()
            
            for i, row in enumerate(overlapping[:5]):
                item_id, csv_created, csv_updated, csv_sync, json_created, json_modified = row
                print(f"🔍 Item {item_id}:")
                print(f"   CSV: created={csv_created}, updated={csv_updated}, sync={csv_sync}")
                print(f"   JSON: created={json_created}, modified={json_modified}")
                
                # Try to parse and compare dates
                try:
                    if csv_updated and json_modified:
                        print(f"   📅 Comparison: CSV updated vs JSON modified")
                        print(f"      CSV: {csv_updated}")
                        print(f"      JSON: {json_modified}")
                        
                        # Simple string comparison (assumes ISO format)
                        if str(json_modified) > str(csv_updated):
                            print(f"      ✅ JSON is fresher")
                        elif str(csv_updated) > str(json_modified):
                            print(f"      ✅ CSV is fresher")
                        else:
                            print(f"      ⚖️  Same timestamp")
                except Exception as e:
                    print(f"      ❌ Date comparison error: {e}")
                print()
        else:
            print("⚠️  No overlapping records found between csv_items and json_items")
            
    except Exception as e:
        print(f"❌ Error analyzing overlapping records: {e}")
    
    conn.close()


def recommend_freshness_strategy():
    """Recommend the best strategy for preferring fresh data"""
    print("=" * 80)
    print("RECOMMENDED FRESHNESS STRATEGY")
    print("=" * 80)
    
    print("🎯 **SMART CSV-PREFERRED STRATEGY WITH FRESHNESS CHECK**")
    print()
    print("**Recommended Logic:**")
    print("1. 🔄 **Default**: Prefer CSV data (current business logic)")
    print("2. 🆕 **Override**: Use JSON data ONLY when it's demonstrably fresher")
    print("3. 📅 **Freshness Check**: Compare timestamp fields to determine recency")
    print()
    
    print("**🔍 Recommended Timestamp Fields for Comparison:**")
    print("- **Primary**: `updated_timestamp` (CSV) vs `last_modified_time` (JSON)")
    print("- **Secondary**: `last_sync_time` (CSV) vs `last_modified_time` (JSON)")
    print("- **Fallback**: `created_timestamp` (CSV) vs `created_time` (JSON)")
    print()
    
    print("**📝 Proposed SQL Pattern:**")
    print("""
```sql
-- Smart CSV-preferred with freshness check
SELECT 
    CASE 
        WHEN json.last_modified_time > csv.updated_timestamp 
        THEN json.field_name
        ELSE csv.field_name 
    END AS field_name,
    
    CASE 
        WHEN json.last_modified_time > csv.updated_timestamp 
        THEN 'JSON_FRESH'
        ELSE 'CSV_PREFERRED' 
    END AS data_source
    
FROM csv_table csv
LEFT JOIN json_table json ON csv.id = json.id
```
""")
    
    print("**🎯 Benefits of This Approach:**")
    print("✅ Maintains CSV as the primary/trusted source")
    print("✅ Only uses JSON when it's actually fresher")
    print("✅ Provides clear data lineage tracking")
    print("✅ Minimizes disruption to current business logic")
    print("✅ Maximizes data quality and recency")


def main():
    """Main analysis function"""
    analyze_timestamp_fields()
    analyze_specific_items_timestamps()
    recommend_freshness_strategy()


if __name__ == "__main__":
    main()
