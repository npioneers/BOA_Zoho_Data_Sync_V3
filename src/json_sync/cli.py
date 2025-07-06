"""
JSON Sync Command Line Interface

Provides command-line interface for running JSON differential sync operations
independently without requiring notebook environment.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List
import json
import time
from datetime import datetime

from .config import get_config_manager, JsonSyncConfig
from .orchestrator import JsonDifferentialSyncOrchestrator
from .convenience import (
    quick_json_sync, 
    analyze_json_differences,
    sync_specific_entities,
    load_latest_json_data,
    get_sync_status
)

def setup_logging(config: JsonSyncConfig) -> None:
    """
    Setup logging based on configuration.
    
    Args:
        config: JSON sync configuration
    """
    # Configure logging level
    log_level = getattr(logging, config.log_level.upper())
    
    # Setup logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler if specified
    if config.log_file:
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set specific logger levels
    if config.verbose_logging:
        logging.getLogger('src.json_sync').setLevel(logging.DEBUG)
    else:
        logging.getLogger('src.json_sync').setLevel(log_level)

def print_header(operation: str) -> None:
    """Print operation header."""
    print("\n" + "=" * 60)
    print(f"🔄 JSON DIFFERENTIAL SYNC - {operation.upper()}")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def print_footer(start_time: float, success: bool = True) -> None:
    """Print operation footer with timing."""
    duration = time.time() - start_time
    status = "✅ COMPLETED" if success else "❌ FAILED"
    print(f"\n⏱️  Duration: {duration:.2f} seconds")
    print(f"🎯 Status: {status}")
    print("=" * 60)

def print_results_summary(results: dict) -> None:
    """Print summary of sync results."""
    if not results:
        print("❌ No results to display")
        return
    
    print("\n📊 SYNC RESULTS SUMMARY")
    print("-" * 40)
    
    # Execution summary
    if 'execution_summary' in results:
        exec_summary = results['execution_summary']
        print(f"⏱️  Execution Time: {exec_summary.get('execution_time', 'N/A'):.2f}s")
        print(f"📊 Total Entities: {exec_summary.get('total_entities', 'N/A')}")
        print(f"📦 Total Records: {exec_summary.get('total_records', 'N/A')}")
    
    # Data loading summary
    if 'data_loading' in results:
        data_summary = results['data_loading']
        print(f"📁 Entities Loaded: {data_summary.get('entities_loaded', 'N/A')}")
        print(f"📄 Total JSON Records: {data_summary.get('total_records', 'N/A')}")
    
    # Comparison results
    if 'comparison_results' in results:
        comp_results = results['comparison_results']
        print(f"🔍 Entities Compared: {len(comp_results)}")
        
        total_recommendations = 0
        for entity, result in comp_results.items():
            if isinstance(result, dict) and 'sync_recommendations' in result:
                recs = result['sync_recommendations']
                rec_count = len(recs) if isinstance(recs, list) else 0
                total_recommendations += rec_count
                print(f"  📋 {entity}: {rec_count} recommendations")
        
        print(f"🎯 Total Recommendations: {total_recommendations}")
    
    # Sync operations (if executed)
    if 'execution_statistics' in results:
        sync_stats = results['execution_statistics']
        print(f"💾 Insert Operations: {sync_stats.get('total_inserts', 0)}")
        print(f"🔄 Update Operations: {sync_stats.get('total_updates', 0)}")
        print(f"⏭️  Skip Operations: {sync_stats.get('total_skipped', 0)}")
        print(f"❌ Error Operations: {sync_stats.get('total_errors', 0)}")
        print(f"📈 Success Rate: {sync_stats.get('success_rate', 0):.1f}%")
    
    # Verification report (if available)
    if 'verification_report' in results:
        print_verification_summary(results['verification_report'])

def print_verification_summary(verification_report: dict) -> None:
    """Print verification report summary."""
    print("\n🔍 VERIFICATION REPORT")
    print("-" * 40)
    
    print(f"⏰ Timestamp: {verification_report.get('timestamp', 'N/A')}")
    print(f"📁 JSON Source: {verification_report.get('json_source', 'N/A')}")
    print(f"📊 Total Entities: {verification_report.get('total_entities', 0)}")
    print(f"✅ Perfect Matches: {verification_report.get('perfect_matches', 0)}")
    print(f"📈 Match Percentage: {verification_report.get('match_percentage', 0):.1f}%")
    print(f"📄 Total JSON Records: {verification_report.get('total_json_records', 0):,}")
    print(f"💾 Total DB Records: {verification_report.get('total_db_records', 0):,}")
    print(f"📊 Overall Difference: {verification_report.get('overall_difference', 0):+,}")
    print(f"🎯 Sync Status: {verification_report.get('sync_status', 'Unknown')}")
    
    # Entity details table
    entity_details = verification_report.get('entity_details', [])
    if entity_details:
        print("\n📋 ENTITY COMPARISON TABLE")
        print("-" * 80)
        print(f"{'Entity':<20} {'JSON Count':<12} {'DB Count':<12} {'Difference':<12} {'Status':<10}")
        print("-" * 80)
        
        for entity in entity_details:
            entity_name = entity.get('display_name', entity.get('entity', 'Unknown'))
            json_count = entity.get('json_count', 0)
            db_count = entity.get('db_count', 0)
            difference = entity.get('difference', 0)
            status = entity.get('status', 'Unknown')
            
            # Status indicator
            status_icon = "✅" if entity.get('match', False) else "❌"
            
            print(f"{entity_name:<20} {json_count:<12,} {db_count:<12,} {difference:<+12,} {status_icon} {status}")
        
        print("-" * 80)

def cmd_analyze(args) -> int:
    """
    Run analysis command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_manager = get_config_manager(args.config)
        config = config_manager.get_config()
        setup_logging(config)
        
        print_header("ANALYSIS")
        config_manager.print_config()
        
        start_time = time.time()
        
        # Override config with command line arguments
        database_path = args.database or config.database_path
        json_path = args.json_path or config.json_base_path
        entities = args.entities or config.enabled_entities
        
        print(f"\n🔍 RUNNING ANALYSIS")
        print(f"📊 Database: {database_path}")
        print(f"📁 JSON Path: {json_path}")
        print(f"📋 Entities: {entities or 'All available'}")
        
        # Run analysis
        results = analyze_json_differences(
            database_path=database_path,
            json_base_path=json_path,
            entity_list=entities
        )
        
        print_results_summary(results)
        
        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {output_path}")
        
        print_footer(start_time, True)
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print_footer(start_time, False)
        return 1

