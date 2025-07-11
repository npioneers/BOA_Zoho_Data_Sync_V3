"""
JSON2DB Sync Runner
Pure business logic for JSON to Database synchronization operations.
No user interaction - designed for programmatic access.
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Handle imports for both standalone and module usage
try:
    from .json_analyzer import JSONAnalyzer
    from .table_generator import TableGenerator
    from .json_tables_recreate import JSONTablesRecreator
    from .data_populator import JSONDataPopulator
    from .summary_reporter import SyncSummaryReporter
    from .check_json_tables import check_json_tables
    from .config import get_config
except ImportError:
    from json_analyzer import JSONAnalyzer
    from table_generator import TableGenerator
    from json_tables_recreate import JSONTablesRecreator
    from data_populator import JSONDataPopulator
    from summary_reporter import SyncSummaryReporter
    from check_json_tables import check_json_tables
    from config import get_config


class JSON2DBSyncRunner:
    """Core runner for JSON to Database synchronization operations"""
    
    def __init__(self, db_path: str = None,
                 data_source: str = None,
                 config_file: str = None):
        self.config = get_config(config_file)
        
        # Use provided paths or fall back to configuration
        self.db_path = Path(db_path or self.config.get_database_path())
        self.data_source = data_source or (
            self.config.get_api_sync_path() if self.config.is_api_sync_mode() 
            else self.config.get_consolidated_path()
        )
        self.data_source_type = self.config.get("data_source", "type")
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for runner operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_json_files(self, json_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze JSON files and generate schema information.
        
        Args:
            json_dir: Path to JSON files directory (optional)
            
        Returns:
            Dict containing analysis results and schema information
        """
        try:
            target_dir = json_dir or str(self.json_dir)
            self.logger.info(f"Analyzing JSON files in: {target_dir}")
            
            analyzer = JSONAnalyzer(target_dir)
            schema_analysis = analyzer.analyze_all_files()
            
            return {
                "success": True,
                "schema_analysis": schema_analysis,
                "json_dir": target_dir,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"JSON analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "json_dir": target_dir if 'target_dir' in locals() else str(self.json_dir)
            }

    def generate_table_schemas(self, json_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate SQL table schemas from JSON analysis.
        
        Args:
            json_dir: Path to JSON files directory (optional)
            
        Returns:
            Dict containing generated schemas and SQL statements
        """
        try:
            target_dir = json_dir or str(self.json_dir)
            self.logger.info(f"Generating table schemas from: {target_dir}")
            
            analyzer = JSONAnalyzer(target_dir)
            generator = TableGenerator(analyzer)
            
            # Generate schemas
            table_sql = generator.generate_all_table_sql()
            index_sql = generator.generate_all_index_sql()
            
            return {
                "success": True,
                "table_sql": table_sql,
                "index_sql": index_sql,
                "json_dir": target_dir,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Schema generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "json_dir": target_dir if 'target_dir' in locals() else str(self.json_dir)
            }

    def recreate_json_tables(self, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Recreate JSON tables in existing database (default operation).
        
        Args:
            db_path: Path to database file (optional)
            
        Returns:
            Dict containing recreation results and statistics
        """
        try:
            target_db = db_path or str(self.db_path)
            self.logger.info(f"Recreating JSON tables in: {target_db}")
            
            recreator = JSONTablesRecreator(target_db)
            result = recreator.recreate_all_json_tables()
            
            return {
                "success": result.get("success", False),
                "operation": "recreate_tables",
                "db_path": target_db,
                "statistics": result.get("statistics", {}),
                "errors": result.get("errors", []),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Table recreation failed: {e}")
            return {
                "success": False,
                "operation": "recreate_tables",
                "error": str(e),
                "db_path": target_db if 'target_db' in locals() else str(self.db_path)
            }

    def create_all_tables(self, db_path: Optional[str] = None, force_recreate: bool = False) -> Dict[str, Any]:
        """
        Create all tables (use with caution - for new databases).
        
        Args:
            db_path: Path to database file (optional)
            force_recreate: Whether to recreate existing tables
            
        Returns:
            Dict containing creation results and statistics
        """
        try:
            target_db = db_path or str(self.db_path)
            self.logger.info(f"Creating all tables in: {target_db}")
            
            recreator = JSONTablesRecreator(target_db)
            result = recreator.create_all_tables_full()
            
            return {
                "success": result.get("success", False),
                "operation": "create_all_tables",
                "db_path": target_db,
                "statistics": result.get("statistics", {}),
                "errors": result.get("errors", []),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Table creation failed: {e}")
            return {
                "success": False,
                "operation": "create_all_tables",
                "error": str(e),
                "db_path": target_db if 'target_db' in locals() else str(self.db_path)
            }

    def populate_tables(self, db_path: Optional[str] = None, 
                       json_dir: Optional[str] = None,
                       cutoff_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Populate JSON tables with data from JSON files.
        
        Args:
            db_path: Path to database file (optional)
            json_dir: Path to JSON files directory (optional)
            cutoff_days: Number of days back to filter data (optional)
            
        Returns:
            Dict containing population results and statistics
        """
        try:
            target_db = db_path or str(self.db_path)
            target_json = json_dir or str(self.json_dir)
            
            self.logger.info(f"Populating tables in {target_db} with data from {target_json}")
            if cutoff_days:
                self.logger.info(f"Using cutoff filter: {cutoff_days} days")
            
            populator = JSONDataPopulator(target_db, target_json)
            
            if cutoff_days:
                result = populator.populate_all_tables_with_cutoff(cutoff_days)
            else:
                result = populator.populate_all_tables()
            
            return {
                "success": result.get("success", False),
                "operation": "populate_tables",
                "db_path": target_db,
                "json_dir": target_json,
                "cutoff_days": cutoff_days,
                "statistics": result.get("statistics", {}),
                "errors": result.get("errors", []),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Table population failed: {e}")
            return {
                "success": False,
                "operation": "populate_tables",
                "error": str(e),
                "db_path": target_db if 'target_db' in locals() else str(self.db_path),
                "json_dir": target_json if 'target_json' in locals() else str(self.json_dir)
            }

    def verify_tables(self, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify JSON tables structure and data.
        
        Args:
            db_path: Path to database file (optional)
            
        Returns:
            Dict containing verification results
        """
        try:
            target_db = db_path or str(self.db_path)
            self.logger.info(f"Verifying tables in: {target_db}")
            
            # Use check_json_tables functionality
            verification_result = check_json_tables()
            
            return {
                "success": True,
                "operation": "verify_tables",
                "db_path": target_db,
                "verification_result": verification_result,
                "verified_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Table verification failed: {e}")
            return {
                "success": False,
                "operation": "verify_tables",
                "error": str(e),
                "db_path": target_db if 'target_db' in locals() else str(self.db_path)
            }

    def generate_summary_report(self, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate summary report of database state.
        
        Args:
            db_path: Path to database file (optional)
            
        Returns:
            Dict containing summary report
        """
        try:
            target_db = db_path or str(self.db_path)
            self.logger.info(f"Generating summary report for: {target_db}")
            
            reporter = SyncSummaryReporter(target_db)
            report = reporter.generate_full_summary()
            
            return {
                "success": True,
                "operation": "summary_report",
                "db_path": target_db,
                "report": report,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Summary report generation failed: {e}")
            return {
                "success": False,
                "operation": "summary_report",
                "error": str(e),
                "db_path": target_db if 'target_db' in locals() else str(self.db_path)
            }

    def full_sync_workflow(self, db_path: Optional[str] = None,
                          json_dir: Optional[str] = None,
                          cutoff_days: Optional[int] = None,
                          skip_table_creation: bool = False) -> Dict[str, Any]:
        """
        Execute complete JSON to DB sync workflow.
        
        Args:
            db_path: Path to database file (optional)
            json_dir: Path to JSON files directory (optional)
            cutoff_days: Number of days back to filter data (optional)
            skip_table_creation: Skip table recreation step
            
        Returns:
            Dict containing workflow results
        """
        workflow_results = {
            "success": False,
            "operation": "full_sync_workflow",
            "steps_completed": [],
            "steps_failed": [],
            "overall_statistics": {},
            "started_at": datetime.now().isoformat()
        }
        
        try:
            target_db = db_path or str(self.db_path)
            target_json = json_dir or str(self.json_dir)
            
            self.logger.info("Starting full JSON2DB sync workflow")
            self.logger.info(f"Database: {target_db}")
            self.logger.info(f"JSON Source: {target_json}")
            
            # Step 1: Analyze JSON files
            self.logger.info("Step 1: Analyzing JSON files...")
            analysis_result = self.analyze_json_files(target_json)
            if analysis_result["success"]:
                workflow_results["steps_completed"].append("json_analysis")
                workflow_results["json_analysis"] = analysis_result
            else:
                workflow_results["steps_failed"].append("json_analysis")
                workflow_results["json_analysis"] = analysis_result
                return workflow_results
            
            # Step 2: Recreate tables (unless skipped)
            if not skip_table_creation:
                self.logger.info("Step 2: Recreating JSON tables...")
                tables_result = self.recreate_json_tables(target_db)
                if tables_result["success"]:
                    workflow_results["steps_completed"].append("table_recreation")
                    workflow_results["table_recreation"] = tables_result
                else:
                    workflow_results["steps_failed"].append("table_recreation")
                    workflow_results["table_recreation"] = tables_result
                    return workflow_results
            else:
                self.logger.info("Step 2: Skipping table recreation")
                workflow_results["steps_completed"].append("table_recreation_skipped")
            
            # Step 3: Populate tables
            self.logger.info("Step 3: Populating tables with data...")
            population_result = self.populate_tables(target_db, target_json, cutoff_days)
            if population_result["success"]:
                workflow_results["steps_completed"].append("data_population")
                workflow_results["data_population"] = population_result
            else:
                workflow_results["steps_failed"].append("data_population")
                workflow_results["data_population"] = population_result
                return workflow_results
            
            # Step 4: Verify tables
            self.logger.info("Step 4: Verifying tables...")
            verification_result = self.verify_tables(target_db)
            if verification_result["success"]:
                workflow_results["steps_completed"].append("verification")
                workflow_results["verification"] = verification_result
            else:
                workflow_results["steps_failed"].append("verification")
                workflow_results["verification"] = verification_result
                # Don't fail workflow for verification issues
            
            # Step 5: Generate summary
            self.logger.info("Step 5: Generating summary report...")
            summary_result = self.generate_summary_report(target_db)
            if summary_result["success"]:
                workflow_results["steps_completed"].append("summary_report")
                workflow_results["summary_report"] = summary_result
            else:
                workflow_results["steps_failed"].append("summary_report")
                workflow_results["summary_report"] = summary_result
                # Don't fail workflow for summary issues
            
            # Workflow completed successfully
            workflow_results["success"] = True
            workflow_results["completed_at"] = datetime.now().isoformat()
            
            self.logger.info("Full JSON2DB sync workflow completed successfully")
            return workflow_results
            
        except Exception as e:
            self.logger.error(f"Full sync workflow failed: {e}")
            workflow_results["error"] = str(e)
            workflow_results["failed_at"] = datetime.now().isoformat()
            return workflow_results


def run_json_analysis(json_dir: str = None) -> Dict[str, Any]:
    """Standalone function for JSON analysis"""
    runner = JSON2DBSyncRunner()
    if json_dir is None:
        config = get_config()
        json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                   else config.get_consolidated_path())
    return runner.analyze_json_files(json_dir)


def run_table_recreation(db_path: str = None) -> Dict[str, Any]:
    """Standalone function for table recreation"""
    runner = JSON2DBSyncRunner()
    if db_path is None:
        config = get_config()
        db_path = config.get_database_path()
    return runner.recreate_json_tables(db_path)


def run_data_population(db_path: str = None,
                       json_dir: str = None,
                       cutoff_days: Optional[int] = None) -> Dict[str, Any]:
    """Standalone function for data population"""
    runner = JSON2DBSyncRunner()
    config = get_config()
    
    if db_path is None:
        db_path = config.get_database_path()
    if json_dir is None:
        json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                   else config.get_consolidated_path())
    
    return runner.populate_tables(db_path, json_dir, cutoff_days)


def run_full_workflow(db_path: str = None,
                     json_dir: str = None,
                     cutoff_days: Optional[int] = None,
                     skip_table_creation: bool = False) -> Dict[str, Any]:
    """Standalone function for full workflow"""
    runner = JSON2DBSyncRunner()
    config = get_config()
    
    if db_path is None:
        db_path = config.get_database_path()
    if json_dir is None:
        json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                   else config.get_consolidated_path())
    
    return runner.full_sync_workflow(db_path, json_dir, cutoff_days, skip_table_creation)
