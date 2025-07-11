"""
JSON Consolidate Package

Package for consolidating, deduplicating, and validating JSON files
from multiple timestamp directories into unified files.
"""

__version__ = "1.0.0"

from .json_consolidator import JSONConsolidator

__all__ = [
    'JSONConsolidator'
]
