"""
Global Zoho Data Sync Configuration
Centralized configuration management for orch                "date_column_mapping": {
                    "json_invoices": "last_modified_time",
                    "json_bills": "last_modified_time",
                    "json_customer_payments": "date",
                    "json_vendor_payments": "date", 
                    "json_sales_orders": "last_modified_time",
                    "json_purchase_orders": "last_modified_time",
                    "json_credit_notes": "last_modified_time",
                    "json_items": "last_modified_time",
                    "json_contacts": "last_modified_time"
                }pi_sync, json2db_sync, and csv_db_rebuild packages.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime


class GlobalSyncConfig:
    """Centralized configuration for global Zoho data sync operations"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config = {}
        self._load_configuration()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            # Global system configuration
            "system": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "description": "Global Zoho Data Sync System Configuration",
                "log_level": "INFO"
            },
            
            # Database configuration (shared across all packages)
            "database": {
                "path": "../data/database/production.db",
                "backup_before_operations": True,
                "connection_timeout": 30,
                "enable_wal_mode": True
            },
            
            # Package paths and configurations
            "packages": {
                "api_sync": {
                    "path": "../api_sync",
                    "enabled": True,
                    "runner_module": "runner_api_sync",
                    "config_path": "../api_sync/config.py",
                    "data_output_path": "../api_sync/data/sync_sessions"
                },
                "json2db_sync": {
                    "path": "../json2db_sync", 
                    "enabled": True,
                    "runner_module": "runner_json2db_sync",
                    "config_path": "../json2db_sync/config.py",
                    "data_source_path": "../api_sync/data/sync_sessions"
                },
                "csv_db_rebuild": {
                    "path": "../csv_db_rebuild",
                    "enabled": True,
                    "runner_module": "runner_csv_db_rebuild", 
                    "config_path": None,  # Uses direct initialization
                    "csv_data_path": "../data/csv/Nangsel Pioneers_Latest"
                }
            },
            
            # Sync pipeline configuration
            "sync_pipeline": {
                "default_cutoff_days": 30,
                "enable_freshness_check": True,
                "freshness_threshold_days": 1,
                "auto_backup_before_sync": True,
                "verify_integrity_after_sync": True,
                "cleanup_old_sessions": False,
                "max_sessions_to_keep": 10
            },
            
            # Freshness monitoring configuration
            "freshness": {
                "check_tables": [
                    "json_invoices",
                    "json_bills", 
                    "json_items",
                    "json_contacts",
                    "json_customer_payments",
                    "json_vendor_payments",
                    "json_sales_orders",
                    "json_purchase_orders",
                    "json_credit_notes"
                ],
                "date_columns": {
                    "json_invoices": "last_modified_time",
                    "json_bills": "last_modified_time",
                    "json_customer_payments": "date",
                    "json_vendor_payments": "date", 
                    "json_sales_orders": "last_modified_time",
                    "json_purchase_orders": "last_modified_time",
                    "json_credit_notes": "last_modified_time",
                    "json_items": "last_modified_time",
                    "json_contacts": "last_modified_time"
                }
            },
            
            # Logging configuration
            "logging": {
                "enabled": True,
                "log_dir": "../logs",
                "global_log_file": "global_sync.log",
                "session_logs": True,
                "detailed_logging": True,
                "max_log_size_mb": 10,
                "backup_count": 5
            },
            
            # Session management
            "session": {
                "create_session_folders": True,
                "session_name_format": "global_sync_{timestamp}",
                "include_package_results": True,
                "generate_consolidated_report": True
            },
            
            # User interface configuration
            "ui": {
                "auto_freshness_check_on_startup": True,
                "confirm_destructive_operations": True,
                "show_progress_indicators": True,
                "detailed_error_messages": True,
                "menu_timeout_seconds": 300
            }
        }
    
    def _load_configuration(self) -> None:
        """Load configuration from file or use defaults"""
        self._config = self._get_default_config()
        
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self._merge_config(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
                print("Using default configuration")
    
    def _merge_config(self, file_config: Dict[str, Any]) -> None:
        """Recursively merge file configuration with defaults"""
        def merge_dicts(default: dict, override: dict) -> dict:
            result = default.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        self._config = merge_dicts(self._config, file_config)
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        output_file = output_path or self.config_file or "global_sync_config.json"
        
        # Update timestamp
        self._config["system"]["last_updated"] = datetime.now().isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(self._config, f, indent=4, sort_keys=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'database.path')"""
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_package_config(self, package_name: str) -> Dict[str, Any]:
        """Get configuration for a specific package"""
        return self.get(f'packages.{package_name}', {})
    
    def is_package_enabled(self, package_name: str) -> bool:
        """Check if a package is enabled"""
        return self.get(f'packages.{package_name}.enabled', False)
    
    def get_database_path(self) -> str:
        """Get the database path"""
        return self.get('database.path')
    
    def get_freshness_tables(self) -> list:
        """Get list of tables to check for freshness"""
        return self.get('freshness.check_tables', [])
    
    def get_date_column_for_table(self, table_name: str) -> Optional[str]:
        """Get the date column for freshness checking for a specific table"""
        return self.get(f'freshness.date_columns.{table_name}')
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return json.dumps(self._config, indent=2)


# Global configuration instance
global_config = GlobalSyncConfig()
