#!/usr/bin/env python3
"""
Detailed analysis of bills FINAL view to evaluate our fixes
"""

import sqlite3
import os

def main():
    db_path = '../data/database/production.db'
    
    print('🔍 DETAILED BILLS FINAL VIEW ANALYSIS')
    print('='*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check base tables first
    print("📋 BASE TABLE ANALYSIS:")
    try:
        csv_count = conn.execute('SELECT COUNT(*) FROM csv_bills').fetchone()[0]
        print(f"   csv_bills: {csv_count:,} records")
    except Exception as e:
        print(f"   ❌ csv_bills: {e}")
        
    try:
        json_count = conn.execute('SELECT COUNT(*) FROM json_bills').fetchone()[0]
        print(f"   json_bills: {json_count:,} records")
    except Exception as e:
        print(f"   ❌ json_bills: {e}")
    
    # 2. Check FINAL view details
    print(f"\n🎯 FINAL VIEW DETAILED ANALYSIS:")
    try:
        # Total records
        total = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_bills').fetchone()[0]
        print(f"   Total records: {total:,}")
        
        # Data source breakdown
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FINAL_view_csv_json_bills), 2) as percentage
            FROM FINAL_view_csv_json_bills 
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
                COUNT(bill_id) as has_bill_id,
                COUNT(bill_number) as has_bill_number,
                COUNT(vendor_name) as has_vendor,
                COUNT(total) as has_total
            FROM FINAL_view_csv_json_bills
        ''')
        
        field_check = cursor.fetchone()
        total, bill_id, bill_num, vendor, amount = field_check
        print(f"   Field completeness:")
        print(f"      bill_id: {bill_id:,}/{total:,} ({bill_id/total*100:.1f}%)")
        print(f"      bill_number: {bill_num:,}/{total:,} ({bill_num/total*100:.1f}%)")
        print(f"      vendor_name: {vendor:,}/{total:,} ({vendor/total*100:.1f}%)")
        print(f"      total: {amount:,}/{total:,} ({amount/total*100:.1f}%)")
        
    except Exception as e:
        print(f"   ❌ FINAL view analysis failed: {e}")
    
    # 3. Check if there's a base integration view
    print(f"\n🔄 INTEGRATION VIEW CHECK:")
    try:
        int_count = conn.execute('SELECT COUNT(*) FROM view_csv_json_bills').fetchone()[0]
        print(f"   view_csv_json_bills: {int_count:,} records")
        
        # Compare with FINAL
        final_count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_bills').fetchone()[0]
        if int_count == final_count:
            print(f"   ✅ Integration and FINAL views match exactly")
        else:
            print(f"   ⚠️ Integration ({int_count:,}) vs FINAL ({final_count:,}) - difference: {abs(int_count-final_count):,}")
            
        # Check integration view data sources
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count
            FROM view_csv_json_bills 
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        int_sources = cursor.fetchall()
        print(f"   Integration view data sources:")
        for source, count in int_sources:
            print(f"      {source}: {count:,} records")
            
    except Exception as e:
        if "no such table" in str(e):
            print(f"   ❌ view_csv_json_bills does not exist")
        else:
            print(f"   ❌ Integration view check failed: {e}")
    
    # 4. Check if our smart merging is needed
    print(f"\n💡 SMART MERGING ASSESSMENT:")
    try:
        # Are there JSON bills that might not be in the FINAL view?
        json_bills = conn.execute('SELECT COUNT(*) FROM json_bills').fetchone()[0]
        csv_bills = conn.execute('SELECT COUNT(*) FROM csv_bills').fetchone()[0]
        final_bills = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_bills').fetchone()[0]
        
        print(f"   Source records: CSV={csv_bills:,}, JSON={json_bills:,}")
        print(f"   FINAL view records: {final_bills:,}")
        
        if json_bills > 0 and final_bills == csv_bills:
            print(f"   🎯 OPPORTUNITY: JSON bills exist but not visible in FINAL view!")
            print(f"   Recommendation: Implement smart merging to include JSON data")
        elif json_bills > 0:
            print(f"   ✅ JSON data appears to be integrated")
        else:
            print(f"   ℹ️ No JSON bills data to integrate")
            
        # Check for potential overlap
        if json_bills > 0 and csv_bills > 0:
            try:
                overlap = conn.execute('''
                    SELECT COUNT(*) FROM csv_bills c 
                    INNER JOIN json_bills j ON c.bill_number = j.bill_number
                ''').fetchone()[0]
                print(f"   Overlap by bill_number: {overlap:,} records")
            except Exception as e:
                print(f"   Could not check overlap: {e}")
                
    except Exception as e:
        print(f"   ❌ Smart merging assessment failed: {e}")
    
    # 5. Sample records
    print(f"\n📋 SAMPLE RECORDS:")
    try:
        cursor.execute('''
            SELECT bill_id, bill_number, data_source, vendor_name, total, bill_date
            FROM FINAL_view_csv_json_bills 
            ORDER BY bill_id
            LIMIT 3
        ''')
        
        samples = cursor.fetchall()
        for bill_id, bill_num, source, vendor, total, date in samples:
            print(f"   {source}: ID={bill_id}, #={bill_num}, Vendor={vendor}, Total={total}, Date={date}")
            
    except Exception as e:
        print(f"   ❌ Sample records failed: {e}")
    
    conn.close()
    
    print(f"\n" + "="*60)
    print(f"🎯 BILLS FINAL VIEW EVALUATION COMPLETE")

if __name__ == "__main__":
    main()
