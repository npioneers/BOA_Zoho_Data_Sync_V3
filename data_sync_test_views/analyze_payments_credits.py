#!/usr/bin/env python3
"""
Detailed analysis of customer payments and credit notes FINAL views to evaluate our fixes
"""

import sqlite3
import os

def analyze_table(conn, table_name, display_name):
    """Analyze a specific table's FINAL view"""
    
    print(f"\n🔍 {display_name.upper()} ANALYSIS:")
    print("-" * 50)
    
    cursor = conn.cursor()
    
    # 1. Check if FINAL view exists
    final_view_name = f"FINAL_view_csv_json_{table_name}"
    try:
        final_count = conn.execute(f'SELECT COUNT(*) FROM {final_view_name}').fetchone()[0]
        print(f"✅ {final_view_name}: {final_count:,} records")
    except Exception as e:
        print(f"❌ {final_view_name} does not exist: {e}")
        return
    
    # 2. Check base tables
    print(f"\n📋 BASE TABLE ANALYSIS:")
    csv_table = f"csv_{table_name}"
    json_table = f"json_{table_name}"
    
    try:
        csv_count = conn.execute(f'SELECT COUNT(*) FROM {csv_table}').fetchone()[0]
        print(f"   {csv_table}: {csv_count:,} records")
    except Exception as e:
        print(f"   ❌ {csv_table}: {e}")
        csv_count = 0
        
    try:
        json_count = conn.execute(f'SELECT COUNT(*) FROM {json_table}').fetchone()[0]
        print(f"   {json_table}: {json_count:,} records")
    except Exception as e:
        print(f"   ❌ {json_table}: {e}")
        json_count = 0
    
    # 3. Data source distribution in FINAL view
    print(f"\n🎯 FINAL VIEW DATA SOURCE DISTRIBUTION:")
    try:
        cursor.execute(f'''
            SELECT 
                data_source,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {final_view_name}), 2) as percentage
            FROM {final_view_name}
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        sources = cursor.fetchall()
        for source, count, pct in sources:
            print(f"   {source}: {count:,} records ({pct}%)")
            
    except Exception as e:
        print(f"   ❌ Data source analysis failed: {e}")
    
    # 4. Check integration view if it exists
    integration_view_name = f"view_csv_json_{table_name}"
    print(f"\n🔄 INTEGRATION VIEW CHECK:")
    try:
        int_count = conn.execute(f'SELECT COUNT(*) FROM {integration_view_name}').fetchone()[0]
        print(f"   {integration_view_name}: {int_count:,} records")
        
        if int_count == final_count:
            print(f"   ✅ Integration and FINAL views match exactly")
        else:
            print(f"   ⚠️ Integration ({int_count:,}) vs FINAL ({final_count:,}) - difference: {abs(int_count-final_count):,}")
            
        # Check integration view data sources
        cursor.execute(f'''
            SELECT 
                data_source,
                COUNT(*) as count
            FROM {integration_view_name}
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        int_sources = cursor.fetchall()
        print(f"   Integration view data sources:")
        for source, count in int_sources:
            print(f"      {source}: {count:,} records")
            
    except Exception as e:
        if "no such table" in str(e):
            print(f"   ❌ {integration_view_name} does not exist")
        else:
            print(f"   ❌ Integration view check failed: {e}")
    
    # 5. Smart merging assessment
    print(f"\n💡 SMART MERGING ASSESSMENT:")
    total_source = csv_count + json_count
    if total_source > 0:
        expansion_ratio = final_count / total_source if total_source > 0 else 0
        print(f"   Source records: CSV={csv_count:,}, JSON={json_count:,}")
        print(f"   FINAL view records: {final_count:,}")
        print(f"   Expansion ratio: {expansion_ratio:.1f}x")
        
        if expansion_ratio > 1.5:
            print(f"   📊 Data expansion detected - likely line item expansion")
        elif expansion_ratio < 0.9:
            print(f"   ⚠️ Data loss detected - some records may be missing")
        else:
            print(f"   ✅ Expected record count - header level data")
    
    # 6. Check for overlap if both CSV and JSON exist
    if csv_count > 0 and json_count > 0:
        try:
            # Try common ID fields for overlap detection
            id_fields = [f"{table_name}_id", "id", f"{table_name}_number", "number"]
            overlap_found = False
            
            for id_field in id_fields:
                try:
                    overlap = conn.execute(f'''
                        SELECT COUNT(*) FROM {csv_table} c 
                        INNER JOIN {json_table} j ON c.{id_field} = j.{id_field}
                    ''').fetchone()[0]
                    if overlap > 0:
                        print(f"   Overlap by {id_field}: {overlap:,} records")
                        overlap_found = True
                        break
                except:
                    continue
                    
            if not overlap_found:
                print(f"   ℹ️ No overlap detected or overlap field not found")
                
        except Exception as e:
            print(f"   Could not check overlap: {e}")
    
    # 7. Sample records
    print(f"\n📋 SAMPLE RECORDS:")
    try:
        # Get column names first
        cursor.execute(f'PRAGMA table_info({final_view_name})')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Select appropriate columns for display
        display_cols = []
        for potential_col in [f"{table_name}_id", "id", f"{table_name}_number", "number", "name", "total", "amount", "date"]:
            if potential_col in columns:
                display_cols.append(potential_col)
        
        if "data_source" in columns:
            display_cols.insert(0, "data_source")
            
        if display_cols:
            col_list = ", ".join(display_cols[:6])  # Limit to 6 columns
            cursor.execute(f'''
                SELECT {col_list}
                FROM {final_view_name} 
                ORDER BY data_source
                LIMIT 3
            ''')
            
            samples = cursor.fetchall()
            for sample in samples:
                sample_str = ", ".join([f"{col}={val}" for col, val in zip(display_cols[:len(sample)], sample)])
                print(f"   {sample_str}")
        else:
            print(f"   ❌ Could not determine appropriate columns for sampling")
            
    except Exception as e:
        print(f"   ❌ Sample records failed: {e}")

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 CUSTOMER PAYMENTS & CREDIT NOTES FINAL VIEW ANALYSIS')
    print('='*70)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
        
    print(f"📂 Database: {db_path}")
    print(f"📏 Size: {os.path.getsize(db_path):,} bytes")
    
    conn = sqlite3.connect(db_path)
    
    # Analyze both tables
    analyze_table(conn, "customer_payments", "Customer Payments")
    analyze_table(conn, "credit_notes", "Credit Notes")
    
    # Check if these have missing FINAL views that need to be created
    print(f"\n🔍 MISSING FINAL VIEWS CHECK:")
    
    tables_to_check = ["customer_payments", "credit_notes"]
    for table in tables_to_check:
        final_view = f"FINAL_view_csv_json_{table}"
        integration_view = f"view_csv_json_{table}"
        
        try:
            # Check if FINAL exists
            conn.execute(f'SELECT 1 FROM {final_view} LIMIT 1')
            print(f"   ✅ {final_view} exists")
        except:
            # Check if integration view exists to create FINAL from
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM {integration_view}').fetchone()[0]
                print(f"   ❌ {final_view} missing but {integration_view} exists ({count:,} records)")
                print(f"      💡 Recommendation: Create {final_view} based on {integration_view}")
            except:
                print(f"   ❌ Both {final_view} and {integration_view} missing")
    
    conn.close()
    
    print(f"\n" + "="*70)
    print(f"🎯 CUSTOMER PAYMENTS & CREDIT NOTES ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()
