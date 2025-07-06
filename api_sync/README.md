# API Sync Package

This package provides tools to fetch data from the Zoho Books API and verify it against local data. It includes a high-level wrapper interface and supports both real-time verification during sync and standalone verification operations.

## Quick Start

### Setup

1. Copy `.env.example` to `.env` in the `src/api_sync/` directory and configure:
   ```
   GCP_PROJECT_ID=your-project-id
   ZOHO_CLIENT_ID=your-client-id
   ZOHO_CLIENT_SECRET=your-client-secret
   ZOHO_REFRESH_TOKEN=your-refresh-token
   ZOHO_ORGANIZATION_ID=your-org-id
   ```

2. Set up Google Cloud authentication:
   ```
   set GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Main Operations

#### High-Level Wrapper (Recommended)

**Sync all modules with verification:**
```bash
python main_api_sync.py sync
```

**Sync specific modules:**
```bash
python main_api_sync.py sync --modules invoices,bills,contacts
```

**Sync since specific date:**
```bash
python main_api_sync.py sync --since 2025-05-01
```

**Full verification (with API calls):**
```bash
python main_api_sync.py verify --full
```

**Quick verification (using session data):**
```bash
python main_api_sync.py verify --quick
```

#### Direct CLI Access

**Fetch specific module:**
```bash
python -m src.api_sync.cli fetch <module> [--since TIMESTAMP]
```

**Full verification:**
```bash
python -m src.api_sync.cli verify
```

**Quick verification:**
```bash
python -m src.api_sync.cli verify --quick
```

### Supported Modules

Standard modules:
- `contacts` - Customers/vendors
- `items` - Products/services  
- `customerpayments` - Customer payments
- `vendorpayments` - Vendor payments
- `organizations` - Organization info

Document modules (with line items):
- `invoices` - Sales invoices
- `bills` - Vendor bills
- `salesorders` - Sales orders
- `purchaseorders` - Purchase orders
- `creditnotes` - Credit notes

## Verification Modes

### Quick Verification
- Uses data from recent sync sessions
- No API calls required
- Fast execution
- Shows results from simultaneous tracking

### Full Verification  
- Makes fresh API calls for current counts
- Compares against local JSON data
- Comprehensive line item analysis
- Always up-to-date results

### Simultaneous Verification
- Automatic during sync operations
- Real-time progress tracking
- Records verification data during sync
- Creates session files for later quick verification

## System Architecture

### Entry Points
- `main_api_sync.py` - High-level wrapper (recommended for most users)
- `python -m src.api_sync.cli` - Direct CLI access for advanced operations
- `main_json2db.py` - JSON-to-database sync operations

### Core Components
- `src/api_sync/cli.py` - Command line interface
- `src/api_sync/core/` - Core API communication modules
  - `auth.py` - OAuth2 authentication with Zoho
  - `client.py` - API client with page-looping support
  - `secrets.py` - GCP Secret Manager integration
- `src/api_sync/processing/` - Data processing modules
  - `raw_data_handler.py` - JSON data storage and retrieval
- `src/api_sync/verification/` - Verification modules
  - `api_local_verifier.py` - API vs Local data comparison
  - `simultaneous_verifier.py` - Real-time sync verification

### Configuration Files
- `src/api_sync/.env` - Environment configuration (create from .env.example)
- `src/api_sync/config.py` - Application configuration defaults

## Data Structure

### Local Storage
```
data/
  raw_json/
    YYYY-MM-DD_HH-MM-SS/  # Timestamp of each sync run
      invoices.json         # Document headers
      invoices_line_items.json  # Line items (for document modules)
      bills.json
      bills_line_items.json
      contacts.json         # Standard modules
      items.json
      ...
      sync_verification_session.json  # Session tracking data
```

### Verification Output
All verification reports show:
- Module name and display name
- API count vs Local count  
- Line items count (for document modules)
- Difference analysis and match status
- Summary statistics with total line items

## Examples

### Complete Workflow
```bash
# 1. Sync all modules since May 1st
python main_api_sync.py sync --since 2025-05-01

# 2. Quick verification of the sync
python main_api_sync.py verify --quick

# 3. Full verification with fresh API calls
python main_api_sync.py verify --full
```

### Targeted Operations
```bash
# Sync only invoice-related modules
python main_api_sync.py sync --modules invoices,creditnotes

# Sync with extended timeout for large datasets
python main_api_sync.py sync --timeout 1800

# Direct CLI for advanced users
python -m src.api_sync.cli fetch invoices --since 2025-01-01 --full
```

### Help and Documentation
```bash
python main_api_sync.py --help
python main_api_sync.py sync --help
python main_api_sync.py verify --help
```

For comprehensive user documentation, see `docs/API_SYNC_USER_GUIDE.md`.
