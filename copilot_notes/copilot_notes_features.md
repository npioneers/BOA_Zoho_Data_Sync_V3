# Feature Requests & Enhancements

This file contains all feature requests, enhancement ideas, and their implementation status.

---

(You can move the feature request and enhancement details here from the cockpit if you want to keep the cockpit concise.)

## FEATURE REQUEST: Dynamic Source Path Resolution 🔄

### 📋 PROBLEM STATEMENT
The current settings.yaml requires hardcoded paths to specific timestamped data folders. This is not ideal for automation since new data dumps create new timestamped directories.

### 🎯 PROPOSED SOLUTION
**Enhanced Dynamic Path Resolution for Both CSV and JSON Sources**

1. **CSV Backup Paths**: If csv_backup_path is set to 'LATEST', automatically find the most recent timestamped directory in data/csv/
2. **JSON API Paths**: If json_api_path is set to 'LATEST', automatically find the most recent timestamped directory in data/raw_json/

### 🔧 IMPLEMENTATION APPROACH
- Create utility function `find_latest_timestamped_directory()` in config.py
- Support timestamp patterns: YYYY-MM-DD_HH-MM-SS and "Company Name_YYYY-MM-DD"
- Enhance `get_data_source_paths()` method to resolve 'LATEST' dynamically
- Maintain backward compatibility with explicit paths

### 📊 ACTUAL DATA STRUCTURE DISCOVERED
**CSV Directories**: `data/csv/Nangsel Pioneers_2025-06-22/`
**JSON Directories**: 
- `data/raw_json/2025-07-04_15-27-24/`
- `data/raw_json/2025-07-05_09-15-30/`
- `data/raw_json/2025-07-05_09-30-15/`
- `data/raw_json/2025-07-05_14-45-22/`
- `data/raw_json/2025-07-05_16-20-31/`
