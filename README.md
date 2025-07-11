# Zoho Data Sync - Complete ETL Pipeline

## 🎯 Overview

A comprehensive data synchronization system that provides both **JSON-to-Da- `creditnotes` - 567 headers + 756 line items

## 🔄 JSON Consolidation & Freshness Check

### Smart Freshness Detection
The JSON consolidation system includes an intelligent freshness check that tracks processed files and only processes new or modified files, dramatically improving performance for large datasets.

**Key Features:**
- **File Tracking**: Maintains metadata (size, modification time) for all processed files
- **Change Detection**: Automatically detects new and modified files
- **Skip Optimization**: Skips consolidation when no changes detected
- **Force Rebuild**: Option to override freshness check for full reprocessing

**Usage Examples:**
```bash
# Smart consolidation (default - only new/changed files)
python -m json_consolidate.json_consolidator

# Check freshness status without processing
# See json_consolidate/README.md for additional options
```

**Performance Benefits:**
- **Typical 90%+ time savings** on subsequent runs
- **Efficient for large datasets** (tested with 271 files, 54K+ records)
- **Automatic skip** when no new data available
- **Incremental processing** maintains data consistency

### Example Output
```
FRESHNESS CHECK RESULTS
════════════════════════════════════════════════════════════
No new or modified files found.
Checked 271 files - all up to date.
════════════════════════════════════════════════════════════
```

## 📋 Usage Examplesase sync** and **API sync with verification**. The system includes modular pipeline components, real-time verification, and user-friendly interfaces for production operations.

## 🚀 Quick Start

### Entry Points

**🔥 Direct Differential Build (Fastest):**
```bash
python direct_differential_build.py              # Quick analysis (bypasses API sync)
python direct_differential_build.py --apply      # Apply changes only
```

**JSON-to-Database Sync:**
```bash
python main_json2db.py sync     # Full sync
python main_json2db.py status   # Check status
```

**JSON Consolidation (with Freshness Check):**
```bash
python main_json_consolidate.py                # Smart consolidation (process only new/changed files)
python main_json_consolidate.py --force-rebuild # Force full rebuild (all files)
python main_json_consolidate.py --freshness-check # Check file status only
python main_json_consolidate.py --stats-only   # Show statistics only
```

**API Sync with Verification:**
```bash
python main_api_sync.py sync                    # Sync all modules
python main_api_sync.py sync --since 2025-05-01 # Sync since date
python main_api_sync.py verify --full           # Full verification
python main_api_sync.py verify --quick          # Quick verification
```

**Global Sync Manager (Interactive):**
```bash
python main_sync.py             # Interactive menu with all options
```

### Setup

1. **Configure API sync** (copy `src/api_sync/.env.example` to `src/api_sync/.env`):
   ```
   GCP_PROJECT_ID=your-project-id
   ZOHO_CLIENT_ID=your-client-id
   ZOHO_CLIENT_SECRET=your-client-secret
   ZOHO_REFRESH_TOKEN=your-refresh-token
   ZOHO_ORGANIZATION_ID=your-org-id
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud authentication:**
   ```bash
   set GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
   ```

## 🏗️ System Architecture

### Core Components

**JSON Consolidation:**
```
json_consolidate/           # JSON file consolidation with freshness check
├── json_consolidator.py   # Main consolidation logic
├── __init__.py            # Package interface
└── README.md             # Detailed documentation
```

**JSON Sync Pipeline:**
```
src/json_sync/           # JSON-to-database sync
├── orchestrator/
│   └── cli.py          # Command interface
├── transformers/        # Data transformation
└── database/           # Database operations
```

**API Sync Pipeline:**
```
src/api_sync/           # API sync with verification
├── cli.py              # Command interface  
├── core/               # API communication
│   ├── auth.py         # OAuth2 authentication
│   ├── client.py       # API client with pagination
│   └── secrets.py      # GCP Secret Manager
├── processing/         # Data processing
│   └── raw_data_handler.py
└── verification/       # Multi-mode verification
    ├── api_local_verifier.py      # API vs Local comparison
    └── simultaneous_verifier.py   # Real-time verification
