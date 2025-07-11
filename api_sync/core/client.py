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
        
        � OPTIMIZED: Uses efficient API-side filtering (all modules support it)

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

        # Check if we're doing incremental sync with API filtering
        using_api_filter = 'last_modified_time' in params
        if using_api_filter:
            logger.info(f"🚀 API-FILTERED FETCH: Using server-side filtering for {module_name}")
            print(f"[API-FILTERED] Starting efficient fetch for {module_name} with server-side filtering...")

        logger.info(f"Fetching all records for module: '{module_name}'")
        print(f"[FETCH] Starting paginated fetch for {module_name}...")
        
        while has_more_pages:
            params['page'] = page
            
            try:
                full_url = f"{self.base_url}{endpoint}"
                logger.debug(f"Requesting page {page} from {full_url}")
                print(f"[FETCH] Fetching page {page} of {module_name}...")
                
                response = requests.get(full_url, headers=self.headers, params=params)
                
                # Gracefully handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    logger.warning("Rate limit hit. Waiting for 60 seconds before retrying...")
                    print("[WARN] Rate limit hit. Waiting 60 seconds before retrying...")
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
                print(f"[FETCH] Page {page}: Found {len(items_on_page)} records. Total so far: {len(all_items)}")

                if has_more_pages:
                    page += 1
                    print(f"[FETCH] More pages available. Moving to page {page}...")
                else:
                    print(f"[FETCH] Completed fetch. Total records: {len(all_items)}")
                
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
        if using_api_filter:
            logger.info(f"🎯 API-FILTERED: Efficiently fetched {len(all_items)} filtered records")
        return all_items

    def get_data_for_module(self, module_name: str, since_timestamp: str = None) -> List[Dict[str, Any]]:
        """
        Fetches all records for a specific module with efficient API-side filtering.
        
        ✅ OPTIMIZED: Uses API-side filtering (all modules support last_modified_time)
        
        Args:
            module_name: The name of the module to fetch data for (e.g., 'invoices').
            since_timestamp: Optional ISO-8601 timestamp to only fetch records modified since that time.
        
        Returns:
            A list of records from the specified module.
        """
        params = {}
        
        # USE API-SIDE FILTERING (all modules support this now!)
        if since_timestamp:
            # Convert to Zoho format before sending to API
            zoho_timestamp = ensure_zoho_timestamp_format(since_timestamp)
            if zoho_timestamp:
                params['last_modified_time'] = zoho_timestamp
                logger.info(f"🚀 API FILTER: Fetching '{module_name}' modified since {zoho_timestamp}")
                print(f"[API-FILTER] {module_name}: Using cutoff {zoho_timestamp}")
            else:
                logger.warning(f"Invalid timestamp format: {since_timestamp}")
        
        # Special handling for certain modules
        if module_name == "organizations":
            # Organizations endpoint is different and returns a direct list
            return self._get_organizations()
        
        # Fetch records using efficient API-side filtering
        all_items = self._get_all_pages(module_name, params)
        
        logger.info(f"📊 API FILTER RESULTS: Fetched {len(all_items)} {module_name} records")
        if since_timestamp:
            print(f"[API-FILTER] {module_name}: Retrieved {len(all_items)} records after {since_timestamp}")
        
        return all_items

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
        
        SMART FETCH: Checks for existing comprehensive data before making individual API calls.
        
        For modules that have line items (invoices, bills, etc.), this method:
        1. Checks if we already have comprehensive line item data
        2. If yes, fetches only headers (much faster)
        3. If no, fetches detailed data for each record to get line items
        4. Returns both headers and extracted line items
        
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
        
        # SMART CHECK: Do we already have comprehensive line item data?
        # OPTION A: Force bypass comprehensive data check during incremental sync
        if since_timestamp:
            logger.info(f"🔄 OPTION A: Incremental sync detected - BYPASSING comprehensive data check")
            logger.info(f"🚫 Forcing individual line item fetching to respect cutoff: {since_timestamp}")
            has_comprehensive_data = False  # Force bypass
        else:
            has_comprehensive_data = self._has_comprehensive_line_item_data(module_name)
        
        # Add detailed logging for incremental sync decision
        logger.info(f"🔍 LINE ITEM FETCH DECISION for {module_name}:")
        logger.info(f"  📅 Since timestamp: {since_timestamp}")
        logger.info(f"  📊 Has comprehensive data: {has_comprehensive_data}")
        logger.info(f"  🔄 Forced bypass: {since_timestamp is not None}")
        
        # OPTION A LOGIC: Only skip line item fetching if no incremental sync is requested
        if has_comprehensive_data and not since_timestamp:
            logger.info(f"📊 SMART FETCH: Found comprehensive {module_name} line item data, skipping individual fetches")
            print(f"[SMART] Found comprehensive {module_name} data with line items - skipping individual fetches")
            print(f"[SMART] This saves {1000}+ individual API calls!")
            
            # Just get headers, we already have line items in consolidated data
            headers = self.get_data_for_module(module_name, since_timestamp)
            return {'headers': headers, 'line_items': []}
        
        # OPTION A: When incremental sync is requested, ALWAYS fetch line items individually
        if since_timestamp:
            logger.info(f"🔄 OPTION A: Incremental sync - forcing individual line item fetching")
            print(f"[OPTION A] Incremental sync detected - forcing fresh line item fetch")
            print(f"[OPTION A] Cutoff date: {since_timestamp} - ensuring all new/updated items are captured")
        else:
            logger.info(f"⚠️ No comprehensive {module_name} line item data found, fetching individually")
            print(f"[VERBOSE] No comprehensive line item data found, fetching individually...")
        
        logger.info(f"📋 Will fetch line items for each {module_name} record individually")
        
        # Get the ID field for this module
        id_field = self.MODULES_WITH_LINE_ITEMS[module_name]
        
        # First, get the list of records (headers only)
        logger.info(f"Fetching {module_name} headers...")
        print(f"[VERBOSE] Step 1: Fetching {module_name} headers...")
        headers = self.get_data_for_module(module_name, since_timestamp)
        
        if not headers:
            logger.info(f"No {module_name} found, no line items to fetch")
            print(f"[VERBOSE] No {module_name} found, no line items to fetch")
            return {'headers': [], 'line_items': []}
        
        print(f"[VERBOSE] Found {len(headers)} {module_name} headers")
        
        # Then fetch detailed data for each record to get line items
        logger.info(f"Fetching detailed data with line items for {len(headers)} {module_name}...")
        logger.info(f"📋 INDIVIDUAL FETCH: Processing {len(headers)} records to get line items")
        if since_timestamp:
            logger.info(f"📅 Incremental sync active: since {since_timestamp}")
        else:
            logger.info(f"📅 Full sync: no timestamp filter")
        print(f"[VERBOSE] Step 2: Fetching detailed records with line items...")
        detailed_records = []
        all_line_items = []
        
        for i, header in enumerate(headers):
            record_id = header.get(id_field)
            if not record_id:
                logger.warning(f"No {id_field} found in {module_name} record {i+1}")
                continue
            
            # Show progress for large batches
            if len(headers) > 10 and (i + 1) % 10 == 0:
                print(f"[VERBOSE] Processing record {i+1}/{len(headers)}...")
                
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
        print(f"[VERBOSE] Completed: {len(detailed_records)} detailed records with {len(all_line_items)} line items")
        
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
            
            # The response structure varies with module, but typically the data is under a key
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

    def _has_comprehensive_line_item_data(self, module_name: str) -> bool:
        """
        Check if we already have comprehensive line item data for a module.
        This prevents unnecessary individual API calls when we have complete data.
        
        ⚠️ FIXED: Now prioritizes JSON storage (API sync data) over database
        
        Priority order for API sync operations:
        1. Check recent timestamped directories (most recent API data)
        2. Check consolidated JSON files with line items  
        3. Check database for existing line items (fallback)
        """
        logger.info(f"🔍 CHECKING for comprehensive {module_name} line item data...")
        
        try:
            # PRIORITY 1: Check recent timestamped directories first (most recent API data)
            from pathlib import Path
            import json
            
            base_path = Path("data/raw_json")
            logger.info(f"� Checking JSON storage in: {base_path}")
            
            timestamped_dirs = [d for d in base_path.iterdir() 
                              if d.is_dir() and self._is_timestamped_dir(d.name)]
            
            if timestamped_dirs:
                logger.info(f"� Found {len(timestamped_dirs)} timestamped directories")
                # Check last few recent directories
                recent_dirs = sorted(timestamped_dirs, key=lambda x: x.name)[-5:]
                logger.info(f"📂 Checking {len(recent_dirs)} most recent directories")
                
                for directory in reversed(recent_dirs):  # Start with most recent
                    line_items_file = directory / f"{module_name}_line_items.json"
                    logger.info(f"📄 Checking: {line_items_file}")
                    if line_items_file.exists():
                        with open(line_items_file, 'r') as f:
                            line_items_data = json.load(f)
                            if line_items_data and len(line_items_data) > 100:  # Substantial data
                                logger.warning(f"🎯 FOUND comprehensive line items in {directory.name} ({len(line_items_data)} items)")
                                logger.warning(f"🚨 This will SKIP individual API fetches!")
                                return True
                            else:
                                logger.info(f"� File exists but insufficient data: {len(line_items_data) if line_items_data else 0} items")
                    else:
                        logger.info(f"� Line items file not found in {directory.name}")
            else:
                logger.info(f"📂 No timestamped directories found in {base_path}")
            
            # PRIORITY 2: Check consolidated JSON files with line items
            
            # Check consolidated directory first
            consolidated_dirs = [d for d in base_path.iterdir() 
                               if d.is_dir() and d.name.startswith("CONSOLIDATED_")]
            
            if consolidated_dirs:
                # Use most recent consolidated directory
                latest_consolidated = sorted(consolidated_dirs, key=lambda x: x.name)[-1]
                module_file = latest_consolidated / f"{module_name}.json"
                line_items_file = latest_consolidated / f"{module_name}_line_items.json"
                
                if module_file.exists():
                    # Check if the main module file has line items embedded
                    with open(module_file, 'r') as f:
                        data = json.load(f)
                        if data and len(data) > 0:
                            # Check if records have line_items embedded
                            sample_record = data[0] if isinstance(data, list) else data
                            if isinstance(sample_record, dict) and 'line_items' in sample_record:
                                logger.info(f"Found comprehensive {module_name} data with embedded line items")
                                return True
                
                if line_items_file.exists():
                    logger.info(f"Found separate {module_name} line items file")
                    return True
            
            # PRIORITY 3: Check recent timestamped directories for comprehensive data
            timestamped_dirs = [d for d in base_path.iterdir() 
                              if d.is_dir() and self._is_timestamped_dir(d.name)]
            
            if timestamped_dirs:
                # Check last few recent directories
                recent_dirs = sorted(timestamped_dirs, key=lambda x: x.name)[-5:]
                
                for directory in reversed(recent_dirs):  # Start with most recent
                    line_items_file = directory / f"{module_name}_line_items.json"
                    if line_items_file.exists():
                        with open(line_items_file, 'r') as f:
                            line_items_data = json.load(f)
                            if line_items_data and len(line_items_data) > 100:  # Substantial data
                                logger.info(f"Found comprehensive line items in {directory.name}")
                                return True
            
            logger.info(f"🔍 NO comprehensive {module_name} line item data found")
            logger.info(f"📋 Will need to fetch line items individually")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for comprehensive data: {e}")
            logger.info(f"🔍 Due to error, assuming NO comprehensive data - will fetch individually")
            return False
    
    def _is_timestamped_dir(self, dirname: str) -> bool:
        """Check if directory name follows timestamp pattern."""
        try:
            parts = dirname.split('_')
            if len(parts) != 2:
                return False
            
            date_part, time_part = parts
            date_elements = date_part.split('-')
            time_elements = time_part.split('-')
            
            return (len(date_elements) == 3 and 
                    len(time_elements) == 3 and
                    all(elem.isdigit() for elem in date_elements + time_elements))
        except:
            return False
    
    def get_modified_records_report(self, module_name: str, since_timestamp: str) -> List[Dict[str, Any]]:
        """
        Get a lightweight report of records modified since a given timestamp.
        
        This fetches only essential fields (ID and timestamps) to create a filtered list
        of records that need to be synced, avoiding the need to fetch all data.
        
        Args:
            module_name: The module to query (e.g., 'invoices')
            since_timestamp: ISO timestamp to filter by last_modified_time
            
        Returns:
            List of dictionaries with minimal fields (id, last_modified_time, etc.)
        """
        logger.info(f"🔍 Getting modified records report for {module_name} since {since_timestamp}")
        
        # Convert timestamp to Zoho format
        zoho_timestamp = ensure_zoho_timestamp_format(since_timestamp)
        if not zoho_timestamp:
            logger.error(f"Invalid timestamp format: {since_timestamp}")
            return []
        
        all_modified_records = []
        page = 1
        has_more_pages = True
        endpoint = f"/{module_name}"
        
        # Parameters for lightweight fetch - try to get minimal fields
        params = {
            'organization_id': self.organization_id,
            'last_modified_time': zoho_timestamp,  # Try API-side filtering
            # Try to request only essential fields to reduce payload
            'fields': 'invoice_id,last_modified_time,date,created_time'  # Adjust per module
        }
        
        logger.info(f"📋 Fetching modified records report with params: {params}")
        print(f"[REPORT] Generating modified records report for {module_name}...")
        
        while has_more_pages:
            params['page'] = page
            
            try:
                full_url = f"{self.base_url}{endpoint}"
                logger.debug(f"Report request - Page {page}: {full_url}")
                print(f"[REPORT] Scanning page {page} for modified records...")
                
                response = requests.get(full_url, headers=self.headers, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning("Rate limit hit during report generation. Waiting...")
                    print("[REPORT] Rate limit hit. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                items_on_page = data.get(module_name, [])
                if not items_on_page:
                    logger.info(f"No more items found on page {page}")
                    break
                
                # Filter records on client-side as backup (in case API filtering doesn't work)
                filtered_items = []
                cutoff_dt = None
                
                try:
                    from datetime import datetime
                    if 'T' in since_timestamp:
                        cutoff_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                    else:
                        cutoff_dt = datetime.fromisoformat(since_timestamp)
                    cutoff_dt = cutoff_dt.replace(tzinfo=None)
                except Exception as e:
                    logger.warning(f"Could not parse cutoff date: {e}")
                
                for item in items_on_page:
                    # Check if this record was modified after our cutoff
                    item_modified_str = item.get('last_modified_time') or item.get('updated_time')
                    
                    if item_modified_str and cutoff_dt:
                        try:
                            if 'T' in item_modified_str:
                                item_modified_dt = datetime.fromisoformat(item_modified_str.replace('Z', '+00:00'))
                            else:
                                item_modified_dt = datetime.strptime(item_modified_str, '%Y-%m-%d')
                            item_modified_dt = item_modified_dt.replace(tzinfo=None)
                            
                            if item_modified_dt >= cutoff_dt:
                                # Keep only essential fields for the report
                                report_item = {
                                    'id': item.get(f'{module_name.rstrip("s")}_id', item.get('id')),
                                    'last_modified_time': item_modified_str,
                                    'date': item.get('date'),
                                    'created_time': item.get('created_time')
                                }
                                filtered_items.append(report_item)
                        except Exception as e:
                            logger.warning(f"Could not parse modified time '{item_modified_str}': {e}")
                            # Include item if we can't parse (safer)
                            report_item = {
                                'id': item.get(f'{module_name.rstrip("s")}_id', item.get('id')),
                                'last_modified_time': item_modified_str,
                                'date': item.get('date'),
                                'created_time': item.get('created_time')
                            }
                            filtered_items.append(report_item)
                    else:
                        # No modified time or couldn't parse cutoff - include it (safer)
                        report_item = {
                            'id': item.get(f'{module_name.rstrip("s")}_id', item.get('id')),
                            'last_modified_time': item_modified_str,
                            'date': item.get('date'),
                            'created_time': item.get('created_time')
                        }
                        filtered_items.append(report_item)
                
                all_modified_records.extend(filtered_items)
                
                # Check pagination
                page_context = data.get("page_context", {})
                has_more_pages = page_context.get("has_more_page", False)
                
                logger.debug(f"Report page {page}: {len(items_on_page)} total, {len(filtered_items)} modified since cutoff")
                print(f"[REPORT] Page {page}: {len(filtered_items)} modified records found")
                
                if has_more_pages:
                    page += 1
                else:
                    print(f"[REPORT] Report complete: {len(all_modified_records)} modified records total")
                
                # Small delay between pages
                time.sleep(0.8)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching report page {page}: {e}")
                if e.response is not None:
                    logger.error(f"Response Status: {e.response.status_code}")
                    logger.error(f"Response Body: {e.response.text}")
                break
        
        logger.info(f"📊 Modified records report complete: {len(all_modified_records)} records found")
        return all_modified_records

    def fetch_specific_records(self, module_name: str, record_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch specific records by their IDs.
        
        This is much more efficient than fetching all records and filtering,
        especially when we have a small list of specific records to fetch.
        
        Args:
            module_name: The module name (e.g., 'invoices')
            record_ids: List of record IDs to fetch
            
        Returns:
            List of full record data for the specified IDs
        """
        logger.info(f"🎯 Fetching {len(record_ids)} specific {module_name} records")
        print(f"[TARGETED] Fetching {len(record_ids)} specific records...")
        
        if not record_ids:
            logger.info("No record IDs provided, returning empty list")
            return []
        
        fetched_records = []
        failed_count = 0
        
        for i, record_id in enumerate(record_ids):
            if not record_id:
                logger.warning(f"Skipping empty record ID at index {i}")
                continue
                
            try:
                # Show progress for large batches
                if len(record_ids) > 10 and (i + 1) % 10 == 0:
                    print(f"[TARGETED] Fetching record {i+1}/{len(record_ids)}...")
                
                endpoint = f"/{module_name}/{record_id}"
                params = {'organization_id': self.organization_id}
                full_url = f"{self.base_url}{endpoint}"
                
                response = requests.get(full_url, headers=self.headers, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit while fetching {record_id}. Waiting...")
                    time.sleep(60)
                    # Retry once
                    response = requests.get(full_url, headers=self.headers, params=params)
                
                if response.status_code == 404:
                    logger.warning(f"Record {record_id} not found (404), skipping")
                    failed_count += 1
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Extract the record from response
                singular_key = module_name.rstrip('s')  # invoices -> invoice
                record = data.get(singular_key, data)
                
                if record:
                    fetched_records.append(record)
                else:
                    logger.warning(f"No data returned for record {record_id}")
                    failed_count += 1
                
                # Rate limiting delay
                time.sleep(0.3)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to fetch record {record_id}: {e}")
                failed_count += 1
                continue
            except Exception as e:
                logger.warning(f"Unexpected error fetching record {record_id}: {e}")
                failed_count += 1
                continue
        
        success_count = len(fetched_records)
        logger.info(f"📊 Targeted fetch complete: {success_count} successful, {failed_count} failed")
        print(f"[TARGETED] Completed: {success_count} records fetched, {failed_count} failed")
        
        return fetched_records
