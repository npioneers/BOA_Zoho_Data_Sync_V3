#!/usr/bin/env python3
"""
Comprehensive Column Mapping Analysis
Check for mismatches across all CSV tables before applying fixes
"""
import pandas as pd
import sqlite3
from pathlib import Path
import re
from typing import Dict, List, Tuple

def original_csv_to_db_column_name(csv_column: str) -> str:
    """Original function that's causing issues"""
    db_column = re.sub(r'[^a-zA-Z0-9]', '_', csv_column)
    db_column = db_column.lower()
    db_column = re.sub(r'_+', '_', db_column)
    db_column = db_column.strip('_')
    return db_column

def fixed_csv_to_db_column_name(csv_column: str) -> str:
    """Fixed function with compound word handling"""
    column = csv_column
    # Split compound words: SalesOrder -> Sales Order
    column = re.sub(r'([a-z])([A-Z])', r'\1 \2', column)
    # Convert spaces and special characters to underscores
    db_column = re.sub(r'[^a-zA-Z0-9]', '_', column)
    db_column = db_column.lower()
    db_column = re.sub(r'_+', '_', db_column)
    db_column = db_column.strip('_')
    return db_column

def analyze_all_table_mappings():
    """Analyze column mappings for all CSV tables"""
    
    csv_dir = "../data/csv/Nangsel Pioneers_Latest"
    db_path = "../data/database/production.db"
    
    # Table mappings from the CSV rebuild package
    table_mappings = {
        "csv_invoices": "Invoice.csv",
        "csv_items": "Item.csv", 
        "csv_contacts": "Contacts.csv",
        "csv_bills": "Bill.csv",
        "csv_customer_payments": "Customer_Payment.csv",
        "csv_vendor_payments": "Vendor_Payment.csv",
        "csv_sales_orders": "Sales_Order.csv",
        "csv_purchase_orders": "Purchase_Order.csv",
        "csv_credit_notes": "Credit_Note.csv"
    }
    
    print("=== COMPREHENSIVE COLUMN MAPPING ANALYSIS ===")
    print(f"CSV Directory: {csv_dir}")
    print(f"Database: {db_path}")
    print()
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        total_mismatches = 0
        tables_with_issues = []
        
        for table_name, csv_file in table_mappings.items():
            print(f"📋 ANALYZING TABLE: {table_name}")
            print(f"   CSV File: {csv_file}")
            
            csv_path = Path(csv_dir) / csv_file
            if not csv_path.exists():
                print(f"   ❌ CSV file not found: {csv_path}")
                continue
            
            try:
                # Read CSV headers only
                df = pd.read_csv(csv_path, nrows=0)  # Just headers
                csv_columns = list(df.columns)
                
                # Get database columns
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                db_columns_info = cursor.fetchall()
                db_columns = [row[1] for row in db_columns_info if not row[1].startswith(('created_timestamp', 'updated_timestamp', 'data_source'))]
                
                print(f"   CSV Columns: {len(csv_columns)}")
                print(f"   DB Columns: {len(db_columns)} (excluding system columns)")
                
                # Analyze mappings
                mismatches_original = []
                mismatches_fixed = []
                compound_word_issues = []
                
                for csv_col in csv_columns:
                    original_mapping = original_csv_to_db_column_name(csv_col)
                    fixed_mapping = fixed_csv_to_db_column_name(csv_col)
                    
                    # Check if mapping exists in database
                    original_exists = original_mapping in db_columns
                    fixed_exists = fixed_mapping in db_columns
                    
                    if not original_exists and fixed_exists:
                        mismatches_original.append((csv_col, original_mapping, fixed_mapping))
                        compound_word_issues.append(csv_col)
                    elif not original_exists and not fixed_exists:
                        mismatches_fixed.append((csv_col, original_mapping, fixed_mapping))
                
                print(f"   Column Mapping Issues:")
                print(f"     ❌ Original function mismatches: {len(mismatches_original)}")
                print(f"     ✅ Fixed by compound word handling: {len(mismatches_original)}")
                print(f"     ⚠️  Still problematic after fix: {len(mismatches_fixed)}")
                
                if mismatches_original:
                    print(f"   🔧 COMPOUND WORD ISSUES (Will be fixed):")
                    for csv_col, orig, fixed in mismatches_original[:5]:  # Show first 5
                        print(f"     '{csv_col}' -> '{orig}' ❌ -> '{fixed}' ✅")
                    if len(mismatches_original) > 5:
                        print(f"     ... and {len(mismatches_original) - 5} more")
                
                if mismatches_fixed:
                    print(f"   ⚠️  OTHER ISSUES (Need investigation):")
                    for csv_col, orig, fixed in mismatches_fixed[:3]:  # Show first 3
                        print(f"     '{csv_col}' -> '{orig}' -> '{fixed}' (no DB column found)")
                    if len(mismatches_fixed) > 3:
                        print(f"     ... and {len(mismatches_fixed) - 3} more")
                
                total_mismatches += len(mismatches_original)
                if mismatches_original or mismatches_fixed:
                    tables_with_issues.append(table_name)
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error analyzing {table_name}: {e}")
                print()
        
        conn.close()
        
        # Summary
        print("=" * 60)
        print("🎯 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Tables analyzed: {len(table_mappings)}")
        print(f"Tables with mapping issues: {len(tables_with_issues)}")
        print(f"Total compound word issues found: {total_mismatches}")
        print()
        
        if tables_with_issues:
            print("📋 TABLES AFFECTED BY COMPOUND WORD BUG:")
            for table in tables_with_issues:
                print(f"   - {table}")
            print()
            
            print("🔧 RECOMMENDED ACTION:")
            print("   1. Apply compound word fix to csv_to_db_column_name() function")
            print("   2. Re-import ALL affected tables (not just sales_orders)")
            print("   3. Verify critical business fields populate correctly")
            print("   4. Test with smaller dataset first")
        else:
            print("✅ No compound word issues found!")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")

