#!/usr/bin/env python3
"""
Detailed Table-by-Table Mapping Analysis
Analyze one JSON table vs corresponding CSV table at a time for precise mapping corrections
"""

import sqlite3
from pathlib import Path

def analyze_table_pair(json_table, csv_table):
    """Analyze a specific JSON table vs its corresponding CSV table"""
    
    db_path = Path("data/database/production.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("="*100)
    print(f"DETAILED ANALYSIS: {json_table} vs {csv_table}")
    print("="*100)
    
    # Get JSON table fields and their current mappings
    cursor.execute(f"""
        SELECT field_name, field_type, CSV_table, CSV_field 
        FROM {json_table} 
        ORDER BY field_name
    """)
    
    json_fields = cursor.fetchall()
    
    # Get CSV table fields
    cursor.execute(f"PRAGMA table_info({csv_table})")
    csv_fields = [row[1] for row in cursor.fetchall()]  # field names only
    
    print(f"\n--- JSON FIELDS IN {json_table} ---")
    print(f"Total: {len(json_fields)} fields")
    
    mapped_count = 0
    questionable_mappings = []
    good_mappings = []
    unmapped_fields = []
    
    for json_field, field_type, mapped_csv_table, mapped_csv_field in json_fields:
        if mapped_csv_table and mapped_csv_field:
            mapped_count += 1
            mapping_desc = f"{json_field} ({field_type}) -> {mapped_csv_field}"
            
            # Check if mapping makes logical sense
            is_questionable = False
            reason = ""
            
            # Check for obvious mismatches
            if 'precision' in json_field.lower() and 'price' in mapped_csv_field.lower():
                is_questionable = True
                reason = "Precision setting mapped to price field"
            elif 'color' in json_field.lower() and 'name' in mapped_csv_field.lower():
                is_questionable = True
                reason = "Color code mapped to name field"
            elif 'time' in json_field.lower() and 'time' not in mapped_csv_field.lower():
                is_questionable = True
                reason = "Time field mapped to non-time field"
            elif 'id' in json_field.lower() and 'name' in mapped_csv_field.lower():
                is_questionable = True
                reason = "ID field mapped to name field"
            elif 'view' in json_field.lower() or 'client' in json_field.lower():
                is_questionable = True
                reason = "View/client tracking field should not be mapped"
            elif json_field.startswith('is_') and not mapped_csv_field.startswith('is_'):
                is_questionable = True
                reason = "Boolean field mapped to non-boolean field"
            
            if is_questionable:
                questionable_mappings.append((mapping_desc, reason))
                print(f"❌ QUESTIONABLE: {mapping_desc} - {reason}")
            else:
                good_mappings.append(mapping_desc)
                print(f"✅ GOOD: {mapping_desc}")
        else:
            unmapped_fields.append(f"{json_field} ({field_type})")
            print(f"⭕ UNMAPPED: {json_field} ({field_type})")
    
    print(f"\n--- CSV FIELDS IN {csv_table} ---")
    print(f"Total: {len(csv_fields)} fields")
    for i, field in enumerate(csv_fields, 1):
        print(f"{i:2d}. {field}")
    
    print(f"\n--- MAPPING SUMMARY ---")
    print(f"JSON fields: {len(json_fields)}")
    print(f"CSV fields: {len(csv_fields)}")
    print(f"Mapped: {mapped_count}")
    print(f"Unmapped: {len(unmapped_fields)}")
    print(f"Good mappings: {len(good_mappings)}")
    print(f"Questionable mappings: {len(questionable_mappings)}")
    
    if questionable_mappings:
        print(f"\n--- QUESTIONABLE MAPPINGS TO FIX ---")
        for mapping, reason in questionable_mappings:
            print(f"- {mapping} ({reason})")
    
    conn.close()
    return questionable_mappings, good_mappings, unmapped_fields

def analyze_credit_notes():
    """Detailed analysis of credit notes table"""
    return analyze_table_pair('map_json_credit_notes', 'csv_credit_notes')

def analyze_bills():
    """Detailed analysis of bills table"""
    return analyze_table_pair('map_json_bills', 'csv_bills')

def analyze_invoices():
    """Detailed analysis of invoices table"""
    return analyze_table_pair('map_json_invoices', 'csv_invoices')

def analyze_items():
    """Detailed analysis of items table"""
    return analyze_table_pair('map_json_items', 'csv_items')

def analyze_contacts():
    """Detailed analysis of contacts table"""
    return analyze_table_pair('map_json_contacts', 'csv_contacts')

def analyze_purchase_orders():
    """Detailed analysis of purchase orders table"""
    return analyze_table_pair('map_json_purchase_orders', 'csv_purchase_orders')

def analyze_sales_orders():
    """Detailed analysis of sales orders table"""
    return analyze_table_pair('map_json_sales_orders', 'csv_sales_orders')

def analyze_customer_payments():
    """Detailed analysis of customer payments table"""
    return analyze_table_pair('map_json_customer_payments', 'csv_customer_payments')

def analyze_vendor_payments():
    """Detailed analysis of vendor payments table"""
    return analyze_table_pair('map_json_vendor_payments', 'csv_vendor_payments')

if __name__ == "__main__":
    print("DETAILED TABLE-BY-TABLE MAPPING ANALYSIS")
    print("Starting with Credit Notes as requested...")
    
    # Start with credit notes as user mentioned the issue there
    questionable, good, unmapped = analyze_credit_notes()
    
    print(f"\nPress Enter to continue to next table or Ctrl+C to stop...")
