# Table Analysis Generation Guide

## Overview

This document explains how the **Detailed Table Analysis** feature works in the JSON2DB Sync system. This analysis provides comprehensive insights into database tables, including row counts, date ranges, and sync status information.

## Sample Output

```
📋 DETAILED TABLE ANALYSIS
---------------------------------------------------------------------------------------------------------
Table Name                     Row Count    Oldest Data          Latest Data          Last Sync
---------------------------------------------------------------------------------------------------------
✅ csv_bills                    3,097        2023-01-01           2025-06-13           Source: csv
✅ csv_contacts                 224          2023-04-02 20:42:01  2025-06-21 16:56:53  N/A
✅ csv_credit_notes             738          2023-08-15           2025-06-18           Source: csv
✅ csv_customer_payments        1,694        2023-01-31           2025-07-11           Source: csv
✅ csv_invoices                 6,696        2023-01-31           2025-06-21           Source: csv
✅ csv_items                    925          2025-07-08 00:34:36  2025-07-08 00:34:36  N/A
❌ csv_organizations            0            N/A                  N/A                  N/A
✅ csv_purchase_orders          2,875        2023-07-27           2025-06-14           Source: csv
✅ csv_sales_orders             5,509        2023-09-04           2025-06-21           Source: csv
✅ csv_vendor_payments          526          2023-01-01           2025-06-20           Source: csv
```

## How It Works

### 1. Database Connection & Table Discovery

The system connects to the SQLite database and discovers all user-created tables:

```python
# Connect to SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all user tables (excluding system tables)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
```

### 2. Per-Table Analysis Process

For each discovered table, the system performs the following analysis:

#### A. Row Count Calculation
```python
cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
row_count = cursor.fetchone()[0]
```

#### B. Smart Business Date Column Selection

The system uses intelligent business logic to find the most meaningful date column for each table type:

**Priority 1: Document-Specific Business Dates**
- **Invoices** → looks for `invoice_date`, then `date`
- **Bills** → looks for `bill_date`, then `date`  
- **Sales Orders** → looks for `salesorder_date`, `order_date`, then `date`
- **Purchase Orders** → looks for `purchaseorder_date`, then `date`
- **Credit Notes** → looks for `creditnote_date`, then `date`
- **Payments** → looks for `payment_date`, then `date`

**Priority 2: Generic Business Date**
- Falls back to `date` column if no specific business date found

**Priority 3: System Dates (Last Resort)**
- `created_time`, `last_modified_time`, `updated_time`, etc.

#### C. Date Range Extraction

Once the best date column is identified, the system extracts the temporal range:

```python
# Get oldest date
cursor.execute(f"SELECT MIN(`{primary_date_col}`) FROM `{table_name}` WHERE `{primary_date_col}` IS NOT NULL")
oldest_date = cursor.fetchone()[0]

# Get latest date  
cursor.execute(f"SELECT MAX(`{primary_date_col}`) FROM `{table_name}` WHERE `{primary_date_col}` IS NOT NULL")
latest_date = cursor.fetchone()[0]
```

#### D. Last Sync Information

The system checks for sync metadata in this priority order:

1. **Sync Timestamp**: If `last_sync_time` column exists
2. **Data Source**: If `data_source` column exists, shows "Source: csv" or similar

### 3. Display Formatting Logic

#### Status Indicators
```python
status_emoji = "✅" if table.get('row_count', 0) > 0 else "❌"
```
- ✅ = Table has data (row_count > 0)
- ❌ = Table is empty (row_count = 0)

#### Column Formatting Rules

**Table Name**: Truncated to 28 characters (leaves room for emoji)
```python
if len(table_name) > 28:
    table_name = table_name[:25] + "..."
```

**Row Count**: Comma-separated formatting for readability
```python
row_count = f"{table.get('row_count', 0):,}"
```

**Dates**: Truncated to 19 characters (YYYY-MM-DD HH:MM:SS format)
```python
oldest_date = str(table.get('oldest_date', 'N/A'))[:19]
latest_date = str(table.get('latest_date', 'N/A'))[:19]
```

## Business Date Logic Implementation

### Smart Column Detection Method

