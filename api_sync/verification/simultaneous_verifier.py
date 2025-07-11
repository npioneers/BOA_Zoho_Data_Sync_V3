"""
Simultaneous Sync Verifier Module

Provides real-time verification during API sync operations, tracking progress
and building verification reports without requiring separate API calls.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from ..processing import raw_data_handler

logger = logging.getLogger(__name__)

class SimultaneousSyncVerifier:
    """
    Tracks API sync operations in real-time and builds verification reports
    without requiring additional API calls.
    """
    
    def __init__(self, json_base_dir: str = "data/raw_json"):
        """
        Initialize the simultaneous verifier.
        
        Args:
            json_base_dir: Base directory containing JSON data directories
        """
        self.json_base_dir = json_base_dir
        self.sync_session = {
            "start_time": None,
            "end_time": None,
            "modules_processed": {},
            "errors": [],
            "session_dir": None
        }
        self.api_counts = {}  # Store API counts as we fetch
        
    def start_sync_session(self, session_dir: str) -> None:
        """
        Start a new sync session.
        
        Args:
            session_dir: Directory name for this sync session
        """
        self.sync_session = {
            "start_time": datetime.now(),
            "end_time": None,
            "modules_processed": {},
            "errors": [],
            "session_dir": session_dir
        }
        self.api_counts = {}
        logger.info(f"Started simultaneous verification session: {session_dir}")
        
    def record_module_fetch(self, module: str, api_count: int, headers_saved: int, line_items_saved: int = 0) -> None:
        """
        Record the results of a module fetch operation.
        
        Args:
            module: Module name
            api_count: Count from API response
            headers_saved: Number of headers saved to local storage
            line_items_saved: Number of line items saved (if applicable)
        """
        module_data = {
            "api_count": api_count,
            "headers_saved": headers_saved,
            "line_items_saved": line_items_saved,
            "timestamp": datetime.now(),
            "status": "success",
            "difference": api_count - headers_saved
        }
        
        self.sync_session["modules_processed"][module] = module_data
        self.api_counts[module] = api_count
        
        logger.info(f"Recorded {module}: API={api_count}, Headers={headers_saved}, LineItems={line_items_saved}")
        
    def record_module_error(self, module: str, error: str) -> None:
        """
        Record an error during module fetch.
        
        Args:
            module: Module name
            error: Error description
        """
        module_data = {
            "api_count": -1,
            "headers_saved": 0,
            "line_items_saved": 0,
            "timestamp": datetime.now(),
            "status": "error",
            "error": error,
            "difference": 0
        }
        
        self.sync_session["modules_processed"][module] = module_data
        self.sync_session["errors"].append(f"{module}: {error}")
        
        logger.error(f"Recorded error for {module}: {error}")
        
    def get_live_progress(self) -> Dict[str, Any]:
        """
        Get current sync progress for live monitoring.
        
        Returns:
            Dictionary with current progress information
        """
        processed = len(self.sync_session["modules_processed"])
        successful = len([m for m in self.sync_session["modules_processed"].values() if m["status"] == "success"])
        errors = len(self.sync_session["errors"])
        
        total_headers = sum(m.get("headers_saved", 0) for m in self.sync_session["modules_processed"].values())
        total_line_items = sum(m.get("line_items_saved", 0) for m in self.sync_session["modules_processed"].values())
        
        return {
            "session_dir": self.sync_session["session_dir"],
            "start_time": self.sync_session["start_time"],
            "modules_processed": processed,
            "successful_modules": successful,
            "errors": errors,
            "total_headers": total_headers,
            "total_line_items": total_line_items,
            "modules": self.sync_session["modules_processed"]
        }
        
    def finalize_session(self) -> Dict[str, Any]:
        """
        Finalize the sync session and generate final report.
        
        Returns:
            Complete verification report
        """
        self.sync_session["end_time"] = datetime.now()
        
        # Generate comprehensive report
        report = self._generate_verification_report()
        
        # Save session data for future reference
        self._save_session_data()
        
        logger.info("Finalized simultaneous verification session")
        return report
        
    def _generate_verification_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive verification report.
        
        Returns:
            Complete verification report matching the standard format
        """
        modules_data = {}
        total_modules = len(self.sync_session["modules_processed"])
        perfect_matches = 0
        discrepancies = 0
        api_errors = 0
        
        # Module name mapping for display
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
        
        for module, data in self.sync_session["modules_processed"].items():
            if data["status"] == "error":
                api_errors += 1
                status = "api_error"
            elif data["difference"] == 0:
                perfect_matches += 1
                status = "perfect_match"
            else:
                discrepancies += 1
                status = "discrepancy"
                
            # Get line item details for document modules
            line_item_details = None
            if data.get("line_items_saved", 0) > 0:
                line_item_details = {
                    "headers": data["headers_saved"],
                    "line_items": data["line_items_saved"]
                }
                
            modules_data[module] = {
                "module": module,
                "api_count": data["api_count"],
                "local_count": data["headers_saved"],
                "difference": data["difference"],
                "status": status,
                "error": data.get("error"),
                "source_dir": self.sync_session["session_dir"],
                "line_item_details": line_item_details,
                "sync_timestamp": data["timestamp"]
            }
            
        # Calculate session duration
        duration = None
        if self.sync_session["start_time"] and self.sync_session["end_time"]:
            duration = self.sync_session["end_time"] - self.sync_session["start_time"]
            
        return {
            "verification_type": "simultaneous_sync",
            "session_info": {
                "session_dir": self.sync_session["session_dir"],
                "start_time": self.sync_session["start_time"],
                "end_time": self.sync_session["end_time"],
                "duration": duration.total_seconds() if duration else None
            },
            "modules": modules_data,
            "summary": {
                "total_modules": total_modules,
                "perfect_matches": perfect_matches,
                "discrepancies": discrepancies,
                "api_errors": api_errors,
                "match_percentage": (perfect_matches / total_modules * 100) if total_modules > 0 else 0
            }
        }
        
    def _save_session_data(self) -> None:
        """
        Save session data to a JSON file for future reference.
        """
        try:
            session_file = Path(self.json_base_dir) / self.sync_session["session_dir"] / "sync_verification_session.json"
            
            # Convert datetime objects to strings for JSON serialization
            session_data = self.sync_session.copy()
            for module_data in session_data["modules_processed"].values():
                if "timestamp" in module_data:
                    module_data["timestamp"] = module_data["timestamp"].isoformat()
                    
            if session_data["start_time"]:
                session_data["start_time"] = session_data["start_time"].isoformat()
            if session_data["end_time"]:
                session_data["end_time"] = session_data["end_time"].isoformat()
                
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            logger.info(f"Saved sync session data to {session_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save session data: {e}")
            
    def print_live_progress(self) -> None:
        """
        Print current progress in a user-friendly format.
        """
        progress = self.get_live_progress()
        
        print(f"\n[PROGRESS] LIVE SYNC PROGRESS")
        print(f"Session: {progress['session_dir']}")
        print(f"Modules: {progress['successful_modules']}/{progress['modules_processed']} successful")
        if progress['errors'] > 0:
            print(f"[ERROR] Errors: {progress['errors']}")
        print(f"Records: {progress['total_headers']:,} headers, {progress['total_line_items']:,} line items")
        
        if progress['modules']:
            print(f"\n[MODULES] Latest modules:")
            recent_modules = list(progress['modules'].items())[-3:]  # Show last 3
            for module, data in recent_modules:
                status = "[OK]" if data['status'] == 'success' else "[ERR]"
                line_info = f" + {data.get('line_items_saved', 0)} items" if data.get('line_items_saved', 0) > 0 else ""
                print(f"   {status} {module}: {data.get('headers_saved', 0)} headers{line_info}")


