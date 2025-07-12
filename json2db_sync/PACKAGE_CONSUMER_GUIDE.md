# JSON2DB Sync Package - Data Consumer Guide

## 📋 Overview

The `json2db_sync` package provides robust JSON-to-Database synchronization capabilities with comprehensive data processing, validation, and verification features. This guide covers everything you need to know to effectively use this package for data consumption and synchronization operations.

**Last Updated:** July 12, 2025  
**Package Version:** Production Ready  
**Architecture:** Runner/Wrapper Pattern

---

## 🎯 Quick Start

### Immediate Usage (Interactive)
```bash
# Navigate to the package directory
cd json2db_sync

# Launch interactive menu system
python -m json2db_sync.main_json2db_sync

# Follow the menu prompts - Option 6 (Full Workflow) is most common
```

### Programmatic Usage
```python
from json2db_sync.runner_json2db_sync import JSON2DBSyncRunner

# Initialize runner with default configuration
runner = JSON2DBSyncRunner()

# Execute full sync workflow
result = runner.full_sync_workflow(
    db_path="data/database/production.db",
    json_dir="data/raw_json/json_compiled",
    cutoff_days=30
)

if result["success"]:
    print(f"✅ Sync completed: {result['statistics']['total_records']} records")
else:
    print(f"❌ Sync failed: {result['error']}")
```

---

## 🏗️ Package Architecture

### Core Components

#### 1. **Interactive Wrapper** (`main_json2db_sync.py`)
- **Purpose**: User-friendly menu-driven interface
- **Features**: Guided workflows, input validation, no dead ends
- **Best For**: Manual operations, testing, exploration

#### 2. **Business Logic Runner** (`runner_json2db_sync.py`)
- **Purpose**: Pure programmatic access without UI
- **Features**: Structured return values, error handling, logging
- **Best For**: Automation, integration, scripting

#### 3. **Core Processing Modules**
- `json_analyzer.py` - JSON file structure analysis
- `table_generator.py` - SQL schema generation
- `data_populator.py` - Data loading with filtering
- `summary_reporter.py` - Comprehensive reporting
- `config.py` - Centralized configuration management

---

## 🔧 Configuration Setup

### Method 1: Environment Variables (Recommended)
```bash
# Copy template and customize
cp .env.example .env

# Edit .env file with your settings
# Key variables:
JSON2DB_DATA_SOURCE_TYPE=api_sync           # or "consolidated"
JSON2DB_API_SYNC_PATH=../api_sync          # Path to API sync data
JSON2DB_DATABASE_PATH=../data/database/production.db
JSON2DB_SESSION_MAX_AGE=24                 # Hours
```

### Method 2: Configuration File
```json
{
  "data_source": {
    "type": "api_sync",
    "api_sync_base_path": "../api_sync/data/sync_sessions",
    "prefer_session_based": true
  },
  "database": {
    "path": "../data/database/production.db",
    "backup_before_operations": true
  },
  "processing": {
    "default_cutoff_days": 30,
    "enable_duplicate_prevention": true
  }
}
```

### Method 3: Runtime Parameters
```python
runner = JSON2DBSyncRunner(
    db_path="custom/path/database.db",
    data_source="../api_sync",
    config_file="custom_config.json"
)
```

---

## 📊 Data Sources Supported

### 1. **API Sync Data** (Recommended)
- **Location**: `../api_sync/data/sync_sessions/`
- **Format**: Session-based JSON files with metadata
- **Advantages**: Timestamped, verified, metadata-rich
- **Auto-detection**: Latest successful sessions

### 2. **Consolidated JSON**
- **Location**: `data/raw_json/json_compiled/`
- **Format**: Consolidated JSON files
- **Advantages**: Pre-processed, deduplicated
- **Use Case**: When API sync not available

### 3. **Custom JSON Directory**
- **Location**: User-specified path
- **Format**: Standard JSON files
- **Advantages**: Flexible, external data sources
- **Use Case**: External integrations

---

