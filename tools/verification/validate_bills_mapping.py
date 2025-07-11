#!/usr/bin/env python3
"""
Manual Mapping Validation for Bills
Check and validate mappings between map_json_bills and map_csv_bills
Ensure no duplicate mappings exist (one-to-one or one-to-none only)
"""

import sqlite3
import os
from collections import defaultdict

def validate_bills_mapping():
    db_path = "data/database/production.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("="*100)
        print("BILLS MAPPING VALIDATION: map_json_bills -> map_csv_bills")
        print("="*100)
        
        # Get all CSV fields available for mapping
        cursor.execute("SELECT field_name FROM map_csv_bills ORDER BY field_name")
        csv_fields = [row[0] for row in cursor.fetchall()]
        
        print(f"\nAvailable CSV fields in map_csv_bills ({len(csv_fields)} total):")
        print("-" * 60)
        for i, field in enumerate(csv_fields, 1):
            print(f"{i:2d}. {field}")
        
        # Get current JSON to CSV mappings
        cursor.execute("""
            SELECT field_name, CSV_table, CSV_field 
            FROM map_json_bills 
            WHERE CSV_field IS NOT NULL 
            ORDER BY field_name
        """)
        
        json_mappings = cursor.fetchall()
        
        print(f"\nCurrent JSON to CSV mappings ({len(json_mappings)} total):")
        print("-" * 80)
        print(f"{'JSON Field':<30} {'CSV Table':<15} {'CSV Field'}")
        print("-" * 80)
        
        # Track duplicate mappings
        csv_field_usage = defaultdict(list)
        json_field_usage = defaultdict(list)
        
        for json_field, csv_table, csv_field in json_mappings:
            print(f"{json_field:<30} {csv_table:<15} {csv_field}")
            
            # Track usage for duplicate detection
            csv_field_usage[csv_field].append(json_field)
            json_field_usage[json_field].append(csv_field)
        
        # Check for duplicate mappings
        print(f"\n" + "="*100)
        print("DUPLICATE MAPPING ANALYSIS")
        print("="*100)
        
        # Check CSV fields mapped by multiple JSON fields
        csv_duplicates = {csv_field: json_fields for csv_field, json_fields in csv_field_usage.items() if len(json_fields) > 1}
        
        if csv_duplicates:
            print(f"\n❌ CSV FIELDS MAPPED BY MULTIPLE JSON FIELDS:")
            print("-" * 60)
            for csv_field, json_fields in csv_duplicates.items():
                print(f"  CSV Field: {csv_field}")
                print(f"  Mapped by JSON fields: {', '.join(json_fields)}")
                print()
        else:
            print(f"\n✅ No CSV fields are mapped by multiple JSON fields")
        
        # Check JSON fields mapped to multiple CSV fields  
        json_duplicates = {json_field: csv_fields for json_field, csv_fields in json_field_usage.items() if len(csv_fields) > 1}
        
        if json_duplicates:
            print(f"\n❌ JSON FIELDS MAPPED TO MULTIPLE CSV FIELDS:")
            print("-" * 60)
            for json_field, csv_fields in json_duplicates.items():
                print(f"  JSON Field: {json_field}")
                print(f"  Mapped to CSV fields: {', '.join(csv_fields)}")
                print()
        else:
            print(f"\n✅ No JSON fields are mapped to multiple CSV fields")
        
        # Check unmapped CSV fields
        mapped_csv_fields = set(csv_field_usage.keys())
        unmapped_csv_fields = set(csv_fields) - mapped_csv_fields
        
        print(f"\nUNMAPPED CSV FIELDS ({len(unmapped_csv_fields)} total):")
        print("-" * 60)
        if unmapped_csv_fields:
            for field in sorted(unmapped_csv_fields):
                print(f"  • {field}")
        else:
            print("  All CSV fields are mapped!")
        
        # Summary statistics
        print(f"\n" + "="*100)
        print("MAPPING SUMMARY")
        print("="*100)
        print(f"Total CSV fields available: {len(csv_fields)}")
        print(f"Total CSV fields mapped: {len(mapped_csv_fields)}")
        print(f"Total CSV fields unmapped: {len(unmapped_csv_fields)}")
        print(f"Total JSON fields mapped: {len(json_mappings)}")
        print(f"CSV field coverage: {len(mapped_csv_fields)/len(csv_fields)*100:.1f}%")
        
        # Validation status
        is_valid = len(csv_duplicates) == 0 and len(json_duplicates) == 0
        
        print(f"\n{'✅ MAPPING VALIDATION: PASSED' if is_valid else '❌ MAPPING VALIDATION: FAILED'}")
        
        if not is_valid:
            print("\nISSUES TO FIX:")
            if csv_duplicates:
                print(f"  - {len(csv_duplicates)} CSV fields have multiple JSON mappings")
            if json_duplicates:
                print(f"  - {len(json_duplicates)} JSON fields map to multiple CSV fields")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def show_detailed_field_comparison():
    """Show side-by-side comparison of JSON and CSV fields for manual review"""
    db_path = "data/database/production.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n" + "="*100)
        print("DETAILED FIELD COMPARISON FOR MANUAL REVIEW")
        print("="*100)
        
        # Get JSON fields
        cursor.execute("SELECT field_name, field_type FROM map_json_bills ORDER BY field_name")
        json_fields = cursor.fetchall()
        
        # Get CSV fields
        cursor.execute("SELECT field_name, field_type FROM map_csv_bills ORDER BY field_name")
        csv_fields = cursor.fetchall()
        
        print(f"\nSIDE-BY-SIDE FIELD COMPARISON:")
        print("-" * 100)
        print(f"{'JSON FIELDS':<50} {'CSV FIELDS'}")
        print("-" * 100)
        
        max_rows = max(len(json_fields), len(csv_fields))
        
        for i in range(max_rows):
            json_info = f"{json_fields[i][0]} ({json_fields[i][1]})" if i < len(json_fields) else ""
            csv_info = f"{csv_fields[i][0]} ({csv_fields[i][1]})" if i < len(csv_fields) else ""
            
            print(f"{json_info:<50} {csv_info}")
        
        print(f"\nField Count Summary:")
        print(f"  JSON fields: {len(json_fields)}")
        print(f"  CSV fields: {len(csv_fields)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error in detailed comparison: {e}")

if __name__ == "__main__":
    validate_bills_mapping()
    show_detailed_field_comparison()
