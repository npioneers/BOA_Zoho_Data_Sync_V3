"""
Simple Stats Reporter
Compares CSV vs Database record counts
"""
import pandas as pd
import logging
from pathlib import Path
from .simple_table_manager import SimpleTableManager

# Simple table mappings
TABLE_MAPPINGS = {
    "csv_invoices": {"csv_file": "Invoice.csv"},
    "csv_items": {"csv_file": "Item.csv"},
    "csv_contacts": {"csv_file": "Contacts.csv"},
    "csv_bills": {"csv_file": "Bill.csv"},
    "csv_customer_payments": {"csv_file": "Customer_Payment.csv"},
    "csv_vendor_payments": {"csv_file": "Vendor_Payment.csv"},
    "csv_sales_orders": {"csv_file": "Sales_Order.csv"},
    "csv_purchase_orders": {"csv_file": "Purchase_Order.csv"},
    "csv_credit_notes": {"csv_file": "Credit_Note.csv"}
}


class SimpleStatsReporter:
    """Simple CSV vs Database stats reporter"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 csv_dir: str = "data/csv/Nangsel Pioneers_Latest"):
        self.db_path = Path(db_path)
        self.csv_dir = Path(csv_dir)
        self.table_manager = SimpleTableManager(db_path)
        self.logger = logging.getLogger(__name__)

    def get_csv_count(self, csv_file: str) -> int:
        """Get record count from CSV file"""
        csv_path = self.csv_dir / csv_file
        
        if not csv_path.exists():
            self.logger.warning(f"CSV file not found: {csv_path}")
            return -1
        
        try:
            df = pd.read_csv(csv_path)
            return len(df)
        except Exception as e:
            self.logger.error(f"Error reading {csv_file}: {str(e)}")
            return -1

    def generate_comparison_report(self) -> dict:
        """Generate CSV vs DB comparison report"""
        self.logger.info("Generating CSV vs Database comparison report")
        
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "tables": {},
            "summary": {}
        }
        
        total_csv = 0
        total_db = 0
        
        for table_name, mapping in TABLE_MAPPINGS.items():
            csv_file = mapping["csv_file"]
            
            csv_count = self.get_csv_count(csv_file)
            db_count = self.table_manager.get_table_count(table_name)
            
            difference = db_count - csv_count if csv_count >= 0 and db_count >= 0 else None
            success_rate = (db_count / csv_count * 100) if csv_count > 0 else 0
            
            table_stats = {
                "csv_file": csv_file,
                "csv_count": csv_count,
                "db_count": db_count,
                "difference": difference,
                "success_rate": round(success_rate, 2)
            }
            
            report["tables"][table_name] = table_stats
            
            if csv_count >= 0:
                total_csv += csv_count
            if db_count >= 0:
                total_db += db_count
        
        # Summary
        report["summary"] = {
            "total_csv_records": total_csv,
            "total_db_records": total_db,
            "overall_success_rate": round((total_db / total_csv * 100) if total_csv > 0 else 0, 2)
        }
        
        return report

    def print_comparison_report(self):
        """Print formatted comparison report"""
        report = self.generate_comparison_report()
        
        print("\n" + "="*80)
        print("CSV vs DATABASE COMPARISON REPORT")
        print("="*80)
        
        print(f"{'Table':<20} {'CSV':<8} {'DB':<8} {'Diff':<8} {'Success %':<10}")
        print("-" * 60)
        
        for table_name, stats in report["tables"].items():
            csv_count = stats["csv_count"] if stats["csv_count"] >= 0 else "N/A"
            db_count = stats["db_count"] if stats["db_count"] >= 0 else "N/A"
            diff = stats["difference"] if stats["difference"] is not None else "N/A"
            success = f"{stats['success_rate']}%" if stats["success_rate"] > 0 else "0%"
            
            print(f"{table_name:<20} {csv_count:<8} {db_count:<8} {diff:<8} {success:<10}")
        
        print("-" * 60)
        print(f"{'TOTAL':<20} {report['summary']['total_csv_records']:<8} "
              f"{report['summary']['total_db_records']:<8} "
              f"{report['summary']['total_db_records'] - report['summary']['total_csv_records']:<8} "
              f"{report['summary']['overall_success_rate']}%")
        print("="*80)
        
        return report
