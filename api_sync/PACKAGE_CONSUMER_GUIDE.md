# Data Consumer Guide
## How to Access and Consume Synced Zoho Data

**Version**: 1.0  
**Last Updated**: July 11, 2025  
**Target Audience**: Developers, Data Analysts, Other Modules/Systems

---

## 📋 Overview

This guide explains how external modules and systems can access and consume the locally synced Zoho data. The API Sync system fetches data from Zoho APIs and stores it in organized JSON files and session folders for downstream consumption.

## 📁 Data Structure & Organization

### 1. **Session-Based Organization** (Recommended - New Structure)

**Location**: `api_sync/data/sync_sessions/`

Each sync operation creates a timestamped session folder:
```
api_sync/data/sync_sessions/
├── sync_session_2025-07-11_13-54-38/
│   ├── README.md                    # Session documentation
│   ├── session_info.json          # Session metadata
│   ├── raw_json/                   # Raw JSON data by timestamp
│   │   ├── 2025-07-11_13-54-38/   # Main modules
│   │   │   ├── invoices.json
│   │   │   └── invoices_line_items.json
│   │   ├── 2025-07-11_13-54-50/   # Next module batch
│   │   │   └── items.json
│   │   └── 2025-07-11_13-54-52/
│   │       └── contacts.json
│   ├── logs/                       # Session-specific logs
│   └── reports/                    # Session summary reports
│       └── session_summary.json
└── sync_session_2025-07-11_13-47-47/  # Previous session
    └── ...
```

### 2. **Traditional Structure** (Legacy - Still Supported)

**Location**: `api_sync/data/raw_json/`

Direct timestamp-based folders:
```
api_sync/data/raw_json/
├── 2025-07-11_10-05-44/           # Latest sync
│   ├── creditnotes.json
│   └── creditnotes_line_items.json
└── 2025-07-11_10-02-05/           # Previous sync
    ├── creditnotes.json
    └── creditnotes_line_items.json
```

## 🎯 Available Data Modules

### Main Business Entities
| Module | File Name | Description | Includes Line Items |
|--------|-----------|-------------|-------------------|
| **Invoices** | `invoices.json` | Customer invoices | ✅ `invoices_line_items.json` |
| **Bills** | `bills.json` | Vendor bills/purchases | ✅ `bills_line_items.json` |
| **Sales Orders** | `salesorders.json` | Customer sales orders | ✅ `salesorders_line_items.json` |
| **Purchase Orders** | `purchaseorders.json` | Vendor purchase orders | ✅ `purchaseorders_line_items.json` |
| **Credit Notes** | `creditnotes.json` | Customer credit notes | ✅ `creditnotes_line_items.json` |
| **Items** | `items.json` | Products/services catalog | ❌ |
| **Contacts** | `contacts.json` | Customer contacts | ❌ |
| **Customer Payments** | `customerpayments.json` | Payment receipts | ❌ |
| **Vendor Payments** | `vendorpayments.json` | Payment to vendors | ❌ |

### Supporting Entities
| Module | File Name | Description |
|--------|-----------|-------------|
| **Organizations** | `organizations.json` | Company/org details |
| **Budgets** | `budgets.json` | Budget information |
| **Tasks** | `tasks.json` | Project tasks |

## 🔍 Data Format & Structure

### JSON File Format
Each JSON file contains an array of objects:

```json
[
  {
    "id": "12345",
    "invoice_number": "INV-001",
    "customer_name": "ABC Company",
    "invoice_date": "2025-07-11",
    "total": 1500.00,
    "last_modified_time": "2025-07-11T10:30:00Z",
    "status": "paid"
  },
  {
    "id": "12346",
    "invoice_number": "INV-002",
    // ... more fields
  }
]
```

### Line Items Structure
Line items are stored in separate files with parent references:

```json
[
  {
    "line_item_id": "line_001",
    "invoice_id": "12345",  // Parent reference
    "item_id": "item_123",
    "description": "Product A",
    "quantity": 2,
    "rate": 750.00,
    "amount": 1500.00
  }
]
```

## 🛠️ How to Consume Data

### 1. **Find Latest Session Data** (Recommended)

