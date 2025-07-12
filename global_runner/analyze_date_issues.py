#!/usr/bin/env python3
"""
Analyze date parsing issues in database tables
"""

import sqlite3

def analyze_date_issues():
    conn = sqlite3.connect('../data/database/production.db')
    cursor = conn.cursor()
    
    print("DATE PARSING ISSUE ANALYSIS")
    print("=" * 50)
    
    # Check tables with date errors
    tables_with_errors = ['json_items', 'json_contacts']
    
    for table in tables_with_errors:
        print(f'\n{table.upper()}:')
        
        # Get sample last_modified_time values
        cursor.execute(f'SELECT last_modified_time FROM {table} WHERE last_modified_time IS NOT NULL LIMIT 5')
        samples = cursor.fetchall()
        print(f'  Sample last_modified_time values:')
        for i, sample in enumerate(samples):
            print(f'    {i+1}: "{sample[0]}"')
    
    # Check working tables
    print(f'\nWORKING TABLES:')
    for table in ['json_customer_payments', 'json_vendor_payments']:
        print(f'\n{table}:')
        cursor.execute(f'SELECT date FROM {table} WHERE date IS NOT NULL LIMIT 5')
        samples = cursor.fetchall()
        print(f'  Sample date values:')
        for i, sample in enumerate(samples):
            print(f'    {i+1}: "{sample[0]}"')
    
    # Check tables with no date columns
    print(f'\nTABLES WITH NO DATE COLUMNS:')
    no_date_tables = ['json_invoices', 'json_bills', 'json_sales_orders', 'json_purchase_orders', 'json_credit_notes']
    
    for table in no_date_tables:
        cursor.execute(f'PRAGMA table_info({table})')
        columns = [col[1] for col in cursor.fetchall()]
        potential_date_cols = [col for col in columns if any(word in col.lower() for word in ['date', 'time', 'created', 'modified', 'updated'])]
        print(f'\n{table}:')
        print(f'  Potential date columns: {potential_date_cols if potential_date_cols else "None found"}')
        
        # Show first few columns to understand structure
        print(f'  First 5 columns: {columns[:5]}')
        
        # Check for specific common date field names
        common_date_fields = ['invoice_date', 'bill_date', 'order_date', 'created_time', 'last_modified_time']
        found_fields = [field for field in common_date_fields if field in columns]
        if found_fields:
            print(f'  Found common date fields: {found_fields}')
            
            # Sample values from the first found date field
            field = found_fields[0]
            cursor.execute(f'SELECT {field} FROM {table} WHERE {field} IS NOT NULL LIMIT 3')
            samples = cursor.fetchall()
            print(f'  Sample {field} values:')
            for i, sample in enumerate(samples):
                print(f'    {i+1}: "{sample[0]}"')
    
    conn.close()

if __name__ == "__main__":
    analyze_date_issues()