```python
def _get_business_date_column(self, table_name: str, columns: List[str]) -> Optional[str]:
    """
    Get the most appropriate business date column for a table.
    Prioritizes business document dates over system sync dates.
    """
    table_lower = table_name.lower()
    
    # 1. Document-specific business dates (HIGHEST PRIORITY)
    if 'invoice' in table_lower:
        for col in ['invoice_date', 'date']:
            if col in columns: 
                return col
                
    elif 'bill' in table_lower:
        for col in ['bill_date', 'date']:
            if col in columns: 
                return col
                
    elif 'salesorder' in table_lower or 'sales_order' in table_lower:
        for col in ['salesorder_date', 'order_date', 'date']:
            if col in columns: 
                return col
                
    elif 'purchaseorder' in table_lower or 'purchase_order' in table_lower:
        for col in ['purchaseorder_date', 'purchase_order_date', 'date']:
            if col in columns: 
                return col
                
    elif 'creditnote' in table_lower or 'credit_note' in table_lower:
        for col in ['creditnote_date', 'credit_note_date', 'date']:
            if col in columns: 
                return col
                
    elif any(term in table_lower for term in ['payment', 'customerpayment', 'vendorpayment']):
        for col in ['payment_date', 'date']:
            if col in columns: 
                return col
    
    # 2. Generic business date (MEDIUM PRIORITY)
    if 'date' in columns:
        return 'date'
    
    # 3. System dates (LOWEST PRIORITY - only if no business date available)
    for sys_date in ['created_time', 'last_modified_time', 'updated_time', 'modified_time', 'created_timestamp', 'updated_timestamp']:
        if sys_date in columns:
            return sys_date
            
    return None
```

## Real-World Example Analysis

For the `csv_bills` table with 3,097 rows:

1. **Row Count**: Query `SELECT COUNT(*) FROM csv_bills` → 3,097
2. **Business Date Column**: Table name contains "bill" → looks for `bill_date` → found!
3. **Date Range**: 
   - `SELECT MIN(bill_date) FROM csv_bills` → "2023-01-01"
   - `SELECT MAX(bill_date) FROM csv_bills` → "2025-06-13"
4. **Sync Info**: Found `data_source` column → "Source: csv"
5. **Status**: 3,097 > 0 → ✅ emoji

**Final Display**:
```
✅ csv_bills                    3,097        2023-01-01           2025-06-13           Source: csv
```

## Key Features & Benefits

### 🎯 **Intelligent Business Logic**
- **Prioritizes actual business dates** over system timestamps
- **Understands document types** and their relevant dates
- **Provides meaningful temporal insights** for business data

### 📊 **Professional Display**
- **Visual status indicators**: Immediate feedback with ✅/❌ emojis
- **Consistent formatting**: Fixed-width columns for professional appearance
- **Robust error handling**: Shows "N/A" or "Error" for missing/invalid data

### 🔍 **Comprehensive Insights**
- **Data Coverage**: Which tables have data vs. are empty
- **Temporal Range**: The age and freshness of business information
- **Audit Trail**: Data source tracking for audit purposes
- **Business Context**: Focuses on business-relevant dates, not technical sync times

## Source Code Locations

### Core Implementation Files:
- **`runner_json2db_sync.py`**: Contains `_generate_table_summary_report()` method
- **`main_json2db_sync.py`**: Contains display formatting logic around line 466
- **Business date logic**: `_get_business_date_column()` method in runner

### Key Methods:
1. **`_generate_table_summary_report()`**: Main analysis engine
2. **`_get_business_date_column()`**: Smart date column selection
3. **Display formatting**: Professional table rendering in main wrapper

## Error Handling

The system includes robust error handling for:
- **Missing database files**: Clear error messages
- **Invalid date formats**: Graceful fallback to "N/A"
- **Missing columns**: Skips unavailable date columns
- **Database connection issues**: Proper exception handling
- **Corrupted tables**: Individual table error reporting

## Performance Considerations

- **Efficient queries**: Uses MIN/MAX aggregations instead of full table scans
- **Column introspection**: Uses PRAGMA table_info for schema discovery
- **Lazy evaluation**: Only analyzes tables that exist and have data
- **Memory efficient**: Processes one table at a time

## Customization Options

The system can be extended to:
- **Add new document types**: Extend business date logic
- **Custom date formats**: Modify date parsing logic
- **Additional metadata**: Include more sync information
- **Export formats**: Add CSV, JSON export options

---

*This analysis system provides immediate, actionable insights into your database state, focusing on business-relevant information rather than technical metadata.*