## 🎛️ Available Operations

### Interactive Menu Options

| Option | Operation | Description | Use Case |
|--------|-----------|-------------|----------|
| **1** | JSON Analysis | Analyze JSON file structures | Schema discovery |
| **2** | Table Recreation | Recreate JSON tables (safe) | Schema updates |
| **3** | Data Population | Load data with filtering | Data refresh |
| **4** | Table Verification | Check table integrity | Quality assurance |
| **5** | Summary Report | Generate database report | Status overview |
| **6** | Full Workflow ⭐ | Complete sync process | Most common |
| **7** | Advanced Options | Additional configurations | Power users |

### Programmatic Methods

```python
# Individual operations
runner.analyze_json_files(json_dir_path)
runner.recreate_json_tables(db_path)
runner.populate_tables(db_path, json_dir, cutoff_days=30)
runner.verify_tables(db_path)
runner.generate_summary_report(db_path)

# Complete workflow (recommended)
runner.full_sync_workflow(
    db_path="production.db",
    json_dir="json_files/",
    cutoff_days=30,
    skip_table_creation=False
)
```

---

## 🔄 Common Workflows

### 1. **Daily Data Sync** (Most Common)
```bash
# Interactive approach
python -m json2db_sync.main_json2db_sync
# → Select Option 6 (Full Workflow)
# → Accept default paths
# → Set cutoff to 7-30 days
```

```python
# Programmatic approach
from json2db_sync import JSON2DBSyncRunner

runner = JSON2DBSyncRunner()
result = runner.full_sync_workflow(cutoff_days=7)
```

### 2. **Schema Updates**
```bash
# Recreate tables with new schema
python -m json2db_sync.main_json2db_sync
# → Select Option 2 (Table Recreation)
# → Confirm database path
```

### 3. **Data Verification**
```bash
# Check data integrity
python -m json2db_sync.main_json2db_sync
# → Select Option 4 (Table Verification)
```

### 4. **Historical Data Load**
```python
# Load older data with larger cutoff
runner = JSON2DBSyncRunner()
result = runner.full_sync_workflow(
    cutoff_days=90,  # Load 90 days of data
    skip_table_creation=True  # Keep existing schema
)
```

---

## 📁 Data Structure & Schema

### JSON Table Naming Convention
```
json_<entity_name>           # Main entity tables
json_<entity>_line_items     # Line item tables (for documents)
```

### Standard Columns Added
- `data_source` - Always set to 'json' for identification
- `id` - Primary key from source data
- `created_at` - Record creation timestamp
- `updated_at` - Last modification timestamp

### Supported Entity Types

#### **Main Entities**
- `json_contacts` - Customer and vendor contacts
- `json_items` - Products and services
- `json_organizations` - Organization data
- `json_customerpayments` - Customer payment records
- `json_vendorpayments` - Vendor payment records

#### **Document Entities** (with line items)
- `json_invoices` + `json_invoices_line_items`
- `json_bills` + `json_bills_line_items`
- `json_salesorders` + `json_salesorders_line_items`
- `json_purchaseorders` + `json_purchaseorders_line_items`
- `json_creditnotes` + `json_creditnotes_line_items`

---

## 🛡️ Data Safety & Validation

### Built-in Safety Features
- **Duplicate Prevention**: Automatic detection and skipping
- **Schema Validation**: Type checking and constraint validation
- **Backup Creation**: Optional database backup before operations
- **Transaction Safety**: Rollback on errors
- **Progress Tracking**: Detailed logging and progress reporting

### Validation Checks
- **Data Type Validation**: Ensures data types match schema
- **Required Field Checks**: Validates mandatory fields
- **Relationship Integrity**: Checks foreign key relationships
- **Date Format Validation**: Ensures proper date formatting
- **Numeric Range Validation**: Validates numeric constraints

