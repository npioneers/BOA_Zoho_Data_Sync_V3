"""
Data Transformation Module for Project Bedrock V3 - Normalized Schema

This module contains transformer classes that convert raw data sources
(CSV backup, JSON API) to normalized database schemas. The key innovation
is the "un-flattening" logic that separates flattened CSV data into 
proper header and line items DataFrames for normalized database storage.

Key Features:
- Un-flattening: CSV → (header_df, line_items_df) 
- Schema-driven transformations using CANONICAL_SCHEMA
- Configuration-driven field mappings
- Robust error handling and validation
- Support for both bulk (CSV) and incremental (JSON) data sources
- Data integrity through BillID relationships
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
import uuid

# Import from the mappings.py file (not the mappings/ directory)
from .mappings import (
    CANONICAL_SCHEMA,
    get_entity_schema,
    get_entity_csv_mapping,
    get_header_columns,
    get_line_item_columns,
    get_all_entities,
    get_entities_with_line_items,
    BILLS_CSV_MAP
)

# Configure logging
logger = logging.getLogger(__name__)


class BillsTransformer:
    """
    Transformer class for Bills entity with normalized schema support.
    
    Key Innovation: Un-flattening logic that takes flattened CSV data and 
    separates it into proper Bills header and Bills_LineItems DataFrames 
    for normalized database storage.
    
    Features:
    - transform_from_csv(): Returns (header_df, line_items_df) tuple
    - Schema-driven field separation using CANONICAL_SCHEMA
    - Automatic LineItemID generation for line items
    - Data integrity through BillID relationships
    - Metadata enrichment (DataSource, ProcessedTime)
    """
    
    def __init__(self):
        """Initialize the BillsTransformer with normalized schema configurations."""
        # Entity configuration
        self.entity_name = 'Bills'
        self.entity_schema = get_entity_schema(self.entity_name)
        
        if not self.entity_schema:
            raise ValueError(f"No schema found for entity: {self.entity_name}")
        
        # Get schema definitions using new helper functions
        self.header_columns = get_header_columns(self.entity_name)
        self.line_items_columns = get_line_item_columns(self.entity_name)
        self.schema = CANONICAL_SCHEMA
        
        # Mapping configurations using new CSV mappings
        self.csv_mapping = BILLS_CSV_MAP
        self.has_line_items = self.entity_schema['has_line_items']
        
        # Field defaults (simplified - can be enhanced later)
        self.field_defaults = {}
        
        logger.info(f"BillsTransformer initialized for normalized schema:")
        logger.info(f"  Entity: {self.entity_name}")
        logger.info(f"  Header columns: {len(self.header_columns)}")
        logger.info(f"  Line item columns: {len(self.line_items_columns)}")
        logger.info(f"  Has line items: {self.has_line_items}")
    
    def transform_from_csv(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform flattened CSV backup data into normalized header and line items DataFrames.
        
        This is the core "un-flattening" logic that separates a flattened CSV structure
        into proper normalized tables for the database.
        
        Args:
            df: Flattened DataFrame from CSV backup (each row is a bill line item)
            
        Returns:
            Tuple of (header_df, line_items_df) where:
            - header_df: Unique bill headers with Bills table schema
            - line_items_df: All line items with Bills_LineItems table schema
            
        Raises:
            ValueError: If required columns are missing or transformation fails
        """
        logger.info(f"Starting CSV un-flattening transformation for {len(df)} records")
        
        if df.empty:
            logger.warning("Input DataFrame is empty, returning empty normalized DataFrames")
            return self._create_empty_normalized_dataframes()
        
        try:
            # Step 1: Apply column mapping from CSV to canonical names
            mapped_df = df.copy()
            mapped_df = mapped_df.rename(columns=self.csv_mapping)
            logger.debug(f"Applied CSV column mapping")
            
            # Step 2: Add metadata fields
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            mapped_df['DataSource'] = 'CSV_BACKUP'
            mapped_df['ProcessedTime'] = current_time
            
            # Step 3: Create Bills Header DataFrame
            header_df = self._extract_bills_header(mapped_df)
            logger.info(f"Extracted {len(header_df)} unique bill headers")
            
            # Step 4: Create Bills Line Items DataFrame  
            line_items_df = self._extract_bills_line_items(mapped_df)
            logger.info(f"Extracted {len(line_items_df)} line items")
            
            # Step 5: Validate the transformation
            self._validate_normalized_transformation(header_df, line_items_df)
            
            logger.info(f"[SUCCESS] Successfully un-flattened CSV data:")
            logger.info(f"  [HEADERS] Headers: {len(header_df)} unique bills")
            logger.info(f"  [LINE_ITEMS] Line Items: {len(line_items_df)} items")
            
            return header_df, line_items_df
            
        except Exception as e:
            logger.error(f"CSV un-flattening transformation failed: {str(e)}")
            raise ValueError(f"Failed to transform CSV data: {str(e)}")
    
    def _extract_bills_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract unique bill headers from flattened data."""
        # Identify header columns that exist in the data
        available_header_cols = [col for col in self.header_columns if col in df.columns]
        
        # Extract header data and remove duplicates by BillID
        if 'BillID' in available_header_cols:
            header_df = df[available_header_cols].drop_duplicates(subset=['BillID'])
        else:
            # Fallback: use all available header columns
            header_df = df[available_header_cols].drop_duplicates()
            logger.warning("BillID column not found, using all header columns for deduplication")
        
        # Add missing header columns with defaults
        for col in self.header_columns:
            if col not in header_df.columns:
                default_value = self.field_defaults.get(col, '')
                header_df[col] = default_value
                logger.debug(f"Added missing header column '{col}' with default value")
        
        # Ensure correct column order
        header_df = header_df.reindex(columns=self.header_columns, fill_value='')
        
        # Reset index for clean DataFrame
        header_df = header_df.reset_index(drop=True)
        
        return header_df
    
    def _extract_bills_line_items(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract line items data with generated LineItemIDs."""
        # Identify line item columns that exist in the data
        available_line_item_cols = [col for col in self.line_items_columns if col in df.columns]
        
        # Extract line items data (all rows since each row represents a line item)
        line_items_df = df[available_line_item_cols].copy()
        
        # Generate unique LineItemID for each line item
        line_items_df['LineItemID'] = [f"LI_{uuid.uuid4().hex[:12].upper()}" for _ in range(len(line_items_df))]
        
        # Ensure BillID exists for foreign key relationship
        if 'BillID' not in line_items_df.columns:
            # Try to use any ID-like column as fallback
            id_columns = [col for col in df.columns if 'ID' in col or 'id' in col]
            if id_columns:
                line_items_df['BillID'] = df[id_columns[0]]
                logger.warning(f"BillID not found, using {id_columns[0]} as foreign key")
            else:
                # Generate placeholder BillIDs
                line_items_df['BillID'] = [f"BILL_{i:06d}" for i in range(len(line_items_df))]
                logger.warning("No suitable BillID found, generated placeholder BillIDs")
        
        # Add missing line item columns with defaults
        for col in self.line_items_columns:
            if col not in line_items_df.columns:
                default_value = self.field_defaults.get(col, '')
                line_items_df[col] = default_value
                logger.debug(f"Added missing line item column '{col}' with default value")
        
        # Ensure correct column order
        line_items_df = line_items_df.reindex(columns=self.line_items_columns, fill_value='')
        
        # Reset index for clean DataFrame
        line_items_df = line_items_df.reset_index(drop=True)
        
        return line_items_df
    
    def transform_from_json(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform JSON API data to normalized header and line items DataFrames.
        
        Handles nested line_items by creating proper normalized structure
        for the database.
        
        Args:
            df: DataFrame with JSON API structure (snake_case, nested line_items)
            
        Returns:
            Tuple of (header_df, line_items_df) for normalized storage
            
        Raises:
            ValueError: If transformation fails or invalid JSON structure
        """
        logger.info(f"Starting JSON transformation for {len(df)} records")
        
        if df.empty:
            logger.warning("Input DataFrame is empty, returning empty normalized DataFrames")
            return self._create_empty_normalized_dataframes()
        
        try:
            header_rows = []
            line_item_rows = []
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            for index, bill_row in df.iterrows():
                logger.debug(f"Processing JSON bill row {index}")
                
                # Extract bill header information
                bill_data = bill_row.to_dict()
                line_items = bill_data.pop('line_items', [])
                
                # Create header record
                header_record = {}
                for json_field, canonical_field in self.json_header_mapping.items():
                    header_record[canonical_field] = bill_data.get(json_field, '')
                
                # Add metadata
                header_record['DataSource'] = 'JSON_API'
                header_record['ProcessedTime'] = current_time
                header_rows.append(header_record)
                
                # Create line item records
                if line_items:
                    for line_item in line_items:
                        line_item_record = {}
                        
                        # Map line item fields
                        for json_field, canonical_field in self.json_line_item_mapping.items():
                            line_item_record[canonical_field] = line_item.get(json_field, '')
                        
                        # Add foreign key relationship
                        line_item_record['BillID'] = bill_data.get('bill_id', f"BILL_{index:06d}")
                        
                        # Generate unique LineItemID
                        line_item_record['LineItemID'] = f"LI_{uuid.uuid4().hex[:12].upper()}"
                        
                        # Add metadata
                        line_item_record['DataSource'] = 'JSON_API'
                        line_item_record['ProcessedTime'] = current_time
                        
                        line_item_rows.append(line_item_record)
                else:
                    # Create empty line item if none exist
                    empty_line_item = {
                        'BillID': bill_data.get('bill_id', f"BILL_{index:06d}"),
                        'LineItemID': f"LI_{uuid.uuid4().hex[:12].upper()}",
                        'DataSource': 'JSON_API',
                        'ProcessedTime': current_time
                    }
                    line_item_rows.append(empty_line_item)
            
            # Create DataFrames
            header_df = pd.DataFrame(header_rows) if header_rows else pd.DataFrame(columns=self.header_columns)
            line_items_df = pd.DataFrame(line_item_rows) if line_item_rows else pd.DataFrame(columns=self.line_items_columns)
            
            # Add missing fields and ensure proper structure
            header_df = self._ensure_header_structure(header_df)
            line_items_df = self._ensure_line_items_structure(line_items_df)
            
            # Validate the transformation
            self._validate_normalized_transformation(header_df, line_items_df)
            
            logger.info(f"[SUCCESS] Successfully transformed JSON data:")
            logger.info(f"  [HEADERS] Headers: {len(header_df)} bills")
            logger.info(f"  [LINE_ITEMS] Line Items: {len(line_items_df)} items")
            
            return header_df, line_items_df
            
        except Exception as e:
            logger.error(f"JSON transformation failed: {str(e)}")
            raise ValueError(f"Failed to transform JSON data: {str(e)}")
    
    def _ensure_header_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure header DataFrame has correct structure and column order."""
        # Add missing columns with defaults
        for col in self.header_columns:
            if col not in df.columns:
                default_value = self.field_defaults.get(col, '')
                df[col] = default_value
        
        # Ensure correct column order
        df = df.reindex(columns=self.header_columns, fill_value='')
        return df.reset_index(drop=True)
    
    def _ensure_line_items_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure line items DataFrame has correct structure and column order."""
        # Add missing columns with defaults
        for col in self.line_items_columns:
            if col not in df.columns:
                default_value = self.field_defaults.get(col, '')
                df[col] = default_value
        
        # Ensure correct column order
        df = df.reindex(columns=self.line_items_columns, fill_value='')
        return df.reset_index(drop=True)
    
    def _validate_normalized_transformation(self, header_df: pd.DataFrame, line_items_df: pd.DataFrame) -> None:
        """Validate that normalized transformation produced correct schemas."""
        # Validate header DataFrame
        if list(header_df.columns) != self.header_columns:
            missing = set(self.header_columns) - set(header_df.columns)
            extra = set(header_df.columns) - set(self.header_columns)
            error_msg = f"Header DataFrame validation failed. Missing: {missing}, Extra: {extra}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate line items DataFrame
        if list(line_items_df.columns) != self.line_items_columns:
            missing = set(self.line_items_columns) - set(line_items_df.columns)
            extra = set(line_items_df.columns) - set(self.line_items_columns)
            error_msg = f"Line items DataFrame validation failed. Missing: {missing}, Extra: {extra}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate BillID relationship integrity
        if not line_items_df.empty and not header_df.empty:
            header_bill_ids = set(header_df['BillID'].dropna())
            line_item_bill_ids = set(line_items_df['BillID'].dropna())
            orphaned_line_items = line_item_bill_ids - header_bill_ids
            
            if orphaned_line_items:
                logger.warning(f"Found {len(orphaned_line_items)} orphaned line items (no matching header)")
        
        logger.debug("Normalized transformation validation passed")
    
    def _create_empty_normalized_dataframes(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create empty DataFrames with correct normalized schemas."""
        header_df = pd.DataFrame(columns=self.header_columns)
        line_items_df = pd.DataFrame(columns=self.line_items_columns)
        return header_df, line_items_df
    
    # Legacy flattened transformation methods (for backward compatibility)
    def transform_from_csv_flattened(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Legacy method: Transform CSV to flattened canonical schema.
        
        This method is maintained for backward compatibility but the preferred
        approach is to use transform_from_csv() which returns normalized DataFrames.
        
        Args:
            df: DataFrame with CSV backup structure
            
        Returns:
            DataFrame with flattened canonical schema (all columns in one table)
        """
        logger.warning("Using legacy flattened transformation - consider using normalized approach")
        
        # Get normalized DataFrames
        header_df, line_items_df = self.transform_from_csv(df)
        
        # Merge back into flattened structure
        if header_df.empty or line_items_df.empty:
            return pd.DataFrame()
        
        # Join header and line items on BillID
        flattened_df = line_items_df.merge(header_df, on='BillID', how='left', suffixes=('', '_header'))
        
        # Remove duplicate columns
        duplicate_cols = [col for col in flattened_df.columns if col.endswith('_header')]
        flattened_df = flattened_df.drop(columns=duplicate_cols)
        
        return flattened_df
    
    # Utility and validation methods
    def get_header_columns(self) -> List[str]:
        """Get the list of Bills header column names."""
        return self.header_columns.copy()
    
    def get_line_items_columns(self) -> List[str]:
        """Get the list of Bills line items column names."""
        return self.line_items_columns.copy()
    
    def validate_csv_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that CSV DataFrame has required columns for transformation.
        
        Args:
            df: CSV DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        csv_columns = set(df.columns)
        mapped_columns = set(self.csv_mapping.keys())
        
        available = csv_columns.intersection(mapped_columns)
        missing = mapped_columns - csv_columns
        unmapped = csv_columns - mapped_columns
        
        validation_result = {
            'is_valid': len(missing) == 0,
            'available_columns': list(available),
            'missing_columns': list(missing),
            'unmapped_columns': list(unmapped),
            'total_csv_columns': len(csv_columns),
            'total_mapped_columns': len(mapped_columns),
            'mapping_coverage': len(available) / len(mapped_columns) if mapped_columns else 0
        }
        
        logger.info(f"CSV validation: {len(available)}/{len(mapped_columns)} columns available, "
                   f"{len(missing)} missing, {len(unmapped)} unmapped")
        
        return validation_result
    
    def validate_json_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that JSON DataFrame has required structure for transformation.
        
        Args:
            df: JSON DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        if df.empty:
            return {'is_valid': False, 'error': 'DataFrame is empty'}
        
        json_columns = set(df.columns)
        header_columns = set(self.json_header_mapping.keys())
        
        available_headers = json_columns.intersection(header_columns)
        missing_headers = header_columns - json_columns
        
        # Check for line_items column
        has_line_items = 'line_items' in json_columns
        
        # Sample line items structure if available
        line_items_valid = False
        sample_line_items = []
        
        if has_line_items and len(df) > 0:
            try:
                first_line_items = df['line_items'].iloc[0]
                if isinstance(first_line_items, list) and len(first_line_items) > 0:
                    sample_line_items = list(first_line_items[0].keys())
                    line_item_columns = set(sample_line_items)
                    expected_line_item_columns = set(self.json_line_item_mapping.keys())
                    line_items_valid = len(line_item_columns.intersection(expected_line_item_columns)) > 0
            except Exception as e:
                logger.warning(f"Could not analyze line_items structure: {str(e)}")
        
        validation_result = {
            'is_valid': len(missing_headers) == 0 and has_line_items,
            'available_header_columns': list(available_headers),
            'missing_header_columns': list(missing_headers),
            'has_line_items_field': has_line_items,
            'line_items_structure_valid': line_items_valid,
            'sample_line_item_fields': sample_line_items,
            'total_json_columns': len(json_columns),
            'header_mapping_coverage': len(available_headers) / len(header_columns) if header_columns else 0
        }
        
        logger.info(f"JSON validation: {len(available_headers)}/{len(header_columns)} header columns available, "
                   f"line_items field: {has_line_items}, structure valid: {line_items_valid}")
        
        return validation_result
    
    def get_transformation_stats(self, header_df: pd.DataFrame, line_items_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about a normalized transformation.
        
        Args:
            header_df: Bills header DataFrame
            line_items_df: Bills line items DataFrame
            
        Returns:
            Dictionary with transformation statistics
        """
        stats = {
            'header_records': len(header_df),
            'line_item_records': len(line_items_df),
            'header_columns': len(header_df.columns),
            'line_item_columns': len(line_items_df.columns),
            'total_records': len(header_df) + len(line_items_df),
            'unique_bills': header_df['BillID'].nunique() if 'BillID' in header_df.columns else 0,
            'avg_line_items_per_bill': len(line_items_df) / len(header_df) if len(header_df) > 0 else 0
        }
        
        return stats


class UniversalTransformer:
    """
    Universal transformer class that can handle any entity from the canonical schema.
    
    This class provides entity-agnostic transformation capabilities using the 
    CANONICAL_SCHEMA and CSV mapping dictionaries. It can handle both entities
    with line items and standalone entities.
    
    Features:
    - Entity-agnostic: Works with any entity in CANONICAL_SCHEMA
    - Automatic schema detection and configuration
    - Support for entities with/without line items
    - Consistent transformation interface across all entities
    - Built-in validation and error handling
    """
    
    def __init__(self, entity_name: str):
        """
        Initialize the UniversalTransformer for a specific entity.
        
        Args:
            entity_name: Name of the entity (e.g., 'Invoices', 'Bills', 'Items')
            
        Raises:
            ValueError: If entity is not supported or has no schema definition
        """
        self.entity_name = entity_name
        
        # Validate entity is supported
        if entity_name not in get_all_entities():
            raise ValueError(f"Unsupported entity: {entity_name}. "
                           f"Supported entities: {get_all_entities()}")
        
        # Get entity schema and configuration
        self.entity_schema = get_entity_schema(entity_name)
        if not self.entity_schema:
            raise ValueError(f"No schema found for entity: {entity_name}")
        
        # Extract schema information
        self.header_columns = get_header_columns(entity_name)
        self.line_items_columns = get_line_item_columns(entity_name)
        self.has_line_items = self.entity_schema['has_line_items']
        self.header_table = self.entity_schema['header_table']
        self.line_items_table = self.entity_schema.get('line_items_table')
        self.primary_key = self.entity_schema['primary_key']
        self.foreign_key = self.entity_schema.get('foreign_key')
        
        # Get CSV mapping
        self.csv_mapping = get_entity_csv_mapping(entity_name)
        if not self.csv_mapping:
            logger.warning(f"No CSV mapping found for entity: {entity_name}")
        
        # Field defaults (can be enhanced later)
        self.field_defaults = {}
        
        logger.info(f"UniversalTransformer initialized for entity: {entity_name}")
        logger.info(f"  Header table: {self.header_table}")
        logger.info(f"  Header columns: {len(self.header_columns)}")
        logger.info(f"  Has line items: {self.has_line_items}")
        if self.has_line_items:
            logger.info(f"  Line items table: {self.line_items_table}")
            logger.info(f"  Line item columns: {len(self.line_items_columns)}")
    
    def transform_from_csv(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        Transform CSV data for any entity into normalized header and line items DataFrames.
        
        Args:
            df: Raw CSV DataFrame to transform
            
        Returns:
            Tuple of (header_df, line_items_df). line_items_df is None for standalone entities.
            
        Raises:
            ValueError: If transformation fails or data is invalid
        """
        if df.empty:
            raise ValueError(f"Cannot transform empty DataFrame for entity: {self.entity_name}")
        
        if not self.csv_mapping:
            raise ValueError(f"No CSV mapping available for entity: {self.entity_name}")
        
        try:
            logger.info(f"[TRANSFORM] Starting CSV transformation for entity: {self.entity_name}")
            logger.info(f"  Input records: {len(df)}")
            logger.info(f"  Input columns: {len(df.columns)}")
            
            # Step 1: Apply CSV column mapping
            mapped_df = self._apply_csv_mapping(df)
            logger.debug(f"Applied CSV column mapping for {self.entity_name}")
            
            # Step 2: Add metadata fields
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            mapped_df['DataSource'] = 'CSV_BACKUP'
            mapped_df['ProcessedTime'] = current_time
            
            # Step 3: Extract header DataFrame
            header_df = self._extract_header_data(mapped_df)
            logger.info(f"Extracted {len(header_df)} unique {self.entity_name} headers")
            
            # Step 4: Extract line items DataFrame (if applicable)
            line_items_df = None
            if self.has_line_items:
                line_items_df = self._extract_line_items_data(mapped_df)
                logger.info(f"Extracted {len(line_items_df)} line items")
            
            # Step 5: Validate the transformation
            self._validate_transformation(header_df, line_items_df)
            
            logger.info(f"[SUCCESS] Successfully transformed CSV data for {self.entity_name}:")
            logger.info(f"  [HEADERS] Headers: {len(header_df)} records")
            if line_items_df is not None:
                logger.info(f"  [LINE_ITEMS] Line Items: {len(line_items_df)} records")
            
            return header_df, line_items_df
            
        except Exception as e:
            logger.error(f"CSV transformation failed for {self.entity_name}: {str(e)}")
            raise ValueError(f"Failed to transform CSV data for {self.entity_name}: {str(e)}")
    
    def _apply_csv_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply CSV column mapping to transform column names to canonical format."""
        # Find columns that exist in both CSV and our mapping
        available_mappings = {csv_col: canonical_col 
                            for csv_col, canonical_col in self.csv_mapping.items() 
                            if csv_col in df.columns}
        
        if not available_mappings:
            raise ValueError(f"No CSV columns found that match the mapping for {self.entity_name}")
        
        # Apply the mapping
        mapped_df = df.rename(columns=available_mappings)
        
        logger.debug(f"Mapped {len(available_mappings)} columns for {self.entity_name}")
        return mapped_df
    
    def _extract_header_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract header data from the mapped DataFrame."""
        # Identify header columns that exist in the data
        available_header_cols = [col for col in self.header_columns if col in df.columns]
        
        if not available_header_cols:
            raise ValueError(f"No header columns found in data for {self.entity_name}")
        
        # Extract header data and remove duplicates by primary key
        if self.primary_key in available_header_cols:
            header_df = df[available_header_cols].drop_duplicates(subset=[self.primary_key])
        else:
            # Fallback: use all available header columns
            header_df = df[available_header_cols].drop_duplicates()
            logger.warning(f"Primary key '{self.primary_key}' not found for {self.entity_name}, "
                         f"using all header columns for deduplication")
        
        # Add missing header columns with defaults
        for col in self.header_columns:
            if col not in header_df.columns:
                default_value = self.field_defaults.get(col, '')
                header_df[col] = default_value
                logger.debug(f"Added missing header column '{col}' with default value")
        
        # Ensure correct column order
        header_df = header_df.reindex(columns=self.header_columns, fill_value='')
        
        return header_df.reset_index(drop=True)
    
    def _extract_line_items_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract line items data from the mapped DataFrame."""
        if not self.has_line_items:
            return pd.DataFrame()
        
        # Identify line item columns that exist in the data
        available_line_cols = [col for col in self.line_items_columns if col in df.columns]
        
        if not available_line_cols:
            logger.warning(f"No line item columns found in data for {self.entity_name}")
            return pd.DataFrame()
        
        # Extract line items data
        line_items_df = df[available_line_cols].copy()
        
        # Generate line item IDs if not present
        line_item_pk = self.entity_schema.get('line_item_pk')
        if line_item_pk and line_item_pk not in line_items_df.columns:
            line_items_df[line_item_pk] = [f"{self.entity_name}_LI_{uuid.uuid4().hex[:8]}" 
                                         for _ in range(len(line_items_df))]
            logger.debug(f"Generated {line_item_pk} for line items")
        
        # Add missing line item columns with defaults
        for col in self.line_items_columns:
            if col not in line_items_df.columns:
                default_value = self.field_defaults.get(col, '')
                line_items_df[col] = default_value
                logger.debug(f"Added missing line item column '{col}' with default value")
        
        # Ensure correct column order
        line_items_df = line_items_df.reindex(columns=self.line_items_columns, fill_value='')
        
        return line_items_df.reset_index(drop=True)
    
    def _validate_transformation(self, header_df: pd.DataFrame, 
                               line_items_df: Optional[pd.DataFrame] = None) -> None:
        """Validate the transformation results."""
        # Validate header DataFrame
        if header_df.empty:
            raise ValueError(f"Header DataFrame is empty for {self.entity_name}")
        
        # Check for primary key
        if self.primary_key not in header_df.columns:
            raise ValueError(f"Primary key '{self.primary_key}' missing in header data")
        
        # Check for null primary keys
        null_pks = header_df[self.primary_key].isnull().sum()
        if null_pks > 0:
            raise ValueError(f"Found {null_pks} null primary keys in header data")
        
        # Validate line items if applicable
        if self.has_line_items and line_items_df is not None:
            if line_items_df.empty:
                logger.warning(f"Line items DataFrame is empty for {self.entity_name}")
            else:
                # Check foreign key relationship
                if self.foreign_key and self.foreign_key in line_items_df.columns:
                    header_ids = set(header_df[self.primary_key].values)
                    line_item_ids = set(line_items_df[self.foreign_key].values)
                    orphaned_items = line_item_ids - header_ids
                    
                    if orphaned_items:
                        logger.warning(f"Found {len(orphaned_items)} orphaned line items for {self.entity_name}")
        
        logger.debug(f"Validation passed for {self.entity_name} transformation")
    
    def get_supported_entities(self) -> List[str]:
        """Get list of all supported entities."""
        return get_all_entities()
    
    def get_entities_with_line_items(self) -> List[str]:
        """Get list of entities that have line items."""
        return get_entities_with_line_items()
    
    def get_transformation_stats(self, header_df: pd.DataFrame, 
                               line_items_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Get statistics about a transformation.
        
        Args:
            header_df: Header DataFrame
            line_items_df: Line items DataFrame (optional)
            
        Returns:
            Dictionary with transformation statistics
        """
        stats = {
            'entity_name': self.entity_name,
            'header_table': self.header_table,
            'header_records': len(header_df),
            'header_columns': len(header_df.columns),
            'has_line_items': self.has_line_items
        }
        
        if line_items_df is not None:
            stats.update({
                'line_items_table': self.line_items_table,
                'line_item_records': len(line_items_df),
                'line_item_columns': len(line_items_df.columns),
                'total_records': len(header_df) + len(line_items_df)
            })
            
            # Calculate average line items per header record
            if len(header_df) > 0:
                stats['avg_line_items_per_header'] = len(line_items_df) / len(header_df)
        else:
            stats['total_records'] = len(header_df)
        
        return stats


# Factory function for creating transformers
def create_transformer(entity_name: str) -> UniversalTransformer:
    """
    Factory function to create a transformer for any supported entity.
    
    Args:
        entity_name: Name of the entity (e.g., 'Invoices', 'Bills', 'Items')
        
    Returns:
        UniversalTransformer instance configured for the entity
        
    Raises:
        ValueError: If entity is not supported
    """
    return UniversalTransformer(entity_name)
