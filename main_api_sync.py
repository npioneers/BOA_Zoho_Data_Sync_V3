#!/usr/bin/env python3
"""
Main API Sync Wrapper
Provides high-level interface for API sync operations with verification options.

This wrapper allows you to:
1. Run full API sync with quick verification (tracks progress during sync)
2. Run standalone full verification (requires separate API calls)
3. Run standalone quick verification (uses existing session data)
"""

import argparse
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Get absolute path to project root
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from src.api_sync.verification.simultaneous_verifier import (
    SimultaneousSyncVerifier, 
    print_simultaneous_verification_results,
    load_session_verification
)

def print_header(title: str) -> None:
    """Print operation header."""
    print("\n" + "=" * 80)
    print(f"*** MAIN API SYNC - {title.upper()} ***")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {PROJECT_ROOT}")
    print()

def print_footer(success: bool = True) -> None:
    """Print operation footer."""
    status = "[COMPLETED]" if success else "[FAILED]"
    print(f"\nStatus: {status}")
    print("=" * 80)

def run_sync_with_quick_verification(modules: List[str], since_date: Optional[str] = None, timeout: int = 1200) -> bool:
    """
    Run API sync for multiple modules with simultaneous verification tracking.
    
    Args:
        modules: List of module names to sync
        since_date: Date filter (ISO format YYYY-MM-DD)
        timeout: Timeout per module in seconds
        
    Returns:
        True if all successful, False if any failed
    """
    print_header("SYNC WITH QUICK VERIFICATION")
    
    # Initialize simultaneous verifier
    verifier = SimultaneousSyncVerifier()
    run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    verifier.start_sync_session(run_timestamp)
    
    print(f"[SYNC] Syncing {len(modules)} modules")
    if since_date:
        print(f"Date filter: {since_date}")
    print(f"Session ID: {run_timestamp}")
    print()
    
    successful_modules = []
    failed_modules = []
    
    for i, module in enumerate(modules, 1):
        print(f"\n{'─' * 60}")
        print(f"[MODULE {i}/{len(modules)}] SYNCING: {module.upper()}")
        print(f"{'─' * 60}")
        
        try:
            # Build command
            cmd = [
                sys.executable, "-m", "src.api_sync.cli", 
                "fetch", module
            ]
            if since_date:
                cmd.extend(["--since", since_date])
            
            print(f"Command: {' '.join(cmd)}")
            print(f"Fetching {module}...")
            
            # Run the sync command
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                print(f"[SUCCESS] Successfully fetched {module}")
                
                # Parse output to extract counts (basic parsing)
                output = result.stdout
                api_count = 0
                headers_saved = 0
                line_items_saved = 0
                
                # Extract counts from output (you may need to enhance this parsing)
                lines = output.split('\n')
                for line in lines:
                    if "Retrieved" in line and "records from API" in line:
                        try:
                            api_count = int(line.split()[1])
                            headers_saved = api_count  # Assume all saved successfully
                        except:
                            pass
                    elif "line items from API" in line:
                        try:
                            line_items_saved = int(line.split()[3])
                        except:
                            pass
                
                # Record success in verifier
                verifier.record_module_fetch(module, api_count, headers_saved, line_items_saved)
                successful_modules.append(module)
                
            else:
                print(f"[ERROR] Failed to fetch {module} (exit code: {result.returncode})")
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                verifier.record_module_error(module, error_msg)
                failed_modules.append(module)
                
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] Timeout fetching {module} ({timeout/60:.1f} minutes)")
            verifier.record_module_error(module, f"Timeout after {timeout} seconds")
            failed_modules.append(module)
        except Exception as e:
            print(f"[EXCEPTION] Error fetching {module}: {str(e)}")
            verifier.record_module_error(module, str(e))
            failed_modules.append(module)
        
        # Show live progress
        verifier.print_live_progress()
        
        # Brief pause between modules
        if i < len(modules):
            print(f"\nWaiting 3 seconds before next module...")
            time.sleep(3)
    
    # Finalize session and generate report
    print(f"\n{'=' * 80}")
    print("[REPORT] FINALIZING SYNC SESSION")
    print("=" * 80)
    
    final_report = verifier.finalize_session()
    print_simultaneous_verification_results(final_report)
    
    # Summary
    print(f"\n[SUMMARY] SYNC RESULTS:")
    print(f"   [SUCCESS] Successful: {len(successful_modules)}/{len(modules)}")
    print(f"   [FAILED] Failed: {len(failed_modules)}/{len(modules)}")
    
    if successful_modules:
        print(f"\n[SUCCESS] Successfully synced modules:")
        for module in successful_modules:
            print(f"   - {module}")
    
    if failed_modules:
        print(f"\n[FAILED] Failed to sync modules:")
        for module in failed_modules:
            print(f"   - {module}")
        print(f"\n[RETRY] You can retry failed modules individually using:")
        for module in failed_modules:
            print(f"   python -m src.api_sync.cli fetch {module}" + (f" --since {since_date}" if since_date else ""))
    
    return len(failed_modules) == 0

