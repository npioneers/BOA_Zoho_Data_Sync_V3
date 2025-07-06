"""
API Sync Command Line Interface

Provides command-line interface for API data fetching and verification operations.
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .core import auth, secrets, client
from .processing import raw_data_handler
from .verification import api_local_verifier
from .utils import get_latest_sync_timestamp

def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def print_header(operation: str) -> None:
    """Print operation header."""
    print("\n" + "=" * 60)
    print(f"*** API SYNC - {operation.upper()} ***")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def print_footer(success: bool = True) -> None:
    """Print operation footer."""
    status = "[COMPLETED]" if success else "[FAILED]"
    print(f"\nStatus: {status}")
    print("=" * 60)

def cmd_fetch(args) -> int:
    """
    Execute API fetch command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print_header("API DATA FETCH")
        
        # Determine the since timestamp
        since_timestamp = args.since
        if not since_timestamp and not args.full:
            # Auto-detect latest sync timestamp
            print("\n--- Auto-detecting Latest Sync ---")
            latest_sync = get_latest_sync_timestamp()
            if latest_sync:
                since_timestamp = latest_sync
                print(f"[OK] Using latest sync timestamp: {since_timestamp}")
            else:
                print("[WARN] No previous sync found, fetching all records")
        elif args.full:
            print("\n--- Full Sync Mode ---")
            print("[SYNC] Fetching all records (ignoring previous sync)")
            since_timestamp = None
        
        print(f"\n[FETCH] FETCHING DATA")
        print(f"Module: {args.module}")
        print(f"Since: {since_timestamp or 'All records'}")
        
        run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Get credentials and initialize client
        print("\n--- Step 1: Authentication ---")
        zoho_credentials = secrets.get_zoho_credentials()
        access_token = auth.get_access_token(zoho_credentials)
        zoho_org_id = zoho_credentials.get('organization_id')
        print("[OK] Authentication successful")
        
        # Initialize API client
        print("\n--- Step 2: Initializing API Client ---")
        zoho_client = client.ZohoClient(
            access_token, 
            zoho_org_id, 
            "https://www.zohoapis.com/books/v3"
        )
        print("[OK] API client initialized")
        
        # Fetch data
        print(f"\n--- Step 3: Fetching {args.module} Data ---")
        
        # Check if this module has line items
        if hasattr(zoho_client, 'MODULES_WITH_LINE_ITEMS') and args.module in zoho_client.MODULES_WITH_LINE_ITEMS:
            print(f"[FETCH] Fetching {args.module} with line items...")
            result = zoho_client.get_data_for_module_with_line_items(args.module, since_timestamp=since_timestamp)
            headers = result['headers']
            line_items = result['line_items']
            
            if not headers:
                print(f"[WARN] No {args.module} found in API response")
                print_footer(True)
                return 0
                
            print(f"[OK] Retrieved {len(headers)} {args.module} headers with {len(line_items)} line items from API")
            
            # Save both headers and line items
            print("\n--- Step 4: Saving Data ---")
            raw_data_handler.save_raw_json(headers, args.module, run_timestamp)
            print(f"[OK] Headers saved to data/raw_json/{run_timestamp}/{args.module}.json")
            
            if line_items:
                raw_data_handler.save_raw_json(line_items, f"{args.module}_line_items", run_timestamp)
                print(f"[OK] Line items saved to data/raw_json/{run_timestamp}/{args.module}_line_items.json")
            
        else:
            # Standard fetch for modules without line items
            records = zoho_client.get_data_for_module(args.module, since_timestamp=since_timestamp)
            
            if not records:
                print(f"[WARN] No {args.module} found in API response")
                print_footer(True)
                return 0
            
            print(f"[OK] Retrieved {len(records)} {args.module} records from API")
            
            # Save data
            print("\n--- Step 4: Saving Data ---")
            raw_data_handler.save_raw_json(records, args.module, run_timestamp)
            print(f"[OK] Data saved to data/raw_json/{run_timestamp}/{args.module}.json")
            
            headers = records
            line_items = []
        
        # Quick analysis
        print(f"\n--- Step 5: Quick Analysis ---")
        total_records = len(headers)
        if line_items:
            print(f"[DATA] Total headers: {len(headers)}")
            print(f"[DATA] Total line items: {len(line_items)}")
            print(f"[DATA] Total records: {total_records + len(line_items)}")
        else:
            print(f"[DATA] Total records fetched: {total_records}")
            
            # Check for line items in document modules (fallback for old method)
            if args.module in ['invoices', 'bills', 'salesorders', 'purchaseorders', 'creditnotes']:
                line_items_found = 0
                for record in headers:
                    if 'line_items' in record and record['line_items']:
                        line_items_found += len(record['line_items'])
                
                if line_items_found > 0:
                    print(f"[DATA] Line items found in headers: {line_items_found}")
        
        print_footer(True)
        return 0
        
    except Exception as e:
        print(f"[ERROR] Fetch failed: {e}")
        print_footer(False)
        return 1

