"""
API Sync Package

This package provides tools to fetch data from the Zoho Books API and verify it 
against local data. It is focused on the API fetching and verification components 
of the larger data sync system.
"""

from .core import auth, client, secrets
from .processing import raw_data_handler
from .verification import api_local_verifier
from . import config

__all__ = [
    'auth',
    'client', 
    'secrets',
    'raw_data_handler',
    'api_local_verifier',
    'config'
]

__version__ = "1.0.0"