def print_simultaneous_verification_results(results: Dict[str, Any]) -> None:
    """
    Print simultaneous verification results in the standard enhanced format.
    
    Args:
        results: Results dictionary from simultaneous verification
    """
    if "error" in results:
        print(f"[ERROR] Verification Error: {results['error']}")
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

    print("\n" + "=" * 110)
    print("[REPORT] SIMULTANEOUS SYNC VERIFICATION REPORT")
    print("=" * 110)
    
    # Session info
    session_info = results.get("session_info", {})
    print(f"Session: {session_info.get('session_dir', 'Unknown')}")
    print(f"Duration: {session_info.get('duration', 0):.1f} seconds" if session_info.get('duration') else "Duration: Unknown")
    
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
            status = "[MATCH] Match"
        elif data["status"] == "api_error":
            difference = "Error"
            status = f"[ERROR] API Error"
        else:
            diff_val = data['difference']
            if diff_val > 0:
                difference = f"+{diff_val}"
                status = f"[DIFF] Off by +{diff_val}"
            elif diff_val < 0:
                difference = f"{diff_val}"
                status = f"[DIFF] Off by {diff_val}"
            else:
                difference = "Perfect"
                status = "[MATCH] Match"
        
        print(f"{display_name:<22} {api_count:<12} {local_count:<12} {line_items:<12} {difference:<12} {status}")
        
        if data.get("error"):
            print(f"{'':>22} Error: {data['error']}")
    
    print("-" * 110)
    
    # Summary
    summary = results['summary']
    total = summary['total_modules']
    matches = summary['perfect_matches']
    match_percentage = summary['match_percentage']
    
    print(f"\n[SUMMARY] Summary: {matches}/{total} modules match perfectly ({match_percentage:.1f}%)")
    if summary['discrepancies'] > 0:
        print(f"[WARNING] {summary['discrepancies']} modules have discrepancies")
    if summary['api_errors'] > 0:
        print(f"[ERROR] {summary['api_errors']} modules had API errors")
        
    # Calculate and display total line items
    total_line_items = 0
    line_item_breakdown = []
    for module, data in results["modules"].items():
        if data.get("line_item_details") and data["line_item_details"]["line_items"] > 0:
            count = data["line_item_details"]["line_items"]
            total_line_items += count
            line_item_breakdown.append(f"{module}: {count:,}")
    
    if total_line_items > 0:
        print(f"\n[LINE ITEMS] Line Items Summary:")
        print(f"   Total line items across all modules: {total_line_items:,}")
        for breakdown in line_item_breakdown:
            print(f"   - {breakdown}")
            
    print("=" * 110)