```python
import json
import os
from pathlib import Path
from datetime import datetime

def get_latest_session_data():
    """Get data from the most recent sync session."""
    sessions_dir = Path("api_sync/data/sync_sessions")
    
    if not sessions_dir.exists():
        return None
    
    # Find latest session folder
    session_folders = [
        f for f in sessions_dir.iterdir() 
        if f.is_dir() and f.name.startswith("sync_session_")
    ]
    
    if not session_folders:
        return None
    
    # Sort by timestamp (newest first)
    latest_session = sorted(session_folders, key=lambda x: x.name, reverse=True)[0]
    
    return latest_session

def load_module_data(module_name, include_line_items=False):
    """Load data for a specific module from the latest session."""
    latest_session = get_latest_session_data()
    if not latest_session:
        return None, None
    
    raw_json_dir = latest_session / "raw_json"
    
    # Find timestamp directories within the session
    timestamp_dirs = [
        d for d in raw_json_dir.iterdir() 
        if d.is_dir() and d.name.count('-') >= 5  # timestamp format
    ]
    
    main_data = None
    line_items_data = None
    
    # Look for the module in timestamp directories
    for timestamp_dir in sorted(timestamp_dirs, reverse=True):
        main_file = timestamp_dir / f"{module_name}.json"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                main_data = json.load(f)
        
        if include_line_items:
            line_items_file = timestamp_dir / f"{module_name}_line_items.json"
            if line_items_file.exists():
                with open(line_items_file, 'r', encoding='utf-8') as f:
                    line_items_data = json.load(f)
        
        # If found in this timestamp, use it
        if main_data:
            break
    
    return main_data, line_items_data

# Example usage
invoices, invoice_line_items = load_module_data("invoices", include_line_items=True)
contacts, _ = load_module_data("contacts")
```

### 2. **Session Metadata Access**

```python
def get_session_info(session_folder):
    """Get metadata about a sync session."""
    session_info_file = session_folder / "session_info.json"
    
    if session_info_file.exists():
        with open(session_info_file, 'r') as f:
            return json.load(f)
    
    return None

def get_session_summary(session_folder):
    """Get summary report of a sync session."""
    summary_file = session_folder / "reports" / "session_summary.json"
    
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            return json.load(f)
    
    return None

# Example usage
latest_session = get_latest_session_data()
session_info = get_session_info(latest_session)
session_summary = get_session_summary(latest_session)

print(f"Session started: {session_info['session_start']}")
print(f"Total records synced: {session_summary.get('summary', {}).get('total_records', 0)}")
```

### 3. **Traditional Data Access** (Legacy Support)

```python
def get_latest_traditional_data():
    """Get data from traditional raw_json structure."""
    raw_json_dir = Path("api_sync/data/raw_json")
    
    if not raw_json_dir.exists():
        return None
    
    # Find latest timestamp directory
    timestamp_dirs = [
        d for d in raw_json_dir.iterdir() 
        if d.is_dir() and d.name.count('-') >= 5
    ]
    
    if not timestamp_dirs:
        return None
    
    return sorted(timestamp_dirs, key=lambda x: x.name, reverse=True)[0]

def load_traditional_module_data(module_name):
    """Load module data from traditional structure."""
    latest_dir = get_latest_traditional_data()
    if not latest_dir:
        return None
    
    module_file = latest_dir / f"{module_name}.json"
    if module_file.exists():
        with open(module_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return None
```

## 📊 Data Freshness & Sync Timestamps

### Understanding Data Age
```python
def get_data_freshness():
    """Check how fresh the latest data is."""
    latest_session = get_latest_session_data()
    if not latest_session:
        return "No data available"
    
    # Extract timestamp from folder name
    timestamp_str = latest_session.name.replace("sync_session_", "")
    sync_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    
    age = datetime.now() - sync_time
    return f"Data is {age.total_seconds() / 3600:.1f} hours old"

print(get_data_freshness())
# Output: "Data is 2.3 hours old"
```

### Incremental vs Full Sync
- **Incremental Sync**: Contains only records modified since the last sync
- **Full Sync**: Contains all records regardless of modification date
- Check `session_info.json` for sync type information

## 🔗 Data Relationships

### Linking Main Records with Line Items
```python
def link_invoices_with_line_items(invoices, line_items):
    """Create a complete invoice structure with embedded line items."""
    invoice_dict = {}
    
    # Index invoices by ID
    for invoice in invoices:
        invoice['line_items'] = []
        invoice_dict[invoice['id']] = invoice
    
    # Attach line items to their parent invoices
    for line_item in line_items:
        parent_id = line_item.get('invoice_id')
        if parent_id in invoice_dict:
            invoice_dict[parent_id]['line_items'].append(line_item)
    
    return list(invoice_dict.values())

# Example usage
invoices, line_items = load_module_data("invoices", include_line_items=True)
complete_invoices = link_invoices_with_line_items(invoices, line_items)
```

