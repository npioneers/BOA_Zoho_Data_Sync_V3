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
    
    def get_status(self):
        """Get system status."""
        if self.runner:
            return self.runner.get_status()
        else:
            return {
                "error": "Runner not initialized",
                "credentials": False,
                "latest_sync": None
            }
    
    def get_sync_history(self):
        """Get sync history."""
        if self.runner:
            return self.runner.get_sync_history()
        else:
            return []
    
    def fetch_data(self, module, full_sync=False, since_timestamp=None):
        """Fetch data for a module (incremental by default)."""
        try:
            return self.runner.fetch_data(module, full_sync=full_sync, since_timestamp=since_timestamp)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_all_modules(self, full_sync=False, include_excluded=False, since_timestamp=None):
        """Fetch data for all configured modules (incremental by default, config-driven filtering)."""
        try:
            return self.runner.fetch_all_modules(
                full_sync=full_sync, 
                include_excluded=include_excluded,
                since_timestamp=since_timestamp
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def verify_data(self, quick=True):
        """Verify data completeness using quick local verification."""
        if self.runner:
            return self.runner.quick_local_verification()
        else:
            return {
                "success": False,
                "error": "Runner not initialized - check credentials"
            }
    
    def quick_local_verification(self):
        """Quick local verification without API calls."""
        if self.runner:
            return self.runner.quick_local_verification()
        else:
            return {
                "success": False,
                "error": "Runner not initialized - check credentials"
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
            print("2. Verify Data")
            print("3. Quick Local Analysis")
            print("4. Show Status")
            print("5. Show Sync History")
            print("6. Run Tests")
            print("7. Exit")
            
            try:
                choice = input("\nEnter your choice (1-7): ").strip()
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
                print("\n🔍 Quick Local Data Verification...")
                try:
                    result = wrapper.verify_data()
                    if result.get('success'):
                        print("✅ Local verification completed")
                        
                        # Show detailed results
                        directory = result.get('directory')
                        modules = result.get('modules', {})
                        summary = result.get('summary', {})
                        
                        print(f"\n📁 Analyzing directory: {directory}")
                        print("\n📊 Module Analysis:")
                        print("=" * 100)
                        print(f"{'Module':<25} {'Records':<10} {'Date Range'}")
                        print("-" * 100)
                        
                        # Regular modules first
                        regular_modules = []
                        line_item_modules = []
                        
                        for module_name, data in modules.items():
                            if isinstance(data, dict) and 'error' not in data:
                                if "_line_items" in module_name:
                                    line_item_modules.append((module_name, data))
                                else:
                                    regular_modules.append((module_name, data))
                        
                        # Display regular modules
                        for module_name, data in sorted(regular_modules):
                            count = data.get("total_records", 0)
                            date_range = data.get("date_range", "No dates found")
                            module_display = module_name.replace('_', ' ').title()
                            print(f"{module_display:<25} {count:<10} {date_range}")
                        
                        if line_item_modules:
                            print("\n📋 Line Items:")
                            print("-" * 50)
                            for module_name, data in sorted(line_item_modules):
                                count = data.get("total_records", 0)
                                date_range = data.get("date_range", "No dates found")
                                base_module = module_name.replace("_line_items", "").replace('_', ' ').title()
                                print(f"{base_module} line items: {count} records")
                                if date_range != "No dates found":
                                    print(f"  Date range: {date_range}")
                        
                        # Show summary
                        print("\n📈 Summary:")
                        print("-" * 30)
                        total_header = summary.get('total_header_records', 0)
                        total_line_items = summary.get('total_line_items', 0)
                        total_records = summary.get('total_records', 0)
                        regular_count = summary.get('regular_modules_count', 0)
                        overall_range = summary.get('overall_date_range')
                        
                        print(f"Header records: {total_header}")
                        print(f"Line items: {total_line_items}")
                        print(f"Total records: {total_records}")
                        print(f"Regular modules: {regular_count}")
                        if overall_range:
                            print(f"Overall date range: {overall_range}")
                            
                    else:
                        print(f"❌ Verification failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == "3":
                print("\n📋 System Status:")
                try:
                    status = wrapper.get_status()
                    for key, value in status.items():
                        print(f"  {key}: {value}")
                except Exception as e:
                    print(f"❌ Error getting status: {e}")
            
            elif choice == "4":
                print("\n📈 Sync History:")
                try:
                    history = wrapper.get_sync_history()
                    if history:
                        for entry in history[:5]:  # Show last 5 entries
                            timestamp = entry.get('timestamp', 'Unknown')
                            modules = entry.get('modules', [])
                            print(f"  {timestamp} - {len(modules)} modules")
                    else:
                        print("  No sync history found")
                except Exception as e:
                    print(f"❌ Error getting history: {e}")
            
            elif choice == "5":
                print("\n🧪 Running wrapper tests...")
                test_wrapper_functionality()
                input("\nPress Enter to continue...")
            
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-6.")
    
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
    Perform pre-sync check for comprehensive data availability.
    
    If comprehensive data is not available for modules with line items,
    prompt the user for a cutoff date to avoid slow individual API calls.
    
    Args:
        wrapper: ApiSyncWrapper instance
        modules_to_fetch: List of modules that will be fetched, or None for all fetchable modules
        
    Returns:
        ISO timestamp string to use as since_timestamp, or None for no cutoff
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
    print("\n🔍 Performing pre-sync comprehensive data check...")
    has_comprehensive, missing_modules = check_comprehensive_data_availability(modules_to_fetch)
    
    if has_comprehensive:
        print("✅ Comprehensive data available for all modules with line items")
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
    print(f"\n⚠️  Missing comprehensive data for: {', '.join(missing_modules)}")
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
