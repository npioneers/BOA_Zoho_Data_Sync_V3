#!/usr/bin/env python3

import sqlite3
import yaml

def create_final_merged_views():
    """Create FINAL_ prefixed merged views for easy identification"""
    
    # Load config and connect
    with open('config/json_sync.yaml', 'r') as f:
        config = yaml.safe_load(f)
    conn = sqlite3.connect(config['json_sync']['database_path'])
    cursor = conn.cursor()
    
    print("=== CREATING FINAL MERGED VIEWS ===")
    print("Purpose: FINAL_ prefix for easy identification of production views")
    
    # Create FINAL_view_csv_json_bills
    print("\n1. Creating FINAL_view_csv_json_bills...")
    try:
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_bills;")
        
        final_bills_sql = """
        CREATE VIEW FINAL_view_csv_json_bills AS
        SELECT 
            COALESCE(flat.bill_number, csv.bill_number) AS bill_number,
            COALESCE(flat.vendor_name, csv.vendor_name) AS vendor_name,
            COALESCE(flat.total, csv.total) AS total,
            COALESCE(flat.balance, csv.balance) AS balance,
            COALESCE(flat.date, csv.bill_date) AS bill_date,
            csv.account,
            csv.account_code,
            csv.accounts_payable,
            flat.vendor_id,
            flat.due_date,
            flat.currency_code,
            flat.line_item_name,
            flat.line_item_quantity,
            flat.line_item_rate,
            flat.line_item_item_total,
            flat.line_item_account_name,
            flat.line_item_description,
            flat.line_item_unit,
            flat.line_item_tax_name,
            flat.line_item_tax_percentage,
            CASE 
                WHEN flat.bill_number IS NOT NULL THEN 'json_precedence'
                ELSE 'csv_only' 
            END AS data_source,
            CASE 
                WHEN flat.bill_number IS NOT NULL THEN 1  -- JSON priority
                ELSE 2  -- CSV backup
            END AS source_priority
        FROM csv_bills csv
        LEFT JOIN view_flat_json_bills flat ON csv.bill_number = flat.bill_number
        WHERE COALESCE(flat.bill_number, csv.bill_number) IS NOT NULL
        """
        
        cursor.execute(final_bills_sql)
        
        # Test the view
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_bills")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_bills WHERE data_source = 'json_precedence'")
        json_count = cursor.fetchone()[0]
        
        enhancement_rate = (json_count / total * 100) if total > 0 else 0
        
        print(f"  ✅ FINAL_view_csv_json_bills created:")
        print(f"     Total records: {total:,}")
        print(f"     JSON precedence: {json_count:,} ({enhancement_rate:.1f}%)")
        
    except Exception as e:
        print(f"  ❌ Error creating FINAL_view_csv_json_bills: {e}")
    
    # Create FINAL_view_bills_summary
    print("\n2. Creating FINAL_view_bills_summary...")
    try:
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_bills_summary;")
        
        final_bills_summary_sql = """
        CREATE VIEW FINAL_view_bills_summary AS
        SELECT 
            bill_number,
            vendor_name,
            total,
            balance,
            bill_date,
            account,
            account_code,
            accounts_payable,
            vendor_id,
            due_date,
            currency_code,
            data_source,
            source_priority,
            COUNT(line_item_name) as line_item_count
        FROM FINAL_view_csv_json_bills
        WHERE bill_number IS NOT NULL
        GROUP BY 
            bill_number,
            vendor_name,
            total,
            balance,
            bill_date,
            account,
            account_code,
            accounts_payable,
            vendor_id,
            due_date,
            currency_code,
            data_source,
            source_priority
        HAVING MIN(source_priority) = source_priority
        """
        
        cursor.execute(final_bills_summary_sql)
        
        # Test summary view
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_bills_summary")
        summary_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_bills_summary WHERE data_source = 'json_precedence'")
        summary_json = cursor.fetchone()[0]
        
        # Calculate data reduction ratio
        reduction_ratio = total / summary_total if summary_total > 0 else 0
        
        print(f"  ✅ FINAL_view_bills_summary created:")
        print(f"     Unique bills: {summary_total:,}")
        print(f"     JSON precedence: {summary_json:,}")
        print(f"     Data reduction: {reduction_ratio:.0f}:1 (enhanced:summary)")
        
    except Exception as e:
        print(f"  ❌ Error creating FINAL_view_bills_summary: {e}")
    
    # Create FINAL_view_csv_json_invoices
    print("\n3. Creating FINAL_view_csv_json_invoices...")
    try:
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_invoices;")
        
        final_invoices_sql = """
        CREATE VIEW FINAL_view_csv_json_invoices AS
        SELECT 
            COALESCE(flat.invoice_number, csv.invoice_number) AS invoice_number,
            COALESCE(flat.customer_name, csv.customer_name) AS customer_name,
            COALESCE(flat.total, csv.total) AS total,
            COALESCE(flat.balance, csv.balance) AS balance,
            COALESCE(flat.date, csv.invoice_date) AS invoice_date,
            csv.account,
            csv.account_code,
            flat.customer_id,
            flat.due_date,
            flat.line_item_name,
            flat.line_item_quantity,
            flat.line_item_rate,
            flat.line_item_item_total,
            flat.line_item_account_name,
            flat.line_item_description,
            flat.line_item_unit,
            flat.line_item_tax_name,
            flat.line_item_tax_percentage,
            CASE 
                WHEN flat.invoice_number IS NOT NULL THEN 'json_precedence'
                ELSE 'csv_only' 
            END AS data_source,
            CASE 
                WHEN flat.invoice_number IS NOT NULL THEN 1  -- JSON priority
                ELSE 2  -- CSV backup
            END AS source_priority
        FROM csv_invoices csv
        LEFT JOIN view_flat_json_invoices flat ON csv.invoice_number = flat.invoice_number
        WHERE COALESCE(flat.invoice_number, csv.invoice_number) IS NOT NULL
        """
        
        cursor.execute(final_invoices_sql)
        
        # Test invoices view
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_invoices")
        inv_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_invoices WHERE data_source = 'json_precedence'")
        inv_json = cursor.fetchone()[0]
        
        inv_enhancement_rate = (inv_json / inv_total * 100) if inv_total > 0 else 0
        
        print(f"  ✅ FINAL_view_csv_json_invoices created:")
        print(f"     Total records: {inv_total:,}")
        print(f"     JSON precedence: {inv_json:,} ({inv_enhancement_rate:.1f}%)")
        
    except Exception as e:
        print(f"  ❌ Error creating FINAL_view_csv_json_invoices: {e}")
    
    # Create FINAL_view_invoices_summary
    print("\n4. Creating FINAL_view_invoices_summary...")
    try:
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_invoices_summary;")
        
        final_invoices_summary_sql = """
        CREATE VIEW FINAL_view_invoices_summary AS
        SELECT 
            invoice_number,
            customer_name,
            total,
            balance,
            invoice_date,
            account,
            account_code,
            customer_id,
            due_date,
            data_source,
            source_priority,
            COUNT(line_item_name) as line_item_count
        FROM FINAL_view_csv_json_invoices
        WHERE invoice_number IS NOT NULL
        GROUP BY 
            invoice_number,
            customer_name,
            total,
            balance,
            invoice_date,
            account,
            account_code,
            customer_id,
            due_date,
            data_source,
            source_priority
        HAVING MIN(source_priority) = source_priority
        """
        
        cursor.execute(final_invoices_summary_sql)
        
        # Test invoices summary
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_invoices_summary")
        inv_summary_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FINAL_view_invoices_summary WHERE data_source = 'json_precedence'")
        inv_summary_json = cursor.fetchone()[0]
        
        print(f"  ✅ FINAL_view_invoices_summary created:")
        print(f"     Unique invoices: {inv_summary_total:,}")
        print(f"     JSON precedence: {inv_summary_json:,}")
        
    except Exception as e:
        print(f"  ❌ Error creating FINAL_view_invoices_summary: {e}")
    
    print("\n=== FINAL VIEWS SUMMARY ===")
    print("✅ Production-ready views with FINAL_ prefix:")
    print("   📊 FINAL_view_csv_json_bills - Enhanced view with line items")
    print("   📈 FINAL_view_bills_summary - Deduplicated for reporting")
    print("   📊 FINAL_view_csv_json_invoices - Enhanced invoices with line items")
    print("   📈 FINAL_view_invoices_summary - Deduplicated invoices for reporting")
    print("")
    print("🎯 Benefits of FINAL_ prefix:")
    print("   • Easy identification of production views")
    print("   • Clear distinction from test/intermediate views")
    print("   • Consistent naming convention")
    print("   • Business user friendly naming")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_final_merged_views()
