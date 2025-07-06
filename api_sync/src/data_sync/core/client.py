import time
import requests
import json
from typing import List, Dict, Any

class ZohoClient:
    """
    A client for interacting with the Zoho Books API.

    Handles authentication headers, pagination, and basic error handling.
    Designed to fetch data one module at a time.
    """
    def __init__(self, access_token: str, organization_id: str, api_base_url: str):
        """
        Initializes the Zoho API client.

        Args:
            access_token: The active OAuth2 access token.
            organization_id: The ID of the Zoho Books organization to query.
            api_base_url: The base URL for the Zoho Books API.
        """
        if not all([access_token, organization_id, api_base_url]):
            raise ValueError("Access token, organization ID, and API base URL are required.")
            
        self.access_token = access_token
        self.organization_id = organization_id
        self.base_url = api_base_url
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}"
        }
        print("INFO: ZohoClient initialized successfully.")

    def _get_all_pages(self, module_name: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Private helper method to handle pagination for any given module.
        This is the core engine for all data-fetching methods.

        Args:
            module_name: The API name of the module (e.g., 'invoices', 'contacts').
                         This is also used as the response key.
            params: Optional dictionary of query parameters.

        Returns:
            A list containing all items for the module from all pages.
        """
        all_items = []
        page = 1
        has_more_pages = True
        endpoint = f"/{module_name}"

        # Ensure params is a dict and add the mandatory organization_id
        if params is None:
            params = {}
        params['organization_id'] = self.organization_id

        print(f"\n---> Fetching all records for module: '{module_name}' <---")
        while has_more_pages:
            params['page'] = page
            
            try:
                full_url = f"{self.base_url}{endpoint}"
                print(f"  - Requesting page {page} from {full_url}")
                response = requests.get(full_url, headers=self.headers, params=params)
                
                # Gracefully handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    print("  - WARN: Rate limit hit. Waiting for 60 seconds before retrying...")
                    time.sleep(60)
                    continue # Retry the same page without incrementing

                response.raise_for_status() # Raise an exception for other bad status codes (4xx, 5xx)
                
                data = response.json()
                
                # The response key (e.g., "invoices") is the same as the module name
                items_on_page = data.get(module_name, [])
                if items_on_page:
                    all_items.extend(items_on_page)
                
                page_context = data.get("page_context", {})
                has_more_pages = page_context.get("has_more_page", False)
                
                print(f"  - Found {len(items_on_page)} items on page {page}. More pages: {has_more_pages}")

                if has_more_pages:
                    page += 1
                
                # Be a good API citizen: add a small delay between paged requests
                time.sleep(1.2)

            except requests.exceptions.RequestException as e:
                print(f"  - ERROR: A network error occurred while fetching '{module_name}' on page {page}.")
                if e.response is not None:
                    print(f"    Response Status: {e.response.status_code}")
                    print(f"    Response Body: {e.response.text}")
                print("  - Aborting fetch for this module.")
                # On error, stop processing this module and return what we have so far
                break

        print(f"---> Finished. Total records for '{module_name}': {len(all_items)} <---\n")
        return all_items

    def get_data_for_module(self, module_name: str, since_timestamp: str = None) -> List[Dict[str, Any]]:
        """
        Generic public method to fetch all records for a given Zoho module.

        Args:
            module_name: The name of the module to fetch (e.g., 'contacts', 'invoices').
            since_timestamp: If provided, fetches records modified after this time.
                             Format: 'YYYY-MM-DD'T'HH:MM:SS+0530'

        Returns:
            A list of dictionary objects, where each object is a record.
        """
        params = {}
        if since_timestamp:
            params['last_modified_time'] = since_timestamp
        
        # The module_name is passed directly to the generic pagination handler
        return self._get_all_pages(module_name=module_name, params=params)

    def get_salesorder_details(self, salesorder_id: str) -> Dict[str, Any]:
        """
        Fetch complete details for a specific sales order, including line items.
        
        Args:
            salesorder_id: The ID of the sales order to fetch details for
            
        Returns:
            A dictionary containing the complete sales order data with line items
            
        Raises:
            requests.exceptions.RequestException: If the API call fails
            ValueError: If salesorder_id is invalid or sales order not found
        """
        if not salesorder_id or not isinstance(salesorder_id, str):
            raise ValueError("salesorder_id must be a non-empty string")
            
        endpoint = f"/salesorders/{salesorder_id}"
        params = {'organization_id': self.organization_id}
        
        try:
            full_url = f"{self.base_url}{endpoint}"
            print(f"  - Fetching sales order details for ID: {salesorder_id}")
            
            response = requests.get(full_url, headers=self.headers, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                print("  - WARN: Rate limit hit. Waiting for 60 seconds before retrying...")
                time.sleep(60)
                response = requests.get(full_url, headers=self.headers, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            # Extract the salesorder object from the response
            salesorder_data = data.get('salesorder', {})
            if not salesorder_data:
                raise ValueError(f"No sales order data found for ID: {salesorder_id}")
                
            print(f"  - Successfully fetched sales order details. Line items: {len(salesorder_data.get('line_items', []))}")
            return salesorder_data
            
        except requests.exceptions.RequestException as e:
            print(f"  - ERROR: Failed to fetch sales order details for ID {salesorder_id}")
            if e.response is not None:
                print(f"    Response Status: {e.response.status_code}")
                print(f"    Response Body: {e.response.text}")
            raise
