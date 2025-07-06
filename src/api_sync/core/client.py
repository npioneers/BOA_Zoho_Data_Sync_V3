import time
import requests
import json
import logging
from typing import List, Dict, Any, Optional
from ..utils import ensure_zoho_timestamp_format

logger = logging.getLogger(__name__)

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
        logger.info("ZohoClient initialized successfully.")

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

        logger.info(f"Fetching all records for module: '{module_name}'")
        while has_more_pages:
            params['page'] = page
            
            try:
                full_url = f"{self.base_url}{endpoint}"
                logger.debug(f"Requesting page {page} from {full_url}")
                response = requests.get(full_url, headers=self.headers, params=params)
                
                # Gracefully handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    logger.warning("Rate limit hit. Waiting for 60 seconds before retrying...")
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
                
                logger.debug(f"Found {len(items_on_page)} items on page {page}. More pages: {has_more_pages}")

                if has_more_pages:
                    page += 1
                
                # Be a good API citizen: add a small delay between paged requests
                time.sleep(1.2)

            except requests.exceptions.RequestException as e:
                logger.error(f"A network error occurred while fetching '{module_name}' on page {page}.")
                if e.response is not None:
                    logger.error(f"Response Status: {e.response.status_code}")
                    logger.error(f"Response Body: {e.response.text}")
                logger.error("Aborting fetch for this module.")
                # On error, stop processing this module and return what we have so far
                break

        logger.info(f"Finished. Total records for '{module_name}': {len(all_items)}")
        return all_items

    def get_data_for_module(self, module_name: str, since_timestamp: str = None) -> List[Dict[str, Any]]:
        """
        Fetches all records for a specific module.
        
        Args:
            module_name: The name of the module to fetch data for (e.g., 'invoices').
            since_timestamp: Optional ISO-8601 timestamp to only fetch records modified since that time.
        
        Returns:
            A list of records from the specified module.
        """
        params = {}
        
        # Add the last_modified_time filter if specified
        if since_timestamp:
            # Convert to Zoho format before sending to API
            zoho_timestamp = ensure_zoho_timestamp_format(since_timestamp)
            if zoho_timestamp:
                # Try different parameter names for Zoho Books API
                # Some endpoints use 'modified_time' instead of 'last_modified_time'
                params['modified_time'] = zoho_timestamp
                logger.info(f"Fetching '{module_name}' modified since {zoho_timestamp} (converted from {since_timestamp})")
            else:
                logger.warning(f"Invalid timestamp format, fetching all records: {since_timestamp}")
        
        # Special handling for certain modules
        if module_name == "organizations":
            # Organizations endpoint is different and returns a direct list
            return self._get_organizations()
        
        # For all other modules, use the standard pagination approach
        return self._get_all_pages(module_name, params)

    def _get_organizations(self) -> List[Dict[str, Any]]:
        """
        Special method for the organizations endpoint which behaves differently.
        """
        try:
            endpoint = "/organizations"
            full_url = f"{self.base_url}{endpoint}"
            
            logger.info(f"Fetching organizations from {full_url}")
            response = requests.get(full_url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            organizations = data.get("organizations", [])
            
            logger.info(f"Found {len(organizations)} organizations")
            return organizations
            
        except requests.exceptions.RequestException as e:
            logger.error("A network error occurred while fetching organizations.")
            if e.response is not None:
                logger.error(f"Response Status: {e.response.status_code}")
                logger.error(f"Response Body: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching organizations: {str(e)}")
            return []
    
    # Modules that have line items and need detailed fetching
    MODULES_WITH_LINE_ITEMS = {
        'invoices': 'invoice_id',
        'bills': 'bill_id', 
        'salesorders': 'salesorder_id',
        'purchaseorders': 'purchaseorder_id',
        'creditnotes': 'creditnote_id'
    }

    def get_data_for_module_with_line_items(self, module_name: str, since_timestamp: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches all data for a module including detailed records with line items.
        
        For modules that have line items (invoices, bills, etc.), this method:
        1. Fetches the list of records (headers)
        2. Fetches detailed data for each record to get line items
        3. Returns both headers and extracted line items
        
        Args:
            module_name: The name of the module to fetch
            since_timestamp: Optional timestamp to filter records
            
        Returns:
            Dictionary with 'headers' and 'line_items' lists
        """
        if module_name not in self.MODULES_WITH_LINE_ITEMS:
            # For modules without line items, just return headers
            headers = self.get_data_for_module(module_name, since_timestamp)
            return {'headers': headers, 'line_items': []}
        
        # Get the ID field for this module
        id_field = self.MODULES_WITH_LINE_ITEMS[module_name]
        
        # First, get the list of records (headers only)
        logger.info(f"Fetching {module_name} headers...")
        headers = self.get_data_for_module(module_name, since_timestamp)
        
        if not headers:
            logger.info(f"No {module_name} found, no line items to fetch")
            return {'headers': [], 'line_items': []}
        
        # Then fetch detailed data for each record to get line items
        logger.info(f"Fetching detailed data with line items for {len(headers)} {module_name}...")
        detailed_records = []
        all_line_items = []
        
        for i, header in enumerate(headers):
            record_id = header.get(id_field)
            if not record_id:
                logger.warning(f"No {id_field} found in {module_name} record {i+1}")
                continue
                
            # Fetch detailed record
            detailed_record = self._get_detailed_record(module_name, record_id)
            if detailed_record:
                detailed_records.append(detailed_record)
                
                # Extract line items if present
                line_items = self._extract_line_items(detailed_record, module_name, record_id)
                all_line_items.extend(line_items)
                
            # Rate limiting - small delay between requests
            if i > 0 and i % 10 == 0:
                logger.info(f"Processed {i+1}/{len(headers)} {module_name} records...")
                time.sleep(0.5)  # Short pause every 10 requests
        
        logger.info(f"Successfully fetched {len(detailed_records)} detailed {module_name} with {len(all_line_items)} total line items")
        
        return {
            'headers': detailed_records,  # Use detailed records instead of basic headers
            'line_items': all_line_items
        }
    
    def _get_detailed_record(self, module_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed data for a single record including line items.
        
        Args:
            module_name: The module name (e.g., 'invoices')
            record_id: The ID of the specific record
            
        Returns:
            Detailed record data or None if failed
        """
        try:
            endpoint = f"/{module_name}/{record_id}"
            params = {'organization_id': self.organization_id}
            full_url = f"{self.base_url}{endpoint}"
            
            response = requests.get(full_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # The response structure varies by module, but typically the data is under a key
            # like "invoice", "bill", etc. (singular form of module name)
            singular_key = module_name.rstrip('s')  # invoices -> invoice, bills -> bill
            record = data.get(singular_key, data)
            
            return record
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch detailed {module_name} record {record_id}: {e}")
            if e.response is not None and e.response.status_code == 429:
                # Rate limit hit, wait and retry once
                logger.info("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                try:
                    response = requests.get(full_url, headers=self.headers, params=params)
                    response.raise_for_status()
                    data = response.json()
                    singular_key = module_name.rstrip('s')
                    return data.get(singular_key, data)
                except:
                    pass
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching detailed {module_name} record {record_id}: {e}")
            return None
    
    def _extract_line_items(self, detailed_record: Dict[str, Any], module_name: str, record_id: str) -> List[Dict[str, Any]]:
        """
        Extract line items from a detailed record.
        
        Args:
            detailed_record: The detailed record containing line items
            module_name: The module name for context
            record_id: The parent record ID
            
        Returns:
            List of line item dictionaries
        """
        line_items = []
        
        # Common line item field names in Zoho Books
        line_item_fields = ['line_items', 'invoice_items', 'bill_items', 'items']
        
        for field in line_item_fields:
            if field in detailed_record:
                items = detailed_record[field]
                if isinstance(items, list):
                    for item in items:
                        # Add parent reference to line item
                        if isinstance(item, dict):
                            item['parent_id'] = record_id
                            item['parent_type'] = module_name.rstrip('s')  # invoices -> invoice
                            line_items.append(item)
                break
        
        return line_items

    def get_module_count(self, module_name: str, since_timestamp: str = None) -> int:
        """
        Get count of records for a specific module by looping through all pages.
        
        Args:
            module_name: The name of the module to count (e.g., 'invoices').
            since_timestamp: Optional ISO-8601 timestamp to only count records modified since that time.
        
        Returns:
            Count of records in the specified module.
        """
        params = {"organization_id": self.organization_id}
        
        # Add the modified_time filter if specified (using corrected parameter name)
        if since_timestamp:
            # Convert ISO timestamp to YYYY-MM-DD format for Zoho API
            if 'T' in since_timestamp:
                date_part = since_timestamp.split('T')[0]
                params['modified_time'] = date_part
            else:
                params['modified_time'] = since_timestamp
        
        total_count = 0
        page = 1
        params['per_page'] = 200  # Use maximum page size for efficiency
        
        try:
            while True:
                params['page'] = page
                
                response = requests.get(
                    f"{self.base_url}/{module_name}",
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                # Get records for this page
                records = data.get(module_name, [])
                if not records:
                    break
                    
                total_count += len(records)
                
                # Check if there are more pages
                page_context = data.get("page_context", {})
                has_more_page = page_context.get("has_more_page", False)
                
                if not has_more_page:
                    break
                    
                page += 1
                logger.debug(f"Fetched page {page-1} for {module_name}: {len(records)} records")
            
            logger.info(f"API count for {module_name}: {total_count} records across {page} pages")
            return total_count
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get count for '{module_name}': {e}")
            if e.response is not None:
                logger.error(f"Response Status: {e.response.status_code}")
                logger.error(f"Response Body: {e.response.text}")
            return 0
