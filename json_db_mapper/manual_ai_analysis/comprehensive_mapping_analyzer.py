#!/usr/bin/env python3
"""
Comprehensive Manual Mapping Analysis
Author: GitHub Copilot
Date: July 8, 2025

Following user instructions precisely:
1. Analyze each JSON table manually using domain knowledge
2. Categorize mappings: Perfect, Good, Questionable, Unmapped
3. Check for duplicate CSV mappings (ONLY ONE CSV_field per JSON field allowed)
4. Flag questionable/unmapped fields that have CSV data available
5. Generate comprehensive manual mapping report
"""

import sqlite3
import json
from datetime import datetime
import os
from collections import defaultdict

class ComprehensiveMappingAnalyzer:
    def __init__(self):
        self.db_path = os.path.join("..", "..", "data", "database", "production.db")
        self.analysis_results = {
            "analysis_date": datetime.now().isoformat(),
            "table_analysis": {},
            "duplicate_mappings": [],
            "critical_issues": [],
            "recommendations": {},
            "summary": {}
        }
        
    def get_csv_field_counts(self, conn, csv_table):
        """Get CSV field data counts"""
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                SELECT field_name, CSV_data_count 
                FROM map_csv_{csv_table}
                ORDER BY CSV_data_count DESC
            """)
            return {row[0]: row[1] for row in cursor.fetchall()}
        except:
            return {}
    
    def categorize_mapping_quality(self, json_field, csv_field, csv_data_count):
        """Categorize mapping quality using domain knowledge"""
        if not csv_field:
            return "unmapped", "No CSV field mapped"
            
        if csv_data_count == 0:
            return "questionable", f"Mapped to {csv_field} but no data available"
            
        # Semantic analysis using domain knowledge
        json_lower = json_field.lower()
        csv_lower = csv_field.lower()
        
        # Perfect matches - exact or nearly exact semantic alignment
        perfect_patterns = [
            # Exact matches
            (json_lower == csv_lower),
            # ID fields
            (json_lower.endswith('_id') and csv_lower.endswith('_id') and 
             json_lower.replace('_id', '') == csv_lower.replace('_id', '')),
            # Name fields
            (json_lower.endswith('_name') and csv_lower.endswith('_name') and 
             json_lower.replace('_name', '') == csv_lower.replace('_name', '')),
            # Number fields
            (json_lower.endswith('_number') and csv_lower.endswith('_number') and 
             json_lower.replace('_number', '') == csv_lower.replace('_number', '')),
            # Date fields
            (json_lower.endswith('_date') and csv_lower.endswith('_date') and 
             json_lower.replace('_date', '') == csv_lower.replace('_date', '')),
            # Amount/Total fields
            (json_lower in ['total', 'amount', 'balance'] and csv_lower in ['total', 'amount', 'balance']),
            # Status fields
            (json_lower.endswith('_status') and csv_lower.endswith('_status')),
        ]
        
        if any(perfect_patterns):
            return "perfect", f"Excellent semantic match: {json_field} -> {csv_field}"
            
        # Good matches - logical business relationships
        good_patterns = [
            # ID to name relationships (acceptable for identification)
            (json_lower.endswith('_id') and csv_lower.endswith('_name') and 
             json_lower.replace('_id', '') == csv_lower.replace('_name', '')),
            # Related business concepts
            ('bill' in json_lower and 'bill' in csv_lower),
            ('invoice' in json_lower and 'invoice' in csv_lower),
            ('payment' in json_lower and 'payment' in csv_lower),
            ('customer' in json_lower and 'customer' in csv_lower),
            ('vendor' in json_lower and 'vendor' in csv_lower),
            ('item' in json_lower and 'item' in csv_lower),
            ('tax' in json_lower and 'tax' in csv_lower),
            ('address' in json_lower and 'address' in csv_lower),
            ('phone' in json_lower and 'phone' in csv_lower),
            ('email' in json_lower and 'email' in csv_lower),
            # Date relationships
            ('date' in json_lower and 'date' in csv_lower),
            ('time' in json_lower and 'time' in csv_lower),
            # Amount relationships
            ('amount' in json_lower and ('amount' in csv_lower or 'total' in csv_lower)),
            ('total' in json_lower and ('total' in csv_lower or 'amount' in csv_lower)),
            ('balance' in json_lower and 'balance' in csv_lower),
            # Account relationships
            ('account' in json_lower and 'account' in csv_lower),
            # Reference relationships
            ('reference' in json_lower and 'reference' in csv_lower),
        ]
        
        if any(good_patterns):
            return "good", f"Good business relationship: {json_field} -> {csv_field}"
            
        # Questionable matches - semantic mismatches or unclear relationships
        questionable_patterns = [
            # Type mismatches
            ('_id' in json_lower and 'name' in csv_lower and not any(
                json_lower.replace('_id', '') == csv_lower.replace(suffix, '') 
                for suffix in ['_name', 'name'])),
            ('date' in json_lower and not ('date' in csv_lower or 'time' in csv_lower)),
            ('amount' in json_lower and not ('amount' in csv_lower or 'total' in csv_lower or 'balance' in csv_lower)),
            ('status' in json_lower and not 'status' in csv_lower),
            # Metadata to business data
            (json_lower in ['tags', 'has_attachment', 'documents'] and 
             csv_lower not in ['tags', 'attachment', 'documents']),
            # Obviously unrelated concepts
            ('color' in json_lower and not 'color' in csv_lower),
            ('image' in json_lower and not 'image' in csv_lower),
            ('precision' in json_lower and not 'precision' in csv_lower),
        ]
        
        if any(questionable_patterns):
            return "questionable", f"Semantic mismatch or unclear relationship: {json_field} -> {csv_field}"
            
        # Default to good if no red flags
        return "good", f"Acceptable mapping: {json_field} -> {csv_field}"
    
    def check_duplicate_mappings(self, conn, json_table):
        """Check for duplicate CSV field mappings (violation of one-to-one rule)"""
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT CSV_field, GROUP_CONCAT(field_name) as json_fields, COUNT(*) as count
            FROM {json_table}
            WHERE CSV_field IS NOT NULL
            GROUP BY CSV_field
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = []
        for csv_field, json_fields, count in cursor.fetchall():
            duplicates.append({
                "csv_field": csv_field,
                "json_fields": json_fields.split(','),
                "count": count,
                "table": json_table
            })
            
        return duplicates
    
    def analyze_table_comprehensively(self, conn, json_table, csv_table):
        """Comprehensive analysis of a single table"""
        print(f"\n📋 ANALYZING {json_table} -> {csv_table}")
        print("-" * 60)
        
        cursor = conn.cursor()
        
        # Get all JSON mappings
        cursor.execute(f"""
            SELECT field_name, CSV_field, CSV_data_count 
            FROM {json_table}
            ORDER BY field_name
        """)
        mappings = cursor.fetchall()
        
        # Get CSV field counts for reference
        csv_counts = self.get_csv_field_counts(conn, csv_table)
        
        # Check for duplicate mappings
        duplicates = self.check_duplicate_mappings(conn, json_table)
        
        # Categorize each mapping
        categorized = {
            "perfect": [],
            "good": [],
            "questionable": [],
            "unmapped": []
        }
        
        critical_issues = []
        
        for json_field, csv_field, csv_data_count in mappings:
            category, reason = self.categorize_mapping_quality(json_field, csv_field, csv_data_count)
            
            mapping_info = {
                "json_field": json_field,
                "csv_field": csv_field,
                "csv_data_count": csv_data_count,
                "reason": reason
            }
            
            categorized[category].append(mapping_info)
            
            # Check for critical issues (unmapped/questionable with available CSV data)
            if category in ["unmapped", "questionable"]:
                # Look for available CSV fields with data
                available_fields = [(field, count) for field, count in csv_counts.items() 
                                  if count > 0 and field != csv_field]
                
                if available_fields and category == "unmapped":
                    critical_issues.append({
                        "type": "unmapped_with_data",
                        "json_field": json_field,
                        "available_csv_fields": available_fields[:5],  # Top 5
                        "severity": "HIGH"
                    })
                elif category == "questionable" and csv_data_count == 0 and available_fields:
                    critical_issues.append({
                        "type": "mapped_to_empty_field",
                        "json_field": json_field,
                        "current_mapping": csv_field,
                        "available_csv_fields": available_fields[:5],
                        "severity": "MEDIUM"
                    })
        
        # Store analysis results
        table_analysis = {
            "total_fields": len(mappings),
            "perfect": len(categorized["perfect"]),
            "good": len(categorized["good"]),
            "questionable": len(categorized["questionable"]),
            "unmapped": len(categorized["unmapped"]),
            "duplicate_mappings": duplicates,
            "critical_issues": critical_issues,
            "categorized_mappings": categorized,
            "csv_table": csv_table
        }
        
        self.analysis_results["table_analysis"][json_table] = table_analysis
        
        # Print summary
        print(f"   📊 Perfect: {len(categorized['perfect'])}")
        print(f"   ✅ Good: {len(categorized['good'])}")
        print(f"   ⚠️  Questionable: {len(categorized['questionable'])}")
        print(f"   ❌ Unmapped: {len(categorized['unmapped'])}")
        print(f"   🔄 Duplicate mappings: {len(duplicates)}")
        print(f"   🚨 Critical issues: {len(critical_issues)}")
        
        # Show critical issues
        for issue in critical_issues:
            if issue["type"] == "unmapped_with_data":
                print(f"      🚨 {issue['json_field']}: UNMAPPED but CSV data available")
            else:
                print(f"      ⚠️  {issue['json_field']}: Mapped to empty field but data available")
                
        # Show duplicate mappings
        for dup in duplicates:
            print(f"      🔄 DUPLICATE: {dup['csv_field']} -> {dup['json_fields']}")
            
        return table_analysis
    
    def run_comprehensive_analysis(self):
        """Run comprehensive manual mapping analysis"""
        print("🔍 COMPREHENSIVE MANUAL MAPPING ANALYSIS")
        print("Following instructions: Manual review with domain knowledge")
        print("Key requirement: ONLY ONE CSV_field per JSON field (checking duplicates)")
        print("=" * 80)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Define table mappings
            table_mappings = [
                ("map_json_bills", "bills"),
                ("map_json_contacts", "contacts"),
                ("map_json_invoices", "invoices"),
                ("map_json_items", "items"),
                ("map_json_customer_payments", "customer_payments"),
                ("map_json_vendor_payments", "vendor_payments"),
                ("map_json_credit_notes", "credit_notes"),
                ("map_json_sales_orders", "sales_orders"),
                ("map_json_purchase_orders", "purchase_orders"),
                ("map_json_bills_line_items", "bills"),
                ("map_json_invoices_line_items", "invoices"),
                ("map_json_creditnotes_line_items", "credit_notes"),
                ("map_json_salesorders_line_items", "sales_orders"),
                ("map_json_purchaseorders_line_items", "purchase_orders"),
                ("map_json_organizations", "contacts")  # No direct CSV equivalent
            ]
            
            # Analyze each table
            total_perfect = 0
            total_good = 0
            total_questionable = 0
            total_unmapped = 0
            total_duplicates = 0
            total_critical = 0
            
            for json_table, csv_table in table_mappings:
                try:
                    analysis = self.analyze_table_comprehensively(conn, json_table, csv_table)
                    
                    total_perfect += analysis["perfect"]
                    total_good += analysis["good"]
                    total_questionable += analysis["questionable"]
                    total_unmapped += analysis["unmapped"]
                    total_duplicates += len(analysis["duplicate_mappings"])
                    total_critical += len(analysis["critical_issues"])
                    
                    # Collect all duplicates and critical issues
                    self.analysis_results["duplicate_mappings"].extend(analysis["duplicate_mappings"])
                    self.analysis_results["critical_issues"].extend(analysis["critical_issues"])
                    
                except Exception as e:
                    print(f"   ❌ Error analyzing {json_table}: {e}")
            
            conn.close()
            
            # Generate overall summary
            total_fields = total_perfect + total_good + total_questionable + total_unmapped
            
            self.analysis_results["summary"] = {
                "total_fields": total_fields,
                "perfect_count": total_perfect,
                "good_count": total_good,
                "questionable_count": total_questionable,
                "unmapped_count": total_unmapped,
                "duplicate_mappings_count": total_duplicates,
                "critical_issues_count": total_critical,
                "quality_score": round((total_perfect + total_good) / total_fields * 100, 2) if total_fields > 0 else 0
            }
            
            # Generate recommendations
            self.generate_recommendations()
            
            # Generate reports
            self.generate_comprehensive_reports()
            
            print(f"\n📊 OVERALL ANALYSIS SUMMARY")
            print("=" * 80)
            print(f"   📋 Total fields analyzed: {total_fields}")
            print(f"   🎯 Perfect mappings: {total_perfect}")
            print(f"   ✅ Good mappings: {total_good}")
            print(f"   ⚠️  Questionable mappings: {total_questionable}")
            print(f"   ❌ Unmapped fields: {total_unmapped}")
            print(f"   🔄 Duplicate mappings: {total_duplicates}")
            print(f"   🚨 Critical issues: {total_critical}")
            print(f"   📈 Quality score: {self.analysis_results['summary']['quality_score']}%")
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return False
            
        return True
    
    def generate_recommendations(self):
        """Generate specific recommendations for improvements"""
        recommendations = {}
        
        for table, analysis in self.analysis_results["table_analysis"].items():
            table_recs = []
            
            # Recommendations for duplicates
            if analysis["duplicate_mappings"]:
                table_recs.append({
                    "priority": "HIGH",
                    "issue": "Duplicate CSV mappings violate one-to-one rule",
                    "action": f"Resolve {len(analysis['duplicate_mappings'])} duplicate mappings",
                    "details": [f"{dup['csv_field']} mapped to {len(dup['json_fields'])} fields" 
                              for dup in analysis["duplicate_mappings"]]
                })
            
            # Recommendations for critical issues
            if analysis["critical_issues"]:
                table_recs.append({
                    "priority": "HIGH",
                    "issue": "Unmapped fields with available CSV data",
                    "action": f"Map {len(analysis['critical_issues'])} critical fields",
                    "details": [f"{issue['json_field']}: {issue['type']}" 
                              for issue in analysis["critical_issues"]]
                })
            
            # Recommendations for questionable mappings
            if analysis["questionable"] > 0:
                table_recs.append({
                    "priority": "MEDIUM",
                    "issue": "Questionable semantic mappings",
                    "action": f"Review {analysis['questionable']} questionable mappings",
                    "details": [f"{mapping['json_field']} -> {mapping['csv_field']}" 
                              for mapping in analysis["categorized_mappings"]["questionable"]]
                })
            
            recommendations[table] = table_recs
            
        self.analysis_results["recommendations"] = recommendations
    
    def generate_comprehensive_reports(self):
        """Generate comprehensive analysis reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate JSON report
        json_file = f"comprehensive_mapping_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        # Generate detailed Markdown report
        md_file = f"comprehensive_mapping_report_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            self.write_comprehensive_report(f)
        
        print(f"\n📄 Comprehensive reports generated:")
        print(f"   📊 JSON: {json_file}")
        print(f"   📋 Markdown: {md_file}")
    
    def write_comprehensive_report(self, f):
        """Write comprehensive markdown report"""
        f.write("# Comprehensive Manual Mapping Analysis Report\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n")
        f.write("**Analysis Type:** Manual review using domain knowledge and business logic\n")
        f.write("**Key Requirement:** ONLY ONE CSV_field can be mapped to each JSON field\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        summary = self.analysis_results["summary"]
        f.write(f"- **Total Fields Analyzed:** {summary['total_fields']}\n")
        f.write(f"- **Quality Score:** {summary['quality_score']}%\n")
        f.write(f"- **Perfect Mappings:** {summary['perfect_count']} ({summary['perfect_count']/summary['total_fields']*100:.1f}%)\n")
        f.write(f"- **Good Mappings:** {summary['good_count']} ({summary['good_count']/summary['total_fields']*100:.1f}%)\n")
        f.write(f"- **Questionable Mappings:** {summary['questionable_count']} ({summary['questionable_count']/summary['total_fields']*100:.1f}%)\n")
        f.write(f"- **Unmapped Fields:** {summary['unmapped_count']} ({summary['unmapped_count']/summary['total_fields']*100:.1f}%)\n")
        f.write(f"- **Duplicate Mappings:** {summary['duplicate_mappings_count']} (RULE VIOLATION)\n")
        f.write(f"- **Critical Issues:** {summary['critical_issues_count']}\n\n")
        
        # Critical Issues Section
        if self.analysis_results["critical_issues"]:
            f.write("## 🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION\n\n")
            
            unmapped_issues = [issue for issue in self.analysis_results["critical_issues"] 
                             if issue["type"] == "unmapped_with_data"]
            empty_mapping_issues = [issue for issue in self.analysis_results["critical_issues"] 
                                  if issue["type"] == "mapped_to_empty_field"]
            
            if unmapped_issues:
                f.write("### Unmapped Fields with Available CSV Data\n\n")
                for issue in unmapped_issues:
                    f.write(f"**{issue['json_field']}** - Unmapped but CSV data available:\n")
                    for csv_field, count in issue["available_csv_fields"][:3]:
                        f.write(f"- {csv_field}: {count} records\n")
                    f.write("\n")
                    
            if empty_mapping_issues:
                f.write("### Fields Mapped to Empty CSV Fields\n\n")
                for issue in empty_mapping_issues:
                    f.write(f"**{issue['json_field']}** - Currently mapped to {issue['current_mapping']} (0 records):\n")
                    for csv_field, count in issue["available_csv_fields"][:3]:
                        f.write(f"- Alternative: {csv_field}: {count} records\n")
                    f.write("\n")
        
        # Duplicate Mappings Section
        if self.analysis_results["duplicate_mappings"]:
            f.write("## 🔄 DUPLICATE MAPPINGS (RULE VIOLATIONS)\n\n")
            f.write("**CRITICAL:** Multiple JSON fields mapped to same CSV field violates one-to-one rule\n\n")
            
            for dup in self.analysis_results["duplicate_mappings"]:
                f.write(f"### {dup['table']} - {dup['csv_field']}\n")
                f.write(f"**CSV Field:** {dup['csv_field']}\n")
                f.write(f"**Mapped JSON Fields:** {len(dup['json_fields'])}\n")
                for json_field in dup['json_fields']:
                    f.write(f"- {json_field}\n")
                f.write("\n")
        
        # Table-by-Table Analysis
        f.write("## 📋 TABLE-BY-TABLE ANALYSIS\n\n")
        
        for table, analysis in self.analysis_results["table_analysis"].items():
            f.write(f"### {table}\n")
            f.write(f"**CSV Table:** {analysis['csv_table']}\n")
            f.write(f"**Total Fields:** {analysis['total_fields']}\n")
            f.write(f"**Quality Breakdown:**\n")
            f.write(f"- Perfect: {analysis['perfect']}\n")
            f.write(f"- Good: {analysis['good']}\n")
            f.write(f"- Questionable: {analysis['questionable']}\n")
            f.write(f"- Unmapped: {analysis['unmapped']}\n")
            f.write(f"- Duplicates: {len(analysis['duplicate_mappings'])}\n")
            f.write(f"- Critical Issues: {len(analysis['critical_issues'])}\n\n")
            
            # Show some examples of each category
            for category in ["perfect", "good", "questionable", "unmapped"]:
                mappings = analysis["categorized_mappings"][category]
                if mappings:
                    f.write(f"**{category.title()} Mappings:**\n")
                    for mapping in mappings[:5]:  # Show first 5
                        if category == "unmapped":
                            f.write(f"- {mapping['json_field']}: UNMAPPED\n")
                        else:
                            f.write(f"- {mapping['json_field']} -> {mapping['csv_field']} ({mapping['csv_data_count']} records)\n")
                    if len(mappings) > 5:
                        f.write(f"- ... and {len(mappings) - 5} more\n")
                    f.write("\n")
        
        # Recommendations
        f.write("## 🔧 RECOMMENDATIONS BY PRIORITY\n\n")
        
        for table, recs in self.analysis_results["recommendations"].items():
            if recs:
                f.write(f"### {table}\n")
                for rec in recs:
                    f.write(f"**{rec['priority']} PRIORITY:** {rec['issue']}\n")
                    f.write(f"- Action: {rec['action']}\n")
                    if rec['details']:
                        f.write("- Details:\n")
                        for detail in rec['details'][:5]:
                            f.write(f"  - {detail}\n")
                    f.write("\n")
        
        # Next Steps
        f.write("## 🚀 NEXT STEPS\n\n")
        f.write("1. **IMMEDIATE:** Resolve duplicate mappings (violate one-to-one rule)\n")
        f.write("2. **HIGH PRIORITY:** Map unmapped fields with available CSV data\n")
        f.write("3. **MEDIUM PRIORITY:** Review questionable semantic mappings\n")
        f.write("4. **VALIDATION:** Test all mapping changes with sample data\n")
        f.write("5. **DOCUMENTATION:** Update mapping documentation\n\n")

if __name__ == "__main__":
    analyzer = ComprehensiveMappingAnalyzer()
    analyzer.run_comprehensive_analysis()
