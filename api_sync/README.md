# API Sync Package

## Overview

The API Sync package provides a comprehensive solution for fetching, storing, and verifying data from the Zoho Books API. This package is designed to be a robust and configurable component of the larger Zoho Data Sync system, handling the API integration aspects.

## Features

- **OAuth Authentication**: Secure authentication with the Zoho Books API using OAuth 2.0
- **GCP Secret Management**: Integration with Google Cloud Platform Secret Manager for secure credential storage
- **Incremental Data Fetching**: Smart fetching of only new or modified data since last sync
- **Session Folder Organization**: Automatic creation of timestamped sync session folders for organized data storage
- **Comprehensive Reporting**: Session summaries, logs, and verification reports
- **Verification**: Data completeness verification between API and local data
- **Modular Design**: Well-structured codebase for maintainability and extensibility
- **Robust Error Handling**: Comprehensive error handling and retry logic for network issues
- **Detailed Logging**: Configurable logging levels for debugging and monitoring

## Key Features Added

### Timestamped Session Folders
Each sync operation creates a unique folder like `sync_session_2025-07-11_13-03-15` for better organization and traceability.

### Organized Folder Structure
```
sync_session_TIMESTAMP/
├── README.md                    # Auto-generated documentation
├── session_info.json          # Session metadata
├── raw_json/                   # Raw API data in timestamped subdirs
│   ├── 2025-07-11_13-03-15/   # Individual module sync timestamps
│   ├── 2025-07-11_13-03-27/
│   └── ...
├── logs/                       # Reserved for sync logs
└── reports/                    # Summary and verification reports
    └── session_summary.json   # Comprehensive sync results
```

### Enhanced API Methods
- `fetch_data()` with `use_session_folder=True` (default)
- `fetch_all_modules()` with session organization
- `list_sync_sessions()` for managing previous sessions

### Automatic Documentation
- Session README files explaining folder contents
- Session info metadata with timestamps
- Comprehensive summary reports with statistics

### Backward Compatibility
- Option to disable session folders with `use_session_folder=False`
- Maintains traditional `data/raw_json/` structure when disabled

### Benefits
- **Better Organization**: Clear separation of different sync operations
- **Traceability**: Complete audit trail of sync sessions
- **Easy Management**: Simple identification and cleanup of old sessions
- **Comprehensive Reporting**: Detailed statistics per session
- **Self-Documenting**: Auto-generated documentation for each session

### Files Modified/Created
- **Enhanced** `main_api_sync.py` - Added session folder functionality
- **Updated** `README.md` - Added documentation for new features
- **Created** `test_session_folders.py` - Test script for functionality
- **Created** `example_session_folders.py` - Usage examples

The system now automatically creates organized, timestamped folders for each sync operation, making data management much cleaner and more professional! 🎉

## Supported Modules

The package can fetch data from the following Zoho Books modules:

- `invoices`: Customer invoices and billing documents
- `items`: Inventory items and product catalog 
- `contacts`: Customer and vendor contact information
- `customerpayments`: Customer payment records
- `bills`: Vendor bills and purchase documents
- `vendorpayments`: Vendor payment records
- `salesorders`: Sales order documents
- `purchaseorders`: Purchase order documents
- `creditnotes`: Credit note documents
- `organizations`: Organization settings and information

## Installation

This package is part of the Zoho Data Sync V2 project and is designed to be used within that context.

### Requirements

- Python 3.8 or higher
- Required Python packages (see `requirements.txt` in the main project folder)
- Google Cloud Platform project with Secret Manager enabled
- Zoho Books API credentials (Client ID, Client Secret, Refresh Token)

## Configuration

1. Copy `.env.example` to `.env` in the project root and fill in your values:

```bash
# Google Cloud Project ID for Secret Manager
GCP_PROJECT_ID=your-gcp-project-id

# Path to Google Application Credentials JSON (for GCP Secret Manager)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json

# (Optional) Zoho Books Organization ID
ZOHO_ORGANIZATION_ID=your-zoho-org-id
```

2. Store your Zoho API credentials in Google Cloud Secret Manager:
   - `ZOHO_CLIENT_ID` 
   - `ZOHO_CLIENT_SECRET`
   - `ZOHO_REFRESH_TOKEN`

## Usage

### As a Module

```python
python -m api_sync [command] [options]
```

### From the Project Root

```python
# Command-line interface
python main_api_sync.py [command] [options]

# Interactive menu interface
python main_api_sync_menu.py
```

### From the api_sync Directory

You can run the main script directly from within the `api_sync` directory:

```bash
# Interactive menu interface
python runner_api_sync.py

# Or import for programmatic use
python -c "from runner_api_sync import create_runner; runner = create_runner()"
```

**Note**: The import logic automatically detects whether you're running from within the `api_sync` directory or from the parent directory and adjusts the imports accordingly, ensuring the script works from any location.

