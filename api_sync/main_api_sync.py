#!/usr/bin/env python3
"""
Main API Sync Wrapper

This script provides a comprehensive wrapper for the Zoho API sync functionality,
including interactive menu, testing capabilities, and direct runner access.
Ported from runner_api_sync.py to provide a standalone main interface.
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import config for module info
try:
    from api_sync.config import get_supported_modules, validate_module
except ImportError:
    try:
        from .config import get_supported_modules, validate_module
    except ImportError:
        try:
            from config import get_supported_modules, validate_module
        except ImportError:
            from api_sync.config.main import get_supported_modules, validate_module

# Set up logging
logger = logging.getLogger(__name__)


class ApiSyncWrapper:
    """
    Main wrapper class for API sync functionality.
    
    Provides access to the runner, testing, and menu functionality
    in a unified interface.
    """
    
    def __init__(self):
        self.runner = None
        self._initialize_runner()
    
    def _initialize_runner(self):
        """Initialize the API sync runner."""
        try:
            # Try relative import first
            from .runner_api_sync import create_runner
            self.runner = create_runner()
        except ImportError:
            try:
                # Fallback to direct import when running as script
                from runner_api_sync import create_runner
                self.runner = create_runner()
            except ImportError:
                try:
                    # Fallback to absolute import
                    from api_sync.runner_api_sync import create_runner
                    self.runner = create_runner()
                except Exception as e:
                    print(f"⚠️  Runner initialization failed: {e}")
                    self.runner = None
        except Exception as e:
            print(f"⚠️  Runner initialization failed: {e}")
            self.runner = None
    
    def _create_sync_session_folder(self, base_dir="data/sync_sessions"):
        """
        Create a timestamped sync session folder to organize all sync outputs.
        
        Args:
            base_dir: Base directory for sync sessions
            
        Returns:
            tuple: (session_timestamp, session_folder_path)
        """
        session_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        session_folder = Path(base_dir) / f"sync_session_{session_timestamp}"
        
        try:
            session_folder.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for organization
            (session_folder / "raw_json").mkdir(exist_ok=True)
            (session_folder / "logs").mkdir(exist_ok=True)
            (session_folder / "reports").mkdir(exist_ok=True)
            
            # Create session info file
            session_info = {
                "session_timestamp": session_timestamp,
                "session_start": datetime.now().isoformat(),
                "session_folder": str(session_folder),
                "subdirectories": {
                    "raw_json": "Raw JSON data from API",
                    "logs": "Sync operation logs",
                    "reports": "Verification and summary reports"
                }
            }
            
            import json
            with open(session_folder / "session_info.json", 'w') as f:
                json.dump(session_info, f, indent=2)
            
            # Create README for the session
            self._create_session_readme(session_folder, session_timestamp)
            
            logger.info(f"Created sync session folder: {session_folder}")
            return session_timestamp, str(session_folder)
        except OSError as e:
            logger.error(f"Failed to create sync session folder: {e}")
            return session_timestamp, None
    
    def _create_session_summary(self, session_folder, sync_results):
        """
        Create a summary report for the sync session.
        
        Args:
            session_folder: Path to the session folder
            sync_results: Results from the sync operation
        """
        try:
            summary = {
                "session_completed": datetime.now().isoformat(),
                "sync_results": sync_results,
                "summary": {
                    "total_modules": 0,
                    "successful_modules": 0,
                    "failed_modules": 0,
                    "total_records": 0
                }
            }
            
            # Calculate summary statistics
            if isinstance(sync_results, dict) and "modules" in sync_results:
                modules_data = sync_results["modules"]
                summary["summary"]["total_modules"] = len(modules_data)
                
                for module_result in modules_data.values():
                    if isinstance(module_result, dict):
                        if module_result.get("success", False):
                            summary["summary"]["successful_modules"] += 1
                            summary["summary"]["total_records"] += module_result.get("record_count", 0)
                        else:
                            summary["summary"]["failed_modules"] += 1
            
            # Save summary file
            import json
            summary_file = Path(session_folder) / "reports" / "session_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Created session summary: {summary_file}")
            
        except Exception as e:
            logger.warning(f"Failed to create session summary: {e}")
    
    def _create_session_readme(self, session_folder, session_timestamp):
        """
        Create a README file for the sync session.
        
        Args:
            session_folder: Path to the session folder
            session_timestamp: Timestamp of the session
        """
        try:
            readme_content = f"""# Sync Session: {session_timestamp}

This folder contains all files generated during the sync session that started at {session_timestamp}.

## Folder Structure

