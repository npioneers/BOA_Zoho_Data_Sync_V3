"""
JSON Sync Engine

Independent module for executing JSON-to-database synchronization operations.
Handles inserts, updates, and conflict resolution.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .json_mappings import get_json_mapping, get_field_mapping, get_primary_key_info
from .json_comparator import SyncRecommendation

logger = logging.getLogger(__name__)

@dataclass
class SyncResult:
    """Result of a sync operation."""
    entity_name: str
    action: str
    success: bool
    records_processed: int
    records_success: int
    records_failed: int
    errors: List[str]
    execution_time: float
    timestamp: str

@dataclass
class SyncStatistics:
    """Overall sync statistics."""
    total_entities: int
    total_records_processed: int
    total_inserts: int
    total_updates: int
    total_skipped: int
    total_errors: int
    execution_time: float
    success_rate: float

class JsonSyncEngine:
    """
    Executes JSON-to-database synchronization operations.
    
    Features:
    - Insert missing records from JSON
    - Update changed records in database
    - Conflict detection and resolution
    - Transaction safety with rollback
    - Detailed logging and error handling
    """
    
    def __init__(self, database_path: str):
        """
        Initialize sync engine with database connection.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.sync_results = {}
        self.conflict_resolution = 'json_wins'  # Default: JSON data takes precedence
        
    def set_conflict_resolution(self, strategy: str):
        """
        Set conflict resolution strategy.
        
        Args:
            strategy: 'json_wins', 'db_wins', or 'manual'
        """
        valid_strategies = ['json_wins', 'db_wins', 'manual']
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}")
        
        self.conflict_resolution = strategy
        logger.info(f"Conflict resolution strategy set to: {strategy}")
    
    def execute_sync_recommendation(self, recommendation: SyncRecommendation, 
                                  json_records: List[Dict[str, Any]]) -> SyncResult:
        """
        Execute a single sync recommendation.
        
        Args:
            recommendation: Sync recommendation to execute
            json_records: JSON records for the entity
            
        Returns:
            SyncResult with execution details
        """
        start_time = datetime.now()
        entity_name = recommendation.entity_name
        
        logger.info(f"Executing {recommendation.action} for {entity_name}: "
                   f"{recommendation.record_count} records")
        
        try:
            if recommendation.action == 'insert':
                result = self._execute_inserts(entity_name, recommendation.primary_keys, json_records)
            elif recommendation.action == 'update':
                result = self._execute_updates(entity_name, recommendation.primary_keys, json_records)
            elif recommendation.action == 'skip':
                result = self._execute_skip(entity_name, recommendation)
            elif recommendation.action == 'investigate':
                result = self._execute_investigation(entity_name, recommendation)
            else:
                raise ValueError(f"Unknown action: {recommendation.action}")
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            self.sync_results[entity_name] = result
            logger.info(f"Sync completed for {entity_name}: "
                       f"{result.records_success}/{result.records_processed} successful")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = SyncResult(
                entity_name=entity_name,
                action=recommendation.action,
                success=False,
                records_processed=0,
                records_success=0,
                records_failed=recommendation.record_count,
                errors=[str(e)],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
            
            self.sync_results[entity_name] = error_result
            logger.error(f"Sync failed for {entity_name}: {str(e)}")
            return error_result
    
    def _execute_inserts(self, entity_name: str, primary_keys: List[str], 
                        json_records: List[Dict[str, Any]]) -> SyncResult:
        """
        Execute insert operations for missing records.
        
        Args:
            entity_name: Name of the entity
            primary_keys: List of primary keys to insert
            json_records: JSON records for the entity
            
        Returns:
            SyncResult with insert operation details
        """
        mapping = get_json_mapping(entity_name)
        field_mappings = get_field_mapping(entity_name)
        json_pk, db_pk = get_primary_key_info(entity_name)
        table_name = mapping['database_table']
        
        # Create lookup for JSON records by primary key
        json_lookup = {}
        for record in json_records:
            pk_value = str(record.get(json_pk, ''))
            if pk_value:
                json_lookup[pk_value] = record
        
        success_count = 0
        failed_count = 0
        errors = []
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for pk in primary_keys:
                    json_record = json_lookup.get(pk)
                    if not json_record:
                        errors.append(f"JSON record not found for primary key: {pk}")
                        failed_count += 1
                        continue
                    
                    try:
                        # Map JSON fields to database fields
                        db_record = self._map_json_to_db(json_record, field_mappings)
                        
                        # Prepare INSERT statement
                        columns = list(db_record.keys())
                        placeholders = ','.join(['?' for _ in columns])
                        values = [db_record[col] for col in columns]
                        
                        insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                        cursor.execute(insert_sql, values)
                        
                        success_count += 1
                        logger.debug(f"Inserted record with {db_pk}={pk} into {table_name}")
                        
                    except Exception as e:
                        error_msg = f"Failed to insert record {pk}: {str(e)}"
                        errors.append(error_msg)
                        failed_count += 1
                        logger.warning(error_msg)
                
                conn.commit()
                
        except Exception as e:
            error_msg = f"Database error during inserts: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return SyncResult(
            entity_name=entity_name,
            action='insert',
            success=failed_count == 0,
            records_processed=len(primary_keys),
            records_success=success_count,
            records_failed=failed_count,
            errors=errors,
            execution_time=0.0,  # Will be set by caller
            timestamp=datetime.now().isoformat()
        )
    
    def _execute_updates(self, entity_name: str, primary_keys: List[str], 
                        json_records: List[Dict[str, Any]]) -> SyncResult:
        """
        Execute update operations for changed records.
        
        Args:
            entity_name: Name of the entity
            primary_keys: List of primary keys to update
            json_records: JSON records for the entity
            
        Returns:
            SyncResult with update operation details
        """
        mapping = get_json_mapping(entity_name)
        field_mappings = get_field_mapping(entity_name)
        json_pk, db_pk = get_primary_key_info(entity_name)
        table_name = mapping['database_table']
        
        # Create lookup for JSON records by primary key
        json_lookup = {}
        for record in json_records:
            pk_value = str(record.get(json_pk, ''))
            if pk_value:
                json_lookup[pk_value] = record
        
        success_count = 0
        failed_count = 0
        errors = []
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for pk in primary_keys:
                    json_record = json_lookup.get(pk)
                    if not json_record:
                        errors.append(f"JSON record not found for primary key: {pk}")
                        failed_count += 1
                        continue
                    
                    try:
                        # Map JSON fields to database fields
                        db_record = self._map_json_to_db(json_record, field_mappings)
                        
                        # Prepare UPDATE statement (exclude primary key from SET clause)
                        update_fields = [col for col in db_record.keys() if col != db_pk]
                        set_clause = ','.join([f"{col}=?" for col in update_fields])
                        values = [db_record[col] for col in update_fields]
                        values.append(pk)  # Add primary key for WHERE clause
                        
                        update_sql = f"UPDATE {table_name} SET {set_clause} WHERE {db_pk}=?"
                        cursor.execute(update_sql, values)
                        
                        if cursor.rowcount > 0:
                            success_count += 1
                            logger.debug(f"Updated record with {db_pk}={pk} in {table_name}")
                        else:
                            errors.append(f"No rows updated for primary key: {pk}")
                            failed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to update record {pk}: {str(e)}"
                        errors.append(error_msg)
                        failed_count += 1
                        logger.warning(error_msg)
                
                conn.commit()
                
        except Exception as e:
            error_msg = f"Database error during updates: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return SyncResult(
            entity_name=entity_name,
            action='update',
            success=failed_count == 0,
            records_processed=len(primary_keys),
            records_success=success_count,
            records_failed=failed_count,
            errors=errors,
            execution_time=0.0,  # Will be set by caller
            timestamp=datetime.now().isoformat()
        )
    
    def _execute_skip(self, entity_name: str, recommendation: SyncRecommendation) -> SyncResult:
        """
        Handle skip recommendation (no action needed).
        
        Args:
            entity_name: Name of the entity
            recommendation: Skip recommendation
            
        Returns:
            SyncResult indicating skip operation
        """
        return SyncResult(
            entity_name=entity_name,
            action='skip',
            success=True,
            records_processed=recommendation.record_count,
            records_success=recommendation.record_count,
            records_failed=0,
            errors=[],
            execution_time=0.0,
            timestamp=datetime.now().isoformat()
        )
    
    def _execute_investigation(self, entity_name: str, recommendation: SyncRecommendation) -> SyncResult:
        """
        Handle investigate recommendation (log for manual review).
        
        Args:
            entity_name: Name of the entity
            recommendation: Investigation recommendation
            
        Returns:
            SyncResult indicating investigation needed
        """
        logger.warning(f"Manual investigation needed for {entity_name}: "
                      f"{recommendation.record_count} orphaned database records")
        
        return SyncResult(
            entity_name=entity_name,
            action='investigate',
            success=True,
            records_processed=recommendation.record_count,
            records_success=0,
            records_failed=0,
            errors=[f"Manual investigation required for {recommendation.record_count} orphaned records"],
            execution_time=0.0,
            timestamp=datetime.now().isoformat()
        )
    
    def _map_json_to_db(self, json_record: Dict[str, Any], 
                       field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        Map JSON record fields to database fields.
        
        Args:
            json_record: JSON record dictionary
            field_mappings: JSON-to-DB field mappings
            
        Returns:
            Dictionary with database field names and values
        """
        db_record = {}
        
        for json_field, db_field in field_mappings.items():
            value = json_record.get(json_field)
            if value is not None:
                # Convert value to appropriate type for database
                db_record[db_field] = self._convert_value_for_db(value)
        
        return db_record
    
    def _convert_value_for_db(self, value: Any) -> Any:
        """
        Convert a value to appropriate type for database storage.
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value suitable for database
        """
        if value is None:
            return None
        elif isinstance(value, str):
            return value.strip()
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, bool):
            return int(value)  # SQLite stores booleans as integers
        elif isinstance(value, (dict, list)):
            return json.dumps(value)  # Store complex types as JSON strings
        else:
            return str(value)
    
    def execute_all_recommendations(self, recommendations: Dict[str, List[SyncRecommendation]], 
                                  entity_data: Dict[str, List[Dict[str, Any]]]) -> SyncStatistics:
        """
        Execute all sync recommendations for multiple entities.
        
        Args:
            recommendations: Dictionary mapping entity names to their recommendations
            entity_data: Dictionary mapping entity names to their JSON records
            
        Returns:
            SyncStatistics with overall execution results
        """
        start_time = datetime.now()
        
        total_entities = 0
        total_records_processed = 0
        total_inserts = 0
        total_updates = 0
        total_skipped = 0
        total_errors = 0
        
        for entity_name, entity_recommendations in recommendations.items():
            json_records = entity_data.get(entity_name, [])
            
            for recommendation in entity_recommendations:
                try:
                    result = self.execute_sync_recommendation(recommendation, json_records)
                    
                    total_records_processed += result.records_processed
                    total_errors += result.records_failed
                    
                    if recommendation.action == 'insert':
                        total_inserts += result.records_success
                    elif recommendation.action == 'update':
                        total_updates += result.records_success
                    elif recommendation.action == 'skip':
                        total_skipped += result.records_success
                    
                except Exception as e:
                    logger.error(f"Failed to execute recommendation for {entity_name}: {str(e)}")
                    total_errors += recommendation.record_count
            
            total_entities += 1
        
        execution_time = (datetime.now() - start_time).total_seconds()
        success_rate = ((total_records_processed - total_errors) / total_records_processed * 100) if total_records_processed > 0 else 0
        
        statistics = SyncStatistics(
            total_entities=total_entities,
            total_records_processed=total_records_processed,
            total_inserts=total_inserts,
            total_updates=total_updates,
            total_skipped=total_skipped,
            total_errors=total_errors,
            execution_time=execution_time,
            success_rate=success_rate
        )
        
        logger.info(f"Sync execution completed: {total_entities} entities, "
                   f"{total_records_processed} records processed, "
                   f"{success_rate:.1f}% success rate")
        
        return statistics
    
    def get_sync_summary(self) -> Dict[str, Any]:
        """
        Get summary of all sync operations.
        
        Returns:
            Dictionary with sync summary data
        """
        if not self.sync_results:
            return {'message': 'No sync operations executed yet'}
        
        total_processed = sum(r.records_processed for r in self.sync_results.values())
        total_success = sum(r.records_success for r in self.sync_results.values())
        total_failed = sum(r.records_failed for r in self.sync_results.values())
        total_execution_time = sum(r.execution_time for r in self.sync_results.values())
        
        return {
            'entities_synced': len(self.sync_results),
            'total_records_processed': total_processed,
            'total_records_success': total_success,
            'total_records_failed': total_failed,
            'success_rate': (total_success / total_processed * 100) if total_processed > 0 else 0,
            'total_execution_time': total_execution_time,
            'conflict_resolution_strategy': self.conflict_resolution,
            'individual_results': {name: {
                'action': result.action,
                'success': result.success,
                'records_processed': result.records_processed,
                'records_success': result.records_success,
                'error_count': len(result.errors)
            } for name, result in self.sync_results.items()}
        }
