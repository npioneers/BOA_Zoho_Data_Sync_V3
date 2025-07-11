# Quick Reference: Data Consumer APIs

## 🚀 Quick Start

```python
from pathlib import Path
import json

# 1. Get Latest Session
sessions_dir = Path("api_sync/data/sync_sessions")
latest_session = sorted([f for f in sessions_dir.iterdir() if f.is_dir()], reverse=True)[0]

# 2. Load Module Data
def load_data(module_name):
    raw_json_dir = latest_session / "raw_json"
    for timestamp_dir in raw_json_dir.iterdir():
        file_path = timestamp_dir / f"{module_name}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    return None

# 3. Quick Data Access
invoices = load_data("invoices")
items = load_data("items") 
contacts = load_data("contacts")
```

## 📊 Available Modules

| Module | Has Line Items | Example Usage |
|--------|----------------|---------------|
| `invoices` | ✅ | Customer billing |
| `bills` | ✅ | Vendor expenses |
| `salesorders` | ✅ | Sales pipeline |
| `purchaseorders` | ✅ | Procurement |
| `creditnotes` | ✅ | Refunds/adjustments |
| `items` | ❌ | Product catalog |
| `contacts` | ❌ | Customer database |
| `customerpayments` | ❌ | Payment tracking |
| `vendorpayments` | ❌ | Vendor payments |

## 🔗 Data Structure

**Session Path**: `api_sync/data/sync_sessions/sync_session_YYYY-MM-DD_HH-MM-SS/`

```
session_folder/
├── session_info.json      # Metadata
├── raw_json/             # Actual data
│   ├── timestamp_dir_1/  # Module batch 1
│   ├── timestamp_dir_2/  # Module batch 2
│   └── ...
└── reports/
    └── session_summary.json  # Sync summary
```

## 🎯 One-Liners

```python
# Get session age in hours
age = (datetime.now() - datetime.strptime(latest_session.name[-19:], "%Y-%m-%d_%H-%M-%S")).total_seconds() / 3600

# Check if data exists
has_invoices = any((latest_session / "raw_json" / d / "invoices.json").exists() for d in (latest_session / "raw_json").iterdir())

# Count total records
total = sum(len(json.load(open(f))) for f in (latest_session / "raw_json").rglob("*.json"))
```

## ⚠️ Best Practices

- ✅ Always use latest session
- ✅ Handle missing data gracefully  
- ✅ Check data freshness
- ❌ Don't hardcode paths
- ❌ Don't assume files exist
