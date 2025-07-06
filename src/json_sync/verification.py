def print_entity_comparison_table(api_counts, db_counts):
    """
    Print a formatted table comparing API (JSON) and database entity counts.
    Args:
        api_counts: dict of {entity: count}
        db_counts: dict of {entity: count}
    """
    header = (
        f"{'Endpoint':<22} {'Local API Count':>15} {'Database Count':>15} {'Difference':>12}   Status\n"
        + "-" * 80
    )
    print(header)
    for entity in sorted(set(api_counts) | set(db_counts)):
        api_count = api_counts.get(entity, 0)
        db_count = db_counts.get(entity, 0)
        diff = db_count - api_count
        if diff == 0:
            diff_str = 'Perfect'
            status = '✅ Match'
        else:
            diff_str = f"{diff:+d}"
            status = f"❌ Off by {diff_str}"
        print(f"{entity:<22} {api_count:>15} {db_count:>15} {diff_str:>12}   {status}")
"""
JSON Sync Verification and Reporting

Provides verification functions and formatted reports for JSON differential sync operations.
Includes data comparison reports and sync status verification.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .config import get_config
from .json_loader import JsonDataLoader

logger = logging.getLogger(__name__)

@dataclass
class EntityComparison:
    """Comparison data for a single entity."""
    entity: str
    display_name: str
    json_count: int
    db_count: int
    difference: int
    status: str
    match: bool

@dataclass
class VerificationReport:
    """Complete verification report data."""
    timestamp: str
    json_source: str
    database_path: str
    entity_comparisons: List[EntityComparison]
    total_json_records: int
    total_db_records: int
    perfect_matches: int
    total_entities: int
    match_percentage: float
    overall_difference: int
    sync_status: str

class SyncVerificationReporter:
    """
    Generates comprehensive verification reports for JSON sync operations.
    
    Features:
    - Data count comparisons between JSON and database
    - Formatted tabular reports
    - Summary statistics and status assessment
    - Integration with sync workflows
    """
    
    def __init__(self, database_path: Optional[str] = None, json_base_path: Optional[str] = None):
        """
        Initialize verification reporter.
        
        Args:
            database_path: Path to database (uses config default if None)
            json_base_path: Path to JSON data (uses config default if None)
        """
        config = get_config()
        self.database_path = database_path or config.database_path
        self.json_base_path = json_base_path or config.json_base_path
        
        # Entity mappings for display and database tables
        self.entity_tables = {
            'invoices': 'Invoices',
            'items': 'Items', 
            'contacts': 'Contacts',
            'customerpayments': 'CustomerPayments',
            'bills': 'Bills',
            'vendorpayments': 'VendorPayments', 
            'salesorders': 'SalesOrders',
            'purchaseorders': 'PurchaseOrders',
            'creditnotes': 'CreditNotes'
        }
        
        self.display_names = {
            'invoices': 'Sales invoices',
            'items': 'Products/services', 
            'contacts': 'Customers/vendors',
            'customerpayments': 'Customer payments',
            'bills': 'Vendor bills',
            'vendorpayments': 'Vendor payments',
            'salesorders': 'Sales orders', 
            'purchaseorders': 'Purchase orders',
            'creditnotes': 'Credit notes'
        }
    
    def get_database_counts(self) -> Dict[str, int]:
        """
        Get record counts from database for all entities.
        
        Returns:
            Dictionary mapping entity names to record counts
        """
        db_counts = {}
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            for entity, table in self.entity_tables.items():
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    db_counts[entity] = cursor.fetchone()[0]
                except Exception as e:
                    logger.warning(f"Could not read {table}: {e}")
                    db_counts[entity] = 0
            
            conn.close()
            logger.info(f"Retrieved database counts for {len(db_counts)} entities")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            # Return zeros for all entities
            for entity in self.entity_tables.keys():
                db_counts[entity] = 0
        
        return db_counts
    
    def get_json_counts(self, json_directory: Optional[str] = None) -> Tuple[Dict[str, int], str]:
        """
        Get record counts from JSON data.
        
        Args:
            json_directory: Specific JSON directory to use (uses latest if None)
            
        Returns:
            Tuple of (entity counts dict, source directory name)
        """
        json_counts = {}
        source_dir = ""
        
        try:
            if json_directory:
                # Use specific directory
                json_path = Path(json_directory)
                source_dir = json_path.name
            else:
                # Find latest directory
                json_base = Path(self.json_base_path)
                if not json_base.exists():
                    logger.error(f"JSON base path does not exist: {json_base}")
                    return {entity: 0 for entity in self.entity_tables.keys()}, "Not Found"
                
                json_dirs = [d for d in json_base.iterdir() if d.is_dir()]
                if not json_dirs:
                    logger.error("No JSON directories found")
                    return {entity: 0 for entity in self.entity_tables.keys()}, "No Directories"
                
                json_path = sorted(json_dirs, reverse=True)[0]
                source_dir = json_path.name
            
            # Load JSON data
            loader = JsonDataLoader(str(json_path))
            json_data = loader.load_all_entities()
            
            # Count records for each entity
            for entity in self.entity_tables.keys():
                json_counts[entity] = len(json_data.get(entity, []))
            
            logger.info(f"Retrieved JSON counts from {source_dir} for {len(json_counts)} entities")
            
        except Exception as e:
            logger.error(f"JSON loading error: {e}")
            # Return zeros for all entities
            for entity in self.entity_tables.keys():
                json_counts[entity] = 0
            source_dir = "Error"
        
        return json_counts, source_dir
    
    def generate_verification_report(self, json_directory: Optional[str] = None) -> VerificationReport:
        """
        Generate a comprehensive verification report.
        
        Args:
            json_directory: Specific JSON directory to use (uses latest if None)
            
        Returns:
            Complete verification report data
        """
        logger.info("Generating verification report")
        
        # Get data counts
        db_counts = self.get_database_counts()
        json_counts, json_source = self.get_json_counts(json_directory)
        
        # Generate entity comparisons
        entity_comparisons = []
        perfect_matches = 0
        total_json = 0
        total_db = 0
        
        for entity in self.entity_tables.keys():
            display_name = self.display_names.get(entity, entity.title())
            json_count = json_counts.get(entity, 0)
            db_count = db_counts.get(entity, 0)
            
            total_json += json_count
            total_db += db_count
            
            # Calculate difference
            diff = db_count - json_count
            
            # Determine status
            if diff == 0:
                status = '✅ Match'
                match = True
                perfect_matches += 1
            else:
                sign = '+' if diff > 0 else ''
                status = f'❌ Off by {sign}{diff}'
                match = False
            
            entity_comparisons.append(EntityComparison(
                entity=entity,
                display_name=display_name,
                json_count=json_count,
                db_count=db_count,
                difference=diff,
                status=status,
                match=match
            ))
        
        # Calculate summary statistics
        total_entities = len(self.entity_tables)
        match_percentage = (perfect_matches / total_entities) * 100 if total_entities > 0 else 0
        overall_difference = total_db - total_json
        
        # Determine sync status
        if perfect_matches == total_entities:
            sync_status = "✅ PERFECT SYNC - All entities match"
        elif perfect_matches >= total_entities * 0.8:
            sync_status = "⚠️  MOSTLY SYNCED - Minor differences detected"
        else:
            sync_status = "❌ SYNC ISSUES - Significant differences found"
        
        report = VerificationReport(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            json_source=json_source,
            database_path=self.database_path,
            entity_comparisons=entity_comparisons,
            total_json_records=total_json,
            total_db_records=total_db,
            perfect_matches=perfect_matches,
            total_entities=total_entities,
            match_percentage=match_percentage,
            overall_difference=overall_difference,
            sync_status=sync_status
        )
        
        logger.info(f"Verification report generated: {perfect_matches}/{total_entities} perfect matches")
        return report
    
    def print_formatted_report(self, report: VerificationReport) -> None:
        """
        Print a formatted verification report to console.
        
        Args:
            report: Verification report data to display
        """
        print("\n🔄 DATA COMPARISON VERIFICATION REPORT")
        print("=" * 90)
        print(f"📁 JSON Source: {report.json_source}")
        print(f"📊 Database: {report.database_path}")
        print(f"⏰ Generated: {report.timestamp}")
        print()
        
        # Print header
        print("Endpoint               Local API Count    Database Count  Difference   Status")
        print("-" * 90)
        
        # Print entity comparisons
        for comp in report.entity_comparisons:
            # Format counts with commas
            json_formatted = f'{comp.json_count:,}' if comp.json_count > 0 else '0'
            db_formatted = f'{comp.db_count:,}' if comp.db_count > 0 else '0'
            
            # Format difference
            if comp.difference == 0:
                diff_str = 'Perfect'
            else:
                sign = '+' if comp.difference > 0 else ''
                diff_str = f'{sign}{comp.difference}'
            
            # Print row with proper spacing
            print(f'{comp.display_name:<22} {json_formatted:>8}        {db_formatted:>8}        {diff_str:<12} {comp.status}')
        
        print("-" * 90)
        print()
        
        # Summary statistics
        print(f"📊 SUMMARY:")
        print(f"  🔹 Total JSON Records: {report.total_json_records:,}")
        print(f"  🔹 Total DB Records: {report.total_db_records:,}")
        print(f"  🔹 Perfect Matches: {report.perfect_matches}/{report.total_entities} entities ({report.match_percentage:.1f}%)")
        print(f"  🔹 Overall Difference: {report.overall_difference:+,} records")
        print(f"  🎯 Status: {report.sync_status}")
        print()
    
    def save_report_to_file(self, report: VerificationReport, output_path: str) -> None:
        """
        Save verification report to a file.
        
        Args:
            report: Verification report data
            output_path: Path to save the report
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(f"Data Comparison Verification Report\n")
            f.write(f"Generated: {report.timestamp}\n")
            f.write(f"JSON Source: {report.json_source}\n")
            f.write(f"Database: {report.database_path}\n\n")
            
            f.write("Endpoint               Local API Count    Database Count  Difference   Status\n")
            f.write("-" * 90 + "\n")
            
            for comp in report.entity_comparisons:
                json_formatted = f'{comp.json_count:,}' if comp.json_count > 0 else '0'
                db_formatted = f'{comp.db_count:,}' if comp.db_count > 0 else '0'
                
                if comp.difference == 0:
                    diff_str = 'Perfect'
                else:
                    sign = '+' if comp.difference > 0 else ''
                    diff_str = f'{sign}{comp.difference}'
                
                f.write(f'{comp.display_name:<22} {json_formatted:>8}        {db_formatted:>8}        {diff_str:<12} {comp.status}\n')
            
            f.write("-" * 90 + "\n\n")
            f.write(f"SUMMARY:\n")
            f.write(f"  Total JSON Records: {report.total_json_records:,}\n")
            f.write(f"  Total DB Records: {report.total_db_records:,}\n")
            f.write(f"  Perfect Matches: {report.perfect_matches}/{report.total_entities} entities ({report.match_percentage:.1f}%)\n")
            f.write(f"  Overall Difference: {report.overall_difference:+,} records\n")
            f.write(f"  Status: {report.sync_status}\n")
        
        logger.info(f"Verification report saved to: {output_path}")

