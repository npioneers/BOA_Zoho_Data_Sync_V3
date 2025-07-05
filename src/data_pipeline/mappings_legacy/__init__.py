"""
Package initialization for data pipeline mappings.

This package contains mapping configurations for transforming various data sources
to canonical schemas. Each entity has its own mapping configuration module.
"""

from .bills_mapping_config import (
    CANONICAL_BILLS_COLUMNS,
    CSV_COLUMN_MAPPING,
    JSON_HEADER_MAPPING,
    JSON_LINE_ITEM_MAPPING,
    CANONICAL_FIELD_DEFAULTS,
    SCHEMA_INFO
)

__all__ = [
    'CANONICAL_BILLS_COLUMNS',
    'CSV_COLUMN_MAPPING', 
    'JSON_HEADER_MAPPING',
    'JSON_LINE_ITEM_MAPPING',
    'CANONICAL_FIELD_DEFAULTS',
    'SCHEMA_INFO'
]
