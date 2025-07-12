#!/usr/bin/env python3
"""
Detailed analysis of invoices FINAL view to evaluate our fixes
"""

import sqlite3
import os

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 DETAILED INVOICES FINAL VIEW ANALYSIS')
    print('='*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check base tables first
    print("📋 BASE TABLE ANALYSIS:")
    try:
        csv_count = conn.execute('SELECT COUNT(*) FROM csv_invoices').fetchone()[0]
        print(f"   csv_invoices: {csv_count:,} records")
    except Exception as e:
        print(f"   ❌ csv_invoices: {e}")
        
    try:
        json_count = conn.execute('SELECT COUNT(*) FROM json_invoices').fetchone()[0]
        print(f"   json_invoices: {json_count:,} records")
    except Exception as e:
        print(f"   ❌ json_invoices: {e}")
    
    # 2. Check FINAL view details
    print(f"\n🎯 FINAL VIEW DETAILED ANALYSIS:")
    try:
        # Total records
        total = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_invoices').fetchone()[0]
        print(f"   Total records: {total:,}")
        
        # Data source breakdown
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FINAL_view_csv_json_invoices), 2) as percentage
            FROM FINAL_view_csv_json_invoices 
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        sources = cursor.fetchall()
        print(f"   Data source distribution:")
        for source, count, pct in sources:
            print(f"      {source}: {count:,} records ({pct}%)")
        
        # Check for key fields
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(invoice_id) as has_invoice_id,
                COUNT(invoice_number) as has_invoice_number,
                COUNT(customer_name) as has_customer,
                COUNT(total) as has_total
            FROM FINAL_view_csv_json_invoices
        ''')
        
        field_check = cursor.fetchone()
        total, invoice_id, invoice_num, customer, amount = field_check
        print(f"   Field completeness:")
        print(f"      invoice_id: {invoice_id:,}/{total:,} ({invoice_id/total*100:.1f}%)")
        print(f"      invoice_number: {invoice_num:,}/{total:,} ({invoice_num/total*100:.1f}%)")
        print(f"      customer_name: {customer:,}/{total:,} ({customer/total*100:.1f}%)")
        print(f"      total: {amount:,}/{total:,} ({amount/total*100:.1f}%)")
        
    except Exception as e:
        print(f"   ❌ FINAL view analysis failed: {e}")
    
    # 3. Check if there's a base integration view
    print(f"\n🔄 INTEGRATION VIEW CHECK:")
    try:
        int_count = conn.execute('SELECT COUNT(*) FROM view_csv_json_invoices').fetchone()[0]
        print(f"   view_csv_json_invoices: {int_count:,} records")
        
        # Compare with FINAL
        final_count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_invoices').fetchone()[0]
        if int_count == final_count:
            print(f"   ✅ Integration and FINAL views match exactly")
        else:
            print(f"   ⚠️ Integration ({int_count:,}) vs FINAL ({final_count:,}) - difference: {abs(int_count-final_count):,}")
            
        # Check integration view data sources
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count
            FROM view_csv_json_invoices 
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        int_sources = cursor.fetchall()
        print(f"   Integration view data sources:")
        for source, count in int_sources:
            print(f"      {source}: {count:,} records")
            
    except Exception as e:
        if "no such table" in str(e):
            print(f"   ❌ view_csv_json_invoices does not exist")
        else:
            print(f"   ❌ Integration view check failed: {e}")
    
    # 4. Check if our smart merging is needed
    print(f"\n💡 SMART MERGING ASSESSMENT:")
    try:
        # Are there JSON invoices that might not be in the FINAL view?
        json_invoices = conn.execute('SELECT COUNT(*) FROM json_invoices').fetchone()[0]
        csv_invoices = conn.execute('SELECT COUNT(*) FROM csv_invoices').fetchone()[0]
        final_invoices = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_invoices').fetchone()[0]
        
        print(f"   Source records: CSV={csv_invoices:,}, JSON={json_invoices:,}")
        print(f"   FINAL view records: {final_invoices:,}")
        print(f"   Expansion ratio: {final_invoices / (csv_invoices + json_invoices):.1f}x")
        
        # Calculate expected vs actual
        total_source = csv_invoices + json_invoices
        if final_invoices > total_source:
            print(f"   📊 Data expansion detected: {final_invoices - total_source:,} additional records")
            print(f"   ℹ️ This indicates line item expansion (invoices → invoice lines)")
        
        # Check for potential overlap
        if json_invoices > 0 and csv_invoices > 0:
            try:
                overlap = conn.execute('''
                    SELECT COUNT(*) FROM csv_invoices c 
                    INNER JOIN json_invoices j ON c.invoice_number = j.invoice_number
                ''').fetchone()[0]
                print(f"   Overlap by invoice_number: {overlap:,} records")
                
                # Check if JSON records are properly included
                json_only_in_final = conn.execute('''
                    SELECT COUNT(*) FROM FINAL_view_csv_json_invoices 
                    WHERE data_source = 'json_only'
                ''').fetchone()[0]
                
                enhanced_in_final = conn.execute('''
                    SELECT COUNT(*) FROM FINAL_view_csv_json_invoices 
                    WHERE data_source = 'enhanced'
                ''').fetchone()[0]
                
                print(f"   JSON-only records in FINAL: {json_only_in_final:,}")
                print(f"   Enhanced (CSV+JSON) records in FINAL: {enhanced_in_final:,}")
                
                if json_only_in_final > 0 or enhanced_in_final > 0:
                    print(f"   ✅ JSON data is being integrated successfully")
                else:
                    print(f"   ⚠️ JSON data may not be fully integrated")
                    
            except Exception as e:
                print(f"   Could not check overlap: {e}")
                
    except Exception as e:
        print(f"   ❌ Smart merging assessment failed: {e}")
    
    # 5. Check data source pattern analysis
    print(f"\n📊 DATA SOURCE PATTERN ANALYSIS:")
    try:
        # Analyze the distribution patterns
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count,
                MIN(invoice_id) as min_id,
                MAX(invoice_id) as max_id,
                COUNT(DISTINCT customer_name) as unique_customers
            FROM FINAL_view_csv_json_invoices 
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        patterns = cursor.fetchall()
        for source, count, min_id, max_id, customers in patterns:
            print(f"   {source}:")
            print(f"      Records: {count:,}")
            print(f"      ID range: {min_id} to {max_id}")
            print(f"      Unique customers: {customers:,}")
            
    except Exception as e:
        print(f"   ❌ Pattern analysis failed: {e}")
    
    # 6. Sample records
    print(f"\n📋 SAMPLE RECORDS:")
    try:
        cursor.execute('''
            SELECT invoice_id, invoice_number, data_source, customer_name, total, invoice_date
            FROM FINAL_view_csv_json_invoices 
            ORDER BY data_source, invoice_id
            LIMIT 5
        ''')
        
        samples = cursor.fetchall()
        for invoice_id, invoice_num, source, customer, total, date in samples:
            print(f"   {source}: ID={invoice_id}, #={invoice_num}, Customer={customer}, Total={total}, Date={date}")
            
    except Exception as e:
        print(f"   ❌ Sample records failed: {e}")
    
    # 7. Line item expansion analysis
    print(f"\n🔍 LINE ITEM EXPANSION ANALYSIS:")
    try:
        # Check if this is line-item level data
        cursor.execute('''
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT invoice_number) as unique_invoices,
                ROUND(CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT invoice_number), 2) as avg_lines_per_invoice
            FROM FINAL_view_csv_json_invoices
        ''')
        
        expansion = cursor.fetchone()
        total_recs, unique_invoices, avg_lines = expansion
        
        print(f"   Total records: {total_recs:,}")
        print(f"   Unique invoices: {unique_invoices:,}")
        print(f"   Average lines per invoice: {avg_lines}")
        
        if avg_lines > 1.5:
            print(f"   ✅ This appears to be line-item level data (expansion factor: {avg_lines})")
        else:
            print(f"   ℹ️ This appears to be header-level data")
            
    except Exception as e:
        print(f"   ❌ Line item analysis failed: {e}")
    
    conn.close()
    
    print(f"\n" + "="*60)
    print(f"🎯 INVOICES FINAL VIEW EVALUATION COMPLETE")

if __name__ == "__main__":
    main()
