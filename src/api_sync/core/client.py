import time
import requests
import json
import logging
from typing import List, Dict, Any

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
            params['last_modified_time'] = since_timestamp
            logger.info(f"Fetching '{module_name}' modified since {since_timestamp}")
        
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
