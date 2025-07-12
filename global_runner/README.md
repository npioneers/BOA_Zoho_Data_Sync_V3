# Global Zoho Data Sync Package

A comprehensive orchestration system for managing Zoho data synchronization across multiple packages. This global runner coordinates `api_sync`, `json2db_sync`, and `csv_db_rebuild` packages to provide a complete data pipeline solution.

## Overview

The Global Zoho Data Sync package provides a unified interface for managing the complete Zoho data synchronization pipeline. It orchestrates three main components:

1. **API Sync** - Fetches latest data from Zoho APIs
2. **JSON2DB Sync** - Processes JSON data into structured database tables  
3. **Freshness Analysis** - Monitors data currency and provides sync recommendations

## Package Structure

```
global_runner/
├── config.py                    # Configuration management (GlobalSyncConfig)
├── runner_zoho_data_sync.py     # Pure business logic runner
├── main_zoho_data_sync.py       # User interface wrapper with menu
├── README.md                    # This file
├── PACKAGE_CONSUMER_GUIDE.md    # Usage guide for consumers
└── COPILOT_GLOBAL_PACKAGE_NOTES.md  # Development notes
```

## Core Components

### 1. GlobalSyncConfig (config.py)
- Centralized configuration management for all packages
- Database connection settings and package paths
- Freshness monitoring configuration
- UI and logging preferences
- Supports JSON configuration files and environment variables

### 2. GlobalSyncRunner (runner_zoho_data_sync.py)
- Pure business logic for orchestrating sync operations
- Database freshness analysis across multiple tables
- Full sync pipeline execution (API → JSON2DB → Verification)
- System status monitoring and package availability checks
- No user interaction - designed for programmatic access

### 3. GlobalSyncWrapper (main_zoho_data_sync.py)
- Interactive menu system for user operations
- User-friendly display of freshness status and sync results
- Formatted tables and status indicators
- Startup checks and auto-freshness analysis
- Menu options: Full Sync, Freshness Check, System Status, Help, Exit

## Key Features

### Database Freshness Monitoring
- Analyzes data freshness across configured tables
- Configurable freshness thresholds (default: 1 day)
- Intelligent date column detection
- Master data table recognition (items, contacts)
- Clear distinction between data dates and load timestamps

### Full Sync Pipeline
- Orchestrates complete API → JSON2DB → Verification workflow
- Configurable data cutoff periods (default: 30 days)
- Comprehensive error handling and progress tracking
- Detailed results reporting with stage-by-stage status

### System Status Monitoring
- Package availability and configuration validation
- Database connectivity and table analysis
- Configuration summary and recommendations
- Real-time status indicators

### User Interface
- Color-coded status messages (✓ ⚠ ✗ ℹ)
- Formatted tables for data display
- Interactive menu with input validation
- Detailed help system with configuration info
- Auto-startup freshness checks

## Configuration

### Default Configuration
The package includes sensible defaults for all settings:

```python
{
    "database": {
        "path": "../data/json_sync.db"
    },
    "packages": {
        "api_sync": {"enabled": true, "path": "../api_sync"},
        "json2db_sync": {"enabled": true, "path": "../json2db_sync"},
        "csv_db_rebuild": {"enabled": true, "path": "../csv_db_rebuild"}
    },
    "sync_pipeline": {
        "default_cutoff_days": 30,
        "freshness_threshold_days": 1
    },
    "ui": {
        "use_colors": true,
        "show_detailed_output": true,
        "auto_freshness_check_on_startup": true
    }
}
```

### Custom Configuration
Create a `global_sync_config.json` file to override defaults:

```json
{
    "database": {
        "path": "/custom/path/to/database.db"
    },
    "sync_pipeline": {
        "default_cutoff_days": 14,
        "freshness_threshold_days": 2
    },
    "freshness_monitoring": {
        "tables_to_check": ["invoices", "bills", "contacts", "items"],
        "date_column_mapping": {
            "invoices": "invoice_date",
            "bills": "bill_date"
        }
    }
}
```

### Environment Variables
Override any configuration using environment variables:

```bash
GLOBAL_SYNC_DATABASE_PATH="/path/to/database.db"
GLOBAL_SYNC_SYNC_PIPELINE_DEFAULT_CUTOFF_DAYS=14
GLOBAL_SYNC_UI_USE_COLORS=false
```

## Usage Examples

### Running the Interactive Menu
```bash
cd global_runner
python main_zoho_data_sync.py
```

### Using Custom Configuration
```bash
python main_zoho_data_sync.py /path/to/custom_config.json
```

### Programmatic Usage
```python
from global_runner.runner_zoho_data_sync import GlobalSyncRunner

# Initialize runner
runner = GlobalSyncRunner()

# Check freshness
freshness = runner.check_database_freshness()
print(f"Overall status: {freshness['overall_status']}")

# Run full sync
result = runner.run_full_sync(cutoff_days=14)
print(f"Sync successful: {result['success']}")
```

## Menu Options

1. **Run Full Sync Pipeline**
   - Executes API Sync → JSON2DB Sync → Freshness Check
   - Configurable cutoff days for data retrieval
   - Comprehensive progress tracking and results display

2. **Check Database Freshness**
   - Analyzes current data freshness across all monitored tables
   - Shows detailed table status with record counts and age
   - Provides sync recommendations based on data staleness

3. **View System Status**
   - Package availability and configuration validation
   - Database connectivity and size information
   - Configuration summary and current settings

4. **Help**
   - Detailed usage instructions and configuration info
   - Package location and status information
   - Menu option explanations

## Integration with Other Packages

### API Sync Integration
- Automatically detects and initializes API sync runner
- Passes configuration and parameters
- Handles API sync results and error reporting

### JSON2DB Sync Integration
- Loads JSON2DB configuration and initializes runner
- Manages session-based data processing
- Tracks sync progress and validates results

### CSV DB Rebuild Integration
- Optional integration for CSV data management
- Database and CSV path configuration
- Table management and verification

## Error Handling

### Graceful Degradation
- Continues operation even if individual packages are unavailable
- Clear error messages and status reporting
- Fallback mechanisms for missing configurations

### Comprehensive Logging
- Session-based log files with timestamps
- Multiple log levels (INFO, WARNING, ERROR)
- Both file and console output options

### User-Friendly Error Messages
- Clear status indicators for different error types
- Helpful suggestions for resolving common issues
- Non-technical language for user-facing messages

## Development Notes

### Architecture Pattern
- **Runner**: Pure business logic, no user interaction
- **Wrapper**: All user interface, menus, and display formatting
- **Config**: Centralized configuration with environment variable support

### Extension Points
- Package registration system for adding new sync packages
- Configurable freshness monitoring tables and date columns
- Pluggable display formatters and status indicators

### Testing Considerations
- Comprehensive unit tests for freshness analysis logic
- Integration tests for package orchestration
- User interface testing for menu and display components

## Support and Troubleshooting

### Common Issues
1. **Package Not Available**: Check package paths and runner module availability
2. **Database Connection**: Verify database path and permissions
3. **Configuration Errors**: Validate JSON syntax and required fields

### Debug Mode
Enable detailed logging by setting environment variable:
```bash
GLOBAL_SYNC_DEBUG=true python main_zoho_data_sync.py
```

### Log Files
Session logs are automatically created in `../logs/` directory with timestamp-based filenames for easy tracking and debugging.
