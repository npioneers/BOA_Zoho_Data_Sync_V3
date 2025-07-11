#!/usr/bin/env python3
"""
Detailed Bills Table Analysis
"""

import sqlite3
from pathlib import Path

def analyze_bills_detailed():
    """Detailed analysis of bills table mappings"""
    
    db_path = Path("data/database/production.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("="*100)
    print("DETAILED ANALYSIS: map_json_bills vs map_csv_bills fields")
    print("="*100)
    
    # Get JSON bills fields and current mappings
    cursor.execute("""
        SELECT field_name, field_type, CSV_table, CSV_field 
        FROM map_json_bills 
        ORDER BY field_name
    """)
    
    json_fields = cursor.fetchall()
    
    # Get available CSV bills fields
    cursor.execute("SELECT field_name FROM map_csv_bills ORDER BY field_name")
    csv_fields = [row[0] for row in cursor.fetchall()]
    
    print(f"\n--- JSON BILLS FIELDS ANALYSIS ---")
    print(f"Total JSON fields: {len(json_fields)}")
    print(f"Available CSV fields: {len(csv_fields)}")
    
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
            
            # Detailed logic checks
            if json_field == 'created_time' and mapped_csv_field == 'created_timestamp':
                # This is actually good - both are time fields
                pass
            elif 'time' in json_field.lower() and 'time' not in mapped_csv_field.lower() and 'timestamp' not in mapped_csv_field.lower():
                is_questionable = True
                reason = "Time field mapped to non-time field"
            elif json_field == 'location_id' and mapped_csv_field == 'region':
                is_questionable = True
                reason = "ID field mapped to name field - should map to location_id if available"
            elif 'color' in json_field.lower():
                is_questionable = True
                reason = "Color code should not be mapped to business data"
            elif json_field.startswith('is_') and json_field in ['is_viewed_by_client', 'is_bill_reconciliation_violated', 'is_uber_bill']:
                is_questionable = True
                reason = "Internal flag should not be mapped"
            elif 'precision' in json_field.lower():
                is_questionable = True
                reason = "Precision setting should not be mapped to data field"
            elif json_field == 'vendor_id' and mapped_csv_field == 'vendor_name':
                is_questionable = True
                reason = "ID field mapped to name field"
            
            if is_questionable:
                questionable_mappings.append((json_field, mapped_csv_field, reason))
                print(f"❌ QUESTIONABLE: {mapping_desc} - {reason}")
            else:
                good_mappings.append((json_field, mapped_csv_field))
                print(f"✅ GOOD: {mapping_desc}")
        else:
            unmapped_fields.append(json_field)
            print(f"⭕ UNMAPPED: {json_field} ({field_type})")
    
    print(f"\n--- AVAILABLE CSV FIELDS ---")
    for i, field in enumerate(csv_fields, 1):
        print(f"{i:2d}. {field}")
    
    print(f"\n--- MAPPING SUMMARY ---")
    print(f"JSON fields: {len(json_fields)}")
    print(f"CSV fields available: {len(csv_fields)}")
    print(f"Currently mapped: {mapped_count}")
    print(f"Currently unmapped: {len(unmapped_fields)}")
    print(f"Good mappings: {len(good_mappings)}")
    print(f"Questionable mappings: {len(questionable_mappings)}")
    
    if questionable_mappings:
        print(f"\n--- QUESTIONABLE MAPPINGS TO FIX ---")
        for json_field, csv_field, reason in questionable_mappings:
            print(f"- {json_field} -> {csv_field} ({reason})")
    
    # Check for potential better mappings for unmapped fields
    print(f"\n--- UNMAPPED FIELDS ANALYSIS ---")
    for json_field in unmapped_fields:
        # Look for potential matches
        potential_matches = []
        for csv_field in csv_fields:
            if json_field.lower() in csv_field.lower() or csv_field.lower() in json_field.lower():
                potential_matches.append(csv_field)
        
        if potential_matches:
            print(f"  {json_field}: potential matches -> {', '.join(potential_matches)}")
        else:
            print(f"  {json_field}: no obvious matches")
    
    conn.close()
    return questionable_mappings, good_mappings, unmapped_fields

if __name__ == "__main__":
    analyze_bills_detailed()
