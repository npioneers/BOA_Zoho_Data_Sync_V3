"""
JSON Differential Sync - Convenience Functions

High-level convenience functions for common JSON sync operations.
Provides simple interface for notebooks and scripts.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import sqlite3

from .config import get_config
from .orchestrator import JsonDifferentialSyncOrchestrator
from .json_loader import JsonDataLoader
from .json_comparator import JsonDatabaseComparator
from .json_sync_engine import JsonSyncEngine

logger = logging.getLogger(__name__)

def quick_json_sync(database_path: str, 
                   json_base_path: Optional[str] = None,
                   entity_list: Optional[List[str]] = None,
                   conflict_resolution: str = 'json_wins',
                   dry_run: bool = False) -> Dict[str, Any]:
    """
    Perform a complete JSON differential sync in one function call.
    
    Args:
        database_path: Path to SQLite database
        json_base_path: Base path to JSON data directory (optional)
        entity_list: List of entities to sync (optional, defaults to all)
        conflict_resolution: How to resolve conflicts ('json_wins', 'db_wins', 'manual')
        dry_run: If True, only analyzes differences without making changes
        
    Returns:
        Complete sync results dictionary
        
    Example:
        >>> results = quick_json_sync('data/database/production.db', dry_run=True)
        >>> print(f"Found {results['comparison_results']['summary']['total_missing_in_database']} records to insert")
    """
    logger.info(f"Starting quick JSON sync: database={database_path}, dry_run={dry_run}")
    
    orchestrator = JsonDifferentialSyncOrchestrator(database_path, json_base_path)
    results = orchestrator.execute_full_differential_sync(
        entity_list=entity_list,
        conflict_resolution=conflict_resolution,
        dry_run=dry_run
    )
    
    logger.info("Quick JSON sync completed")
    return results

def analyze_json_differences(database_path: str,
                           json_base_path: Optional[str] = None,
                           entity_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze differences between JSON and database without making changes.
    
    Args:
        database_path: Path to SQLite database
        json_base_path: Base path to JSON data directory (optional)
        entity_list: List of entities to analyze (optional, defaults to all)
        
    Returns:
        Analysis results with recommendations but no database changes
    """
    return quick_json_sync(
        database_path=database_path,
        json_base_path=json_base_path,
        entity_list=entity_list,
        dry_run=True
    )

def sync_specific_entities(database_path: str,
                          entity_names: List[str],
                          json_base_path: Optional[str] = None,
                          conflict_resolution: str = 'json_wins') -> Dict[str, Any]:
    """
    Sync specific entities from JSON to database.
    
    Args:
        database_path: Path to SQLite database
        entity_names: List of specific entity names to sync
        json_base_path: Base path to JSON data directory (optional)
        conflict_resolution: How to resolve conflicts
        
    Returns:
        Sync results for specified entities
        
    Example:
        >>> results = sync_specific_entities('data/database/production.db', ['bills', 'invoices'])
        >>> print(f"Synced {results['execution_statistics']['total_inserts']} new records")
    """
    return quick_json_sync(
        database_path=database_path,
        json_base_path=json_base_path,
        entity_list=entity_names,
        conflict_resolution=conflict_resolution,
        dry_run=False
    )

