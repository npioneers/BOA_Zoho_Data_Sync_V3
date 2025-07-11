#!/usr/bin/env python3
"""
Critical Issues Analysis - Manual Mapping Review
Author: GitHub Copilot
Date: July 8, 2025

Analyzes questionable and unmapped fields to identify critical issues where:
1. Questionable mappings exist but better CSV fields with data are available
2. Unmapped JSON fields exist but corresponding CSV fields with data are available
3. Fields are mapped to CSV fields with no data when better options exist

This analysis focuses on data loss prevention and mapping accuracy.
"""

import sqlite3
import json
from datetime import datetime
import os

class CriticalIssuesAnalyzer:
    def __init__(self):
        self.db_path = os.path.join("..", "..", "data", "database", "production.db")
        self.issues = []
        self.analysis_data = {
            "analysis_date": datetime.now().isoformat(),
            "critical_issues": [],
            "questionable_mappings": [],
            "unmapped_with_data": [],
            "data_loss_risks": [],
            "summary": {}
        }
        
    def log_issue(self, severity, table, json_field, issue_type, description, current_mapping=None, suggested_mapping=None, csv_data_count=0):
        """Log a critical mapping issue"""
        issue = {
            "severity": severity,
            "table": table,
            "json_field": json_field,
            "issue_type": issue_type,
            "description": description,
            "current_mapping": current_mapping,
            "suggested_mapping": suggested_mapping,
            "csv_data_count": csv_data_count,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        
        if severity == "CRITICAL":
            self.analysis_data["critical_issues"].append(issue)
        elif issue_type == "questionable_mapping":
            self.analysis_data["questionable_mappings"].append(issue)
        elif issue_type == "unmapped_with_data":
            self.analysis_data["unmapped_with_data"].append(issue)
        elif issue_type == "data_loss_risk":
            self.analysis_data["data_loss_risks"].append(issue)
            
    def get_csv_field_data_counts(self, conn, csv_table):
        """Get data counts for all fields in a CSV table"""
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT field_name, CSV_data_count 
            FROM map_csv_{csv_table}
            ORDER BY CSV_data_count DESC
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}
        
    def analyze_table_mappings(self, conn, json_table, csv_table):
        """Analyze mappings for a specific table pair"""
        cursor = conn.cursor()
        
        print(f"🔍 Analyzing {json_table} -> {csv_table}")
        
        # Get current JSON mappings
        cursor.execute(f"""
            SELECT field_name, CSV_field, CSV_data_count 
            FROM {json_table}
            ORDER BY field_name
        """)
        json_mappings = cursor.fetchall()
        
        # Get CSV field data counts
        csv_data_counts = self.get_csv_field_data_counts(conn, csv_table)
        
        table_issues = 0
        
        for json_field, current_csv_field, current_data_count in json_mappings:
            # Check for unmapped fields
            if not current_csv_field:
                # Look for potential CSV matches with data
                potential_matches = []
                json_field_lower = json_field.lower()
                
                for csv_field, data_count in csv_data_counts.items():
                    if data_count > 0:
                        csv_field_lower = csv_field.lower()
                        # Simple semantic matching
                        if (json_field_lower in csv_field_lower or 
                            csv_field_lower in json_field_lower or
                            any(keyword in json_field_lower and keyword in csv_field_lower 
                                for keyword in ['id', 'name', 'date', 'amount', 'status', 'number', 'total', 'code'])):
                            potential_matches.append((csv_field, data_count))
                
                if potential_matches:
                    # Sort by data count descending
                    potential_matches.sort(key=lambda x: x[1], reverse=True)
                    best_match = potential_matches[0]
                    
                    self.log_issue(
                        "CRITICAL",
                        json_table,
                        json_field,
                        "unmapped_with_data",
                        f"JSON field '{json_field}' is unmapped but potential CSV field '{best_match[0]}' has {best_match[1]} records",
                        current_mapping=None,
                        suggested_mapping=best_match[0],
                        csv_data_count=best_match[1]
                    )
                    table_issues += 1
                    
            else:
                # Check if current mapping has no data but better options exist
                if current_data_count == 0:
                    # Look for better alternatives
                    better_options = []
                    json_field_lower = json_field.lower()
                    
                    for csv_field, data_count in csv_data_counts.items():
                        if data_count > 0 and csv_field != current_csv_field:
                            csv_field_lower = csv_field.lower()
                            if (json_field_lower in csv_field_lower or 
                                csv_field_lower in json_field_lower or
                                any(keyword in json_field_lower and keyword in csv_field_lower 
                                    for keyword in ['id', 'name', 'date', 'amount', 'status', 'number', 'total', 'code'])):
                                better_options.append((csv_field, data_count))
                    
                    if better_options:
                        better_options.sort(key=lambda x: x[1], reverse=True)
                        best_option = better_options[0]
                        
                        self.log_issue(
                            "HIGH",
                            json_table,
                            json_field,
                            "data_loss_risk",
                            f"JSON field '{json_field}' mapped to '{current_csv_field}' (0 records) but '{best_option[0]}' has {best_option[1]} records",
                            current_mapping=current_csv_field,
                            suggested_mapping=best_option[0],
                            csv_data_count=best_option[1]
                        )
                        table_issues += 1
                        
                # Check for questionable semantic mappings
                elif current_data_count > 0:
                    # Semantic validation - flag obviously wrong mappings
                    json_field_lower = json_field.lower()
                    csv_field_lower = current_csv_field.lower()
                    
                    # Check for obvious mismatches
                    mismatch_patterns = [
                        # Date fields mapped to non-date fields
                        (["date", "time", "created", "modified", "updated"], ["name", "id", "amount", "total", "status", "code"]),
                        # ID fields mapped to non-ID fields
                        (["_id", "id"], ["name", "date", "amount", "description", "notes"]),
                        # Amount fields mapped to non-amount fields
                        (["amount", "total", "balance", "price", "rate"], ["name", "id", "date", "status", "code"]),
                        # Status fields mapped to amounts
                        (["status", "state"], ["amount", "total", "balance", "rate", "price"]),
                        # Name fields mapped to numbers
                        (["name", "description", "notes"], ["amount", "total", "id", "count"])
                    ]
                    
                    for json_patterns, csv_patterns in mismatch_patterns:
                        if (any(pattern in json_field_lower for pattern in json_patterns) and
                            any(pattern in csv_field_lower for pattern in csv_patterns)):
                            
                            # Look for better semantic matches
                            better_matches = []
                            for csv_field, data_count in csv_data_counts.items():
                                if data_count > 0 and csv_field != current_csv_field:
                                    csv_field_check = csv_field.lower()
                                    if any(pattern in csv_field_check for pattern in json_patterns):
                                        better_matches.append((csv_field, data_count))
                            
                            if better_matches:
                                better_matches.sort(key=lambda x: x[1], reverse=True)
                                best_match = better_matches[0]
                                
                                self.log_issue(
                                    "MEDIUM",
                                    json_table,
                                    json_field,
                                    "questionable_mapping",
                                    f"Semantic mismatch: '{json_field}' mapped to '{current_csv_field}' but '{best_match[0]}' seems more appropriate ({best_match[1]} records)",
                                    current_mapping=current_csv_field,
                                    suggested_mapping=best_match[0],
                                    csv_data_count=best_match[1]
                                )
                                table_issues += 1
                                break
        
        return table_issues
        
    def run_analysis(self):
        """Run comprehensive critical issues analysis"""
        print("🚨 CRITICAL ISSUES ANALYSIS - MANUAL MAPPING REVIEW")
        print("=" * 80)
        print("Analyzing questionable and unmapped fields for data loss risks...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all JSON tables and their corresponding CSV tables
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
                ("map_json_purchaseorders_line_items", "purchase_orders")
            ]
            
            total_issues = 0
            
            for json_table, csv_table in table_mappings:
                try:
                    issues_count = self.analyze_table_mappings(conn, json_table, csv_table)
                    total_issues += issues_count
                    print(f"   🔍 {json_table}: {issues_count} issues found")
                except Exception as e:
                    print(f"   ❌ Error analyzing {json_table}: {e}")
                    
            # Organizations table (no direct CSV equivalent)
            print(f"   ⚠️  map_json_organizations: Skipped (no direct CSV equivalent)")
            
            conn.close()
            
            # Generate summary
            self.analysis_data["summary"] = {
                "total_issues": len(self.issues),
                "critical_issues": len(self.analysis_data["critical_issues"]),
                "questionable_mappings": len(self.analysis_data["questionable_mappings"]),
                "unmapped_with_data": len(self.analysis_data["unmapped_with_data"]),
                "data_loss_risks": len(self.analysis_data["data_loss_risks"])
            }
            
            self.generate_reports()
            
            print(f"\n📊 ANALYSIS COMPLETE")
            print(f"   🚨 Critical issues: {self.analysis_data['summary']['critical_issues']}")
            print(f"   ⚠️  High priority: {self.analysis_data['summary']['data_loss_risks']}")
            print(f"   📋 Questionable mappings: {self.analysis_data['summary']['questionable_mappings']}")
            print(f"   📄 Total issues: {self.analysis_data['summary']['total_issues']}")
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return False
            
        return True
        
    def generate_reports(self):
        """Generate comprehensive issue reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate JSON report
        json_file = f"critical_issues_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.analysis_data, f, indent=2)
            
        # Generate Markdown report
        md_file = f"critical_issues_report_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Critical Issues Analysis - Manual Mapping Review\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Issues Found:** {self.analysis_data['summary']['total_issues']}\n")
            f.write(f"- **Critical Issues:** {self.analysis_data['summary']['critical_issues']} (Unmapped fields with available CSV data)\n")
            f.write(f"- **High Priority:** {self.analysis_data['summary']['data_loss_risks']} (Mapped to fields with no data)\n")
            f.write(f"- **Medium Priority:** {self.analysis_data['summary']['questionable_mappings']} (Questionable semantic mappings)\n\n")
            
            # Critical Issues
            if self.analysis_data["critical_issues"]:
                f.write("## 🚨 CRITICAL ISSUES - Unmapped Fields with Available CSV Data\n\n")
                f.write("These are JSON fields that are completely unmapped but have potential CSV fields with data available.\n\n")
                
                for issue in self.analysis_data["critical_issues"]:
                    f.write(f"### {issue['table']} - {issue['json_field']}\n")
                    f.write(f"- **Issue:** {issue['description']}\n")
                    f.write(f"- **Suggested Mapping:** {issue['suggested_mapping']} ({issue['csv_data_count']} records)\n")
                    f.write(f"- **Risk:** Complete data loss for this field\n\n")
                    
            # Data Loss Risks
            if self.analysis_data["data_loss_risks"]:
                f.write("## ⚠️ HIGH PRIORITY - Data Loss Risks\n\n")
                f.write("These are JSON fields mapped to CSV fields with no data when better options exist.\n\n")
                
                for issue in self.analysis_data["data_loss_risks"]:
                    f.write(f"### {issue['table']} - {issue['json_field']}\n")
                    f.write(f"- **Current Mapping:** {issue['current_mapping']} (0 records)\n")
                    f.write(f"- **Suggested Mapping:** {issue['suggested_mapping']} ({issue['csv_data_count']} records)\n")
                    f.write(f"- **Risk:** Missing {issue['csv_data_count']} data records\n\n")
                    
            # Questionable Mappings
            if self.analysis_data["questionable_mappings"]:
                f.write("## 📋 MEDIUM PRIORITY - Questionable Semantic Mappings\n\n")
                f.write("These are mappings that may be semantically incorrect based on field names and types.\n\n")
                
                for issue in self.analysis_data["questionable_mappings"]:
                    f.write(f"### {issue['table']} - {issue['json_field']}\n")
                    f.write(f"- **Current Mapping:** {issue['current_mapping']}\n")
                    f.write(f"- **Issue:** {issue['description']}\n")
                    f.write(f"- **Suggested Alternative:** {issue['suggested_mapping']} ({issue['csv_data_count']} records)\n\n")
                    
            # Recommendations
            f.write("## 🔧 Recommended Actions\n\n")
            f.write("1. **Immediate Action Required:** Address all CRITICAL issues to prevent data loss\n")
            f.write("2. **High Priority:** Review and fix data loss risks where better CSV fields exist\n")
            f.write("3. **Medium Priority:** Evaluate questionable semantic mappings for accuracy\n")
            f.write("4. **Validation:** Test all mapping changes with sample data before production\n\n")
            
        print(f"\n📄 Reports generated:")
        print(f"   📊 JSON: {json_file}")
        print(f"   📋 Markdown: {md_file}")

if __name__ == "__main__":
    analyzer = CriticalIssuesAnalyzer()
    analyzer.run_analysis()
