#!/usr/bin/env python3
"""
Database vs JSON Field Mapping Report Generator

This script compares the canonical database schema against JSON-to-database mappings
to create comprehensive reports showing:
- Database fields that are mapped from JSON
- Database fields that are NOT mapped (unmapped)
- JSON fields that map to each database table
- Coverage statistics for each entity

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

# Import schema and mappings
try:
    # Load the enhanced mappings module
    mappings_path = current_dir / "src" / "data_pipeline" / "json_db_mappings.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("json_db_mappings", mappings_path)
    mappings_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mappings_module)
    
    # Import the required components
    CANONICAL_SCHEMA = mappings_module.CANONICAL_SCHEMA
    get_entity_json_mapping = mappings_module.get_entity_json_mapping
    get_all_entities = mappings_module.get_all_entities
    print("✅ Successfully imported enhanced JSON-to-database mappings")
    
except Exception as e:
    print(f"❌ Error importing mappings: {e}")
    sys.exit(1)

def analyze_database_vs_json_mappings():
    """
    Analyze database schema vs JSON mappings for all entities.
    """
    print("📊 DATABASE vs JSON FIELD MAPPING ANALYSIS")
    print("=" * 60)
    
    all_analysis = {}
    summary_data = []
    
    # Get all entities from canonical schema
    entities = get_all_entities()
    print(f"📋 Analyzing {len(entities)} entities...")
    
    for entity in entities:
        print(f"\n🔍 Analyzing {entity}...")
        analysis = analyze_entity_mappings(entity)
        all_analysis[entity] = analysis
        
        # Add to summary data
        summary_data.append({
            'Entity': entity,
            'DB_Header_Fields': analysis['db_stats']['header_fields_count'],
            'DB_LineItem_Fields': analysis['db_stats']['line_item_fields_count'],
            'DB_Total_Fields': analysis['db_stats']['total_db_fields'],
            'JSON_Mapped_Fields': analysis['mapping_stats']['json_fields_mapped'],
            'DB_Mapped_Fields': analysis['mapping_stats']['db_fields_mapped'],
            'DB_Unmapped_Fields': analysis['mapping_stats']['db_fields_unmapped'],
            'DB_Coverage_Percent': analysis['mapping_stats']['db_coverage_percent'],
            'JSON_Coverage_Percent': analysis['mapping_stats']['json_coverage_percent']
        })
        
        # Print summary for this entity
        print(f"  📊 DB Fields: {analysis['db_stats']['total_db_fields']}")
        print(f"  📈 DB Mapped: {analysis['mapping_stats']['db_fields_mapped']}")
        print(f"  📉 DB Unmapped: {analysis['mapping_stats']['db_fields_unmapped']}")
        print(f"  🎯 DB Coverage: {analysis['mapping_stats']['db_coverage_percent']:.1f}%")
    
    return all_analysis, summary_data

def analyze_entity_mappings(entity_name: str) -> Dict[str, Any]:
    """
    Analyze mapping coverage for a specific entity.
    """
    # Get database schema
    schema = CANONICAL_SCHEMA.get(entity_name, {})
    if not schema:
        return {}
    
    # Get JSON mappings
    json_mapping = get_entity_json_mapping(entity_name)
    if not json_mapping:
        json_mapping = {}
    
    # Extract database fields
    header_fields = list(schema.get('header_columns', {}).keys())
    line_item_fields = list(schema.get('line_items_columns', {}).keys())
    all_db_fields = header_fields + line_item_fields
    
    # Extract mapped database fields (targets of JSON mappings)
    mapped_db_fields = set(json_mapping.values())
    
    # Find unmapped database fields
    unmapped_db_fields = set(all_db_fields) - mapped_db_fields
    
    # Calculate coverage statistics
    total_db_fields = len(all_db_fields)
    mapped_db_count = len(mapped_db_fields)
    unmapped_db_count = len(unmapped_db_fields)
    db_coverage_percent = (mapped_db_count / total_db_fields * 100) if total_db_fields > 0 else 0
    
    # JSON field statistics
    json_fields_count = len(json_mapping)
    json_coverage_percent = 100.0  # We assume all JSON mappings are valid
    
    analysis = {
        'entity_name': entity_name,
        'db_schema': {
            'header_fields': header_fields,
            'line_item_fields': line_item_fields,
            'all_db_fields': all_db_fields
        },
        'db_stats': {
            'header_fields_count': len(header_fields),
            'line_item_fields_count': len(line_item_fields),
            'total_db_fields': total_db_fields
        },
        'json_mapping': json_mapping,
        'mapping_analysis': {
            'mapped_db_fields': sorted(list(mapped_db_fields)),
            'unmapped_db_fields': sorted(list(unmapped_db_fields)),
            'json_to_db_mappings': dict(json_mapping)
        },
        'mapping_stats': {
            'json_fields_mapped': json_fields_count,
            'db_fields_mapped': mapped_db_count,
            'db_fields_unmapped': unmapped_db_count,
            'db_coverage_percent': db_coverage_percent,
            'json_coverage_percent': json_coverage_percent
        }
    }
    
    return analysis

def generate_detailed_reports(all_analysis: Dict, summary_data: List[Dict]):
    """
    Generate detailed reports for database vs JSON mapping analysis.
    """
    # Ensure reports directory exists
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Generate summary CSV
    summary_df = pd.DataFrame(summary_data)
    summary_csv_path = reports_dir / f"db_vs_json_mapping_summary_{timestamp}.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"📊 Summary CSV saved: {summary_csv_path}")
    
    # 2. Generate detailed JSON report
    detailed_json_path = reports_dir / f"db_vs_json_mapping_detailed_{timestamp}.json"
    with open(detailed_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_analysis, f, indent=2, ensure_ascii=False)
    print(f"📄 Detailed JSON report saved: {detailed_json_path}")
    
    # 3. Generate comprehensive markdown report
    markdown_path = reports_dir / f"DATABASE_VS_JSON_MAPPING_REPORT_{timestamp}.md"
    generate_markdown_report(all_analysis, summary_data, markdown_path)
    print(f"📋 Markdown report saved: {markdown_path}")
    
    # 4. Generate individual entity CSV files
    for entity, analysis in all_analysis.items():
        entity_csv_path = reports_dir / f"db_mapping_{entity.lower()}_{timestamp}.csv"
        generate_entity_csv(entity, analysis, entity_csv_path)
    print(f"📁 Individual entity CSV files saved in: {reports_dir}")
    
    return {
        'summary_csv': summary_csv_path,
        'detailed_json': detailed_json_path,
        'markdown_report': markdown_path,
        'reports_directory': reports_dir
    }

def generate_entity_csv(entity_name: str, analysis: Dict, output_path: Path):
    """
    Generate a detailed CSV report for a specific entity.
    """
    rows = []
    
    # Add header fields
    for field in analysis['db_schema']['header_fields']:
        is_mapped = field in analysis['mapping_analysis']['mapped_db_fields']
        mapping_source = None
        if is_mapped:
            # Find the JSON field that maps to this DB field
            for json_field, db_field in analysis['json_mapping'].items():
                if db_field == field:
                    mapping_source = json_field
                    break
        
        rows.append({
            'Entity': entity_name,
            'Table_Type': 'Header',
            'DB_Field': field,
            'Is_Mapped': is_mapped,
            'JSON_Source_Field': mapping_source or '',
            'Coverage_Status': 'Mapped' if is_mapped else 'Unmapped'
        })
    
    # Add line item fields (if any)
    for field in analysis['db_schema']['line_item_fields']:
        is_mapped = field in analysis['mapping_analysis']['mapped_db_fields']
        mapping_source = None
        if is_mapped:
            # Find the JSON field that maps to this DB field
            for json_field, db_field in analysis['json_mapping'].items():
                if db_field == field:
                    mapping_source = json_field
                    break
        
        rows.append({
            'Entity': entity_name,
            'Table_Type': 'Line Items',
            'DB_Field': field,
            'Is_Mapped': is_mapped,
            'JSON_Source_Field': mapping_source or '',
            'Coverage_Status': 'Mapped' if is_mapped else 'Unmapped'
        })
    
    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

def generate_markdown_report(all_analysis: Dict, summary_data: List[Dict], output_path: Path):
    """
    Generate a comprehensive markdown report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Database vs JSON Field Mapping Analysis Report
