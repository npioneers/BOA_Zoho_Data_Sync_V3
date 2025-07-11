import os
import logging
from dotenv import load_dotenv
from google.cloud import secretmanager
from google.api_core import exceptions
from typing import Dict

logger = logging.getLogger(__name__)

ZOHO_SECRET_NAMES = [
    "ZOHO_CLIENT_ID",
    "ZOHO_CLIENT_SECRET", 
    "ZOHO_REFRESH_TOKEN",
]

OPTIONAL_ZOHO_SECRETS = [
    "ZOHO_ORGANIZATION_ID",
]

def get_zoho_credentials() -> Dict[str, str]:
    """
    Fetches Zoho credentials from Google Cloud Secret Manager.

    This function relies on GOOGLE_APPLICATION_CREDENTIALS for authentication.
    It reads the GCP_PROJECT_ID from a .env file to know which project to get secrets from.
    
    Returns:
        Dictionary containing Zoho credentials with lowercase keys
        
    Raises:
        SystemExit: If credentials cannot be retrieved
    """
    logger.info("Loading environment variables from .env file...")
    load_dotenv()

    # The project where the SECRETS are stored.
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        logger.error("GCP_PROJECT_ID environment variable not set.")
        logger.error("Please create a .env file in the project root with GCP_PROJECT_ID='your-project-id'")
        raise SystemExit(1)

    logger.info(f"Fetching secrets from GCP Project ID '{project_id}'.")
    
    try:
        client = secretmanager.SecretManagerServiceClient()
    except Exception as e:
        logger.error(f"Failed to initialize Secret Manager client: {e}")
        raise SystemExit(1)
    
    credentials = {}
    logger.info("Accessing Google Cloud Secret Manager...")

    # Fetch required secrets
    for secret_name in ZOHO_SECRET_NAMES:
        resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        try:
            logger.debug(f"Accessing secret: {secret_name}")
            response = client.access_secret_version(request={"name": resource_name})
            secret_value = response.payload.data.decode("UTF-8")
            credentials[secret_name.lower()] = secret_value
        except exceptions.NotFound:
            logger.error(f"Secret '{secret_name}' not found in project '{project_id}'.")
            raise SystemExit(1)
        except exceptions.PermissionDenied:
            logger.error(f"Permission denied for secret '{secret_name}' in project '{project_id}'.")
            logger.error("Ensure your service account has the 'Secret Manager Secret Accessor' role ON THIS PROJECT.")
            raise SystemExit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching '{secret_name}': {e}")
            raise SystemExit(1)

    # Fetch optional secrets (don't fail if not found)
    for secret_name in OPTIONAL_ZOHO_SECRETS:
        resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        try:
            logger.debug(f"Accessing optional secret: {secret_name}")
            response = client.access_secret_version(request={"name": resource_name})
            secret_value = response.payload.data.decode("UTF-8")
            credentials[secret_name.lower()] = secret_value
        except exceptions.NotFound:
            logger.debug(f"Optional secret '{secret_name}' not found in project '{project_id}', will check environment variables.")
        except exceptions.PermissionDenied:
            logger.warning(f"Permission denied for optional secret '{secret_name}' in project '{project_id}'.")
        except Exception as e:
            logger.warning(f"Error fetching optional secret '{secret_name}': {e}")

    # Add organization_id for backwards compatibility and env fallback
    org_id = credentials.get('zoho_organization_id', '') or os.getenv('ZOHO_ORGANIZATION_ID', '')
    credentials['organization_id'] = org_id
    
    if not org_id:
        logger.warning("Organization ID not found in secrets or environment variables.")
        logger.warning("Set ZOHO_ORGANIZATION_ID environment variable or add to Secret Manager.")
    
    logger.info("All secrets fetched successfully.")
    return credentials
