"""
State Management Module for Incremental Sync

This module provides state tracking for incremental synchronization,
storing the last successful sync timestamp to enable efficient data fetching.

Features:
- Thread-safe state file operations
- Graceful handling of missing state files
- Automatic state file creation
- JSON-based persistence

Adheres to operational guidelines: NO hardcoded values, externalized configuration
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages synchronization state for incremental sync operations.
    
    Tracks last successful sync timestamps to enable efficient incremental updates.
    Thread-safe operations with file-based persistence.
    """
    
    def __init__(self, state_file_path: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            state_file_path: Optional path to state file. If None, uses default location.
        """
        if state_file_path:
            self.state_file_path = Path(state_file_path)
        else:
            # Default to config/sync_state.json relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.state_file_path = project_root / "config" / "sync_state.json"
        
        # Thread safety for concurrent operations
        self._lock = Lock()
        
        # Ensure state directory exists
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StateManager initialized with state file: {self.state_file_path}")
    
    def get_last_sync_time(self, module_name: Optional[str] = None) -> Optional[str]:
        """
        Get the last successful sync timestamp.
        
        Args:
            module_name: Optional module name for module-specific timestamps.
                        If None, returns global sync timestamp.
        
        Returns:
            ISO format timestamp string, or None if no previous sync
        """
        with self._lock:
            try:
                if not self.state_file_path.exists():
                    logger.info("No state file found, this appears to be the first sync")
                    return None
                
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                if module_name:
                    # Module-specific timestamp
                    module_timestamps = state_data.get('module_timestamps', {})
                    timestamp = module_timestamps.get(module_name)
                    if timestamp:
                        logger.info(f"Last sync time for {module_name}: {timestamp}")
                    else:
                        logger.info(f"No previous sync found for module: {module_name}")
                    return timestamp
                else:
                    # Global timestamp
                    timestamp = state_data.get('last_sync_time')
                    if timestamp:
                        logger.info(f"Last global sync time: {timestamp}")
                    else:
                        logger.info("No previous global sync found")
                    return timestamp
                
            except Exception as e:
                logger.error(f"Failed to read sync state: {e}")
                return None
    
    def update_last_sync_time(self, new_time: Optional[str] = None, module_name: Optional[str] = None) -> bool:
        """
        Update the last successful sync timestamp.
        
        Args:
            new_time: ISO format timestamp string. If None, uses current time.
            module_name: Optional module name for module-specific timestamps.
                        If None, updates global sync timestamp.
        
        Returns:
            True if update successful, False otherwise
        """
        with self._lock:
            try:
                # Use current time if not provided
                if new_time is None:
                    new_time = datetime.now(timezone.utc).isoformat()
                
                # Load existing state or create new
                state_data = {}
                if self.state_file_path.exists():
                    try:
                        with open(self.state_file_path, 'r', encoding='utf-8') as f:
                            state_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Invalid state file found, creating new state")
                        state_data = {}
                
                # Update timestamps
                if module_name:
                    # Module-specific timestamp
                    if 'module_timestamps' not in state_data:
                        state_data['module_timestamps'] = {}
                    state_data['module_timestamps'][module_name] = new_time
                    logger.info(f"Updated last sync time for {module_name}: {new_time}")
                else:
                    # Global timestamp
                    state_data['last_sync_time'] = new_time
                    logger.info(f"Updated global sync time: {new_time}")
                
                # Add metadata
                state_data['last_updated'] = datetime.now(timezone.utc).isoformat()
                state_data['version'] = '1.0'
                
                # Write updated state
                with open(self.state_file_path, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Successfully updated sync state file: {self.state_file_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update sync state: {e}")
                return False
    
    def get_all_module_timestamps(self) -> Dict[str, str]:
        """
        Get all module-specific sync timestamps.
        
        Returns:
            Dictionary mapping module names to their last sync timestamps
        """
        with self._lock:
            try:
                if not self.state_file_path.exists():
                    return {}
                
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                return state_data.get('module_timestamps', {})
                
            except Exception as e:
                logger.error(f"Failed to read module timestamps: {e}")
                return {}
    
    def clear_sync_state(self, module_name: Optional[str] = None) -> bool:
        """
        Clear sync state for full rebuild operations.
        
        Args:
            module_name: Optional module name. If provided, clears only that module's state.
                        If None, clears all sync state.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if module_name:
                    # Clear specific module
                    if self.state_file_path.exists():
                        with open(self.state_file_path, 'r', encoding='utf-8') as f:
                            state_data = json.load(f)
                        
                        module_timestamps = state_data.get('module_timestamps', {})
                        if module_name in module_timestamps:
                            del module_timestamps[module_name]
                            state_data['module_timestamps'] = module_timestamps
                            
                            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                                json.dump(state_data, f, indent=2, ensure_ascii=False)
                            
                            logger.info(f"Cleared sync state for module: {module_name}")
                        else:
                            logger.info(f"No sync state found for module: {module_name}")
                else:
                    # Clear all state
                    if self.state_file_path.exists():
                        self.state_file_path.unlink()
                        logger.info("Cleared all sync state")
                    else:
                        logger.info("No sync state file to clear")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to clear sync state: {e}")
                return False
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get comprehensive state information for monitoring and debugging.
        
        Returns:
            Dictionary containing all state information
        """
        with self._lock:
            try:
                if not self.state_file_path.exists():
                    return {
                        'state_file_exists': False,
                        'state_file_path': str(self.state_file_path),
                        'message': 'No state file found - this appears to be the first sync'
                    }
                
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                info = {
                    'state_file_exists': True,
                    'state_file_path': str(self.state_file_path),
                    'last_sync_time': state_data.get('last_sync_time'),
                    'last_updated': state_data.get('last_updated'),
                    'version': state_data.get('version'),
                    'module_timestamps': state_data.get('module_timestamps', {}),
                    'module_count': len(state_data.get('module_timestamps', {}))
                }
                
                return info
                
            except Exception as e:
                return {
                    'state_file_exists': self.state_file_path.exists(),
                    'state_file_path': str(self.state_file_path),
                    'error': str(e),
                    'message': 'Error reading state file'
                }
    
    def validate_state_file(self) -> bool:
        """
        Validate the integrity of the state file.
        
        Returns:
            True if state file is valid, False otherwise
        """
        try:
            if not self.state_file_path.exists():
                return True  # Missing file is valid (first run)
            
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Basic validation checks
            if not isinstance(state_data, dict):
                logger.error("State file contains invalid data structure")
                return False
            
            # Check timestamp format if present
            if 'last_sync_time' in state_data:
                try:
                    datetime.fromisoformat(state_data['last_sync_time'].replace('Z', '+00:00'))
                except ValueError:
                    logger.error("Invalid timestamp format in state file")
                    return False
            
            # Check module timestamps if present
            module_timestamps = state_data.get('module_timestamps', {})
            if not isinstance(module_timestamps, dict):
                logger.error("Invalid module timestamps structure")
                return False
            
            for module_name, timestamp in module_timestamps.items():
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    logger.error(f"Invalid timestamp for module {module_name}")
                    return False
            
            logger.info("State file validation successful")
            return True
            
        except Exception as e:
            logger.error(f"State file validation failed: {e}")
            return False


# Global state manager instance
_state_manager = None

def get_state_manager(state_file_path: Optional[str] = None) -> StateManager:
    """
    Get global state manager instance.
    
    Args:
        state_file_path: Optional path to state file
        
    Returns:
        StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager(state_file_path)
    return _state_manager

def reload_state_manager(state_file_path: Optional[str] = None) -> StateManager:
    """
    Reload state manager (useful for testing or config changes).
    
    Args:
        state_file_path: Optional path to state file
        
    Returns:
        New StateManager instance
    """
    global _state_manager
    _state_manager = StateManager(state_file_path)
    return _state_manager
