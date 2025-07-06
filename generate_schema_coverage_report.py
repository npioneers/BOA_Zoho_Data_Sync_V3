#!/usr/bin/env python3
"""
Database Schema Coverage Analysis - CORRECTED VERSION

This script analyzes how well the canonical database schema is covered by JSON mappings.
It focuses on database fields (not JSON fields) and shows which database fields
have JSON sources and which don't.

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

def analyze_database_schema_coverage():
    """
    Analyze database schema coverage by JSON mappings for all entities.
    """
    print("📊 DATABASE SCHEMA COVERAGE ANALYSIS")
    print("=" * 50)
    
    all_analysis = {}
    summary_data = []
    
    # Get all entities from canonical schema
    entities = get_all_entities()
    print(f"📋 Analyzing {len(entities)} entities...")
    
    for entity in entities:
        print(f"\n🔍 Analyzing {entity}...")
        analysis = analyze_entity_schema_coverage(entity)
        all_analysis[entity] = analysis
        
        # Add to summary data
        summary_data.append({
            'Entity': entity,
            'DB_Header_Fields': analysis['db_stats']['header_fields_count'],
            'DB_LineItem_Fields': analysis['db_stats']['line_item_fields_count'],
            'DB_Total_Fields': analysis['db_stats']['total_db_fields'],
            'Header_Mapped': analysis['coverage_stats']['header_mapped'],
            'Header_Unmapped': analysis['coverage_stats']['header_unmapped'],
            'LineItem_Mapped': analysis['coverage_stats']['line_item_mapped'],
            'LineItem_Unmapped': analysis['coverage_stats']['line_item_unmapped'],
            'Total_Mapped': analysis['coverage_stats']['total_mapped'],
            'Total_Unmapped': analysis['coverage_stats']['total_unmapped'],
            'Coverage_Percent': analysis['coverage_stats']['coverage_percent'],
            'JSON_Mappings_Count': analysis['json_stats']['mappings_count']
        })
        
        # Print summary for this entity
        stats = analysis['coverage_stats']
        print(f"  📊 DB Fields: {analysis['db_stats']['total_db_fields']}")
        print(f"  ✅ Mapped: {stats['total_mapped']}")
        print(f"  ❌ Unmapped: {stats['total_unmapped']}")
        print(f"  🎯 Coverage: {stats['coverage_percent']:.1f}%")
    
    return all_analysis, summary_data

def analyze_entity_schema_coverage(entity_name: str) -> Dict[str, Any]:
    """
    Analyze database schema coverage for a specific entity.
    """
    # Get database schema
    schema = CANONICAL_SCHEMA.get(entity_name, {})
    if not schema:
        return {}
    
    # Get JSON mappings
    json_mapping = get_entity_json_mapping(entity_name)
    if not json_mapping:
        json_mapping = {}
    
    # Extract database fields from schema
    header_fields = list(schema.get('header_columns', {}).keys())
    line_item_fields = list(schema.get('line_items_columns', {}).keys())
    all_db_fields = set(header_fields + line_item_fields)
    
    # Extract mapped database fields (targets of JSON mappings)
    mapped_db_fields = set(json_mapping.values())
    
    # Find which schema fields are mapped vs unmapped
    header_mapped = [f for f in header_fields if f in mapped_db_fields]
    header_unmapped = [f for f in header_fields if f not in mapped_db_fields]
    line_item_mapped = [f for f in line_item_fields if f in mapped_db_fields]
    line_item_unmapped = [f for f in line_item_fields if f not in mapped_db_fields]
    
    # Calculate coverage statistics
    total_schema_fields = len(all_db_fields)
    total_mapped = len(header_mapped) + len(line_item_mapped)
    total_unmapped = len(header_unmapped) + len(line_item_unmapped)
    coverage_percent = (total_mapped / total_schema_fields * 100) if total_schema_fields > 0 else 0
    
    # Create reverse mapping (DB field -> JSON fields)
    db_to_json_mapping = defaultdict(list)
    for json_field, db_field in json_mapping.items():
        db_to_json_mapping[db_field].append(json_field)
    
    analysis = {
        'entity_name': entity_name,
        'db_schema': {
            'header_fields': header_fields,
            'line_item_fields': line_item_fields,
            'all_schema_fields': sorted(list(all_db_fields))
        },
        'db_stats': {
            'header_fields_count': len(header_fields),
            'line_item_fields_count': len(line_item_fields),
            'total_db_fields': total_schema_fields
        },
        'coverage_analysis': {
            'header_mapped': sorted(header_mapped),
            'header_unmapped': sorted(header_unmapped),
            'line_item_mapped': sorted(line_item_mapped),
            'line_item_unmapped': sorted(line_item_unmapped),
            'db_to_json_mapping': dict(db_to_json_mapping)
        },
        'coverage_stats': {
            'header_mapped': len(header_mapped),
            'header_unmapped': len(header_unmapped),
            'line_item_mapped': len(line_item_mapped),
            'line_item_unmapped': len(line_item_unmapped),
            'total_mapped': total_mapped,
            'total_unmapped': total_unmapped,
            'coverage_percent': coverage_percent
        },
        'json_stats': {
            'mappings_count': len(json_mapping),
            'unique_db_targets': len(mapped_db_fields)
        }
    }
    
    return analysis

def generate_schema_coverage_reports(all_analysis: Dict, summary_data: List[Dict]):
    """
    Generate detailed reports for database schema coverage analysis.
    """
    # Ensure reports directory exists
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Generate summary CSV
    summary_df = pd.DataFrame(summary_data)
    summary_csv_path = reports_dir / f"db_schema_coverage_summary_{timestamp}.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"📊 Summary CSV saved: {summary_csv_path}")
    
    # 2. Generate detailed JSON report
    detailed_json_path = reports_dir / f"db_schema_coverage_detailed_{timestamp}.json"
    with open(detailed_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_analysis, f, indent=2, ensure_ascii=False)
    print(f"📄 Detailed JSON report saved: {detailed_json_path}")
    
    # 3. Generate comprehensive markdown report
    markdown_path = reports_dir / f"DATABASE_SCHEMA_COVERAGE_REPORT_{timestamp}.md"
    generate_markdown_coverage_report(all_analysis, summary_data, markdown_path)
    print(f"📋 Markdown report saved: {markdown_path}")
    
    # 4. Generate individual entity detailed CSV files
    for entity, analysis in all_analysis.items():
        entity_csv_path = reports_dir / f"db_coverage_{entity.lower()}_{timestamp}.csv"
        generate_entity_coverage_csv(entity, analysis, entity_csv_path)
    print(f"📁 Individual entity CSV files saved in: {reports_dir}")
    
    return {
        'summary_csv': summary_csv_path,
        'detailed_json': detailed_json_path,
        'markdown_report': markdown_path,
        'reports_directory': reports_dir
    }

def generate_entity_coverage_csv(entity_name: str, analysis: Dict, output_path: Path):
    """
    Generate a detailed CSV report for database schema coverage of a specific entity.
    """
    rows = []
    
    # Add header fields
    for field in analysis['db_schema']['header_fields']:
        is_mapped = field in analysis['coverage_analysis']['header_mapped']
        json_sources = analysis['coverage_analysis']['db_to_json_mapping'].get(field, [])
        
        rows.append({
            'Entity': entity_name,
            'Table_Type': 'Header',
            'DB_Schema_Field': field,
            'Is_Mapped': is_mapped,
            'JSON_Source_Count': len(json_sources),
            'JSON_Source_Fields': '; '.join(json_sources) if json_sources else '',
            'Coverage_Status': 'Mapped' if is_mapped else 'Unmapped'
        })
    
    # Add line item fields (if any)
    for field in analysis['db_schema']['line_item_fields']:
        is_mapped = field in analysis['coverage_analysis']['line_item_mapped']
        json_sources = analysis['coverage_analysis']['db_to_json_mapping'].get(field, [])
        
        rows.append({
            'Entity': entity_name,
            'Table_Type': 'Line Items',
            'DB_Schema_Field': field,
            'Is_Mapped': is_mapped,
            'JSON_Source_Count': len(json_sources),
            'JSON_Source_Fields': '; '.join(json_sources) if json_sources else '',
            'Coverage_Status': 'Mapped' if is_mapped else 'Unmapped'
        })
    
    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

def generate_markdown_coverage_report(all_analysis: Dict, summary_data: List[Dict], output_path: Path):
    """
    Generate a comprehensive markdown report for database schema coverage.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Database Schema Coverage Analysis Report
