"""
API Sync Configuration Management

Handles configuration for API sync operations with support for environment variables
and default settings.
"""

import os
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ApiSyncConfig:
    """Configuration settings for API sync operations."""
    
    # API Settings
    api_base_url: str = "https://www.zohoapis.com/books/v3"
    
    # Data Storage
    json_base_dir: str = "data/raw_json"
    
    # Authentication
    gcp_project_id: str = ""
    
    # Request Settings
    request_timeout: int = 300
    retry_count: int = 3
    rate_limit_delay: float = 1.2
    
    # Logging
    log_level: str = "INFO"
    
    # Fetch Filters
    default_organization_id: str = "806931205"
    excluded_modules: list = None  # Will be set to ["organizations"] in post_init
    
    # Line Items Fetch Behavior
    prompt_for_line_items_date: bool = True  # Prompt user for date when no comprehensive data found
    
    def __post_init__(self):
        """Initialize default excluded modules if not set."""
        if self.excluded_modules is None:
            self.excluded_modules = ["organizations"]

# Read configuration from environment variables
# Google Cloud Project ID - Required for Secret Manager
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")

# Zoho Organization ID - Optional, can be specified per request
ZOHO_ORGANIZATION_ID = os.getenv("ZOHO_ORGANIZATION_ID", "806931205")

# Base directory for storing JSON data
JSON_BASE_DIR = os.getenv("JSON_BASE_DIR", "data/raw_json")

# Fetch behavior configuration
DEFAULT_ORGANIZATION_ID = os.getenv("DEFAULT_ORGANIZATION_ID", "806931205")
EXCLUDED_MODULES = os.getenv("EXCLUDED_MODULES", "organizations").split(",") if os.getenv("EXCLUDED_MODULES") else ["organizations"]

def get_config() -> ApiSyncConfig:
    """
    Get configuration from environment variables with fallbacks to defaults.
    
    Returns:
        ApiSyncConfig object with configuration values
    """
    config = ApiSyncConfig()
    
    # Set values from environment variables
    config.gcp_project_id = GCP_PROJECT_ID
    config.json_base_dir = JSON_BASE_DIR
    config.default_organization_id = DEFAULT_ORGANIZATION_ID
    config.excluded_modules = EXCLUDED_MODULES.copy()  # Make a copy to avoid mutation
    
    logger.debug(f"Loaded configuration: {config}")
    return config

def get_supported_modules() -> Dict[str, str]:
    """
    Get list of supported Zoho modules with descriptions.
    
    Returns:
        Dictionary mapping module names to descriptions
    """
    return {
        "invoices": "Customer invoices and billing documents",
        "items": "Inventory items and product catalog", 
        "contacts": "Customer and vendor contact information",
        "customerpayments": "Customer payment records",
        "bills": "Vendor bills and purchase documents",
        "vendorpayments": "Vendor payment records",
        "salesorders": "Sales order documents",
        "purchaseorders": "Purchase order documents", 
        "creditnotes": "Credit note documents",
        "organizations": "Organization settings and information"
    }

def validate_module(module_name: str) -> bool:
    """
    Validate if a module name is supported.
    
    Args:
        module_name: Name of the module to validate
        
    Returns:
        True if module is supported, False otherwise
    """
    return module_name in get_supported_modules()

def get_fetchable_modules(exclude_list: list = None) -> Dict[str, str]:
    """
    Get list of modules that should be fetched by default.
    
    Args:
        exclude_list: Optional list of modules to exclude. If None, uses config default.
        
    Returns:
        Dictionary mapping module names to descriptions (filtered)
    """
    if exclude_list is None:
        config = get_config()
        exclude_list = config.excluded_modules
    
    all_modules = get_supported_modules()
    return {name: desc for name, desc in all_modules.items() if name not in exclude_list}

def should_fetch_module(module_name: str, exclude_list: list = None) -> bool:
    """
    Check if a module should be fetched based on exclusion rules.
    
    Args:
        module_name: Name of the module to check
        exclude_list: Optional list of excluded modules. If None, uses config default.
        
    Returns:
        True if module should be fetched, False otherwise
    """
    if exclude_list is None:
        config = get_config()
        exclude_list = config.excluded_modules
    
    return validate_module(module_name) and module_name not in exclude_list

def print_config_info(config: ApiSyncConfig) -> None:
    """
    Print configuration information.
    
    Args:
        config: Configuration instance to display
    """
    print("🔧 API SYNC CONFIGURATION")
    print("=" * 50)
    print(f"📊 API Base URL: {config.api_base_url}")
    print(f"📁 JSON Base Dir: {config.json_base_dir}")
    print(f"🔐 GCP Project ID: {config.gcp_project_id or 'Not set'}")
    print(f"🏢 Default Org ID: {config.default_organization_id}")
    print(f"🚫 Excluded Modules: {', '.join(config.excluded_modules)}")
    print(f"⏱️  Request Timeout: {config.request_timeout}s")
    print(f"🔁 Retry Count: {config.retry_count}")
    print(f"💤 Rate Limit Delay: {config.rate_limit_delay}s")
    print(f"📝 Log Level: {config.log_level}")
    print(f"📅 Prompt for Line Items Date: {config.prompt_for_line_items_date}")
    print("=" * 50)


# Create default configuration instance
_default_config = get_config()

# Export commonly used values as module-level constants for backward compatibility
JSON_BASE_DIR = _default_config.json_base_dir
SUPPORTED_MODULES = get_supported_modules()
FETCHABLE_MODULES = get_fetchable_modules()
GCP_PROJECT_ID = _default_config.gcp_project_id
DEFAULT_ORGANIZATION_ID = _default_config.default_organization_id
EXCLUDED_MODULES = _default_config.excluded_modules
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
API_BASE_URL = _default_config.api_base_url
REQUEST_TIMEOUT = _default_config.request_timeout
RETRY_COUNT = _default_config.retry_count

def get_api_filter_supported_modules() -> Dict[str, bool]:
    """
    Get mapping of which modules support API-side last_modified_time filtering.
    
    🎉 BREAKTHROUGH: All modules now confirmed to support API-side filtering!
    
    Returns:
        Dictionary mapping module names to filtering support status
    """
    return {
        "invoices": True,        # ✅ Confirmed July 2025
        "items": True,           # ✅ Confirmed July 2025
        "contacts": True,        # ✅ Confirmed July 2025
        "customerpayments": True, # ✅ Confirmed July 2025
        "bills": True,           # ✅ Confirmed July 2025
        "vendorpayments": True,  # ✅ Confirmed July 2025
        "salesorders": True,     # ✅ Confirmed July 2025
        "purchaseorders": True,  # ✅ Confirmed July 2025
        "creditnotes": True,     # ✅ Confirmed July 2025
        "organizations": False   # Special endpoint, doesn't support filtering
    }

def supports_api_filtering(module_name: str) -> bool:
    """
    Check if a module supports API-side last_modified_time filtering.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        True if module supports API-side filtering, False otherwise
    """
    return get_api_filter_supported_modules().get(module_name, False)
