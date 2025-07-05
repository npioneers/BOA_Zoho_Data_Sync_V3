"""
Incremental Updater Module for Project Bedrock V2

This module handles incremental updates from JSON API data.
It applies changes to the existing canonical database without rebuilding from scratch.

Responsibilities:
- Load latest JSON API data
- Transform JSON to canonical schema (with flattening)
- Apply incremental updates using UPSERT logic
- Track sync state and timestamps
- Handle conflict resolution

Adheres to operational guidelines: Configuration-driven, no hardcoded values
"""

import logging
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config import get_config_manager
from .database import DatabaseHandler
from .transformer import BillsTransformer
from .mappings import get_entity_schema

logger = logging.getLogger(__name__)


class IncrementalUpdater:
    """
    Handles incremental updates from JSON API data.
    
    This class applies incremental changes to an existing canonical database
    using UPSERT logic. It maintains sync state and handles conflict resolution.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize IncrementalUpdater.
        
        Args:
            config_manager: Optional ConfigurationManager instance
        """
        self.config = config_manager or get_config_manager()
        self.db_handler = DatabaseHandler()
        self.transformer = BillsTransformer()
        self.stats = {
            'json_records_loaded': 0,
            'json_records_transformed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'records_unchanged': 0,
            'conflicts_resolved': 0,
            'update_start_time': None,
            'update_end_time': None,
            'update_duration': None,
            'last_sync_time': None
        }
        
        logger.info("IncrementalUpdater initialized")
    
    def apply_incremental_update(self, conflict_resolution: str = 'json_wins') -> Dict[str, Any]:
        """
        Apply incremental updates from JSON API data.
        
        Args:
            conflict_resolution: Strategy for handling conflicts ('json_wins', 'csv_wins', 'manual')
            
        Returns:
            Dictionary with update statistics and results
        """
        self.stats['update_start_time'] = datetime.now()
        logger.info("🔄 Starting incremental update from JSON API data")
        
        try:
            # Step 1: Load and validate JSON data
            json_data = self._load_json_api_data()
            if json_data.empty:
                logger.warning("⚠️ No JSON data found - skipping incremental update")
                return self._finalize_stats(success=True, message="No updates needed")
            
            # Step 2: Transform JSON to canonical schema
            canonical_data = self._transform_json_data(json_data)
            
            # Step 3: Apply UPSERT logic to update database
            upsert_stats = self._apply_upsert_updates(canonical_data, conflict_resolution)
            
            # Step 4: Update sync state
            self._update_sync_state()
            
            # Finalize statistics
            final_stats = self._finalize_stats(success=True, upsert_stats=upsert_stats)
            
            logger.info(f"✅ Incremental update completed in {self.stats['update_duration']:.2f} seconds")
            return final_stats
            
        except Exception as e:
            logger.error(f"❌ Incremental update failed: {e}")
            return self._finalize_stats(success=False, error=str(e))
    
    def _load_json_api_data(self) -> pd.DataFrame:
        """Load JSON API data from configured source."""
        logger.info("🌐 Loading JSON API data")
        
        # Get JSON source path (with LATEST resolution)
        data_paths = self.config.get_data_source_paths()
        json_api_path = Path(data_paths['json_api_path'])
        bills_json_file = json_api_path / self.config.get('entities', 'bills', 'json_file')
        
        logger.info(f"📁 JSON Source: {bills_json_file}")
        
        if not bills_json_file.exists():
            logger.warning(f"JSON API file not found: {bills_json_file}")
            return pd.DataFrame()
        
        # Load JSON data
        json_data = pd.read_json(bills_json_file)
        self.stats['json_records_loaded'] = len(json_data)
        
        logger.info(f"✅ Loaded {len(json_data)} records from JSON API")
        logger.debug(f"📋 JSON columns: {list(json_data.columns)}")
        
        return json_data
    
    def _transform_json_data(self, json_data: pd.DataFrame) -> pd.DataFrame:
        """Transform JSON data to canonical schema with flattening."""
        logger.info("🔄 Transforming JSON data to canonical schema (with flattening)")
        
        try:
            canonical_data = self.transformer.transform_from_json(json_data)
            self.stats['json_records_transformed'] = len(canonical_data)
            
            logger.info(f"✅ Transformed {len(canonical_data)} records to canonical schema")
            return canonical_data
            
        except Exception as e:
            logger.error(f"❌ JSON transformation failed: {e}")
            raise
    
    def _apply_upsert_updates(self, canonical_data: pd.DataFrame, conflict_resolution: str) -> Dict[str, Any]:
        """Apply UPSERT logic to update database with incremental changes."""
        table_name = self.config.get('entities', 'bills', 'table_name')
        
        logger.info(f"🔄 Applying UPSERT updates to {table_name}")
        logger.info(f"   📊 Records to process: {len(canonical_data)}")
        logger.info(f"   🎯 Conflict resolution: {conflict_resolution}")
        
        upsert_stats = {
            'records_inserted': 0,
            'records_updated': 0,
            'records_unchanged': 0,
            'conflicts_resolved': 0
        }
        
        try:
            with self.db_handler:
                # For each record in the canonical data, apply UPSERT logic
                for idx, row in canonical_data.iterrows():
                    bill_id = row.get('BillID')
                    
                    if pd.isna(bill_id):
                        logger.warning(f"Skipping record {idx} - missing BillID")
                        continue
                    
                    # Check if record exists in database
                    existing_record = self._get_existing_record(table_name, bill_id)
                    
                    if existing_record is None:
                        # INSERT: Record doesn't exist
                        self._insert_new_record(table_name, row)
                        upsert_stats['records_inserted'] += 1
                        
                    else:
                        # UPDATE: Record exists, check for changes
                        update_needed, conflicts = self._compare_records(existing_record, row)
                        
                        if conflicts:
                            # Handle conflicts based on resolution strategy
                            resolved_row = self._resolve_conflicts(existing_record, row, conflicts, conflict_resolution)
                            upsert_stats['conflicts_resolved'] += len(conflicts)
                        else:
                            resolved_row = row
                        
                        if update_needed:
                            self._update_existing_record(table_name, bill_id, resolved_row)
                            upsert_stats['records_updated'] += 1
                        else:
                            upsert_stats['records_unchanged'] += 1
                
                # Update overall statistics
                self.stats.update(upsert_stats)
                
                logger.info(f"✅ UPSERT operations completed:")
                logger.info(f"   ➕ Inserted: {upsert_stats['records_inserted']}")
                logger.info(f"   🔄 Updated: {upsert_stats['records_updated']}")
                logger.info(f"   ➖ Unchanged: {upsert_stats['records_unchanged']}")
                logger.info(f"   ⚡ Conflicts resolved: {upsert_stats['conflicts_resolved']}")
                
                return upsert_stats
                
        except Exception as e:
            logger.error(f"❌ UPSERT operations failed: {e}")
            raise
    
    def _get_existing_record(self, table_name: str, bill_id: str) -> Optional[Dict[str, Any]]:
        """Get existing record from database by BillID."""
        try:
            query = f"SELECT * FROM {table_name} WHERE BillID = ?"
            results = self.db_handler.execute_query(query, (bill_id,))
            
            if results:
                # Convert to dictionary using column names
                columns = [desc[0] for desc in self.db_handler.cursor.description]
                return dict(zip(columns, results[0]))
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving existing record for BillID {bill_id}: {e}")
            return None
    
    def _compare_records(self, existing_record: Dict[str, Any], new_record: pd.Series) -> tuple[bool, List[str]]:
        """
        Compare existing and new records to detect changes and conflicts.
        
        Returns:
            Tuple of (update_needed, conflicts_list)
        """
        update_needed = False
        conflicts = []
        
        # Get Bills schema and compare each field
        bills_schema = get_entity_schema('Bills')
        bills_header_columns = bills_schema['header_columns']
        
        for field in bills_header_columns.keys():
            existing_value = existing_record.get(field)
            new_value = new_record.get(field)
            
            # Handle pandas NaN values
            if pd.isna(existing_value):
                existing_value = None
            if pd.isna(new_value):
                new_value = None
            
            # Check for differences
            if existing_value != new_value:
                update_needed = True
                
                # Check if this is a conflict (both values are non-null and different)
                if existing_value is not None and new_value is not None:
                    conflicts.append(field)
        
        return update_needed, conflicts
    
    def _resolve_conflicts(self, existing_record: Dict[str, Any], new_record: pd.Series, 
                          conflicts: List[str], resolution_strategy: str) -> pd.Series:
        """Resolve conflicts between existing and new records."""
        resolved_record = new_record.copy()
        
        for field in conflicts:
            existing_value = existing_record.get(field)
            new_value = new_record.get(field)
            
            if resolution_strategy == 'csv_wins':
                # Keep existing (CSV) value
                resolved_record[field] = existing_value
            elif resolution_strategy == 'json_wins':
                # Keep new (JSON) value (already in resolved_record)
                pass
            elif resolution_strategy == 'manual':
                # Log conflict for manual resolution
                logger.warning(f"Manual resolution needed for BillID {new_record.get('BillID')}, field {field}")
                logger.warning(f"  Existing (CSV): {existing_value}")
                logger.warning(f"  New (JSON): {new_value}")
                # Default to JSON wins for now
                pass
            
            logger.debug(f"Conflict resolved for {field}: {existing_value} → {resolved_record[field]}")
        
        return resolved_record
    
    def _insert_new_record(self, table_name: str, record: pd.Series) -> None:
        """Insert new record into database."""
        try:
            # Convert Series to DataFrame for database loading
            record_df = pd.DataFrame([record])
            self.db_handler.load_data(table_name, record_df, if_exists='append')
            
        except Exception as e:
            logger.error(f"Failed to insert new record: {e}")
            raise
    
    def _update_existing_record(self, table_name: str, bill_id: str, record: pd.Series) -> None:
        """Update existing record in database."""
        try:
            # Build UPDATE query
            set_clauses = []
            values = []
            
            for field, value in record.items():
                if field != 'BillID':  # Don't update the primary key
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            values.append(bill_id)  # For WHERE clause
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE BillID = ?"
            self.db_handler.execute_query(query, values)
            
        except Exception as e:
            logger.error(f"Failed to update record {bill_id}: {e}")
            raise
    
    def _update_sync_state(self) -> None:
        """Update sync state with current timestamp."""
        self.stats['last_sync_time'] = datetime.now()
        logger.info(f"🕒 Sync state updated: {self.stats['last_sync_time']}")
        
        # TODO: Implement persistent sync state storage
        # This will be added when StateManager is implemented
    
    def _finalize_stats(self, success: bool, upsert_stats: Dict[str, Any] = None, 
                       message: str = None, error: str = None) -> Dict[str, Any]:
        """Finalize and return update statistics."""
        self.stats['update_end_time'] = datetime.now()
        self.stats['update_duration'] = (
            self.stats['update_end_time'] - self.stats['update_start_time']
        ).total_seconds()
        
        final_stats = self.stats.copy()
        final_stats['success'] = success
        
        if upsert_stats:
            final_stats.update(upsert_stats)
        
        if message:
            final_stats['message'] = message
        
        if error:
            final_stats['error'] = error
        
        return final_stats
    
    def validate_incremental_update(self) -> bool:
        """
        Validate the incremental update results.
        
        Returns:
            True if validation passes, False otherwise
        """
        table_name = self.config.get('entities', 'bills', 'table_name')
        
        logger.info("✅ Validating incremental update")
        
        try:
            with self.db_handler:
                # Basic validation: ensure table still exists and has data
                table_info = self.db_handler.get_table_info(table_name)
                
                if table_info['record_count'] > 0:
                    logger.info(f"✅ Incremental update validation passed")
                    logger.info(f"   📊 Total records: {table_info['record_count']:,}")
                    return True
                else:
                    logger.error("❌ Incremental update validation failed: No records found")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return False


# Convenience function for simple incremental updates
def apply_json_updates(conflict_resolution: str = 'json_wins', config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to apply incremental updates from JSON.
    
    Args:
        conflict_resolution: Strategy for handling conflicts
        config_file: Optional path to configuration file
        
    Returns:
        Update statistics dictionary
    """
    from .config import reload_config
    
    # Reload config if specified
    if config_file:
        config_manager = reload_config(config_file)
    else:
        config_manager = get_config_manager()
    
    # Apply incremental updates
    updater = IncrementalUpdater(config_manager)
    stats = updater.apply_incremental_update(conflict_resolution)
    
    # Validate updates
    validation_passed = updater.validate_incremental_update()
    stats['validation_passed'] = validation_passed
    
    return stats