## Generated: {timestamp}

---

## 📊 **EXECUTIVE SUMMARY**

This report analyzes how well the **canonical database schema** is covered by JSON-to-database field mappings. 
It shows which database fields have JSON data sources and which database fields are unmapped.

### **Key Metrics**:
- **Database Schema Fields**: Total fields defined in canonical schema
- **Mapped Fields**: Database fields that have JSON source mappings  
- **Unmapped Fields**: Database fields without JSON source mappings
- **Coverage**: Percentage of schema fields that are mapped

---

## 📈 **DATABASE SCHEMA COVERAGE SUMMARY**

| Entity | Schema Fields | Mapped | Unmapped | Coverage | Status |
|--------|---------------|--------|----------|----------|--------|
""")
        
        # Add summary table
        for row in summary_data:
            coverage = row['Coverage_Percent']
            status_icon = "🎯" if coverage == 100 else "⭐" if coverage >= 90 else "📈" if coverage >= 70 else "⚠️"
            f.write(f"| **{row['Entity']}** | {row['DB_Total_Fields']} | {row['Total_Mapped']} | {row['Total_Unmapped']} | {coverage:.1f}% | {status_icon} |\n")
        
        # Calculate totals
        total_fields = sum(row['DB_Total_Fields'] for row in summary_data)
        total_mapped = sum(row['Total_Mapped'] for row in summary_data)
        total_unmapped = sum(row['Total_Unmapped'] for row in summary_data)
        overall_coverage = (total_mapped / total_fields * 100) if total_fields > 0 else 0
        
        f.write(f"| **TOTALS** | **{total_fields}** | **{total_mapped}** | **{total_unmapped}** | **{overall_coverage:.1f}%** | **📊** |\n")
        
        f.write(f"""