### Programmatic Usage

```python
from api_sync.runner_api_sync import create_runner

# Create a runner instance
runner = create_runner(log_level="INFO")

# Fetch data from a module
result = runner.fetch_data("invoices", full_sync=False)

# Verify data completeness
verify_result = runner.verify_data()

# Get system status
status = runner.get_status()
```

### Available Commands

#### Fetch Data

Fetch data from a specific Zoho Books module:

```bash
python -m api_sync fetch invoices [--since TIMESTAMP] [--full]
```

Options:
- `--since`: Only fetch records modified since this timestamp (ISO format)
- `--full`: Fetch all records, ignore the latest sync timestamp

#### Verify Data

Verify local data against the API to ensure completeness:

```bash
python -m api_sync verify [--directory DIR] [--modules MODULES] [--output FILE] [--quick] [--session SESSION]
```

Options:
- `--directory`, `-d`: Specific timestamp directory to verify (uses latest if not specified)
- `--modules`, `-m`: Comma-separated list of modules to verify (verifies all if not specified)
- `--output`, `-o`: Save verification results to a JSON file
- `--quick`: Quick verification mode (no API calls, uses existing session data)
- `--session`, `-s`: Specific session directory to use for quick verification

#### Check Status

Show system status including configuration and authentication:

```bash
python -m api_sync status
```

### Global Options

- `--log-level {DEBUG,INFO,WARNING,ERROR}`: Set the logging level

## Incremental Data Fetching

The api_sync package is designed to pull only incremental data by default. Here's how it works:

### How Incremental Fetching Works

1. **Timestamp-Based Incremental Fetching**:
   - The package tracks the last sync time and uses it to fetch only data that has been created or modified since that time.
   - This is controlled by the `--since` parameter in the fetch command, which defaults to using the latest sync timestamp if not specified.

2. **How the "Since" Timestamp is Determined**:
   - When you run a fetch command without the `--full` flag, the package automatically:
     - Scans the `data/raw_json` directory for folders with timestamp names (YYYY-MM-DD_HH-MM-SS format)
     - Finds the most recent timestamp directory and converts that to an ISO format timestamp
     - Uses this timestamp for the API call to request only records modified since that time

3. **Zoho API Integration**:
   - The timestamp is converted to the format Zoho expects (MySQL datetime format: YYYY-MM-DD HH:MM:SS)
   - It's included in the API request parameters as `modified_time`
   - The Zoho API then returns only records that were created or modified after that timestamp

4. **Force Full Sync**:
   - If you want to override the incremental behavior, use the `--full` flag to fetch all records regardless of modification time
   - You can also specify a custom timestamp with `--since "2025-01-01T00:00:00Z"` to fetch data modified since that time

### Local JSON Storage

The JSON data is stored locally in the following structure:

1. **Base Directory**: `data/raw_json` (configurable via `JSON_BASE_DIR` environment variable)

2. **Timestamp Directories**:
   - Each sync run creates a new timestamped directory, e.g., `data/raw_json/2025-07-08_14-30-00/`
   - This timestamp is used for future incremental syncs

3. **Module Files**:
   - Inside each timestamped directory, JSON files are created for each module
   - For example: `data/raw_json/2025-07-08_14-30-00/invoices.json`
   - Each file contains the array of records fetched from the API

4. **Directory Structure Example**:
   ```
   data/
   └── raw_json/
       ├── 2025-06-10_09-15-30/
       │   ├── invoices.json
       │   ├── bills.json
       │   └── contacts.json
       ├── 2025-06-28_15-45-22/
       │   ├── invoices.json
       │   └── items.json
       └── 2025-07-08_14-30-00/  (latest sync)
           ├── invoices.json
           ├── bills.json
           ├── contacts.json
           └── customerpayments.json
   ```

### Benefits of Incremental Fetching

- **Efficiency**: Minimizes API requests by only fetching new or changed data
- **Speed**: Reduces processing time for subsequent syncs
- **API Quota Management**: Helps stay within API rate limits
- **Historical Data Preservation**: Maintains a historical record of each sync in separate directories

## Session Folder Organization

The api_sync package now supports automatic organization of sync operations into timestamped session folders for better data management and traceability.

### Session Folder Structure

When using the enhanced `ApiSyncWrapper` with session folders enabled (default), each sync operation creates a dedicated session folder:

```
data/
└── sync_sessions/
    └── sync_session_2025-07-11_13-01-06/
        ├── README.md                    # Session documentation
        ├── session_info.json          # Session metadata
        ├── raw_json/                   # Raw API data (timestamped subdirs)
        │   └── 2025-07-11_13-01-06/
        │       ├── invoices.json
        │       ├── bills.json
        │       └── contacts.json
        ├── logs/                       # Sync operation logs
        └── reports/                    # Summary and verification reports
            └── session_summary.json   # Session completion summary
```

