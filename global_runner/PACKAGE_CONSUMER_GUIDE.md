# Global Zoho Data Sync - Package Consumer Guide

This guide explains how to use the Global Zoho Data Sync package both as a standalone tool and when integrating it with other systems.

## Quick Start

### Interactive Menu Usage
```bash
cd global_runner
python main_zoho_data_sync.py
```

The interactive menu provides:
1. **Run Full Sync Pipeline** - Complete API → JSON2DB → Verification workflow
2. **Check Database Freshness** - Analyze data currency and completeness 
3. **View System Status** - Package availability and database status
4. **Help** - Detailed usage instructions
5. **Exit** - Close the application

### Programmatic Usage

#### Basic Runner Operations
```python
from global_runner.runner_zoho_data_sync import GlobalSyncRunner

# Initialize with default configuration
runner = GlobalSyncRunner()

# Check database freshness
freshness_result = runner.check_database_freshness()
print(f"Overall status: {freshness_result['overall_status']}")
print(f"Fresh tables: {freshness_result['fresh_tables']}")
print(f"Stale tables: {freshness_result['stale_tables']}")

# Run full sync pipeline
sync_result = runner.run_full_sync(cutoff_days=30)
if sync_result['success']:
    print("Sync completed successfully!")
    print(f"Processing time: {sync_result['total_processing_time']:.1f} seconds")
else:
    print(f"Sync failed: {sync_result.get('error', 'Unknown error')}")

# Get system status
status = runner.get_system_status()
print(f"Database has {status['database_status']['table_count']} tables")
```

#### Custom Configuration
```python
from global_runner.runner_zoho_data_sync import GlobalSyncRunner

# Using custom config file
runner = GlobalSyncRunner(config_file="/path/to/config.json")

# Disable logging
runner = GlobalSyncRunner(enable_logging=False)
```

## Configuration Management

### Configuration File Structure
Create `global_sync_config.json` in the package directory:

```json
{
    "database": {
        "path": "../data/json_sync.db"
    },
    "packages": {
        "api_sync": {
            "enabled": true,
            "path": "../api_sync",
            "runner_module": "runner_api_sync",
            "config_path": "../api_sync/config.json"
        },
        "json2db_sync": {
            "enabled": true,
            "path": "../json2db_sync",
            "runner_module": "runner_json2db_sync",
            "config_path": "../json2db_sync/config.json"
        },
        "csv_db_rebuild": {
            "enabled": true,
            "path": "../csv_db_rebuild",
            "runner_module": "runner_csv_db_rebuild",
            "csv_data_path": "../data/csv"
        }
    },
    "sync_pipeline": {
        "default_cutoff_days": 30,
        "freshness_threshold_days": 1,
        "enable_duplicate_prevention": true
    },
    "freshness_monitoring": {
        "tables_to_check": [
            "invoices", "bills", "contacts", "items", 
            "payments", "expenses", "purchase_orders"
        ],
        "date_column_mapping": {
            "invoices": "invoice_date",
            "bills": "bill_date",
            "contacts": "last_modified_time",
            "items": "last_modified_time",
            "payments": "payment_date",
            "expenses": "expense_date",
            "purchase_orders": "order_date"
        }
    },
    "logging": {
        "log_dir": "../logs",
        "log_level": "INFO",
        "max_log_files": 10
    },
    "ui": {
        "use_colors": true,
        "show_detailed_output": true,
        "auto_freshness_check_on_startup": true
    }
}
```

### Environment Variable Override
Override any configuration using environment variables with dot notation:

```bash
# Database configuration
export GLOBAL_SYNC_DATABASE_PATH="/custom/path/database.db"

# Pipeline settings
export GLOBAL_SYNC_SYNC_PIPELINE_DEFAULT_CUTOFF_DAYS=14
export GLOBAL_SYNC_SYNC_PIPELINE_FRESHNESS_THRESHOLD_DAYS=2

# UI settings
export GLOBAL_SYNC_UI_USE_COLORS=false
export GLOBAL_SYNC_UI_SHOW_DETAILED_OUTPUT=false

# Package enablement
export GLOBAL_SYNC_PACKAGES_API_SYNC_ENABLED=false
```

## Data Access Patterns

### Freshness Analysis Results
```python
freshness_result = runner.check_database_freshness()

# Result structure:
{
    "success": true,
    "check_timestamp": "2024-01-15T10:30:00",
    "threshold_days": 1,
    "cutoff_date": "2024-01-14T10:30:00",
    "tables_checked": 7,
    "fresh_tables": 5,
    "stale_tables": 2,
    "overall_status": "stale",  # "fresh", "stale", "empty", "unknown"
    "table_details": {
        "invoices": {
            "status": "fresh",      # "fresh", "stale", "empty", "missing", etc.
            "record_count": 1250,
            "latest_date": "2024-01-15T09:15:00",
            "days_old": 0,
            "date_column": "invoice_date"
        },
        "bills": {
            "status": "stale",
            "record_count": 890,
            "latest_date": "2024-01-12T14:30:00",
            "days_old": 3,
            "date_column": "bill_date"
        }
    }
}
```

### Sync Pipeline Results
```python
sync_result = runner.run_full_sync(cutoff_days=30)

# Result structure:
{
    "success": true,
    "start_time": "2024-01-15T10:00:00",
    "end_time": "2024-01-15T10:15:00",
    "total_processing_time": 900.5,
    "cutoff_days": 30,
    "stages_completed": ["api_sync", "json2db_sync", "freshness_check"],
    "stages_failed": [],
    "api_sync_result": {
        "success": true,
        "message": "API sync completed",
        "records_fetched": 5000
    },
    "json2db_sync_result": {
        "success": true,
        "tables_processed": 7,
        "records_inserted": 4890,
        "records_updated": 110
    },
    "freshness_check_result": {
        # Same structure as freshness analysis above
    }
}
```

