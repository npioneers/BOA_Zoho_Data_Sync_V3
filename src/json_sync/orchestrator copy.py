"""
JSON Differential Sync Orchestrator

Main orchestrator for JSON-to-database differential synchronization.
Coordinates all components and provides high-level interface.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .json_loader import JsonDataLoader
from .json_comparator import JsonDatabaseComparator, ComparisonResult, SyncRecommendation
from .json_sync_engine import JsonSyncEngine, SyncStatistics
from .json_mappings import JSON_ENTITY_MAPPINGS
from .verification import verify_sync_completion, SyncVerificationReporter

logger = logging.getLogger(__name__)

class JsonDifferentialSyncOrchestrator:
    """
    Main orchestrator for JSON differential sync operations.
    
    Features:
    - End-to-end JSON differential sync workflow
    - Configuration-driven operation
    - Comprehensive logging and error handling
    - Rollback capabilities for failed operations
    - Detailed reporting and statistics
    """
    
    def __init__(self, database_path: str, json_base_path: Optional[str] = None):
        """
        Initialize orchestrator with database and JSON paths.
        
        Args:
            database_path: Path to SQLite database
            json_base_path: Base path to JSON data directory
        """
        # Resolve paths to handle notebook execution from different directories
        self.database_path = str(Path(database_path).resolve())
        self.json_base_path = str(Path(json_base_path or "data/raw_json").resolve())
        
        logger.info("JsonDifferentialSyncOrchestrator initialized:")
        logger.info(f"  Database: {self.database_path}")
        logger.info(f"  JSON Base Path: {self.json_base_path}")
        
        # Initialize components
        self.json_loader = JsonDataLoader(self.json_base_path)
        self.comparator = JsonDatabaseComparator(self.database_path)
        self.sync_engine = JsonSyncEngine(self.database_path)
        
        # Initialize state attributes
        self.loaded_data = {}
        self.comparison_results = {}
        self.sync_recommendations = {}
        self.execution_statistics = None
        self.verification_report = None
        
        # Execution state
        self.loaded_data = {}
        self.comparison_results = {}
        self.sync_recommendations = {}
        self.execution_statistics = None
        
        logger.info(f"JsonDifferentialSyncOrchestrator initialized:")
        logger.info(f"  Database: {database_path}")
        logger.info(f"  JSON Base Path: {self.json_base_path}")
    
    def execute_full_differential_sync(self, entity_list: Optional[List[str]] = None,
                                     conflict_resolution: str = 'json_wins',
                                     dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute complete differential sync workflow.
        
        Args:
            entity_list: List of entities to sync. If None, syncs all available.
            conflict_resolution: Strategy for resolving conflicts ('json_wins', 'db_wins', 'manual')
            dry_run: If True, performs comparison but no database changes
            
        Returns:
            Dictionary with complete execution results
        """
        start_time = datetime.now()
        logger.info("Starting full differential sync workflow")
        logger.info(f"  Entities: {entity_list or 'All available'}")
        logger.info(f"  Conflict Resolution: {conflict_resolution}")
        logger.info(f"  Dry Run: {dry_run}")
        
        try:
            # Step 1: Load JSON data
            logger.info("Step 1: Loading JSON data")
            self.loaded_data = self.load_json_data(entity_list)
            
            if not self.loaded_data:
                raise RuntimeError("No JSON data loaded - cannot proceed with sync")
            
            # Step 2: Compare with database
            logger.info("Step 2: Comparing JSON data with database")
            self.comparison_results = self.compare_with_database(self.loaded_data)
            
            # Step 3: Generate sync recommendations
            logger.info("Step 3: Generating sync recommendations")
            self.sync_recommendations = self.generate_sync_recommendations(self.comparison_results)
            
            # Step 4: Execute sync (unless dry run)
            if not dry_run:
                logger.info("Step 4: Executing sync operations")
                self.sync_engine.set_conflict_resolution(conflict_resolution)
                self.execution_statistics = self.execute_sync_operations(
                    self.sync_recommendations, self.loaded_data
                )
                
                # Step 5: Verify sync completion and generate comparison report
                logger.info("Step 5: Verifying sync completion")
                self.verification_report = self.run_sync_verification()
            else:
                logger.info("Step 4: Skipped (dry run mode)")
                self.execution_statistics = None
                self.verification_report = None
            
            # Generate final report
            execution_time = (datetime.now() - start_time).total_seconds()
            final_report = self.generate_final_report(execution_time, dry_run)
            
            logger.info(f"Differential sync workflow completed in {execution_time:.2f} seconds")
            return final_report
            
        except Exception as e:
            logger.error(f"Differential sync workflow failed: {str(e)}")
            raise
    
    def load_json_data(self, entity_list: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load JSON data for specified entities.
        
        Args:
            entity_list: List of entity names to load
            
        Returns:
            Dictionary mapping entity names to their JSON records
        """
        if entity_list is None:
            # Use all available entities from mappings
            entity_list = list(JSON_ENTITY_MAPPINGS.keys())
        
        logger.info(f"Loading JSON data for {len(entity_list)} entities")
        loaded_data = self.json_loader.load_all_entities(entity_list)
        
        # Log loading summary
        total_records = sum(len(records) for records in loaded_data.values())
        logger.info(f"JSON data loaded: {len(loaded_data)} entities, {total_records} total records")
        
        for entity, records in loaded_data.items():
            logger.debug(f"  {entity}: {len(records)} records")
        
        # Check for load errors
        load_summary = self.json_loader.get_load_summary()
        if load_summary['total_errors'] > 0:
            logger.warning(f"JSON loading completed with {load_summary['total_errors']} errors:")
            for error in load_summary['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  {error}")
        
        return loaded_data
    
    def compare_with_database(self, json_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ComparisonResult]:
        """
        Compare JSON data with database records.
        
        Args:
            json_data: Dictionary of JSON data by entity
            
        Returns:
            Dictionary of comparison results by entity
        """
        logger.info(f"Comparing {len(json_data)} entities with database")
        comparison_results = self.comparator.compare_multiple_entities(json_data)
        
        # Log comparison summary
        total_json = sum(r.json_count for r in comparison_results.values())
        total_db = sum(r.db_count for r in comparison_results.values())
        total_missing_in_db = sum(len(r.missing_in_db) for r in comparison_results.values())
        total_missing_in_json = sum(len(r.missing_in_json) for r in comparison_results.values())
        total_potential_updates = sum(len(r.potential_updates) for r in comparison_results.values())
        
        logger.info(f"Comparison completed:")
        logger.info(f"  JSON records: {total_json}")
        logger.info(f"  Database records: {total_db}")
        logger.info(f"  Missing in DB: {total_missing_in_db}")
        logger.info(f"  Missing in JSON: {total_missing_in_json}")
        logger.info(f"  Potential updates: {total_potential_updates}")
        
        return comparison_results
    
    def generate_sync_recommendations(self, comparison_results: Dict[str, ComparisonResult]) -> Dict[str, List[SyncRecommendation]]:
        """
        Generate sync recommendations from comparison results.
        
        Args:
            comparison_results: Comparison results by entity
            
        Returns:
            Dictionary of sync recommendations by entity
        """
        recommendations = {}
        
        for entity_name, comparison_result in comparison_results.items():
            entity_recommendations = self.comparator.generate_sync_recommendations(comparison_result)
            recommendations[entity_name] = entity_recommendations
            
            # Log recommendations summary
            action_counts = {}
            for rec in entity_recommendations:
                action_counts[rec.action] = action_counts.get(rec.action, 0) + rec.record_count
            
            logger.debug(f"Recommendations for {entity_name}: {action_counts}")
        
        # Log overall recommendations summary
        total_recommendations = sum(len(recs) for recs in recommendations.values())
        logger.info(f"Generated {total_recommendations} sync recommendations across {len(recommendations)} entities")
        
        return recommendations
    
    def execute_sync_operations(self, recommendations: Dict[str, List[SyncRecommendation]], 
                               json_data: Dict[str, List[Dict[str, Any]]]) -> SyncStatistics:
        """
        Execute sync operations based on recommendations.
        
        Args:
            recommendations: Sync recommendations by entity
            json_data: JSON data by entity
            
        Returns:
            Overall sync statistics
        """
        logger.info("Executing sync operations")
        statistics = self.sync_engine.execute_all_recommendations(recommendations, json_data)
        
        logger.info(f"Sync execution completed:")
        logger.info(f"  Entities processed: {statistics.total_entities}")
        logger.info(f"  Records processed: {statistics.total_records_processed}")
        logger.info(f"  Inserts: {statistics.total_inserts}")
        logger.info(f"  Updates: {statistics.total_updates}")
        logger.info(f"  Skipped: {statistics.total_skipped}")
        logger.info(f"  Errors: {statistics.total_errors}")
        logger.info(f"  Success rate: {statistics.success_rate:.1f}%")
        
        return statistics
    
    def generate_final_report(self, execution_time: float, dry_run: bool) -> Dict[str, Any]:
        """
        Generate comprehensive final report.
        
        Args:
            execution_time: Total execution time in seconds
            dry_run: Whether this was a dry run
            
        Returns:
            Complete execution report
        """
        report = {
            'execution_summary': {
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time,
                'dry_run': dry_run,
                'database_path': self.database_path,
                'json_base_path': self.json_base_path
            },
            'data_loading': {
                'entities_attempted': len(self.loaded_data),
                'entities_loaded': len([k for k, v in self.loaded_data.items() if v]),
                'total_json_records': sum(len(records) for records in self.loaded_data.values()),
                'load_errors': self.json_loader.get_load_summary()['errors']
            },
            'comparison_results': {},
            'sync_recommendations': {},
            'execution_statistics': None
        }
        
        # Add comparison results summary
        if self.comparison_results:
            report['comparison_results'] = self.comparator.get_summary_report()
        
        # Add sync recommendations summary
        if self.sync_recommendations:
            action_summary = {}
            for entity_recs in self.sync_recommendations.values():
                for rec in entity_recs:
                    action_summary[rec.action] = action_summary.get(rec.action, 0) + rec.record_count
            
            report['sync_recommendations'] = {
                'total_recommendations': sum(len(recs) for recs in self.sync_recommendations.values()),
                'action_summary': action_summary,
                'by_entity': {
                    entity: [
                        {
                            'action': rec.action,
                            'record_count': rec.record_count,
                            'priority': rec.priority,
                            'reason': rec.reason
                        } for rec in recs
                    ] for entity, recs in self.sync_recommendations.items()
                }
            }
        
        # Add execution statistics (if not dry run)
        if self.execution_statistics:
            report['execution_statistics'] = {
                'total_entities': self.execution_statistics.total_entities,
                'total_records_processed': self.execution_statistics.total_records_processed,
                'total_inserts': self.execution_statistics.total_inserts,
                'total_updates': self.execution_statistics.total_updates,
                'total_skipped': self.execution_statistics.total_skipped,
                'total_errors': self.execution_statistics.total_errors,
                'success_rate': self.execution_statistics.success_rate,
                'sync_execution_time': self.execution_statistics.execution_time
            }
        
        # Add verification report (if sync was executed)
        if hasattr(self, 'verification_report') and self.verification_report:
            report['verification_report'] = {
                'timestamp': self.verification_report.timestamp,
                'json_source': self.verification_report.json_source,
                'total_entities': self.verification_report.total_entities,
                'perfect_matches': self.verification_report.perfect_matches,
                'match_percentage': self.verification_report.match_percentage,
                'total_json_records': self.verification_report.total_json_records,
                'total_db_records': self.verification_report.total_db_records,
                'overall_difference': self.verification_report.overall_difference,
                'sync_status': self.verification_report.sync_status,
                'entity_details': [
                    {
                        'entity': comp.entity,
                        'display_name': comp.display_name,
                        'json_count': comp.json_count,
                        'db_count': comp.db_count,
                        'difference': comp.difference,
                        'status': comp.status,
                        'match': comp.match
                    } for comp in self.verification_report.entity_comparisons
                ]
            }
        
        return report
    
    def get_entity_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed status for each entity.
        
        Returns:
            Dictionary with entity status information
        """
        status = {}
        
        for entity in JSON_ENTITY_MAPPINGS.keys():
            entity_status = {
                'json_loaded': entity in self.loaded_data and len(self.loaded_data[entity]) > 0,
                'json_record_count': len(self.loaded_data.get(entity, [])),
                'comparison_completed': entity in self.comparison_results,
                'recommendations_generated': entity in self.sync_recommendations,
                'sync_executed': entity in self.sync_engine.sync_results
            }
            
            if entity in self.comparison_results:
                comparison = self.comparison_results[entity]
                entity_status.update({
                    'db_record_count': comparison.db_count,
                    'missing_in_db': len(comparison.missing_in_db),
                    'missing_in_json': len(comparison.missing_in_json),
                    'potential_updates': len(comparison.potential_updates)
                })
            
            if entity in self.sync_engine.sync_results:
                sync_result = self.sync_engine.sync_results[entity]
                entity_status.update({
                    'sync_success': sync_result.success,
                    'records_processed': sync_result.records_processed,
                    'records_success': sync_result.records_success,
                    'records_failed': sync_result.records_failed
                })
            
            status[entity] = entity_status
        
        return status
    
    def run_sync_verification(self) -> Optional[Any]:
        """
        Run sync verification and generate comparison report.
        
        Returns:
            Verification report data or None if verification fails
        """
        try:
            from .verification import SyncVerificationReporter
            
            logger.info("Running sync verification...")
            reporter = SyncVerificationReporter(self.database_path)
            
            # Generate verification report (don't print to console here, we'll include in final report)
            verification_report = reporter.generate_verification_report(self.json_base_path)
            
            # Log verification summary
            logger.info(f"Verification completed:")
            logger.info(f"  Perfect matches: {verification_report.perfect_matches}/{verification_report.total_entities} entities ({verification_report.match_percentage:.1f}%)")
            logger.info(f"  Overall difference: {verification_report.overall_difference:+,} records")
            logger.info(f"  Status: {verification_report.sync_status}")
            
            return verification_report
            
        except Exception as e:
            logger.error(f"Sync verification failed: {str(e)}")
            return None
    
    def get_formatted_verification_report(self) -> Optional[str]:
        """
        Get a formatted string representation of the verification report.
        
        Returns:
            Formatted verification report string or None if no verification was run
        """
        if not hasattr(self, 'verification_report') or not self.verification_report:
            return None
        
        try:
            from .verification import SyncVerificationReporter
            
            # Create a temporary reporter to use its formatting method
            reporter = SyncVerificationReporter(self.database_path)
            
            # Capture the formatted report by redirecting it to a string
            import io
            import sys
            from contextlib import redirect_stdout
            
            string_buffer = io.StringIO()
            with redirect_stdout(string_buffer):
                reporter.print_formatted_report(self.verification_report)
            
            return string_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate formatted verification report: {str(e)}")
            return f"Verification completed with {self.verification_report.perfect_matches}/{self.verification_report.total_entities} perfect matches ({self.verification_report.match_percentage:.1f}%)"
