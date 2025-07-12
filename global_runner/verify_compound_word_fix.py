#!/usr/bin/env python3
"""
Verify the compound word fix has been applied correctly
"""
import sys
import os
import re
from pathlib import Path

# Add CSV rebuild path
sys.path.append('../csv_db_rebuild')

def test_updated_function():
    """Test the updated csv_to_db_column_name function"""
    
    print("=== VERIFYING COMPOUND WORD FIX ===")
    print()
    
    try:
        # Import the updated function
        from runner_csv_db_rebuild import CSVDatabaseRebuildRunner
        
        # Create instance to test the function
        runner = CSVDatabaseRebuildRunner()
        
        # Test critical compound word cases
        test_cases = [
            ("SalesOrder Number", "sales_order_number"),
            ("SalesOrder ID", "sales_order_id"),
            ("CustomerID", "customer_id"),
            ("PurchaseOrder", "purchase_order"),
            ("QuantityOrdered", "quantity_ordered"),
            ("EmailID", "email_id"),
            ("CustomerPayment ID", "customer_payment_id"),
            ("Order Date", "order_date"),  # Should remain unchanged
            ("Item Name", "item_name"),    # Should remain unchanged
        ]
        
        print("TESTING UPDATED FUNCTION:")
        print("-" * 50)
        
        all_passed = True
        
        for csv_col, expected in test_cases:
            result = runner.csv_to_db_column_name(csv_col)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} '{csv_col}' -> '{result}' (expected: '{expected}')")
            
            if result != expected:
                all_passed = False
        
        print()
        if all_passed:
            print("🎯 SUCCESS: All compound word transformations are now working correctly!")
            print("📋 The fix has been successfully applied.")
            print()
            print("NEXT STEPS:")
            print("1. Re-import the affected CSV tables manually")
            print("2. Verify that critical business fields are now populated")
            print("3. Focus on these priority tables first:")
            print("   - csv_sales_orders (SalesOrder Number, SalesOrder ID)")
            print("   - csv_customer_payments (CustomerPayment ID, CustomerID)")
            print("   - csv_purchase_orders (Quantity fields)")
        else:
            print("❌ ISSUE: Some transformations are still not working correctly.")
            print("Please check the function implementation.")
            
    except Exception as e:
        print(f"❌ Error testing function: {e}")

if __name__ == "__main__":
    test_updated_function()