def check_specific_compound_words():
    """Check for common compound word patterns that might be affected"""
    
    print("\n" + "=" * 60)
    print("🔍 COMPOUND WORD PATTERN ANALYSIS")
    print("=" * 60)
    
    # Common compound words in business data
    test_cases = [
        "SalesOrder Number",
        "SalesOrder ID", 
        "PurchaseOrder Number",
        "PurchaseOrder ID",
        "CustomerName",
        "CustomerID", 
        "ProductID",
        "ItemName",
        "ItemCode",
        "ItemTotal",
        "SubTotal",
        "TotalAmount",
        "PaymentDate",
        "PaymentTerms",
        "BillingAddress",
        "ShippingAddress",
        "CreditNote",
        "DebitNote",
        "TaxAmount",
        "DiscountAmount",
        "AccountCode"
    ]
    
    print("Testing common compound word transformations:")
    print()
    
    problematic_cases = []
    
    for test_case in test_cases:
        original = original_csv_to_db_column_name(test_case)
        fixed = fixed_csv_to_db_column_name(test_case)
        
        if original != fixed:
            status = "🔧 WILL FIX"
            problematic_cases.append(test_case)
        else:
            status = "✅ OK"
        
        print(f"{status} '{test_case}'")
        print(f"     Original: '{original}'")
        print(f"     Fixed:    '{fixed}'")
        print()
    
    print(f"🎯 SUMMARY: {len(problematic_cases)} compound word patterns will be fixed")
    print()
    
    return problematic_cases

if __name__ == "__main__":
    analyze_all_table_mappings()
    compound_issues = check_specific_compound_words()
    
    print("=" * 60)
    print("📋 FINAL RECOMMENDATIONS")
    print("=" * 60)
    print("1. Apply the compound word fix to handle all identified patterns")
    print("2. Focus re-import on tables with confirmed mapping issues")
    print("3. Verify critical business identifier fields after fix")
    print("4. Monitor for any remaining unmapped columns")
    print(f"5. Expected improvement: {len(compound_issues)} compound word patterns fixed")
