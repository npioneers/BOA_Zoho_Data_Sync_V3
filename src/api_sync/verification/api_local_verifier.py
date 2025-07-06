"""
API vs Local Data Verification Module

Compares data counts between Zoho API and local JSON files to verify completeness.
"""

import json
import logging
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
        
        # Get timestamp directory
        if not timestamp_dir:
            timestamp_dir = raw_data_handler.get_latest_timestamp_dir(self.json_base_dir)
            if not timestamp_dir:
                return {"error": "No timestamp directories found"}
        
        logger.info(f"Verifying data in directory: {timestamp_dir}")
        
        # Get modules to verify
        if not modules:
            modules = self._get_available_modules(timestamp_dir)
        
        if not modules:
            return {"error": f"No JSON files found in {timestamp_dir}"}
        
        # Perform verification for each module
        results = {
            "timestamp": datetime.now().isoformat(),
            "directory": timestamp_dir,
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
            module_result = self._verify_module(module, timestamp_dir)
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
    
    def _verify_module(self, module: str, timestamp_dir: str) -> Dict[str, Any]:
        """
        Verify a specific module against API.
        
        Args:
            module: Module name
            timestamp_dir: Timestamp directory name
            
        Returns:
            Dictionary containing verification results for the module
        """
        result = {
            "module": module,
            "local_count": 0,
            "api_count": 0,
            "difference": 0,
            "status": "unknown",
            "error": None
        }
        
        try:
            # Get local count
            local_data = raw_data_handler.load_raw_json(module, timestamp_dir, self.json_base_dir)
            result["local_count"] = len(local_data)
            
            # Get API count
            api_data = self.api_client.get_data_for_module(module)
            result["api_count"] = len(api_data)
            
            # Calculate difference
            result["difference"] = result["api_count"] - result["local_count"]
            
            # Determine status
            if result["difference"] == 0:
                result["status"] = "perfect_match"
            else:
                result["status"] = "discrepancy"
            
            logger.info(f"Module {module}: Local={result['local_count']}, API={result['api_count']}, Diff={result['difference']}")
            
        except Exception as e:
            logger.error(f"Error verifying module {module}: {e}")
            result["error"] = str(e)
            result["status"] = "api_error"
        
        return result
    
    def print_verification_report(self, results: Dict[str, Any]) -> None:
        """
        Print a formatted verification report.
        
        Args:
            results: Verification results dictionary
        """
        if "error" in results:
            print(f"❌ Verification failed: {results['error']}")
            return
        
        print("\n" + "=" * 80)
        print("🔍 API VS LOCAL DATA VERIFICATION REPORT")
        print("=" * 80)
        print(f"📅 Timestamp: {results['timestamp']}")
        print(f"📁 Directory: {results['directory']}")
        print(f"📊 Total Modules: {results['summary']['total_modules']}")
        print(f"✅ Perfect Matches: {results['summary']['perfect_matches']}")
        print(f"⚠️  Discrepancies: {results['summary']['discrepancies']}")
        print(f"❌ API Errors: {results['summary']['api_errors']}")
        print(f"📈 Match Rate: {results['summary']['match_percentage']:.1f}%")
        
        print("\n" + "-" * 80)
        print(f"{'Module':<20} {'Local Count':<12} {'API Count':<12} {'Difference':<12} {'Status'}")
        print("-" * 80)
        
        for module, data in results["modules"].items():
            status_icon = "✅" if data["status"] == "perfect_match" else "❌" if data["status"] == "api_error" else "⚠️"
            print(f"{module:<20} {data['local_count']:<12,} {data['api_count']:<12,} {data['difference']:<+12,} {status_icon} {data['status']}")
            
            if data.get("error"):
                print(f"{'':>20} Error: {data['error']}")
        
        print("-" * 80)
        
        # Overall assessment
        if results["summary"]["match_percentage"] == 100:
            print("🎉 All modules have perfect matches! Data is completely synchronized.")
        elif results["summary"]["match_percentage"] >= 90:
            print("✅ Most modules match well. Minor discrepancies detected.")
        else:
            print("⚠️  Significant discrepancies detected. Investigation recommended.")


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
