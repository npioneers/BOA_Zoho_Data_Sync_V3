# JSON-DB Mapper

A comprehensive package for analyzing and mapping field structures between CSV-uploaded tables and JSON-uploaded tables in SQLite databases.

## Overview

The JSON-DB Mapper helps analyze database schemas and create mapping tables to understand the relationship between CSV tables and JSON tables (prefixed with `json_`). This is essential for data synchronization and transformation operations.

## Features

- **Table Structure Analysis**: Automatically categorizes and analyzes all tables in a database
- **Mapping Table Creation**: Creates standardized mapping tables for both CSV and JSON sources
- **Field Information Extraction**: Captures field names, types, constraints, and positions
- **CLI Interface**: Easy-to-use command line interface for all operations
- **Comprehensive Logging**: Detailed logs for all operations and errors
- **Configuration-Driven**: No hardcoded values, externalized configuration

## Package Structure

```
json_db_mapper/
├── __init__.py
├── table_structure_analyzer.py    # Analyzes database table structures
├── mapping_table_creator_new.py   # Creates and populates mapping tables
├── runner.py                      # CLI interface
└── README.md                      # This file
```

## Installation

No additional installation required - uses Python standard library and sqlite3.

## Usage

### CLI Commands

#### 1. Analyze Tables in a Database
```bash
python runner.py analyze --db "path/to/database.db"
```

#### 2. Create Mapping Tables for a Database
```bash
python runner.py create-maps --db "path/to/database.db"
```

#### 3. Full Analysis (Both Databases)
```bash
python runner.py full
```

#### 4. Help
```bash
python runner.py --help
```

### Default Database Paths

The system uses these default paths:
- **Production DB**: `../backups/production_db_refactor_complete_20250707_211611.db`
- **JSON Sync DB**: `../backups/json_sync_backup_20250707_222640.db`

### Custom Database Paths

For the full analysis with custom paths:
```bash
python runner.py full --production-db "path/to/production.db" --json-db "path/to/json.db"
```

## Output

### Mapping Tables Created

The system creates mapping tables with this schema:
- `id` - Primary key
- `field_name` - Name of the field
- `field_type` - Data type of the field
- `max_length` - Maximum length (if applicable)
- `is_nullable` - Whether field allows NULL values
- `is_primary_key` - Whether field is a primary key
- `field_position` - Position of field in table
- `sample_values` - Sample values (for future enhancement)
- `field_description` - Description (for future enhancement)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Example Mapping Tables Created

**CSV Tables (9 tables):**
- `map_csv_bills` (66 fields)
- `map_csv_contacts` (74 fields)
- `map_csv_credit_notes` (89 fields)
- `map_csv_customer_payments` (31 fields)
- `map_csv_invoices` (124 fields)
- `map_csv_items` (43 fields)
- `map_csv_purchase_orders` (77 fields)
- `map_csv_sales_orders` (85 fields)
- `map_csv_vendor_payments` (30 fields)

**JSON Tables (15 tables):**
- `map_json_bills` (37 fields)
- `map_json_contacts` (53 fields)
- `map_json_invoices` (60 fields)
- `map_json_items` (46 fields)
- `map_json_organizations` (92 fields)
- `map_json_purchase_orders` (108 fields)
- And more...

## Logging

All operations are logged to the `logs/` directory with timestamps:
- `table_structure_analyzer_YYYYMMDD_HHMMSS.log`
- `mapping_table_creator_YYYYMMDD_HHMMSS.log`
- `json_db_mapper_cli_YYYYMMDD_HHMMSS.log`

## Development Status

✅ **Phase 1 COMPLETE**: Skeleton mapping tables created and tested
- Table structure analysis working
- Mapping table creation working
- CLI interface working
- All field information properly extracted

🔄 **Next Phase**: Field mapping logic implementation
- Compare fields between CSV and JSON tables
- Implement actual mapping algorithms
- Add field comparison and analysis features

## Error Handling

The system includes comprehensive error handling:
- Database connection validation
- Table existence checks
- Field extraction error handling
- Logging of all errors and warnings

