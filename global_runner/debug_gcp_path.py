#!/usr/bin/env python3
"""
Debug GCP credentials path resolution
"""
import os
from pathlib import Path

print("=== GCP Credentials Path Debug ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python file location: {__file__}")
print(f"Python file parent: {Path(__file__).parent}")

# Check environment variable
gcp_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
print(f"GOOGLE_APPLICATION_CREDENTIALS env var: '{gcp_creds}'")

# Check if file exists at various paths
test_paths = [
    gcp_creds,
    'gcp-service-key.json',
    './gcp-service-key.json',
    '../api_sync/gcp-service-key.json',
    Path(__file__).parent / 'gcp-service-key.json',
    Path(__file__).parent.parent / 'api_sync' / 'gcp-service-key.json'
]

for path in test_paths:
    if path:
        path_obj = Path(path)
        exists = path_obj.exists()
        abs_path = path_obj.resolve()
        print(f"Path: {path} -> exists: {exists} -> resolved: {abs_path}")

# Load .env and check
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"After loading .env - GOOGLE_APPLICATION_CREDENTIALS: '{os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}'")
except ImportError:
    print("dotenv not available")