```

**Entry Points:**
- `main_json2db.py` - JSON-to-database operations
- `main_json_consolidate.py` - JSON consolidation with freshness check
- `main_api_sync.py` - High-level API sync wrapper
- Direct CLI access via `python -m src.api_sync.cli`

## 📊 Verification System

### Full Verification
- Makes fresh API calls for current counts
- Compares against all local JSON data
- Comprehensive line item analysis
- **Latest Results**: 10/10 modules perfect match (19,579 total line items)

### Quick Verification  
- Uses recent sync session data
- No API calls required
- Fast execution

### Simultaneous Verification
- Real-time tracking during sync operations
- Records progress as API fetches run
- Creates session files for later quick verification

## 🎯 Supported Modules

**Standard Modules:**
- `contacts` (Customers/vendors) - 253 records
- `items` (Products/services) - 928 records  
- `customerpayments` - 1,154 records
- `vendorpayments` - 442 records
- `organizations` - 3 records

**Document Modules with Line Items:**
- `invoices` (Sales invoices) - 1,836 headers + 6,897 line items
- `bills` (Vendor bills) - 421 headers + 3,216 line items
- `salesorders` - 949 headers + 5,728 line items
- `purchaseorders` - 57 headers + 2,982 line items
- `creditnotes` - 567 headers + 756 line items

## � Usage Examples

### Complete API Sync Workflow
```bash
# Sync all modules since May 1st with verification
python main_api_sync.py sync --since 2025-05-01

# Quick verification using session data
python main_api_sync.py verify --quick

# Full verification with fresh API calls
python main_api_sync.py verify --full
```

### Targeted Operations
```bash
# Sync specific modules only
python main_api_sync.py sync --modules invoices,bills,contacts

# Sync with extended timeout for large datasets
python main_api_sync.py sync --timeout 1800

# JSON-to-database sync
python main_json2db.py sync

# Check JSON sync status
python main_json2db.py status
```

### Direct CLI Access (Advanced)
```bash
# Fetch specific module with date filter
python -m src.api_sync.cli fetch invoices --since 2025-01-01

# Run verification
python -m src.api_sync.cli verify

# JSON sync via direct CLI
python -m src.json_sync sync
```

## � Data Structure

### Local JSON Storage
```
data/
  raw_json/
    YYYY-MM-DD_HH-MM-SS/        # Timestamp of each sync run
      invoices.json              # Document headers
      invoices_line_items.json   # Line items (for document modules)
      bills.json
      bills_line_items.json
      contacts.json              # Standard modules
      items.json
      sync_verification_session.json  # Session tracking data
    json_compiled/               # Consolidated output (freshness-tracked)
      invoices.json              # Deduplicated consolidated files
      contacts.json              # All record types
      processed_files.json       # Freshness tracking metadata
      consolidation_report.json  # Processing statistics
```

### Database Storage
```
data/
  database/
    production.db               # SQLite database with canonical schema
## 🛠️ Configuration

### API Sync Configuration (`src/api_sync/.env`)
```bash
# Copy from .env.example and configure:
GCP_PROJECT_ID=your-project-id
ZOHO_CLIENT_ID=your-client-id
ZOHO_CLIENT_SECRET=your-client-secret
ZOHO_REFRESH_TOKEN=your-refresh-token
ZOHO_ORGANIZATION_ID=your-org-id
```

### System Configuration (`config/settings.yaml`)
```yaml
data_sources:
  json_api_path: "data/raw_json"
  target_database: "data/database/production.db"

processing:
  batch_size: 1000
  validate_transformations: true
  show_progress: true

logging:
  level: "INFO"
  console: true
```

## 🧪 Testing & Validation

