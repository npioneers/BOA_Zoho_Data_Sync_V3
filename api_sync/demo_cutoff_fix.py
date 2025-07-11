#!/usr/bin/env python3
"""
Quick demo to show that the cutoff date logic is now fixed.
This will simulate the menu choice without user interaction.
"""

import sys
import os
from pathlib import Path

# Add api_sync to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_fixed_logic():
    """Demo the fixed cutoff date logic."""
    
    print("🚀 CUTOFF DATE LOGIC FIX - DEMO")
    print("=" * 50)
    
    try:
        from main_api_sync import ApiSyncWrapper, perform_pre_sync_check
        
        print("🔄 Creating wrapper...")
        wrapper = ApiSyncWrapper()
        
        if wrapper.runner:
            print("✅ Wrapper initialized with credentials")
        else:
            print("⚠️  Wrapper initialized without credentials")
        
        print("\n📊 Simulating menu choice: Fetch all modules...")
        print("🔍 This should NOT prompt for cutoff date because we have existing data")
        
        # Test the pre-sync check (this is what gets called in the menu)
        print("\n" + "="*50)
        cutoff_timestamp = perform_pre_sync_check(wrapper, modules_to_fetch=None)
        print("="*50)
        
        if cutoff_timestamp is None:
            print("\n🎉 SUCCESS! No cutoff date prompted")
            print("✅ System correctly detected existing data")
            print("✅ Will proceed with normal incremental sync")
            print("✅ This is the expected behavior with existing data")
        else:
            print(f"\n⚠️  Cutoff timestamp was returned: {cutoff_timestamp}")
            print("   This suggests first-time sync or user provided cutoff")
        
        print(f"\n📁 Data availability check:")
        data_path = Path("data/raw_json")
        session_path = Path("data/sync_sessions")
        
        if data_path.exists():
            timestamp_dirs = [d for d in data_path.iterdir() if d.is_dir()]
            print(f"  Traditional data: ✅ {len(timestamp_dirs)} timestamp directories")
        else:
            print(f"  Traditional data: ❌ Not found")
            
        if session_path.exists():
            session_dirs = [d for d in session_path.iterdir() if d.is_dir()]
            print(f"  Session data: ✅ {len(session_dirs)} session directories")
        else:
            print(f"  Session data: ❌ Not found")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_fixed_logic()
