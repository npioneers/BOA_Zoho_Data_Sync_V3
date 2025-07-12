#!/usr/bin/env python3
"""
Investigate CSV vs Database record discrepancies
"""

import pandas as pd
import sqlite3

def analyze_csv_vs_database():
    # Compare Item.csv with other CSV files
    csv_files = {
        'Item.csv': '../data/csv/Nangsel Pioneers_Latest/Item.csv',
        'Invoice.csv': '../data/csv/Nangsel Pioneers_Latest/Invoice.csv', 
        'Bill.csv': '../data/csv/Nangsel Pioneers_Latest/Bill.csv',
        'Sales_Order.csv': '../data/csv/Nangsel Pioneers_Latest/Sales_Order.csv'
    }

    print('CSV FILE ANALYSIS:')
    print('='*80)

    for name, path in csv_files.items():
        try:
            df = pd.read_csv(path)
            print(f'{name:<20} | Records: {len(df):>6,} | Columns: {len(df.columns):>2}')
            
            # Check for line items structure
            if 'Item ID' in df.columns:
                unique_items = df['Item ID'].nunique()
                print(f'{"  -> Unique Items":<20} | {unique_items:>6,}')
            
            if 'Invoice ID' in df.columns:
                unique_invoices = df['Invoice ID'].nunique()
                print(f'{"  -> Unique Invoices":<20} | {unique_invoices:>6,}')
                
        except Exception as e:
            print(f'{name:<20} | Error: {e}')

    print('\n' + '='*80)
    print('DATABASE COMPARISON:')
    print('='*80)

    # Check database records
    conn = sqlite3.connect('../data/database/production.db')

    tables = ['csv_items', 'csv_invoices', 'csv_bills', 'csv_sales_orders']
    for table in tables:
        try:
            count_result = conn.execute(f'SELECT COUNT(*) FROM `{table}`').fetchone()
            count = count_result[0] if count_result else 0
            print(f'{table:<20} | Records: {count:>6,}')
        except Exception as e:
            print(f'{table:<20} | Error: {e}')

    conn.close()

    print('\n' + '='*80)
    print('INVESTIGATING ITEM.CSV STRUCTURE:')
    print('='*80)
    
    # Let's look more closely at Item.csv
    df_items = pd.read_csv('../data/csv/Nangsel Pioneers_Latest/Item.csv')
    print(f'Item.csv has {len(df_items):,} records')
    print(f'Item.csv has {len(df_items.columns)} columns')
    print('\nSample Item IDs:')
    print(df_items['Item ID'].head(10).tolist())
    
    print('\nChecking for duplicates in Item.csv:')
    duplicates = df_items['Item ID'].duplicated().sum()
    print(f'Duplicate Item IDs: {duplicates}')
    
    print('\nItem Status distribution:')
    if 'Status' in df_items.columns:
        print(df_items['Status'].value_counts())

if __name__ == "__main__":
    analyze_csv_vs_database()
