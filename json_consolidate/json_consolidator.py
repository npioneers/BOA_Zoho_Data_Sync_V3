"""
JSON Consolidator
Consolidates JSON files from multiple timestamp directories into unified files,
removes duplicates, validates data, and creates a compiled output directory.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Set
import hashlib


class JSONConsolidator:
    """Consolidates JSON files from raw_json directories"""
    
    def __init__(self, raw_json_dir: str = "data/raw_json", 
                 output_dir: str = "data/raw_json/json_compiled"):
        self.raw_json_dir = Path(raw_json_dir)
        self.output_dir = Path(output_dir)
        self.setup_logging()
        
        # Statistics tracking
        self.stats = {
            "directories_processed": 0,
            "files_processed": 0,
            "total_records": 0,
            "duplicates_removed": 0,
            "errors_found": 0,
            "critical_errors": 0,
            "output_files_created": 0,
            "new_files_found": 0,
            "skipped_files": 0
        }
        
        # Error tracking for validation
        self.validation_errors = []
        self.critical_errors = []
        
        # Freshness tracking
        self.processed_files_log = self.output_dir / "processed_files.json"
        self.processed_files = self.load_processed_files()
        
    def setup_logging(self):
        """Setup logging for consolidation process"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"json_consolidation_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"JSON Consolidation started - Logging to: {log_file}")

    def get_record_hash(self, record: Dict[str, Any]) -> str:
        """Generate a hash for a record to identify duplicates"""
        # Create a stable string representation for hashing
        # Remove timestamps and other volatile fields that might change
        stable_record = record.copy()
        
        # Remove common timestamp fields that might vary between API calls
        volatile_fields = ['last_modified_time', 'created_time', 'time_entries']
        for field in volatile_fields:
            stable_record.pop(field, None)
        
        # Create hash from sorted JSON string
        record_str = json.dumps(stable_record, sort_keys=True, default=str)
        return hashlib.md5(record_str.encode()).hexdigest()

    def validate_json_record(self, record: Dict[str, Any], record_type: str) -> bool:
        """Validate a JSON record for basic integrity"""
        if not isinstance(record, dict):
            error_msg = f"Invalid record type in {record_type}: expected dict, got {type(record)}"
            self.logger.error(error_msg)
            self.validation_errors.append(error_msg)
            self.stats["errors_found"] += 1
            return False
        
        # Check for required ID field based on record type
        id_field_map = {
            "invoices": "invoice_id",
            "bills": "bill_id", 
            "items": "item_id",
            "contacts": "contact_id",
            "organizations": "organization_id",
            "customerpayments": "payment_id",
            "vendorpayments": "payment_id",
            "salesorders": "salesorder_id",
            "purchaseorders": "purchaseorder_id",
            "creditnotes": "creditnote_id"
        }
        
        # Handle line items differently - they don't need parent IDs
        if "_line_items" in record_type:
            # Line items should have their own line_item_id or similar
            if "line_item_id" not in record and "item_id" not in record:
                error_msg = f"Missing line item ID in {record_type}"
                self.logger.warning(error_msg)
                self.validation_errors.append(error_msg)
                self.stats["errors_found"] += 1
                # Don't fail validation for line items missing parent IDs
            return True
        
        # For main records, check for required ID
        base_type = record_type.replace("_line_items", "")
        expected_id_field = id_field_map.get(base_type)
        
        if expected_id_field and expected_id_field not in record:
            error_msg = f"Missing required ID field '{expected_id_field}' in {record_type}"
            self.logger.error(error_msg)
            self.critical_errors.append(error_msg)
            self.stats["critical_errors"] += 1
            return False
        
        return True

    def get_timestamp_directories(self) -> List[Path]:
        """Get all timestamp directories, excluding special ones"""
        dirs = []
        for item in self.raw_json_dir.iterdir():
            if (item.is_dir() and 
                not item.name.startswith("CONSOLIDATED") and 
                not item.name.startswith("TEST") and
                not item.name == "json_compiled"):
                dirs.append(item)
        
        # Sort by timestamp (newest first)
        dirs.sort(reverse=True)
        return dirs

    def load_processed_files(self) -> Dict[str, Dict[str, Any]]:
        """Load the list of already processed files"""
        if self.processed_files_log.exists():
            try:
                with open(self.processed_files_log, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load processed files log: {e}")
                return {}
        return {}
    
    def save_processed_files(self):
        """Save the list of processed files"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            with open(self.processed_files_log, 'w') as f:
                json.dump(self.processed_files, f, indent=2, default=str)
            self.logger.info(f"Processed files log saved to: {self.processed_files_log}")
        except Exception as e:
            self.logger.error(f"Could not save processed files log: {e}")
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file metadata for freshness checking"""
        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "modified_time": stat.st_mtime,
            "path": str(file_path)
        }
    
    def is_file_new_or_changed(self, file_path: Path) -> bool:
        """Check if a file is new or has been modified since last processing"""
        file_key = str(file_path.relative_to(self.raw_json_dir))
        current_info = self.get_file_info(file_path)
        
        if file_key not in self.processed_files:
            return True  # New file
        
        previous_info = self.processed_files[file_key]
        
        # Check if file has been modified
        if (current_info["size"] != previous_info.get("size") or
            current_info["modified_time"] != previous_info.get("modified_time")):
            return True  # File changed
        
        return False  # File unchanged
    
    def mark_file_as_processed(self, file_path: Path):
        """Mark a file as processed"""
        file_key = str(file_path.relative_to(self.raw_json_dir))
        self.processed_files[file_key] = self.get_file_info(file_path)
    
    def check_for_new_files(self) -> Dict[str, List[Path]]:
        """Check all directories for new or changed files"""
        new_files_by_type = defaultdict(list)
        timestamp_dirs = self.get_timestamp_directories()
        
        self.logger.info("Checking for new or modified files...")
        
        for timestamp_dir in timestamp_dirs:
            for json_file in timestamp_dir.glob("*.json"):
                if self.is_file_new_or_changed(json_file):
                    file_type = json_file.stem
                    new_files_by_type[file_type].append(json_file)
                    self.stats["new_files_found"] += 1
                else:
                    self.stats["skipped_files"] += 1
        
        return new_files_by_type

    def consolidate_json_files(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Main consolidation process with freshness checking"""
        self.logger.info("Starting JSON file consolidation")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not force_rebuild:
            # Check for new or modified files only
            new_files_by_type = self.check_for_new_files()
            
            if not new_files_by_type:
                self.logger.info("No new or modified files found. Consolidation skipped.")
                self.logger.info(f"Skipped {self.stats['skipped_files']} unchanged files")
                return self.generate_skip_report()
            
            self.logger.info(f"Found {self.stats['new_files_found']} new/modified files")
            self.logger.info(f"Skipped {self.stats['skipped_files']} unchanged files")
            json_files_by_type = new_files_by_type
        else:
            # Force full rebuild - collect all files
            self.logger.info("Force rebuild mode - processing all files")
            json_files_by_type = defaultdict(list)
            timestamp_dirs = self.get_timestamp_directories()
            
            self.logger.info(f"Found {len(timestamp_dirs)} timestamp directories to process")
            
            # Scan all directories for JSON files
            for timestamp_dir in timestamp_dirs:
                self.stats["directories_processed"] += 1
                self.logger.info(f"Scanning directory: {timestamp_dir.name}")
                
                for json_file in timestamp_dir.glob("*.json"):
                    file_type = json_file.stem  # filename without extension
                    json_files_by_type[file_type].append(json_file)
                    self.stats["files_processed"] += 1
        
        self.logger.info(f"Found {len(json_files_by_type)} unique JSON file types")
        
        # Process each file type
        consolidated_data = {}
        for file_type, file_list in json_files_by_type.items():
            self.logger.info(f"Consolidating {file_type}: {len(file_list)} files")
            consolidated_data[file_type] = self.consolidate_file_type(file_type, file_list)
            
            # Mark all processed files
            for file_path in file_list:
                self.mark_file_as_processed(file_path)
            
            # Check for critical errors after each file type
            if self.stats["critical_errors"] > 0:
                self.logger.error(f"Critical errors found during consolidation of {file_type}")
                self.log_errors_and_exit()
        
        # Final check for any accumulated errors
        if self.stats["critical_errors"] > 0:
            self.log_errors_and_exit()
        
        # Save processed files log
        self.save_processed_files()
        
        # Generate summary report
        return self.generate_consolidation_report(consolidated_data)

    def consolidate_file_type(self, file_type: str, file_list: List[Path]) -> Dict[str, Any]:
        """Consolidate all files of a specific type"""
        all_records = []
        seen_hashes = set()
        file_errors = []
        
        # Sort files by timestamp (newest first)
        file_list.sort(key=lambda f: f.parent.name, reverse=True)
        
        for json_file in file_list:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both list and dict formats
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict) and 'data' in data:
                    records = data['data']
                elif isinstance(data, dict):
                    records = [data]  # Single record
                else:
                    self.logger.warning(f"Unexpected data format in {json_file}")
                    continue
                
                # Process each record
                for record in records:
                    if self.validate_json_record(record, file_type):
                        record_hash = self.get_record_hash(record)
                        
                        if record_hash not in seen_hashes:
                            all_records.append(record)
                            seen_hashes.add(record_hash)
                            self.stats["total_records"] += 1
                        else:
                            self.stats["duplicates_removed"] += 1
                    else:
                        self.stats["errors_found"] += 1
                        
            except Exception as e:
                error_msg = f"Error processing {json_file}: {str(e)}"
                self.logger.error(error_msg)
                file_errors.append(error_msg)
                self.stats["errors_found"] += 1
        
        # Save consolidated file
        output_file = self.output_dir / f"{file_type}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, indent=2, default=str)
            
            self.stats["output_files_created"] += 1
            self.logger.info(f"Created {output_file} with {len(all_records)} records")
            
        except Exception as e:
            self.logger.error(f"Error saving {output_file}: {str(e)}")
            self.stats["errors_found"] += 1
        
        return {
            "total_records": len(all_records),
            "duplicates_removed": self.stats["duplicates_removed"],
            "file_errors": file_errors,
            "output_file": str(output_file)
        }

    def generate_consolidation_report(self, consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive consolidation report"""
        report = {
            "consolidation_timestamp": datetime.now().isoformat(),
            "statistics": self.stats.copy(),
            "file_types": {},
            "summary": {}
        }
        
        total_consolidated_records = 0
        for file_type, data in consolidated_data.items():
            report["file_types"][file_type] = {
                "records": data["total_records"],
                "output_file": data["output_file"],
                "errors": len(data["file_errors"])
            }
            total_consolidated_records += data["total_records"]
        
        # Summary
        report["summary"] = {
            "total_file_types": len(consolidated_data),
            "total_consolidated_records": total_consolidated_records,
            "consolidation_efficiency": round(
                (total_consolidated_records / max(self.stats["total_records"], 1)) * 100, 2
            )
        }
        
        # Save report
        report_file = self.output_dir / "consolidation_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Consolidation report saved to: {report_file}")
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
        
        return report

    def generate_skip_report(self) -> Dict[str, Any]:
        """Generate a report when consolidation is skipped due to no new files"""
        return {
            "consolidation_skipped": True,
            "reason": "No new or modified files found",
            "statistics": {
                "skipped_files": self.stats["skipped_files"],
                "new_files_found": self.stats["new_files_found"],
                "last_check_time": datetime.now().isoformat()
            },
            "summary": {
                "message": "Consolidation skipped - no changes detected",
                "skipped_files": self.stats["skipped_files"]
            }
        }

    def print_consolidation_summary(self, report: Dict[str, Any]):
        """Print a formatted summary of consolidation results"""
        print("\n" + "="*70)
        print("JSON CONSOLIDATION SUMMARY")
        print("="*70)
        
        # Handle skip case
        if report.get("consolidation_skipped"):
            print("CONSOLIDATION SKIPPED")
            print(f"Reason: {report['reason']}")
            print(f"Files Checked: {report['statistics']['skipped_files']}")
            print(f"New Files Found: {report['statistics']['new_files_found']}")
            print(f"Last Check: {report['statistics']['last_check_time']}")
            print("\nNo consolidation needed - all files are up to date.")
            print("="*70)
            return
        
        stats = report["statistics"]
        print(f"Directories Processed: {stats['directories_processed']}")
        print(f"Files Processed: {stats['files_processed']}")
        print(f"Total Records Found: {stats['total_records']}")
        print(f"Duplicates Removed: {stats['duplicates_removed']}")
        print(f"Errors Found: {stats['errors_found']}")
        print(f"Output Files Created: {stats['output_files_created']}")
        
        # Show freshness stats if available
        if "new_files_found" in stats:
            print(f"New/Modified Files: {stats['new_files_found']}")
            print(f"Skipped Files: {stats['skipped_files']}")
        
        print("\nFILE TYPE BREAKDOWN:")
        print("-" * 50)
        print(f"{'File Type':<25} {'Records':<10} {'Status'}")
        print("-" * 50)
        
        for file_type, data in report["file_types"].items():
            status = "✓ Success" if data["errors"] == 0 else f"✗ {data['errors']} errors"
            print(f"{file_type:<25} {data['records']:<10} {status}")
        
        print("-" * 50)
        print(f"{'TOTAL':<25} {report['summary']['total_consolidated_records']:<10}")
        print("="*70)

    def log_errors_and_exit(self):
        """Log all errors and exit the process"""
        self.logger.error("="*70)
        self.logger.error("CRITICAL ERRORS FOUND - CONSOLIDATION STOPPED")
        self.logger.error("="*70)
        
        if self.critical_errors:
            self.logger.error(f"Critical errors ({len(self.critical_errors)}):")
            for i, error in enumerate(self.critical_errors, 1):
                self.logger.error(f"  {i}. {error}")
        
        if self.validation_errors:
            self.logger.error(f"Validation errors ({len(self.validation_errors)}):")
            for i, error in enumerate(self.validation_errors, 1):
                self.logger.error(f"  {i}. {error}")
        
        self.logger.error("="*70)
        self.logger.error("Please fix the above errors before proceeding with consolidation.")
        self.logger.error("Check the source JSON files for missing required fields.")
        self.logger.error("="*70)
        
        # Write error report to file
        error_report_file = Path("logs") / f"json_consolidation_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_report_file, 'w') as f:
            f.write("JSON CONSOLIDATION ERROR REPORT\n")
            f.write("="*50 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Critical Errors: {len(self.critical_errors)}\n")
            f.write(f"Validation Errors: {len(self.validation_errors)}\n\n")
            
            f.write("CRITICAL ERRORS:\n")
            for error in self.critical_errors:
                f.write(f"- {error}\n")
            
            f.write("\nVALIDATION ERRORS:\n")
            for error in self.validation_errors:
                f.write(f"- {error}\n")
        
        self.logger.error(f"Error report saved to: {error_report_file}")
        
        # Exit with error code
        raise SystemExit(1)


def main():
    """Main function to run JSON consolidation"""
    consolidator = JSONConsolidator()
    
    try:
        # Run consolidation
        report = consolidator.consolidate_json_files()
        
        # Print summary
        consolidator.print_consolidation_summary(report)
        
        print(f"\nConsolidated files saved to: {consolidator.output_dir}")
        print(f"Consolidation efficiency: {report['summary']['consolidation_efficiency']}%")
        
    except Exception as e:
        logging.error(f"Consolidation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
