# Main API Sync Wrapper - User Guide

The `main_api_sync.py` wrapper provides a simplified interface for API sync operations with integrated verification.

## Quick Start

### Environment Setup
1. Copy `.env.example` to `.env` in the `src/api_sync/` directory
2. Fill in your Zoho credentials in the `.env` file
3. Ensure Python dependencies are installed: `pip install -r requirements.txt`

### Basic Operations

#### Sync All Modules with Verification
```bash
python main_api_sync.py sync
```

#### Sync Specific Modules  
```bash
python main_api_sync.py sync --modules invoices,bills,contacts
```

#### Sync Since Specific Date
```bash
python main_api_sync.py sync --since 2025-05-01
```

#### Run Full Verification Only
```bash
python main_api_sync.py verify --full
```

#### Run Quick Verification Only
```bash
python main_api_sync.py verify --quick
```

## Verification Modes

### Quick Verification (`--quick`)
- Uses data from the most recent sync session
- No API calls required
- Fast execution
- Shows verification results from simultaneous tracking

### Full Verification (`--full`) 
- Makes fresh API calls to get current counts
- Compares against local JSON data
- Slower but always up-to-date
- Comprehensive line item analysis

### Simultaneous Verification (during sync)
- Automatic during `sync` command
- Tracks progress in real-time
- Records verification data as sync runs
- Creates session files for later quick verification

## Output Format

All verification reports show:
- Module name and display name
- API count vs Local count
- Line items count (for document modules)
- Difference analysis
- Match status
- Summary statistics

## Module Support

**Standard Modules:**
- organizations (Organization info)
- items (Products/services)
- contacts (Customers/vendors)
- customerpayments (Customer payments)
- vendorpayments (Vendor payments)

**Document Modules with Line Items:**
- invoices (Sales invoices)
- bills (Vendor bills)
- salesorders (Sales orders)
- purchaseorders (Purchase orders)
- creditnotes (Credit notes)

## File Locations

**Raw JSON Data**: `data/raw_json/<timestamp>/`
**Session Data**: `data/raw_json/<timestamp>/sync_verification_session.json`
**Configuration**: `src/api_sync/.env`

## Troubleshooting

### Common Issues
1. **Authentication Error**: Check .env file has correct Zoho credentials
2. **No Session Data**: Run a sync first before quick verification
3. **Module Not Found**: Ensure module name is correct and supported
4. **Timeout Error**: Increase timeout with `--timeout <seconds>`

### Error Recovery
- Failed modules are reported clearly
- Retry commands are provided in output
- Each module can be synced individually if needed

### Getting Help
```bash
python main_api_sync.py --help
python main_api_sync.py sync --help
python main_api_sync.py verify --help
```

## Examples

### Complete Workflow
```bash
# 1. Sync all modules since May 1st
python main_api_sync.py sync --since 2025-05-01

# 2. Quick verification of the sync
python main_api_sync.py verify --quick

# 3. Full verification with API calls
python main_api_sync.py verify --full
```

### Targeted Operations
```bash
# Sync only invoice-related modules
python main_api_sync.py sync --modules invoices,creditnotes

# Sync everything with extended timeout
python main_api_sync.py sync --timeout 1800
```

All operations include progress tracking, error handling, and clear status reporting.
