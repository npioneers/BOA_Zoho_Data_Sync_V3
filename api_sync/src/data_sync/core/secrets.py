import os
from dotenv import load_dotenv
from google.cloud import secretmanager
from google.api_core import exceptions

ZOHO_SECRET_NAMES = [
    "ZOHO_CLIENT_ID",
    "ZOHO_CLIENT_SECRET",
    "ZOHO_REFRESH_TOKEN",
]

def get_zoho_credentials() -> dict[str, str]:
    """
    Fetches Zoho credentials from Google Cloud Secret Manager.

    This function relies on GOOGLE_APPLICATION_CREDENTIALS for authentication.
    It reads the GCP_PROJECT_ID from a .env file to know which project to get secrets from.
    """
    print("INFO: Loading environment variables from .env file...")
    load_dotenv()

    # The project where the SECRETS are stored.
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        print("ERROR: GCP_PROJECT_ID environment variable not set.")
        print("Please create a .env file in the project root with GCP_PROJECT_ID='your-project-id'")
        raise SystemExit(1)

    print(f"INFO: Fetching secrets from GCP Project ID '{project_id}'.")
    client = secretmanager.SecretManagerServiceClient()
    
    credentials = {}
    print("INFO: Accessing Google Cloud Secret Manager...")

    for secret_name in ZOHO_SECRET_NAMES:
        resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        try:
            print(f"  - Accessing secret: {secret_name}")
            response = client.access_secret_version(request={"name": resource_name})
            secret_value = response.payload.data.decode("UTF-8")
            credentials[secret_name.lower()] = secret_value
        except exceptions.NotFound:
            print(f"ERROR: Secret '{secret_name}' not found in project '{project_id}'.")
            raise SystemExit(1)
        except exceptions.PermissionDenied:
            print(f"ERROR: Permission denied for secret '{secret_name}' in project '{project_id}'.")
            print(f"  - Ensure your service account has the 'Secret Manager Secret Accessor' role ON THIS PROJECT.")
            raise SystemExit(1)
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while fetching '{secret_name}': {e}")
            raise SystemExit(1)

    print("INFO: All secrets fetched successfully.")
    return credentials
