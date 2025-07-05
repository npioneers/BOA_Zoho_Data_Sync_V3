"""
JSON Data Loader

Independent module for loading and processing JSON data from Zoho API exports.
Handles dynamic path resolution and data validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class JsonDataLoader:
    """
    Loads JSON data from Zoho API export files.
    
    Features:
    - Dynamic path resolution for timestamped directories
    - Configuration-driven data source paths
    - Data validation and error handling
    - Supports multiple JSON data formats
    """
    
    def __init__(self, base_json_path: Optional[str] = None):
        """
        Initialize JSON data loader.
        
        Args:
            base_json_path: Base path to JSON data directory. Can be:
                - Base directory containing timestamped subdirectories
                - Specific timestamped directory with JSON files
        """
        self.base_json_path = base_json_path or "data/raw_json"
        self.loaded_data = {}
        self.load_errors = []
        
        # Check if the path is a specific directory with JSON files
        path = Path(self.base_json_path)
        if path.exists() and any(path.glob("*.json")):
            # Path contains JSON files directly - use it as specific directory
            self.specific_json_dir = path
        else:
            # Path is a base directory - need to find subdirectories
            self.specific_json_dir = None
        
    def find_latest_json_directory(self) -> Optional[Path]:
        """
        Find the most recent timestamped JSON directory.
        
        Returns:
            Path to latest JSON directory or None if not found
        """
        base_path = Path(self.base_json_path)
        
        # If path doesn't exist, try relative to project root (for notebook usage)
        if not base_path.exists():
            # Try from parent directory (notebook running from notebooks/ folder)
            alt_base_path = Path("..") / self.base_json_path
            if alt_base_path.exists():
                base_path = alt_base_path
                logger.info(f"Using alternative path: {base_path.absolute()}")
            else:
                logger.warning(f"JSON base path does not exist: {base_path}")
                logger.warning(f"Alternative path also does not exist: {alt_base_path}")
                return None
            
        # Look for timestamped directories (YYYY-MM-DD_HH-MM-SS pattern)
        json_dirs = []
        for item in base_path.iterdir():
            if item.is_dir() and self._is_timestamped_directory(item.name):
                json_dirs.append(item)
                
        if not json_dirs:
            logger.warning(f"No timestamped JSON directories found in: {base_path}")
            return None
            
        # Sort by directory name (which contains timestamp) and get latest
        latest_dir = sorted(json_dirs, key=lambda x: x.name)[-1]
        logger.info(f"Found latest JSON directory: {latest_dir}")
        return latest_dir
    
    def _is_timestamped_directory(self, dirname: str) -> bool:
        """
        Check if directory name follows timestamp pattern.
        
        Args:
            dirname: Directory name to check
            
        Returns:
            True if directory follows YYYY-MM-DD_HH-MM-SS pattern
        """
        try:
            # Try to parse as timestamp: YYYY-MM-DD_HH-MM-SS
            datetime.strptime(dirname, "%Y-%m-%d_%H-%M-%S")
            return True
        except ValueError:
            return False
    
    def load_entity_data(self, entity_name: str, json_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Load JSON data for a specific entity.
        
        Args:
            entity_name: Name of the entity (e.g., 'bills', 'invoices')
            json_dir: Specific JSON directory to use. If None, finds latest.
            
        Returns:
            List of entity records from JSON
        """
        if json_dir is None:
            # Check if we have a specific directory or need to find one
            if self.specific_json_dir:
                json_dir = self.specific_json_dir
            else:
                json_dir = self.find_latest_json_directory()
                if json_dir is None:
                    self.load_errors.append(f"Could not find JSON directory for entity: {entity_name}")
                    return []
        
        # Try different possible filenames for the entity
        possible_filenames = [
            f"{entity_name}.json",
            f"{entity_name.lower()}.json",
            f"{entity_name.capitalize()}.json",
            f"{entity_name.upper()}.json"
        ]
        
        for filename in possible_filenames:
            json_file = json_dir / filename
            if json_file.exists():
                try:
                    return self._load_json_file(json_file, entity_name)
                except Exception as e:
                    error_msg = f"Error loading {json_file}: {str(e)}"
                    logger.error(error_msg)
                    self.load_errors.append(error_msg)
                    continue
        
        # If no file found, log and return empty list
        error_msg = f"No JSON file found for entity '{entity_name}' in {json_dir}"
        logger.warning(error_msg)
        self.load_errors.append(error_msg)
        return []
    
    def _load_json_file(self, json_file: Path, entity_name: str) -> List[Dict[str, Any]]:
        """
        Load and parse a JSON file.
        
        Args:
            json_file: Path to JSON file
            entity_name: Name of entity for logging
            
        Returns:
            List of records from JSON file
        """
        logger.info(f"Loading JSON file: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        records = self._extract_records(data, entity_name)
        
        logger.info(f"Loaded {len(records)} records from {json_file}")
        return records
    
    def _extract_records(self, data: Any, entity_name: str) -> List[Dict[str, Any]]:
        """
        Extract records from JSON data structure.
        
        Args:
            data: Raw JSON data
            entity_name: Name of entity for context
            
        Returns:
            List of record dictionaries
        """
        # Handle different JSON response formats
        if isinstance(data, list):
            # Direct list of records
            return data
        elif isinstance(data, dict):
            # Check for common API response structures
            for key in [entity_name, entity_name.lower(), 'data', 'records', 'items']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            
            # If dict contains a single entity, wrap in list
            if 'id' in data or f'{entity_name.lower()}_id' in data:
                return [data]
        
        logger.warning(f"Unexpected JSON structure for {entity_name}: {type(data)}")
        return []
    
    def load_all_entities(self, entity_list: Optional[List[str]] = None, 
                         json_dir: Optional[Path] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load JSON data for multiple entities.
        
        Args:
            entity_list: List of entity names to load. If None, loads all available.
            json_dir: Specific JSON directory to use. If None, finds latest.
            
        Returns:
            Dictionary mapping entity names to their record lists
        """
        if json_dir is None:
            # Check if we have a specific directory or need to find one
            if self.specific_json_dir:
                json_dir = self.specific_json_dir
            else:
                json_dir = self.find_latest_json_directory()
                if json_dir is None:
                    logger.error("Could not find JSON directory for bulk load")
                    return {}
        
        if entity_list is None:
            # Discover entities from available JSON files
            entity_list = self._discover_entities(json_dir)
        
        results = {}
        for entity in entity_list:
            try:
                results[entity] = self.load_entity_data(entity, json_dir)
            except Exception as e:
                error_msg = f"Failed to load entity '{entity}': {str(e)}"
                logger.error(error_msg)
                self.load_errors.append(error_msg)
                results[entity] = []
        
        logger.info(f"Loaded data for {len(results)} entities from {json_dir}")
        return results
    
    def _discover_entities(self, json_dir: Path) -> List[str]:
        """
        Discover available entities from JSON files in directory.
        
        Args:
            json_dir: Directory to scan for JSON files
            
        Returns:
            List of discovered entity names
        """
        entities = []
        for json_file in json_dir.glob("*.json"):
            # Extract entity name from filename (remove .json extension)
            entity_name = json_file.stem.lower()
            entities.append(entity_name)
        
        logger.info(f"Discovered {len(entities)} entities in {json_dir}: {entities}")
        return entities
    
    def get_load_summary(self) -> Dict[str, Any]:
        """
        Get summary of loading operations.
        
        Returns:
            Dictionary with loading statistics and errors
        """
        return {
            'entities_loaded': len(self.loaded_data),
            'total_errors': len(self.load_errors),
            'errors': self.load_errors.copy(),
            'loaded_entities': list(self.loaded_data.keys())
        }
    
    def clear_cache(self):
        """Clear cached data and errors."""
        self.loaded_data.clear()
        self.load_errors.clear()
        logger.debug("Cleared JSON loader cache")
