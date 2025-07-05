"""
JSON Differential Sync Package

Independent JSON-to-database synchronization system that operates
separately from the CSV-to-DB pipeline.
"""

from .config import get_config, get_config_manager, JsonSyncConfig, JsonSyncConfigManager
from .json_loader import JsonDataLoader
from .json_comparator import JsonDatabaseComparator  
from .json_sync_engine import JsonSyncEngine
from .json_mappings import JSON_ENTITY_MAPPINGS
from .orchestrator import JsonDifferentialSyncOrchestrator
from .convenience import (
    quick_json_sync,
    analyze_json_differences,
    sync_specific_entities,
    load_latest_json_data,
    compare_json_with_database,
    get_sync_status,
    create_json_sync_config_template,
    run_incremental_sync,
    get_sync_cockpit_status,
    print_cockpit_banner,
    format_sync_results
)

__all__ = [
    # Configuration
    'get_config',
    'get_config_manager', 
    'JsonSyncConfig',
    'JsonSyncConfigManager',
    
    # Core modules
    'JsonDataLoader',
    'JsonDatabaseComparator', 
    'JsonSyncEngine',
    'JSON_ENTITY_MAPPINGS',
    'JsonDifferentialSyncOrchestrator',
    
    # Convenience functions
    'quick_json_sync',
    'analyze_json_differences', 
    'sync_specific_entities',
    'load_latest_json_data',
    'compare_json_with_database',
    'get_sync_status',
    'create_json_sync_config_template',
    'run_incremental_sync',
    'get_sync_cockpit_status',
    'print_cockpit_banner',
    'format_sync_results'
]

__version__ = '1.1.0'