### System Status (Latest Test - July 6, 2025)
- ✅ **API Sync**: 10/10 modules perfect match (100%)
- ✅ **JSON Sync**: All entities synchronized successfully
- ✅ **Verification**: 19,579 total line items verified
- ✅ **Windows Compatibility**: Unicode issues resolved
- ✅ **Error Handling**: Robust timeout and failure recovery

### Built-in Validation
- **API vs Local**: Real-time comparison during sync
- **Data integrity**: Type validation and constraint checking
- **Schema consistency**: Verified across all modules
- **Line item tracking**: Complete visibility into document structure

## � Production Ready Features

### Reliability
- **Windows PowerShell compatible** output (Unicode issues resolved)
- **Robust error handling** with clear recovery instructions
- **Progress tracking** for long-running operations
- **Session management** for interrupted sync recovery

### User Experience
- **Clear status messages** with bracketed indicators [OK], [ERROR]
- **Comprehensive help** documentation and examples
- **Multiple verification modes** for different use cases
- **Timeout management** for large dataset handling

## 📁 Project Structure

```
Zoho_Data_Sync/
├── main_api_sync.py              # High-level API sync wrapper
├── main_json2db.py               # JSON-to-database entry point
├── main_json_consolidate.py      # JSON consolidation entry point
├── json_consolidate/             # JSON consolidation package
│   ├── json_consolidator.py     # Consolidation logic with freshness check
│   ├── __init__.py              # Package interface
│   └── README.md                # Package documentation
├── src/
│   ├── api_sync/                 # API sync pipeline
│   │   ├── cli.py               # Command interface
│   │   ├── core/                # API communication
│   │   ├── processing/          # Data processing
│   │   └── verification/        # Multi-mode verification
│   └── json_sync/               # JSON-to-database pipeline
│       ├── orchestrator/
│       ├── transformers/
│       └── database/
├── data/
│   ├── raw_json/                # API fetch results
│   │   └── json_compiled/       # Consolidated & deduplicated files
│   └── database/                # SQLite databases
├── docs/
│   └── API_SYNC_USER_GUIDE.md   # Comprehensive user guide
├── copilot_notes/               # Modular project documentation
└── PROJECT_COMPLETION_REPORT.md # Final project status
```

## 🎯 Getting Help

### Documentation
- **Quick Start**: This README
- **API Sync**: `api_sync/README.md`  
- **User Guide**: `docs/API_SYNC_USER_GUIDE.md`
- **Project Status**: `PROJECT_COMPLETION_REPORT.md`

### Command Help
```bash
python main_api_sync.py --help
python main_json2db.py --help
python -m src.api_sync.cli --help
```

**Status**: Production ready system with comprehensive testing and documentation.

### Immediate Enhancements
1. **Add more entities**: Invoices, Customers, Items, etc.
2. **Enhanced error handling**: Specific error recovery strategies
3. **Progress indicators**: Real-time progress bars for large datasets
4. **Data validation**: Business rule validation beyond schema

### Future Features
1. **Incremental updates**: Smart detection of changed records
2. **Conflict resolution**: Handle data conflicts between sources
3. **Data quality metrics**: Comprehensive data quality reporting
4. **API integration**: Direct API fetching alongside file processing

## 🏆 Success Metrics

This production implementation delivers:
- ✅ **Unified canonical schema** for all data sources
- ✅ **100% validated transformations** based on comprehensive PoC
- ✅ **Smart freshness check system** with 90%+ performance improvements
- ✅ **Configuration-driven flexibility** for different environments
- ✅ **Robust error handling** and comprehensive logging
- ✅ **Production-ready code** with proper separation of concerns
- ✅ **Scalable architecture** ready for additional entities
- ✅ **Incremental processing** with file change detection

**Project Bedrock V2 successfully transforms validated PoC logic into a robust, production-ready data synchronization pipeline!** 🚀
