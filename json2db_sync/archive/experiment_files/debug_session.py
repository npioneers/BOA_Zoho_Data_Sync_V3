"""
Debug session directory discovery
"""
import sys
from pathlib import Path
sys.path.append('.')

from json2db_config import JSON2DBSyncConfig

def debug_session_structure():
    """Debug the session structure step by step"""
    
    config = JSON2DBSyncConfig()
    latest_session = config.get_latest_session_folder()
    
    if not latest_session:
        print("No sessions found")
        return
    
    print(f"Session: {latest_session}")
    
    raw_json_dir = latest_session / "raw_json"
    print(f"Raw JSON dir: {raw_json_dir}")
    print(f"Raw JSON dir exists: {raw_json_dir.exists()}")
    
    if raw_json_dir.exists():
        print("\nContents of raw_json:")
        for item in raw_json_dir.iterdir():
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")
        
        print("\nTesting timestamp directory detection:")
        for item in raw_json_dir.iterdir():
            if item.is_dir():
                dash_count = item.name.count('-')
                print(f"  {item.name}: dash count = {dash_count}, matches criteria = {dash_count >= 5}")
                
                if dash_count >= 5:
                    print(f"    Contents: {list(item.iterdir())}")

if __name__ == "__main__":
    debug_session_structure()
