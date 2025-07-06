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
    print(f"🔄 API SYNC - {operation.upper()}")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def print_footer(success: bool = True) -> None:
    """Print operation footer."""
    status = "✅ COMPLETED" if success else "❌ FAILED"
    print(f"\n🎯 Status: {status}")
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
        
        print(f"\n🔍 FETCHING DATA")
        print(f"📊 Module: {args.module}")
        print(f"📅 Since: {args.since or 'All records'}")
        
        run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Get credentials and initialize client
        print("\n--- Step 1: Authentication ---")
        zoho_credentials = secrets.get_zoho_credentials()
        access_token = auth.get_access_token(zoho_credentials)
        zoho_org_id = zoho_credentials.get('organization_id')
        print("✅ Authentication successful")
        
        # Initialize API client
        print("\n--- Step 2: Initializing API Client ---")
        zoho_client = client.ZohoClient(
            access_token, 
            zoho_org_id, 
            "https://www.zohoapis.com/books/v3"
        )
        print("✅ API client initialized")
        
        # Fetch data
        print(f"\n--- Step 3: Fetching {args.module} Data ---")
        records = zoho_client.get_data_for_module(args.module, since_timestamp=args.since)
        
        if not records:
            print(f"⚠️ No {args.module} found in API response")
            print_footer(True)
            return 0
        
        print(f"✅ Retrieved {len(records)} {args.module} records from API")
        
        # Save data
        print("\n--- Step 4: Saving Data ---")
        raw_data_handler.save_raw_json(records, args.module, run_timestamp)
        print(f"✅ Data saved to data/raw_json/{run_timestamp}/{args.module}.json")
        
        # Quick analysis
        print(f"\n--- Step 5: Quick Analysis ---")
        print(f"📊 Total records fetched: {len(records)}")
        
        # Check for line items in document modules
        if args.module in ['invoices', 'bills', 'salesorders', 'purchaseorders', 'creditnotes']:
            line_items_found = 0
            for record in records:
                if 'line_items' in record and record['line_items']:
                    line_items_found += len(record['line_items'])
            
            if line_items_found > 0:
                print(f"📋 Line items found: {line_items_found}")
        
        print_footer(True)
        return 0
        
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
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
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify local data against API')
    verify_parser.add_argument('--directory', '-d',
                              help='Specific timestamp directory to verify (uses latest if not specified)')
    verify_parser.add_argument('--modules', '-m',
                              help='Comma-separated list of modules to verify (verifies all if not specified)')
    verify_parser.add_argument('--output', '-o',
                              help='Save verification results to JSON file')
    
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
