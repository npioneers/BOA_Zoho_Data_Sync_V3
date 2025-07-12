"""
JSON2DB Sync Configuration
Centralized configuration management for JSON2DB sync operations.
Eliminates hardcoded paths and provides flexible configuration options.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class JSON2DBConfig:
    """Centralized configuration for JSON2DB sync operations"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config = {}
        self._load_configuration()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            # Data source configuration  
            "data_source": {
                "type": "api_sync",  # "api_sync" or "consolidated"
                "api_sync_base_path": "../api_sync/data/sync_sessions",  # Always point to sync_sessions
                "consolidated_path": "data/raw_json/json_compiled",
                "prefer_session_based": True,  # Always use session-based
                "fallback_to_traditional": False  # No fallback - always session-based
            },
            
            # Database configuration
            "database": {
                "path": "../data/database/production.db",
                "backup_before_operations": True,
                "connection_timeout": 30
            },
            
            # Processing configuration
            "processing": {
                "default_cutoff_days": 30,
                "batch_size": 1000,
                "max_memory_usage_mb": 512,
                "enable_progress_logging": True,
                "enable_duplicate_prevention": True,  # Always enable duplicate prevention
                "skip_existing_records": True  # Skip records that already exist
            },
            
            # Session configuration
            "session": {
                "auto_detect_latest": True,  # Always find latest session
                "max_session_age_hours": 48,  # Allow older sessions if needed
                "require_session_success": False,  # Don't require session success flag
                "include_metadata": True,  # Include session metadata
                "force_session_based": True  # Always treat as session-based
            },
            
            # Logging configuration
            "logging": {
                "level": "INFO",
                "log_dir": "logs",
                "max_log_files": 10,
                "log_rotation_size_mb": 50
            },
            
            # Module mapping (for backward compatibility)
            "modules": {
                "enabled_modules": [
                    "invoices", "bills", "salesorders", "purchaseorders", 
                    "creditnotes", "items", "contacts", "customerpayments", 
                    "vendorpayments", "organizations", "budgets", "tasks"
                ],
                "line_item_modules": [
                    "invoices", "bills", "salesorders", 
                    "purchaseorders", "creditnotes"
                ]
            }
        }
    
    def _load_configuration(self):
        """Load configuration from multiple sources in priority order"""
        # Start with defaults
        self._config = self._get_default_config()
        
        # Override with config file if provided
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self._merge_config(self._config, file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            "JSON2DB_DATA_SOURCE_TYPE": ("data_source", "type"),
            "JSON2DB_API_SYNC_PATH": ("data_source", "api_sync_base_path"),
            "JSON2DB_CONSOLIDATED_PATH": ("data_source", "consolidated_path"),
            "JSON2DB_DATABASE_PATH": ("database", "path"),
            "JSON2DB_CUTOFF_DAYS": ("processing", "default_cutoff_days"),
            "JSON2DB_LOG_LEVEL": ("logging", "level"),
            "JSON2DB_LOG_DIR": ("logging", "log_dir")
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert to appropriate type
                if key in ["default_cutoff_days", "max_session_age_hours", "connection_timeout"]:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif key in ["prefer_session_based", "fallback_to_traditional", "backup_before_operations"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                
                self._config[section][key] = value
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        if key is None:
            return self._config.get(section, default)
        return self._config.get(section, {}).get(key, default)
    
    def _resolve_path(self, path: str) -> str:
        """Resolve relative path to absolute path"""
        if os.path.isabs(path):
            return path
        
        # Get the directory where the config file is located (json2db_sync directory)
        config_dir = Path(__file__).parent
        resolved_path = (config_dir / path).resolve()
        return str(resolved_path)
    
    def get_data_source_config(self) -> Dict[str, Any]:
        """Get complete data source configuration"""
        return self._config["data_source"]
    
    def get_database_path(self) -> str:
        """Get database file path (resolved to absolute path)"""
        relative_path = self._config["database"]["path"]
        return self._resolve_path(relative_path)
    
    def get_api_sync_path(self) -> str:
        """Get API sync base path (resolved to absolute path)"""
        relative_path = self._config["data_source"]["api_sync_base_path"]
        return self._resolve_path(relative_path)
    
    def get_effective_data_source_path(self) -> str:
        """Get the effective data source path based on current configuration"""
        if self.is_api_sync_mode():
            return self.get_api_sync_path()
        else:
            return self.get_consolidated_path()
    
    def get_consolidated_path(self) -> str:
        """Get consolidated JSON path (resolved to absolute path)"""
        relative_path = self._config["data_source"]["consolidated_path"]
        return self._resolve_path(relative_path)
    
    def is_api_sync_mode(self) -> bool:
        """Check if using API sync data source"""
        return self._config["data_source"]["type"] == "api_sync"
    
    def is_consolidated_mode(self) -> bool:
        """Check if using consolidated data source"""
        return self._config["data_source"]["type"] == "consolidated"
    
    def get_enabled_modules(self) -> list:
        """Get list of enabled modules"""
        return self._config["modules"]["enabled_modules"]
    
    def get_line_item_modules(self) -> list:
        """Get list of modules that have line items"""
        return self._config["modules"]["line_item_modules"]
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return self._config["processing"]
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get session configuration"""
        return self._config["session"]
    
    def get_latest_session_folder(self) -> Optional[str]:
        """Get the latest session folder from the sync_sessions directory"""
        try:
            sync_sessions_path = Path(self.get_api_sync_path())
            if not sync_sessions_path.exists():
                return None
            
            # Find all session folders
            session_folders = [
                f for f in sync_sessions_path.iterdir() 
                if f.is_dir() and f.name.startswith("sync_session_")
            ]
            
            if not session_folders:
                return None
            
            # Sort by creation time (newest first) and return the latest
            latest_session = max(session_folders, key=lambda x: x.stat().st_mtime)
            return str(latest_session)
            
        except Exception as e:
            print(f"Warning: Could not determine latest session folder: {e}")
            return None
    
    def get_session_json_directories(self, session_path: Optional[str] = None) -> list:
        """Get list of directories containing JSON files from sync_sessions"""
        try:
            json_directories = []
            
            if session_path:
                # We have a specific session path - work with that directly
                session_path_obj = Path(session_path)
                
                # Case 1: We're pointing to a specific session folder
                if session_path_obj.name.startswith("sync_session_"):
                    raw_json_path = session_path_obj / "raw_json"
                    if raw_json_path.exists():
                        # Find timestamp directories within raw_json
                        timestamp_dirs = [
                            d for d in raw_json_path.iterdir() 
                            if d.is_dir()
                        ]
                        json_directories.extend(timestamp_dirs)
                    return json_directories
                
                # Case 2: We might be pointing to sync_sessions directory
                elif session_path_obj.name == "sync_sessions":
                    sync_sessions_path = session_path_obj
                else:
                    # Case 3: Try to interpret as a path that might contain sessions
                    sync_sessions_path = session_path_obj
            else:
                # No specific path provided - use default api_sync path
                sync_sessions_path = Path(self.get_api_sync_path())
            
            if not sync_sessions_path.exists():
                return []
            
            # Find all session folders
            session_folders = [
                f for f in sync_sessions_path.iterdir() 
                if f.is_dir() and f.name.startswith("sync_session_")
            ]
            
            for session_folder in session_folders:
                # Look for raw_json subdirectory
                raw_json_path = session_folder / "raw_json"
                if raw_json_path.exists():
                    # Find timestamp directories within raw_json
                    timestamp_dirs = [
                        d for d in raw_json_path.iterdir() 
                        if d.is_dir()
                    ]
                    json_directories.extend(timestamp_dirs)
            
            return json_directories
            
        except Exception as e:
            print(f"Warning: Could not get session directories: {e}")
            return []
    
    def save_config(self, file_path: str):
        """Save current configuration to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save configuration: {e}")
    
    def create_sample_config(self, file_path: str):
        """Create a sample configuration file"""
        sample_config = {
            "data_source": {
                "type": "api_sync",
                "api_sync_base_path": "../api_sync",
                "prefer_session_based": True,
                "fallback_to_traditional": True
            },
            "database": {
                "path": "data/database/production.db"
            },
            "processing": {
                "default_cutoff_days": 30,
                "batch_size": 1000
            },
            "logging": {
                "level": "INFO",
                "log_dir": "logs"
            }
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(sample_config, f, indent=2)
            print(f"✅ Sample configuration created: {file_path}")
        except Exception as e:
            print(f"❌ Failed to create sample config: {e}")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return status"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate data source paths
        if self.is_api_sync_mode():
            api_sync_path = Path(self.get_api_sync_path())
            if not api_sync_path.exists():
                validation["errors"].append(f"API sync path does not exist: {api_sync_path}")
                validation["valid"] = False
        
        if self.is_consolidated_mode():
            consolidated_path = Path(self.get_consolidated_path())
            if not consolidated_path.exists():
                validation["errors"].append(f"Consolidated path does not exist: {consolidated_path}")
                validation["valid"] = False
        
        # Validate database path directory
        db_path = Path(self.get_database_path())
        if not db_path.parent.exists():
            validation["warnings"].append(f"Database directory does not exist: {db_path.parent}")
        
        # Validate log directory
        log_dir = Path(self.get("logging", "log_dir"))
        if not log_dir.exists():
            validation["warnings"].append(f"Log directory does not exist: {log_dir}")
        
        return validation
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"JSON2DBConfig(type={self.get('data_source', 'type')}, source={self.get_api_sync_path() if self.is_api_sync_mode() else self.get_consolidated_path()})"


# Global configuration instance
_global_config = None

def get_config(config_file: Optional[str] = None) -> JSON2DBConfig:
    """Get global configuration instance"""
    global _global_config
    if _global_config is None or config_file is not None:
        _global_config = JSON2DBConfig(config_file)
    return _global_config

def reload_config(config_file: Optional[str] = None):
    """Reload global configuration"""
    global _global_config
    _global_config = JSON2DBConfig(config_file)
    return _global_config
