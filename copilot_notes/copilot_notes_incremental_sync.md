# Incremental Sync Investigation

This file contains the full investigation, root cause analysis, and workaround notes for incremental sync and changed record detection.

---

# INCREMENTAL SYNC ENHANCEMENT PLAN

## Overview
We need to implement incremental sync functionality to complement our existing full rebuild system. This will allow the system to fetch only changes since the last successful run, making regular operations much more efficient.

## Required Components

### 1. StateManager Module (src/data_pipeline/state_manager.py)
- **Purpose**: Track and manage sync timestamps
- **Key Methods**:
  - `get_last_sync_time()` - Retrieve last successful sync timestamp
  - `update_last_sync_time(new_time)` - Update timestamp after successful sync
- **Storage**: Uses `config/sync_state.json` for persistence
- **Features**: Thread-safe, handles missing state file gracefully

### 2. Enhanced ZohoClient
- **Modification**: Add `since_timestamp` parameter to data fetching methods
- **API Integration**: Append `last_modified_time` filter to Zoho API requests
- **Backward Compatibility**: Optional parameter, maintains existing full-fetch behavior

### 3. Updated Orchestrator/Main Runner
- **Dual Mode Operation**:
  - `--full-rebuild` flag: Complete rebuild (existing functionality)
  - Default mode: Incremental sync using state manager
- **Workflow**:
  1. Check for `--full-rebuild` flag
  2. If incremental: Get last sync time from StateManager
  3. Fetch data with appropriate filters
  4. Transform and load data (existing UPSERT logic handles updates)
  5. Update sync state on success

## Benefits
- **Efficiency**: Only fetch changed records
- **Performance**: Faster sync times for regular operations
- **Flexibility**: Maintains full rebuild capability when needed
- **Reliability**: State tracking ensures no data loss

## Implementation Priority
1. StateManager module (foundation)
2. ZohoClient enhancements (API integration)
3. Orchestrator updates (workflow coordination)
4. CLI interface updates
5. Testing and validation
