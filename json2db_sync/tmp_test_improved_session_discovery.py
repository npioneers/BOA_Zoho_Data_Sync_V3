#!/usr/bin/env python3
"""
Test the improved session discovery that looks for sessions with actual data
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config import JSON2DBConfig

def test_improved_session_discovery():
    """Test that the session discovery now finds sessions with actual data"""
    print("=== Testing Improved Session Discovery ===")
    
    # Create config instance
    config = JSON2DBConfig()
    
    # Test the latest session discovery
    latest_session = config.get_latest_session_folder()
    print(f"Latest session with data: {latest_session}")
    
    if latest_session:
        session_path = Path(latest_session)
        print(f"Session name: {session_path.name}")
        
        # Check if it has data files
        has_data = config._session_has_data_files(session_path)
        print(f"Has actual data files: {has_data}")
        
        # Show what's in the session
        raw_json_path = session_path / "raw_json"
        if raw_json_path.exists():
            print(f"\nTimestamp directories in session:")
            for timestamp_dir in raw_json_path.iterdir():
                if timestamp_dir.is_dir():
                    json_files = list(timestamp_dir.glob("*.json"))
                    data_files = [f for f in json_files if not f.name.startswith("sync_metadata_")]
                    metadata_files = [f for f in json_files if f.name.startswith("sync_metadata_")]
                    
                    print(f"  📁 {timestamp_dir.name}:")
                    if data_files:
                        print(f"    ✅ Data files: {[f.name for f in data_files]}")
                    if metadata_files:
                        print(f"    📋 Metadata files: {[f.name for f in metadata_files]}")
                    if not json_files:
                        print(f"    ❌ No JSON files")
    else:
        print("❌ No session found!")

if __name__ == "__main__":
    test_improved_session_discovery()
