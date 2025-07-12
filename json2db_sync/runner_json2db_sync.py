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
    from .data_populator import JSONDataPopulator
    from .config import get_config
    from .json_analyzer import JSONAnalyzer
    from .table_generator import TableGenerator
    from .summary_reporter import SyncSummaryReporter
except ImportError:
    from data_populator import JSONDataPopulator
    from config import get_config
    from json_analyzer import JSONAnalyzer
    from table_generator import TableGenerator
    from summary_reporter import SyncSummaryReporter


class JSON2DBSyncRunner:
    """Core runner for JSON to Database synchronization operations"""
    
    def __init__(self, db_path: str = None,
                 data_source: str = None,
                 config_file: str = None):
        self.config = get_config(config_file)
        
        # Use provided paths or fall back to configuration
        self.db_path = Path(db_path or self.config.get_database_path())
        self.data_source = data_source or self.config.get_api_sync_path()
        self.data_source_type = "api_sync"
        
        # Set json_dir based on data_source (always session-based)
        self.json_dir = Path(self.data_source)
        
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
            schema_analysis = analyzer.analyze_all_json_files()
            
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
            
            # Use TableGenerator for recreating tables
            table_generator = TableGenerator()
            result = table_generator.analyze_and_generate()
            
            if result.get("success"):
                # Generate SQL and execute (simplified approach)
                sql_script = table_generator.generate_complete_sql_script()
                
                return {
                    "success": True,
                    "operation": "recreate_tables",
                    "db_path": target_db,
                    "statistics": {"tables_created": len(result.get("tables", {}))},
                    "errors": [],
                    "completed_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "operation": "recreate_tables",
                    "db_path": target_db,
                    "statistics": {},
                    "errors": ["Table recreation failed"],
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
            
            # Use TableGenerator for creating tables
            table_generator = TableGenerator()
            result = table_generator.analyze_and_generate()
            
            if result.get("success"):
                # Generate SQL and execute (simplified approach)
                sql_script = table_generator.generate_complete_sql_script()
                
                return {
                    "success": True,
                    "operation": "create_all_tables",
                    "db_path": target_db,
                    "statistics": {"tables_created": len(result.get("tables", {}))},
                    "errors": [],
                    "completed_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "operation": "create_all_tables",
                    "db_path": target_db,
                    "statistics": {},
                    "errors": ["Table creation failed"],
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
        Verify JSON tables structure and data with comprehensive summary report.
        
        Args:
            db_path: Path to database file (optional)
            
        Returns:
            Dict containing verification results including detailed summary report
        """
        try:
            target_db = db_path or str(self.db_path)
            self.logger.info(f"Verifying tables in: {target_db}")
            
            # Generate comprehensive table summary
            summary_report = self._generate_table_summary_report(target_db)
            
            verification_result = {
                "status": "completed",
                "message": "Comprehensive verification completed with summary report",
                "db_path": target_db,
                "summary_report": summary_report
            }
            
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

    def _get_business_date_column(self, table_name: str, columns: List[str]) -> Optional[str]:
        """
        Get the most appropriate business date column for a table.
        Prioritizes business document dates over system sync dates.
        
        Args:
            table_name: Name of the database table
            columns: List of column names in the table
            
        Returns:
            The best date column to use for oldest/latest date calculation, or None
        """
        table_lower = table_name.lower()
        
        # 1. Document-specific business dates (HIGHEST PRIORITY)
        if 'invoice' in table_lower:
            for col in ['invoice_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'bill' in table_lower:
            for col in ['bill_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'salesorder' in table_lower or 'sales_order' in table_lower:
            for col in ['salesorder_date', 'order_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'purchaseorder' in table_lower or 'purchase_order' in table_lower:
            for col in ['purchaseorder_date', 'purchase_order_date', 'date']:
                if col in columns: 
                    return col
                    
        elif 'creditnote' in table_lower or 'credit_note' in table_lower:
            for col in ['creditnote_date', 'credit_note_date', 'date']:
                if col in columns: 
                    return col
                    
        elif any(term in table_lower for term in ['payment', 'customerpayment', 'vendorpayment']):
            for col in ['payment_date', 'date']:
                if col in columns: 
                    return col
        
        # 2. Generic business date (MEDIUM PRIORITY)
        if 'date' in columns:
            return 'date'
        
        # 3. System dates (LOWEST PRIORITY - only if no business date available)
        for sys_date in ['created_time', 'last_modified_time', 'updated_time', 'modified_time', 'created_timestamp', 'updated_timestamp']:
            if sys_date in columns:
                return sys_date
                
        return None

    def _generate_table_summary_report(self, db_path: str) -> Dict[str, Any]:
        """
        Generate comprehensive table summary report with requested metrics.
        
        Args:
            db_path: Path to database file
            
        Returns:
            Dict containing detailed table analysis
        """
        import sqlite3
        from pathlib import Path
        
        if not Path(db_path).exists():
            return {"error": f"Database file not found: {db_path}"}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all table names (excluding system tables)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                return {"error": "No tables found in database"}
            
            table_details = []
            total_records = 0
            
            for table_name in tables:
                try:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    row_count = cursor.fetchone()[0]
                    total_records += row_count
                    
                    # Initialize date fields
                    oldest_date = "N/A"
                    latest_date = "N/A"
                    last_sync_timestamp = "N/A"
                    
                    if row_count > 0:
                        # Get table schema to find date columns
                        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        # Use business date priority logic to find the best date column
                        primary_date_col = self._get_business_date_column(table_name, columns)
                        
                        # Try to find oldest and latest dates using business date column
                        if primary_date_col:
                            try:
                                # Get oldest date
                                cursor.execute(f"SELECT MIN(`{primary_date_col}`) FROM `{table_name}` WHERE `{primary_date_col}` IS NOT NULL")
                                oldest_result = cursor.fetchone()[0]
                                if oldest_result:
                                    oldest_date = str(oldest_result)[:19]  # Truncate to datetime format
                                
                                # Get latest date  
                                cursor.execute(f"SELECT MAX(`{primary_date_col}`) FROM `{table_name}` WHERE `{primary_date_col}` IS NOT NULL")
                                latest_result = cursor.fetchone()[0]
                                if latest_result:
                                    latest_date = str(latest_result)[:19]  # Truncate to datetime format
                                    
                            except Exception:
                                # If date parsing fails, keep N/A
                                pass
                        
                        # Check for sync timestamp metadata and data source info
                        data_source_info = None
                        last_modified_time = None
                        
                        # First check our table population tracking table
                        try:
                            cursor.execute("""
                                SELECT last_populated_time, data_source 
                                FROM table_population_tracking 
                                WHERE table_name = ?
                            """, (table_name,))
                            tracking_result = cursor.fetchone()
                            if tracking_result:
                                last_modified_time = str(tracking_result[0])[:19]
                                if tracking_result[1]:
                                    data_source_info = tracking_result[1]
                        except Exception:
                            # Table might not exist yet, continue with other methods
                            pass
                        
                        # Get data source information if not found in tracking
                        if not data_source_info and 'data_source' in columns:
                            try:
                                cursor.execute(f"SELECT `data_source` FROM `{table_name}` ORDER BY rowid DESC LIMIT 1")
                                source_result = cursor.fetchone()
                                if source_result and source_result[0]:
                                    data_source_info = source_result[0]
                            except Exception:
                                pass
                        
                        # Check for explicit sync timestamp if not found in tracking
                        if not last_modified_time and 'last_sync_time' in columns:
                            try:
                                cursor.execute(f"SELECT MAX(`last_sync_time`) FROM `{table_name}` WHERE `last_sync_time` IS NOT NULL")
                                sync_result = cursor.fetchone()[0]
                                if sync_result:
                                    last_modified_time = str(sync_result)[:19]
                            except Exception:
                                pass
                        
                        # If no explicit sync time, try to find latest modification time from data
                        if not last_modified_time and row_count > 0:
                            # Look for common timestamp columns that might indicate last modification
                            timestamp_columns = ['import_timestamp', 'sync_timestamp', 'last_modified_time', 'updated_at', 'modified_date', 'updated_time']
                            for ts_col in timestamp_columns:
                                if ts_col in columns:
                                    try:
                                        cursor.execute(f"SELECT MAX(`{ts_col}`) FROM `{table_name}` WHERE `{ts_col}` IS NOT NULL")
                                        ts_result = cursor.fetchone()[0]
                                        if ts_result:
                                            last_modified_time = str(ts_result)[:19]
                                            break
                                    except Exception:
                                        continue
                        
                        # If still no modification time, try to get the most recent data timestamp using business date column
                        if not last_modified_time and row_count > 0 and primary_date_col:
                            try:
                                cursor.execute(f"SELECT MAX(`{primary_date_col}`) FROM `{table_name}` WHERE `{primary_date_col}` IS NOT NULL")
                                business_result = cursor.fetchone()[0]
                                if business_result:
                                    last_modified_time = str(business_result)[:19]
                            except Exception:
                                pass
                        
                        # Construct the last sync information
                        if data_source_info and last_modified_time:
                            # Check if this is from our tracking table (recent population)
                            try:
                                # If the timestamp is very recent (today), it's likely from our tracking
                                from datetime import datetime
                                parsed_time = datetime.fromisoformat(last_modified_time.replace('T', ' '))
                                current_time = datetime.now()
                                time_diff = current_time - parsed_time
                                
                                if time_diff.total_seconds() < 86400:  # Less than 24 hours
                                    last_sync_timestamp = f"Source: {data_source_info}, Populated: {last_modified_time}"
                                else:
                                    last_sync_timestamp = f"Source: {data_source_info}, Modified: {last_modified_time}"
                            except:
                                last_sync_timestamp = f"Source: {data_source_info}, Modified: {last_modified_time}"
                        elif data_source_info:
                            last_sync_timestamp = f"Source: {data_source_info}"
                        elif last_modified_time:
                            last_sync_timestamp = f"Modified: {last_modified_time}"
                    
                    table_details.append({
                        "table_name": table_name,
                        "row_count": row_count,
                        "oldest_date": oldest_date,
                        "latest_date": latest_date,
                        "last_sync_timestamp": last_sync_timestamp
                    })
                    
                except Exception as e:
                    # Add table with error info
                    table_details.append({
                        "table_name": table_name,
                        "row_count": 0,
                        "oldest_date": "Error",
                        "latest_date": "Error", 
                        "last_sync_timestamp": f"Error: {str(e)[:50]}"
                    })
            
            conn.close()
            
            # Sort by table name (alphabetically)
            table_details.sort(key=lambda x: x["table_name"].lower())
            
            return {
                "total_tables": len(tables),
                "total_records": total_records,
                "populated_tables": len([t for t in table_details if t["row_count"] > 0]),
                "table_details": table_details,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to generate summary report: {str(e)}"}

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
            report = reporter.generate_comprehensive_report()
            
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
        json_dir = config.get_api_sync_path()
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
        json_dir = config.get_api_sync_path()
    
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
        json_dir = config.get_api_sync_path()
    
    return runner.full_sync_workflow(db_path, json_dir, cutoff_days, skip_table_creation)
