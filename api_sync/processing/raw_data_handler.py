import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def _create_sync_metadata(output_dir: Path, module_name: str, record_count: int, is_temp: bool = False):
    """
    Creates sync metadata file to track sync completion and results.
    
    Args:
        output_dir: Directory where metadata should be saved
        module_name: Name of the module that was synced
        record_count: Number of records found (0 for empty results)
        is_temp: Whether this is in a temporary directory (sync in progress)
    """
    try:
        metadata = {
            "sync_timestamp": datetime.now().isoformat(),
            "module": module_name,
            "records_found": record_count,
            "sync_completed": not is_temp,  # Only true for finalized syncs
            "is_temporary": is_temp,
            "has_data": record_count > 0
        }
        
        metadata_file = output_dir / f"sync_metadata_{module_name}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        logger.debug(f"Created sync metadata: {metadata_file} (temp: {is_temp})")
        
    except Exception as e:
        logger.warning(f"Failed to create sync metadata for {module_name}: {e}")
        # Don't fail the sync if metadata creation fails

def save_raw_json_temp(data: List[Dict[str, Any]], module_name: str, run_timestamp_str: str, output_base_dir: str = "data/raw_json"):
    """
    Saves raw data to a TEMPORARY directory during sync.
    
    This prevents timestamp advancement until sync is fully complete.
    Use finalize_sync_timestamp() to make the timestamp official.

    Args:
        data: The list of records (as dicts) fetched from the API.
        module_name: The name of the Zoho module (e.g., 'invoices').
        run_timestamp_str: A string representing the current sync run's start time.
        output_base_dir: Base directory for JSON output (default: data/raw_json)
        
    Returns:
        str: The temporary directory path that was created
    """
    try:
        # Use .tmp suffix to indicate temporary/incomplete status
        temp_dir_name = f"{run_timestamp_str}.tmp"
        output_dir = Path(output_base_dir) / temp_dir_name
        
        # Create temporary directory
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created temporary sync directory: {output_dir}")
        except OSError as dir_error:
            logger.error(f"Failed to create temporary directory '{output_dir}': {dir_error}")
            return temp_dir_name

        # Create sync metadata in temp directory
        _create_sync_metadata(output_dir, module_name, len(data or []), is_temp=True)

        # Only save data file if there's actual data
        if data:
            file_path = output_dir / f"{module_name}.json"
            logger.info(f"Saving {len(data)} raw records for '{module_name}' to temporary location: {file_path}")

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"Raw JSON saved for '{module_name}' to temporary directory")
            except (IOError, OSError) as file_error:
                logger.error(f"Could not write temporary file '{file_path}': {file_error}")
                return temp_dir_name
        else:
            logger.info(f"No raw data for module '{module_name}', but temporary directory created.")

        return temp_dir_name

    except Exception as e:
        logger.error(f"Could not create temporary directory for '{module_name}': {e}")
        return f"{run_timestamp_str}.tmp"

def save_raw_json(data: List[Dict[str, Any]], module_name: str, run_timestamp_str: str, output_base_dir: str = "data/raw_json"):
    """
    Legacy function for backward compatibility. 
    Now uses temporary storage to prevent premature timestamp advancement.
    """
    return save_raw_json_temp(data, module_name, run_timestamp_str, output_base_dir)

def finalize_sync_timestamp(run_timestamp_str: str, output_base_dir: str = "data/raw_json"):
    """
    Finalizes a sync by renaming the temporary directory to the final timestamp.
    
    This is the ONLY way a timestamp should advance - when the entire sync completes successfully.
    
    Args:
        run_timestamp_str: The timestamp string for this sync run
        output_base_dir: Base directory for JSON output
        
    Returns:
        bool: True if finalization succeeded, False otherwise
    """
    try:
        temp_dir_name = f"{run_timestamp_str}.tmp"
        temp_path = Path(output_base_dir) / temp_dir_name
        final_path = Path(output_base_dir) / run_timestamp_str
        
        if not temp_path.exists():
            logger.warning(f"Temporary directory not found: {temp_path}")
            return False
        
        # Atomic rename operation
        temp_path.rename(final_path)
        logger.info(f"✅ Sync finalized: {temp_dir_name} → {run_timestamp_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to finalize sync timestamp: {e}")
        return False

def cleanup_failed_sync(run_timestamp_str: str, output_base_dir: str = "data/raw_json"):
    """
    Cleans up temporary directory after a failed/interrupted sync.
    
    This ensures no partial data remains and timestamp doesn't advance.
    
    Args:
        run_timestamp_str: The timestamp string for the failed sync
        output_base_dir: Base directory for JSON output
    """
    try:
        temp_dir_name = f"{run_timestamp_str}.tmp"
        temp_path = Path(output_base_dir) / temp_dir_name
        
        if temp_path.exists():
            import shutil
            shutil.rmtree(temp_path)
            logger.info(f"🧹 Cleaned up failed sync directory: {temp_dir_name}")
        
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary directory: {e}")

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
