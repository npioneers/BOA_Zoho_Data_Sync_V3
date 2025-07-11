#!/usr/bin/env python3
"""
Example: Using Enhanced API Sync with Session Folders

This script demonstrates how to use the new session folder functionality
in the API Sync package for organized data management.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from main_api_sync import ApiSyncWrapper

def example_single_module_sync():
    """Example: Sync a single module with session organization."""
    print("📋 Example: Single Module Sync with Session Folder")
    print("=" * 55)
    
    try:
        # Create wrapper instance
        wrapper = ApiSyncWrapper()
        
        # Check system status first
        status = wrapper.get_status()
        if not status.get("credentials", False):
            print("⚠️  Warning: No valid credentials found")
            print("   This example will show the session folder structure without actual API calls")
            return
        
        print("📤 Syncing 'contacts' module...")
        
        # Sync with session folder (default behavior)
        result = wrapper.fetch_data('contacts', full_sync=False)
        
        if result.get("success", False):
            print("✅ Sync completed successfully!")
            print(f"📊 Records fetched: {result.get('record_count', 0)}")
            
            # Show session information
            if "sync_session" in result:
                session = result["sync_session"]
                print(f"📁 Session folder: {session['session_folder']}")
                print(f"🕐 Session timestamp: {session['session_timestamp']}")
                print(f"💾 JSON output: {session['json_output_dir']}")
        else:
            print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Example failed: {e}")

def example_all_modules_sync():
    """Example: Sync all modules with session organization."""
    print("\n📋 Example: All Modules Sync with Session Folder")
    print("=" * 55)
    
    try:
        wrapper = ApiSyncWrapper()
        
        print("📤 Syncing all configured modules...")
        print("   (This will create a comprehensive session folder)")
        
        # Sync all modules with session folder
        result = wrapper.fetch_all_modules(full_sync=False)
        
        if result.get("success", False):
            print("✅ Multi-module sync completed!")
            
            # Show summary of what was synced
            if "modules" in result:
                modules_data = result["modules"]
                successful = sum(1 for m in modules_data.values() if m.get("success", False))
                total = len(modules_data)
                print(f"📊 Modules: {successful}/{total} successful")
                
                # Show per-module results
                for module, module_result in modules_data.items():
                    if module_result.get("success", False):
                        count = module_result.get("record_count", 0)
                        print(f"   ✅ {module}: {count} records")
                    else:
                        print(f"   ❌ {module}: {module_result.get('error', 'Failed')}")
            
            # Show session information
            if "sync_session" in result:
                session = result["sync_session"]
                print(f"📁 Session folder: {session['session_folder']}")
        else:
            print(f"❌ Multi-module sync failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Example failed: {e}")

def example_session_management():
    """Example: Managing and listing sync sessions."""
    print("\n📋 Example: Session Management")
    print("=" * 40)
    
    try:
        wrapper = ApiSyncWrapper()
        
        # List all available sessions
        sessions = wrapper.list_sync_sessions()
        
        print(f"📂 Found {len(sessions)} sync sessions:")
        
        if not sessions:
            print("   No sessions found. Run a sync operation first.")
            return
        
        # Show latest 3 sessions
        for i, session in enumerate(sessions[:3], 1):
            print(f"\n{i}. 🕐 {session.get('session_timestamp', 'Unknown')}")
            print(f"   📁 {session.get('session_folder', 'Unknown')}")
            print(f"   ✅ Completed: {session.get('completed', False)}")
            
            # Show summary if available
            if 'summary' in session:
                summary = session['summary']
                total_modules = summary.get('total_modules', 0)
                successful_modules = summary.get('successful_modules', 0)
                total_records = summary.get('total_records', 0)
                
                print(f"   📊 Modules: {successful_modules}/{total_modules}")
                print(f"   📈 Records: {total_records}")
            
            # Show folder contents
            folder_path = Path(session.get('session_folder', ''))
            if folder_path.exists():
                subdirs = [d.name for d in folder_path.iterdir() if d.is_dir()]
                files = [f.name for f in folder_path.iterdir() if f.is_file()]
                print(f"   📂 Subdirs: {', '.join(subdirs)}")
                print(f"   📄 Files: {', '.join(files)}")
        
        if len(sessions) > 3:
            print(f"\n... and {len(sessions) - 3} more sessions")
            
    except Exception as e:
        print(f"❌ Example failed: {e}")

def example_comparison_old_vs_new():
    """Example: Comparing old vs new sync approaches."""
    print("\n📋 Example: Old vs New Sync Approaches")
    print("=" * 50)
    
    try:
        wrapper = ApiSyncWrapper()
        
        print("🔄 Traditional approach (files go to data/raw_json/):")
        print("   result = wrapper.fetch_data('contacts', use_session_folder=False)")
        print("   # Creates: data/raw_json/TIMESTAMP/contacts.json")
        
        print("\n🆕 Enhanced approach (organized in session folders):")
        print("   result = wrapper.fetch_data('contacts', use_session_folder=True)")
        print("   # Creates: data/sync_sessions/sync_session_TIMESTAMP/")
        print("   #           ├── raw_json/TIMESTAMP/contacts.json")
        print("   #           ├── session_info.json")
        print("   #           ├── README.md")
        print("   #           ├── logs/")
        print("   #           └── reports/session_summary.json")
        
        print("\n💡 Benefits of session folders:")
        print("   • Better organization and traceability")
        print("   • Comprehensive documentation per sync")
        print("   • Easier cleanup and archival")
        print("   • Isolated logs and reports")
        print("   • Session-level summary statistics")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")

if __name__ == "__main__":
    print("🚀 API Sync Session Folder Examples")
    print("=" * 60)
    print("These examples demonstrate the new session folder functionality")
    print("for better organization of sync operations.\n")
    
    # Run examples
    example_single_module_sync()
    example_all_modules_sync()
    example_session_management()
    example_comparison_old_vs_new()
    
    print("\n" + "=" * 60)
    print("📚 For more information, see:")
    print("   • api_sync/README.md - Complete documentation")
    print("   • test_session_folders.py - Testing functionality")
    print("   • main_api_sync.py - Enhanced wrapper implementation")
    print("\n✨ Session folders are now the default for better data organization!")