## Generated: {timestamp}

---

## 📊 **EXECUTIVE SUMMARY**

This report provides a comprehensive analysis of how database schema fields map to JSON data fields 
in the Zoho Data Sync pipeline. It identifies:

- **Database fields that are successfully mapped** from JSON data
- **Database fields that are unmapped** (no JSON source)
- **Coverage statistics** for each entity
- **Detailed field-by-field analysis** for all entities

---

## 📈 **OVERALL COVERAGE SUMMARY**

| Entity | DB Fields | Mapped | Unmapped | Coverage |
|--------|-----------|--------|----------|----------|
""")
        
        # Add summary table
        for row in summary_data:
            coverage = row['DB_Coverage_Percent']
            status_icon = "🎯" if coverage == 100 else "⭐" if coverage >= 90 else "📈" if coverage >= 70 else "⚠️"
            f.write(f"| **{row['Entity']}** | {row['DB_Total_Fields']} | {row['DB_Mapped_Fields']} | {row['DB_Unmapped_Fields']} | {coverage:.1f}% {status_icon} |\n")
        
        f.write(f"""
---

## 🔍 **DETAILED ENTITY ANALYSIS**

""")
        
        # Add detailed analysis for each entity
        for entity, analysis in all_analysis.items():
            stats = analysis['mapping_stats']
            coverage = stats['db_coverage_percent']
            status_icon = "🎯" if coverage == 100 else "⭐" if coverage >= 90 else "📈" if coverage >= 70 else "⚠️"
            
            f.write(f"""
