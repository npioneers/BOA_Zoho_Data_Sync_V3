"""
CSV Database Rebuild Package
Provides tools for rebuilding SQLite databases from Zoho CSV exports
"""

# Import main classes for external access
from .runner_csv_db_rebuild import CSVDatabaseRebuildRunner
from .main_csv_db_rebuild import CSVDatabaseRebuildMain

# Import legacy class for backward compatibility
try:
    from .simple_populator import SimpleCSVPopulator
except ImportError:
    # Handle case where legacy script might not be available
    SimpleCSVPopulator = None

# Package metadata
__version__ = "2.0"
__author__ = "Automated Operations Team"
__description__ = "CSV to Database Rebuild Tools"

# Define what gets imported with "from csv_db_rebuild import *"
__all__ = [
    "CSVDatabaseRebuildRunner",
    "CSVDatabaseRebuildMain", 
    "SimpleCSVPopulator"
]

# Package-level convenience functions
def create_runner(**kwargs):
    """
    Convenience function to create a configured runner instance.
    
    Args:
        **kwargs: Configuration parameters for CSVDatabaseRebuildRunner
        
    Returns:
        CSVDatabaseRebuildRunner: Configured runner instance
    """
    return CSVDatabaseRebuildRunner(**kwargs)

def run_interactive_menu():
    """
    Convenience function to start the interactive menu system.
    """
    app = CSVDatabaseRebuildMain()
    app.run()

def quick_populate_all(db_path=None, csv_dir=None, **kwargs):
    """
    Convenience function for quick population of all tables.
    
    Args:
        db_path: Optional database path override
        csv_dir: Optional CSV directory override
        **kwargs: Additional configuration parameters
        
    Returns:
        dict: Population results
    """
    config = {}
    if db_path:
        config['db_path'] = db_path
    if csv_dir:
        config['csv_dir'] = csv_dir
    config.update(kwargs)
    
    runner = CSVDatabaseRebuildRunner(**config)
    return runner.populate_all_tables()

# Package information for help systems
def get_package_info():
    """
    Get package information and available interfaces.
    
    Returns:
        dict: Package information including version, interfaces, and usage examples
    """
    return {
        "name": "csv_db_rebuild",
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "interfaces": {
            "interactive": "main_csv_db_rebuild.py - Menu-driven interface",
            "programmatic": "runner_csv_db_rebuild.py - API for integration",
            "legacy": "simple_populator.py - Backward compatibility"
        },
        "main_classes": {
            "CSVDatabaseRebuildRunner": "Pure business logic runner",
            "CSVDatabaseRebuildMain": "Interactive menu wrapper",
            "SimpleCSVPopulator": "Legacy populator class"
        },
        "quick_start": {
            "interactive": "from csv_db_rebuild import run_interactive_menu; run_interactive_menu()",
            "programmatic": "from csv_db_rebuild import create_runner; runner = create_runner(); result = runner.populate_all_tables()",
            "quick_populate": "from csv_db_rebuild import quick_populate_all; result = quick_populate_all()"
        }
    }
