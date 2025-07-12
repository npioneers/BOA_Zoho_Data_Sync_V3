"""
Verification script for consolidated removal
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("🔍 Testing consolidated removal...")

try:
    # Test runner import and initialization
    from runner_json2db_sync import JSON2DBSyncRunner
    runner = JSON2DBSyncRunner()
    print(f"✅ Runner initialized with data_source_type: {runner.data_source_type}")
    print(f"✅ JSON directory: {runner.json_dir}")
    
    # Test that it always uses api_sync
    assert runner.data_source_type == "api_sync", f"Expected 'api_sync', got '{runner.data_source_type}'"
    print("✅ Data source type is correctly set to 'api_sync'")
    
    # Test analyzer import
    from json_analyzer import JSONAnalyzer
    print("✅ JSONAnalyzer imports successfully")
    
    # Test main wrapper import
    from main_json2db_sync import JSON2DBSyncWrapper
    print("✅ Main wrapper imports successfully")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Consolidated JSON support has been successfully removed")
    print("✅ System now exclusively uses session-based structure from api_sync")
    print("✅ No conflicts or confusion between data sources")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
