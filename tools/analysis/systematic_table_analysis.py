#!/usr/bin/env python3
"""
Systematic Table-by-Table Analysis and Correction
Go through each table pair systematically to identify and fix mapping issues
"""

import sqlite3
from pathlib import Path

class TableAnalyzer:
    def __init__(self):
        self.db_path = Path("data/database/production.db")
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
    
    def analyze_table(self, json_table, csv_mapping_table):
        """Analyze a specific table pair"""
        
        print("="*100)
        print(f"ANALYZING: {json_table} vs {csv_mapping_table}")
        print("="*100)
        
        # Get JSON fields and current mappings
        self.cursor.execute(f"""
            SELECT field_name, field_type, CSV_table, CSV_field 
            FROM {json_table} 
            ORDER BY field_name
        """)
        
        json_fields = self.cursor.fetchall()
        
        # Get available CSV fields
        self.cursor.execute(f"SELECT field_name FROM {csv_mapping_table} ORDER BY field_name")
        csv_fields = [row[0] for row in self.cursor.fetchall()]
        
        print(f"JSON fields: {len(json_fields)}, CSV fields: {len(csv_fields)}")
        
        issues = {
            'duplicate_targets': [],
            'questionable_mappings': [],
            'good_mappings': [],
            'unmapped_with_potential': []
        }
        
        # Track which CSV fields are mapped to
        csv_usage = {}
        
        # Analyze each JSON field
        for json_field, field_type, mapped_csv_table, mapped_csv_field in json_fields:
            if mapped_csv_table and mapped_csv_field:
                # Track CSV field usage
                if mapped_csv_field not in csv_usage:
                    csv_usage[mapped_csv_field] = []
                csv_usage[mapped_csv_field].append(json_field)
                
                # Check for questionable mappings
                is_questionable, reason = self.is_questionable_mapping(json_field, mapped_csv_field, field_type)
                
                if is_questionable:
                    issues['questionable_mappings'].append((json_field, mapped_csv_field, reason))
                else:
                    issues['good_mappings'].append((json_field, mapped_csv_field))
            else:
                # Check for potential mappings
                potential = self.find_potential_matches(json_field, csv_fields)
                if potential:
                    issues['unmapped_with_potential'].append((json_field, potential))
        
        # Find duplicate targets
        for csv_field, json_fields_list in csv_usage.items():
            if len(json_fields_list) > 1:
                issues['duplicate_targets'].append((csv_field, json_fields_list))
        
        return issues
    
    def is_questionable_mapping(self, json_field, csv_field, field_type):
        """Check if a mapping is questionable"""
        
        json_lower = json_field.lower()
        csv_lower = csv_field.lower()
        
        # Time field checks
        if 'time' in json_lower and 'time' not in csv_lower and 'timestamp' not in csv_lower:
            return True, "Time field mapped to non-time field"
        
        # Color code checks
        if 'color' in json_lower and 'color' not in csv_lower:
            return True, "Color field mapped to non-color field"
        
        # Precision checks
        if 'precision' in json_lower and 'precision' not in csv_lower:
            return True, "Precision setting mapped to data field"
        
        # View/client tracking checks
        if any(word in json_lower for word in ['view', 'client_viewed', 'emailed']):
            return True, "View/tracking field should not be mapped"
        
        # ID to name mapping checks (sometimes OK, sometimes not)
        if json_field.endswith('_id') and ('name' in csv_lower or csv_field.endswith('_name')):
            # Some ID->name mappings are OK (like vendor_id -> vendor_name)
            # Others are questionable (like template_id -> template_name might be better as template_type)
            if json_field in ['vendor_id', 'customer_id', 'item_id']:
                return False, "Acceptable ID to name mapping"
            else:
                return True, "ID field mapped to name field - check if appropriate"
        
        # Boolean field checks
        if json_field.startswith('is_') and not csv_field.startswith('is_'):
            # Some boolean mappings are OK if they make sense
            if 'status' in csv_lower or 'flag' in csv_lower:
                return False, "Boolean to status mapping"
            else:
                return True, "Boolean field mapped to non-boolean field"
        
        return False, "Mapping appears good"
    
    def find_potential_matches(self, json_field, csv_fields):
        """Find potential matches for unmapped fields"""
        
        json_lower = json_field.lower()
        potential = []
        
        for csv_field in csv_fields:
            csv_lower = csv_field.lower()
            
            # Exact match
            if json_lower == csv_lower:
                potential.append((csv_field, "exact match"))
            # Contains match
            elif json_lower in csv_lower or csv_lower in json_lower:
                potential.append((csv_field, "contains match"))
            # Similar words
            elif any(word in csv_lower for word in json_lower.split('_') if len(word) > 2):
                potential.append((csv_field, "word match"))
        
        return potential[:3]  # Return top 3 matches
    
    def print_issues(self, table_name, issues):
        """Print analysis results"""
        
        print(f"\n--- ANALYSIS RESULTS FOR {table_name} ---")
        
        if issues['duplicate_targets']:
            print(f"\n❌ DUPLICATE TARGETS ({len(issues['duplicate_targets'])}):")
            for csv_field, json_fields_list in issues['duplicate_targets']:
                print(f"  {csv_field} <- {', '.join(json_fields_list)}")
        
        if issues['questionable_mappings']:
            print(f"\n❓ QUESTIONABLE MAPPINGS ({len(issues['questionable_mappings'])}):")
            for json_field, csv_field, reason in issues['questionable_mappings']:
                print(f"  {json_field} -> {csv_field} ({reason})")
        
        print(f"\n✅ GOOD MAPPINGS ({len(issues['good_mappings'])}):")
        for json_field, csv_field in issues['good_mappings'][:5]:  # Show first 5
            print(f"  {json_field} -> {csv_field}")
        if len(issues['good_mappings']) > 5:
            print(f"  ... and {len(issues['good_mappings']) - 5} more")
        
        if issues['unmapped_with_potential']:
            print(f"\n⭕ UNMAPPED WITH POTENTIAL ({len(issues['unmapped_with_potential'])}):")
            for json_field, potential in issues['unmapped_with_potential'][:5]:  # Show first 5
                if potential:
                    best_match = potential[0]
                    print(f"  {json_field} -> could map to {best_match[0]} ({best_match[1]})")
        
        total_issues = len(issues['duplicate_targets']) + len(issues['questionable_mappings'])
        print(f"\n📊 SUMMARY: {total_issues} issues found, {len(issues['good_mappings'])} good mappings")
        
        return total_issues
    
    def close(self):
        self.conn.close()