### {status_icon} **{entity.upper()}**

**Coverage**: {coverage:.1f}% ({stats['db_fields_mapped']}/{analysis['db_stats']['total_db_fields']} fields)

#### 📋 **Database Schema Structure**
- **Header Fields**: {analysis['db_stats']['header_fields_count']}
- **Line Item Fields**: {analysis['db_stats']['line_item_fields_count']}
- **Total DB Fields**: {analysis['db_stats']['total_db_fields']}

#### ✅ **Mapped Database Fields** ({stats['db_fields_mapped']} fields)
""")
            
            # List mapped fields
            for field in analysis['mapping_analysis']['mapped_db_fields']:
                # Find source JSON field
                source_json = None
                for json_field, db_field in analysis['json_mapping'].items():
                    if db_field == field:
                        source_json = json_field
                        break
                f.write(f"- `{field}` ← `{source_json}`\n")
            
            if analysis['mapping_analysis']['unmapped_db_fields']:
                f.write(f"""
#### ❌ **Unmapped Database Fields** ({stats['db_fields_unmapped']} fields)
""")
                for field in analysis['mapping_analysis']['unmapped_db_fields']:
                    f.write(f"- `{field}` *(No JSON source)*\n")
            
            f.write(f"""
#### 📊 **JSON to Database Mappings** ({stats['json_fields_mapped']} mappings)
| JSON Field | Database Field |
|------------|---------------|
""")
            # Sort mappings for better readability
            sorted_mappings = sorted(analysis['json_mapping'].items())
            for json_field, db_field in sorted_mappings[:20]:  # Show first 20 to avoid huge tables
                f.write(f"| `{json_field}` | `{db_field}` |\n")
            
            if len(sorted_mappings) > 20:
                f.write(f"| ... | *(+{len(sorted_mappings)-20} more mappings)* |\n")
            
            f.write("\n---\n")
        
        f.write(f"""
## 🎯 **RECOMMENDATIONS**

### **High Priority Actions**:
""")
        
        # Add recommendations based on coverage
        for row in summary_data:
            coverage = row['DB_Coverage_Percent']
            entity = row['Entity']
            unmapped = row['DB_Unmapped_Fields']
            
            if coverage < 100 and unmapped > 0:
                f.write(f"- **{entity}**: Map {unmapped} unmapped database fields to improve {coverage:.1f}% coverage\n")
        
        f.write(f"""
### **Implementation Strategy**:
1. **Review unmapped database fields** to determine if they should have JSON sources
2. **Add missing JSON mappings** for critical business fields
3. **Update mapping dictionaries** in `json_db_mappings.py`
4. **Re-run validation** to confirm improved coverage
5. **Deploy to production** after validation

---

## 📁 **REPORT FILES GENERATED**

- **Summary CSV**: Entity-level coverage statistics
- **Detailed JSON**: Complete analysis data in JSON format
- **Individual Entity CSVs**: Field-by-field mapping details for each entity
- **This Markdown Report**: Human-readable comprehensive analysis

---

**Generated by**: Zoho Data Sync Pipeline Analysis Tool  
**Timestamp**: {timestamp}  
**Total Entities Analyzed**: {len(all_analysis)}  
**Total Database Fields**: {sum(row['DB_Total_Fields'] for row in summary_data)}  
**Total Mapped Fields**: {sum(row['DB_Mapped_Fields'] for row in summary_data)}  
**Overall Average Coverage**: {sum(row['DB_Coverage_Percent'] for row in summary_data) / len(summary_data):.1f}%
""")

def main():
    """
    Main function to run the database vs JSON mapping analysis.
    """
    print("🚀 Starting Database vs JSON Field Mapping Analysis")
    print("=" * 60)
    
    # Run the analysis
    all_analysis, summary_data = analyze_database_vs_json_mappings()
    
    # Generate reports
    print(f"\n📄 Generating comprehensive reports...")
    report_files = generate_detailed_reports(all_analysis, summary_data)
    
    # Print final summary
    print(f"\n🎊 ANALYSIS COMPLETE!")
    print("=" * 40)
    print(f"📊 Entities Analyzed: {len(all_analysis)}")
    total_db_fields = sum(row['DB_Total_Fields'] for row in summary_data)
    total_mapped = sum(row['DB_Mapped_Fields'] for row in summary_data)
    overall_coverage = (total_mapped / total_db_fields * 100) if total_db_fields > 0 else 0
    print(f"📈 Total DB Fields: {total_db_fields}")
    print(f"✅ Total Mapped: {total_mapped}")
    print(f"🎯 Overall Coverage: {overall_coverage:.1f}%")
    print(f"📁 Reports saved in: {report_files['reports_directory']}")
    
    return report_files

if __name__ == "__main__":
    main()
