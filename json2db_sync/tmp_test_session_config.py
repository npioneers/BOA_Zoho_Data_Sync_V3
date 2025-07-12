#!/usr/bin/env python3
"""
Test script to verify JSON2DB session-based configuration
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config import JSON2DBConfig

def test_session_config():
    """Test the corrected session configuration"""
    print("=== Testing JSON2DB Session Configuration ===")
    
    # Create config instance
    config = JSON2DBConfig()
    
    # Display configuration
    print(f"Data source type: {config.get_data_source_config()['type']}")
    print(f"API sync path: {config.get_api_sync_path()}")
    print(f"Consolidated path: {config.get_consolidated_path()}")
    print(f"Is API sync mode: {config.is_api_sync_mode()}")
    print(f"Is consolidated mode: {config.is_consolidated_mode()}")
    
    # Check if session directories exist
    try:
        session_dirs = config.get_session_json_directories()
        print(f"\nFound {len(session_dirs)} session directories:")
        for session_dir in session_dirs:
            print(f"  - {session_dir}")
            
        if session_dirs:
            # Test with the first session
            first_session = session_dirs[0]
            print(f"\nTesting first session: {first_session}")
            
            # Check what's inside the session directory
            session_path = Path(first_session)
            if session_path.exists():
                print(f"Session contents:")
                for item in session_path.iterdir():
                    print(f"  - {item.name}")
                    
                # Check raw_json subdirectory
                raw_json_path = session_path / "raw_json"
                if raw_json_path.exists():
                    print(f"\nraw_json contents:")
                    for item in raw_json_path.iterdir():
                        print(f"  - {item.name}")
                        
                        # Check timestamp directories
                        if item.is_dir():
                            print(f"    Timestamp {item.name} contents:")
                            for subitem in item.iterdir():
                                if subitem.suffix == '.json':
                                    print(f"      - {subitem.name}")
        else:
            print("No session directories found!")
            
    except Exception as e:
        print(f"Error checking session directories: {e}")

if __name__ == "__main__":
    test_session_config()
