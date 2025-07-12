"""
Global Zoho Data Sync Runner
Pure business logic for orchestrating api_sync, json2db_sync, and csv_db_rebuild packages.
No user interaction - designed for programmatic access.
"""
import sys
import os
from pathlib import Path
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import importlib.util
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from global_runner.config import GlobalSyncConfig


class GlobalSyncRunner:
    """
    Pure business logic runner for global Zoho data sync operations.
    Orchestrates api_sync, json2db_sync, and csv_db_rebuild packages.
    """
    
    def __init__(self, config_file: Optional[str] = None, enable_logging: bool = True):
        """
        Initialize the global sync runner.
        
        Args:
            config_file: Path to configuration file
            enable_logging: Whether to enable logging
        """
        self.config = GlobalSyncConfig(config_file)
        self.enable_logging = enable_logging
        self.logger = None
        
        if self.enable_logging:
            self._setup_logging()
        
        # Package runners (loaded on demand)
        self._api_sync_runner = None
        self._json2db_sync_runner = None
        self._csv_db_rebuild_runner = None
        
        # Store original working directory for package execution
        self._original_cwd = os.getcwd()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        log_dir = Path(self.config.get('logging.log_dir', '../logs'))
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"global_sync_{timestamp}.log"
        
        # Create logger for this instance
        self.logger = logging.getLogger(f"global_sync_{timestamp}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self._log(f"Global Sync Log: {log_file}")
    
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if logging is enabled"""
        if self.logger:
            getattr(self.logger, level.lower(), self.logger.info)(message)
    
    def _execute_in_package_directory(self, package_name: str, func, *args, **kwargs):
        """
        Execute a function in the package's directory for proper path resolution.
        
        Args:
            package_name: Name of the package
            func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function execution
        """
        package_config = self.config.get_package_config(package_name)
        if not package_config:
            raise ValueError(f"Package {package_name} not configured")
        
        package_path = Path(package_config['path']).resolve()
        original_cwd = os.getcwd()
        
        try:
            # Change to package directory
            os.chdir(package_path)
            self._log(f"Executing {func.__name__} in directory: {package_path}")
            
            # Execute the function
            result = func(*args, **kwargs)
            return result
            
        finally:
            # Always restore original directory
            os.chdir(original_cwd)
    
    def _import_package_runner(self, package_name: str):
        """Dynamically import a package runner"""
        try:
            package_config = self.config.get_package_config(package_name)
            if not package_config or not self.config.is_package_enabled(package_name):
                self._log(f"Package {package_name} is not enabled or configured", "warning")
                return None
            
            package_path = Path(package_config['path']).resolve()
            runner_module = package_config['runner_module']
            
            # Add package directory to sys.path for proper local imports
            package_path_str = str(package_path)
            path_added = False
            if package_path_str not in sys.path:
                sys.path.insert(0, package_path_str)
                path_added = True
            
            try:
                # Import the runner module
                spec = importlib.util.spec_from_file_location(
                    runner_module, 
                    package_path / f"{runner_module}.py"
                )
                if not spec or not spec.loader:
                    self._log(f"Could not load {runner_module} from {package_path}", "error")
                    return None
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[runner_module] = module
                spec.loader.exec_module(module)
                
                # Get the runner class (assuming it follows naming convention)
                runner_class_name = self._get_runner_class_name(package_name)
                runner_class = getattr(module, runner_class_name, None)
                
                if not runner_class:
                    self._log(f"Could not find runner class {runner_class_name} in {runner_module}", "error")
                    return None
                
                self._log(f"Successfully imported {runner_class_name} from {package_name}")
                return runner_class
            
            finally:
                # Clean up sys.path if we added it
                if path_added and package_path_str in sys.path:
                    sys.path.remove(package_path_str)
            
        except Exception as e:
            self._log(f"Error importing {package_name} runner: {str(e)}", "error")
            return None
    
    def _get_runner_class_name(self, package_name: str) -> str:
        """Get the expected runner class name for a package"""
        class_names = {
            'api_sync': 'ApiSyncRunner',
            'json2db_sync': 'JSON2DBSyncRunner',
            'csv_db_rebuild': 'CSVDatabaseRebuildRunner'
        }
        return class_names.get(package_name, f'{package_name.title()}Runner')
    
    def _get_api_sync_runner(self):
        """Get or create API sync runner"""
        if self._api_sync_runner is None:
            def _create_runner():
                runner_class = self._import_package_runner('api_sync')
                if runner_class:
                    return runner_class()
                return None
            
            # Execute runner creation in the api_sync directory
            self._api_sync_runner = self._execute_in_package_directory('api_sync', _create_runner)
        return self._api_sync_runner
    
    def _get_json2db_sync_runner(self):
        """Get or create JSON2DB sync runner"""
        if self._json2db_sync_runner is None:
            def _create_runner():
                runner_class = self._import_package_runner('json2db_sync')
                if runner_class:
                    # Initialize with configuration
                    config_path = self.config.get('packages.json2db_sync.config_path')
                    return runner_class(config_file=config_path)
                return None
            
            # Execute runner creation in the json2db_sync directory
            self._json2db_sync_runner = self._execute_in_package_directory('json2db_sync', _create_runner)
        return self._json2db_sync_runner
    
    def _get_csv_db_rebuild_runner(self):
        """Get or create CSV DB rebuild runner"""
        if self._csv_db_rebuild_runner is None:
            runner_class = self._import_package_runner('csv_db_rebuild')
            if runner_class:
                # Initialize with database and CSV paths
                db_path = self.config.get_database_path()
                csv_dir = self.config.get('packages.csv_db_rebuild.csv_data_path')
                self._csv_db_rebuild_runner = runner_class(
                    db_path=db_path,
                    csv_dir=csv_dir,
                    enable_logging=False  # We handle logging globally
                )
        return self._csv_db_rebuild_runner
    
    def check_database_freshness(self) -> Dict[str, Any]:
        """
        Check database freshness by examining the latest data timestamps.
        
        Returns:
            Dictionary with freshness analysis results
        """
        self._log("Starting database freshness check...")
        
        try:
            db_path = self.config.get_database_path()
            if not Path(db_path).exists():
                return {
                    "success": False,
                    "error": f"Database not found at {db_path}",
                    "tables_checked": 0,
                    "fresh_tables": 0,
                    "stale_tables": 0
                }
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            tables_to_check = self.config.get_freshness_tables()
            threshold_days = self.config.get('sync_pipeline.freshness_threshold_days', 1)
            cutoff_date = datetime.now() - timedelta(days=threshold_days)
            
            results = {
                "success": True,
                "check_timestamp": datetime.now().isoformat(),
                "threshold_days": threshold_days,
                "cutoff_date": cutoff_date.isoformat(),
                "tables_checked": len(tables_to_check),
                "fresh_tables": 0,
                "stale_tables": 0,
                "table_details": {},
                "overall_status": "fresh"
            }
            
            for table_name in tables_to_check:
                try:
                    # Check if table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                    if not cursor.fetchone():
                        results["table_details"][table_name] = {
                            "status": "missing",
                            "record_count": 0,
                            "latest_date": None,
                            "days_old": None
                        }
                        results["stale_tables"] += 1
                        continue
                    
                    # Get record count
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    record_count = cursor.fetchone()[0]
                    
                    if record_count == 0:
                        results["table_details"][table_name] = {
                            "status": "empty",
                            "record_count": 0,
                            "latest_date": None,
                            "days_old": None
                        }
                        results["stale_tables"] += 1
                        continue
                    
                    # Get latest date
                    date_column = self.config.get_date_column_for_table(table_name)
                    columns = None
                    
                    if not date_column:
                        # Try common date columns
                        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                        columns = [row[1] for row in cursor.fetchall()]
                        date_column = self._find_best_date_column(columns)
                    
                    # If we still don't have columns, get them now
                    if not columns:
                        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                        columns = [row[1] for row in cursor.fetchall()]
                    
                    if date_column and date_column in columns:
                        cursor.execute(f"SELECT MAX(`{date_column}`) FROM `{table_name}` WHERE `{date_column}` IS NOT NULL")
                        latest_date_str = cursor.fetchone()[0]
                        
                        if latest_date_str:
                            try:
                                # Handle different date formats
                                latest_date = self._parse_date(latest_date_str)
                                days_old = (datetime.now() - latest_date).days
                                
                                status = "fresh" if latest_date >= cutoff_date else "stale"
                                if status == "fresh":
                                    results["fresh_tables"] += 1
                                else:
                                    results["stale_tables"] += 1
                                
                                results["table_details"][table_name] = {
                                    "status": status,
                                    "record_count": record_count,
                                    "latest_date": latest_date.isoformat(),
                                    "days_old": days_old,
                                    "date_column": date_column
                                }
                            except:
                                results["table_details"][table_name] = {
                                    "status": "date_error",
                                    "record_count": record_count,
                                    "latest_date": latest_date_str,
                                    "days_old": None,
                                    "date_column": date_column
                                }
                                results["stale_tables"] += 1
                        else:
                            results["table_details"][table_name] = {
                                "status": "no_dates",
                                "record_count": record_count,
                                "latest_date": None,
                                "days_old": None,
                                "date_column": date_column
                            }
                            results["stale_tables"] += 1
                    else:
                        results["table_details"][table_name] = {
                            "status": "no_date_column",
                            "record_count": record_count,
                            "latest_date": None,
                            "days_old": None,
                            "date_column": None
                        }
                        results["stale_tables"] += 1
                
                except Exception as e:
                    self._log(f"Error checking table {table_name}: {str(e)}", "warning")
                    results["table_details"][table_name] = {
                        "status": "error",
                        "error": str(e),
                        "record_count": 0,
                        "latest_date": None,
                        "days_old": None
                    }
                    results["stale_tables"] += 1
            
            conn.close()
            
            # Determine overall status
            if results["stale_tables"] > 0:
                results["overall_status"] = "stale"
            elif results["fresh_tables"] == 0:
                results["overall_status"] = "empty"
            
            self._log(f"Freshness check completed: {results['fresh_tables']} fresh, {results['stale_tables']} stale")
            return results
            
        except Exception as e:
            error_msg = f"Error during freshness check: {str(e)}"
            self._log(error_msg, "error")
            return {
                "success": False,
                "error": error_msg,
                "tables_checked": 0,
                "fresh_tables": 0,
                "stale_tables": 0
            }
    
    def _find_best_date_column(self, columns: List[str]) -> Optional[str]:
        """Find the best date column from available columns"""
        date_preferences = [
            'last_modified_time', 'modified_time', 'updated_time',
            'created_time', 'date', 'invoice_date', 'bill_date',
            'order_date', 'payment_date'
        ]
        
        for pref in date_preferences:
            if pref in columns:
                return pref
        
        # Look for any column with 'date' or 'time' in the name
        for col in columns:
            if 'date' in col.lower() or 'time' in col.lower():
                return col
        
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in various formats, always returning timezone-naive datetime"""
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Convert to timezone-naive if needed
                return parsed_date.replace(tzinfo=None) if parsed_date.tzinfo else parsed_date
            except ValueError:
                continue
        
        # Handle timezone format like +0600 by removing timezone info
        if '+' in date_str and 'T' in date_str:
            try:
                # Remove timezone info and parse
                date_part = date_str.split('+')[0]
                return datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                pass
        
        # Handle timezone format like -0600 by removing timezone info
        if '-' in date_str and 'T' in date_str:
            try:
                # Remove timezone info and parse (split on last dash to avoid splitting date)
                parts = date_str.rsplit('-', 1)
                if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 4:
                    date_part = parts[0]
                    return datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                pass
        
        # If all fails, try to parse just the date part
        date_part = date_str.split()[0] if ' ' in date_str else date_str
        try:
            return datetime.strptime(date_part, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Could not parse date: {date_str}")
    
    def run_full_sync(self, cutoff_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Run complete sync pipeline: api_sync -> json2db_sync -> freshness check.
        
        Args:
            cutoff_days: Number of days to look back for data (None for intelligent detection)
            
        Returns:
            Dictionary with sync results from all stages
        """
        start_time = datetime.now()
        cutoff_days = cutoff_days or self.config.get('sync_pipeline.default_cutoff_days', 30)
        
        self._log(f"Starting full sync pipeline using intelligent detection...")
        
        results = {
            "success": False,
            "start_time": start_time.isoformat(),
            "stages_completed": [],
            "stages_failed": [],
            "api_sync_result": None,
            "json2db_sync_result": None,
            "freshness_check_result": None,
            "total_processing_time": None
        }
        
        try:
            # Stage 1: API Sync
            self._log("Stage 1: Running API sync...")
            api_runner = self._get_api_sync_runner()
            if api_runner:
                try:
                    # Define the API sync execution function
                    def _execute_api_sync():
                        # Use API sync's intelligent timestamp detection instead of forcing global cutoff
                        # This allows API sync to determine optimal timestamp based on database state
                        return api_runner.fetch_all_modules(
                            since_timestamp=None,  # Let API sync determine optimal timestamp
                            full_sync=False
                        )
                    
                    # Execute API sync in its own directory
                    api_result = self._execute_in_package_directory('api_sync', _execute_api_sync)
                    
                    # Extract summary from API sync result
                    if api_result and "summary" in api_result:
                        summary = api_result["summary"]
                        results["api_sync_result"] = {
                            "success": summary.get("success", False),
                            "modules_processed": summary.get("modules_processed", 0),
                            "total_records": summary.get("total_records", 0),
                            "failed_modules": summary.get("failed_modules", []),
                            "output_dir": summary.get("output_dir", "")
                        }
                        
                        if summary.get("success", False):
                            results["stages_completed"].append("api_sync")
                            self._log(f"API sync completed successfully - {summary.get('total_records', 0)} records")
                        else:
                            results["stages_failed"].append("api_sync")
                            failed_modules = summary.get("failed_modules", [])
                            self._log(f"API sync partially failed - failed modules: {failed_modules}", "warning")
                            # Continue to next stage even if some modules failed
                    else:
                        results["stages_failed"].append("api_sync")
                        results["api_sync_result"] = {"success": False, "error": "Invalid API sync result format"}
                        self._log("API sync failed - invalid result format", "error")
                        return results
                        
                except Exception as e:
                    results["stages_failed"].append("api_sync")
                    results["api_sync_result"] = {"success": False, "error": f"API sync exception: {str(e)}"}
                    self._log(f"API sync failed with exception: {str(e)}", "error")
                    return results
            else:
                results["stages_failed"].append("api_sync")
                results["api_sync_result"] = {"success": False, "error": "Could not initialize API sync runner"}
                self._log("API sync failed - could not initialize runner", "error")
                return results
            
            # Stage 2: JSON2DB Sync
            self._log("Stage 2: Running JSON2DB sync...")
            json2db_runner = self._get_json2db_sync_runner()
            if json2db_runner:
                try:
                    # Define the JSON2DB sync execution function
                    def _execute_json2db_sync():
                        # Use proper parameters to ensure enhanced reporting works
                        # This will use session-based data, 30-day cutoff, and duplicate prevention
                        return json2db_runner.populate_tables(
                            db_path=None,  # Use default from config
                            json_dir=None,  # Use default from config  
                            cutoff_days=30  # Ensure cutoff is applied for enhanced reporting
                        )
                    
                    # Execute JSON2DB sync in its own directory
                    json2db_result = self._execute_in_package_directory('json2db_sync', _execute_json2db_sync)
                    
                    results["json2db_sync_result"] = json2db_result
                    if json2db_result.get("success", False):
                        results["stages_completed"].append("json2db_sync")
                        # Extract useful metrics
                        tables_processed = json2db_result.get("tables_processed", 0)
                        total_records = json2db_result.get("total_records_processed", 0)
                        self._log(f"JSON2DB sync completed successfully - {tables_processed} tables, {total_records} records")
                    else:
                        results["stages_failed"].append("json2db_sync")
                        error_msg = json2db_result.get("error", "Unknown error")
                        self._log(f"JSON2DB sync failed: {error_msg}", "error")
                        return results
                        
                except Exception as e:
                    results["stages_failed"].append("json2db_sync")
                    results["json2db_sync_result"] = {"success": False, "error": f"JSON2DB sync exception: {str(e)}"}
                    self._log(f"JSON2DB sync failed with exception: {str(e)}", "error")
                    return results
            else:
                results["stages_failed"].append("json2db_sync")
                results["json2db_sync_result"] = {"success": False, "error": "Could not initialize JSON2DB sync runner"}
                self._log("JSON2DB sync failed - could not initialize runner", "error")
                return results
            
            # Stage 3: Final freshness check
            self._log("Stage 3: Running final freshness check...")
            freshness_result = self.check_database_freshness()
            results["freshness_check_result"] = freshness_result
            if freshness_result.get("success", False):
                results["stages_completed"].append("freshness_check")
                self._log("Final freshness check completed")
            else:
                results["stages_failed"].append("freshness_check")
                self._log("Final freshness check failed", "warning")
            
            # Calculate total time
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            results["total_processing_time"] = total_time
            results["end_time"] = end_time.isoformat()
            
            # Determine overall success
            results["success"] = len(results["stages_failed"]) == 0
            
            success_msg = f"Full sync pipeline completed in {total_time:.1f} seconds"
            if results["success"]:
                success_msg += " - All stages successful"
            else:
                success_msg += f" - {len(results['stages_failed'])} stages failed"
            
            self._log(success_msg)
            return results
            
        except Exception as e:
            error_msg = f"Error during full sync pipeline: {str(e)}"
            self._log(error_msg, "error")
            results["error"] = error_msg
            return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including package availability and database status.
        
        Returns:
            Dictionary with system status information
        """
        self._log("Checking system status...")
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "database_status": {},
            "package_status": {},
            "configuration": {
                "cutoff_days": self.config.get('sync_pipeline.default_cutoff_days'),
                "freshness_threshold": self.config.get('sync_pipeline.freshness_threshold_days'),
                "logging_enabled": self.enable_logging
            }
        }
        
        # Check database
        db_path = self.config.get_database_path()
        if Path(db_path).exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get database size
                status["database_status"]["path"] = db_path
                status["database_status"]["exists"] = True
                status["database_status"]["size_mb"] = Path(db_path).stat().st_size / (1024 * 1024)
                
                # Get table count
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                status["database_status"]["table_count"] = table_count
                
                conn.close()
                status["database_status"]["accessible"] = True
            except Exception as e:
                status["database_status"]["accessible"] = False
                status["database_status"]["error"] = str(e)
        else:
            status["database_status"]["exists"] = False
        
        # Check package availability
        for package_name in ['api_sync', 'json2db_sync', 'csv_db_rebuild']:
            package_config = self.config.get_package_config(package_name)
            package_status = {
                "enabled": self.config.is_package_enabled(package_name),
                "path_exists": False,
                "runner_available": False
            }
            
            if package_config:
                package_path = Path(package_config['path'])
                package_status["path_exists"] = package_path.exists()
                
                if package_status["path_exists"]:
                    runner_file = package_path / f"{package_config['runner_module']}.py"
                    package_status["runner_available"] = runner_file.exists()
            
            status["package_status"][package_name] = package_status
        
        return status
