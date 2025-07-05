"""
Project Bedrock V2 - Modular Data Pipeline Package

This package provides a modular, production-ready data synchronization pipeline
with separated concerns for maintainability and scalability.

Core Components:
- BaseBuilder: Initial database population from CSV backup
- IncrementalUpdater: JSON API updates with UPSERT logic
- ConfigurationManager: Dynamic path resolution and environment overrides
- DatabaseHandler: Centralized database operations
- BillsTransformer: Dual-source data transformation

Architecture Principles:
- Configuration-driven (no hardcoded values)
- Modular design (separated concerns)
- Environment-aware (dev/staging/prod)
- Production-ready (error handling, logging, validation)
"""

# Core configuration and database components
from .config import ConfigurationManager, get_config_manager, reload_config
from .database import DatabaseHandler
from .transformer import BillsTransformer

# Modular pipeline components
from .base_builder import BaseBuilder, build_base_from_csv
from .incremental_updater import IncrementalUpdater, apply_json_updates

# Mapping configurations
from .mappings import CANONICAL_SCHEMA, get_entity_schema

__version__ = "2.0.0"
__author__ = "Bedrock Development Team"

# Package-level convenience exports
__all__ = [
    # Configuration
    'ConfigurationManager',
    'get_config_manager', 
    'reload_config',
    
    # Core components
    'DatabaseHandler',
    'BillsTransformer',
    'CANONICAL_BILLS_COLUMNS',
    
    # Modular pipeline
    'BaseBuilder',
    'build_base_from_csv',
    'IncrementalUpdater', 
    'apply_json_updates',
]

# Package-level logging configuration
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())