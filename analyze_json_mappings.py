#!/usr/bin/env python3
"""
JSON Field Analysis and Mapping Coverage Report

This script analyzes all JSON files in the data/raw_json directory, extracts field names
from each entity, and compares them against the JSON-to-database mappings to generate
a comprehensive coverage report.

Author: Data Pipeline Team
Date: 2025-07-05
"""

import os
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any, Optional
import pandas as pd
from datetime import datetime

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import the JSON mappings using importlib for the hyphenated filename
import importlib.util
try:
    # Load the mappings module (enhanced version with complete coverage)
    mappings_path = current_dir / "src" / "data_pipeline" / "json_db_mappings.py"
    spec = importlib.util.spec_from_file_location("json_db_mappings", mappings_path)
    mappings_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mappings_module)
    
    # Import the required components
    CANONICAL_SCHEMA = mappings_module.CANONICAL_SCHEMA
    get_entity_json_mapping = mappings_module.get_entity_json_mapping
    get_all_entities = mappings_module.get_all_entities
    print("✅ Successfully imported JSON-to-database mappings")
except ImportError as e:
    print(f"❌ Failed to import mappings: {e}")
    sys.exit(1)

class JSONFieldAnalyzer:
    """Analyzes JSON files and compares field coverage against mappings."""
    
    def __init__(self, json_data_dir: str):
        self.json_data_dir = Path(json_data_dir)
        self.entity_fields = defaultdict(set)
        self.entity_field_counts = defaultdict(Counter)
        self.sample_data = defaultdict(dict)
        self.all_entities = get_all_entities()
        self.processed_files = 0
        self.total_records = 0
        
    def normalize_field_name(self, field_name: str) -> str:
        """Normalize field names to match mapping expectations."""
        # Convert snake_case to Title Case with spaces
        # bill_id -> Bill ID
        # invoice_number -> Invoice Number
        words = field_name.replace('_', ' ').split()
        return ' '.join(word.capitalize() for word in words)
        
    def get_field_variations(self, field_name: str) -> List[str]:
        """Get different variations of a field name for matching."""
        variations = [
            field_name,  # Original
            field_name.lower(),  # lowercase
            field_name.upper(),  # UPPERCASE
            self.normalize_field_name(field_name),  # Title Case
            field_name.replace('_', ' '),  # spaces instead of underscores
            field_name.replace(' ', '_'),  # underscores instead of spaces
        ]
        return list(set(variations))  # Remove duplicates
        
    def discover_json_files(self) -> List[Path]:
        """Discover all JSON files in the data directory."""
        json_files = []
        
        if not self.json_data_dir.exists():
            print(f"❌ JSON data directory not found: {self.json_data_dir}")
            return json_files
            
        # Search for JSON files in all subdirectories
        for json_file in self.json_data_dir.rglob("*.json"):
            json_files.append(json_file)
            
        return sorted(json_files)
    
    def extract_fields_from_record(self, record: Dict, prefix: str = "") -> Set[str]:
        """Extract all field names from a JSON record, handling nested structures."""
        fields = set()
        
        for key, value in record.items():
            field_name = f"{prefix}.{key}" if prefix else key
            
            # Store both original and normalized field names
            fields.add(field_name)
            normalized = self.normalize_field_name(field_name)
            if normalized != field_name:
                fields.add(normalized)
            
            # Handle nested objects
            if isinstance(value, dict):
                nested_fields = self.extract_fields_from_record(value, field_name)
                fields.update(nested_fields)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle arrays of objects (like line items)
                nested_fields = self.extract_fields_from_record(value[0], field_name)
                fields.update(nested_fields)
                
        return fields
    
    def analyze_json_file(self, json_file: Path) -> None:
        """Analyze a single JSON file and extract field information."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.processed_files += 1
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # Check if it's a response with nested data
                for entity_name in self.all_entities:
                    entity_key = entity_name.lower()
                    
                    # Try different possible keys
                    possible_keys = [
                        entity_key,
                        entity_name,
                        entity_key + 's',
                        entity_name + 's'
                    ]
                    
                    for key in possible_keys:
                        if key in data:
                            entity_data = data[key]
                            self._process_entity_data(entity_name, entity_data, json_file)
                            break
                    else:
                        # Check if the root object matches an entity structure
                        self._try_match_entity_structure(data, json_file)
                        
            elif isinstance(data, list):
                # Handle array of records
                for record in data:
                    self._try_match_entity_structure(record, json_file)
                    
        except Exception as e:
            print(f"⚠️  Error processing {json_file}: {e}")
    
    def _process_entity_data(self, entity_name: str, entity_data: Any, source_file: Path) -> None:
        """Process data for a specific entity."""
        if isinstance(entity_data, list):
            for record in entity_data:
                if isinstance(record, dict):
                    fields = self.extract_fields_from_record(record)
                    self.entity_fields[entity_name].update(fields)
                    
                    # Count field occurrences
                    for field in fields:
                        self.entity_field_counts[entity_name][field] += 1
                    
                    # Store sample data
                    if entity_name not in self.sample_data:
                        self.sample_data[entity_name] = {
                            'record': record,
                            'source_file': str(source_file)
                        }
                    
                    self.total_records += 1
                    
        elif isinstance(entity_data, dict):
            fields = self.extract_fields_from_record(entity_data)
            self.entity_fields[entity_name].update(fields)
            
            # Count field occurrences
            for field in fields:
                self.entity_field_counts[entity_name][field] += 1
            
            # Store sample data
            if entity_name not in self.sample_data:
                self.sample_data[entity_name] = {
                    'record': entity_data,
                    'source_file': str(source_file)
                }
            
            self.total_records += 1
    
    def _try_match_entity_structure(self, record: Dict, source_file: Path) -> None:
        """Try to match a record structure to a known entity."""
        if not isinstance(record, dict):
            return
            
        fields = self.extract_fields_from_record(record)
        
        # Try to match based on key fields - check multiple naming patterns
        for entity_name in self.all_entities:
            schema = CANONICAL_SCHEMA.get(entity_name, {})
            primary_key = schema.get('primary_key', '')
            
            # Generate possible field name variations for the primary key
            possible_pk_names = [
                primary_key,  # Original: InvoiceID
                primary_key.lower(),  # lowercase: invoiceid
                # Convert CamelCase to snake_case
                ''.join(['_' + c.lower() if c.isupper() and i > 0 else c.lower() 
                        for i, c in enumerate(primary_key)]),  # snake_case: invoice_id
                # Convert to title case with spaces
                ''.join([' ' + c if c.isupper() and i > 0 else c 
                        for i, c in enumerate(primary_key)]).strip()  # Invoice ID
            ]
            
            # Check if this record might belong to this entity
            for pk_variation in possible_pk_names:
                if pk_variation and pk_variation.lower() in [f.lower() for f in fields]:
                    self._process_entity_data(entity_name, record, source_file)
                    return
                    
        # If no primary key match, try entity-specific heuristics
        field_lower = [f.lower() for f in fields]
        
        # Invoice detection
        if any(f in field_lower for f in ['invoice_id', 'invoice_number', 'invoiceid']):
            self._process_entity_data('Invoices', record, source_file)
        # Bill detection  
        elif any(f in field_lower for f in ['bill_id', 'bill_number', 'billid']):
            self._process_entity_data('Bills', record, source_file)
        # Item detection
        elif any(f in field_lower for f in ['item_id', 'item_name', 'itemid', 'sku']):
            self._process_entity_data('Items', record, source_file)
        # Contact detection
        elif any(f in field_lower for f in ['contact_id', 'contactid', 'customer_id', 'customerid', 'vendor_id', 'vendorid']):
            self._process_entity_data('Contacts', record, source_file)
        # SalesOrder detection
        elif any(f in field_lower for f in ['salesorder_id', 'sales_order_id', 'salesorderid']):
            self._process_entity_data('SalesOrders', record, source_file)
        # PurchaseOrder detection
        elif any(f in field_lower for f in ['purchaseorder_id', 'purchase_order_id', 'purchaseorderid']):
            self._process_entity_data('PurchaseOrders', record, source_file)
        # CustomerPayment detection
        elif any(f in field_lower for f in ['customerpayment_id', 'customer_payment_id', 'payment_id']) and any(f in field_lower for f in ['customer_id', 'customerid']):
            self._process_entity_data('CustomerPayments', record, source_file)
        # VendorPayment detection
        elif any(f in field_lower for f in ['vendorpayment_id', 'vendor_payment_id', 'payment_id']) and any(f in field_lower for f in ['vendor_id', 'vendorid']):
            self._process_entity_data('VendorPayments', record, source_file)
        # CreditNote detection
        elif any(f in field_lower for f in ['creditnote_id', 'credit_note_id', 'creditnoteid']):
            self._process_entity_data('CreditNotes', record, source_file)
    
    def find_field_matches(self, json_fields: Set[str], mapping_fields: Set[str]) -> Dict[str, str]:
        """Find matches between JSON fields and mapping fields with flexible matching."""
        matches = {}
        
        # Create normalized lookup for mapping fields
        mapping_lookup = {}
        for mapping_field in mapping_fields:
            variations = self.get_field_variations(mapping_field)
            for variation in variations:
                mapping_lookup[variation.lower()] = mapping_field
        
        # Find matches for JSON fields
        for json_field in json_fields:
            json_variations = self.get_field_variations(json_field)
            for variation in json_variations:
                if variation.lower() in mapping_lookup:
                    matches[json_field] = mapping_lookup[variation.lower()]
                    break
        
        return matches
        
    def generate_mapping_coverage_report(self) -> Dict[str, Any]:
        """Generate a comprehensive mapping coverage report."""
        report = {
            'summary': {
                'processed_files': self.processed_files,
                'total_records': self.total_records,
                'entities_found': len(self.entity_fields),
                'timestamp': datetime.now().isoformat()
            },
            'entities': {}
        }
        
        for entity_name in sorted(self.entity_fields.keys()):
            json_fields = self.entity_fields[entity_name]
            field_counts = self.entity_field_counts[entity_name]
            mapping = get_entity_json_mapping(entity_name)
            
            if mapping:
                mapped_fields = set(mapping.keys())
                
                # Use flexible matching
                field_matches = self.find_field_matches(json_fields, mapped_fields)
                
                # Calculate coverage
                covered_fields = set(field_matches.keys())
                missing_from_mapping = json_fields - covered_fields
                unused_mappings = mapped_fields - set(field_matches.values())
                
                coverage_percentage = len(covered_fields) / len(json_fields) * 100 if json_fields else 0
                
                entity_report = {
                    'total_json_fields': len(json_fields),
                    'total_mapping_fields': len(mapped_fields),
                    'covered_fields': len(covered_fields),
                    'missing_from_mapping': len(missing_from_mapping),
                    'unused_mappings': len(unused_mappings),
                    'coverage_percentage': round(coverage_percentage, 2),
                    'field_details': {
                        'covered_fields': sorted(list(covered_fields)),
                        'missing_from_mapping': sorted(list(missing_from_mapping)),
                        'unused_mappings': sorted(list(unused_mappings)),
                        'field_matches': field_matches
                    },
                    'field_frequency': dict(field_counts.most_common()),
                    'sample_source': self.sample_data.get(entity_name, {}).get('source_file', 'N/A')
                }
            else:
                entity_report = {
                    'total_json_fields': len(json_fields),
                    'total_mapping_fields': 0,
                    'covered_fields': 0,
                    'missing_from_mapping': len(json_fields),
                    'unused_mappings': 0,
                    'coverage_percentage': 0.0,
                    'field_details': {
                        'covered_fields': [],
                        'missing_from_mapping': sorted(list(json_fields)),
                        'unused_mappings': []
                    },
                    'field_frequency': dict(field_counts.most_common()),
                    'sample_source': self.sample_data.get(entity_name, {}).get('source_file', 'N/A'),
                    'note': 'No mapping found for this entity'
                }
            
            report['entities'][entity_name] = entity_report
        
        return report
    
    def save_detailed_csv_reports(self, output_dir: Path) -> None:
        """Save detailed CSV reports for analysis."""
        output_dir.mkdir(exist_ok=True)
        
        # Entity summary report
        summary_data = []
        for entity_name, entity_data in self.entity_fields.items():
            mapping = get_entity_json_mapping(entity_name)
            mapped_fields = set(mapping.keys()) if mapping else set()
            
            json_fields = entity_data
            covered = json_fields & mapped_fields
            missing = json_fields - mapped_fields
            unused = mapped_fields - json_fields
            
            coverage = len(covered) / len(json_fields) * 100 if json_fields else 0
            
            summary_data.append({
                'Entity': entity_name,
                'JSON_Fields_Count': len(json_fields),
                'Mapping_Fields_Count': len(mapped_fields),
                'Covered_Fields': len(covered),
                'Missing_From_Mapping': len(missing),
                'Unused_Mappings': len(unused),
                'Coverage_Percentage': round(coverage, 2),
                'Sample_Source': self.sample_data.get(entity_name, {}).get('source_file', 'N/A')
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_file = output_dir / f"json_mapping_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"📊 Summary report saved: {summary_file}")
        
        # Detailed field analysis for each entity
        for entity_name in self.entity_fields.keys():
            field_data = []
            json_fields = self.entity_fields[entity_name]
            field_counts = self.entity_field_counts[entity_name]
            mapping = get_entity_json_mapping(entity_name)
            mapped_fields = set(mapping.keys()) if mapping else set()
            
            for field in sorted(json_fields):
                mapped_to = mapping.get(field, '') if mapping else ''
                status = 'MAPPED' if field in mapped_fields else 'MISSING_FROM_MAPPING'
                
                field_data.append({
                    'Field_Name': field,
                    'Frequency': field_counts.get(field, 0),
                    'Mapping_Status': status,
                    'Mapped_To': mapped_to
                })
            
            if field_data:
                field_df = pd.DataFrame(field_data)
                field_file = output_dir / f"json_fields_{entity_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                field_df.to_csv(field_file, index=False)
        
        print(f"📁 Detailed reports saved in: {output_dir}")

def main():
    """Main execution function."""
    print("🔍 JSON Field Analysis and Mapping Coverage Report")
    print("=" * 60)
    
    # Configuration
    project_root = Path(__file__).parent
    json_data_dir = project_root / "data" / "raw_json"
    output_dir = project_root / "reports"
    
    print(f"📂 JSON Data Directory: {json_data_dir}")
    print(f"📁 Output Directory: {output_dir}")
    
    # Initialize analyzer
    analyzer = JSONFieldAnalyzer(str(json_data_dir))
    
    # Discover JSON files
    json_files = analyzer.discover_json_files()
    print(f"📋 Found {len(json_files)} JSON files")
    
    if not json_files:
        print("❌ No JSON files found to analyze")
        return
    
    # Process all JSON files
    print("\n🔄 Processing JSON files...")
    for i, json_file in enumerate(json_files, 1):
        print(f"  Processing {i}/{len(json_files)}: {json_file.name}")
        analyzer.analyze_json_file(json_file)
    
    # Generate report
    print("\n📊 Generating mapping coverage report...")
    report = analyzer.generate_mapping_coverage_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Processed Files: {report['summary']['processed_files']}")
    print(f"Total Records: {report['summary']['total_records']}")
    print(f"Entities Found: {report['summary']['entities_found']}")
    
    # Print entity details
    print("\n📈 ENTITY COVERAGE REPORT")
    print("-" * 80)
    print(f"{'Entity':<20} {'JSON Fields':<12} {'Mapped':<8} {'Missing':<8} {'Coverage':<10}")
    print("-" * 80)
    
    for entity_name, entity_info in sorted(report['entities'].items()):
        coverage = entity_info['coverage_percentage']
        print(f"{entity_name:<20} {entity_info['total_json_fields']:<12} "
              f"{entity_info['covered_fields']:<8} {entity_info['missing_from_mapping']:<8} "
              f"{coverage:<10.1f}%")
    
    # Detailed analysis for critical entities
    print("\n🔍 DETAILED ANALYSIS FOR KEY ENTITIES")
    print("=" * 60)
    
    key_entities = ['Invoices', 'Items', 'Contacts', 'Bills']
    for entity_name in key_entities:
        if entity_name in report['entities']:
            entity_info = report['entities'][entity_name]
            print(f"\n📊 {entity_name.upper()}")
            print(f"  Total JSON Fields: {entity_info['total_json_fields']}")
            print(f"  Coverage: {entity_info['coverage_percentage']:.1f}%")
            
            if entity_info['field_details']['missing_from_mapping']:
                print(f"  Missing from Mapping ({len(entity_info['field_details']['missing_from_mapping'])}):")
                for field in entity_info['field_details']['missing_from_mapping'][:10]:  # Show first 10
                    freq = entity_info['field_frequency'].get(field, 0)
                    print(f"    - {field} (appears {freq} times)")
                
                if len(entity_info['field_details']['missing_from_mapping']) > 10:
                    remaining = len(entity_info['field_details']['missing_from_mapping']) - 10
                    print(f"    ... and {remaining} more fields")
    
    # Save reports
    print(f"\n💾 Saving detailed reports...")
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON report
    report_file = output_dir / f"json_mapping_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"📄 JSON report saved: {report_file}")
    
    # Save CSV reports
    analyzer.save_detailed_csv_reports(output_dir)
    
    print("\n✅ Analysis complete!")
    print(f"📁 Reports saved in: {output_dir}")

if __name__ == "__main__":
    main()
