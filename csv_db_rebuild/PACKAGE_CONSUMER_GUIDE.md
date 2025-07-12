# CSV Database Rebuild Package - Consumer Guide

**Package:** `csv_db_rebuild`  
**Version:** 2.0  
**Updated:** July 12, 2025  
**Purpose:** Complete guide for using the CSV Database Rebuild package

## 📋 Overview

The `csv_db_rebuild` package provides robust tools for rebuilding SQLite databases from Zoho CSV exports. It offers multiple interfaces for different use cases:

- **Interactive Menu System** - For manual operations and testing
- **Programmatic API** - For integration with other systems
- **Legacy Scripts** - For backward compatibility

## 🎯 Target Users

### End Users (Manual Operations)
- Database administrators performing manual rebuilds
- Developers testing database operations
- Users needing interactive control and confirmation

### Developers (Programmatic Integration)
- Systems integrating database rebuild functionality
- Automated pipelines requiring database refresh
- Applications needing CSV-to-database synchronization

### Legacy System Maintainers
- Systems currently using simple_populator.py
- Batch scripts requiring minimal changes
- Existing automation workflows

## 🚀 Usage Methods

### Method 1: Interactive Menu System

#### Starting the Application
```powershell
# Navigate to the project directory
cd c:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3

# Run the interactive menu (auto-initializes on startup)
python csv_db_rebuild/main_csv_db_rebuild.py
```

**Note:** The system automatically initializes on startup, eliminating the need for manual initialization.

#### Menu Navigation
The interactive system provides (auto-initializes on startup):

1. **Clear and Populate All Tables** - Complete rebuild (clear all + populate from CSV)
2. **Populate All Tables (No Clear)** - Add data without clearing existing records
3. **Populate Single Table** - Rebuild specific table only
4. **Clear All Tables** - Remove all data from all tables
5. **Clear Single Table** - Remove data from specific table
6. **Verify Table Population** - Check table status and record counts
7. **Show System Status** - Display current configuration and status
8. **Configuration Settings** - Modify paths and settings
9. **Show Available Tables** - List all mapped tables

**Recommended**: Use option 1 (Clear and Populate All Tables) for complete database rebuilds.

#### Configuration Management
```
Configuration Settings Menu:
1. Change Database Path        (default: data/database/production.db)
2. Change CSV Directory       (default: data/csv/Nangsel Pioneers_Latest)
3. Change Log Directory       (default: logs)
4. Toggle Logging            (default: enabled)
5. Show Current Configuration
6. Reset to Defaults
```

### Method 2: Programmatic API

#### Basic Usage
```python
from csv_db_rebuild.runner_csv_db_rebuild import CSVDatabaseRebuildRunner

# Initialize with default settings
runner = CSVDatabaseRebuildRunner()

# Or initialize with custom settings
runner = CSVDatabaseRebuildRunner(
    db_path="custom/path/database.db",
    csv_dir="custom/csv/directory",
    enable_logging=True,
    log_dir="custom/logs"
)

# Method 1: Clear and populate all tables (recommended for full rebuild)
result = runner.clear_and_populate_all_tables()

# Method 2: Populate all tables (without clearing first)
result = runner.populate_all_tables()

# Check overall success
if result['overall_success_rate'] >= 95:
    print("Database rebuild successful!")
else:
    print(f"Issues detected: {result['failed_tables']}")
```

#### Advanced Operations

##### Single Table Operations
```python
# Populate specific table
result = runner.populate_single_table("csv_invoices")

if result['success']:
    print(f"Inserted {result['records']} records")
else:
    print(f"Failed: {result['error']}")

# Clear specific table
clear_result = runner.clear_table("csv_invoices")
print(f"Deleted {clear_result['rows_deleted']} records")
```

##### Custom Table Mappings
```python
custom_mappings = {
    "csv_custom_table": {"csv_file": "CustomData.csv"},
    "csv_invoices": {"csv_file": "Invoice.csv"}
}

runner = CSVDatabaseRebuildRunner(
    table_mappings=custom_mappings
)
```

##### Verification and Status
```python
# Verify single table
status = runner.verify_table_population("csv_invoices")
print(f"Table has {status['record_count']} records")

# Get overall system status
summary = runner.get_table_status_summary()
print(f"Population rate: {summary['population_rate']:.1f}%")
print(f"Total records: {summary['total_records']:,}")
```

#### Result Structure

##### populate_all_tables() Results
```python
{
    "tables_attempted": 9,
    "tables_successful": 9,
    "tables_failed": 0,
    "table_success_rate": 100.0,
    "total_csv_records": 31254,
    "total_records_inserted": 31254,
    "overall_success_rate": 100.0,
    "processing_time_seconds": 120.5,
    "failed_tables": [],
    "results": {
        "csv_invoices": {
            "success": True,
            "records": 6988,
            "csv_records": 6988,
            "error": None
        }
        # ... other tables
    }
}
```

##### populate_single_table() Results
```python
{
    "success": True,
    "records": 6988,
    "csv_records": 6988,
    "error": None
}
```

### Method 3: Legacy Script Compatibility

#### Direct Script Execution
```powershell
# Original simple populator (unchanged interface)
python csv_db_rebuild/simple_populator.py

# Schema comparison
python csv_db_rebuild/compare_schemas.py

# Schema verification
python csv_db_rebuild/verify_schema.py
```

#### Legacy Import Pattern
```python
# Existing code continues to work
import sys
sys.path.append('csv_db_rebuild')
from simple_populator import SimpleCSVPopulator

populator = SimpleCSVPopulator()
result = populator.populate_all_tables()
```

## ⚙️ Configuration Options

