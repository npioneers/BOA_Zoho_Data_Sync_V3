#!/usr/bin/env python3
"""
Comprehensive Verification: CSV Re-import Success
Check if compound word fields are now populated correctly after re-import
"""
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

def verify_reimport_success():
    """Verify that the CSV re-import successfully populated compound word fields"""
    
    csv_dir = "data/csv/Nangsel Pioneers_Latest"
    db_path = "data/database/production.db"
    
    print("=== CSV RE-IMPORT VERIFICATION ===")
    print(f"CSV Directory: {csv_dir}")
    print(f"Database: {db_path}")
    print()
    
    # Critical compound word fields to verify by table
    critical_fields = {
        "csv_sales_orders": {
            "csv_file": "Sales_Order.csv",
            "compound_fields": [
                ("SalesOrder Number", "sales_order_number"),
                ("SalesOrder ID", "sales_order_id"),
                ("QuantityOrdered", "quantity_ordered"),
                ("QuantityInvoiced", "quantity_invoiced"),
                ("QuantityCancelled", "quantity_cancelled")
            ]
        },
        "csv_customer_payments": {
            "csv_file": "Customer_Payment.csv", 
            "compound_fields": [
                ("CustomerPayment ID", "customer_payment_id"),
                ("CustomerID", "customer_id"),
                ("InvoicePayment ID", "invoice_payment_id")
            ]
        },
        "csv_contacts": {
            "csv_file": "Contacts.csv",
            "compound_fields": [
                ("EmailID", "email_id"),
                ("MobilePhone", "mobile_phone")
            ]
        },
        "csv_purchase_orders": {
            "csv_file": "Purchase_Order.csv",
            "compound_fields": [
                ("QuantityOrdered", "quantity_ordered"),
                ("QuantityReceived", "quantity_received"),
                ("QuantityBilled", "quantity_billed"),
                ("QuantityCancelled", "quantity_cancelled")
            ]
        },
        "csv_vendor_payments": {
            "csv_file": "Vendor_Payment.csv",
            "compound_fields": [
                ("VendorPayment ID", "vendor_payment_id"),
                ("EmailID", "email_id")
            ]
        }
    }
    
    try:
        conn = sqlite3.connect(db_path)
        overall_success = True
        total_fields_tested = 0
        total_fields_working = 0
        
        for table_name, table_info in critical_fields.items():
            print(f"🔍 VERIFYING TABLE: {table_name}")
            print(f"   CSV Source: {table_info['csv_file']}")
            
            csv_path = Path(csv_dir) / table_info['csv_file']
            if not csv_path.exists():
                print(f"   ❌ CSV file not found: {csv_path}")
                continue
            
            try:
                # Read CSV for comparison
                df_csv = pd.read_csv(csv_path, nrows=10)  # Sample for structure check
                csv_columns = list(df_csv.columns)
                
                # Get database record count
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                db_record_count = cursor.fetchone()[0]
                
                print(f"   Database records: {db_record_count:,}")
                
                table_success = True
                fields_working = 0
                
                for csv_field, db_field in table_info['compound_fields']:
                    total_fields_tested += 1
                    
                    # Check if CSV field exists
                    csv_has_field = csv_field in csv_columns
                    
                    if csv_has_field:
                        # Get CSV data sample
                        csv_populated = df_csv[csv_field].notna().sum()
                        csv_sample = df_csv[csv_field].dropna().head(3).tolist()
                    
                    # Check database field population
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE `{db_field}` IS NOT NULL AND `{db_field}` != ''")
                        db_populated = cursor.fetchone()[0]
                        db_rate = (db_populated / db_record_count * 100) if db_record_count > 0 else 0
                        
                        # Get database sample
                        cursor.execute(f"SELECT `{db_field}` FROM {table_name} WHERE `{db_field}` IS NOT NULL AND `{db_field}` != '' LIMIT 3")
                        db_sample = [row[0] for row in cursor.fetchall()]
                        
                        # Determine success
                        field_success = db_populated > 0
                        status = "✅ WORKING" if field_success else "❌ FAILED"
                        
                        print(f"   {status} '{csv_field}' -> '{db_field}'")
                        print(f"      DB Population: {db_populated:,}/{db_record_count:,} ({db_rate:.1f}%)")
                        
                        if csv_has_field:
                            print(f"      CSV Sample: {csv_sample}")
                        if db_sample:
                            print(f"      DB Sample:  {db_sample}")
                        
                        if field_success:
                            fields_working += 1
                            total_fields_working += 1
                        else:
                            table_success = False
                            overall_success = False
                        
                    except sqlite3.OperationalError as e:
                        print(f"   ❌ DB FIELD ERROR '{db_field}': {e}")
                        table_success = False
                        overall_success = False
                    
                    print()
                
                table_status = "✅ ALL WORKING" if table_success else f"⚠️  {fields_working}/{len(table_info['compound_fields'])} WORKING"
                print(f"   📊 Table Result: {table_status}")
                print()
                
            except Exception as e:
                print(f"   ❌ Error analyzing {table_name}: {e}")
                overall_success = False
                print()
        
        conn.close()
        
        # Overall results
        print("=" * 60)
        print("🎯 VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Compound word fields tested: {total_fields_tested}")
        print(f"Fields working correctly: {total_fields_working}")
        print(f"Success rate: {(total_fields_working/total_fields_tested)*100:.1f}%")
        print()
        
        if overall_success and total_fields_working == total_fields_tested:
            print("🎉 SUCCESS: All compound word fields are now working!")
            print("✅ The CSV re-import was successful")
            print("✅ All critical business identifiers are accessible")
            print("✅ CSV DB rebuild package is ready for global runner integration")
        elif total_fields_working > 0:
            print("🟡 PARTIAL SUCCESS: Some fields are working")
            print(f"   Working: {total_fields_working}/{total_fields_tested} fields")
            print("   Some tables may need re-import")
        else:
            print("❌ FAILED: Compound word mapping still not working")
            print("   Check if the fix was applied correctly")
            print("   Verify tables were actually re-imported")
        
        return overall_success and total_fields_working == total_fields_tested
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def test_specific_sales_orders():
    """Test specific sales orders mentioned in the original issue"""
    
    print("\n" + "=" * 60)
    print("🔍 SPECIFIC SALES ORDER VERIFICATION")
    print("=" * 60)
    
    db_path = "data/database/production.db"
    target_orders = ['SO/25-26/00808', 'SO-00009', 'SO-00010', 'SO-00011']
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for order_number in target_orders:
            print(f"Searching for: '{order_number}'")
            
            # Search for the order number
            cursor.execute("""
                SELECT sales_order_id, sales_order_number, order_date, status, customer_name
                FROM csv_sales_orders 
                WHERE sales_order_number LIKE ? 
                LIMIT 5
            """, (f'%{order_number}%',))
            
            results = cursor.fetchall()
            
            if results:
                print(f"   ✅ FOUND {len(results)} record(s):")
                for row in results:
                    print(f"      ID: {row[0]}, Number: '{row[1]}', Date: {row[2]}, Status: {row[3]}, Customer: {row[4]}")
            else:
                print(f"   ❌ NOT FOUND")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error testing specific orders: {e}")

if __name__ == "__main__":
    success = verify_reimport_success()
    test_specific_sales_orders()
    
    if success:
        print("\n🚀 READY FOR GLOBAL RUNNER INTEGRATION!")
    else:
        print("\n⚠️  Additional work needed before global runner integration")