def main():
    """Analyze all main tables"""
    
    analyzer = TableAnalyzer()
    
    # Define table pairs to analyze
    table_pairs = [
        ('map_json_bills', 'map_csv_bills'),
        ('map_json_contacts', 'map_csv_contacts'),
        ('map_json_invoices', 'map_csv_invoices'), 
        ('map_json_items', 'map_csv_items'),
        ('map_json_purchase_orders', 'map_csv_purchase_orders'),
        ('map_json_sales_orders', 'map_csv_sales_orders'),
        ('map_json_customer_payments', 'map_csv_customer_payments'),
        ('map_json_vendor_payments', 'map_csv_vendor_payments'),
        ('map_json_credit_notes', 'map_csv_credit_notes'),
    ]
    
    total_issues_found = 0
    
    for json_table, csv_table in table_pairs:
        issues = analyzer.analyze_table(json_table, csv_table)
        table_issues = analyzer.print_issues(json_table, issues)
        total_issues_found += table_issues
        
        print(f"\nPress Enter to continue to next table...")
        input()
    
    print(f"\n{'='*100}")
    print(f"OVERALL SUMMARY: {total_issues_found} total issues found across all tables")
    print(f"{'='*100}")
    
    analyzer.close()

if __name__ == "__main__":
    main()
