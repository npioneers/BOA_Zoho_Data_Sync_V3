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

def get_config() -> ApiSyncConfig:
    """
    Get API sync configuration with environment variable overrides.
    
    Returns:
        ApiSyncConfig instance with current settings
    """
    config = ApiSyncConfig()
    
    # Override with environment variables if available
    config.api_base_url = os.getenv("ZOHO_API_BASE_URL", config.api_base_url)
    config.json_base_dir = os.getenv("JSON_BASE_DIR", config.json_base_dir)
    config.gcp_project_id = os.getenv("GCP_PROJECT_ID", config.gcp_project_id)
    config.request_timeout = int(os.getenv("API_REQUEST_TIMEOUT", str(config.request_timeout)))
    config.retry_count = int(os.getenv("API_RETRY_COUNT", str(config.retry_count)))
    config.rate_limit_delay = float(os.getenv("API_RATE_LIMIT_DELAY", str(config.rate_limit_delay)))
    config.log_level = os.getenv("LOG_LEVEL", config.log_level)
    
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
    print(f"⏱️  Request Timeout: {config.request_timeout}s")
    print(f"🔁 Retry Count: {config.retry_count}")
    print(f"💤 Rate Limit Delay: {config.rate_limit_delay}s")
    print(f"📝 Log Level: {config.log_level}")
    print("=" * 50)
