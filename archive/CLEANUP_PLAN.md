# FOLDER CLEANUP PLAN - July 12, 2025

## ANALYSIS OF CURRENT STATE

### Files to Keep (Production/Core)
- README.md
- requirements.txt
- .env, .env.example, .env.json_sync.example
- .gitignore, .git/, .github/, .vscode/
- main_api_sync.py (core functionality)
- database.db (production database)
- api_sync/ (core package)
- json2db_sync/ (core package)
- csv_db_rebuild/ (core package)
- data/ (production data)
- logs/ (important logs)
- output/ (output directory)
- reports/ (reports directory)
- src/ (source code)
- tools/ (utility tools)
- json_db_mapper/ (core package)
- gcp-service-key.json (credentials)
- copilot_notes_remarks.md (documentation)
- DUPLICATE_PREVENTION_COMPLETION_SUMMARY.md (documentation)
- CLEANUP_README.md (documentation)

### Files to Archive (Test/Development)
- All test_*.py files (development tests)
- All *_test_results.json files (test outputs)
- All *.log files (except those in logs/ directory)
- test_database.db (test database)
- demo_*.py files (demo scripts)
- interactive_*.py files (demo scripts)
- debug_*.py files (debug scripts)
- quick_*.py files (quick test scripts)
- emergency_*.py files (emergency test scripts)
- hardcoded_*.py files (hardcoded test scripts)
- zoho_api_analysis.py (analysis script)
- clear_cache.py (utility script)

### Files to Remove (Temporary/Obsolete)
- main_api_sync_menu.py (old version)
- main_api_sync_menu_new.py (development version)

## CLEANUP ACTIONS

1. Create archive directory for test files
2. Move test files to archive
3. Remove obsolete files
4. Organize remaining structure
5. Update documentation