### Session Features

1. **Automatic Organization**: Each sync creates a unique session folder with timestamp
2. **Comprehensive Documentation**: README and metadata files explain the session contents
3. **Structured Storage**: Organized subdirectories for different types of output
4. **Session Summaries**: Automatic generation of sync result summaries
5. **Session Listing**: Ability to list and analyze previous sync sessions

## Data Consumption Guide

**📋 For Developers, Data Analysts, and External Systems**

The API Sync system provides organized, accessible data for downstream consumption. Here's how to access and consume the synced Zoho data:

### 📁 Quick Access

**Latest Data Location**: `api_sync/data/sync_sessions/` (session-based) or `api_sync/data/raw_json/` (traditional)

**Quick Start Example**:
```python
from pathlib import Path
import json

# Get latest session data
sessions_dir = Path("api_sync/data/sync_sessions")
latest_session = sorted([f for f in sessions_dir.iterdir() if f.is_dir()], reverse=True)[0]

# Load specific module data
def load_data(module_name):
    raw_json_dir = latest_session / "raw_json"
    for timestamp_dir in raw_json_dir.iterdir():
        file_path = timestamp_dir / f"{module_name}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    return None

# Access your data
invoices = load_data("invoices")
contacts = load_data("contacts")
```

### 📊 Available Data Modules

| Module | File Name | Has Line Items | Description |
|--------|-----------|----------------|-------------|
| **invoices** | `invoices.json` | ✅ | Customer invoices + `invoices_line_items.json` |
| **bills** | `bills.json` | ✅ | Vendor bills + `bills_line_items.json` |
| **salesorders** | `salesorders.json` | ✅ | Sales orders + line items |
| **purchaseorders** | `purchaseorders.json` | ✅ | Purchase orders + line items |
| **creditnotes** | `creditnotes.json` | ✅ | Credit notes + line items |
| **items** | `items.json` | ❌ | Product/service catalog |
| **contacts** | `contacts.json` | ❌ | Customer/vendor contacts |
| **customerpayments** | `customerpayments.json` | ❌ | Payment receipts |
| **vendorpayments** | `vendorpayments.json` | ❌ | Vendor payments |

### 📖 Detailed Documentation

- **[📚 DATA_CONSUMER_GUIDE.md](DATA_CONSUMER_GUIDE.md)**: Complete guide with code examples, best practices, and error handling
- **[🚀 QUICK_REFERENCE.md](QUICK_REFERENCE.md)**: Quick reference card for immediate use

### 🔗 Integration Examples

```python
# Check data freshness
age_hours = (datetime.now() - session_timestamp).total_seconds() / 3600

# Link invoices with line items
def link_with_line_items(invoices, line_items):
    for invoice in invoices:
        invoice['line_items'] = [li for li in line_items if li['invoice_id'] == invoice['id']]
    return invoices

# Process in batches for large datasets
def process_batches(data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]
```

**For complete integration examples, patterns, and best practices, see [DATA_CONSUMER_GUIDE.md](DATA_CONSUMER_GUIDE.md)**

## Package Structure

- `__main__.py`: Package entry point
- `cli.py`: Command-line interface and command handlers
- `config.py`: Configuration management
- `utils.py`: Utility functions
- `runner_api_sync.py`: Main script with both programmatic API and interactive menu
- `core/`: Core components
  - `auth.py`: Authentication with Zoho API
  - `client.py`: Zoho API client implementation
  - `secrets.py`: Secure credential management
- `processing/`: Data processing
  - `raw_data_handler.py`: Saving and loading raw JSON data
- `verification/`: Data verification
  - `api_local_verifier.py`: Verification between API and local data
  - `simultaneous_verifier.py`: Session-based verification

## Examples

### Basic Data Fetch

```bash
# Fetch recent invoices
python -m api_sync fetch invoices

# Fetch all contacts (full refresh)
python -m api_sync fetch contacts --full

# Fetch bills modified since a specific date
python -m api_sync fetch bills --since 2025-01-01T00:00:00Z
```

### Data Verification

```bash
# Verify all modules in the latest sync
python -m api_sync verify

# Verify specific modules
python -m api_sync verify --modules invoices,bills,contacts

# Quick verification using existing session data
python -m api_sync verify --quick
```

## Error Handling

The package includes comprehensive error handling for:

- Authentication failures
- Network connectivity issues
- Rate limiting and API throttling
- Malformed responses
- File system errors

## Integration

This package is designed to work as part of the larger Zoho Data Sync system. The raw JSON data it produces can be:

1. Consolidated with the `json_consolidate` package
2. Mapped to database fields with the `json_db_mapper` package
3. Synchronized to a database with the `json2db_sync` package