### System Status Information
```python
status = runner.get_system_status()

# Result structure:
{
    "timestamp": "2024-01-15T10:30:00",
    "database_status": {
        "path": "../data/json_sync.db",
        "exists": true,
        "accessible": true,
        "size_mb": 245.8,
        "table_count": 15
    },
    "package_status": {
        "api_sync": {
            "enabled": true,
            "path_exists": true,
            "runner_available": true
        },
        "json2db_sync": {
            "enabled": true,
            "path_exists": true,
            "runner_available": true
        },
        "csv_db_rebuild": {
            "enabled": false,
            "path_exists": true,
            "runner_available": true
        }
    },
    "configuration": {
        "cutoff_days": 30,
        "freshness_threshold": 1,
        "logging_enabled": true
    }
}
```

## Integration Examples

### Scheduled Automation
```python
#!/usr/bin/env python3
"""
Automated sync script for cron/task scheduler
"""
import sys
from global_runner.runner_zoho_data_sync import GlobalSyncRunner

def automated_sync():
    runner = GlobalSyncRunner(enable_logging=True)
    
    # Check freshness first
    freshness = runner.check_database_freshness()
    
    # Only run sync if data is stale
    if freshness.get('overall_status') == 'stale':
        print("Data is stale, running sync...")
        result = runner.run_full_sync()
        
        if result['success']:
            print("Sync completed successfully")
            return 0
        else:
            print(f"Sync failed: {result.get('error')}")
            return 1
    else:
        print("Data is fresh, skipping sync")
        return 0

if __name__ == "__main__":
    sys.exit(automated_sync())
```

### Web API Integration
```python
from flask import Flask, jsonify
from global_runner.runner_zoho_data_sync import GlobalSyncRunner

app = Flask(__name__)
runner = GlobalSyncRunner()

@app.route('/api/freshness')
def get_freshness():
    result = runner.check_database_freshness()
    return jsonify(result)

@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    cutoff_days = request.json.get('cutoff_days', 30)
    result = runner.run_full_sync(cutoff_days=cutoff_days)
    return jsonify(result)

@app.route('/api/status')
def get_status():
    result = runner.get_system_status()
    return jsonify(result)
```

### Custom Wrapper Integration
```python
from global_runner.runner_zoho_data_sync import GlobalSyncRunner
from global_runner.config import GlobalSyncConfig

class CustomSyncManager:
    def __init__(self, custom_config):
        self.config = GlobalSyncConfig()
        self.config.update(custom_config)
        self.runner = GlobalSyncRunner()
    
    def sync_if_needed(self, max_age_hours=24):
        freshness = self.runner.check_database_freshness()
        
        # Custom logic for determining sync need
        needs_sync = any(
            details.get('days_old', 0) * 24 > max_age_hours
            for details in freshness.get('table_details', {}).values()
        )
        
        if needs_sync:
            return self.runner.run_full_sync()
        
        return {"success": True, "message": "No sync needed"}
```

## Command Line Interface

### Basic Usage
```bash
# Run with default configuration
python main_zoho_data_sync.py

# Use custom configuration file
python main_zoho_data_sync.py /path/to/config.json

# Set environment variables for one-time override
GLOBAL_SYNC_UI_USE_COLORS=false python main_zoho_data_sync.py
```

### Menu Navigation
- Use numeric keys (1-5) to select menu options
- Press Enter to confirm selections
- Use Ctrl+C to cancel operations or exit
- Press Enter after each operation to return to main menu

## Troubleshooting

### Common Integration Issues

#### Package Import Errors
```python
# If packages aren't found, check paths in configuration
runner = GlobalSyncRunner()
status = runner.get_system_status()
print(status['package_status'])  # Check which packages are available
```

#### Database Connection Issues
```python
# Verify database accessibility
import sqlite3
from pathlib import Path

db_path = runner.config.get_database_path()
if Path(db_path).exists():
    try:
        conn = sqlite3.connect(db_path)
        print("Database accessible")
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
else:
    print("Database file not found")
```

#### Configuration Problems
```python
# Debug configuration loading
from global_runner.config import GlobalSyncConfig

config = GlobalSyncConfig()
print("Database path:", config.get_database_path())
print("Enabled packages:", [
    name for name in ['api_sync', 'json2db_sync', 'csv_db_rebuild']
    if config.is_package_enabled(name)
])
```

### Performance Considerations

#### Large Datasets
- Use appropriate cutoff_days to limit data volume
- Monitor memory usage during sync operations
- Consider splitting sync operations for very large datasets

#### Frequent Sync Operations
- Use freshness checking to avoid unnecessary syncs
- Implement custom thresholds based on data criticality
- Cache runner instances for repeated operations

## Support and Resources

### Debug Information
Enable detailed logging for troubleshooting:
```python
runner = GlobalSyncRunner(enable_logging=True)
# Check log files in ../logs/ directory
```

### Configuration Validation
Use the system status check to validate configuration:
```python
status = runner.get_system_status()
if not status['database_status']['accessible']:
    print("Database configuration issue")

for package, details in status['package_status'].items():
    if not details['runner_available']:
        print(f"Package {package} not properly configured")
```

### Error Handling Best Practices
```python
try:
    result = runner.run_full_sync()
    if not result['success']:
        # Handle business logic errors
        print(f"Sync failed: {result.get('error')}")
        # Check individual stage results
        for stage in result.get('stages_failed', []):
            print(f"Failed stage: {stage}")
except Exception as e:
    # Handle system errors
    print(f"System error: {e}")
```
