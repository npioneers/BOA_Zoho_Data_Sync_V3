# Temporary DB Schema Inspection Script

This script (`tmp_db_schema_inspect.py`) was created to inspect the schema of the `Contacts` table in the SQLite database for diagnostics purposes only.

## Usage
Run the script from the project root:

```
python copilot_notes/tmp_db_schema_inspect.py
```

## Output
- Prints the schema of the `Contacts` table in a readable table format.
- Use this to verify which columns are present and identify schema mismatches.

## Cleanup
- Delete `tmp_db_schema_inspect.py` and this README after diagnostics are complete to keep the workspace clean.
