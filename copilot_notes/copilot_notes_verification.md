# Verification Plan & Results

## VERIFICATION PLAN FOR REFACTORED PACKAGE 🧪

### 🎯 VERIFICATION OBJECTIVES
1. **Package Import Test**: Verify all refactored components can be imported
2. **Configuration Loading**: Test configuration hierarchy and path resolution
3. **Data Source Validation**: Confirm CSV and JSON sources exist and are accessible
4. **Full Pipeline Execution**: Run complete cockpit notebook end-to-end
5. **Database Validation**: Verify canonical schema creation and data loading
6. **Results Verification**: Confirm data integrity and completeness

### 📋 STEP-BY-STEP EXECUTION PLAN
**Phase 1**: Pre-flight checks (verify environment and data sources)  
**Phase 2**: Package component testing (import and initialization)  
**Phase 3**: Full pipeline execution (run cockpit notebook)  
**Phase 4**: Post-execution validation (verify results)  

### 🔧 VERIFICATION COMMANDS
Will provide terminal commands for each verification step

---

## JSON/DB Sync Diagnostics & Blockers (2025-07-06)

### Missing JSON Files (Latest Directory: 2025-07-06_08-28-34)
- Only `contacts.json` is present in the latest folder.
- The following expected files are missing:
    - items.json
    - bills.json
    - invoices.json
    - salesorders.json
    - purchaseorders.json
    - creditnotes.json
    - customerpayments.json
    - vendorpayments.json

### Schema Mismatch Errors (from sync logs)
- Example: `table Contacts has no column named CustomerSubType`
    - The database schema for `Contacts` is missing the `CustomerSubType` column, which is present in the JSON mapping.
- Similar issues may exist for other entities if/when their JSON files are present.

### Action Checklist (Non-Destructive, No Critical File Edits)
1. **Data Blocker:**
   - Export all required JSON files to the latest `data/json/raw_json/<latest-date>/` directory.
   - Required files (example):
     - contacts.json (present)
     - items.json
     - bills.json
     - invoices.json
     - salesorders.json
     - purchaseorders.json
     - creditnotes.json
     - customerpayments.json
     - vendorpayments.json
   - _Action:_ Use your export pipeline or manual copy to ensure all above files are present before running sync.

2. **Schema Blocker:**
   - Review sync logs for missing columns (e.g., `CustomerSubType` in Contacts).
   - Prepare a list of required schema changes (do not apply yet):
     - For each error, note the table and missing column.
   - _Action:_ Plan schema migrations or manual ALTER TABLE statements, but do not execute until reviewed.

3. **Verification Plan:**
   - After data and schema are aligned, run:
     - `python main_json2db.py status` (before)
     - `python main_json2db.py sync`
     - `python main_json2db.py status` (after)
   - Confirm that counts update and no schema/data errors are reported.

### Diagnostics Summary
- Only `contacts.json` present in latest raw_json directory; all other expected files missing.
- Sync failed to insert due to missing JSON data and schema mismatch (e.g., missing `CustomerSubType` column in Contacts table).
- No changes made to mappings or schema files (diagnostics only).

_This section tracks active blockers and next steps for JSON/DB sync. Move resolved items to the appropriate sub-file when complete._

---

## API Sync Environment Setup & Test (2025-07-06)

### Environment Setup
- Created `.env` in the project root from `.env.example`.
- Required variables:
    - `GCP_PROJECT_ID` (mandatory)
    - `GOOGLE_APPLICATION_CREDENTIALS` (optional, for GCP auth)
    - `ZOHO_ORGANIZATION_ID` (optional, for Zoho Books)
- **Action:** Fill in your actual values in `.env` before running API sync.

### Test Plan
1. Fill in `.env` with valid credentials and IDs.
2. Run the following command to fetch data for a module (e.g., contacts):
   ```powershell
   python -m src.api_sync fetch contacts
   ```
3. Repeat for other modules as needed (e.g., items, bills, etc.).
4. Verify that new JSON files are created in the latest `data/raw_json/<timestamp>/` directory.

### Troubleshooting
- If you see errors about missing environment variables, double-check your `.env` file and variable names.
- If authentication fails, verify your GCP credentials and organization ID.

---
