"""
Configuration Management Module for Project Bedrock V2

This module provides centralized configuration loading following the hierarchy:
1. Environment Variables (Highest Priority)
2. Configuration Files (config.yaml, settings.yaml)  
3. Sensible Default Fallbacks (Lowest Priority)

Features:
- Dynamic path resolution (use 'LATEST' to auto-find newest timestamped directories)
- Hierarchical configuration loading
- Environment variable overrides
- Path validation and resolution

Adheres to operational guidelines: NO hardcoded values, externalized configuration
"""

import os
import yaml
import logging
import re
import glob
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def _find_latest_timestamped_directory(base_path: str, pattern: str = "*") -> Optional[str]:
    """
    Find the most recent timestamped directory within a base path.
    
    Supports multiple timestamp patterns:
    - JSON API pattern: YYYY-MM-DD_HH-MM-SS (e.g., 2025-07-05_16-20-31)
    - CSV backup pattern: Company Name_YYYY-MM-DD (e.g., Nangsel Pioneers_2025-06-22)
    
    Args:
        base_path: Base directory to search in (e.g., 'data/raw_json', 'data/csv')
        pattern: Pattern to match directories (default: '*')
        
    Returns:
        Path to the latest timestamped directory, or None if none found
    """
    try:
        # Get project root (3 levels up from this file: src/data_pipeline/config.py)
        project_root = Path(__file__).parent.parent.parent
        base_dir = project_root / base_path
        
        if not base_dir.exists():
            logger.warning(f"Base directory does not exist: {base_dir}")
            return None
        
        # Patterns for different timestamp formats
        # JSON API pattern: YYYY-MM-DD_HH-MM-SS
        json_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}).*')
        # CSV backup pattern: Any text followed by _YYYY-MM-DD
        csv_pattern = re.compile(r'^.*_(\d{4}-\d{2}-\d{2})$')
        
        timestamped_dirs = []
        
        for item in base_dir.iterdir():
            if item.is_dir():
                timestamp = None
                timestamp_str = None
                
                # Try JSON API pattern first (more specific)
                json_match = json_pattern.match(item.name)
                if json_match:
                    timestamp_str = json_match.group(1)
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                    except ValueError:
                        continue
                else:
                    # Try CSV backup pattern
                    csv_match = csv_pattern.match(item.name)
                    if csv_match:
                        date_str = csv_match.group(1)
                        try:
                            # For CSV pattern, we only have date, so set time to midnight
                            timestamp = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            continue
                
                if timestamp:
                    timestamped_dirs.append((timestamp, item))
                    logger.debug(f"Found timestamped directory: {item.name} -> {timestamp}")
        
        if not timestamped_dirs:
            logger.warning(f"No timestamped directories found in: {base_dir}")
            return None
        
        # Sort by timestamp (most recent first) and return the latest
        timestamped_dirs.sort(key=lambda x: x[0], reverse=True)
        latest_dir = timestamped_dirs[0][1]
        
        logger.info(f"Found latest timestamped directory: {latest_dir}")
        return str(latest_dir.relative_to(project_root))
        
    except Exception as e:
        logger.error(f"Error finding latest timestamped directory in {base_path}: {e}")
        return None


def _resolve_dynamic_path(config_path: str, base_search_path: str) -> str:
    """
    Resolve dynamic path configurations.
    
    Args:
        config_path: The configured path (may be 'LATEST' or actual path)
        base_search_path: Base directory to search for LATEST (e.g., 'data/raw_json', 'data/csv')
        
    Returns:
        Resolved path string
    """
    if config_path == 'LATEST':
        resolved = _find_latest_timestamped_directory(base_search_path)
        if resolved:
            return resolved
        else:
            logger.warning(f"Could not resolve 'LATEST' for {base_search_path}, falling back to base path")
            return base_search_path
    else:
        return config_path