def cmd_verify(args) -> int:
    """
    Execute verification command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.quick:
            # Quick verification using existing session data
            from .verification.simultaneous_verifier import load_session_verification
            
            print_header("QUICK VERIFICATION (SESSION DATA)")
            
            session_dir = args.session or args.directory
            if not session_dir:
                # Find the latest session directory
                base_dir = Path("data/raw_json")
                if base_dir.exists():
                    dirs = [d.name for d in base_dir.iterdir() if d.is_dir()]
                    if dirs:
                        session_dir = sorted(dirs)[-1]
                        print(f"📁 Using latest session: {session_dir}")
            
            if not session_dir:
                print("❌ No session directory found for quick verification")
                return 1
                
            results = load_session_verification(session_dir)
            if "error" in results:
                print(f"❌ Quick verification failed: {results['error']}")
                return 1
                
            # Print results using simultaneous verifier format
            from .verification.simultaneous_verifier import print_simultaneous_verification_results
            print_simultaneous_verification_results(results)
            
        else:
            # Full verification with API calls
            print_header("API VS LOCAL VERIFICATION")
            
            # Parse modules list
            modules = None
            if args.modules:
                modules = [m.strip() for m in args.modules.split(',')]
                print(f"📋 Modules: {modules}")
            else:
                print("📋 Modules: All available")
            
            # Run verification
            verifier = api_local_verifier.ApiLocalVerifier()
            results = verifier.verify_data_completeness(
                timestamp_dir=args.directory,
                modules=modules
            )
            
            # Print results
            verifier.print_verification_report(results)
        
        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Results saved to: {output_path}")
        
        print_footer(True)
        return 0
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        print_footer(False)
        return 1

def cmd_status(args) -> int:
    """
    Execute status command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print_header("API SYNC STATUS")
        
        print("\n📊 SYSTEM STATUS")
        print("-" * 30)
        
        # Check credentials
        try:
            secrets.get_zoho_credentials()
            print("🔐 Credentials: ✅ Available")
        except:
            print("🔐 Credentials: ❌ Not Available")
        
        # Check data directories
        base_dir = Path("data/raw_json")
        if base_dir.exists():
            dirs = [d.name for d in base_dir.iterdir() if d.is_dir()]
            print(f"📁 JSON Directories: ✅ {len(dirs)} available")
            
            if dirs:
                latest = sorted(dirs)[-1]
                print(f"📅 Latest Directory: {latest}")
                
                # Show modules in latest directory
                latest_path = base_dir / latest
                json_files = list(latest_path.glob("*.json"))
                if json_files:
                    print(f"📋 Available Modules ({len(json_files)}):")
                    for json_file in json_files:
                        try:
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                            print(f"  📄 {json_file.stem}: {len(data)} records")
                        except:
                            print(f"  📄 {json_file.stem}: Error reading file")
        else:
            print("📁 JSON Directories: ❌ data/raw_json not found")
        
        print_footer(True)
        return 0
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        print_footer(False)
        return 1

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="API Sync - Fetch and verify Zoho API data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='Set logging level')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch data from API')
    fetch_parser.add_argument('module', 
                             choices=['invoices', 'items', 'contacts', 'customerpayments',
                                    'bills', 'vendorpayments', 'salesorders', 'purchaseorders',
                                    'creditnotes', 'organizations'],
                             help='Module to fetch data from')
    fetch_parser.add_argument('--since',
                             help='Only fetch records modified since this timestamp (ISO format)')
    fetch_parser.add_argument('--full', action='store_true',
                             help='Fetch all records, ignore latest sync timestamp')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify local data against API')
    verify_parser.add_argument('--directory', '-d',
                              help='Specific timestamp directory to verify (uses latest if not specified)')
    verify_parser.add_argument('--modules', '-m',
                              help='Comma-separated list of modules to verify (verifies all if not specified)')
    verify_parser.add_argument('--output', '-o',
                              help='Save verification results to JSON file')
    verify_parser.add_argument('--quick', action='store_true',
                              help='Quick verification mode (no API calls, uses existing session data)')
    verify_parser.add_argument('--session', '-s',
                              help='Specific session directory to use for quick verification')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    return parser

def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Default command if none specified
    if not args.command:
        args.command = 'status'
    
    # Route to appropriate command handler
    if args.command == 'fetch':
        return cmd_fetch(args)
    elif args.command == 'verify':
        return cmd_verify(args)
    elif args.command == 'status':
        return cmd_status(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