def load_latest_json_data(json_base_path: Optional[str] = None,
                         entity_list: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load the latest JSON data for analysis.
    
    Args:
        json_base_path: Base path to JSON data directory (optional)
        entity_list: List of entities to load (optional, defaults to all)
        
    Returns:
        Dictionary mapping entity names to their JSON records
        
    Example:
        >>> data = load_latest_json_data()
        >>> print(f"Loaded {len(data['bills'])} bills from latest JSON export")
    """
    loader = JsonDataLoader(json_base_path)
    return loader.load_all_entities(entity_list)

def compare_json_with_database(database_path: str,
                              json_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Compare loaded JSON data with database records.
    
    Args:
        database_path: Path to SQLite database
        json_data: JSON data dictionary from load_latest_json_data()
        
    Returns:
        Comparison results with detailed differences
        
    Example:
        >>> json_data = load_latest_json_data()
        >>> comparison = compare_json_with_database('data/database/production.db', json_data)
        >>> summary = comparison['summary']
    """
    comparator = JsonDatabaseComparator(database_path)
    results = comparator.compare_multiple_entities(json_data)
    
    # Generate summary report
    return comparator.get_summary_report()

def get_sync_status(database_path: Optional[str] = None,
                   json_base_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive status of the JSON sync system.
    
    Args:
        database_path: Path to database (uses config default if None)
        json_base_path: Path to JSON data (uses config default if None)
        
    Returns:
        Dictionary with system status information
    """
    config = get_config()
    
    # Use config defaults if not provided
    db_path = database_path or config.database_path
    json_path = json_base_path or config.json_base_path
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'database_path': db_path,
        'json_base_path': json_path,
        'database_available': False,
        'json_data_available': False,
        'modules_working': False,
        'json_directories': [],
        'database_entities': {},
        'configuration': {
            'conflict_resolution': config.conflict_resolution,
            'dry_run': config.dry_run,
            'enabled_entities': config.enabled_entities
        }
    }
    
    try:
        # Check database availability
        db_path_obj = Path(db_path)
        if db_path_obj.exists():
            status['database_available'] = True
            
            # Get database entity counts
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get record counts for each table
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        status['database_entities'][table] = count
                    except:
                        status['database_entities'][table] = 'Error'
                
                conn.close()
                
            except Exception as e:
                logger.warning(f"Could not read database entities: {e}")
        
        # Check JSON data availability
        json_path_obj = Path(json_path)
        if json_path_obj.exists():
            status['json_data_available'] = True
            
            # Get JSON directories
            json_dirs = [d.name for d in json_path_obj.iterdir() if d.is_dir()]
            status['json_directories'] = sorted(json_dirs, reverse=True)
        
        # Test module functionality
        try:
            loader = JsonDataLoader()
            comparator = JsonDatabaseComparator(db_path)
            status['modules_working'] = True
        except Exception as e:
            logger.warning(f"Module test failed: {e}")
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        status['error'] = str(e)
    
    return status

def run_incremental_sync(database_path: str,
                        json_base_path: Optional[str] = None,
                        entity_list: Optional[List[str]] = None,
                        conflict_resolution: str = "json_wins",
                        dry_run: bool = False) -> Dict[str, Any]:
    """
    Run incremental JSON sync with comprehensive cockpit interface.
    
    This function provides a cockpit-style interface for running incremental
    JSON synchronization with detailed progress reporting and configuration.
    
    Args:
        database_path: Path to SQLite database
        json_base_path: Base path to JSON data directory. If None, auto-discovers latest.
        entity_list: Specific entities to sync. If None, syncs all available.
        conflict_resolution: Strategy for resolving conflicts ("json_wins", "db_wins", "manual")
        dry_run: If True, analyze only without making changes
        
    Returns:
        Comprehensive results dictionary with sync statistics and recommendations
    """
    logger.info(f"Starting incremental JSON sync: dry_run={dry_run}")
    
    # Initialize orchestrator
    orchestrator = JsonDifferentialSyncOrchestrator(database_path, json_base_path)
    
    # Execute sync workflow
    results = orchestrator.execute_full_differential_sync(
        entity_list=entity_list,
        conflict_resolution=conflict_resolution,
        dry_run=dry_run
    )
    
    logger.info("Incremental JSON sync completed")
    return results


def get_sync_cockpit_status(database_path: str,
                           json_base_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive status for JSON sync cockpit.
    
    Provides system status, data availability, and readiness for sync operations.
    
    Args:
        database_path: Path to SQLite database
        json_base_path: Base path to JSON data directory
        
    Returns:
        Status dictionary with system health and data availability
    """
    from pathlib import Path
    import sqlite3
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'system_status': 'checking',
        'database': {},
        'json_data': {},
        'sync_readiness': {},
        'recommendations': []
    }
    
    # Check database status
    db_path = Path(database_path)
    if db_path.exists():
        try:
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get record counts
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                
                status['database'] = {
                    'exists': True,
                    'path': str(db_path.absolute()),
                    'tables': len(tables),
                    'table_names': tables,
                    'record_counts': table_counts,
                    'total_records': sum(table_counts.values())
                }
        except Exception as e:
            status['database'] = {
                'exists': True,
                'path': str(db_path.absolute()),
                'error': str(e)
            }
    else:
        status['database'] = {
            'exists': False,
            'path': str(db_path.absolute())
        }
        status['recommendations'].append("Database not found - check path configuration")
    
    # Check JSON data status
    try:
        loader = JsonDataLoader(json_base_path)
        latest_dir = loader.find_latest_json_directory()
        
        if latest_dir:
            loaded_data = loader.load_all_entities()
            
            status['json_data'] = {
                'latest_directory': str(latest_dir),
                'entities_available': len(loaded_data),
                'entity_names': list(loaded_data.keys()),
                'record_counts': {entity: len(records) for entity, records in loaded_data.items()},
                'total_records': sum(len(records) for records in loaded_data.values()),
                'load_errors': loader.load_errors
            }
        else:
            status['json_data'] = {
                'available': False,
                'error': 'No JSON directories found'
            }
            status['recommendations'].append("No JSON data available - check JSON base path")
            
    except Exception as e:
        status['json_data'] = {
            'available': False,
            'error': str(e)
        }
        status['recommendations'].append(f"JSON loading error: {e}")
    
    # Determine sync readiness
    db_ready = status['database'].get('exists', False)
    json_ready = status['json_data'].get('entities_available', 0) > 0
    
    if db_ready and json_ready:
        status['system_status'] = 'ready'
        status['sync_readiness'] = {
            'ready': True,
            'database_ready': True,
            'json_ready': json_ready,
            'estimated_sync_entities': status['json_data']['entities_available']
        }
    else:
        status['system_status'] = 'not_ready'
        status['sync_readiness'] = {
            'ready': False,
            'database_ready': db_ready,
            'json_ready': json_ready
        }
        
        if not db_ready:
            status['recommendations'].append("Database not accessible")
        if not json_ready:
            status['recommendations'].append("JSON data not available")
    
    return status


def print_cockpit_banner():
    """Print a stylized banner for the JSON sync cockpit."""
    banner = """
🎛️ ═══════════════════════════════════════════════════════════════════════════════
                         JSON DIFFERENTIAL SYNC COCKPIT
                              Independent JSON-to-Database Sync
═══════════════════════════════════════════════════════════════════════════════ 🎛️
"""
    print(banner)


def format_sync_results(results: Dict[str, Any]) -> str:
    """Format sync results for cockpit display."""
    if not results:
        return "❌ No results to display"
    
    output = []
    output.append("📊 SYNC RESULTS SUMMARY")
    output.append("=" * 50)
    
    # Execution summary
    if 'execution_summary' in results:
        exec_summary = results['execution_summary']
        output.append(f"⏱️  Execution Time: {exec_summary.get('execution_time', 0):.2f}s")
        output.append(f"🎯 Operation Mode: {'Dry Run' if exec_summary.get('dry_run', False) else 'Live Sync'}")
        output.append(f"📋 Entities Processed: {exec_summary.get('entities_processed', 0)}")
    
    # Data loading summary
    if 'data_loading' in results:
        data_loading = results['data_loading']
        output.append(f"\n📂 DATA LOADING:")
        output.append(f"  📥 Entities Loaded: {data_loading.get('entities_loaded', 0)}")
        output.append(f"  📊 Total Records: {data_loading.get('total_records', 0)}")
    
    # Comparison results
    if 'comparison_results' in results and results['comparison_results']:
        output.append(f"\n🔍 COMPARISON RESULTS:")
        for entity, comparison in results['comparison_results'].items():
            if isinstance(comparison, dict) and 'sync_recommendations' in comparison:
                recs = comparison['sync_recommendations']
                output.append(f"  📋 {entity}: {len(recs)} recommendations")
    
    # Sync statistics
    if 'sync_statistics' in results:
        stats = results['sync_statistics']
        output.append(f"\n📈 SYNC STATISTICS:")
        output.append(f"  ➕ Inserts: {stats.get('total_inserts', 0)}")
        output.append(f"  🔄 Updates: {stats.get('total_updates', 0)}")
        output.append(f"  ⏭️  Skipped: {stats.get('total_skipped', 0)}")
    
    return "\n".join(output)

def create_json_sync_config_template(output_path: str) -> None:
    """
    Create a template configuration file for JSON sync operations.
    
    Args:
        output_path: Path where to save the configuration template
    """
    from .config import JsonSyncConfigManager
    
    # Create a config manager with defaults
    config_manager = JsonSyncConfigManager()
    
    # Save the default configuration as template
    config_manager.save_config(output_path)
    
    print(f"✅ Configuration template created: {output_path}")
    print("Edit this file to customize your JSON sync settings.")

# Quick access to main classes for advanced usage
def get_orchestrator(database_path: str, json_base_path: Optional[str] = None) -> JsonDifferentialSyncOrchestrator:
    """Get orchestrator instance for advanced operations."""
    return JsonDifferentialSyncOrchestrator(database_path, json_base_path)

def get_loader(json_base_path: Optional[str] = None) -> JsonDataLoader:
    """Get JSON loader instance for custom loading operations."""
    return JsonDataLoader(json_base_path)

def get_comparator(database_path: str) -> JsonDatabaseComparator:
    """Get comparator instance for custom comparison operations."""
    return JsonDatabaseComparator(database_path)

def get_sync_engine(database_path: str) -> JsonSyncEngine:
    """Get sync engine instance for custom sync operations."""
    return JsonSyncEngine(database_path)
