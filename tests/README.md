# Tests Directory

This directory contains all test files and verification scripts for the Zoho Data Sync V3 project.

## Test Categories

### Integration Tests
- `test_json2db_sync_end_to_end.py` - End-to-end testing of JSON to database sync
- `test_duplicate_prevention_integration.py` - Integration tests for duplicate prevention
- `test_production_duplicate_prevention.py` - Production-level duplicate prevention tests

### Behavior Tests  
- `test_incremental_behavior.py` - Testing incremental sync behavior
- `test_interruption_handling.py` - Testing system interruption handling
- `test_interruption_handling_v2.py` - Enhanced interruption handling tests
- `test_two_phase_commit.py` - Two-phase commit transaction tests

### Component Tests
- `test_cutoff_updates.py` - Testing cutoff date logic
- `test_directory_logic.py` - Directory handling logic tests
- `test_runner_backend.py` - Backend runner functionality tests
- `test_runner_direct.py` - Direct runner tests
- `test_timestamp_fix.py` - Timestamp correction tests
- `test_timestamp_function.py` - Timestamp function tests
- `test_transformation.py` - Data transformation tests

### Verification Scripts
- `verify_data_timestamps.py` - Data timestamp verification utility
- `verify_reimport_success.py` - Reimport operation verification

## Running Tests

To run all tests:
```bash
python -m pytest tests/
```

To run specific test categories:
```bash
# Integration tests
python -m pytest tests/test_*integration*.py

# Behavior tests  
python -m pytest tests/test_*behavior*.py tests/test_*interruption*.py

# Component tests
python -m pytest tests/test_runner*.py tests/test_timestamp*.py
```

## Verification Scripts

The verification scripts can be run standalone to check data integrity:
```bash
python tests/verify_data_timestamps.py
python tests/verify_reimport_success.py
```