### Error Handling
```python
result = runner.full_sync_workflow()

if not result["success"]:
    error_type = result.get("error_type", "unknown")
    error_message = result.get("error", "No details")
    
    if error_type == "database_error":
        # Handle database connection issues
        pass
    elif error_type == "validation_error":
        # Handle data validation issues
        pass
    elif error_type == "file_error":
        # Handle file access issues
        pass
```

---

## 📈 Performance & Optimization

### Performance Features
- **Batch Processing**: Configurable batch sizes (default: 1000)
- **Memory Management**: Configurable memory limits
- **Index Optimization**: Automatic index creation
- **Connection Pooling**: Efficient database connections
- **Progress Indicators**: Real-time progress tracking

### Optimization Settings
```python
# High-performance configuration
runner = JSON2DBSyncRunner()
result = runner.full_sync_workflow(
    cutoff_days=7,           # Smaller dataset
    skip_table_creation=True, # Skip schema operations
)

# Configuration via environment
JSON2DB_BATCH_SIZE=2000     # Larger batches
JSON2DB_MEMORY_LIMIT=1024   # More memory
```

### Performance Monitoring
```python
result = runner.full_sync_workflow()

stats = result.get("statistics", {})
print(f"Records processed: {stats.get('total_records', 0)}")
print(f"Processing time: {stats.get('processing_time_seconds', 0):.2f}s")
print(f"Records/second: {stats.get('records_per_second', 0):.1f}")
```

---

## 🔍 Monitoring & Troubleshooting

### Status Checking
```python
# Check current database status
runner = JSON2DBSyncRunner()
report = runner.generate_summary_report()

if report["success"]:
    for table in report["tables"]:
        print(f"{table['name']}: {table['record_count']} records")
```

### Common Issues & Solutions

#### **Issue**: No data found
```
Solution: Check data source configuration
- Verify JSON2DB_DATA_SOURCE_TYPE
- Ensure API sync has run successfully
- Check file permissions
```

#### **Issue**: Schema conflicts
```
Solution: Recreate tables
python -m json2db_sync.main_json2db_sync
# → Option 2 (Table Recreation)
```

#### **Issue**: Performance slow
```
Solution: Optimize settings
- Reduce cutoff_days
- Increase batch_size
- Enable skip_existing_records
```

### Logging Configuration
```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Run operations with detailed logs
runner = JSON2DBSyncRunner()
result = runner.full_sync_workflow()
```

---

## 🔗 Integration Examples

### 1. **Automated Daily Sync**
```python
#!/usr/bin/env python3
"""Daily sync automation script"""
import sys
from datetime import datetime
from json2db_sync import JSON2DBSyncRunner

def daily_sync():
    print(f"Starting daily sync at {datetime.now()}")
    
    runner = JSON2DBSyncRunner()
    result = runner.full_sync_workflow(
        cutoff_days=1,  # Only yesterday's data
        skip_table_creation=True
    )
    
    if result["success"]:
        stats = result["statistics"]
        print(f"✅ Success: {stats['total_records']} records")
        return 0
    else:
        print(f"❌ Failed: {result['error']}")
        return 1

if __name__ == "__main__":
    sys.exit(daily_sync())
```

### 2. **Data Pipeline Integration**
```python
"""Integration with external data pipeline"""
from json2db_sync import JSON2DBSyncRunner

class DataPipeline:
    def __init__(self):
        self.json2db_runner = JSON2DBSyncRunner()
    
    def process_json_data(self, json_directory: str):
        # Step 1: Analyze incoming data
        analysis = self.json2db_runner.analyze_json_files(json_directory)
        
        # Step 2: Update schema if needed
        if analysis.get("schema_changes_required"):
            self.json2db_runner.recreate_json_tables()
        
        # Step 3: Load data
        result = self.json2db_runner.populate_tables(
            json_dir=json_directory,
            cutoff_days=30
        )
        
        # Step 4: Verify data integrity
        verification = self.json2db_runner.verify_tables()
        
        return {
            "analysis": analysis,
            "load_result": result,
            "verification": verification
        }
```

