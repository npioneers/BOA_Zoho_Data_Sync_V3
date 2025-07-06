import requests
import sys
from typing import Dict

# It's good practice to import modules from our own package like this.
from data_sync.core import secrets

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
    print("INFO: Preparing to fetch Zoho access token...")

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
        print(f"INFO: Making POST request to Zoho token endpoint...")
        response = requests.post(token_url, params=params)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)

        response_json = response.json()
        
        access_token = response_json.get("access_token")

        if not access_token:
            print("ERROR: 'access_token' not found in Zoho's response.")
            print(f"  Response from Zoho: {response_json}")
            raise SystemExit(1)

        print("INFO: Successfully obtained new Zoho access token.")
        return access_token

    except requests.exceptions.RequestException as e:
        print(f"ERROR: A network error occurred while contacting Zoho: {e}")
        # Check if the response object exists to provide more detail
        if e.response is not None:
            print(f"  Response Status: {e.response.status_code}")
            print(f"  Response Body: {e.response.text}")
        raise SystemExit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in get_access_token: {e}")
        raise SystemExit(1)
