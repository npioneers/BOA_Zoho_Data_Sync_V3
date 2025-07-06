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

def convert_to_zoho_timestamp(iso_timestamp: str) -> str:
    """
    Convert ISO timestamp to Zoho API format.
    
    Zoho expects timestamps in format: YYYY-MM-DD HH:MM:SS (MySQL datetime format)
    
    Args:
        iso_timestamp: ISO format timestamp (e.g., 2025-07-01T00:00:00+00:00)
        
    Returns:
        Zoho-formatted timestamp string (MySQL datetime format)
    """
    try:
        # Parse the ISO timestamp
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        
        # Convert to UTC if it has timezone info
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Use MySQL datetime format which many APIs expect
        mysql_format = dt.strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"Converted {iso_timestamp} to Zoho MySQL format: {mysql_format}")
        return mysql_format
        
    except Exception as e:
        logger.error(f"Failed to convert timestamp {iso_timestamp}: {e}")
        raise ValueError(f"Invalid timestamp format: {iso_timestamp}")

def get_latest_sync_timestamp(json_base_dir: str = "data/raw_json") -> Optional[str]:
    """
    Auto-detect the latest sync timestamp from raw JSON directories.
    
    Looks for timestamped directories (YYYY-MM-DD_HH-MM-SS) and finds
    the most recent one to determine the last sync time.
    
    Args:
        json_base_dir: Base directory containing timestamped JSON folders
        
    Returns:
        ISO timestamp string of the latest sync, or None if no data found
    """
    try:
        json_path = Path(json_base_dir)
        if not json_path.exists():
            logger.warning(f"JSON base directory not found: {json_base_dir}")
            return None
        
        # Pattern to match timestamped directories: YYYY-MM-DD_HH-MM-SS
        timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})')
        
        latest_timestamp = None
        latest_datetime = None
        
        for item in json_path.iterdir():
            if item.is_dir():
                match = timestamp_pattern.search(item.name)
                if match:
                    timestamp_str = match.group(1)
                    try:
                        # Convert to datetime for comparison
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                        
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