### 3. **Custom Configuration**
```python
"""Custom configuration for specific environments"""
import os
from json2db_sync import JSON2DBSyncRunner

# Production environment
if os.getenv("ENVIRONMENT") == "production":
    runner = JSON2DBSyncRunner(
        db_path="/production/database/zoho_data.db",
        data_source="/data/api_sync_production/",
        config_file="config/production.json"
    )
else:
    # Development environment
    runner = JSON2DBSyncRunner(
        db_path="dev_database.db",
        data_source="test_data/",
        config_file="config/development.json"
    )

# Run with environment-specific settings
result = runner.full_sync_workflow(
    cutoff_days=7 if os.getenv("ENVIRONMENT") == "production" else 365
)
```

---

## 📚 Advanced Features

### 1. **Custom Data Filtering**
```python
# Filter data by date range and entity type
runner = JSON2DBSyncRunner()

# Custom filtering parameters
result = runner.populate_tables(
    json_dir="data/json_files/",
    cutoff_days=30,
    entity_filter=["invoices", "bills"],  # Only specific entities
    date_filter="2025-01-01"  # Only data after this date
)
```

### 2. **Schema Customization**
```python
# Custom schema generation
runner = JSON2DBSyncRunner()

schema_result = runner.generate_table_schemas(
    json_dir="data/",
    include_indexes=True,
    custom_columns={
        "data_source": "TEXT DEFAULT 'json'",
        "import_timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
)
```

### 3. **Multi-Source Data Handling**
```python
# Handle multiple data sources
sources = [
    {"path": "../api_sync/session_1/", "type": "api_sync"},
    {"path": "consolidated_data/", "type": "consolidated"},
    {"path": "external_data/", "type": "custom"}
]

for source in sources:
    runner = JSON2DBSyncRunner(data_source=source["path"])
    result = runner.full_sync_workflow(cutoff_days=30)
    print(f"Processed {source['type']}: {result['success']}")
```

---

## 🎯 Best Practices

### 1. **Configuration Management**
- ✅ Use environment variables for credentials
- ✅ Use configuration files for complex settings
- ✅ Document configuration changes
- ✅ Test configuration in development first

### 2. **Data Management**
- ✅ Regular backups before major operations
- ✅ Use appropriate cutoff days for data volume
- ✅ Monitor disk space and memory usage
- ✅ Implement data retention policies

### 3. **Performance**
- ✅ Start with small cutoff days, increase gradually
- ✅ Use batch processing for large datasets
- ✅ Monitor processing times and adjust settings
- ✅ Enable duplicate prevention for efficiency

### 4. **Error Handling**
- ✅ Always check return values for success
- ✅ Implement retry logic for transient failures
- ✅ Log errors with sufficient detail
- ✅ Have rollback procedures for critical operations

### 5. **Monitoring**
- ✅ Regular status reports and verification
- ✅ Monitor data freshness and completeness
- ✅ Set up alerts for sync failures
- ✅ Track performance metrics over time

---

## 📞 Support & Troubleshooting

### Getting Help
1. **Interactive Help**: Use the menu system for guided operations
2. **Documentation**: Check README.md for latest updates
3. **Error Messages**: Review detailed error messages and suggestions
4. **Logging**: Enable debug logging for detailed troubleshooting

### Common Commands for Support
```bash
# Check package status
python -c "from json2db_sync import JSON2DBSyncRunner; print('Package loaded successfully')"

# Test database connection
python -m json2db_sync.main_json2db_sync
# → Option 4 (Verify Tables)

# Generate diagnostic report
python -m json2db_sync.main_json2db_sync
# → Option 5 (Summary Report)
```

### Emergency Procedures
```python
# Emergency data verification
runner = JSON2DBSyncRunner()
verification = runner.verify_tables()

if not verification["success"]:
    # Restore from backup
    # Re-run table recreation
    # Contact support with error details
```

---

**Package Status**: Production Ready ✅  
**Last Updated**: July 12, 2025  
**Maintained By**: JSON2DB Sync Team  
**Support**: See package documentation and error messages for guidance
