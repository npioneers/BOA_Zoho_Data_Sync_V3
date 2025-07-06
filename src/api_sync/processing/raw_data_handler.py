import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def save_raw_json(data: List[Dict[str, Any]], module_name: str, run_timestamp_str: str, output_base_dir: str = "data/raw_json"):
    """
    Saves the fetched raw data to a timestamped JSON file.

    Args:
        data: The list of records (as dicts) fetched from the API.
        module_name: The name of the Zoho module (e.g., 'invoices').
        run_timestamp_str: A string representing the current sync run's start time,
                             used for creating a unique folder.
        output_base_dir: Base directory for JSON output (default: data/raw_json)
    """
    if not data:
        logger.info(f"No new raw data to save for module '{module_name}'.")
        return

    try:
        # Define the path for the timestamped output directory
        output_dir = Path(output_base_dir) / run_timestamp_str
        
        # Create the directory if it doesn't exist
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified directory: {output_dir}")
        except OSError as dir_error:
            logger.error(f"Failed to create directory '{output_dir}': {dir_error}")
            return

        # Define the full path for the output file
        file_path = output_dir / f"{module_name}.json"

        logger.info(f"Saving {len(data)} raw records for '{module_name}' to {file_path}")

        # Write the data to the file with indentation for readability
        # Use context manager to ensure proper file closure
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Raw JSON saved for '{module_name}' successfully")
        except (IOError, OSError) as file_error:
            logger.error(f"Could not write file '{file_path}': {file_error}")
            return

    except Exception as e:
        logger.error(f"Could not write raw JSON file for '{module_name}': {e}")

def load_raw_json(module_name: str, timestamp_dir: str, data_base_dir: str = "data/raw_json") -> List[Dict[str, Any]]:
    """
    Loads raw JSON data from a timestamped directory.
    
    Args:
        module_name: The name of the Zoho module (e.g., 'invoices').
        timestamp_dir: The timestamp directory name.
        data_base_dir: Base directory for JSON data (default: data/raw_json)
        
    Returns:
        List of records from the JSON file, or empty list if file not found.
    """
    try:
        file_path = Path(data_base_dir) / timestamp_dir / f"{module_name}.json"
        
        if not file_path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.info(f"Loaded {len(data)} records for '{module_name}' from {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Failed to load JSON data for '{module_name}': {e}")
        return []

def get_latest_timestamp_dir(data_base_dir: str = "data/raw_json") -> str:
    """
    Gets the most recent timestamp directory.
    
    Args:
        data_base_dir: Base directory for JSON data (default: data/raw_json)
        
    Returns:
        Name of the latest timestamp directory, or empty string if none found.
    """
    try:
        base_path = Path(data_base_dir)
        if not base_path.exists():
            logger.warning(f"Base directory does not exist: {base_path}")
            return ""
        
        # Get all directories that match timestamp pattern
        timestamp_dirs = [d.name for d in base_path.iterdir() 
                         if d.is_dir() and len(d.name) >= 19]  # YYYY-MM-DD_HH-MM-SS format
        
        if not timestamp_dirs:
            logger.warning(f"No timestamp directories found in {base_path}")
            return ""
        
        # Sort and get the latest
        latest = sorted(timestamp_dirs)[-1]
        logger.info(f"Latest timestamp directory: {latest}")
        return latest
        
    except Exception as e:
        logger.error(f"Failed to get latest timestamp directory: {e}")
        return ""