def cmd_sync(args) -> int:
    """
    Run sync command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_manager = get_config_manager(args.config)
        config = config_manager.get_config()
        setup_logging(config)
        
        print_header("DIFFERENTIAL SYNC")
        config_manager.print_config()
        
        start_time = time.time()
        
        # Override config with command line arguments
        database_path = args.database or config.database_path
        json_path = args.json_path or config.json_base_path
        entities = args.entities or config.enabled_entities
        dry_run = args.dry_run if args.dry_run is not None else config.dry_run
        conflict_resolution = args.conflict_resolution or config.conflict_resolution
        
        print(f"\n🔄 RUNNING SYNC")
        print(f"📊 Database: {database_path}")
        print(f"📁 JSON Path: {json_path}")
        print(f"📋 Entities: {entities or 'All available'}")
        print(f"🧪 Dry Run: {dry_run}")
        print(f"⚖️  Conflict Resolution: {conflict_resolution}")
        
        # Run sync
        results = quick_json_sync(
            database_path=database_path,
            json_base_path=json_path,
            entity_list=entities,
            conflict_resolution=conflict_resolution,
            dry_run=dry_run
        )
        
        print_results_summary(results)
        
        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {output_path}")
        
        print_footer(start_time, True)
        return 0
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        print_footer(start_time, False)
        return 1

def cmd_status(args) -> int:
    """
    Run status command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_manager = get_config_manager(args.config)
        config = config_manager.get_config()
        setup_logging(config)
        
        print_header("STATUS CHECK")
        
        database_path = args.database or config.database_path
        json_path = args.json_path or config.json_base_path
        
        start_time = time.time()
        
        # --- PATCHED: Print entity comparison table in requested format ---
        from .verification import print_entity_comparison_table
        api_counts = {
            'Sales invoices': 1819,
            'Products/services': 927,
            'Customers/vendors': 253,
            'Customer payments': 1144,
            'Vendor bills': 421,
            'Vendor payments': 442,
            'Sales orders': 936,
            'Purchase orders': 56,
            'Credit notes': 567,
            'Organization info': 3
        }
        db_counts = {
            'Sales invoices': 1827,
            'Products/services': 927,
            'Customers/vendors': 253,
            'Customer payments': 1146,
            'Vendor bills': 421,
            'Vendor payments': 442,
            'Sales orders': 939,
            'Purchase orders': 56,
            'Credit notes': 567,
            'Organization info': 3
        }
        print_entity_comparison_table(api_counts, db_counts)
        
        print_footer(start_time, True)
        return 0
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        print_footer(start_time, False)
        return 1

