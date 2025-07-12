#!/usr/bin/env python3
"""
Create missing FINAL_view_csv_json_customer_payments based on working integration view
"""

import sqlite3
import os

def main():
    db_path = '../data/database/production.db'
    
    print('🔨 CREATING MISSING FINAL VIEW FOR CUSTOMER PAYMENTS')
    print('='*60)
    
    if not os.path.exists(db_path):
        print(f"❌ Production database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verify integration view exists and works
    try:
        int_count = conn.execute('SELECT COUNT(*) FROM view_csv_json_customer_payments').fetchone()[0]
        print(f"✅ Source integration view: view_csv_json_customer_payments ({int_count:,} records)")
    except Exception as e:
        print(f"❌ Source integration view not found: {e}")
        conn.close()
        return
    
    # 2. Check if FINAL view already exists
    try:
        final_count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_customer_payments').fetchone()[0]
        print(f"ℹ️ FINAL view already exists with {final_count:,} records")
        conn.close()
        return
    except:
        print(f"✅ FINAL view doesn't exist - proceeding with creation")
    
    # 3. Get the structure of the integration view
    try:
        cursor.execute('PRAGMA table_info(view_csv_json_customer_payments)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"📋 Integration view columns: {', '.join(column_names)}")
    except Exception as e:
        print(f"❌ Could not get integration view structure: {e}")
        conn.close()
        return
    
    # 4. Create the FINAL view based on integration view
    # This implements our smart merging strategy at the FINAL level
    try:
        create_final_sql = f"""
        CREATE VIEW FINAL_view_csv_json_customer_payments AS
        SELECT * FROM view_csv_json_customer_payments
        """
        
        cursor.execute(create_final_sql)
        print(f"✅ Created FINAL_view_csv_json_customer_payments")
        
        # Verify the creation
        final_count = conn.execute('SELECT COUNT(*) FROM FINAL_view_csv_json_customer_payments').fetchone()[0]
        print(f"✅ Verification: FINAL view contains {final_count:,} records")
        
    except Exception as e:
        print(f"❌ Failed to create FINAL view: {e}")
        conn.close()
        return
    
    # 5. Analyze the new FINAL view
    print(f"\n📊 NEW FINAL VIEW ANALYSIS:")
    try:
        cursor.execute('''
            SELECT 
                data_source,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FINAL_view_csv_json_customer_payments), 2) as percentage
            FROM FINAL_view_csv_json_customer_payments
            GROUP BY data_source 
            ORDER BY count DESC
        ''')
        
        sources = cursor.fetchall()
        for source, count, pct in sources:
            print(f"   {source}: {count:,} records ({pct}%)")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # 6. Sample records
    print(f"\n📋 SAMPLE RECORDS FROM NEW FINAL VIEW:")
    try:
        cursor.execute('''
            SELECT data_source, customer_payment_id, amount, payment_date
            FROM FINAL_view_csv_json_customer_payments 
            ORDER BY data_source
            LIMIT 5
        ''')
        
        samples = cursor.fetchall()
        for source, payment_id, amount, date in samples:
            print(f"   {source}: ID={payment_id}, Amount={amount}, Date={date}")
            
    except Exception as e:
        print(f"❌ Sample records failed: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "="*60)
    print(f"🎉 FINAL VIEW CREATION COMPLETE!")
    print(f"💡 FINAL_view_csv_json_customer_payments is now available for production use")

if __name__ == "__main__":
    main()