### Default Configuration
```python
{
    "db_path": "data/database/production.db",
    "csv_dir": "data/csv/Nangsel Pioneers_Latest",
    "log_dir": "logs",
    "enable_logging": True
}
```

### Environment-Specific Configurations

#### Development Environment
```python
runner = CSVDatabaseRebuildRunner(
    db_path="dev/database/test.db",
    csv_dir="dev/csv/test_data",
    log_dir="dev/logs"
)
```

#### Production Environment
```python
runner = CSVDatabaseRebuildRunner(
    db_path="prod/database/production.db",
    csv_dir="prod/csv/latest_export",
    log_dir="prod/logs"
)
```

#### Minimal Configuration (No Logging)
```python
runner = CSVDatabaseRebuildRunner(
    enable_logging=False
)
```

## 📊 Expected Results

### Performance Metrics
- **Processing Time**: ~2 minutes for 31K+ records
- **Success Rate**: 100% with default configuration
- **Database Size**: ~7.8 MB when fully populated
- **Memory Usage**: Minimal - processes tables sequentially

### Table Population Results

| Table Name | Expected Records | Processing Time | Success Rate |
|------------|------------------|-----------------|--------------|
| csv_invoices | ~7,000 | ~20 seconds | 100% |
| csv_sales_orders | ~11,000 | ~30 seconds | 100% |
| csv_bills | ~3,100 | ~15 seconds | 100% |
| csv_customer_payments | ~3,400 | ~15 seconds | 100% |
| csv_purchase_orders | ~2,900 | ~15 seconds | 100% |
| csv_items | ~1,850 | ~10 seconds | 100% |
| csv_credit_notes | ~1,500 | ~10 seconds | 100% |
| csv_vendor_payments | ~1,050 | ~8 seconds | 100% |
| csv_contacts | ~450 | ~5 seconds | 100% |
| csv_organizations | ~30 | ~2 seconds | 100% |

## 🔍 Troubleshooting

### Common Issues

#### CSV File Not Found
```
Error: CSV file not found: data/csv/Invoice.csv
```
**Solution**: Check CSV directory path and file names. Update configuration if needed.

#### Database Connection Error
```
Error: unable to open database file
```
**Solution**: Verify database path and permissions. Create directory if it doesn't exist.

#### Column Mapping Issues
```
Warning: CSV column 'Invoice Date' -> 'invoice_date' not found
```
**Solution**: This is normal. The system maps available columns and skips missing ones.

#### Permission Errors
```
Error: Permission denied writing to logs/
```
**Solution**: Ensure write permissions for log directory or change log directory.

### Debug Mode
Enable detailed logging for troubleshooting:
```python
runner = CSVDatabaseRebuildRunner(enable_logging=True)
```

### Verification Steps
1. **Check Configuration**: Verify all paths exist and are accessible
2. **Test Single Table**: Try populating one table first
3. **Review Logs**: Check log files for detailed error information
4. **Verify CSV Format**: Ensure CSV files are properly formatted

## 🔧 Integration Examples

### Automated Pipeline Integration
```python
def daily_database_refresh():
    """Automated daily database refresh"""
    try:
        runner = CSVDatabaseRebuildRunner(
            db_path="prod/database/production.db",
            csv_dir="prod/csv/daily_export"
        )
        
        result = runner.populate_all_tables()
        
        if result['overall_success_rate'] >= 95:
            send_success_notification(result)
        else:
            send_error_notification(result['failed_tables'])
            
    except Exception as e:
        send_error_notification([str(e)])
```

### Selective Table Updates
```python
def update_critical_tables():
    """Update only critical business tables"""
    critical_tables = [
        "csv_invoices",
        "csv_sales_orders", 
        "csv_customer_payments"
    ]
    
    runner = CSVDatabaseRebuildRunner()
    result = runner.populate_all_tables(tables=critical_tables)
    
    return result['table_success_rate'] == 100
```

### Data Quality Monitoring
```python
def monitor_data_quality():
    """Monitor data quality and record counts"""
    runner = CSVDatabaseRebuildRunner()
    summary = runner.get_table_status_summary()
    
    quality_report = {
        "timestamp": datetime.now(),
        "total_records": summary['total_records'],
        "populated_tables": summary['populated_tables'],
        "population_rate": summary['population_rate']
    }
    
    return quality_report
```

## 📚 Best Practices

### For End Users
1. **Always initialize** the system before operations
2. **Verify configuration** before running destructive operations  
3. **Use single table operations** for testing
4. **Check verification reports** after population
5. **Keep backups** of important databases

### For Developers
1. **Handle return values** from all operations
2. **Check success rates** before proceeding
3. **Use appropriate logging levels** for your environment
4. **Implement error handling** for network and I/O issues
5. **Test with sample data** before production use

### For System Integrators
1. **Use programmatic API** instead of menu system
2. **Implement health checks** using verification methods
3. **Monitor processing times** for performance tracking
4. **Set up automated alerts** for failures
5. **Use custom table mappings** for flexibility

## 📞 Support and Maintenance

### Log Files
- **Location**: `logs/csv_rebuild_YYYYMMDD_HHMMSS.log`
- **Content**: Detailed operation logs with column mapping and progress
- **Format**: Human-readable with structured information

### Regular Maintenance
1. **Clean old log files** periodically
2. **Monitor disk space** for database and logs
3. **Update CSV mappings** when source structure changes
4. **Test with sample data** before major updates

### Getting Help
1. **Check logs** for detailed error information
2. **Review this guide** for usage examples
3. **Test with single tables** to isolate issues
4. **Verify file permissions** and paths

---

**Package Version**: 2.0  
**Last Updated**: July 12, 2025  
**Compatibility**: Python 3.7+, Windows/Linux  
**Dependencies**: pandas, sqlite3 (built-in)
