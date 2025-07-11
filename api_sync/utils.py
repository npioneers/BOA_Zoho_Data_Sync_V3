"""
Utility functions for API sync operations.

Handles timestamp formatting, auto-detection of latest sync data, 
and other common operations.
"""

import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

def is_timestamp_dir(dirname: str) -> bool:
    """
    Check if a directory name is a valid timestamp format (YYYY-MM-DD_HH-MM-SS).
    
    Args:
        dirname: Directory name to check
    
    Returns:
        True if the directory is a valid timestamp format
    """
    pattern = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"
    if not re.match(pattern, dirname):
        return False
    
    # Additional validation: check if the date/time values are actually valid
    try:
        # Extract components
        date_part, time_part = dirname.split('_')
        year, month, day = map(int, date_part.split('-'))
        hour, minute, second = map(int, time_part.split('-'))
        
        # Validate ranges
        if not (1 <= month <= 12):
            return False
        if not (1 <= day <= 31):
            return False
        if not (0 <= hour <= 23):
            return False
        if not (0 <= minute <= 59):
            return False
        if not (0 <= second <= 59):
            return False
        
        # Use datetime to validate the actual date
        from datetime import datetime
        datetime(year, month, day, hour, minute, second)
        return True
        
    except (ValueError, IndexError):
        return False

def dir_to_iso_timestamp(dirname: str) -> str:
    """
    Convert a directory name (YYYY-MM-DD_HH-MM-SS) to ISO timestamp format.
    
    Args:
        dirname: Directory name in timestamp format
    
    Returns:
        ISO format timestamp string
    """
    # Parse the directory name: YYYY-MM-DD_HH-MM-SS
    date_part, time_part = dirname.split("_")
    year, month, day = date_part.split("-")
    hour, minute, second = time_part.split("-")
    
    # Create ISO format: YYYY-MM-DDTHH:MM:SSZ
    iso_timestamp = f"{year}-{month}-{day}T{hour}:{minute}:{second}Z"
    return iso_timestamp

def get_latest_timestamp_dir(base_dir: str = None) -> Optional[str]:
    """
    Find the latest timestamp directory in the JSON base directory.
    
    Args:
        base_dir: Base directory to search in. If None, uses config value.
    
    Returns:
        Latest timestamp directory name or None if not found
    """
    # Determine the base directory
    if base_dir is None:
        # Try to get from config, otherwise use default
        try:
            from . import config
            base_dir = config.JSON_BASE_DIR
        except:
            base_dir = "data/raw_json"
    
    # Make path relative to project root (parent of api_sync)
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    full_base_dir = os.path.join(project_root, base_dir)
    
    if not os.path.exists(full_base_dir):
        return None
    
    timestamp_dirs = []
    for item in os.listdir(full_base_dir):
        item_path = os.path.join(full_base_dir, item)
        if os.path.isdir(item_path) and is_timestamp_dir(item):
            timestamp_dirs.append(item)
    
    if not timestamp_dirs:
        return None
    
    # Sort directories by timestamp (newest first)
    timestamp_dirs.sort(reverse=True)
    return timestamp_dirs[0]

def convert_to_zoho_timestamp(iso_timestamp: str) -> str:
    """
    Convert ISO timestamp to Zoho API format.
    
    Zoho expects timestamps in ISO format with UTC timezone: YYYY-MM-DDTHH:MM:SS+0000
    
    Args:
        iso_timestamp: ISO format timestamp (e.g., 2025-07-01T00:00:00+00:00 or 2025-07-01)
        
    Returns:
        Zoho-formatted timestamp string (ISO with UTC timezone)
    """
    try:
        # Handle date-only format (YYYY-MM-DD)
        if 'T' not in iso_timestamp:
            # Add midnight time for date-only input
            iso_timestamp = f"{iso_timestamp}T00:00:00"
        
        # Parse the ISO timestamp
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        
        # Convert to UTC if it has timezone info
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Format for Zoho API: ISO format with UTC timezone
        zoho_format = dt.strftime('%Y-%m-%dT%H:%M:%S+0000')
        logger.debug(f"Converted {iso_timestamp} to Zoho format: {zoho_format}")
        return zoho_format
        
    except Exception as e:
        logger.error(f"Failed to convert timestamp {iso_timestamp}: {e}")
        raise ValueError(f"Invalid timestamp format: {iso_timestamp}")

