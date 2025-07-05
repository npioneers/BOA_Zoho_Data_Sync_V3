"""
JSON-Database Comparator

Independent module for comparing JSON data with database records.
Identifies differences and generates sync recommendations.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import pandas as pd
from dataclasses import dataclass
from datetime import datetime

from .json_mappings import get_json_mapping, get_field_mapping, get_primary_key_info

logger = logging.getLogger(__name__)

@dataclass
class ComparisonResult:
    """Results of comparing JSON data with database."""
    entity_name: str
    json_count: int
    db_count: int
    missing_in_db: List[str]  # Primary keys missing in database
    missing_in_json: List[str]  # Primary keys missing in JSON
    potential_updates: List[str]  # Primary keys that might need updates
    identical_records: List[str]  # Primary keys with identical data
    comparison_fields: List[str]  # Fields that were compared
    timestamp: str

@dataclass 
class SyncRecommendation:
    """Recommendation for syncing an entity."""
    entity_name: str
    action: str  # 'insert', 'update', 'skip', 'investigate'
    record_count: int
    primary_keys: List[str]
    reason: str
    priority: int  # 1=high, 2=medium, 3=low

class JsonDatabaseComparator:
    """
    Compares JSON data with database records to identify differences.
    
    Features:
    - Field-level comparison using mappings
    - Primary key integrity checks
    - Missing record identification  
    - Update candidate detection
    - Sync recommendations generation
    """
    
    def __init__(self, database_path: str):
        """
        Initialize comparator with database connection.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.comparison_results = {}
        self.sync_recommendations = {}
        
    def compare_entity(self, entity_name: str, json_records: List[Dict[str, Any]]) -> ComparisonResult:
        """
        Compare JSON records with database records for an entity.
        
        Args:
            entity_name: Name of the entity to compare
            json_records: List of JSON records for the entity
            
        Returns:
            ComparisonResult with detailed comparison data
        """
        logger.info(f"Comparing {entity_name}: {len(json_records)} JSON records vs database")
        
        try:
            # Get mapping configuration
            mapping = get_json_mapping(entity_name)
            field_mappings = get_field_mapping(entity_name)
            json_pk, db_pk = get_primary_key_info(entity_name)
            
            # Load database records
            db_records = self._load_database_records(mapping['database_table'], db_pk)
            
            # Extract primary keys
            json_pks = self._extract_primary_keys(json_records, json_pk)
            db_pks = set(db_records.keys()) if db_records else set()
            
            # Find differences
            missing_in_db = [pk for pk in json_pks if pk not in db_pks]
            missing_in_json = [pk for pk in db_pks if pk not in json_pks]
            
            # Find potential updates (records that exist in both)
            common_pks = json_pks.intersection(db_pks)
            potential_updates, identical_records = self._identify_updates(
                json_records, db_records, common_pks, json_pk, field_mappings
            )
            
            result = ComparisonResult(
                entity_name=entity_name,
                json_count=len(json_records),
                db_count=len(db_records) if db_records else 0,
                missing_in_db=missing_in_db,
                missing_in_json=missing_in_json,
                potential_updates=potential_updates,
                identical_records=identical_records,
                comparison_fields=list(field_mappings.keys()),
                timestamp=datetime.now().isoformat()
            )
            
            self.comparison_results[entity_name] = result
            logger.info(f"Comparison complete for {entity_name}: "
                       f"{len(missing_in_db)} missing in DB, "
                       f"{len(missing_in_json)} missing in JSON, "
                       f"{len(potential_updates)} potential updates")
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing entity {entity_name}: {str(e)}")
            raise
    
    def _load_database_records(self, table_name: str, primary_key: str) -> Dict[str, Dict[str, Any]]:
        """
        Load all records from database table.
        
        Args:
            table_name: Name of database table
            primary_key: Primary key field name
            
        Returns:
            Dictionary mapping primary key values to record dictionaries
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                if not cursor.fetchone():
                    logger.warning(f"Database table '{table_name}' does not exist")
                    return {}
                
                # Load all records
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Convert to dictionary keyed by primary key
                records = {}
                for row in rows:
                    row_dict = dict(row)
                    pk_value = row_dict.get(primary_key)
                    if pk_value:
                        records[str(pk_value)] = row_dict
                
                logger.debug(f"Loaded {len(records)} records from {table_name}")
                return records
                
        except Exception as e:
            logger.error(f"Error loading database records from {table_name}: {str(e)}")
            return {}
    
    def _extract_primary_keys(self, json_records: List[Dict[str, Any]], 
                            json_pk_field: str) -> Set[str]:
        """
        Extract primary key values from JSON records.
        
        Args:
            json_records: List of JSON record dictionaries
            json_pk_field: Name of primary key field in JSON
            
        Returns:
            Set of primary key values as strings
        """
        primary_keys = set()
        for record in json_records:
            pk_value = record.get(json_pk_field)
            if pk_value:
                primary_keys.add(str(pk_value))
        
        logger.debug(f"Extracted {len(primary_keys)} primary keys from JSON records")
        return primary_keys
    
    def _identify_updates(self, json_records: List[Dict[str, Any]], 
                         db_records: Dict[str, Dict[str, Any]],
                         common_pks: Set[str], json_pk_field: str,
                         field_mappings: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """
        Identify records that need updates vs those that are identical.
        
        Args:
            json_records: JSON records list
            db_records: Database records dictionary
            common_pks: Primary keys that exist in both JSON and DB
            json_pk_field: JSON primary key field name
            field_mappings: JSON-to-DB field mappings
            
        Returns:
            Tuple of (potential_updates, identical_records) as lists of primary keys
        """
        potential_updates = []
        identical_records = []
        
        # Create lookup for JSON records by primary key
        json_lookup = {}
        for record in json_records:
            pk_value = str(record.get(json_pk_field, ''))
            if pk_value:
                json_lookup[pk_value] = record
        
        for pk in common_pks:
            json_record = json_lookup.get(pk)
            db_record = db_records.get(pk)
            
            if not json_record or not db_record:
                continue
            
            # Compare mapped fields
            has_differences = False
            for json_field, db_field in field_mappings.items():
                json_value = self._normalize_value(json_record.get(json_field))
                db_value = self._normalize_value(db_record.get(db_field))
                
                if json_value != db_value:
                    has_differences = True
                    break
            
            if has_differences:
                potential_updates.append(pk)
            else:
                identical_records.append(pk)
        
        logger.debug(f"Identified {len(potential_updates)} potential updates, "
                    f"{len(identical_records)} identical records")
        
        return potential_updates, identical_records
    
    def _normalize_value(self, value: Any) -> Any:
        """
        Normalize a value for comparison.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized value
        """
        if value is None:
            return None
        elif isinstance(value, str):
            return value.strip()
        elif isinstance(value, (int, float)):
            return value
        else:
            return str(value).strip()
    
    def generate_sync_recommendations(self, comparison_result: ComparisonResult) -> List[SyncRecommendation]:
        """
        Generate sync recommendations based on comparison results.
        
        Args:
            comparison_result: Results from entity comparison
            
        Returns:
            List of sync recommendations
        """
        recommendations = []
        entity_name = comparison_result.entity_name
        
        # Recommend inserts for missing records
        if comparison_result.missing_in_db:
            recommendations.append(SyncRecommendation(
                entity_name=entity_name,
                action='insert',
                record_count=len(comparison_result.missing_in_db),
                primary_keys=comparison_result.missing_in_db,
                reason=f"{len(comparison_result.missing_in_db)} records exist in JSON but not in database",
                priority=1  # High priority
            ))
        
        # Recommend updates for changed records
        if comparison_result.potential_updates:
            recommendations.append(SyncRecommendation(
                entity_name=entity_name,
                action='update',
                record_count=len(comparison_result.potential_updates),
                primary_keys=comparison_result.potential_updates,
                reason=f"{len(comparison_result.potential_updates)} records have differences between JSON and database",
                priority=2  # Medium priority
            ))
        
        # Flag orphaned database records for investigation
        if comparison_result.missing_in_json:
            recommendations.append(SyncRecommendation(
                entity_name=entity_name,
                action='investigate',
                record_count=len(comparison_result.missing_in_json),
                primary_keys=comparison_result.missing_in_json,
                reason=f"{len(comparison_result.missing_in_json)} records exist in database but not in JSON",
                priority=3  # Low priority
            ))
        
        # Note identical records (no action needed)
        if comparison_result.identical_records:
            recommendations.append(SyncRecommendation(
                entity_name=entity_name,
                action='skip',
                record_count=len(comparison_result.identical_records),
                primary_keys=comparison_result.identical_records,
                reason=f"{len(comparison_result.identical_records)} records are identical between JSON and database",
                priority=3  # Low priority
            ))
        
        self.sync_recommendations[entity_name] = recommendations
        logger.info(f"Generated {len(recommendations)} sync recommendations for {entity_name}")
        
        return recommendations
    
    def compare_multiple_entities(self, entity_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ComparisonResult]:
        """
        Compare multiple entities at once.
        
        Args:
            entity_data: Dictionary mapping entity names to their JSON records
            
        Returns:
            Dictionary mapping entity names to their comparison results
        """
        results = {}
        
        for entity_name, json_records in entity_data.items():
            try:
                result = self.compare_entity(entity_name, json_records)
                results[entity_name] = result
                
                # Generate recommendations immediately
                self.generate_sync_recommendations(result)
                
            except Exception as e:
                logger.error(f"Failed to compare entity {entity_name}: {str(e)}")
                continue
        
        logger.info(f"Completed comparison for {len(results)} entities")
        return results
    
    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary report of all comparisons.
        
        Returns:
            Dictionary with summary statistics and recommendations
        """
        total_entities = len(self.comparison_results)
        total_json_records = sum(r.json_count for r in self.comparison_results.values())
        total_db_records = sum(r.db_count for r in self.comparison_results.values())
        total_missing_in_db = sum(len(r.missing_in_db) for r in self.comparison_results.values())
        total_missing_in_json = sum(len(r.missing_in_json) for r in self.comparison_results.values())
        total_potential_updates = sum(len(r.potential_updates) for r in self.comparison_results.values())
        
        # Count recommendations by action
        action_counts = {}
        for entity_recs in self.sync_recommendations.values():
            for rec in entity_recs:
                action_counts[rec.action] = action_counts.get(rec.action, 0) + rec.record_count
        
        return {
            'summary': {
                'total_entities_compared': total_entities,
                'total_json_records': total_json_records,
                'total_database_records': total_db_records,
                'total_missing_in_database': total_missing_in_db,
                'total_missing_in_json': total_missing_in_json,
                'total_potential_updates': total_potential_updates
            },
            'recommendations': action_counts,
            'comparison_timestamp': datetime.now().isoformat(),
            'entities': list(self.comparison_results.keys())
        }
