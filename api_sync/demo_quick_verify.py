#!/usr/bin/env python3
"""
Quick demo of the new Quick Verify Sync Data functionality.

This script demonstrates the consolidated verification function
without going through the full interactive menu.
"""

import sys
import os

# Add api_sync to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_quick_verify():
    """Demo the quick verify sync data functionality."""
    
    print("🚀 QUICK VERIFY SYNC DATA - DEMO")
    print("=" * 60)
    
    try:
        # Import and create wrapper
        from main_api_sync import ApiSyncWrapper
        
        print("🔄 Initializing API Sync Wrapper...")
        wrapper = ApiSyncWrapper()
        
        print("📊 Running Quick Verify Sync Data Analysis...")
        print("-" * 60)
        
        # Execute the quick verify function
        result = wrapper.quick_verify_sync_data()
        
        if result.get('success'):
            report_data = result.get('report', [])
            summary = result.get('summary', {})
            
            if not report_data:
                print("📝 No sync data found")
                print("   This is expected if no sync operations have been performed")
                return
            
            print("✅ Sync data analysis completed")
            print("\n📊 SYNC DATA ANALYSIS REPORT")
            print("=" * 120)
            print(f"{'Module Name':<25} {'Data Source':<15} {'Records':<10} {'Earliest Date':<15} {'Latest Date':<15} {'Last Sync':<20}")
            print("-" * 120)
            
            # Separate regular modules from line items
            regular_modules = []
            line_item_modules = []
            
            for item in report_data:
                if item['module_name'].endswith('_line_items'):
                    line_item_modules.append(item)
                else:
                    regular_modules.append(item)
            
            # Display regular modules first
            if regular_modules:
                print("📋 MAIN MODULES:")
                for item in sorted(regular_modules, key=lambda x: x['module_name']):
                    module_display = item['module_name'].replace('_', ' ').title()
                    data_source = item.get('data_source', 'Unknown')[:14]
                    record_count = item.get('record_count', 0)
                    earliest = item.get('earliest_date', 'No dates')[:14]
                    latest = item.get('latest_date', 'No dates')[:14]
                    last_sync = item.get('last_sync', 'Unknown')[:19]
                    
                    print(f"{module_display:<25} {data_source:<15} {record_count:<10} {earliest:<15} {latest:<15} {last_sync:<20}")
            
            # Display line item modules
            if line_item_modules:
                print("\n📝 LINE ITEM MODULES:")
                for item in sorted(line_item_modules, key=lambda x: x['module_name']):
                    module_display = item['module_name'].replace('_line_items', '').replace('_', ' ').title() + " (Line Items)"
                    data_source = item.get('data_source', 'Unknown')[:14]
                    record_count = item.get('record_count', 0)
                    earliest = item.get('earliest_date', 'No dates')[:14]
                    latest = item.get('latest_date', 'No dates')[:14]
                    last_sync = item.get('last_sync', 'Unknown')[:19]
                    
                    print(f"{module_display:<25} {data_source:<15} {record_count:<10} {earliest:<15} {latest:<15} {last_sync:<20}")
            
            # Display summary
            print("\n📈 SUMMARY:")
            print("-" * 50)
            print(f"Total Records: {summary.get('total_records', 0):,}")
            print(f"Unique Modules: {summary.get('unique_modules', 0)}")
            print(f"Regular Modules: {summary.get('regular_modules_count', 0)}")
            print(f"Line Item Modules: {summary.get('line_item_modules_count', 0)}")
            print(f"Last Sync: {summary.get('last_sync', 'Unknown')}")
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"⚠️  Analysis result: {error}")
            if error == "No sync data found":
                print("📝 This is expected if no sync operations have been performed")
        
        print("\n✅ Quick Verify Demo completed")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_quick_verify()
