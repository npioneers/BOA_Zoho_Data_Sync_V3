"""
Debug session success detection
"""
import sys
from pathlib import Path
sys.path.append('.')

from json2db_config import get_config

def debug_session_success():
    """Debug why session is not considered successful"""
    
    config = get_config()
    
    print("=== Session Success Debug ===")
    print(f"Require successful: {config.should_require_successful_session()}")
    
    latest_session = config.get_latest_session_folder()
    if latest_session:
        print(f"Latest session: {latest_session.name}")
        
        session_info = config.get_session_info(latest_session)
        print(f"Session info: {session_info}")
        
        is_successful = config.is_session_successful(latest_session)
        print(f"Session successful: {is_successful}")
        
        effective_path = config.get_effective_data_source_path()
        print(f"Effective path: {effective_path}")
        
        # Let's see what happens if we make success requirement False
        config._config["session"]["require_successful"] = False
        is_successful_permissive = config.is_session_successful(latest_session)
        print(f"Session successful (permissive): {is_successful_permissive}")
        
        effective_path_permissive = config.get_effective_data_source_path()
        print(f"Effective path (permissive): {effective_path_permissive}")

if __name__ == "__main__":
    debug_session_success()
