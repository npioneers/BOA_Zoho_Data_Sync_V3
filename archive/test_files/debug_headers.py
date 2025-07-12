#!/usr/bin/env python3
"""
Debug header count issue - check what's actually being sent to Zoho API
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from api_sync.core import secrets, auth
    from api_sync.utils import ensure_zoho_timestamp_format
    import requests
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    def debug_api_parameters():
        """Debug what parameters are actually sent to the API"""
        print("=" * 60)
        print("DEBUGGING API PARAMETERS FOR HEADERS")
        print("=" * 60)
        
        # Get credentials
        try:
            zoho_credentials = secrets.get_zoho_credentials()
            access_token = auth.get_access_token(zoho_credentials)
            organization_id = zoho_credentials.get('organization_id') or '806931205'
        except Exception as e:
            print(f"❌ Failed to get credentials: {e}")
            return
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }
        
        # Test different date formats and parameters
        test_cases = [
            {
                'name': '01-Jul-2025 (User Format)',
                'input_date': '01-Jul-2025',
                'expected_invoices': 124  # User's manual export
            },
            {
                'name': '08-Jul-2025 (Very Recent)',
                'input_date': '08-Jul-2025',
                'expected_invoices': 'Few'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"   Input date: {test_case['input_date']}")
            print(f"   Expected: {test_case['expected_invoices']} invoices")
            
            # Convert date
            try:
                dt = datetime.strptime(test_case['input_date'], "%d-%b-%Y")
                iso_timestamp = dt.isoformat()
                
                print(f"   ISO timestamp: {iso_timestamp}")
                
                # Test our utility function
                zoho_timestamp = ensure_zoho_timestamp_format(iso_timestamp)
                print(f"   Zoho timestamp (utils): {zoho_timestamp}")
                
                # Test different API parameter formats
                api_formats = [
                    {'modified_time': zoho_timestamp, 'name': 'modified_time (utils output)'},
                    {'modified_time': iso_timestamp.split('T')[0], 'name': 'modified_time (YYYY-MM-DD)'},
                    {'modified_time': dt.strftime('%Y-%m-%d'), 'name': 'modified_time (strftime)'},
                    {'last_modified_time': zoho_timestamp, 'name': 'last_modified_time (utils output)'},
                    {'date': dt.strftime('%Y-%m-%d'), 'name': 'date parameter'},
                ]
                
                for api_format in api_formats:
                    param_name = list(api_format.keys())[0]
                    param_value = api_format[param_name]
                    format_name = api_format['name']
                    
                    if param_name == 'name':
                        continue
                        
                    print(f"\n   📡 Testing API format: {format_name}")
                    print(f"      Parameter: {param_name}={param_value}")
                    
                    params = {
                        'organization_id': organization_id,
                        param_name: param_value,
                        'per_page': 200,
                        'page': 1
                    }
                    
                    try:
                        response = requests.get(
                            'https://www.zohoapis.com/books/v3/invoices',
                            headers=headers,
                            params=params,
                            timeout=10
                        )
                        
                        print(f"      Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            invoices = data.get('invoices', [])
                            total_count = len(invoices)
                            
                            # Check if there are more pages
                            page_context = data.get("page_context", {})
                            has_more_page = page_context.get("has_more_page", False)
                            
                            print(f"      First page: {total_count} invoices")
                            print(f"      Has more pages: {has_more_page}")
                            
                            if has_more_page:
                                print(f"      ⚠️ More pages exist - this is NOT the total count")
                            else:
                                print(f"      ✅ Total count: {total_count}")
                                
                            # Check first few invoice dates
                            if invoices:
                                print(f"      📅 Sample invoice dates:")
                                for i, invoice in enumerate(invoices[:3]):
                                    inv_date = invoice.get('date', 'Unknown')
                                    inv_id = invoice.get('invoice_number', 'Unknown')
                                    print(f"         {i+1}. {inv_id}: {inv_date}")
                                    
                        else:
                            print(f"      ❌ Error: {response.text[:200]}")
                            
                    except Exception as e:
                        print(f"      ❌ Exception: {e}")
                    
                    print()  # Blank line
                    
            except Exception as e:
                print(f"   ❌ Error processing date: {e}")
        
        print("=" * 60)
        print("ANALYSIS:")
        print("- Check which parameter format gives the expected count")
        print("- Verify invoice dates match the cutoff")
        print("- Look for the format that returns ~124 invoices for 01-Jul")
        print("=" * 60)

    if __name__ == "__main__":
        debug_api_parameters()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
