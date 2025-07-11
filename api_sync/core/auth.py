import requests
import sys
import logging
from typing import Dict

# Updated import for the new package structure
from . import secrets

logger = logging.getLogger(__name__)

def get_access_token(zoho_credentials: Dict[str, str]) -> str:
    """
    Exchanges a Zoho refresh token for a new access token.

    Args:
        zoho_credentials: A dictionary containing client_id, client_secret,
                          and refresh_token fetched from GCP.

    Returns:
        The new access token as a string.

    Raises:
        SystemExit: If the API call fails or the response is invalid.
    """
    logger.info("Preparing to fetch Zoho access token...")

    # We get the URL from the credentials dict, which will later come from settings.
    # For now, let's hardcode the standard one.
    token_url = "https://accounts.zoho.com/oauth/v2/token"

    params = {
        "refresh_token": zoho_credentials["zoho_refresh_token"],
        "client_id": zoho_credentials["zoho_client_id"],
        "client_secret": zoho_credentials["zoho_client_secret"],
        "grant_type": "refresh_token",
    }

    try:
        logger.info("Making POST request to Zoho token endpoint...")
        response = requests.post(token_url, params=params)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)

        response_json = response.json()
        
        access_token = response_json.get("access_token")

        if not access_token:
            logger.error("'access_token' not found in Zoho's response.")
            logger.error(f"Response from Zoho: {response_json}")
            raise SystemExit(1)

        logger.info("Successfully obtained new Zoho access token.")
        return access_token

    except requests.exceptions.RequestException as e:
        logger.error(f"A network error occurred while contacting Zoho: {e}")
        # Check if the response object exists to provide more detail
        if e.response is not None:
            logger.error(f"Response Status: {e.response.status_code}")
            logger.error(f"Response Body: {e.response.text}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_access_token: {e}")
        raise SystemExit(1)
