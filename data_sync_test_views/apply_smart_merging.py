#!/usr/bin/env python3
"""
Apply Smart Merging Views
Applies the smart merging views to fix CSV-only data loss issues.
Includes safety checks and rollback capabilities.
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any
from config import get_database_path


class SmartMergingApplicator:
    """Applies smart merging views with safety features"""
    
    def __init__(self):
        self.db_path = get_database_path()
        self.backup_file = f"view_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        self.views_to_update = [
            "FINAL_view_csv_json_contacts",
            "FINAL_view_csv_json_customer_payments", 
            "FINAL_view_csv_json_items",
            "FINAL_view_csv_json_sales_orders",
            "FINAL_view_csv_json_vendor_payments"
        ]
        
    def create_backup(self) -> bool:
        """Create backup of original views"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            backup_content = []
            backup_content.append("-- View Backup Created: " + datetime.now().isoformat())
            backup_content.append("-- Original CSV-only views before smart merging conversion")
            backup_content.append("")
            
            for view_name in self.views_to_update:
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='view' AND name = ?
                """, (view_name,))
                
                result = cursor.fetchone()
                if result:
                    backup_content.append(f"-- {view_name}")
                    backup_content.append(f"DROP VIEW IF EXISTS {view_name};")
                    backup_content.append(f"{result[0]};")
                    backup_content.append("")
            
            conn.close()
            
            with open(self.backup_file, 'w') as f:
                f.write('\n'.join(backup_content))
            
            print(f"✅ Backup created: {self.backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def load_smart_views(self) -> Dict[str, str]:
        """Load smart merging views from SQL file"""
        try:
            with open("smart_merging_views.sql", 'r') as f:
                content = f.read()
            
            views = {}
            
            for view_name in self.views_to_update:
                # Find the CREATE VIEW statement for this view
                start_marker = f"CREATE VIEW {view_name} AS"
                start_idx = content.find(start_marker)
                
                if start_idx == -1:
                    print(f"⚠️  Warning: Could not find SQL for {view_name}")
                    continue
                
                # Find the end of this view (next view or end of file)
                next_view_start = float('inf')
                for other_view in self.views_to_update:
                    if other_view != view_name:
                        other_start = content.find(f"CREATE VIEW {other_view} AS", start_idx + 1)
                        if other_start != -1 and other_start < next_view_start:
                            next_view_start = other_start
                
                if next_view_start == float('inf'):
                    # This is the last view
                    view_sql = content[start_idx:].rstrip()
                else:
                    # Find the previous section end
                    end_section = content.rfind("-- =============", start_idx, next_view_start)
                    view_sql = content[start_idx:end_section].rstrip()
                
                # Clean up the SQL
                view_sql = view_sql.rstrip(';').strip()
                views[view_name] = view_sql
            
            print(f"✅ Loaded {len(views)} smart views")
            return views
            
        except Exception as e:
            print(f"❌ Failed to load smart views: {e}")
            return {}
    
    def apply_view(self, view_name: str, sql: str) -> bool:
        """Apply a single smart view"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Drop existing view
            cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
            
            # Create new view
            cursor.execute(sql)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply {view_name}: {e}")
            return False
    
    def test_view(self, view_name: str) -> Dict[str, Any]:
        """Test a view after application"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute(f"SELECT COUNT(*) FROM `{view_name}`")
            total_count = cursor.fetchone()[0]
            
            # Test data source distribution
            cursor.execute(f"""
                SELECT data_source, COUNT(*) 
                FROM `{view_name}` 
                GROUP BY data_source
            """)
            source_dist = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "success": True,
                "total_count": total_count,
                "source_distribution": source_dist
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def apply_all_views(self, confirm: bool = False) -> Dict[str, Any]:
        """Apply all smart merging views"""
        if not confirm:
            print("⚠️  This will modify the production database views!")
            print("🔄 Use apply_all_views(confirm=True) to proceed")
            return {"cancelled": True}
        
        results = {
            "backup_created": False,
            "views_applied": [],
            "views_failed": [],
            "tests_passed": [],
            "tests_failed": []
        }
        
        print("=" * 80)
        print("APPLYING SMART MERGING VIEWS")
        print("=" * 80)
        
        # Step 1: Create backup
        print("\n📋 Step 1: Creating backup...")
        if not self.create_backup():
            return {"error": "Backup failed - aborting"}
        results["backup_created"] = True
        
        # Step 2: Load smart views
        print("\n📥 Step 2: Loading smart views...")
        smart_views = self.load_smart_views()
        if not smart_views:
            return {"error": "No smart views loaded - aborting"}
        
        # Step 3: Apply views
        print("\n🔄 Step 3: Applying views...")
        for view_name, sql in smart_views.items():
            print(f"   Applying {view_name}...")
            if self.apply_view(view_name, sql):
                results["views_applied"].append(view_name)
                print(f"   ✅ {view_name} applied successfully")
            else:
                results["views_failed"].append(view_name)
                print(f"   ❌ {view_name} failed")
        
        # Step 4: Test views
        print("\n🧪 Step 4: Testing views...")
        for view_name in results["views_applied"]:
            print(f"   Testing {view_name}...")
            test_result = self.test_view(view_name)
            if test_result["success"]:
                results["tests_passed"].append({
                    "view": view_name,
                    "count": test_result["total_count"],
                    "sources": test_result["source_distribution"]
                })
                source_info = test_result["source_distribution"]
                print(f"   ✅ {view_name}: {test_result['total_count']:,} records {source_info}")
            else:
                results["tests_failed"].append({
                    "view": view_name,
                    "error": test_result["error"]
                })
                print(f"   ❌ {view_name}: {test_result['error']}")
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print application summary"""
        print("\n" + "=" * 80)
        print("APPLICATION SUMMARY")
        print("=" * 80)
        
        if results.get("cancelled"):
            print("❌ Operation cancelled by user")
            return
        
        if "error" in results:
            print(f"❌ Operation failed: {results['error']}")
            return
        
        print(f"📋 Backup: {'✅ Created' if results['backup_created'] else '❌ Failed'}")
        print(f"🔄 Views Applied: {len(results['views_applied'])}/{len(self.views_to_update)}")
        print(f"🧪 Tests Passed: {len(results['tests_passed'])}")
        print(f"❌ Failures: {len(results['views_failed']) + len(results['tests_failed'])}")
        
        if results["tests_passed"]:
            print(f"\n✅ Successfully Updated Views:")
            for test in results["tests_passed"]:
                view = test["view"]
                count = test["count"]
                sources = test["sources"]
                json_count = sources.get("JSON", 0)
                csv_count = sources.get("CSV", 0)
                print(f"   📊 {view}: {count:,} total ({json_count:,} JSON + {csv_count:,} CSV)")
        
        if results["views_failed"] or results["tests_failed"]:
            print(f"\n❌ Issues:")
            for view in results["views_failed"]:
                print(f"   🔧 {view}: Application failed")
            for test in results["tests_failed"]:
                print(f"   🧪 {test['view']}: Test failed - {test['error']}")
        
        print(f"\n💾 Backup file: {self.backup_file}")
        print(f"🔄 To rollback: Run SQL from backup file")


def main():
    """Main application function"""
    applicator = SmartMergingApplicator()
    
    print("=" * 80)
    print("SMART MERGING VIEW APPLICATOR")
    print("=" * 80)
    print("\nThis will update 5 FINAL views to use smart merging:")
    for view in applicator.views_to_update:
        print(f"  📋 {view}")
    
    print(f"\n🎯 Expected Improvements:")
    print(f"   📊 contacts: +14 records (6.2% more data)")
    print(f"   💳 customer_payments: +84 records (4.8% more data)")
    print(f"   📦 items: +1,114 records (120.0% more data) ⭐")
    print(f"   📋 sales_orders: +387 records (6.7% more data)")
    print(f"   💰 vendor_payments: +13 records (2.5% more data)")
    print(f"   🔢 Total: +1,612 additional records visible")
    
    print(f"\n⚠️  This will modify the production database!")
    response = input("\nProceed with applying smart merging views? (yes/no): ").lower()
    
    if response in ['yes', 'y']:
        results = applicator.apply_all_views(confirm=True)
        applicator.print_summary(results)
    else:
        print("❌ Operation cancelled")


if __name__ == "__main__":
    main()
