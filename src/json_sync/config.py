"""
JSON Sync Configuration Management

Independent configuration system for JSON differential sync operations.
Supports environment variables, config files, and sensible defaults.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class JsonSyncConfig:
    """Configuration settings for JSON differential sync operations."""
    
    # Database Configuration
    database_path: str = "data/database/production.db"
    
    # JSON Data Configuration  
    json_base_path: str = "data/raw_json"
    json_path_pattern: str = "%Y-%m-%d_%H-%M-%S"
    
    # Sync Behavior Configuration
    conflict_resolution: str = "json_wins"  # json_wins, db_wins, manual
    dry_run: bool = True
    batch_size: int = 1000
    max_retries: int = 3
    timeout_seconds: int = 300
    
    # Entity Configuration
    enabled_entities: Optional[List[str]] = None  # None = all entities
    entity_priority: List[str] = None  # Sync order priority
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    verbose_logging: bool = False
    
    # Performance Configuration
    parallel_processing: bool = False
    max_workers: int = 4
    memory_limit_mb: int = 512
    
    # Validation Configuration
    validate_mappings: bool = True
    strict_validation: bool = False
    skip_invalid_records: bool = True
    
    # Backup Configuration
    backup_before_sync: bool = True
    backup_directory: str = "data/database/backups"
    max_backups: int = 10

class JsonSyncConfigManager:
    """
    Manages configuration for JSON sync operations.
    
    Features:
    - Environment variable support
    - YAML configuration file support
    - Hierarchical configuration loading
    - Configuration validation
    - Default value management
    """
    
    def __init__(self, config_file: Optional[str] = None, env_prefix: str = "JSON_SYNC"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to YAML configuration file
            env_prefix: Prefix for environment variables
        """
        self.config_file = config_file
        self.env_prefix = env_prefix
        self.config = self._load_configuration()
        
    def _load_configuration(self) -> JsonSyncConfig:
        """
        Load configuration from multiple sources with precedence:
        1. Environment variables (highest priority)
        2. Configuration file 
        3. Default values (lowest priority)
        
        Returns:
            Loaded and validated configuration
        """
        # Start with defaults
        config_dict = self._get_default_config()
        
        # Override with config file if exists
        if self.config_file and Path(self.config_file).exists():
            file_config = self._load_config_file()
            config_dict.update(file_config)
            logger.info(f"Loaded configuration from file: {self.config_file}")
        
        # Override with environment variables
        env_config = self._load_env_config()
        config_dict.update(env_config)
        
        # Create and validate configuration object
        config = JsonSyncConfig(**config_dict)
        self._validate_configuration(config)
        
        logger.info("JSON sync configuration loaded successfully")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'database_path': "data/database/production.db",
            'json_base_path': "data/raw_json",
            'json_path_pattern': "%Y-%m-%d_%H-%M-%S",
            'conflict_resolution': "json_wins",
            'dry_run': True,
            'batch_size': 1000,
            'max_retries': 3,
            'timeout_seconds': 300,
            'enabled_entities': None,
            'entity_priority': ["items", "contacts", "invoices", "bills", "salesorders", "purchaseorders", "customerpayments", "vendorpayments"],
            'log_level': "INFO",
            'log_file': None,
            'verbose_logging': False,
            'parallel_processing': False,
            'max_workers': 4,
            'memory_limit_mb': 512,
            'validate_mappings': True,
            'strict_validation': False,
            'skip_invalid_records': True,
            'backup_before_sync': True,
            'backup_directory': "data/database/backups",
            'max_backups': 10
        }
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            return config.get('json_sync', config)
        except Exception as e:
            logger.warning(f"Failed to load config file {self.config_file}: {e}")
            return {}
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Define environment variable mappings
        env_mappings = {
            f"{self.env_prefix}_DATABASE_PATH": 'database_path',
            f"{self.env_prefix}_JSON_BASE_PATH": 'json_base_path',
            f"{self.env_prefix}_JSON_PATH_PATTERN": 'json_path_pattern',
            f"{self.env_prefix}_CONFLICT_RESOLUTION": 'conflict_resolution',
            f"{self.env_prefix}_DRY_RUN": 'dry_run',
            f"{self.env_prefix}_BATCH_SIZE": 'batch_size',
            f"{self.env_prefix}_MAX_RETRIES": 'max_retries',
            f"{self.env_prefix}_TIMEOUT_SECONDS": 'timeout_seconds',
            f"{self.env_prefix}_ENABLED_ENTITIES": 'enabled_entities',
            f"{self.env_prefix}_LOG_LEVEL": 'log_level',
            f"{self.env_prefix}_LOG_FILE": 'log_file',
            f"{self.env_prefix}_VERBOSE_LOGGING": 'verbose_logging',
            f"{self.env_prefix}_PARALLEL_PROCESSING": 'parallel_processing',
            f"{self.env_prefix}_MAX_WORKERS": 'max_workers',
            f"{self.env_prefix}_MEMORY_LIMIT_MB": 'memory_limit_mb',
            f"{self.env_prefix}_VALIDATE_MAPPINGS": 'validate_mappings',
            f"{self.env_prefix}_STRICT_VALIDATION": 'strict_validation',
            f"{self.env_prefix}_SKIP_INVALID_RECORDS": 'skip_invalid_records',
            f"{self.env_prefix}_BACKUP_BEFORE_SYNC": 'backup_before_sync',
            f"{self.env_prefix}_BACKUP_DIRECTORY": 'backup_directory',
            f"{self.env_prefix}_MAX_BACKUPS": 'max_backups'
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if config_key in ['dry_run', 'verbose_logging', 'parallel_processing', 
                                'validate_mappings', 'strict_validation', 'skip_invalid_records', 
                                'backup_before_sync']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif config_key in ['batch_size', 'max_retries', 'timeout_seconds', 
                                  'max_workers', 'memory_limit_mb', 'max_backups']:
                    value = int(value)
                elif config_key == 'enabled_entities' and value:
                    value = [entity.strip() for entity in value.split(',')]
                
                env_config[config_key] = value
                logger.debug(f"Loaded environment config: {config_key}={value}")
        
        return env_config
    
    def _validate_configuration(self, config: JsonSyncConfig) -> None:
        """
        Validate configuration settings.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate conflict resolution strategy
        valid_strategies = ['json_wins', 'db_wins', 'manual']
        if config.conflict_resolution not in valid_strategies:
            raise ValueError(f"Invalid conflict_resolution: {config.conflict_resolution}. Must be one of: {valid_strategies}")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log_level: {config.log_level}. Must be one of: {valid_log_levels}")
        
        # Validate numeric ranges
        if config.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if config.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if config.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if config.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")
        if config.max_backups < 0:
            raise ValueError("max_backups must be non-negative")
        
        logger.debug("Configuration validation passed")
    
    def get_config(self) -> JsonSyncConfig:
        """Get the loaded configuration."""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration with new values.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated configuration: {key}={value}")
            else:
                logger.warning(f"Unknown configuration parameter: {key}")
        
        # Re-validate after updates
        self._validate_configuration(self.config)
    
    def save_config(self, output_file: str) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            output_file: Path to output configuration file
        """
        config_dict = {
            'json_sync': {
                'database_path': self.config.database_path,
                'json_base_path': self.config.json_base_path,
                'json_path_pattern': self.config.json_path_pattern,
                'conflict_resolution': self.config.conflict_resolution,
                'dry_run': self.config.dry_run,
                'batch_size': self.config.batch_size,
                'max_retries': self.config.max_retries,
                'timeout_seconds': self.config.timeout_seconds,
                'enabled_entities': self.config.enabled_entities,
                'entity_priority': self.config.entity_priority,
                'log_level': self.config.log_level,
                'log_file': self.config.log_file,
                'verbose_logging': self.config.verbose_logging,
                'parallel_processing': self.config.parallel_processing,
                'max_workers': self.config.max_workers,
                'memory_limit_mb': self.config.memory_limit_mb,
                'validate_mappings': self.config.validate_mappings,
                'strict_validation': self.config.strict_validation,
                'skip_invalid_records': self.config.skip_invalid_records,
                'backup_before_sync': self.config.backup_before_sync,
                'backup_directory': self.config.backup_directory,
                'max_backups': self.config.max_backups
            }
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to: {output_file}")
    
    def print_config(self) -> None:
        """Print current configuration in a readable format."""
        print("\n🔧 JSON SYNC CONFIGURATION")
        print("=" * 50)
        print(f"📊 Database Path: {self.config.database_path}")
        print(f"📁 JSON Base Path: {self.config.json_base_path}")
        print(f"🔄 Conflict Resolution: {self.config.conflict_resolution}")
        print(f"🧪 Dry Run: {self.config.dry_run}")
        print(f"📦 Batch Size: {self.config.batch_size}")
        print(f"🔁 Max Retries: {self.config.max_retries}")
        print(f"⏱️  Timeout: {self.config.timeout_seconds}s")
        print(f"📋 Enabled Entities: {self.config.enabled_entities or 'All'}")
        print(f"📝 Log Level: {self.config.log_level}")
        print(f"🔧 Parallel Processing: {self.config.parallel_processing}")
        print(f"💾 Backup Before Sync: {self.config.backup_before_sync}")
        print("=" * 50)

# Global configuration instance
_config_manager = None

def get_config_manager(config_file: Optional[str] = None, 
                      env_prefix: str = "JSON_SYNC") -> JsonSyncConfigManager:
    """
    Get or create the global configuration manager.
    
    Args:
        config_file: Path to configuration file
        env_prefix: Environment variable prefix
        
    Returns:
        Configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = JsonSyncConfigManager(config_file, env_prefix)
    return _config_manager

def get_config() -> JsonSyncConfig:
    """
    Get the current JSON sync configuration.
    
    Returns:
        Current configuration object
    """
    return get_config_manager().get_config()

def reset_config() -> None:
    """Reset the global configuration manager."""
    global _config_manager
    _config_manager = None