## Configuration

The system follows configuration-driven design principles:
- Database paths can be specified via CLI arguments
- No hardcoded values in the application logic
- Sensible defaults for common use cases

## Features

### Mapping Table Creation
- **CSV Mapping Tables**: Creates `csv_{entity}_map` tables for each CSV entity
- **JSON Mapping Tables**: Creates `{json_entity}_map` tables for each JSON entity
- **Automated Indexing**: Creates performance indexes on key fields
- **Schema Consistency**: Standardized schema across all mapping tables

### Supported Entities

#### CSV Entities (10 tables):
- `csv_bills_map`
- `csv_contacts_map` 
- `csv_credit_notes_map`
- `csv_customer_payments_map`
- `csv_invoices_map`
- `csv_items_map`
- `csv_organizations_map`
- `csv_purchase_orders_map`
- `csv_sales_orders_map`
- `csv_vendor_payments_map`

#### JSON Entities (15 tables):
- `json_bills_map`
- `json_contacts_map`
- `json_credit_notes_map`
- `json_customer_payments_map`
- `json_invoices_map`
- `json_items_map`
- `json_organizations_map`
- `json_purchase_orders_map`
- `json_sales_orders_map`
- `json_vendor_payments_map`
- `json_bills_line_items_map`
- `json_creditnotes_line_items_map`
- `json_invoices_line_items_map`
- `json_purchaseorders_line_items_map`
- `json_salesorders_line_items_map`

## Mapping Table Schema

Each mapping table contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing unique identifier |
| `field_name` | VARCHAR(255) | Name of the field in the source table |
| `field_order` | INTEGER | Order/position of the field |
| `data_type` | VARCHAR(50) | Data type of the field |
| `max_length` | INTEGER | Maximum length for string fields |
| `is_nullable` | BOOLEAN | Whether the field can contain NULL values |
| `is_primary_key` | BOOLEAN | Whether the field is part of primary key |
| `sample_values` | TEXT | Sample values from the field |
| `description` | TEXT | Field description or notes |
| `created_timestamp` | DATETIME | When the mapping was created |
| `updated_timestamp` | DATETIME | When the mapping was last updated |

## Usage

### Command Line Interface

```bash
# Create all mapping tables (both CSV and JSON)
python main_json_db_mapper.py --create-tables

# Create only CSV mapping tables
python main_json_db_mapper.py --create-csv-tables

# Create only JSON mapping tables  
python main_json_db_mapper.py --create-json-tables

# Verify mapping tables exist
python main_json_db_mapper.py --verify-tables

# Use custom database path
python main_json_db_mapper.py --create-tables --db-path "custom/path/database.db"
```

### Python API

```python
from json_db_mapper.mapping_table_creator import MappingTableCreator

# Initialize creator
creator = MappingTableCreator(db_path="data/database/production.db")

# Create all mapping tables
results = creator.create_all_mapping_tables()

# Print summary
creator.print_mapping_tables_summary(results)

# Verify tables were created
verification = creator.verify_mapping_tables()
print(f"Verified {verification['total_verified']} mapping tables")
```

## File Structure

```
json_db_mapper/
├── __init__.py                    # Package initialization
├── mapping_table_creator.py      # Core mapping table creation logic
└── README.md                     # This documentation

main_json_db_mapper.py            # Command-line interface
```

## Next Steps

After creating the mapping table skeletons:

1. **Populate Mapping Data**: Analyze actual CSV and JSON files to populate field information
2. **Schema Analysis**: Implement automated detection of field types and constraints
3. **Field Mapping**: Create relationships between CSV and JSON fields
4. **Validation**: Implement validation of mapping data integrity
5. **Migration Tools**: Build tools to sync schema changes

## Logging

All operations are logged to `logs/mapping_table_creator_{timestamp}.log` with detailed information about:
- Table creation progress
- Index creation
- Error handling
- Verification results

## Error Handling

The package includes comprehensive error handling:
- Database connection errors
- SQL execution errors
- Missing table detection
- Graceful failure with detailed error messages
