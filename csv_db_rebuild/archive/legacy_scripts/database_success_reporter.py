"""
Database Population Success Rate Reporter
Generates detailed success rate reports for populated databases
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Table mappings for CSV to database comparison
TABLE_MAPPINGS = {
    "csv_invoices": {"csv_file": "Invoice.csv"},
    "csv_items": {"csv_file": "Item.csv"},
    "csv_contacts": {"csv_file": "Contacts.csv"},
    "csv_bills": {"csv_file": "Bill.csv"},
    "csv_customer_payments": {"csv_file": "Customer_Payment.csv"},
    "csv_vendor_payments": {"csv_file": "Vendor_Payment.csv"},
    "csv_sales_orders": {"csv_file": "Sales_Order.csv"},
    "csv_purchase_orders": {"csv_file": "Purchase_Order.csv"},
    "csv_credit_notes": {"csv_file": "Credit_Note.csv"},
    "csv_organizations": {"csv_file": "Contacts.csv"}  # Organizations come from Contacts
}

class DatabaseSuccessReporter:
    """Generate success rate reports for populated databases"""
    
    def __init__(self, db_path: str = "data/database/production.db", 
                 csv_dir: str = "data/csv/Nangsel Pioneers_Latest"):
        self.db_path = Path(db_path)
        self.csv_dir = Path(csv_dir)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for reports"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"database_success_report_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Success rate report logging to: {log_file}")

    def get_table_record_count(self, table_name: str) -> int:
        """Get record count from database table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            self.logger.error(f"Error getting count for {table_name}: {e}")
            return 0

    def get_csv_record_count(self, csv_file: str) -> int:
        """Get record count from CSV file"""
        try:
            csv_path = self.csv_dir / csv_file
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                return len(df)
            else:
                self.logger.warning(f"CSV file not found: {csv_path}")
                return 0
        except Exception as e:
            self.logger.error(f"Error reading CSV {csv_file}: {e}")
            return 0

    def generate_success_report(self) -> dict:
        """Generate comprehensive success rate report"""
        start_time = datetime.now()
        self.logger.info("="*80)
        self.logger.info("📊 DATABASE POPULATION SUCCESS RATE REPORT")
        self.logger.info("="*80)
        self.logger.info(f"🕒 Report Generated: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"🗃️  Database: {self.db_path}")
        self.logger.info(f"📁 CSV Source: {self.csv_dir}")
        
        results = {}
        total_csv_records = 0
        total_db_records = 0
        successful_tables = 0
        
        # Check if database exists
        if not self.db_path.exists():
            self.logger.error(f"❌ Database not found: {self.db_path}")
            return {"error": "Database not found"}
        
        # Analyze each table
        for table_name, config in TABLE_MAPPINGS.items():
            csv_file = config["csv_file"]
            
            # Get record counts
            csv_count = self.get_csv_record_count(csv_file)
            db_count = self.get_table_record_count(table_name)
            
            # Calculate success rate
            success_rate = (db_count / csv_count * 100) if csv_count > 0 else 0
            is_success = db_count > 0 and csv_count > 0
            
            results[table_name] = {
                "csv_file": csv_file,
                "csv_records": csv_count,
                "db_records": db_count,
                "success_rate": success_rate,
                "status": "SUCCESS" if is_success else "FAILED"
            }
            
            total_csv_records += csv_count
            total_db_records += db_count
            if is_success:
                successful_tables += 1
        
        # Calculate overall metrics
        overall_success_rate = (total_db_records / total_csv_records * 100) if total_csv_records > 0 else 0
        table_success_rate = (successful_tables / len(TABLE_MAPPINGS) * 100)
        
        # Generate detailed table report
        self.logger.info("="*80)
        self.logger.info("📋 DETAILED SUCCESS RATE TABLE")
        self.logger.info("="*80)
        self.logger.info(f"{'Table Name':<20} | {'CSV File':<20} | {'CSV':<8} | {'DB':<8} | {'Rate':<8} | {'Status':<8}")
        self.logger.info("-" * 80)
        
        for table_name, data in results.items():
            status_icon = "✅" if data["status"] == "SUCCESS" else "❌"
            self.logger.info(
                f"{table_name:<20} | {data['csv_file']:<20} | "
                f"{data['csv_records']:>8,} | {data['db_records']:>8,} | "
                f"{data['success_rate']:>7.1f}% | {status_icon} {data['status']:<6}"
            )
        
        self.logger.info("-" * 80)
        self.logger.info(
            f"{'TOTALS':<20} | {'All Files':<20} | "
            f"{total_csv_records:>8,} | {total_db_records:>8,} | "
            f"{overall_success_rate:>7.1f}% | {'✅ PASS' if overall_success_rate > 95 else '⚠️  WARN':<8}"
        )
        
        # Generate summary
        self.logger.info("="*80)
        self.logger.info("📊 SUMMARY STATISTICS")
        self.logger.info("="*80)
        self.logger.info(f"🎯 Overall Success Rate: {overall_success_rate:.1f}% ({total_db_records:,}/{total_csv_records:,} records)")
        self.logger.info(f"📋 Table Success Rate: {table_success_rate:.1f}% ({successful_tables}/{len(TABLE_MAPPINGS)} tables)")
        
        # Database size
        try:
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024)
            self.logger.info(f"💾 Database Size: {db_size_mb:.1f} MB")
        except:
            self.logger.info("💾 Database Size: Unable to determine")
        
        # Performance assessment
        if overall_success_rate >= 99:
            performance = "🟢 EXCELLENT"
        elif overall_success_rate >= 95:
            performance = "🟡 GOOD"
        elif overall_success_rate >= 85:
            performance = "🟠 FAIR"
        else:
            performance = "🔴 POOR"
        
        self.logger.info(f"📈 Performance Rating: {performance}")
        
        end_time = datetime.now()
        self.logger.info(f"⏱️  Report Generation Time: {(end_time - start_time).total_seconds():.2f} seconds")
        self.logger.info("="*80)
        
        # Return structured data
        summary = {
            "timestamp": start_time.isoformat(),
            "database_path": str(self.db_path),
            "csv_source": str(self.csv_dir),
            "overall_success_rate": overall_success_rate,
            "table_success_rate": table_success_rate,
            "total_csv_records": total_csv_records,
            "total_db_records": total_db_records,
            "successful_tables": successful_tables,
            "total_tables": len(TABLE_MAPPINGS),
            "performance_rating": performance,
            "table_results": results
        }
        
        return summary

def main():
    """Main function to run the success rate report"""
    reporter = DatabaseSuccessReporter()
    result = reporter.generate_success_report()
    
    if "error" in result:
        print(f"❌ Report generation failed: {result['error']}")
        return False
    
    print(f"✅ Success rate report completed successfully!")
    print(f"📊 Overall Success Rate: {result['overall_success_rate']:.1f}%")
    print(f"📋 Tables Successful: {result['successful_tables']}/{result['total_tables']}")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
