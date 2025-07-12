#!/usr/bin/env python3
"""
Investigate CSV Column Mapping Issue for Sales Order Numbers
Root Cause Analysis and Solution Identification
"""
import pandas as pd
import sqlite3
from pathlib import Path
import sys
import os

# Add path for CSV rebuild runner
sys.path.append('../csv_db_rebuild')

def investigate_column_mapping():
    """Investigate why SalesOrder Number is not mapping to database"""
    
    print("=== CSV COLUMN MAPPING INVESTIGATION ===")
    print("Issue: SalesOrder Number not populating in database")
    print()
    
    # Step 1: Compare CSV headers with database columns
    csv_path = "../data/csv/Nangsel Pioneers_Latest/Sales_Order.csv"
    db_path = "../data/database/production.db"
    
    print("1. READING CSV HEADERS...")
    try:
        df = pd.read_csv(csv_path, nrows=5)  # Just read a few rows to get headers
        csv_headers = list(df.columns)
        print(f"   CSV headers count: {len(csv_headers)}")
        print(f"   Target column: 'SalesOrder Number' (position {csv_headers.index('SalesOrder Number') + 1})")
        print()
        
        # Show relevant columns
        print("2. RELEVANT CSV COLUMNS:")
        for i, header in enumerate(csv_headers):
            if 'order' in header.lower() or 'sales' in header.lower() or header == 'SalesOrder Number':
                print(f"   {i+1:2d}. '{header}'")
        print()
        
    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
        return
    
    # Step 2: Check database schema
    print("3. DATABASE SCHEMA CHECK...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(csv_sales_orders)")
        db_columns = cursor.fetchall()
        
        print(f"   Database columns count: {len(db_columns)}")
        
        # Find sales order related columns
        print("   Sales order related columns:")
        for col_id, name, data_type, not_null, default_val, pk in db_columns:
            if 'order' in name.lower() or 'sales' in name.lower():
                print(f"   {col_id+1:2d}. '{name}' ({data_type})")
        print()
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return
    
    # Step 3: Test column name transformation
    print("4. COLUMN NAME TRANSFORMATION TEST...")
    csv_column = "SalesOrder Number"
    expected_db_column = "sales_order_number"
    
    print(f"   CSV column: '{csv_column}'")
    print(f"   Expected DB column: '{expected_db_column}'")
    
    # Test common transformations
    transformations = {
        "lowercase": csv_column.lower(),
        "replace_spaces_with_underscores": csv_column.lower().replace(' ', '_'),
        "remove_special_chars": ''.join(c.lower() if c.isalnum() else '_' for c in csv_column),
        "pandas_default": csv_column.lower().replace(' ', '_').replace('-', '_')
    }
    
    print("   Transformation tests:")
    for method, result in transformations.items():
        match = "✅" if result == expected_db_column else "❌"
        print(f"   {match} {method}: '{csv_column}' -> '{result}'")
    print()
    
    # Step 4: Check actual CSV import process
    print("5. CSV IMPORT PROCESS INVESTIGATION...")
    
    # Try to simulate the CSV import column mapping
    try:
        # Read a small sample with pandas (how the CSV rebuild likely works)
        df_sample = pd.read_csv(csv_path, nrows=10)
        
        print("   Pandas column name handling:")
        for i, original_col in enumerate(df_sample.columns):
            if 'salesorder' in original_col.lower() or 'order' in original_col.lower():
                # Common pandas transformations for SQL
                clean_col = original_col.lower().replace(' ', '_').replace('-', '_')
                print(f"   '{original_col}' -> '{clean_col}'")
        print()
        
        # Check if the exact data exists
        if 'SalesOrder Number' in df_sample.columns:
            so_numbers = df_sample['SalesOrder Number'].dropna().tolist()
            print(f"   Sample SalesOrder Numbers from CSV: {so_numbers[:5]}")
        else:
            print("   ❌ SalesOrder Number column not found in sample")
        print()
        
    except Exception as e:
        print(f"   ❌ CSV import simulation error: {e}")
    
    # Step 5: Check mapping files
    print("6. CHECKING MAPPING CONFIGURATION...")
    
    # Look for mapping files that might control the column mapping
    mapping_files = [
        "../csv_db_rebuild/mappings.py",
        "../json_db_mapper/mappings.py", 
        "../src/data_pipeline/mappings/",
        "../csv_db_rebuild/config/",
    ]
    
    for mapping_file in mapping_files:
        if Path(mapping_file).exists():
            print(f"   📁 Found: {mapping_file}")
        else:
            print(f"   ❌ Not found: {mapping_file}")
    print()
    
    # Step 6: Recommendations
    print("7. RECOMMENDED SOLUTIONS...")
    print("   Option 1: Fix column name mapping in CSV import process")
    print("   Option 2: Check if CSV rebuild runner has column mapping configuration")
    print("   Option 3: Verify pandas column name transformation logic")
    print("   Option 4: Test single-table import with debug logging")
    print()
    
    print("8. IMMEDIATE TESTING STEPS...")
    print("   1. Run single table CSV import for sales_orders with verbose logging")
    print("   2. Check if column mapping can be manually corrected")
    print("   3. Verify other tables have similar mapping issues")
    print("   4. Test with smaller CSV sample to isolate the issue")
    print()

def test_manual_import():
    """Test manual import of sales order data to identify mapping issue"""
    
    print("=== MANUAL IMPORT TEST ===")
    csv_path = "../data/csv/Nangsel Pioneers_Latest/Sales_Order.csv"
    
    try:
        # Read CSV with pandas
        df = pd.read_csv(csv_path, nrows=5)
        
        print(f"CSV columns: {len(df.columns)}")
        print(f"SalesOrder Number column exists: {'SalesOrder Number' in df.columns}")
        
        if 'SalesOrder Number' in df.columns:
            so_data = df[['SalesOrder ID', 'SalesOrder Number', 'Order Date', 'Status']].head()
            print("\\nSample data from CSV:")
            print(so_data.to_string(index=False))
            
            # Test column name transformation
            print("\\nColumn name transformations:")
            original = 'SalesOrder Number'
            transformed = original.lower().replace(' ', '_')
            print(f"'{original}' -> '{transformed}'")
            
            # This should map to 'sales_order_number' in database
            expected = 'sales_order_number'
            print(f"Expected DB column: '{expected}'")
            print(f"Transformation correct: {transformed == expected}")
        
    except Exception as e:
        print(f"❌ Manual import test failed: {e}")

if __name__ == "__main__":
    investigate_column_mapping()
    print("=" * 60)
    test_manual_import()