class ConfigurationManager:
    """
    Centralized configuration manager implementing the approved hierarchy:
    Environment Variables → Config Files → Defaults
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file_path: Optional path to config file. If None, searches standard locations.
        """
        self.config_data = {}
        self.config_file_path = config_file_path
        self._load_configuration()
        
        logger.info(f"ConfigurationManager initialized from: {self.config_file_path}")
    
    def _load_configuration(self) -> None:
        """Load configuration from files and environment variables."""
        # Step 1: Load defaults
        self.config_data = self._get_default_config()
        
        # Step 2: Load from config file
        config_file = self._find_config_file()
        if config_file and config_file.exists():
            self.config_file_path = str(config_file)
            file_config = self._load_config_file(config_file)
            self._deep_merge(self.config_data, file_config)
            logger.info(f"Loaded configuration from: {config_file}")
        else:
            logger.warning("No configuration file found, using defaults + environment variables")
        
        # Step 3: Override with environment variables (highest priority)
        self._apply_environment_overrides()
        
        logger.debug(f"Final configuration loaded with keys: {list(self.config_data.keys())}")
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations."""
        if self.config_file_path:
            return Path(self.config_file_path)
        
        # Search standard locations
        search_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "settings.yaml", 
            Path(__file__).parent.parent.parent / "config" / "settings.yaml",
            Path(__file__).parent.parent.parent / "config.yaml"
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
            return {}
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            # Data source paths
            'BEDROCK_CSV_BACKUP_PATH': ['data_sources', 'csv_backup_path'],
            'BEDROCK_JSON_API_PATH': ['data_sources', 'json_api_path'],
            'BEDROCK_TARGET_DATABASE': ['data_sources', 'target_database'],
            
            # Processing settings
            'BEDROCK_BATCH_SIZE': ['processing', 'batch_size'],
            'BEDROCK_VALIDATE_TRANSFORMATIONS': ['processing', 'validate_transformations'],
            'BEDROCK_CREATE_BACKUPS': ['processing', 'create_backups'],
            'BEDROCK_SHOW_PROGRESS': ['processing', 'show_progress'],
            
            # Logging settings
            'BEDROCK_LOG_LEVEL': ['logging', 'level'],
            'BEDROCK_LOG_FILE': ['logging', 'file'],
            'BEDROCK_LOG_CONSOLE': ['logging', 'console']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(env_value)
                self._set_nested_value(self.config_data, config_path, converted_value)
                logger.debug(f"Applied environment override: {env_var} = {converted_value}")
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: list, value: Any) -> None:
        """Set value in nested dictionary using path list."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override dictionary into base dictionary."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'data_sources': {
                'csv_backup_path': 'LATEST',  # Auto-resolves to most recent CSV backup directory
                'json_api_path': 'LATEST',    # Auto-resolves to most recent timestamped directory
                'target_database': 'data/database/production.db'
            },
            'processing': {
                'batch_size': 1000,
                'validate_transformations': True,
                'create_backups': False,  # Disabled during refactoring
                'show_progress': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/bedrock_rebuild.log', 
                'console': True
            },
            'entities': {
                'bills': {
                    'enabled': True,
                    'csv_file': 'Bill.csv',
                    'json_file': 'bills.json',
                    'table_name': 'bills_canonical'
                }
            }
        }
    
    def get(self, *path, default=None) -> Any:
        """
        Get configuration value using dotted path notation.
        
        Args:
            *path: Path components (e.g., 'data_sources', 'csv_backup_path')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        current = self.config_data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_data_source_paths(self) -> Dict[str, str]:
        """
        Get all data source paths as absolute paths with dynamic resolution support.
        
        Special handling:
        - If csv_backup_path is 'LATEST', resolves to most recent timestamped directory in data/csv/
        - If json_api_path is 'LATEST', resolves to most recent timestamped directory in data/raw_json/
        """
        csv_path = self.get('data_sources', 'csv_backup_path')
        json_path = self.get('data_sources', 'json_api_path')
        db_path = self.get('data_sources', 'target_database')
        
        # Handle dynamic CSV path resolution
        if csv_path and csv_path.upper() == 'LATEST':
            logger.info("Resolving LATEST CSV backup path...")
            resolved_csv_path = _resolve_dynamic_path(csv_path, 'data/csv')
            if resolved_csv_path != 'data/csv':  # Only use if actually resolved
                csv_path = resolved_csv_path
                logger.info(f"Using latest CSV backup: {csv_path}")
            else:
                logger.warning("WARNING: Failed to resolve LATEST CSV path, using fallback")
                csv_path = "data/csv/Nangsel Pioneers_2025-06-22"  # Specific fallback
        
        # Handle dynamic JSON path resolution
        if json_path and json_path.upper() == 'LATEST':
            logger.info("Resolving LATEST JSON API path...")
            resolved_json_path = _resolve_dynamic_path(json_path, 'data/raw_json')
            if resolved_json_path != 'data/raw_json':  # Only use if actually resolved
                json_path = resolved_json_path
                logger.info(f"Using latest JSON data: {json_path}")
            else:
                logger.warning("WARNING: Failed to resolve LATEST JSON path, using fallback")
                json_path = "data/json"  # Fallback to default
        
        return {
            'csv_backup_path': str(Path(csv_path).resolve()) if csv_path else None,
            'json_api_path': str(Path(json_path).resolve()) if json_path else None,
            'target_database': str(Path(db_path).resolve()) if db_path else None
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return {
            'batch_size': self.get('processing', 'batch_size', default=1000),
            'validate_transformations': self.get('processing', 'validate_transformations', default=True),
            'create_backups': self.get('processing', 'create_backups', default=False),
            'show_progress': self.get('processing', 'show_progress', default=True)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': self.get('logging', 'level', default='INFO'),
            'file': self.get('logging', 'file', default='logs/bedrock_rebuild.log'),
            'console': self.get('logging', 'console', default=True)
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate critical configuration values.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        paths = self.get_data_source_paths()
        
        # Check if target database directory exists
        db_path = Path(paths['target_database'])
        if not db_path.parent.exists():
            logger.error(f"Target database directory does not exist: {db_path.parent}")
            return False
        
        # Check if CSV backup path exists
        if paths['csv_backup_path'] and not Path(paths['csv_backup_path']).exists():
            logger.warning(f"CSV backup path does not exist: {paths['csv_backup_path']}")
        
        # Check if JSON API path exists  
        if paths['json_api_path'] and not Path(paths['json_api_path']).exists():
            logger.warning(f"JSON API path does not exist: {paths['json_api_path']}")
        
        logger.info("Configuration validation completed")
        return True
    
    def _resolve_latest_json_path(self) -> Optional[str]:
        """
        Resolve 'LATEST' keyword to the most recent timestamped JSON directory.
        
        Scans for directories in data/raw_json/ with timestamp format YYYY-MM-DD_HH-MM-SS
        and returns the path to the most recent one.
        
        Returns:
            Path to latest timestamped directory, or None if none found
        """
        try:
            # Define the base directory to scan
            base_dir = Path("data") / "raw_json"
            
            if not base_dir.exists():
                logger.warning(f"JSON base directory does not exist: {base_dir}")
                return None
            
            # Find all directories with timestamp pattern
            timestamp_dirs = []
            timestamp_pattern = r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$'
            
            for item in base_dir.iterdir():
                if item.is_dir() and re.match(timestamp_pattern, item.name):
                    try:
                        # Parse timestamp from directory name
                        timestamp_str = item.name
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                        timestamp_dirs.append((timestamp, item))
                        logger.debug(f"Found timestamped directory: {item.name}")
                    except ValueError as e:
                        logger.debug(f"Skipping directory with invalid timestamp format: {item.name}")
                        continue
            
            if not timestamp_dirs:
                logger.warning(f"No timestamped directories found in {base_dir}")
                return None
            
            # Sort by timestamp and get the most recent
            timestamp_dirs.sort(key=lambda x: x[0], reverse=True)
            latest_dir = timestamp_dirs[0][1]
            
            logger.info(f"LATEST JSON path resolved to: {latest_dir}")
            return str(latest_dir)
            
        except Exception as e:
            logger.error(f"Failed to resolve LATEST JSON path: {e}")
            return None
    
# Global configuration instance
_config_manager = None

def get_config_manager(config_file_path: Optional[str] = None) -> ConfigurationManager:
    """
    Get global configuration manager instance.
    
    Args:
        config_file_path: Optional path to config file
        
    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_file_path)
    return _config_manager

def reload_config(config_file_path: Optional[str] = None) -> ConfigurationManager:
    """
    Reload configuration (useful for testing or config changes).
    
    Args:
        config_file_path: Optional path to config file
        
    Returns:
        New ConfigurationManager instance
    """
    global _config_manager
    _config_manager = ConfigurationManager(config_file_path)
    return _config_manager


# Legacy compatibility function
def load_settings():
    """Load settings from config/settings.yaml (legacy compatibility)"""
    config_manager = get_config_manager()
    return config_manager.config_data
