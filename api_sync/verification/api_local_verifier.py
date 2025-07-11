"""
API vs Local Data Verification Module

Compares data counts between Zoho API and local JSON files to verify completeness.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

from ..core import auth, secrets, client
from ..processing import raw_data_handler

logger = logging.getLogger(__name__)

class ApiLocalVerifier:
    """
    Verifies data completeness by comparing API counts with local JSON data.
    """
    
    def __init__(self, json_base_dir: str = "data/raw_json"):
        """
        Initialize the verifier.
        
        Args:
            json_base_dir: Base directory containing JSON data directories
        """
        self.json_base_dir = json_base_dir
        self.api_client = None
        self.verification_results = {}
        
    def _initialize_api_client(self) -> bool:
        """
        Initialize the Zoho API client.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Initializing Zoho API client...")
            
            # Get credentials
            zoho_credentials = secrets.get_zoho_credentials()
            access_token = auth.get_access_token(zoho_credentials)
            zoho_org_id = zoho_credentials.get('organization_id')
            
            # Initialize client
            self.api_client = client.ZohoClient(
                access_token, 
                zoho_org_id, 
                "https://www.zohoapis.com/books/v3"
            )
            
            logger.info("API client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            return False
    
    def verify_data_completeness(self, timestamp_dir: str = None, modules: List[str] = None) -> Dict[str, Any]:
        """
        Verify data completeness for specified modules and timestamp directory.
        
        Args:
            timestamp_dir: Specific timestamp directory to verify (uses latest if None)
            modules: List of modules to verify (uses all found JSON files if None)
            
        Returns:
            Dictionary containing verification results
        """
        logger.info("Starting data completeness verification...")
        
        # Initialize API client
        if not self._initialize_api_client():
            return {"error": "Failed to initialize API client"}
        
        # Get timestamp directory - only use specific directory if explicitly provided
        search_mode = "all_directories"
        if timestamp_dir:
            search_mode = "specific_directory"
            logger.info(f"Verifying data in specific directory: {timestamp_dir}")
        else:
            logger.info("Searching all directories for latest data for each module")
        
        # Get modules to verify
        if not modules:
            if timestamp_dir:
                # Get modules from specific directory
                modules = self._get_available_modules(timestamp_dir)
                if not modules:
                    return {"error": f"No JSON files found in {timestamp_dir}"}
            else:
                # Use standard module list when searching all directories
                modules = ["contacts", "items", "bills", "invoices", "salesorders", 
                          "purchaseorders", "creditnotes", "customerpayments", 
                          "vendorpayments", "organizations"]
                logger.info(f"Using standard module list: {modules}")
        
        # Perform verification for each module
        results = {
            "timestamp": datetime.now().isoformat(),
            "directory": timestamp_dir if timestamp_dir else "all_directories",
            "modules": {},
            "summary": {
                "total_modules": 0,
                "perfect_matches": 0,
                "discrepancies": 0,
                "api_errors": 0
            }
        }
        
        for module in modules:
            logger.info(f"Verifying module: {module}")
            # Use all-directory search if no specific timestamp_dir provided, or use specific dir
            if timestamp_dir:
                module_result = self._verify_module(module, timestamp_dir)
            else:
                module_result = self._verify_module(module, None)  # Search all directories
            results["modules"][module] = module_result
            
            # Update summary
            results["summary"]["total_modules"] += 1
            if module_result.get("status") == "perfect_match":
                results["summary"]["perfect_matches"] += 1
            elif module_result.get("status") == "discrepancy":
                results["summary"]["discrepancies"] += 1
            elif module_result.get("status") == "api_error":
                results["summary"]["api_errors"] += 1
        
        # Calculate match percentage
        total = results["summary"]["total_modules"]
        matches = results["summary"]["perfect_matches"]
        results["summary"]["match_percentage"] = (matches / total * 100) if total > 0 else 0
        
        logger.info(f"Verification completed: {matches}/{total} perfect matches ({results['summary']['match_percentage']:.1f}%)")
        
        return results
    
    def _get_available_modules(self, timestamp_dir: str) -> List[str]:
        """
        Get list of available modules (JSON files) in the timestamp directory.
        
        Args:
            timestamp_dir: Timestamp directory name
            
        Returns:
            List of module names (without .json extension)
        """
        try:
            dir_path = Path(self.json_base_dir) / timestamp_dir
            json_files = list(dir_path.glob("*.json"))
            modules = [f.stem for f in json_files]
            
            logger.info(f"Found {len(modules)} modules: {modules}")
            return modules
            
        except Exception as e:
            logger.error(f"Failed to get available modules: {e}")
            return []
    
    def _verify_module(self, module: str, timestamp_dir: str = None) -> Dict[str, Any]:
        """
        Verify a specific module against API.
        If timestamp_dir is None, searches all directories for the latest data.
        
        Args:
            module: Module name
            timestamp_dir: Timestamp directory name (searches all if None)
            
        Returns:
            Dictionary containing verification results for the module
        """
        result = {
            "module": module,
            "local_count": 0,
            "api_count": 0,
            "difference": 0,
            "status": "unknown",
            "error": None,
            "source_dir": None,
            "line_item_details": None
        }
        
        try:
            # Get local count - search all directories if timestamp_dir not specified
            if timestamp_dir:
                # Use specific directory
                local_data = raw_data_handler.load_raw_json(module, timestamp_dir, self.json_base_dir)
                result["local_count"] = len(local_data) if local_data else 0
                result["source_dir"] = timestamp_dir
            else:
                # Search all directories for latest data
                latest_dir, latest_count = self._find_latest_module_data(module)
                result["local_count"] = latest_count
                result["source_dir"] = latest_dir
                if latest_dir:
                    logger.info(f"Module {module}: Found latest data in {latest_dir} with {latest_count} records")
                else:
                    logger.info(f"Module {module}: No local data found in any directory")
            
            # REMOVED: API count checking to avoid interference with incremental sync
            # Previously: result["api_count"] = self.api_client.get_module_count(module)
            result["api_count"] = "DISABLED"  # API count checking disabled
            
            # Get line item details for document modules
            if result["source_dir"]:
                result["line_item_details"] = self._get_line_item_counts(module, result["source_dir"])
            
            # Calculate difference - disabled since we removed API count
            result["difference"] = "N/A"  # Difference calculation disabled
            
            # Determine status based on local data only
            if result["local_count"] > 0:
                result["status"] = "local_data_found"
            else:
                result["status"] = "no_local_data"
            
            logger.info(f"Module {module}: Local={result['local_count']} (from {result['source_dir']}), API=DISABLED")
            
            # Log line item details if available
            if result["line_item_details"] and result["line_item_details"]["line_items"] > 0:
                line_details = result["line_item_details"]
                logger.info(f"Module {module}: {line_details['headers']} headers + {line_details['line_items']} line items")
            
        except Exception as e:
            logger.error(f"Error verifying module {module}: {e}")
            result["error"] = str(e)
            result["status"] = "api_error"
        
        return result
    
    def _find_latest_module_data(self, module: str) -> Tuple[str, int]:
        """
        Find the latest data file for a module across all timestamp directories.
        
        Args:
            module: Module name to search for
            
        Returns:
            Tuple of (timestamp_dir, record_count) for the latest data
        """
        base_path = Path(self.json_base_dir)
        latest_timestamp = None
        latest_count = 0
        latest_dir = None
        
        # Search all timestamp directories
        for dir_path in base_path.iterdir():
            if dir_path.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', dir_path.name):
                json_file = dir_path / f"{module}.json"
                if json_file.exists():
                    # Parse timestamp from directory name
                    try:
                        dir_timestamp = datetime.strptime(dir_path.name, "%Y-%m-%d_%H-%M-%S")
                        if latest_timestamp is None or dir_timestamp > latest_timestamp:
                            # Load and count records
                            data = raw_data_handler.load_raw_json(module, dir_path.name, self.json_base_dir)
                            if data:  # Only update if we actually got data
                                latest_timestamp = dir_timestamp
                                latest_count = len(data)
                                latest_dir = dir_path.name
                                logger.debug(f"Found {module} in {dir_path.name}: {latest_count} records")
                    except ValueError:
                        continue  # Skip invalid directory names
        
        return latest_dir, latest_count
    
    def print_verification_report(self, results: Dict[str, Any]) -> None:
        """
        Print a formatted verification report in the requested table format.
        
        Args:
            results: Verification results dictionary
        """
        if "error" in results:
            print(f"❌ Verification failed: {results['error']}")
            return

        # Module name mapping for better display
        module_display_names = {
            "invoices": "Sales invoices",
            "items": "Products/services", 
            "contacts": "Customers/vendors",
            "customerpayments": "Customer payments",
            "bills": "Vendor bills",
            "vendorpayments": "Vendor payments",
            "salesorders": "Sales orders",
            "purchaseorders": "Purchase orders",
            "creditnotes": "Credit notes",
            "organizations": "Organization info"
        }

        print("\n" + "-" * 110)
        print(f"{'Endpoint':<22} {'API Count':<12} {'Local Count':<12} {'Line Items':<12} {'Difference':<12} {'Status'}")
        print("-" * 110)
        
        for module, data in results["modules"].items():
            display_name = module_display_names.get(module, module.title())
            
            # Format counts
            api_count = f"{data['api_count']:,}" if data['api_count'] >= 0 else "N/A"
            local_count = f"{data['local_count']:,}" if data['local_count'] >= 0 else "0"
            
            # Format line items
            line_items = "N/A"
            if data.get("line_item_details"):
                line_details = data["line_item_details"]
                if line_details["line_items"] > 0:
                    line_items = f"{line_details['line_items']:,}"
            
            # Format difference and status
            if data["status"] == "perfect_match":
                difference = "Perfect"
                status = "✅ Match"
            elif data["status"] == "api_error":
                difference = "Error"
                status = f"❌ API Error"
            else:
                diff_val = data['difference']
                if diff_val > 0:
                    difference = f"+{diff_val}"
                    status = f"❌ Off by +{diff_val}"
                elif diff_val < 0:
                    difference = f"{diff_val}"
                    status = f"❌ Off by {diff_val}"
                else:
                    difference = "Perfect"
                    status = "✅ Match"
            
            print(f"{display_name:<22} {api_count:<12} {local_count:<12} {line_items:<12} {difference:<12} {status}")
            
            if data.get("error"):
                print(f"{'':>22} Error: {data['error']}")
        
        print("-" * 110)
        
        # Summary
        summary = results['summary']
        total = summary['total_modules']
        matches = summary['perfect_matches']
        match_percentage = (matches / total * 100) if total > 0 else 0
        
        print(f"\n📊 Summary: {matches}/{total} modules match perfectly ({match_percentage:.1f}%)")
        if summary['discrepancies'] > 0:
            print(f"⚠️  {summary['discrepancies']} modules have discrepancies")
        if summary['api_errors'] > 0:
            print(f"❌ {summary['api_errors']} modules had API errors")
            
        # Calculate and display total line items
        total_line_items = 0
        line_item_breakdown = []
        for module, data in results["modules"].items():
            if data.get("line_item_details") and data["line_item_details"]["line_items"] > 0:
                count = data["line_item_details"]["line_items"]
                total_line_items += count
                line_item_breakdown.append(f"{module}: {count:,}")
        
        if total_line_items > 0:
            print(f"\n📋 Line Items Summary:")
            print(f"   Total line items across all modules: {total_line_items:,}")
            for breakdown in line_item_breakdown:
                print(f"   - {breakdown}")
    
    def get_modules_needing_sync(self, modules: List[str] = None) -> List[str]:
        """
        Get a list of modules that have discrepancies and need syncing.
        
        Args:
            modules: List of modules to check (uses standard list if None)
            
        Returns:
            List of module names that need syncing
        """
        if not modules:
            modules = ["contacts", "items", "bills", "invoices", "salesorders", 
                      "purchaseorders", "creditnotes", "customerpayments", 
                      "vendorpayments", "organizations"]
        
        # Run verification to get current status
        results = self.verify_data_completeness(modules=modules)
        
        if "error" in results:
            logger.error(f"Failed to verify modules: {results['error']}")
            return []
        
        modules_needing_sync = []
        for module, data in results["modules"].items():
            if data.get("status") != "perfect_match":
                modules_needing_sync.append(module)
                logger.info(f"Module '{module}' needs sync: API={data.get('api_count', 0)}, Local={data.get('local_count', 0)}")
        
        return modules_needing_sync
    
    def _get_line_item_counts(self, module: str, source_dir: str) -> Dict[str, int]:
        """
        Get line item counts for document modules.
        
        Args:
            module: Module name
            source_dir: Source directory containing the data
            
        Returns:
            Dictionary with header and line item counts
        """
        result = {"headers": 0, "line_items": 0}
        
        # Document modules that have line items
        document_modules = ["invoices", "bills", "salesorders", "purchaseorders", "creditnotes"]
        
        if module not in document_modules or not source_dir:
            return result
            
        try:
            # Get header count
            headers = raw_data_handler.load_raw_json(module, source_dir, self.json_base_dir)
            result["headers"] = len(headers) if headers else 0
            
            # Get line items count
            line_items_module = f"{module}_line_items"
            line_items = raw_data_handler.load_raw_json(line_items_module, source_dir, self.json_base_dir)
            result["line_items"] = len(line_items) if line_items else 0
            
            logger.debug(f"Module {module}: {result['headers']} headers, {result['line_items']} line items")
            
        except Exception as e:
            logger.warning(f"Could not get line item counts for {module}: {e}")
            
        return result
def verify_latest_data(modules: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to verify the latest JSON data against API.
    
    Args:
        modules: List of modules to verify (verifies all if None)
        
    Returns:
        Verification results dictionary
    """
    verifier = ApiLocalVerifier()
    return verifier.verify_data_completeness(modules=modules)