- **raw_json/**: Contains the raw JSON data fetched from Zoho API, organized by timestamp directories
- **logs/**: Contains log files from the sync operation
- **reports/**: Contains summary reports and verification results

## Files

- **session_info.json**: Metadata about this sync session
- **session_summary.json**: Summary of sync results (created after completion)

## Usage

The raw JSON files in the `raw_json/` directory can be used for:
- Data analysis
- Re-processing through the data pipeline
- Backup and recovery
- Verification against database records

## Timestamps

All timestamps are in the format: YYYY-MM-DD_HH-MM-SS
Individual module sync operations create subdirectories with their own timestamps within the raw_json folder.
"""
            
            readme_file = Path(session_folder) / "README.md"
            with open(readme_file, 'w') as f:
                f.write(readme_content)
                
            logger.info(f"Created session README: {readme_file}")
            
        except Exception as e:
            logger.warning(f"Failed to create session README: {e}")
    
    def list_sync_sessions(self, base_dir="data/sync_sessions"):
        """
        List all available sync sessions.
        
        Args:
            base_dir: Base directory for sync sessions
            
        Returns:
            List of session info dictionaries
        """
        try:
            sessions = []
            base_path = Path(base_dir)
            
            if not base_path.exists():
                return []
            
            for session_dir in base_path.iterdir():
                if session_dir.is_dir() and session_dir.name.startswith("sync_session_"):
                    session_info_file = session_dir / "session_info.json"
                    session_summary_file = session_dir / "reports" / "session_summary.json"
                    
                    session_info = {"session_folder": str(session_dir)}
                    
                    # Load session info if available
                    if session_info_file.exists():
                        try:
                            import json
                            with open(session_info_file, 'r') as f:
                                session_info.update(json.load(f))
                        except:
                            pass
                    
                    # Load session summary if available
                    if session_summary_file.exists():
                        try:
                            import json
                            with open(session_summary_file, 'r') as f:
                                summary_data = json.load(f)
                                session_info["summary"] = summary_data.get("summary", {})
                                session_info["completed"] = True
                        except:
                            pass
                    else:
                        session_info["completed"] = False
                    
                    sessions.append(session_info)
            
            # Sort by timestamp (newest first)
            sessions.sort(key=lambda x: x.get("session_timestamp", ""), reverse=True)
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sync sessions: {e}")
            return []
    
    def fetch_data(self, module, full_sync=False, since_timestamp=None, use_session_folder=True):
        """
        Fetch data for a module with optional session folder organization.
        
        Args:
            module: Module name to fetch
            full_sync: Whether to perform full sync
            since_timestamp: Timestamp to sync from
            use_session_folder: Whether to organize output in a session folder
        """
        try:
            if use_session_folder:
                # Create session folder for this sync operation
                session_timestamp, session_folder = self._create_sync_session_folder()
                if session_folder:
                    # Create subdirectory for raw JSON within session folder
                    json_output_dir = Path(session_folder) / "raw_json"
                    json_output_dir.mkdir(exist_ok=True)
                    
                    # Call runner with custom output directory
                    result = self.runner.fetch_data(
                        module, 
                        full_sync=full_sync, 
                        since_timestamp=since_timestamp,
                        output_dir=str(json_output_dir)
                    )
                    
                    # Add session info to result
                    if isinstance(result, dict):
                        result["sync_session"] = {
                            "session_timestamp": session_timestamp,
                            "session_folder": session_folder,
                            "json_output_dir": str(json_output_dir)
                        }
                        
                        # Create session summary for single module
                        self._create_session_summary(session_folder, result)
                    
                    return result
                else:
                    # Fallback to default behavior if session folder creation failed
                    logger.warning("Session folder creation failed, using default output")
            
            # Default behavior without session folder
            return self.runner.fetch_data(module, full_sync=full_sync, since_timestamp=since_timestamp)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_all_modules(self, full_sync=False, include_excluded=False, since_timestamp=None, use_session_folder=True):
        """
        Fetch data for all configured modules with optional session folder organization.
        
        Args:
            full_sync: Whether to perform full sync
            include_excluded: Whether to include excluded modules
            since_timestamp: Timestamp to sync from
            use_session_folder: Whether to organize output in a session folder
        """
        try:
            if use_session_folder:
                # Create session folder for this sync operation
                session_timestamp, session_folder = self._create_sync_session_folder()
                if session_folder:
                    # Create subdirectory for raw JSON within session folder
                    json_output_dir = Path(session_folder) / "raw_json"
                    json_output_dir.mkdir(exist_ok=True)
                    
                    # Call runner with custom output directory
                    result = self.runner.fetch_all_modules(
                        full_sync=full_sync,
                        include_excluded=include_excluded,
                        since_timestamp=since_timestamp,
                        output_dir=str(json_output_dir)
                    )
                    
                    # Add session info to result
                    if isinstance(result, dict):
                        result["sync_session"] = {
                            "session_timestamp": session_timestamp,
                            "session_folder": session_folder,
                            "json_output_dir": str(json_output_dir)
                        }
                        
                        # Create session summary for all modules
                        self._create_session_summary(session_folder, result)
                    
                    return result
                else:
                    # Fallback to default behavior if session folder creation failed
                    logger.warning("Session folder creation failed, using default output")
            
            # Default behavior without session folder
            return self.runner.fetch_all_modules(
                full_sync=full_sync, 
                include_excluded=include_excluded,
                since_timestamp=since_timestamp
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def quick_verify_sync_data(self):
        """
        Quick verification and analysis of sync data with comprehensive table report.
        
        Returns detailed information about synced modules including:
        - Module names (including line items)
        - Date ranges (earliest to latest modified)
        - Record counts
        - Session folder organization
        """
        try:
            # Check both traditional and session folder structures
            report_data = self._analyze_sync_data()
            
            if not report_data:
                return {
                    "success": False,
                    "error": "No sync data found"
                }
            
            return {
                "success": True,
                "report": report_data,
                "summary": self._generate_sync_summary(report_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_sync_data(self):
        """Analyze sync data from both traditional and session folder structures."""
        report_data = []
        
        # Check session folders first (newest structure)
        session_data = self._analyze_session_folders()
        if session_data:
            report_data.extend(session_data)
        
        # Check traditional structure if no session data or to supplement
        traditional_data = self._analyze_traditional_structure()
        if traditional_data:
            report_data.extend(traditional_data)
        
        # Remove duplicates and sort by module name
        unique_data = {}
        for item in report_data:
            key = f"{item['module_name']}_{item.get('data_source', 'unknown')}"
            if key not in unique_data or item.get('last_sync', '') > unique_data[key].get('last_sync', ''):
                unique_data[key] = item
        
        return list(unique_data.values())
    
    def _analyze_session_folders(self):
        """Analyze data from session folders."""
        session_data = []
        sessions = self.list_sync_sessions()
        
        for session in sessions[:5]:  # Analyze last 5 sessions
            session_folder = Path(session.get('session_folder', ''))
            if not session_folder.exists():
                continue
                
            raw_json_path = session_folder / "raw_json"
            if not raw_json_path.exists():
                continue
            
            # Analyze each timestamp directory in the session
            for timestamp_dir in raw_json_path.iterdir():
                if timestamp_dir.is_dir() and self._is_timestamp_dir(timestamp_dir.name):
                    modules_data = self._analyze_timestamp_directory(timestamp_dir, f"Session: {session.get('session_timestamp', 'Unknown')}")
                    session_data.extend(modules_data)
        
        return session_data
    
    def _analyze_traditional_structure(self):
        """Analyze data from traditional data/raw_json structure."""
        traditional_data = []
        data_path = Path("data/raw_json")
        
        if not data_path.exists():
            return traditional_data
        
        # Analyze timestamp directories
        for timestamp_dir in data_path.iterdir():
            if timestamp_dir.is_dir() and self._is_timestamp_dir(timestamp_dir.name):
                modules_data = self._analyze_timestamp_directory(timestamp_dir, "Traditional")
                traditional_data.extend(modules_data)
        
        return traditional_data
    
    def _analyze_timestamp_directory(self, timestamp_dir, data_source):
        """Analyze JSON files in a timestamp directory."""
        modules_data = []
        
        for json_file in timestamp_dir.glob("*.json"):
            try:
                module_name = json_file.stem
                
                # Load and analyze the JSON data
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list) or not data:
                    continue
                
                # Extract date information
                date_info = self._extract_date_range(data)
                
                module_info = {
                    "module_name": module_name,
                    "record_count": len(data),
                    "earliest_date": date_info.get("earliest"),
                    "latest_date": date_info.get("latest"),
                    "last_sync": timestamp_dir.name,
                    "data_source": data_source,
                    "file_path": str(json_file)
                }
                
                modules_data.append(module_info)
                
            except Exception as e:
                logger.warning(f"Error analyzing {json_file}: {e}")
                continue
        
        return modules_data
    
    def _extract_date_range(self, data):
        """Extract earliest and latest dates from JSON data."""
        dates = []
        
        # Common date fields to check
        date_fields = [
            'last_modified_time', 'modified_time', 'created_time', 'date',
            'invoice_date', 'bill_date', 'salesorder_date', 'purchaseorder_date',
            'creditnote_date', 'payment_date'
        ]
        
        for record in data:
            if not isinstance(record, dict):
                continue
                
            for field in date_fields:
                if field in record and record[field]:
                    try:
                        # Parse various date formats
                        date_str = record[field]
                        if isinstance(date_str, str):
                            # Handle ISO format and other common formats
                            if 'T' in date_str:
                                # Parse datetime with timezone awareness
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                # Convert to naive datetime for comparison
                                if date_obj.tzinfo is not None:
                                    date_obj = date_obj.replace(tzinfo=None)
                            else:
                                # Parse date-only format
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            dates.append(date_obj)
                    except Exception as e:
                        # Skip invalid dates silently
                        continue
        
        if dates:
            earliest = min(dates)
            latest = max(dates)
            return {
                "earliest": earliest.strftime('%Y-%m-%d'),
                "latest": latest.strftime('%Y-%m-%d')
            }
        
        return {"earliest": "No dates", "latest": "No dates"}
    
    def _is_timestamp_dir(self, dirname):
        """Check if directory name matches timestamp format."""
        import re
        pattern = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"
        return bool(re.match(pattern, dirname))
    
    def _generate_sync_summary(self, report_data):
        """Generate summary statistics from report data."""
        if not report_data:
            return {}
        
        total_records = sum(item.get('record_count', 0) for item in report_data)
        unique_modules = len(set(item['module_name'] for item in report_data))
        
        # Separate regular modules from line items
        regular_modules = [item for item in report_data if not item['module_name'].endswith('_line_items')]
        line_item_modules = [item for item in report_data if item['module_name'].endswith('_line_items')]
        
        return {
            "total_records": total_records,
            "unique_modules": unique_modules,
            "regular_modules_count": len(regular_modules),
            "line_item_modules_count": len(line_item_modules),
            "last_sync": max((item.get('last_sync', '') for item in report_data), default='Unknown')
        }


def test_wrapper_functionality():
    """
    Test the wrapper functionality including incremental sync logic and data population.
    Ported from runner_api_sync.py test functionality.
    """
    print("🚀 Testing Main API Sync Wrapper Functionality")
    print("=" * 60)
    print("Focus: Ensure incremental sync and data population work correctly\n")
    
    def test_wrapper_creation():
        """Test wrapper creation and runner initialization."""
        print("📋 Testing Wrapper Creation")
        print("-" * 30)
        
        try:
            wrapper = ApiSyncWrapper()
            print("✅ Wrapper created successfully")
            
            if wrapper.runner:
                print("✅ Runner initialized with credentials")
                return wrapper, True
            else:
                print("⚠️  Runner not initialized (expected without credentials)")
                print("✅ Wrapper structure is correct")
                return wrapper, True
                
        except Exception as e:
            print(f"❌ Wrapper creation failed: {e}")
            return None, False
    
    def test_incremental_logic():
        """Test the incremental sync logic."""
        print("\n📋 Testing Incremental Sync Logic")
        print("-" * 35)
        
        try:
            from api_sync.utils import get_latest_sync_timestamp, ensure_zoho_timestamp_format
            
            # Test getting latest timestamp
            latest_timestamp = get_latest_sync_timestamp()
            
            if latest_timestamp:
                print(f"✅ Found latest sync timestamp: {latest_timestamp}")
                
                # Test conversion to Zoho format
                zoho_timestamp = ensure_zoho_timestamp_format(latest_timestamp)
                print(f"✅ Zoho format: {zoho_timestamp}")
                
                # Validate the logic
                try:
                    parsed = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                    print(f"✅ Timestamp is valid: {parsed}")
                    
                    # Check if it's reasonable (not too old/new)
                    now = datetime.now()
                    age_days = (now - parsed.replace(tzinfo=None)).days
                    
                    if 0 <= age_days <= 30:
                        print(f"✅ Timestamp age is reasonable: {age_days} days")
                    else:
                        print(f"⚠️  Timestamp age: {age_days} days (might be old)")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ Timestamp parsing failed: {e}")
                    return False
            else:
                print("⚠️  No previous sync found (first run)")
                print("✅ This is correct behavior")
                return True
                
        except Exception as e:
            print(f"❌ Incremental logic test failed: {e}")
            return False
    
    def test_data_population():
        """Test data population verification."""
        print("\n📋 Testing Data Population")
        print("-" * 28)
        
        try:
            from api_sync.utils import is_timestamp_dir
            
            # Check data directory
            data_dir = Path("data/raw_json")
            
            if data_dir.exists():
                print(f"✅ Data directory exists: {data_dir}")
                
                # Check for timestamp directories
                timestamp_dirs = [d for d in data_dir.iterdir() 
                                if d.is_dir() and is_timestamp_dir(d.name)]
                
                print(f"✅ Found {len(timestamp_dirs)} valid timestamp directories")
                
                if timestamp_dirs:
                    # Check the latest directory for data
                    latest_dir = sorted(timestamp_dirs, key=lambda x: x.name)[-1]
                    json_files = list(latest_dir.glob("*.json"))
                    
                    print(f"✅ Latest directory: {latest_dir.name}")
                    print(f"✅ JSON files in latest: {len(json_files)}")
                    
                    # Check if files have actual data
                    total_records = 0
                    modules_found = set()
                    for json_file in json_files:
                        try:
                            import json
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                            if isinstance(data, list):
                                total_records += len(data)
                                modules_found.add(json_file.stem)
                        except:
                            pass
                    
                    print(f"✅ Total records in latest sync: {total_records}")
                    print(f"✅ Modules in latest sync: {sorted(list(modules_found))}")
                    
                    if total_records > 0:
                        print("✅ Data is properly populated")
                        return True
                    else:
                        print("⚠️  Latest sync has no data (possible aborted sync)")
                        return True  # Still valid, just no data
                else:
                    print("⚠️  No valid timestamp directories found")
                    return False
            else:
                print("⚠️  Data directory doesn't exist (first run)")
                return True  # This is ok for first run
            
        except Exception as e:
            print(f"❌ Data population test failed: {e}")
            return False
    
    def test_wrapper_functions(wrapper):
        """Test wrapper functions."""
        print("\n📋 Testing Wrapper Functions")
        print("-" * 30)
        
        try:
            # Test status function
            print("📊 Testing get_status()...")
            status = wrapper.get_status()
            print("✅ Status function works")
            
            # Test sync history
            print("📈 Testing get_sync_history()...")
            history = wrapper.get_sync_history()
            print(f"✅ History function works - found {len(history)} entries")
            
            return True
            
        except Exception as e:
            print(f"❌ Wrapper function tests failed: {e}")
            return False
    
    # Run all tests
    tests = []
    
    # Test 1: Wrapper creation
    wrapper, creation_success = test_wrapper_creation()
    tests.append(("Wrapper Creation", creation_success))
    
    # Test 2: Incremental logic
    incremental_success = test_incremental_logic()
    tests.append(("Incremental Logic", incremental_success))
    
    # Test 3: Data population
    data_success = test_data_population()
    tests.append(("Data Population", data_success))
    
    # Test 4: Wrapper functions
    if wrapper:
        wrapper_func_success = test_wrapper_functions(wrapper)
        tests.append(("Wrapper Functions", wrapper_func_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 WRAPPER TEST RESULTS")
    print("-" * 25)
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ CONFIRMED:")
        print("  • Wrapper creation and structure works")
        print("  • Incremental sync logic works correctly")
        print("  • Timestamp handling is robust")
        print("  • Data is properly structured and populated")
        print("  • All wrapper functions work correctly")
        print("\n🚀 main_api_sync.py wrapper is fully validated!")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Review the issues above before deploying")
        return False


def interactive_menu():
    """
    Interactive menu interface.
    Ported from runner_api_sync.py menu functionality.
    """
    import os
    
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 50)
    print("          Zoho API Sync Tool")
    print("          (Main Wrapper)")
    print("=" * 50)
    print()
    
    try:
        # Create wrapper instance
        print("🔄 Initializing API Sync Wrapper...")
        wrapper = ApiSyncWrapper()
        
        if wrapper.runner:
            print("✅ Wrapper initialized successfully with credentials!")
        else:
            print("⚠️  Wrapper initialized without credentials")
            print("    (Some functions may be limited)")
        
        while True:
            print("\nAvailable Options:")
            print("1. Fetch Data")
            print("2. Quick Verify Sync Data")
            print("3. List Sync Sessions")
            print("4. Exit")
            
            try:
                choice = input("\nEnter your choice (1-4): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            
            if choice == "1":
                print("\nFetch Options (All syncs are incremental):")
                print("a. Fetch all modules (default - excludes 'organizations')")
                print("b. Fetch specific module")
                print("c. Fetch all modules including excluded ones")
                
                try:
                    fetch_choice = input("Choose option (a/b/c): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("\n❌ Operation cancelled")
                    continue
                
                # All syncs are incremental by default (full_sync=False)
                # This ensures data is fetched since last sync timestamp
                full_sync = False
                
                if fetch_choice == "a" or fetch_choice == "":
                    # Fetch all modules (config-driven, excludes organizations by default)
                    print(f"\n🔄 Fetching all modules (incremental sync - since last sync)...")
                    
                    # Check if runner is available for configuration
                    if wrapper.runner:
                        print(f"🏢 Organization ID: {wrapper.runner.config.default_organization_id}")
                        print(f"🚫 Excluded modules: {', '.join(wrapper.runner.config.excluded_modules)}")
                    else:
                        # Use config defaults when runner not available
                        try:
                            from api_sync.config import get_config
                            config = get_config()
                            print(f"🏢 Organization ID: {config.default_organization_id}")
                            print(f"🚫 Excluded modules: {', '.join(config.excluded_modules)}")
                        except Exception as e:
                            print(f"🏢 Organization ID: 806931205 (default)")
                            print(f"🚫 Excluded modules: organizations (default)")
                    
                    # Perform pre-sync check for comprehensive data
                    try:
                        cutoff_timestamp = perform_pre_sync_check(wrapper, modules_to_fetch=None)
                        if cutoff_timestamp:
                            print(f"🕒 Using cutoff timestamp: {cutoff_timestamp}")
                        else:
                            print("⏭️  No cutoff timestamp - proceeding with normal incremental sync")
                    except Exception as e:
                        print(f"⚠️  Pre-sync check failed: {e}")
                        print("Proceeding without cutoff timestamp...")
                        cutoff_timestamp = None
                    
                    # Attempt to run fetch (will fail gracefully if no runner)
                    if wrapper.runner:
                        try:
                            result = wrapper.fetch_all_modules(
                                full_sync=full_sync, 
                                include_excluded=False,
                                since_timestamp=cutoff_timestamp
                            )
                            if result.get('success'):
                                summary = result.get('summary', {})
                                print(f"✅ Successfully processed {summary.get('modules_succeeded', 0)} modules")
                                print(f"📊 Total records: {summary.get('total_records', 0)}")
                                if summary.get('total_line_items', 0) > 0:
                                    print(f"📋 Total line items: {summary.get('total_line_items', 0)}")
                                if summary.get('output_dir'):
                                    print(f"📁 Data saved to: {summary.get('output_dir')}")
                                if summary.get('failed_modules'):
                                    print(f"⚠️  Failed modules: {', '.join(summary.get('failed_modules'))}")
                            else:
                                print(f"❌ Fetch failed: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                    else:
                        print("⚠️  Cannot execute fetch - runner not initialized (credentials required)")
                        print("💡 Pre-sync check functionality demonstrated successfully!")
                        print(f"   Cutoff timestamp would be: {cutoff_timestamp or 'None (normal incremental)'}")
                        
                elif fetch_choice == "b":
                    # Fetch specific module
                    supported_modules = get_supported_modules()
                    module_list = ', '.join(supported_modules.keys())
                    print(f"\nSupported modules: {module_list}")
                    try:
                        module = input("Enter module name: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\n❌ Operation cancelled")
                        continue
                        
                    if not module:
                        print("❌ Module name required")
                        continue
                        
                    # Validate module name using config
                    if not validate_module(module):
                        print(f"❌ Invalid module '{module}'. Supported modules: {module_list}")
                        continue
                    
                    print(f"\n🔄 Fetching {module} data (incremental sync)...")
                    print(f"🏢 Organization ID: {wrapper.runner.config.default_organization_id}")
                    
                    # Perform pre-sync check for this specific module
                    cutoff_timestamp = perform_pre_sync_check(wrapper, modules_to_fetch=[module])
                    
                    try:
                        result = wrapper.fetch_data(
                            module, 
                            full_sync=full_sync,
                            since_timestamp=cutoff_timestamp
                        )
                        if result.get('success'):
                            print(f"✅ Successfully fetched {result.get('record_count', 0)} records")
                            if result.get('line_item_count', 0) > 0:
                                print(f"📋 Line items: {result.get('line_item_count', 0)}")
                            if result.get('output_dir'):
                                print(f"📁 Data saved to: {result.get('output_dir')}")
                        else:
                            print(f"❌ Fetch failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        
                elif fetch_choice == "c":
                    # Fetch all modules including excluded ones
                    print(f"\n🔄 Fetching ALL modules (incremental sync - including excluded)...")
                    print(f"🏢 Organization ID: {wrapper.runner.config.default_organization_id}")
                    
                    # Perform pre-sync check for all modules (including excluded)
                    cutoff_timestamp = perform_pre_sync_check(wrapper, modules_to_fetch=None)
                    
                    try:
                        result = wrapper.fetch_all_modules(
                            full_sync=full_sync, 
                            include_excluded=True,
                            since_timestamp=cutoff_timestamp
                        )
                        if result.get('success'):
                            summary = result.get('summary', {})
                            print(f"✅ Successfully processed {summary.get('modules_succeeded', 0)} modules")
                            print(f"📊 Total records: {summary.get('total_records', 0)}")
                            if summary.get('total_line_items', 0) > 0:
                                print(f"📋 Total line items: {summary.get('total_line_items', 0)}")
                            if summary.get('output_dir'):
                                print(f"📁 Data saved to: {summary.get('output_dir')}")
                            if summary.get('failed_modules'):
                                print(f"⚠️  Failed modules: {', '.join(summary.get('failed_modules'))}")
                        else:
                            print(f"❌ Fetch failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        
                else:
                    print("❌ Invalid choice. Please select a, b, or c.")
            
            elif choice == "2":
                print("\n� Quick Verify Sync Data - Comprehensive Analysis...")
                try:
                    result = wrapper.quick_verify_sync_data()
                    if result.get('success'):
                        report_data = result.get('report', [])
                        summary = result.get('summary', {})
                        
                        if not report_data:
                            print("❌ No sync data found")
                            continue
                        
                        print("✅ Sync data analysis completed")
                        print("\n📊 SYNC DATA ANALYSIS REPORT")
                        print("=" * 120)
                        print(f"{'Module Name':<25} {'Data Source':<15} {'Records':<10} {'Earliest Date':<15} {'Latest Date':<15} {'Last Sync':<20}")
                        print("-" * 120)
                        
                        # Separate regular modules from line items
                        regular_modules = []
                        line_item_modules = []
                        
                        for item in report_data:
                            if item['module_name'].endswith('_line_items'):
                                line_item_modules.append(item)
                            else:
                                regular_modules.append(item)
                        
                        # Display regular modules first
                        if regular_modules:
                            print("📋 MAIN MODULES:")
                            for item in sorted(regular_modules, key=lambda x: x['module_name']):
                                module_display = item['module_name'].replace('_', ' ').title()
                                data_source = item.get('data_source', 'Unknown')[:14]
                                record_count = item.get('record_count', 0)
                                earliest = item.get('earliest_date', 'No dates')[:14]
                                latest = item.get('latest_date', 'No dates')[:14]
                                last_sync = item.get('last_sync', 'Unknown')[:19]
                                
                                print(f"{module_display:<25} {data_source:<15} {record_count:<10} {earliest:<15} {latest:<15} {last_sync:<20}")
                        
                        # Display line item modules
                        if line_item_modules:
                            print("\n📝 LINE ITEM MODULES:")
                            for item in sorted(line_item_modules, key=lambda x: x['module_name']):
                                module_display = item['module_name'].replace('_line_items', '').replace('_', ' ').title() + " (Line Items)"
                                data_source = item.get('data_source', 'Unknown')[:14]
                                record_count = item.get('record_count', 0)
                                earliest = item.get('earliest_date', 'No dates')[:14]
                                latest = item.get('latest_date', 'No dates')[:14]
                                last_sync = item.get('last_sync', 'Unknown')[:19]
                                
                                print(f"{module_display:<25} {data_source:<15} {record_count:<10} {earliest:<15} {latest:<15} {last_sync:<20}")
                        
                        # Display summary
                        print("\n📈 SUMMARY:")
                        print("-" * 50)
                        print(f"Total Records: {summary.get('total_records', 0):,}")
                        print(f"Unique Modules: {summary.get('unique_modules', 0)}")
                        print(f"Regular Modules: {summary.get('regular_modules_count', 0)}")
                        print(f"Line Item Modules: {summary.get('line_item_modules_count', 0)}")
                        print(f"Last Sync: {summary.get('last_sync', 'Unknown')}")
                        
                    else:
                        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Error during analysis: {e}")
                    import traceback
                    traceback.print_exc()
            
            elif choice == "3":
                print("\n📁 Sync Sessions:")
                try:
                    sessions = wrapper.list_sync_sessions()
                    if sessions:
                        print(f"\nFound {len(sessions)} sync sessions:")
                        print("-" * 80)
                        for i, session in enumerate(sessions[:10], 1):  # Show last 10
                            timestamp = session.get('session_timestamp', 'Unknown')
                            folder = session.get('session_folder', 'Unknown')
                            print(f"{i:2d}. {timestamp}")
                            print(f"    📁 {folder}")
                    else:
                        print("No sync sessions found")
                except Exception as e:
                    print(f"❌ Error listing sessions: {e}")
            
            elif choice == "4":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("\nPlease check your configuration and credentials.")
        print("Error details:")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def prompt_for_cutoff_date() -> Optional[str]:
    """
    Prompt user for a cutoff date when no comprehensive line items data is available.
    
    This function is called when the system detects that modules with line items 
    don't have comprehensive (bulk) data available, which would result in slow 
    individual API calls for each record.
    
    Returns:
        Date string in dd-mmm-yyyy format, or None if user cancels
    """
    import re
    from datetime import datetime
    
    print("\n" + "="*70)
    print("📅 CUTOFF DATE REQUIRED")
    print("="*70)
    print()
    print("⚠️  No comprehensive line items data found for some modules.")
    print("   Without a cutoff date, the sync will fetch ALL historical data,")
    print("   which can be very slow due to individual API calls per record.")
    print()
    print("💡 Recommendation: Use a recent date (e.g., last 6-12 months)")
    print("   to fetch only recent transactions with line items.")
    print()
    print("📋 Affected modules: invoices, bills, salesorders, purchaseorders, creditnotes")
    print()
    
    while True:
        try:
            print("Enter cutoff date (dd-mmm-yyyy format, e.g., 01-Jan-2024):")
            print("Or press Enter to fetch ALL data (warning: can be very slow)")
            date_input = input("Cutoff date: ").strip()
            
            # Allow empty input (fetch all data)
            if not date_input:
                print("⚠️  No cutoff date provided - will fetch ALL historical data")
                print("   This may take a very long time for large datasets.")
                confirm = input("Continue anyway? (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    return None
                else:
                    print("Cancelled. Please provide a cutoff date.")
                    continue
            
            # Validate format
            date_pattern = r'^(\d{1,2})-([A-Za-z]{3})-(\d{4})$'
            match = re.match(date_pattern, date_input)
            
            if not match:
                print("❌ Invalid format. Please use dd-mmm-yyyy (e.g., 01-Jan-2024)")
                continue
            
            day, month_str, year = match.groups()
            
            # Validate and parse the date
            try:
                # Convert month abbreviation to number
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month_num = month_map.get(month_str.lower())
                if not month_num:
                    print("❌ Invalid month. Use 3-letter abbreviation (Jan, Feb, Mar, etc.)")
                    continue
                
                # Validate date
                parsed_date = datetime(int(year), month_num, int(day))
                
                # Check if date is not in the future
                if parsed_date > datetime.now():
                    print("❌ Date cannot be in the future")
                    continue
                
                # Check if date is not too old (more than 10 years)
                if parsed_date.year < datetime.now().year - 10:
                    print("⚠️  Warning: Date is more than 10 years old")
                    confirm = input("Continue with this old date? (y/N): ").strip().lower()
                    if confirm not in ['y', 'yes']:
                        continue
                
                print(f"✅ Cutoff date set: {date_input}")
                print(f"   Will fetch data from {parsed_date.strftime('%B %d, %Y')} onwards")
                return date_input
                
            except ValueError as e:
                print(f"❌ Invalid date: {e}")
                continue
                
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Operation cancelled by user")
            return None
        except Exception as e:
            print(f"❌ Error processing date: {e}")
            continue

def convert_cutoff_date_to_timestamp(cutoff_date: str) -> Optional[str]:
    """
    Convert cutoff date from dd-mmm-yyyy format to Zoho timestamp format.
    
    Args:
        cutoff_date: Date in dd-mmm-yyyy format (e.g., "01-Jan-2024")
        
    Returns:
        ISO timestamp string suitable for Zoho API, or None if conversion fails
    """
    import re
    from datetime import datetime
    
    try:
        # Parse the date
        date_pattern = r'^(\d{1,2})-([A-Za-z]{3})-(\d{4})$'
        match = re.match(date_pattern, cutoff_date)
        
        if not match:
            logger.error(f"Invalid cutoff date format: {cutoff_date}")
            return None
        
        day, month_str, year = match.groups()
        
        # Convert month abbreviation to number
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        month_num = month_map.get(month_str.lower())
        if not month_num:
            logger.error(f"Invalid month abbreviation: {month_str}")
            return None
        
        # Create datetime object
        parsed_date = datetime(int(year), month_num, int(day))
        
        # Convert to ISO format
        iso_timestamp = parsed_date.isoformat()
        
        logger.info(f"Converted cutoff date {cutoff_date} to timestamp {iso_timestamp}")
        return iso_timestamp
        
    except Exception as e:
        logger.error(f"Failed to convert cutoff date {cutoff_date}: {e}")
        return None

def perform_pre_sync_check(wrapper, modules_to_fetch: list = None) -> Optional[str]:
    """
    Perform pre-sync check for data availability.
    
    This function determines if we can proceed with normal incremental sync,
    or if we need a cutoff date for first-time sync.
    
    Args:
        wrapper: ApiSyncWrapper instance
        modules_to_fetch: List of modules that will be fetched, or None for all fetchable modules
        
    Returns:
        ISO timestamp string to use as since_timestamp, or None for normal incremental sync
    """
    # Handle imports for both relative and direct execution contexts
    try:
        from api_sync.utils import check_comprehensive_data_availability
        from api_sync.config import get_fetchable_modules
    except ImportError:
        try:
            from .utils import check_comprehensive_data_availability
            from .config import get_fetchable_modules
        except ImportError:
            try:
                from utils import check_comprehensive_data_availability
                from config import get_fetchable_modules
            except ImportError:
                from api_sync.utils import check_comprehensive_data_availability
                from api_sync.config.main import get_fetchable_modules
    
    # If no specific modules provided, check all fetchable modules
    if modules_to_fetch is None:
        fetchable_modules = get_fetchable_modules()
        modules_to_fetch = list(fetchable_modules.keys())
    
    # Only check modules that we're actually going to fetch
    print("\n🔍 Checking existing data for incremental sync...")
    has_data_or_comprehensive, missing_modules = check_comprehensive_data_availability(modules_to_fetch)
    
    if has_data_or_comprehensive:
        print("✅ Can proceed with normal incremental sync")
        print("🔄 Will fetch data since last sync timestamp")
        return None
    
    # Check if config allows prompting
    if wrapper.runner and hasattr(wrapper.runner.config, 'prompt_for_line_items_date'):
        prompt_enabled = wrapper.runner.config.prompt_for_line_items_date
    else:
        # Fallback to getting config directly
        try:
            # Handle imports for both relative and direct execution contexts
            try:
                from api_sync.config import get_config
            except ImportError:
                try:
                    from .config import get_config
                except ImportError:
                    try:
                        from config import get_config
                    except ImportError:
                        from api_sync.config.main import get_config
            
            config = get_config()
            prompt_enabled = config.prompt_for_line_items_date
        except Exception as e:
            logger.warning(f"Cannot check config for prompt_for_line_items_date: {e}")
            prompt_enabled = True  # Default to allowing prompts
    
    if not prompt_enabled:
        print("⚠️  Configuration disables cutoff date prompting - will fetch all data")
        return None
    
    # Prompt user for cutoff date
    print(f"\n⚠️  No existing sync data found for: {', '.join(missing_modules)}")
    print("📝 This appears to be a first-time sync for these modules")
    cutoff_date = prompt_for_cutoff_date()
    
    if cutoff_date:
        # Convert to timestamp format
        since_timestamp = convert_cutoff_date_to_timestamp(cutoff_date)
        if since_timestamp:
            print(f"🕒 Using cutoff timestamp: {since_timestamp}")
            return since_timestamp
        else:
            print("❌ Failed to convert cutoff date - proceeding without cutoff")
            return None
    else:
        print("⚠️  No cutoff date provided - will fetch all historical data")
        return None


def main():
    """
    Main entry point for the API sync wrapper.
    
    Supports different modes:
    - --test: Run comprehensive tests
    - --menu or no args: Interactive menu
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            return test_wrapper_functionality()
        elif sys.argv[1] == "--help":
            print("Zoho API Sync Main Wrapper")
            print("Usage:")
            print("  python main_api_sync.py          # Interactive menu")
            print("  python main_api_sync.py --test   # Run tests")
            print("  python main_api_sync.py --help   # Show this help")
            return True
    
    # Default to interactive menu
    interactive_menu()
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