---

## 🔍 **DETAILED ENTITY ANALYSIS**

""")
        
        # Add detailed analysis for each entity
        for entity, analysis in all_analysis.items():
            stats = analysis['coverage_stats']
            coverage = stats['coverage_percent']
            status_icon = "🎯" if coverage == 100 else "⭐" if coverage >= 90 else "📈" if coverage >= 70 else "⚠️"
            
            f.write(f"""
### {status_icon} **{entity.upper()}**

**Database Schema Coverage**: {coverage:.1f}% ({stats['total_mapped']}/{analysis['db_stats']['total_db_fields']} fields)

#### 📋 **Database Schema Structure**
- **Header Table Fields**: {analysis['db_stats']['header_fields_count']}
- **Line Item Table Fields**: {analysis['db_stats']['line_item_fields_count']}
- **Total Schema Fields**: {analysis['db_stats']['total_db_fields']}

#### ✅ **MAPPED DATABASE FIELDS**

**Header Fields Mapped** ({stats['header_mapped']}/{analysis['db_stats']['header_fields_count']}):
""")
            
            # List mapped header fields with their JSON sources
            for field in analysis['coverage_analysis']['header_mapped']:
                json_sources = analysis['coverage_analysis']['db_to_json_mapping'].get(field, [])
                f.write(f"- `{field}` ← {len(json_sources)} JSON source(s)\n")
            
            if analysis['coverage_analysis']['line_item_mapped']:
                f.write(f"""
**Line Item Fields Mapped** ({stats['line_item_mapped']}/{analysis['db_stats']['line_item_fields_count']}):
""")
                for field in analysis['coverage_analysis']['line_item_mapped']:
                    json_sources = analysis['coverage_analysis']['db_to_json_mapping'].get(field, [])
                    f.write(f"- `{field}` ← {len(json_sources)} JSON source(s)\n")
            
            # Show unmapped fields if any
            unmapped_header = analysis['coverage_analysis']['header_unmapped']
            unmapped_line_items = analysis['coverage_analysis']['line_item_unmapped']
            
            if unmapped_header or unmapped_line_items:
                f.write(f"""
#### ❌ **UNMAPPED DATABASE FIELDS** ({stats['total_unmapped']} fields)

""")
                if unmapped_header:
                    f.write(f"**Unmapped Header Fields** ({len(unmapped_header)}):\n")
                    for field in unmapped_header:
                        f.write(f"- `{field}` *(No JSON source)*\n")
                
                if unmapped_line_items:
                    f.write(f"\n**Unmapped Line Item Fields** ({len(unmapped_line_items)}):\n")
                    for field in unmapped_line_items:
                        f.write(f"- `{field}` *(No JSON source)*\n")
            
            f.write("\n---\n")
        
        f.write(f"""