## 🚀 Best Practices for Data Consumers

### 1. **Always Use Latest Session Data**
```python
# ✅ GOOD: Use session-based access
latest_session = get_latest_session_data()
data = load_module_data("invoices")

# ❌ AVOID: Hardcoding paths
# data = json.load(open("api_sync/data/raw_json/2025-07-11_10-05-44/invoices.json"))
```

### 2. **Handle Missing Data Gracefully**
```python
def safe_load_data(module_name):
    """Safely load data with fallback handling."""
    try:
        data, line_items = load_module_data(module_name, include_line_items=True)
        
        if data is None:
            print(f"Warning: No data found for module {module_name}")
            return [], []
        
        return data, line_items or []
    
    except Exception as e:
        print(f"Error loading {module_name}: {e}")
        return [], []
```

### 3. **Check Data Freshness**
```python
def ensure_fresh_data(max_age_hours=24):
    """Ensure data is not older than specified hours."""
    latest_session = get_latest_session_data()
    
    if not latest_session:
        raise ValueError("No sync data available")
    
    timestamp_str = latest_session.name.replace("sync_session_", "")
    sync_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    
    age_hours = (datetime.now() - sync_time).total_seconds() / 3600
    
    if age_hours > max_age_hours:
        raise ValueError(f"Data is {age_hours:.1f} hours old (max allowed: {max_age_hours})")
    
    return True
```

### 4. **Efficient Data Processing**
```python
def process_large_dataset(module_name, batch_size=1000):
    """Process large datasets in batches to manage memory."""
    data, _ = load_module_data(module_name)
    
    if not data:
        return
    
    # Process in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        yield batch
        
# Example usage
for batch in process_large_dataset("invoices", batch_size=500):
    # Process each batch
    for invoice in batch:
        # Your processing logic here
        pass
```

## 📈 Monitoring & Health Checks

### Session Health Check
```python
def check_session_health():
    """Perform health check on the latest session."""
    latest_session = get_latest_session_data()
    
    if not latest_session:
        return {"status": "ERROR", "message": "No sessions found"}
    
    session_summary = get_session_summary(latest_session)
    
    if not session_summary:
        return {"status": "WARNING", "message": "No session summary available"}
    
    sync_results = session_summary.get("sync_results", {})
    summary = sync_results.get("summary", {})
    
    if summary.get("success", False):
        return {
            "status": "HEALTHY",
            "modules_succeeded": summary.get("modules_succeeded", 0),
            "total_records": summary.get("total_records", 0),
            "failed_modules": summary.get("failed_modules", [])
        }
    else:
        return {
            "status": "ERROR",
            "message": "Last sync failed",
            "failed_modules": summary.get("failed_modules", [])
        }

# Example usage
health = check_session_health()
print(f"Session status: {health['status']}")
```

## 🛡️ Error Handling

### Common Issues & Solutions

1. **Missing Session Data**
   ```python
   # Always check if session exists
   if not get_latest_session_data():
       print("No sync sessions found. Run API sync first.")
   ```

2. **Empty Module Data**
   ```python
   # Check for empty datasets
   data, _ = load_module_data("invoices")
   if not data:
       print("No invoices found in latest sync")
   ```

3. **Corrupted JSON Files**
   ```python
   # Handle JSON parsing errors
   try:
       with open(json_file, 'r') as f:
           data = json.load(f)
   except json.JSONDecodeError as e:
       print(f"Corrupted JSON file: {e}")
   ```

## 📞 Support & Integration

### For Questions or Issues:
1. Check the `api_sync/README.md` for sync process details
2. Review session logs in `session_folder/logs/`
3. Examine session summaries in `session_folder/reports/`

### Integration Examples:
- **Data Pipeline**: Use session-based data loading for ETL processes
- **Analytics**: Access line items for detailed transaction analysis
- **Reporting**: Monitor data freshness and sync health
- **API Development**: Build REST APIs on top of synced data

---

**Happy Data Consuming! 🚀**

*For technical support or feature requests, please refer to the main project documentation.*
