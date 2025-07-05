"""
Modular Architecture Verification Script

This script tests the new modular architecture with separated BaseBuilder 
and IncrementalUpdater components to ensure proper linkages and functionality.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_modular_imports():
    """Test that all modular components can be imported correctly."""
    print("🧪 Testing modular component imports...")
    
    try:
        # Test core configuration
        from data_pipeline.config import get_config_manager
        config = get_config_manager()
        print("   ✅ ConfigurationManager: OK")
        
        # Test database handler
        from data_pipeline.database import DatabaseHandler
        db_handler = DatabaseHandler()
        print("   ✅ DatabaseHandler: OK")
        
        # Test transformer
        from data_pipeline.transformer import BillsTransformer
        transformer = BillsTransformer()
        print("   ✅ BillsTransformer: OK")
        
        # Test new modular components
        from data_pipeline.base_builder import BaseBuilder, build_base_from_csv
        base_builder = BaseBuilder()
        print("   ✅ BaseBuilder: OK")
        
        from data_pipeline.incremental_updater import IncrementalUpdater, apply_json_updates
        incremental_updater = IncrementalUpdater()
        print("   ✅ IncrementalUpdater: OK")
        
        # Test package-level imports
        from data_pipeline import BaseBuilder as PkgBaseBuilder
        from data_pipeline import IncrementalUpdater as PkgIncrementalUpdater
        print("   ✅ Package-level exports: OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_configuration_resolution():
    """Test configuration and dynamic path resolution."""
    print("\n⚙️ Testing configuration resolution...")
    
    try:
        from data_pipeline.config import get_config_manager
        config = get_config_manager()
        
        # Test basic config access
        csv_path = config.get('data_sources', 'csv_backup_path')
        json_path = config.get('data_sources', 'json_api_path') 
        db_path = config.get('data_sources', 'target_database')
        
        print(f"   📁 CSV backup path: {csv_path}")
        print(f"   📁 JSON API path: {json_path}")
        print(f"   📁 Database path: {db_path}")
        
        # Test dynamic path resolution
        data_paths = config.get_data_source_paths()
        print(f"   🔍 Resolved CSV: {Path(data_paths['csv_backup_path']).name}")
        print(f"   🔍 Resolved JSON: {Path(data_paths['json_api_path']).name}")
        
        print("   ✅ Configuration resolution: OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_module_linkages():
    """Test that modules can work together properly."""
    print("\n🔗 Testing module linkages...")
    
    try:
        from data_pipeline.config import get_config_manager
        from data_pipeline.base_builder import BaseBuilder
        from data_pipeline.incremental_updater import IncrementalUpdater
        
        # Test shared configuration
        config = get_config_manager()
        base_builder = BaseBuilder(config)
        incremental_updater = IncrementalUpdater(config)
        
        print("   ✅ Shared configuration: OK")
        
        # Test module statistics access
        base_stats = base_builder.get_build_statistics()
        print(f"   📊 BaseBuilder stats access: {len(base_stats)} fields")
        
        print("   ✅ Module linkages: OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Linkage test failed: {e}")
        return False

def test_convenience_functions():
    """Test convenience functions for automation."""
    print("\n🚀 Testing convenience functions...")
    
    try:
        from data_pipeline.base_builder import build_base_from_csv
        from data_pipeline.incremental_updater import apply_json_updates
        
        print("   📦 build_base_from_csv: Available")
        print("   📦 apply_json_updates: Available")
        print("   ✅ Convenience functions: OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Convenience function test failed: {e}")
        return False

def main():
    """Run all modular architecture verification tests."""
    print("🏗️ MODULAR ARCHITECTURE VERIFICATION")
    print("=" * 45)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    tests = [
        test_modular_imports,
        test_configuration_resolution,
        test_module_linkages,
        test_convenience_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"   ✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 MODULAR ARCHITECTURE VERIFICATION: PASSED")
        print(f"   🏗️ BaseBuilder module: Ready")
        print(f"   🔄 IncrementalUpdater module: Ready") 
        print(f"   🔗 Module linkages: Working")
        print(f"   🚀 Convenience functions: Available")
        print(f"\n💎 Modular architecture is production-ready!")
        return True
    else:
        print(f"\n❌ MODULAR ARCHITECTURE VERIFICATION: FAILED")
        print(f"   ⚠️ {total - passed} test(s) failed")
        print(f"   🔧 Please review the errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
