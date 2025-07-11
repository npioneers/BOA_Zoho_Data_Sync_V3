"""
JSON to Database Sync Package

Package for analyzing consolidated JSON files and creating database tables
to sync data from JSON files to SQLite database.
"""

__version__ = "1.0.0"

from .json_analyzer import JSONAnalyzer
from .table_generator import TableGenerator

__all__ = [
    'JSONAnalyzer',
    'TableGenerator'
]