def get_latest_sync_timestamp(json_base_dir: str = None) -> Optional[str]:
    """
    Auto-detect the latest sync timestamp from raw JSON directories.
    
    Looks for timestamped directories (YYYY-MM-DD_HH-MM-SS) and finds
    the most recent one to determine the last sync time.
    
    Excludes test directories (TEST_, CONSOLIDATED_, or year 9999)
    
    Args:
        json_base_dir: Base directory containing timestamped JSON folders.
                      If None, uses config value or default relative path.
        
    Returns:
        ISO timestamp string of the latest sync, or None if no data found
    """
    try:
        # Determine the base directory
        if json_base_dir is None:
            # Try to get from config, otherwise use default
            try:
                from . import config
                json_base_dir = config.JSON_BASE_DIR
            except:
                json_base_dir = "data/raw_json"
        
        # Make path relative to project root (parent of api_sync)
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        json_path = Path(project_root) / json_base_dir
        
        if not json_path.exists():
            logger.warning(f"JSON base directory not found: {json_path}")
            return None
        
        # Pattern to match timestamped directories: YYYY-MM-DD_HH-MM-SS
        timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})')
        
        latest_timestamp = None
        latest_datetime = None
        
        for item in json_path.iterdir():
            if item.is_dir():
                # Skip test directories and far-future dates
                if (item.name.startswith('TEST_') or 
                    item.name.startswith('CONSOLIDATED_') or
                    item.name.startswith('9999-')):
                    logger.debug(f"Skipping test/special directory: {item.name}")
                    continue
                
                match = timestamp_pattern.search(item.name)
                if match:
                    timestamp_str = match.group(1)
                    try:
                        # Convert to datetime for comparison
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                        
                        # Skip far-future dates (likely test data)
                        if dt.year >= 9999:
                            logger.debug(f"Skipping far-future timestamp: {timestamp_str}")
                            continue
                        
                        if latest_datetime is None or dt > latest_datetime:
                            latest_datetime = dt
                            latest_timestamp = timestamp_str
                            
                    except ValueError:
                        logger.debug(f"Skipping invalid timestamp format: {timestamp_str}")
                        continue
        
        if latest_timestamp:
            # Convert to ISO format for API use
            iso_timestamp = latest_datetime.isoformat() + '+00:00'
            logger.info(f"Latest sync detected: {latest_timestamp} -> {iso_timestamp}")
            return iso_timestamp
        else:
            logger.info("No previous sync data found in raw_json directory")
            return None
            
    except Exception as e:
        logger.error(f"Failed to detect latest sync timestamp: {e}")
        return None

def get_sync_info(json_base_dir: str = "data/raw_json") -> Tuple[Optional[str], int]:
    """
    Get sync information including latest timestamp and directory count.
    
    Args:
        json_base_dir: Base directory containing timestamped JSON folders
        
    Returns:
        Tuple of (latest_iso_timestamp, directory_count)
    """
    try:
        json_path = Path(json_base_dir)
        if not json_path.exists():
            return None, 0
        
        timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})')
        directories = [
            item for item in json_path.iterdir() 
            if item.is_dir() and timestamp_pattern.search(item.name)
        ]
        
        latest_timestamp = get_latest_sync_timestamp(json_base_dir)
        return latest_timestamp, len(directories)
        
    except Exception as e:
        logger.error(f"Failed to get sync info: {e}")
        return None, 0

def ensure_zoho_timestamp_format(timestamp: Optional[str]) -> Optional[str]:
    """
    Ensure timestamp is in proper Zoho API format.
    
    Args:
        timestamp: Input timestamp (ISO format or None)
        
    Returns:
        Zoho-formatted timestamp or None
    """
    if not timestamp or timestamp.lower() == "none":
        return None
        
    try:
        return convert_to_zoho_timestamp(timestamp)
    except Exception as e:
        logger.warning(f"Failed to convert timestamp '{timestamp}': {e}")
        return None