def load_session_verification(session_dir: str, json_base_dir: str = "data/raw_json") -> Dict[str, Any]:
    """
    Load verification results from a saved session.
    
    Args:
        session_dir: Session directory name
        json_base_dir: Base directory containing JSON data
        
    Returns:
        Verification results dictionary
    """
    try:
        session_file = Path(json_base_dir) / session_dir / "sync_verification_session.json"
        
        if not session_file.exists():
            return {"error": f"No session data found in {session_dir}"}
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
            
        # Convert back to verification format
        modules_data = {}
        for module, data in session_data.get("modules_processed", {}).items():
            line_item_details = None
            if data.get("line_items_saved", 0) > 0:
                line_item_details = {
                    "headers": data["headers_saved"],
                    "line_items": data["line_items_saved"]
                }
                
            modules_data[module] = {
                "module": module,
                "api_count": data["api_count"],
                "local_count": data["headers_saved"],
                "difference": data["difference"],
                "status": data["status"],
                "error": data.get("error"),
                "source_dir": session_dir,
                "line_item_details": line_item_details
            }
            
        # Calculate summary
        total_modules = len(modules_data)
        perfect_matches = len([m for m in modules_data.values() if m["status"] == "success"])
        api_errors = len([m for m in modules_data.values() if m["status"] == "error"])
        discrepancies = total_modules - perfect_matches - api_errors
        
        return {
            "verification_type": "quick_session",
            "session_info": {
                "session_dir": session_dir,
                "start_time": session_data.get("start_time"),
                "end_time": session_data.get("end_time")
            },
            "modules": modules_data,
            "summary": {
                "total_modules": total_modules,
                "perfect_matches": perfect_matches,
                "discrepancies": discrepancies,
                "api_errors": api_errors,
                "match_percentage": (perfect_matches / total_modules * 100) if total_modules > 0 else 0
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to load session data: {str(e)}"}