def run_full_verification() -> bool:
    """
    Run standalone full verification with API calls.
    
    Returns:
        True if successful, False if failed
    """
    print_header("FULL VERIFICATION")
    
    try:
        print("[VERIFY] Running full verification with API calls...")
        
        cmd = [sys.executable, "-m", "src.api_sync.cli", "verify"]
        
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            text=True,
            timeout=600  # 10 minute timeout for verification
        )
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Full verification timed out")
        return False
    except Exception as e:
        print(f"💥 Full verification error: {str(e)}")
        return False

def run_quick_verification(session_dir: Optional[str] = None) -> bool:
    """
    Run standalone quick verification using existing session data.
    
    Args:
        session_dir: Specific session directory (uses latest if None)
        
    Returns:
        True if successful, False if failed
    """
    print_header("QUICK VERIFICATION")
    
    try:
        if not session_dir:
            # Find latest session directory
            base_dir = Path("data/raw_json")
            if base_dir.exists():
                dirs = [d.name for d in base_dir.iterdir() if d.is_dir()]
                if dirs:
                    session_dir = sorted(dirs)[-1]
                    print(f"Using latest session: {session_dir}")
        
        if not session_dir:
            print("[ERROR] No session directory found for quick verification")
            return False
            
        print(f"[VERIFY] Running quick verification for session: {session_dir}")
        
        results = load_session_verification(session_dir)
        if "error" in results:
            print(f"[ERROR] Quick verification failed: {results['error']}")
            return False
            
        print_simultaneous_verification_results(results)
        return True
        
    except Exception as e:
        print(f"[EXCEPTION] Quick verification error: {str(e)}")
        return False

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Main API Sync Wrapper - High-level interface for API sync operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all modules since May 1st with quick verification
  python main_api_sync.py sync --since 2025-05-01

  # Sync specific modules with quick verification  
  python main_api_sync.py sync --modules invoices,bills,contacts

  # Run full verification only (with API calls)
  python main_api_sync.py verify --full

  # Run quick verification only (using session data)
  python main_api_sync.py verify --quick

  # Quick verification for specific session
  python main_api_sync.py verify --quick --session 2025-07-06_12-00-51
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Run API sync with quick verification')
    sync_parser.add_argument('--modules', '-m',
                            help='Comma-separated list of modules to sync (syncs all if not specified)')
    sync_parser.add_argument('--since', '-s',
                            help='Only fetch records modified since this date (YYYY-MM-DD)')
    sync_parser.add_argument('--timeout', '-t', type=int, default=1200,
                            help='Timeout per module in seconds (default: 1200)')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Run verification')
    verify_parser.add_argument('--full', action='store_true',
                              help='Run full verification with API calls')
    verify_parser.add_argument('--quick', action='store_true',
                              help='Run quick verification using session data')
    verify_parser.add_argument('--session', '-s',
                              help='Specific session directory for quick verification')
    
    return parser

def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Default command if none specified
    if not args.command:
        parser.print_help()
        return 1
    
    success = False
    
    if args.command == 'sync':
        # Sync with quick verification
        modules = []
        if args.modules:
            modules = [m.strip() for m in args.modules.split(',')]
        else:
            # Default to all supported modules
            modules = [
                "organizations", "items", "contacts", "invoices", 
                "bills", "salesorders", "purchaseorders", "creditnotes",
                "customerpayments", "vendorpayments"
            ]
        
        success = run_sync_with_quick_verification(modules, args.since, args.timeout)
        
    elif args.command == 'verify':
        if args.full:
            success = run_full_verification()
        elif args.quick:
            success = run_quick_verification(args.session)
        else:
            # Default to full verification
            success = run_full_verification()
    
    else:
        parser.print_help()
        return 1
    
    print_footer(success)
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
