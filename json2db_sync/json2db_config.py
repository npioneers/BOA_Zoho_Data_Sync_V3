"""
JSON2DB Sync Configuration Manager
Centralized configuration with environment variable support.
Removes all hardcoded paths while preserving database-driven table mappings.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging


class JSON2DBSyncConfig:
    """
    Configuration manager for JSON2DB sync operations.
    
    Configuration Hierarchy (highest to lowest priority):
    1. Environment Variables
    2. Configuration File (.json)
    3. Default Values
    
    Note: JSON to database table mappings are preserved from database table.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "json2db_sync_config.json"
        self._config = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from defaults, file, and environment variables"""
        # Start with defaults
        self._config = self._get_defaults()
        
        # Load from config file if exists
        if Path(self.config_file).exists():
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_environment()
        
        # Resolve paths to absolute paths
        self._resolve_paths()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Default configuration values"""
        return {
            "database": {
                "path": "data/database/production.db",
                "connection_timeout": 30
            },
            "data_source": {
                "type": "api_sync",  # api_sync | consolidated
                "api_sync_path": "../api_sync",
                "consolidated_path": "data/raw_json/json_compiled",
                "fallback_enabled": True
            },
            "session": {
                "use_latest": True,
                "max_age_hours": 24,
                "require_successful": True,
                "traditional_fallback": True
            },
            "processing": {
                "default_cutoff_days": 30,
                "batch_size": 1000,
                "enable_date_filtering": True,
                "parallel_processing": False
            },
            "logging": {
                "level": "INFO",
                "directory": "logs",
                "max_log_files": 10,
                "file_size_mb": 50
            },
            "paths": {
                "working_directory": ".",
                "temp_directory": "temp",
                "backup_directory": "backups"
            }
        }
    
    def _load_from_file(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Merge file config with defaults
            self._deep_merge(self._config, file_config)
            
        except Exception as e:
            logging.warning(f"Could not load config file {self.config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Database configuration
            "JSON2DB_DATABASE_PATH": ("database", "path"),
            "JSON2DB_DATABASE_TIMEOUT": ("database", "connection_timeout"),
            
            # Data source configuration
            "JSON2DB_DATA_SOURCE_TYPE": ("data_source", "type"),
            "JSON2DB_API_SYNC_PATH": ("data_source", "api_sync_path"),
            "JSON2DB_CONSOLIDATED_PATH": ("data_source", "consolidated_path"),
            "JSON2DB_FALLBACK_ENABLED": ("data_source", "fallback_enabled"),
            
            # Session configuration
            "JSON2DB_SESSION_MAX_AGE": ("session", "max_age_hours"),
            "JSON2DB_REQUIRE_SUCCESS": ("session", "require_successful"),
            "JSON2DB_TRADITIONAL_FALLBACK": ("session", "traditional_fallback"),
            
            # Processing configuration
            "JSON2DB_CUTOFF_DAYS": ("processing", "default_cutoff_days"),
            "JSON2DB_BATCH_SIZE": ("processing", "batch_size"),
            "JSON2DB_ENABLE_FILTERING": ("processing", "enable_date_filtering"),
            
            # Logging configuration
            "JSON2DB_LOG_LEVEL": ("logging", "level"),
            "JSON2DB_LOG_DIR": ("logging", "directory"),
            "JSON2DB_MAX_LOG_FILES": ("logging", "max_log_files"),
            
            # Path configuration
            "JSON2DB_WORKING_DIR": ("paths", "working_directory"),
            "JSON2DB_TEMP_DIR": ("paths", "temp_directory"),
            "JSON2DB_BACKUP_DIR": ("paths", "backup_directory")
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                converted_value = self._convert_env_value(key, value)
                self._config[section][key] = converted_value
    
    def _convert_env_value(self, key: str, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Integer fields
        if key in ["connection_timeout", "max_age_hours", "default_cutoff_days", 
                  "batch_size", "max_log_files", "file_size_mb"]:
            try:
                return int(value)
            except ValueError:
                logging.warning(f"Invalid integer value for {key}: {value}")
                return value
        
        # Boolean fields
        elif key in ["fallback_enabled", "use_latest", "require_successful", 
                    "traditional_fallback", "enable_date_filtering", "parallel_processing"]:
            return value.lower() in ["true", "1", "yes", "on", "enabled"]
        
        # String fields (default)
        else:
            return value
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge configuration dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _resolve_paths(self):
        """Resolve all paths to absolute paths"""
        path_sections = ["database", "data_source", "logging", "paths"]
        
        for section in path_sections:
            if section in self._config:
                for key, value in self._config[section].items():
                    if "path" in key or "directory" in key:
                        if isinstance(value, str):
                            self._config[section][key] = str(Path(value).resolve())
    
    # Database Configuration
    def get_database_path(self) -> Path:
        """Get database file path"""
        return Path(self._config["database"]["path"])
    
    def get_database_timeout(self) -> int:
        """Get database connection timeout"""
        return self._config["database"]["connection_timeout"]
    
    # Data Source Configuration
    def get_data_source_type(self) -> str:
        """Get data source type (api_sync or consolidated)"""
        return self._config["data_source"]["type"]
    
    def get_api_sync_path(self) -> Path:
        """Get API sync base path"""
        return Path(self._config["data_source"]["api_sync_path"])
    
    def get_consolidated_path(self) -> Path:
        """Get consolidated JSON path"""
        return Path(self._config["data_source"]["consolidated_path"])
    
    def is_fallback_enabled(self) -> bool:
        """Check if fallback data sources are enabled"""
        return self._config["data_source"]["fallback_enabled"]
    
    def get_primary_data_path(self) -> Path:
        """Get primary data path based on configured type"""
        if self.get_data_source_type() == "api_sync":
            return self.get_api_sync_path()
        else:
            return self.get_consolidated_path()
    
    def get_fallback_paths(self) -> List[Path]:
        """Get list of fallback data paths"""
        primary_type = self.get_data_source_type()
        fallback_paths = []
        
        if self.is_fallback_enabled():
            if primary_type == "api_sync":
                # If primary is api_sync, fallback to consolidated
                fallback_paths.append(self.get_consolidated_path())
                # Also try traditional api_sync structure
                fallback_paths.append(self.get_api_sync_path() / "data" / "raw_json")
            else:
                # If primary is consolidated, fallback to api_sync
                fallback_paths.append(self.get_api_sync_path())
        
        return fallback_paths
    
    # Session Configuration
    def should_use_latest_session(self) -> bool:
        """Check if latest session should be used"""
        return self._config["session"]["use_latest"]
    
    def get_max_session_age_hours(self) -> int:
        """Get maximum acceptable session age in hours"""
        return self._config["session"]["max_age_hours"]
    
    def should_require_successful_session(self) -> bool:
        """Check if only successful sessions should be used"""
        return self._config["session"]["require_successful"]
    
    def is_traditional_fallback_enabled(self) -> bool:
        """Check if fallback to traditional structure is enabled"""
        return self._config["session"]["traditional_fallback"]
    
    # Processing Configuration
    def get_default_cutoff_days(self) -> int:
        """Get default cutoff days for data filtering"""
        return self._config["processing"]["default_cutoff_days"]
    
    def get_batch_size(self) -> int:
        """Get processing batch size"""
        return self._config["processing"]["batch_size"]
    
    def is_date_filtering_enabled(self) -> bool:
        """Check if date filtering is enabled by default"""
        return self._config["processing"]["enable_date_filtering"]
    
    def is_parallel_processing_enabled(self) -> bool:
        """Check if parallel processing is enabled"""
        return self._config["processing"]["parallel_processing"]
    
    # Logging Configuration
    def get_log_level(self) -> str:
        """Get logging level"""
        return self._config["logging"]["level"]
    
    def get_log_directory(self) -> Path:
        """Get logging directory"""
        return Path(self._config["logging"]["directory"])
    
    def get_max_log_files(self) -> int:
        """Get maximum number of log files to keep"""
        return self._config["logging"]["max_log_files"]
    
    def get_log_file_size_mb(self) -> int:
        """Get maximum log file size in MB"""
        return self._config["logging"]["file_size_mb"]
    
    # Path Configuration
    def get_working_directory(self) -> Path:
        """Get working directory"""
        return Path(self._config["paths"]["working_directory"])
    
    def get_temp_directory(self) -> Path:
        """Get temporary directory"""
        return Path(self._config["paths"]["temp_directory"])
    
    def get_backup_directory(self) -> Path:
        """Get backup directory"""
        return Path(self._config["paths"]["backup_directory"])
    
    # Utility Methods
    def create_example_config(self, filepath: Optional[str] = None) -> str:
        """Create example configuration file"""
        example_config = {
            "_description": "JSON2DB Sync Configuration",
            "_note": "Environment variables override these settings",
            "_env_prefix": "JSON2DB_",
            "database": {
                "path": "data/database/production.db",
                "connection_timeout": 30
            },
            "data_source": {
                "type": "api_sync",
                "api_sync_path": "../api_sync",
                "consolidated_path": "data/raw_json/json_compiled",
                "fallback_enabled": True
            },
            "session": {
                "use_latest": True,
                "max_age_hours": 24,
                "require_successful": True,
                "traditional_fallback": True
            },
            "processing": {
                "default_cutoff_days": 30,
                "batch_size": 1000,
                "enable_date_filtering": True,
                "parallel_processing": False
            },
            "logging": {
                "level": "INFO",
                "directory": "logs",
                "max_log_files": 10,
                "file_size_mb": 50
            },
            "paths": {
                "working_directory": ".",
                "temp_directory": "temp",
                "backup_directory": "backups"
            }
        }
        
        output_file = filepath or "json2db_sync_config.example.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=4)
        
        return output_file
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Check database path
        db_path = self.get_database_path()
        if not db_path.parent.exists():
            validation["warnings"].append(f"Database directory missing: {db_path.parent}")
        
        # Check primary data source based on type
        if self.get_data_source_type() == "api_sync":
            # Check for session-based structure
            sessions_dir = self.get_api_sync_path() / "data" / "sync_sessions"
            if sessions_dir.exists():
                latest_session = self.get_latest_session_folder()
                if latest_session:
                    if self.is_session_successful(latest_session):
                        validation["info"].append(f"Valid session found: {latest_session.name}")
                    else:
                        validation["warnings"].append(f"Latest session not successful: {latest_session.name}")
                    
                    # Check for available modules
                    modules = self.get_available_modules_in_session(latest_session)
                    if modules:
                        validation["info"].append(f"Available modules: {', '.join(modules[:5])}{'...' if len(modules) > 5 else ''}")
                    else:
                        validation["warnings"].append("No JSON modules found in latest session")
                else:
                    validation["warnings"].append("No valid sessions found in api_sync")
            else:
                # Check for traditional api_sync structure
                traditional_path = self.get_api_sync_path() / "data" / "raw_json"
                if traditional_path.exists():
                    validation["info"].append("Using traditional api_sync structure")
                else:
                    validation["errors"].append(f"API sync path has no valid data structure: {self.get_api_sync_path()}")
                    validation["valid"] = False
        else:
            # Check consolidated structure
            consolidated_path = self.get_consolidated_path()
            if not consolidated_path.exists():
                validation["errors"].append(f"Consolidated path does not exist: {consolidated_path}")
                validation["valid"] = False
        
        # Check fallback availability if primary source has issues
        if not validation["valid"] and self.is_fallback_enabled():
            fallback_found = False
            for fallback in self.get_fallback_paths():
                if fallback.exists():
                    validation["info"].append(f"Fallback available: {fallback}")
                    validation["valid"] = True  # Restore validity if fallback exists
                    fallback_found = True
                    break
            
            if not fallback_found:
                validation["errors"].append("No valid data sources found (including fallbacks)")
        
        # Check log directory
        log_dir = self.get_log_directory()
        if not log_dir.exists():
            validation["info"].append(f"Log directory will be created: {log_dir}")
        
        return validation
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display"""
        summary = {
            "data_source_type": self.get_data_source_type(),
            "primary_data_path": str(self.get_primary_data_path()),
            "database_path": str(self.get_database_path()),
            "fallback_enabled": self.is_fallback_enabled(),
            "session_max_age": self.get_max_session_age_hours(),
            "default_cutoff_days": self.get_default_cutoff_days(),
            "log_level": self.get_log_level()
        }
        
        # Add session-specific information if using api_sync
        if self.get_data_source_type() == "api_sync":
            latest_session = self.get_latest_session_folder()
            if latest_session:
                summary["latest_session"] = latest_session.name
                summary["session_successful"] = self.is_session_successful(latest_session)
                summary["available_modules"] = len(self.get_available_modules_in_session(latest_session))
            else:
                summary["latest_session"] = "None found"
                summary["session_successful"] = False
                summary["available_modules"] = 0
        
        return summary
    
    def __str__(self) -> str:
        return f"JSON2DBSyncConfig(type={self.get_data_source_type()}, path={self.get_primary_data_path()})"
    
    # Session Discovery Methods
    def get_latest_session_folder(self) -> Optional[Path]:
        """Get the latest session folder from api_sync structure"""
        sessions_dir = self.get_api_sync_path() / "data" / "sync_sessions"
        
        if not sessions_dir.exists():
            return None
        
        # Find session folders
        session_folders = [
            f for f in sessions_dir.iterdir() 
            if f.is_dir() and f.name.startswith("sync_session_")
        ]
        
        if not session_folders:
            return None
        
        # Sort by timestamp (newest first)
        latest_session = sorted(session_folders, key=lambda x: x.name, reverse=True)[0]
        
        # Check session age if configured
        if self.get_max_session_age_hours() > 0:
            timestamp_str = latest_session.name.replace("sync_session_", "")
            try:
                from datetime import datetime
                session_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                age_hours = (datetime.now() - session_time).total_seconds() / 3600
                
                if age_hours > self.get_max_session_age_hours():
                    return None  # Session too old
            except ValueError:
                pass  # Invalid timestamp format, continue anyway
        
        return latest_session
    
    def get_session_json_directories(self, session_folder: Path) -> List[Path]:
        """Get all timestamp directories within a session that contain JSON files"""
        raw_json_dir = session_folder / "raw_json"
        
        if not raw_json_dir.exists():
            return []
        
        # Find timestamp directories (format: YYYY-MM-DD_HH-MM-SS = 4 dashes)
        timestamp_dirs = [
            d for d in raw_json_dir.iterdir() 
            if d.is_dir() and d.name.count('-') == 4  # timestamp format YYYY-MM-DD_HH-MM-SS
        ]
        
        # Sort by timestamp (newest first)
        return sorted(timestamp_dirs, key=lambda x: x.name, reverse=True)
    
    def find_module_file_in_session(self, module_name: str, session_folder: Path = None) -> Optional[Path]:
        """Find a specific module JSON file within a session"""
        if session_folder is None:
            session_folder = self.get_latest_session_folder()
            
        if not session_folder:
            return None
        
        timestamp_dirs = self.get_session_json_directories(session_folder)
        
        # Look for the module file in timestamp directories
        for timestamp_dir in timestamp_dirs:
            module_file = timestamp_dir / f"{module_name}.json"
            if module_file.exists():
                return module_file
        
        return None
    
    def get_available_modules_in_session(self, session_folder: Path = None) -> List[str]:
        """Get list of available modules in the latest session"""
        if session_folder is None:
            session_folder = self.get_latest_session_folder()
            
        if not session_folder:
            return []
        
        modules = set()
        timestamp_dirs = self.get_session_json_directories(session_folder)
        
        # Collect all JSON files across timestamp directories
        for timestamp_dir in timestamp_dirs:
            for json_file in timestamp_dir.glob("*.json"):
                module_name = json_file.stem
                # Remove line_items suffix if present
                if module_name.endswith("_line_items"):
                    module_name = module_name.replace("_line_items", "")
                modules.add(module_name)
        
        return sorted(list(modules))
    
    def get_session_info(self, session_folder: Path = None) -> Optional[Dict[str, Any]]:
        """Get session metadata from session_info.json"""
        if session_folder is None:
            session_folder = self.get_latest_session_folder()
            
        if not session_folder:
            return None
        
        session_info_file = session_folder / "session_info.json"
        
        if session_info_file.exists():
            try:
                import json
                with open(session_info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        
        return None
    
    def is_session_successful(self, session_folder: Path = None) -> bool:
        """Check if a session completed successfully"""
        session_info = self.get_session_info(session_folder)
        
        if not session_info:
            # If no session info and success is required, default to False
            # If success is not required, check for actual data files
            if self.should_require_successful_session():
                return False
            else:
                # Check if there are any JSON files in the session
                if session_folder:
                    timestamp_dirs = self.get_session_json_directories(session_folder)
                    for timestamp_dir in timestamp_dirs:
                        json_files = list(timestamp_dir.glob("*.json"))
                        if json_files:
                            return True
                return False
        
        # Check various indicators of success
        session_status = session_info.get("session_status", "unknown")
        if session_status == "completed":
            return True
        elif session_status == "failed":
            return False
        
        # Check for session end time (indicates completion)
        if "session_end" in session_info:
            return True
        
        # If we have session_start and some data files, consider it successful
        # when success requirement is disabled
        if "session_start" in session_info and not self.should_require_successful_session():
            if session_folder:
                timestamp_dirs = self.get_session_json_directories(session_folder)
                for timestamp_dir in timestamp_dirs:
                    json_files = list(timestamp_dir.glob("*.json"))
                    if json_files:
                        return True
        
        # Default based on success requirement setting
        return not self.should_require_successful_session()

    # Enhanced data source methods
    def get_effective_data_source_path(self) -> Path:
        """Get the effective data source path based on type and availability"""
        if self.get_data_source_type() == "api_sync":
            session_folder = self.get_latest_session_folder()
            if session_folder and self.is_session_successful(session_folder):
                return session_folder
            elif self.is_fallback_enabled():
                # Try traditional api_sync structure
                traditional_path = self.get_api_sync_path() / "data" / "raw_json"
                if traditional_path.exists():
                    return traditional_path
                # Fall back to consolidated if available
                consolidated_path = self.get_consolidated_path()
                if consolidated_path.exists():
                    return consolidated_path
        else:
            # Using consolidated mode
            consolidated_path = self.get_consolidated_path()
            if consolidated_path.exists():
                return consolidated_path
            elif self.is_fallback_enabled():
                # Try api_sync as fallback
                session_folder = self.get_latest_session_folder()
                if session_folder:
                    return session_folder
        
        # Return primary path even if it doesn't exist (for error reporting)
        return self.get_primary_data_path()

# Global configuration instance
_global_config = None

def get_config() -> JSON2DBSyncConfig:
    """Get global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = JSON2DBSyncConfig()
    return _global_config

def reload_config(config_file: Optional[str] = None) -> JSON2DBSyncConfig:
    """Reload global configuration"""
    global _global_config
    _global_config = JSON2DBSyncConfig(config_file)
    return _global_config


if __name__ == "__main__":
    # Demo and testing
    config = JSON2DBSyncConfig()
    
    # Create example config
    example_file = config.create_example_config()
    print(f"Created example config: {example_file}")
    
    # Validate configuration
    validation = config.validate_configuration()
    print(f"Validation: {validation}")
    
    # Show summary
    summary = config.get_config_summary()
    print(f"Config summary: {summary}")
