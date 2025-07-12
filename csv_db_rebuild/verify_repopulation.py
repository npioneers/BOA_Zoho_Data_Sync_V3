#!/usr/bin/env python3
"""
Verify CSV re-population worked correctly for compound word fields
Database: production.db in data/database folder
"""
import sqlite3
import pandas as pd
from pathlib import Path

def verify_repopulation():
    """Verify that compound word fields are now properly populated"""
    
    # Full absolute path to the database
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    csv_dir = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\csv\Nangsel Pioneers_Latest"
    
    print("=== COMPOUND WORD FIELD VERIFICATION ===")
    print(f"Database: {db_path}")
    print(f"CSV Directory: {csv_dir}")
    print()
    
    # Check database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    print(f"✅ Database found ({Path(db_path).stat().st_size / (1024*1024):.1f} MB)")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Critical compound word fields to verify
        verification_checks = [
            {
                "table": "csv_sales_orders",
                "csv_file": "Sales_Order.csv",
                "compound_fields": [
                    ("sales_order_id", "SalesOrder ID"),
                    ("sales_order_number", "SalesOrder Number"),
                    ("quantity_ordered", "QuantityOrdered"),
                    ("quantity_invoiced", "QuantityInvoiced"),
                    ("quantity_cancelled", "QuantityCancelled")
                ],
                "critical_test": "sales_order_number"
            },
            {
                "table": "csv_customer_payments", 
                "csv_file": "Customer_Payment.csv",
                "compound_fields": [
                    ("customer_payment_id", "CustomerPayment ID"),
                    ("customer_id", "CustomerID"),
                    ("invoice_payment_id", "InvoicePayment ID")
                ],
                "critical_test": "customer_payment_id"
            },
            {
                "table": "csv_purchase_orders",
                "csv_file": "Purchase_Order.csv", 
                "compound_fields": [
                    ("quantity_ordered", "QuantityOrdered"),
                    ("quantity_cancelled", "QuantityCancelled"),
                    ("quantity_received", "QuantityReceived"),
                    ("quantity_billed", "QuantityBilled")
                ],
                "critical_test": "quantity_ordered"
            },
            {
                "table": "csv_contacts",
                "csv_file": "Contacts.csv",
                "compound_fields": [
                    ("email_id", "EmailID"),
                    ("mobile_phone", "MobilePhone")
                ],
                "critical_test": "email_id"
            },
            {
                "table": "csv_vendor_payments",
                "csv_file": "Vendor_Payment.csv",
                "compound_fields": [
                    ("vendor_payment_id", "VendorPayment ID"),
                    ("email_id", "EmailID")
                ],
                "critical_test": "vendor_payment_id"
            }
        ]
        
        total_checks = 0
        passed_checks = 0
        
        for check in verification_checks:
            table_name = check["table"]
            csv_file = check["csv_file"]
            
            print(f"📋 CHECKING TABLE: {table_name}")
            print(f"   CSV Source: {csv_file}")
            
            # Get total record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            print(f"   Total records: {total_records:,}")
            
            # Check each compound word field
            table_passed = True
            for db_field, csv_field in check["compound_fields"]:
                total_checks += 1
                
                try:
                    # Check population rate
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {db_field} IS NOT NULL AND {db_field} != ''")
                    populated_count = cursor.fetchone()[0]
                    population_rate = (populated_count / total_records * 100) if total_records > 0 else 0
                    
                    status = "✅ PASS" if population_rate > 80 else "❌ FAIL"
                    print(f"   {status} {db_field}: {populated_count:,}/{total_records:,} ({population_rate:.1f}%)")
                    
                    if population_rate > 80:
                        passed_checks += 1
                    else:
                        table_passed = False
                        
                    # Show sample values for critical field
                    if db_field == check["critical_test"] and populated_count > 0:
                        cursor.execute(f"SELECT {db_field} FROM {table_name} WHERE {db_field} IS NOT NULL AND {db_field} != '' LIMIT 3")
                        samples = [row[0] for row in cursor.fetchall()]
                        print(f"     Sample values: {samples}")
                        
                except Exception as e:
                    print(f"   ❌ ERROR checking {db_field}: {e}")
                    table_passed = False
            
            # Special test for sales orders
            if table_name == "csv_sales_orders":
                print(f"   🎯 CRITICAL TEST: Historical sales order SO/25-26/00808")
                cursor.execute("SELECT COUNT(*) FROM csv_sales_orders WHERE sales_order_number LIKE '%SO/25-26/00808%'")
                historical_count = cursor.fetchone()[0]
                if historical_count > 0:
                    print(f"   ✅ FOUND: {historical_count} records with SO/25-26/00808")
                else:
                    print(f"   ❌ NOT FOUND: SO/25-26/00808 not accessible")
                    table_passed = False
            
            print(f"   📊 Table Status: {'✅ PASS' if table_passed else '❌ FAIL'}")
            print()
        
        conn.close()
        
        # Summary
        print("=" * 60)
        print("🎯 VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total field checks: {total_checks}")
        print(f"Passed checks: {passed_checks}")
        print(f"Success rate: {(passed_checks/total_checks*100):.1f}%")
        print()
        
        if passed_checks == total_checks:
            print("🎉 SUCCESS: All compound word fields are properly populated!")
            print("✅ The compound word fix and re-import worked correctly")
            print("✅ CSV DB rebuild package is ready for global runner integration")
        elif passed_checks > total_checks * 0.8:
            print("🟡 MOSTLY SUCCESSFUL: Most fields are working, minor issues remain")
            print("⚠️  Some fields may need individual table re-import")
        else:
            print("❌ SIGNIFICANT ISSUES: Many compound word fields still not populating")
            print("🔧 May need to re-run the re-import process")
        
    except Exception as e:
        print(f"❌ Database verification error: {e}")

if __name__ == "__main__":
    verify_repopulation()
