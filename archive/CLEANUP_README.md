# Root Folder Cleanup

This folder has been cleaned up to improve organization:

## Directory Structure

- **Root Directory**: Contains only essential main entry point scripts and configuration files
- **tools/**: Contains utility scripts organized by function
  - **tools/analysis/**: Scripts for analyzing data
  - **tools/verification/**: Scripts for verifying and validating data
  - **tools/reports/**: Scripts for generating reports
  - **tools/runners/**: Runner scripts for various operations

## Cleanup Summary

- Moved utility scripts from root to appropriate tool subdirectories
- Backed up legacy files to cleanup_backup/
- Maintained proper documentation and configuration files
- Improved organization and maintainability

## Key Files

### Main Entry Points
- Module-specific main entry points in their respective directories:
  - json_db_mapper/main_runner_json_db_mapper.py
  - json_db_mapper/main_wrapper_json_db_mapper.py

### Configuration
- .env* files
- README.md
- requirements.txt

### Documentation
- VIEW_TRACKER.md in json_db_mapper/view_creation/

## Cleanup Benefits
- Cleaner directory structure
- Better organization
- Reduced clutter
- Easier navigation
- Better maintainability
