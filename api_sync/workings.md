# API Data Fetching and Verification Process

## Overview

This document outlines how the Data Sync application fetches data from the Zoho Books API and verifies the completeness of that data in the local storage system.

## API Data Fetching Flow

1. **Authentication Process**
   - The system loads Zoho API credentials from Google Cloud Secret Manager
   - It exchanges the refresh token for a temporary access token
   - The access token is used for all subsequent API calls

2. **Core Data Fetching**
   - The primary class responsible for API communication is `ZohoClient` in `src/data_sync/core/client.py`
   - The main method for fetching data is `ZohoClient.get_data_for_module(module_name, since_timestamp)`
   - This method handles API pagination automatically, fetching all records for the specified module

3. **Local Storage**
   - After fetching data, the raw JSON is saved using `raw_data_handler.save_raw_json()` in `src/data_sync/processing/raw_data_handler.py`
   - Raw data is stored in a timestamp-based folder structure: `output/raw_json/{timestamp}/{module_name}.json`

## Key Components

### 1. Authentication Layer (`src/data_sync/core/auth.py`)

This module handles the OAuth2 authentication flow:
- It uses the refresh token to get a new access token
- Error handling for authentication failures
- Automatic token refresh when needed

### 2. Secrets Management (`src/data_sync/core/secrets.py`)

This module securely retrieves API credentials:
- Fetches credentials from Google Cloud Secret Manager
- Supports local development via environment variables as fallback
- Required credentials: `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`

### 3. API Client (`src/data_sync/core/client.py`)

The `ZohoClient` class handles all API communication:
- Provides methods for fetching different data types
- Handles pagination automatically with `_get_all_pages()`
- Contains specific methods for fetching detailed records (`get_salesorder_details()`, `get_bill_details()`)
- Implements rate limiting and error handling for API requests

### 4. Raw Data Storage (`src/data_sync/processing/raw_data_handler.py`)

This module manages saving the raw API data:
- Creates timestamp-based folder structure
- Saves JSON with proper formatting and encoding
- Optional preprocessing for complex data fields

## Verification Process

The verification system compares API data with locally stored data to ensure completeness:

1. **Verification Tool** (`verification/verify_api_vs_local.py`)
   - Connects to the API to get current record counts for each module
   - Compares these counts with local JSON data
   - Reports any discrepancies between API and local storage

2. **Verification Steps**
   - Authenticate with the Zoho API
   - For each module (invoices, bills, contacts, etc.):
     - Count records available in the API
     - Count records in the local JSON storage
     - Compare the counts and report differences
   - For documents with line items (invoices, bills, sales orders):
     - Verify that detailed records were downloaded
     - Estimate the total number of line items

3. **Verification Output**
   - Summary of API vs local record counts
   - List of any modules with mismatches
   - Recommendations for further action (re-download missing data)

## API-Only Fetch Tool

The system includes a specialized tool (`api_only_fetch.py`) for fetching only the API data:
- Fetches data from a specific module without any database operations
- Saves raw JSON directly to the output folder
- Performs quick analysis of the fetched data
- Useful for diagnosing issues with API data structure

## Usage Guidelines

1. **Authentication Setup**
   - Ensure Google Cloud authentication is configured
   - Required environment variable: `GCP_PROJECT_ID` in a `.env` file

2. **Running API Verification**
   - Use `verify_api_vs_local.py` to check for data completeness
   - Review the verification report for any discrepancies
   - Re-download data for any modules with mismatches

3. **Fetching Fresh API Data**
   - Use `api_only_fetch.py` to download raw data from a specific module
   - Examine the saved JSON files to understand API data structure
   - Use this approach for troubleshooting API-related issues

## Troubleshooting

1. **Authentication Issues**
   - Check that GCP credentials are properly configured
   - Verify that the service account has Secret Manager access
   - Ensure Zoho API credentials are valid and not expired

2. **Missing Data**
   - Run verification to identify which modules have incomplete data
   - Use `api_only_fetch.py` to re-download specific modules
   - Check API permissions for modules with "NO_PERMISSION" errors

3. **Rate Limiting**
   - The client automatically handles rate limiting with delays
   - For large datasets, consider increasing delay parameters
   - Monitor API usage limits in the Zoho Developer Console
