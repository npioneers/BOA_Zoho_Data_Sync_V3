# Copied from orchestrator copy.py (class definition and imports only)
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
    def load_json_data(self, entity_list: Optional[list] = None) -> dict:
        from .json_mappings import JSON_ENTITY_MAPPINGS
        logger = logging.getLogger(__name__)
        if entity_list is None:
            entity_list = list(JSON_ENTITY_MAPPINGS.keys())
        logger.info(f"Loading JSON data for {len(entity_list)} entities")
        loaded_data = self.json_loader.load_all_entities(entity_list)
        total_records = sum(len(records) for records in loaded_data.values())
        logger.info(f"JSON data loaded: {len(loaded_data)} entities, {total_records} total records")
        for entity, records in loaded_data.items():
            logger.debug(f"  {entity}: {len(records)} records")
        load_summary = self.json_loader.get_load_summary()
        if load_summary['total_errors'] > 0:
            logger.warning(f"JSON loading completed with {load_summary['total_errors']} errors:")
            for error in load_summary['errors'][:5]:
                logger.warning(f"  {error}")
        return loaded_data

    def compare_with_database(self, json_data: dict) -> dict:
        logger = logging.getLogger(__name__)
        logger.info(f"Comparing {len(json_data)} entities with database")
        comparison_results = self.comparator.compare_multiple_entities(json_data)
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

    def generate_sync_recommendations(self, comparison_results: dict) -> dict:
        logger = logging.getLogger(__name__)
        recommendations = {}
        for entity_name, comparison_result in comparison_results.items():
            entity_recommendations = self.comparator.generate_sync_recommendations(comparison_result)
            recommendations[entity_name] = entity_recommendations
            action_counts = {}
            for rec in entity_recommendations:
                action_counts[rec.action] = action_counts.get(rec.action, 0) + rec.record_count
            logger.debug(f"Recommendations for {entity_name}: {action_counts}")
        total_recommendations = sum(len(recs) for recs in recommendations.values())
        logger.info(f"Generated {total_recommendations} sync recommendations across {len(recommendations)} entities")
        return recommendations

    def execute_sync_operations(self, recommendations: dict, json_data: dict):
        logger = logging.getLogger(__name__)
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

    def generate_final_report(self, execution_time: float, dry_run: bool) -> dict:
        from datetime import datetime
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
        if self.comparison_results:
            report['comparison_results'] = self.comparator.get_summary_report()
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

    def run_sync_verification(self) -> object:
        try:
            from .verification import SyncVerificationReporter
            logger = logging.getLogger(__name__)
            logger.info("Running sync verification...")
            reporter = SyncVerificationReporter(self.database_path)
            verification_report = reporter.generate_verification_report(self.json_base_path)
            logger.info(f"Verification completed:")
            logger.info(f"  Perfect matches: {verification_report.perfect_matches}/{verification_report.total_entities} entities ({verification_report.match_percentage:.1f}%)")
            logger.info(f"  Overall difference: {verification_report.overall_difference:+,} records")
            logger.info(f"  Status: {verification_report.sync_status}")
            return verification_report
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Sync verification failed: {str(e)}")
            return None
    def execute_full_differential_sync(self, entity_list: Optional[list] = None,
                                     conflict_resolution: str = 'json_wins',
                                     dry_run: bool = False) -> dict:
        """
        Execute complete differential sync workflow.
        Args:
            entity_list: List of entities to sync. If None, syncs all available.
            conflict_resolution: Strategy for resolving conflicts ('json_wins', 'db_wins', 'manual')
            dry_run: If True, performs comparison but no database changes
        Returns:
            Dictionary with complete execution results
        """
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)
        start_time = datetime.now()
        logger.info("Starting full differential sync workflow")
        logger.info(f"  Entities: {entity_list or 'All available'}")
        logger.info(f"  Conflict Resolution: {conflict_resolution}")
        logger.info(f"  Dry Run: {dry_run}")
        try:
            self.loaded_data = self.load_json_data(entity_list)
            if not self.loaded_data:
                raise RuntimeError("No JSON data loaded - cannot proceed with sync")
            self.comparison_results = self.compare_with_database(self.loaded_data)
            self.sync_recommendations = self.generate_sync_recommendations(self.comparison_results)
            if not dry_run:
                self.sync_engine.set_conflict_resolution(conflict_resolution)
                self.execution_statistics = self.execute_sync_operations(
                    self.sync_recommendations, self.loaded_data
                )
                self.verification_report = self.run_sync_verification()
            else:
                self.execution_statistics = None
                self.verification_report = None
            execution_time = (datetime.now() - start_time).total_seconds()
            final_report = self.generate_final_report(execution_time, dry_run)
            logger.info(f"Differential sync workflow completed in {execution_time:.2f} seconds")
            return final_report
        except Exception as e:
            logger.error(f"Differential sync workflow failed: {str(e)}")
            raise
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
        from pathlib import Path
        import logging
        logger = logging.getLogger(__name__)
        self.database_path = str(Path(database_path).resolve())
        self.json_base_path = str(Path(json_base_path or "data/raw_json").resolve())
        logger.info("JsonDifferentialSyncOrchestrator initialized:")
        logger.info(f"  Database: {self.database_path}")
        logger.info(f"  JSON Base Path: {self.json_base_path}")
        from .json_loader import JsonDataLoader
        from .json_comparator import JsonDatabaseComparator
        from .json_sync_engine import JsonSyncEngine
        self.json_loader = JsonDataLoader(self.json_base_path)
        self.comparator = JsonDatabaseComparator(self.database_path)
        self.sync_engine = JsonSyncEngine(self.database_path)
        self.loaded_data = {}
        self.comparison_results = {}
        self.sync_recommendations = {}
        self.execution_statistics = None
        self.verification_report = None
