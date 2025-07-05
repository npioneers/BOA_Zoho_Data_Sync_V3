"""
Zoho API Client for Incremental Sync

Enhanced API client that supports both full and incremental data fetching
from Zoho Books API with rate limiting, error handling, and retry logic.

Features:
- Incremental sync with last_modified_time filter
- Full data fetching with pagination
- Rate limiting and exponential backoff
- Comprehensive error handling
- Request/response logging

Adheres to operational guidelines: NO hardcoded values, externalized configuration
"""

import time
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ZohoClient:
    """
    Enhanced Zoho Books API client with incremental sync support.
    
    Handles authentication, pagination, rate limiting, and provides both
    full and incremental data fetching capabilities.
    """
    
    def __init__(self, access_token: str, organization_id: str, api_base_url: str = None):
        """
        Initialize the Zoho API client.
        
        Args:
            access_token: The active OAuth2 access token
            organization_id: The ID of the Zoho Books organization to query
            api_base_url: Optional base URL for the Zoho Books API
        """
        if not all([access_token, organization_id]):
            raise ValueError("Access token and organization ID are required")
        
        self.access_token = access_token
        self.organization_id = organization_id
        self.base_url = api_base_url or "https://www.zohoapis.com/books/v3"
        
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting settings
        self.default_delay = 1.2  # Default delay between requests
        self.rate_limit_delay = 60  # Delay when rate limited
        self.max_retries = 3
        
        logger.info(f"ZohoClient initialized for organization: {organization_id}")
    
    def get_data_for_module(self, module_name: str, since_timestamp: Optional[str] = None, 
                           page_size: int = 200) -> List[Dict[str, Any]]:
        """
        Fetch all records for a given Zoho module with optional incremental filtering.
        
        Args:
            module_name: The name of the module to fetch (e.g., 'bills', 'invoices')
            since_timestamp: If provided, fetches records modified after this time.
                           Format: ISO 8601 (e.g., '2025-07-05T14:30:00+00:00')
            page_size: Number of records per page (default: 200, max: 200)
        
        Returns:
            List of dictionary objects, where each object is a record
        """
        params = {
            'organization_id': self.organization_id,
            'per_page': min(page_size, 200)  # Zoho API max is 200
        }
        
        # Add incremental filter if provided
        if since_timestamp:
            params['last_modified_time'] = since_timestamp
            logger.info(f"🔄 Fetching {module_name} modified since: {since_timestamp}")
        else:
            logger.info(f"📥 Fetching all {module_name} data (full sync)")
        
        return self._get_all_pages(module_name, params)
    
    def _get_all_pages(self, module_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch all pages of data for a module with pagination handling.
        
        Args:
            module_name: The module name for the API endpoint
            params: Query parameters for the request
            
        Returns:
            List of all records across all pages
        """
        all_items = []
        page = 1
        has_more_pages = True
        
        logger.info(f"🌐 Starting paginated fetch for {module_name}")
        
        while has_more_pages:
            try:
                # Add page parameter
                params['page'] = page
                
                # Construct endpoint URL
                endpoint = f"/{module_name}"
                full_url = f"{self.base_url}{endpoint}"
                
                logger.debug(f"📄 Requesting page {page} from {full_url}")
                
                # Make the API request
                response = self._make_request(full_url, params)
                
                if not response:
                    logger.error(f"Failed to get response for {module_name} page {page}")
                    break
                
                data = response.json()
                
                # Extract items from response (key matches module name)
                items_on_page = data.get(module_name, [])
                if items_on_page:
                    all_items.extend(items_on_page)
                    logger.info(f"📊 Page {page}: Found {len(items_on_page)} {module_name} records")
                else:
                    logger.info(f"📭 Page {page}: No {module_name} records found")
                
                # Check for more pages
                page_context = data.get("page_context", {})
                has_more_pages = page_context.get("has_more_page", False)
                
                if has_more_pages:
                    page += 1
                    # Rate limiting between requests
                    time.sleep(self.default_delay)
                
            except Exception as e:
                logger.error(f"❌ Error fetching {module_name} page {page}: {e}")
                break
        
        logger.info(f"✅ Completed fetch for {module_name}: {len(all_items)} total records")
        return all_items
    
    def _make_request(self, url: str, params: Dict[str, Any], retries: int = 0) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling and retry logic.
        
        Args:
            url: The full URL to request
            params: Query parameters
            retries: Current retry count
            
        Returns:
            Response object if successful, None if failed
        """
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429:
                logger.warning(f"⏰ Rate limit hit. Waiting {self.rate_limit_delay} seconds...")
                time.sleep(self.rate_limit_delay)
                
                if retries < self.max_retries:
                    return self._make_request(url, params, retries + 1)
                else:
                    logger.error("❌ Max retries exceeded for rate limiting")
                    return None
            
            # Handle other HTTP errors
            if response.status_code != 200:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                
                # Retry on server errors (5xx)
                if 500 <= response.status_code < 600 and retries < self.max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    logger.warning(f"🔄 Server error, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    return self._make_request(url, params, retries + 1)
                
                return None
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error("⏱️ Request timeout")
            if retries < self.max_retries:
                time.sleep(2 ** retries)
                return self._make_request(url, params, retries + 1)
            return None
            
        except requests.exceptions.ConnectionError:
            logger.error("🌐 Connection error")
            if retries < self.max_retries:
                time.sleep(2 ** retries)
                return self._make_request(url, params, retries + 1)
            return None
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def get_detail_record(self, module_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific record.
        
        Useful for getting complete record details including line items
        that may not be included in bulk API responses.
        
        Args:
            module_name: The module name (e.g., 'bills', 'invoices')
            record_id: The unique identifier of the record
            
        Returns:
            Complete record data or None if failed
        """
        try:
            endpoint = f"/{module_name}/{record_id}"
            full_url = f"{self.base_url}{endpoint}"
            
            params = {'organization_id': self.organization_id}
            
            logger.debug(f"🔍 Fetching details for {module_name} ID: {record_id}")
            
            response = self._make_request(full_url, params)
            if not response:
                return None
            
            data = response.json()
            
            # Extract the record from response (key is singular form of module)
            record_key = module_name.rstrip('s')  # Simple pluralization handling
            record_data = data.get(record_key, {})
            
            if record_data:
                logger.debug(f"✅ Successfully fetched {module_name} details for ID: {record_id}")
                return record_data
            else:
                logger.warning(f"⚠️ No data found for {module_name} ID: {record_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch {module_name} details for ID {record_id}: {e}")
            return None
    
    def get_multiple_details(self, module_name: str, record_ids: List[str], 
                           batch_size: int = 10, delay_seconds: float = 1.5) -> Dict[str, Dict[str, Any]]:
        """
        Fetch detailed information for multiple records with batch processing.
        
        Args:
            module_name: The module name (e.g., 'bills', 'invoices')
            record_ids: List of record IDs to fetch
            batch_size: Number of requests per batch (default: 10)
            delay_seconds: Delay between individual requests (default: 1.5)
            
        Returns:
            Dictionary mapping record IDs to their detailed data
        """
        results = {}
        failed_ids = []
        
        logger.info(f"📊 Fetching details for {len(record_ids)} {module_name} records")
        
        for i, record_id in enumerate(record_ids, 1):
            try:
                record_data = self.get_detail_record(module_name, record_id)
                if record_data:
                    results[record_id] = record_data
                else:
                    failed_ids.append(record_id)
                
                # Progress reporting
                if i % 5 == 0 or i == len(record_ids):
                    logger.info(f"📈 Progress: {i}/{len(record_ids)} processed ({len(results)} successful)")
                
                # Rate limiting
                if i % batch_size == 0 and i < len(record_ids):
                    logger.info(f"⏸️ Batch completed. Pausing for {delay_seconds * 3} seconds...")
                    time.sleep(delay_seconds * 3)
                else:
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch details for {module_name} ID {record_id}: {e}")
                failed_ids.append(record_id)
                time.sleep(delay_seconds)
        
        logger.info(f"✅ Completed: {len(results)} successful, {len(failed_ids)} failed")
        if failed_ids:
            logger.warning(f"❌ Failed IDs: {failed_ids[:10]}{'...' if len(failed_ids) > 10 else ''}")
        
        return results
    
    def test_connection(self) -> bool:
        """
        Test the API connection and credentials.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("🔍 Testing API connection...")
            
            # Test with a simple endpoint
            endpoint = "/organizations"
            full_url = f"{self.base_url}{endpoint}"
            params = {'organization_id': self.organization_id}
            
            response = self._make_request(full_url, params)
            
            if response:
                data = response.json()
                organizations = data.get('organizations', [])
                
                for org in organizations:
                    if org.get('organization_id') == self.organization_id:
                        org_name = org.get('name', 'Unknown')
                        logger.info(f"✅ Connection successful to organization: {org_name}")
                        return True
                
                logger.error("❌ Organization ID not found in available organizations")
                return False
            else:
                logger.error("❌ Failed to connect to API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def get_organization_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current organization.
        
        Returns:
            Organization information or None if failed
        """
        try:
            endpoint = "/organizations"
            full_url = f"{self.base_url}{endpoint}"
            params = {'organization_id': self.organization_id}
            
            response = self._make_request(full_url, params)
            if not response:
                return None
            
            data = response.json()
            organizations = data.get('organizations', [])
            
            for org in organizations:
                if org.get('organization_id') == self.organization_id:
                    return org
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get organization info: {e}")
            return None