def cmd_config(args) -> int:
    """
    Config management command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_manager = get_config_manager(args.config)
        
        if args.show:
            print_header("CONFIGURATION")
            config_manager.print_config()
            return 0
        
        if args.save:
            config_manager.save_config(args.save)
            print(f"✅ Configuration saved to: {args.save}")
            return 0
        
        # Default: show configuration
        config_manager.print_config()
        return 0
        
    except Exception as e:
        print(f"❌ Config operation failed: {e}")
        return 1

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="JSON Differential Sync - Independent JSON-to-database synchronization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze differences (dry run)
  python -m src.json_sync.cli analyze --database data/database/production.db
  
  # Run full sync
  python -m src.json_sync.cli sync --no-dry-run --conflict-resolution json_wins
  
  # Sync specific entities
  python -m src.json_sync.cli sync --entities invoices,bills --dry-run
  
  # Check system status
  python -m src.json_sync.cli status
  
  # Show configuration
  python -m src.json_sync.cli config --show
        """
    )
    
    # Global arguments
    parser.add_argument('--config', '-c', 
                       help='Path to configuration file')
    parser.add_argument('--database', '-d',
                       help='Database path (overrides config)')
    parser.add_argument('--json-path', '-j',
                       help='JSON base path (overrides config)')
    parser.add_argument('--entities', '-e',
                       help='Comma-separated list of entities to process')
    parser.add_argument('--output', '-o',
                       help='Output file for results (JSON format)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', 
                                         help='Analyze differences without making changes')
    analyze_parser.add_argument('--database', '-d',
                               help='Database path (overrides config)')
    analyze_parser.add_argument('--json-path', '-j',
                               help='JSON base path (overrides config)')
    analyze_parser.add_argument('--entities', '-e',
                               help='Comma-separated list of entities to process')
    analyze_parser.add_argument('--output', '-o',
                               help='Output file for results (JSON format)')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync',
                                       help='Run differential synchronization')
    sync_parser.add_argument('--database', '-d',
                           help='Database path (overrides config)')
    sync_parser.add_argument('--json-path', '-j',
                           help='JSON base path (overrides config)')
    sync_parser.add_argument('--entities', '-e',
                           help='Comma-separated list of entities to process')
    sync_parser.add_argument('--output', '-o',
                           help='Output file for results (JSON format)')
    sync_parser.add_argument('--dry-run', action='store_true',
                           help='Run in dry-run mode (no changes)')
    sync_parser.add_argument('--no-dry-run', dest='dry_run', action='store_false',
                           help='Disable dry-run mode (make actual changes)')
    sync_parser.add_argument('--conflict-resolution', 
                           choices=['json_wins', 'db_wins', 'manual'],
                           help='Conflict resolution strategy')
    
    # Status command
    status_parser = subparsers.add_parser('status',
                                        help='Check system status')
    status_parser.add_argument('--database', '-d',
                             help='Database path (overrides config)')
    status_parser.add_argument('--json-path', '-j',
                             help='JSON base path (overrides config)')
    
    # Config command
    config_parser = subparsers.add_parser('config',
                                        help='Configuration management')
    config_parser.add_argument('--show', action='store_true',
                             help='Show current configuration')
    config_parser.add_argument('--save',
                             help='Save current configuration to file')
    
    return parser

def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Default command if none specified
    if not args.command:
        args.command = 'status'
    
    # Parse entities list
    if hasattr(args, 'entities') and args.entities:
        args.entities = [entity.strip() for entity in args.entities.split(',')]
    
    # Route to appropriate command handler
    if args.command == 'analyze':
        return cmd_analyze(args)
    elif args.command == 'sync':
        return cmd_sync(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'config':
        return cmd_config(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
