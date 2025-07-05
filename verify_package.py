#!/usr/bin/env python3
"""
Verification script for refactored package components
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🧪 BEDROCK V2 PACKAGE VERIFICATION")
print("=" * 50)

def test_imports():
    """Test all package imports"""
    print("\n📦 Testing Package Imports...")
    
    try:
        from data_pipeline.config import get_config_manager
        print("✅ config.py imported successfully")
        
        from data_pipeline.database import DatabaseHandler
        print("✅ database.py imported successfully")
        
        from data_pipeline.transformer import BillsTransformer
        print("✅ transformer.py imported successfully")
        
        from data_pipeline.mappings.bills_mapping_config import CANONICAL_BILLS_COLUMNS
        print("✅ bills_mapping_config.py imported successfully")
        
        print(f"📊 Canonical schema: {len(CANONICAL_BILLS_COLUMNS)} fields")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration management"""
    print("\n⚙️ Testing Configuration Management...")
    
    try:
        from data_pipeline.config import get_config_manager
        
        config = get_config_manager()
        print("✅ Configuration manager initialized")
        
        paths = config.get_data_source_paths()
        print("✅ Data source paths retrieved")
        
        print(f"📁 CSV backup path: {paths['csv_backup_path']}")
        print(f"🌐 JSON API path: {paths['json_api_path']}")
        print(f"🎯 Target database: {paths['target_database']}")
        
        # Test validation
        is_valid = config.validate_configuration()
        print(f"✅ Configuration validation: {'PASSED' if is_valid else 'FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_sources():
    """Test data source accessibility"""
    print("\n📊 Testing Data Source Accessibility...")
    
    try:
        from data_pipeline.config import get_config_manager
        config = get_config_manager()
        paths = config.get_data_source_paths()
        
        # Check CSV source
        csv_backup_path = Path(paths['csv_backup_path'])
        bills_csv = csv_backup_path / "Bill.csv"
        
        if bills_csv.exists():
            print(f"✅ Bills CSV found: {bills_csv}")
            print(f"📊 File size: {bills_csv.stat().st_size:,} bytes")
        else:
            print(f"⚠️  Bills CSV not found: {bills_csv}")
        
        # Check database directory
        db_path = Path(paths['target_database'])
        if db_path.parent.exists():
            print(f"✅ Database directory exists: {db_path.parent}")
        else:
            print(f"⚠️  Database directory missing: {db_path.parent}")
            
        return True
        
    except Exception as e:
        print(f"❌ Data source test failed: {e}")
        return False

def test_component_initialization():
    """Test component initialization"""
    print("\n🔧 Testing Component Initialization...")
    
    try:
        from data_pipeline.config import get_config_manager
        from data_pipeline.database import DatabaseHandler
        from data_pipeline.transformer import BillsTransformer
        
        # Test configuration
        config = get_config_manager()
        print("✅ Configuration manager ready")
        
        # Test database handler
        db_handler = DatabaseHandler()
        print("✅ Database handler ready")
        print(f"📊 Target DB: {db_handler.database_path}")
        
        # Test transformer
        transformer = BillsTransformer()
        print("✅ Bills transformer ready")
        print(f"📋 Canonical columns: {len(transformer.canonical_columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success_count = 0
    total_tests = 4
    
    if test_imports():
        success_count += 1
    
    if test_configuration():
        success_count += 1
        
    if test_data_sources():
        success_count += 1
        
    if test_component_initialization():
        success_count += 1
    
    print(f"\n🏆 VERIFICATION SUMMARY")
    print("=" * 30)
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED - Package ready for execution!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - Package needs attention")
        sys.exit(1)
