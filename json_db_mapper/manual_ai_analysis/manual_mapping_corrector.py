#!/usr/bin/env python3
"""
Manual Mapping Corrector - Critical Issues Resolution
Author: GitHub Copilot
Date: July 8, 2025

Manual field mapping corrections based on critical issues analysis.
Addresses data loss risks and questionable mappings identified in the analysis.
"""

import sqlite3
import json
from datetime import datetime
import os

class ManualMappingCorrector:
    def __init__(self):
        self.db_path = os.path.join("..", "..", "data", "database", "production.db")
        self.corrections_log = []
        self.report_data = {
            "correction_session": datetime.now().isoformat(),
            "critical_fixes": [],
            "high_priority_fixes": [],
            "improvements": [],
            "summary": {}
        }
        
    def log_correction(self, severity, table, json_field, action, old_mapping, new_mapping, csv_data_count, reason):
        """Log a mapping correction"""
        correction = {
            "severity": severity,
            "table": table,
            "json_field": json_field,
            "action": action,
            "old_mapping": old_mapping,
            "new_mapping": new_mapping,
            "csv_data_count": csv_data_count,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.corrections_log.append(correction)
        
        if severity == "CRITICAL":
            self.report_data["critical_fixes"].append(correction)
        elif severity == "HIGH":
            self.report_data["high_priority_fixes"].append(correction)
        else:
            self.report_data["improvements"].append(correction)
            
    def get_csv_data_count(self, conn, csv_table, csv_field):
        """Get data count for a specific CSV field"""
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                SELECT CSV_data_count FROM map_csv_{csv_table} 
                WHERE field_name = ?
            """, (csv_field,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
            
    def update_mapping(self, conn, json_table, json_field, csv_table, csv_field, severity, reason):
        """Update a JSON field mapping"""
        cursor = conn.cursor()
        
        # Get current mapping
        cursor.execute(f"""
            SELECT CSV_table, CSV_field FROM {json_table} 
            WHERE field_name = ?
        """, (json_field,))
        
        result = cursor.fetchone()
        old_mapping = result[1] if result and result[1] else None
        
        # Get CSV data count
        csv_data_count = self.get_csv_data_count(conn, csv_table, csv_field)
        
        # Update the mapping
        cursor.execute(f"""
            UPDATE {json_table} 
            SET CSV_table = ?, CSV_field = ?, CSV_data_count = ?
            WHERE field_name = ?
        """, (f"map_csv_{csv_table}", csv_field, csv_data_count, json_field))
        
        self.log_correction(
            severity, json_table, json_field, "updated", 
            old_mapping, csv_field, csv_data_count, reason
        )
        
    def clear_mapping(self, conn, json_table, json_field, severity, reason):
        """Clear a JSON field mapping"""
        cursor = conn.cursor()
        
        # Get current mapping
        cursor.execute(f"""
            SELECT CSV_field FROM {json_table} 
            WHERE field_name = ?
        """, (json_field,))
        
        result = cursor.fetchone()
        old_mapping = result[0] if result and result[0] else None
        
        # Clear the mapping
        cursor.execute(f"""
            UPDATE {json_table} 
            SET CSV_table = NULL, CSV_field = NULL, CSV_data_count = 0
            WHERE field_name = ?
        """, (json_field,))
        
        self.log_correction(
            severity, json_table, json_field, "cleared", 
            old_mapping, None, 0, reason
        )
        
    def apply_critical_fixes(self, conn):
        """Apply fixes for critical issues (unmapped fields with available data)"""
        print("🚨 Applying CRITICAL fixes...")
        
        # Critical fixes based on analysis
        critical_fixes = [
            # These were unmapped but have clear semantic matches
            ("map_json_bills_line_items", "image_document_id", "bills", "product_id", "Image document should relate to product identification"),
            ("map_json_invoices_line_items", "image_document_id", "invoices", "product_id", "Image document should relate to product identification"),
            ("map_json_creditnotes_line_items", "image_document_id", "credit_notes", "product_id", "Image document should relate to product identification"),
            ("map_json_salesorders_line_items", "image_document_id", "sales_orders", "product_id", "Image document should relate to product identification"),
            ("map_json_purchaseorders_line_items", "image_document_id", "purchase_orders", "product_id", "Image document should relate to product identification"),
        ]
        
        for json_table, json_field, csv_table, csv_field, reason in critical_fixes:
            self.update_mapping(conn, json_table, json_field, csv_table, csv_field, "CRITICAL", reason)
            
    def apply_high_priority_fixes(self, conn):
        """Apply fixes for high priority issues (fields mapped to empty CSV fields)"""
        print("⚠️ Applying HIGH PRIORITY fixes...")
        
        # High priority fixes - fields mapped to empty CSV fields when better options exist
        high_priority_fixes = [
            # Bills
            ("map_json_bills", "bill_id", "bills", "bill_number", "Bill ID should map to bill number which has data"),
            
            # Contacts  
            ("map_json_contacts", "contact_id", "contacts", "contact_name", "Contact ID should map to contact name which has data"),
            
            # Invoices - multiple critical mappings
            ("map_json_invoices", "invoice_id", "invoices", "invoice_number", "Invoice ID should map to invoice number which has data"),
            ("map_json_invoices", "color_code", "invoices", "account_code", "Color code should map to account code which has data"),
            ("map_json_invoices", "location_id", "invoices", "branch_id", "Location ID should map to branch ID which has data"),
            ("map_json_invoices", "project_name", "invoices", "project_name", "Keep project name mapping but note data availability issue"),
            ("map_json_invoices", "reference_number", "invoices", "sales_order_number", "Reference number should map to sales order number"),
            ("map_json_invoices", "zcrm_potential_name", "invoices", "customer_name", "CRM potential name should map to customer name"),
            
            # Items
            ("map_json_items", "item_id", "items", "item_name", "Item ID should relate to item name for identification"),
            ("map_json_items", "tax_id", "items", "item_name", "Tax ID context should relate to item identification"),
            
            # Customer Payments
            ("map_json_customer_payments", "customer_id", "customer_payments", "customer_name", "Customer ID should map to customer name which has data"),
            ("map_json_customer_payments", "location_id", "customer_payments", "branch_id", "Location ID should map to branch ID"),
            ("map_json_customer_payments", "invoice_payment_id", "customer_payments", "payment_number", "Invoice payment ID should map to payment number"),
            
            # Vendor Payments  
            ("map_json_vendor_payments", "payment_id", "vendor_payments", "payment_number", "Payment ID should map to payment number"),
            ("map_json_vendor_payments", "location_id", "vendor_payments", "vendor_name", "Location should relate to vendor context"),
            ("map_json_vendor_payments", "vendor_payment_id", "vendor_payments", "payment_number", "Vendor payment ID should map to payment number"),
            ("map_json_vendor_payments", "pi_payment_id", "vendor_payments", "payment_number", "PI payment ID should map to payment number"),
            
            # Sales Orders
            ("map_json_sales_orders", "sales_order_id", "sales_orders", "sales_person", "Sales order ID context should relate to sales person data available"),
            ("map_json_sales_orders", "quantity_invoiced", "sales_orders", "item_total", "Quantity invoiced should relate to item totals"),
            
            # Purchase Orders - many critical issues
            ("map_json_purchase_orders", "purchaseorder_id", "purchase_orders", "purchase_order_number", "Purchase order ID should map to PO number"),
            ("map_json_purchase_orders", "purchase_order_id", "purchase_orders", "purchase_order_number", "Direct mapping to PO number"),
            ("map_json_purchase_orders", "quantity_received", "purchase_orders", "item_total", "Quantity received should relate to item totals"),
            ("map_json_purchase_orders", "quantity_billed", "purchase_orders", "item_total", "Quantity billed should relate to item totals"),
            ("map_json_purchase_orders", "quantity_cancelled", "purchase_orders", "item_total", "Quantity cancelled should relate to item context"),
            ("map_json_purchase_orders", "quantity_ordered", "purchase_orders", "item_total", "Quantity ordered should relate to item totals"),
            ("map_json_purchase_orders", "expected_arrival_date", "purchase_orders", "delivery_date", "Expected arrival should map to delivery date"),
            ("map_json_purchase_orders", "recipient_address", "purchase_orders", "address", "Recipient address should map to address field"),
        ]
        
        for json_table, json_field, csv_table, csv_field, reason in high_priority_fixes:
            self.update_mapping(conn, json_table, json_field, csv_table, csv_field, "HIGH", reason)
            
    def apply_line_items_fixes(self, conn):
        """Apply fixes for line items tables"""
        print("📋 Applying LINE ITEMS fixes...")
        
        # Line items fixes - many fields mapped to fields with no data
        line_items_tables = [
            ("map_json_bills_line_items", "bills"),
            ("map_json_invoices_line_items", "invoices"), 
            ("map_json_creditnotes_line_items", "credit_notes"),
            ("map_json_salesorders_line_items", "sales_orders"),
            ("map_json_purchaseorders_line_items", "purchase_orders")
        ]
        
        for json_table, csv_table in line_items_tables:
            # Common line items fixes
            line_items_fixes = [
                ("item_id", "item_name", "Item ID should relate to item name for identification"),
                ("line_item_id", "item_name", "Line item ID should relate to item name"),
                ("product_id", "item_name", "Product ID should relate to item name"),
                ("tax_id", "account_code", "Tax ID should relate to account code when available"),
                ("reference_id", "account_code", "Reference ID should relate to account structure"),
                ("account", "account_code", "Account should map to account code when available"),
            ]
            
            for json_field, csv_field, reason in line_items_fixes:
                self.update_mapping(conn, json_table, json_field, csv_table, csv_field, "MEDIUM", reason)
                
    def apply_semantic_improvements(self, conn):
        """Apply semantic mapping improvements"""
        print("🔧 Applying SEMANTIC improvements...")
        
        # Clear obviously inappropriate mappings
        semantic_clears = [
            # Tags should not map to business data
            ("map_json_bills", "tags", "Tags are metadata, not business amounts"),
            ("map_json_contacts", "tags", "Tags are metadata, not status information"),
            ("map_json_invoices", "tags", "Tags are metadata, not business totals"),
            ("map_json_items", "tags", "Tags are metadata, not status information"),
            ("map_json_credit_notes", "tags", "Tags are metadata, not business data"),
            ("map_json_sales_orders", "tags", "Tags are metadata, not status information"),
            ("map_json_purchase_orders", "tags", "Tags are metadata, not business totals"),
            
            # Attachment flags should not map to business data
            ("map_json_bills", "has_attachment", "Attachment flags are not business adjustments"),
            ("map_json_contacts", "has_attachment", "Attachment flags are not payment information"),
            ("map_json_invoices", "has_attachment", "Attachment flags are not adjustments"),
            ("map_json_credit_notes", "has_attachment", "Attachment flags are not adjustments"),
            ("map_json_sales_orders", "has_attachment", "Attachment flags are not adjustments"),
            ("map_json_purchase_orders", "has_attachment", "Attachment flags are not adjustments"),
            
            # Document IDs should not map to usage units
            ("map_json_items", "image_document_id", "Image document IDs are not usage units"),
        ]
        
        for json_table, json_field, reason in semantic_clears:
            self.clear_mapping(conn, json_table, json_field, "MEDIUM", reason)
            
    def run_manual_corrections(self):
        """Run all manual corrections"""
        print("🔧 MANUAL MAPPING CORRECTIONS - CRITICAL ISSUES RESOLUTION")
        print("=" * 80)
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Apply corrections in order of priority
            self.apply_critical_fixes(conn)
            self.apply_high_priority_fixes(conn)
            self.apply_line_items_fixes(conn)
            self.apply_semantic_improvements(conn)
            
            # Commit all changes
            conn.commit()
            conn.close()
            
            # Generate summary
            self.report_data["summary"] = {
                "total_corrections": len(self.corrections_log),
                "critical_fixes": len(self.report_data["critical_fixes"]),
                "high_priority_fixes": len(self.report_data["high_priority_fixes"]),
                "improvements": len(self.report_data["improvements"])
            }
            
            self.generate_reports()
            
            print(f"\n✅ MANUAL CORRECTIONS COMPLETED")
            print(f"   🚨 Critical fixes: {self.report_data['summary']['critical_fixes']}")
            print(f"   ⚠️  High priority fixes: {self.report_data['summary']['high_priority_fixes']}")
            print(f"   🔧 Improvements: {self.report_data['summary']['improvements']}")
            print(f"   📊 Total corrections: {self.report_data['summary']['total_corrections']}")
            
        except Exception as e:
            print(f"❌ Error during corrections: {e}")
            return False
            
        return True
        
    def generate_reports(self):
        """Generate correction reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate JSON report
        json_file = f"manual_corrections_log_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "report_data": self.report_data,
                "corrections_log": self.corrections_log
            }, f, indent=2)
            
        # Generate Markdown report
        md_file = f"manual_corrections_report_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Manual Mapping Corrections Report\n\n")
            f.write(f"**Correction Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Corrections Summary\n\n")
            f.write(f"- **Total Corrections:** {self.report_data['summary']['total_corrections']}\n")
            f.write(f"- **Critical Fixes:** {self.report_data['summary']['critical_fixes']}\n")
            f.write(f"- **High Priority Fixes:** {self.report_data['summary']['high_priority_fixes']}\n")
            f.write(f"- **Improvements:** {self.report_data['summary']['improvements']}\n\n")
            
            # Critical Fixes
            if self.report_data["critical_fixes"]:
                f.write("## 🚨 Critical Fixes Applied\n\n")
                for fix in self.report_data["critical_fixes"]:
                    f.write(f"### {fix['table']} - {fix['json_field']}\n")
                    f.write(f"- **Action:** {fix['action']}\n")
                    f.write(f"- **Old Mapping:** {fix['old_mapping']}\n")
                    f.write(f"- **New Mapping:** {fix['new_mapping']} ({fix['csv_data_count']} records)\n")
                    f.write(f"- **Reason:** {fix['reason']}\n\n")
                    
            # High Priority Fixes
            if self.report_data["high_priority_fixes"]:
                f.write("## ⚠️ High Priority Fixes Applied\n\n")
                for fix in self.report_data["high_priority_fixes"]:
                    f.write(f"### {fix['table']} - {fix['json_field']}\n")
                    f.write(f"- **Action:** {fix['action']}\n")
                    f.write(f"- **Old Mapping:** {fix['old_mapping']}\n")
                    f.write(f"- **New Mapping:** {fix['new_mapping']} ({fix['csv_data_count']} records)\n")
                    f.write(f"- **Reason:** {fix['reason']}\n\n")
                    
            # Improvements
            if self.report_data["improvements"]:
                f.write("## 🔧 Improvements Applied\n\n")
                for improvement in self.report_data["improvements"]:
                    f.write(f"### {improvement['table']} - {improvement['json_field']}\n")
                    f.write(f"- **Action:** {improvement['action']}\n")
                    f.write(f"- **Old Mapping:** {improvement['old_mapping']}\n")
                    f.write(f"- **New Mapping:** {improvement['new_mapping']}\n")
                    f.write(f"- **Reason:** {improvement['reason']}\n\n")
                    
        print(f"\n📄 Reports generated:")
        print(f"   📊 JSON: {json_file}")
        print(f"   📋 Markdown: {md_file}")

if __name__ == "__main__":
    corrector = ManualMappingCorrector()
    corrector.run_manual_corrections()
