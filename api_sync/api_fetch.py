#!/usr/bin/env python3
"""
API-Only Fetch Script
===================
Fetches fresh data from the Zoho API and saves to JSON only.
No database operations, no transformations - just raw API data.
"""

import sys
import os
from datetime import datetime
import argparse
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import core modules
from data_sync.core import secrets, auth, client
from data_sync.processing import raw_data_handler

def main():
    """Fetch data from API and save to JSON only."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch data from Zoho API and save to JSON")
    parser.add_argument("module", choices=["invoices", "items", "contacts", "customerpayments", 
                                          "bills", "vendorpayments", "salesorders", "purchaseorders", 
                                          "creditnotes", "organizations"], 
                       help="The Zoho module to fetch data from")
    parser.add_argument("--since", help="Only fetch records modified since this timestamp (YYYY-MM-DDThh:mm:ss+0000)")
    parser.add_argument("--config", default="config.json", help="Path to the config file (default: config.json)")
    
    args = parser.parse_args()
    
    print(f"🔍 API-ONLY FETCH: {args.module.upper()}")
    print("=" * 60)
    print("Purpose: Fetch raw API data and save to JSON")
    print("No database operations will be performed")
    print("=" * 60)
    
    run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    try:
        # Load configuration
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            # Default configuration if file not found
            config = {
                "zoho": {
                    "api_base_url": "https://www.zohoapis.com/books/v3",
                }
            }
            print(f"⚠️ Config file '{args.config}' not found. Using default configuration.")
        
        # Get Zoho configuration
        zoho_api_url = config.get('zoho', {}).get('api_base_url', "https://www.zohoapis.com/books/v3")
        
        # --- 1. Authentication ---
        print("\n--- Step 1: Authentication ---")
        zoho_credentials = secrets.get_zoho_credentials()
        access_token = auth.get_access_token(zoho_credentials)
        zoho_org_id = zoho_credentials.get('organization_id')
        print("✅ Authentication successful")
        
        # --- 2. Initialize API Client ---
        print("\n--- Step 2: Initializing API Client ---")
        zoho_client = client.ZohoClient(access_token, zoho_org_id, zoho_api_url)
        print("✅ API client initialized")
        
        # --- 3. Fetch Fresh Data ---
        print(f"\n--- Step 3: Fetching Fresh {args.module} Data ---")
        if args.since:
            print(f"Requesting {args.module} modified since {args.since}")
        else:
            print(f"Requesting ALL {args.module} (no incremental filter)")
        
        # Fetch all records with optional timestamp filter
        records = zoho_client.get_data_for_module(args.module, since_timestamp=args.since)
        
        if not records:
            print(f"⚠️ No {args.module} found in API response")
            return False
        
        print(f"✅ Retrieved {len(records)} {args.module} records from API")
        
        # --- 4. Save Raw JSON Only ---
        print("\n--- Step 4: Saving Raw JSON (No Processing) ---")
        raw_data_handler.save_raw_json(records, args.module, run_timestamp)
        
        # --- 5. Quick Analysis of Fetched Data ---
        print("\n--- Step 5: Quick Analysis ---")
        print(f"📊 Total records fetched: {len(records)}")
        
        # Check for line items in documents that might have them
        if args.module in ['invoices', 'bills', 'salesorders', 'purchaseorders', 'creditnotes']:
            line_items_found = 0
            sample_record_with_lines = None
            
            for i, record in enumerate(records[:10]):  # Check first 10 records
                if 'line_items' in record and record['line_items']:
                    line_items_found += 1
                    if sample_record_with_lines is None:
                        sample_record_with_lines = record
                        
            print(f"📋 Records with line_items in first 10: {line_items_found}")
            
            if sample_record_with_lines:
                print(f"📝 Sample record with line items:")
                print(f"   - ID: {sample_record_with_lines.get(f'{args.module[:-1]}_id', 'N/A')}")
                print(f"   - Number: {sample_record_with_lines.get(f'{args.module[:-1]}_number', 'N/A')}")
                print(f"   - Line items count: {len(sample_record_with_lines.get('line_items', []))}")
                
                # Show first line item structure
                if sample_record_with_lines.get('line_items'):
                    first_line_item = sample_record_with_lines['line_items'][0]
                    print(f"   - First line item keys: {list(first_line_item.keys())}")
            else:
                print("⚠️ No line items found in first 10 records - bulk API may not include line items")
        
        # --- 6. Summary ---
        print("\n" + "=" * 60)
        print("📁 RAW JSON SAVED TO:")
        output_path = os.path.join('output', 'raw_json', run_timestamp, f"{args.module}.json")
        print(f"   {output_path}")
        print("\n✅ API-ONLY FETCH COMPLETED")
        print("🔍 Next: Inspect the saved JSON file to verify data structure")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ API fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
