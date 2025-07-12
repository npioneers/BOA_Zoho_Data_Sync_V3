#!/usr/bin/env python3
"""
Debug specific ID field mapping issues
"""
import pandas as pd
import sqlite3
import re
from pathlib import Path

def debug_id_field_mapping():
    """Debug why specific ID fields aren't mapping correctly"""
    
    print("=== DEBUGGING ID FIELD MAPPING ===")
    
    csv_dir = "data/csv/Nangsel Pioneers_Latest"
    
    # Test our transformation function
    def csv_to_db_column_name(csv_column: str) -> str:
        column = csv_column
        column = re.sub(r'([a-z])([A-Z])', r'\\1 \\2', column)
        db_column = re.sub(r'[^a-zA-Z0-9]', '_', column)
        db_column = db_column.lower()
        db_column = re.sub(r'_+', '_', db_column)
        db_column = db_column.strip('_')
        return db_column
    
    # Problem fields
    problem_fields = {
        "Sales_Order.csv": ["SalesOrder ID"],
        "Customer_Payment.csv": ["CustomerPayment ID"], 
        "Vendor_Payment.csv": ["VendorPayment ID", "EmailID"]
    }
    
    for csv_file, fields in problem_fields.items():
        print(f"\\n📋 ANALYZING: {csv_file}")
        csv_path = Path(csv_dir) / csv_file
        
        try:
            # Read just the headers and a few rows
            df = pd.read_csv(csv_path, nrows=10)
            
            for field in fields:
                print(f"\\n🔍 FIELD: '{field}'")
                
                if field in df.columns:
                    # Check CSV data
                    non_null_count = df[field].notna().sum()
                    total_count = len(df)
                    sample_values = df[field].dropna().head(5).tolist()
                    
                    print(f"   CSV Status: {non_null_count}/{total_count} populated in sample")
                    print(f"   CSV Sample: {sample_values}")
                    print(f"   CSV Data Types: {[type(v).__name__ for v in sample_values[:3]]}")
                    
                    # Test transformation
                    transformed = csv_to_db_column_name(field)
                    print(f"   Transformation: '{field}' -> '{transformed}'")
                    
                    # Check if values might be too large for database
                    if sample_values:
                        max_length = max(len(str(v)) for v in sample_values)
                        print(f"   Max value length: {max_length}")
                        
                        # Check for very large numbers (potential overflow)
                        if any(isinstance(v, (int, float)) and abs(v) > 1e15 for v in sample_values):
                            print("   ⚠️  WARNING: Very large numbers detected (potential overflow)")
                else:
                    print(f"   ❌ Field '{field}' not found in CSV")
                    print(f"   Available fields: {list(df.columns)[:10]}...")
                    
        except Exception as e:
            print(f"   ❌ Error reading {csv_file}: {e}")

def test_direct_import():
    """Test importing a small sample directly to see what happens"""
    
    print("\\n" + "=" * 60)
    print("🧪 DIRECT IMPORT TEST")
    print("=" * 60)
    
    csv_dir = "data/csv/Nangsel Pioneers_Latest"
    
    # Test sales orders specifically
    csv_path = Path(csv_dir) / "Sales_Order.csv"
    
    try:
        # Read just 3 rows
        df = pd.read_csv(csv_path, nrows=3)
        
        print("Original CSV columns and data:")
        print(f"Columns: {list(df.columns)}")
        
        # Focus on the problematic field
        if 'SalesOrder ID' in df.columns:
            print(f"\\nSalesOrder ID data:")
            print(df[['SalesOrder ID', 'SalesOrder Number']].to_string())
            
            # Test our transformation
            def csv_to_db_column_name(csv_column: str) -> str:
                column = csv_column
                column = re.sub(r'([a-z])([A-Z])', r'\\1 \\2', column)
                db_column = re.sub(r'[^a-zA-Z0-9]', '_', column)
                db_column = db_column.lower()
                db_column = re.sub(r'_+', '_', db_column)
                db_column = db_column.strip('_')
                return db_column
            
            # Apply column transformation
            column_mapping = {}
            for col in df.columns:
                new_col = csv_to_db_column_name(col)
                column_mapping[col] = new_col
            
            print(f"\\nColumn mapping for ID fields:")
            for orig, new in column_mapping.items():
                if 'id' in orig.lower() or 'ID' in orig:
                    print(f"  '{orig}' -> '{new}'")
            
            # Transform the dataframe
            df_transformed = df.rename(columns=column_mapping)
            
            # Check the transformed data
            if 'sales_order_id' in df_transformed.columns:
                print(f"\\nTransformed sales_order_id data:")
                print(df_transformed[['sales_order_id', 'sales_order_number']])
                print(f"Data types: {df_transformed[['sales_order_id', 'sales_order_number']].dtypes}")
                
                # Check for NaN or empty values
                sales_order_id_data = df_transformed['sales_order_id']
                print(f"\\nData analysis:")
                print(f"  Non-null count: {sales_order_id_data.notna().sum()}")
                print(f"  Null count: {sales_order_id_data.isna().sum()}")
                print(f"  Empty string count: {(sales_order_id_data == '').sum()}")
                print(f"  Values: {sales_order_id_data.tolist()}")
                
    except Exception as e:
        print(f"❌ Direct import test failed: {e}")

if __name__ == "__main__":
    debug_id_field_mapping()
    test_direct_import()