def check_comprehensive_data_availability(modules_to_check: list = None) -> Tuple[bool, list]:
    """
    Check if comprehensive data is available for modules with line items.
    
    This function checks for comprehensive (bulk) data in JSON storage for modules that have line items.
    If comprehensive data is not found, those modules will require individual API calls for each record,
    which can be slow for large datasets.
    
    Args:
        modules_to_check: List of module names to check. If None, checks all modules with line items.
        
    Returns:
        Tuple of (has_comprehensive_data: bool, missing_modules: list)
        - has_comprehensive_data: True if comprehensive data exists for all checked modules
        - missing_modules: List of modules that don't have comprehensive data
    """
    from .config import get_config
    
    # Define modules with line items (same as in client.py)
    MODULES_WITH_LINE_ITEMS = {
        'invoices': 'invoice_id',
        'bills': 'bill_id', 
        'salesorders': 'salesorder_id',
        'purchaseorders': 'purchaseorder_id',
        'creditnotes': 'creditnote_id'
    }
    
    if modules_to_check is None:
        modules_to_check = list(MODULES_WITH_LINE_ITEMS.keys())
    
    # Filter to only check modules that actually have line items
    modules_to_check = [m for m in modules_to_check if m in MODULES_WITH_LINE_ITEMS]
    
    if not modules_to_check:
        logger.info("No modules with line items to check")
        return True, []
    
    config = get_config()
    json_base_dir = config.json_base_dir
    org_id = config.default_organization_id
    
    missing_modules = []
    
    logger.info(f"Checking comprehensive data availability for modules: {modules_to_check}")
    
    for module in modules_to_check:
        has_comprehensive = False
        
        # Check timestamped directories first (highest priority)
        timestamped_path = Path(json_base_dir) / org_id / "timestamped"
        if timestamped_path.exists():
            for sync_dir in sorted(timestamped_path.iterdir(), reverse=True):
                if sync_dir.is_dir() and is_timestamp_dir(sync_dir.name):
                    module_file = sync_dir / f"{module}.json"
                    if module_file.exists():
                        try:
                            import json
                            with open(module_file, 'r') as f:
                                data = json.load(f)
                                # Check if this is comprehensive data (has bulk records)
                                if isinstance(data, list) and len(data) > 0:
                                    # Check if records have line items populated
                                    sample_record = data[0]
                                    if isinstance(sample_record, dict) and 'line_items' in sample_record:
                                        line_items = sample_record.get('line_items', [])
                                        if isinstance(line_items, list) and len(line_items) > 0:
                                            logger.info(f"✅ Found comprehensive data for {module} in {sync_dir.name}")
                                            has_comprehensive = True
                                            break
                        except Exception as e:
                            logger.warning(f"Error checking {module_file}: {e}")
                            continue
        
        # Check consolidated directory if not found in timestamped
        if not has_comprehensive:
            consolidated_path = Path(json_base_dir) / org_id / "consolidated" / f"{module}.json"
            if consolidated_path.exists():
                try:
                    import json
                    with open(consolidated_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            sample_record = data[0]
                            if isinstance(sample_record, dict) and 'line_items' in sample_record:
                                line_items = sample_record.get('line_items', [])
                                if isinstance(line_items, list) and len(line_items) > 0:
                                    logger.info(f"✅ Found comprehensive data for {module} in consolidated")
                                    has_comprehensive = True
                except Exception as e:
                    logger.warning(f"Error checking consolidated {module}: {e}")
        
        if not has_comprehensive:
            logger.warning(f"❌ No comprehensive data found for {module}")
            missing_modules.append(module)
        
    has_all_comprehensive = len(missing_modules) == 0
    
    if has_all_comprehensive:
        logger.info("✅ Comprehensive data available for all checked modules")
    else:
        logger.warning(f"⚠️  Missing comprehensive data for: {', '.join(missing_modules)}")
    
    return has_all_comprehensive, missing_modules