## 🎯 **COVERAGE ANALYSIS & RECOMMENDATIONS**

### **Entities by Coverage Level**:

#### 🎯 **Perfect Coverage (100%)**:
""")
        perfect = [row for row in summary_data if row['Coverage_Percent'] == 100]
        if perfect:
            for entity in perfect:
                f.write(f"- **{entity['Entity']}**: All {entity['DB_Total_Fields']} schema fields mapped\n")
        else:
            f.write("- *None*\n")
        
        f.write(f"""
#### ⭐ **Excellent Coverage (90-99%)**:
""")
        excellent = [row for row in summary_data if 90 <= row['Coverage_Percent'] < 100]
        if excellent:
            for entity in excellent:
                f.write(f"- **{entity['Entity']}**: {entity['Coverage_Percent']:.1f}% ({entity['Total_Unmapped']} unmapped fields)\n")
        else:
            f.write("- *None*\n")
        
        f.write(f"""
#### 📈 **Good Coverage (70-89%)**:
""")
        good = [row for row in summary_data if 70 <= row['Coverage_Percent'] < 90]
        if good:
            for entity in good:
                f.write(f"- **{entity['Entity']}**: {entity['Coverage_Percent']:.1f}% ({entity['Total_Unmapped']} unmapped fields)\n")
        else:
            f.write("- *None*\n")
        
        f.write(f"""
#### ⚠️ **Needs Improvement (<70%)**:
""")
        needs_work = [row for row in summary_data if row['Coverage_Percent'] < 70]
        if needs_work:
            for entity in needs_work:
                f.write(f"- **{entity['Entity']}**: {entity['Coverage_Percent']:.1f}% ({entity['Total_Unmapped']} unmapped fields)\n")
        else:
            f.write("- *None*\n")

        f.write(f"""
### **Action Plan**:

1. **Immediate**: Focus on entities with <90% coverage
2. **Review**: Unmapped database fields to determine if they need JSON sources
3. **Enhance**: Add missing JSON mappings for critical business fields
4. **Validate**: Test enhanced mappings in staging environment
5. **Deploy**: Update production mappings after validation

---

## 📊 **TECHNICAL DETAILS**

### **Mapping Statistics**:
- **Total Database Schema Fields**: {total_fields}
- **Total Mapped Fields**: {total_mapped}
- **Total Unmapped Fields**: {total_unmapped}
- **Overall Schema Coverage**: {overall_coverage:.1f}%

### **Analysis Methodology**:
1. Extracted all database fields from canonical schema
2. Identified which schema fields have JSON source mappings
3. Calculated coverage as: (Mapped Schema Fields / Total Schema Fields) × 100
4. Generated detailed field-by-field analysis for each entity

---

**Generated by**: Database Schema Coverage Analysis Tool  
**Timestamp**: {timestamp}  
**Schema Version**: Canonical Schema v1.0  
**Mapping Source**: Enhanced JSON-to-Database Mappings
""")

def main():
    """
    Main function to run the database schema coverage analysis.
    """
    print("🚀 Starting Database Schema Coverage Analysis")
    print("=" * 60)
    
    # Run the analysis
    all_analysis, summary_data = analyze_database_schema_coverage()
    
    # Generate reports
    print(f"\n📄 Generating comprehensive reports...")
    report_files = generate_schema_coverage_reports(all_analysis, summary_data)
    
    # Print final summary
    print(f"\n🎊 SCHEMA COVERAGE ANALYSIS COMPLETE!")
    print("=" * 45)
    print(f"📊 Entities Analyzed: {len(all_analysis)}")
    total_schema_fields = sum(row['DB_Total_Fields'] for row in summary_data)
    total_mapped = sum(row['Total_Mapped'] for row in summary_data)
    overall_coverage = (total_mapped / total_schema_fields * 100) if total_schema_fields > 0 else 0
    print(f"📈 Total Schema Fields: {total_schema_fields}")
    print(f"✅ Schema Fields Mapped: {total_mapped}")
    print(f"❌ Schema Fields Unmapped: {total_schema_fields - total_mapped}")
    print(f"🎯 Overall Schema Coverage: {overall_coverage:.1f}%")
    print(f"📁 Reports saved in: {report_files['reports_directory']}")
    
    return report_files

if __name__ == "__main__":
    main()