def verify_sync_completion(database_path: Optional[str] = None, 
                          json_directory: Optional[str] = None,
                          print_report: bool = True,
                          save_to_file: Optional[str] = None) -> VerificationReport:
    """
    Verify sync completion and generate a comparison report.
    
    Args:
        database_path: Path to database (uses config default if None)
        json_directory: Specific JSON directory to verify against (uses latest if None)
        print_report: Whether to print the report to console
        save_to_file: Path to save report file (optional)
        
    Returns:
        Complete verification report data
    """
    reporter = SyncVerificationReporter(database_path)
    report = reporter.generate_verification_report(json_directory)
    
    if print_report:
        reporter.print_formatted_report(report)
    
    if save_to_file:
        reporter.save_report_to_file(report, save_to_file)
    
    return report

def get_sync_verification_summary(database_path: Optional[str] = None,
                                json_directory: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a summary of sync verification status.
    
    Args:
        database_path: Path to database (uses config default if None)
        json_directory: Specific JSON directory to verify against (uses latest if None)
        
    Returns:
        Dictionary with verification summary data
    """
    reporter = SyncVerificationReporter(database_path)
    report = reporter.generate_verification_report(json_directory)
    
    return {
        'timestamp': report.timestamp,
        'json_source': report.json_source,
        'total_entities': report.total_entities,
        'perfect_matches': report.perfect_matches,
        'match_percentage': report.match_percentage,
        'total_json_records': report.total_json_records,
        'total_db_records': report.total_db_records,
        'overall_difference': report.overall_difference,
        'sync_status': report.sync_status,
        'all_entities_match': report.perfect_matches == report.total_entities
    }
