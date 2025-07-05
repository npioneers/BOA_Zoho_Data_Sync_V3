"""
Base Builder Module for Project Bedrock V2

This module handles the initial database population from CSV backup data.
It creates the canonical schema and loads the foundational dataset.

Responsibilities:
- Load CSV backup data (complete historical dataset)
- Transform CSV to canonical schema
- Create clean database with canonical tables
- Establish baseline for incremental updates

Adheres to operational guidelines: Configuration-driven, no hardcoded values
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .config import get_config_manager
from .database import DatabaseHandler
from .transformer import BillsTransformer
from .mappings import get_entity_schema

logger = logging.getLogger(__name__)


class BaseBuilder:
    """
    Handles initial database population from CSV backup data.
    
    This class is responsible for creating a clean canonical database
    from CSV backup files. It establishes the baseline that incremental
    updates will build upon.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize BaseBuilder.
        
        Args:
            config_manager: Optional ConfigurationManager instance
        """
        self.config = config_manager or get_config_manager()
        self.db_handler = DatabaseHandler()
        self.transformer = BillsTransformer()
        self.stats = {
            'csv_records_loaded': 0,
            'csv_records_transformed': 0,
            'build_start_time': None,
            'build_end_time': None,
            'build_duration': None
        }
        
        logger.info("BaseBuilder initialized")
    
    def build_base_database(self, clean_rebuild: bool = True) -> Dict[str, Any]:
        """
        Build base database from CSV backup data.
        
        Args:
            clean_rebuild: If True, creates fresh database. If False, appends to existing.
            
        Returns:
            Dictionary with build statistics and results
        """
        self.stats['build_start_time'] = datetime.now()
        logger.info("🏗️ Starting base database build from CSV backup")
        
        try:
            # Step 1: Load and validate CSV data
            csv_data = self._load_csv_backup()
            if csv_data.empty:
                raise ValueError("No CSV data found - cannot build base database")
            
            # Step 2: Transform CSV to canonical schema
            canonical_data = self._transform_csv_data(csv_data)
            
            # Step 3: Create database schema and load data
            load_stats = self._create_and_load_database(canonical_data, clean_rebuild)
            
            # Step 4: Create analysis views
            self._create_analysis_views()
            
            # Update final statistics
            self.stats['build_end_time'] = datetime.now()
            self.stats['build_duration'] = (
                self.stats['build_end_time'] - self.stats['build_start_time']
            ).total_seconds()
            
            # Combine all statistics
            final_stats = {**self.stats, **load_stats}
            
            logger.info(f"✅ Base database build completed in {self.stats['build_duration']:.2f} seconds")
            return final_stats
            
        except Exception as e:
            logger.error(f"❌ Base database build failed: {e}")
            raise
    
    def _load_csv_backup(self) -> pd.DataFrame:
        """Load CSV backup data from configured source."""
        logger.info("📊 Loading CSV backup data")
        
        # Get CSV source path
        data_paths = self.config.get_data_source_paths()
        csv_backup_path = Path(data_paths['csv_backup_path'])
        bills_csv_file = csv_backup_path / self.config.get('entities', 'bills', 'csv_file')
        
        logger.info(f"📁 CSV Source: {bills_csv_file}")
        
        if not bills_csv_file.exists():
            raise FileNotFoundError(f"CSV backup file not found: {bills_csv_file}")
        
        # Load CSV data
        csv_data = pd.read_csv(bills_csv_file)
        self.stats['csv_records_loaded'] = len(csv_data)
        
        logger.info(f"✅ Loaded {len(csv_data)} records from CSV backup")
        logger.debug(f"📋 CSV columns: {list(csv_data.columns)}")
        
        return csv_data
    
    def _transform_csv_data(self, csv_data: pd.DataFrame) -> pd.DataFrame:
        """Transform CSV data to canonical schema."""
        logger.info("🔄 Transforming CSV data to canonical schema")
        
        try:
            canonical_data = self.transformer.transform_from_csv(csv_data)
            self.stats['csv_records_transformed'] = len(canonical_data)
            
            logger.info(f"✅ Transformed {len(canonical_data)} records to canonical schema")
            return canonical_data
            
        except Exception as e:
            logger.error(f"❌ CSV transformation failed: {e}")
            raise
    
    def _create_and_load_database(self, canonical_data: pd.DataFrame, clean_rebuild: bool) -> Dict[str, Any]:
        """Create database schema and load canonical data."""
        table_name = self.config.get('entities', 'bills', 'table_name')
        
        logger.info(f"🏗️ Creating database schema and loading data: {table_name}")
        
        try:
            with self.db_handler:
                # Create canonical table (handles clean rebuild if specified)
                if clean_rebuild:
                    logger.info("🧹 Clean rebuild: dropping existing table if present")
                    self.db_handler.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                
                # Get Bills schema from the new mappings
                bills_schema = get_entity_schema('Bills')
                bills_header_columns = bills_schema['header_columns']
                
                self.db_handler.create_canonical_table(table_name, bills_header_columns)
                
                # Load data
                load_mode = 'replace' if clean_rebuild else 'append'
                load_stats = self.db_handler.load_data(table_name, canonical_data, if_exists=load_mode)
                
                logger.info(f"✅ Database creation and loading completed")
                return load_stats
                
        except Exception as e:
            logger.error(f"❌ Database creation/loading failed: {e}")
            raise
    
    def _create_analysis_views(self) -> None:
        """Create analysis views for the canonical table."""
        table_name = self.config.get('entities', 'bills', 'table_name')
        
        logger.info("📊 Creating analysis views")
        
        try:
            with self.db_handler:
                self.db_handler.create_analysis_views(table_name)
                logger.info("✅ Analysis views created successfully")
                
        except Exception as e:
            logger.warning(f"⚠️ Analysis view creation failed (non-critical): {e}")
    
    def validate_base_build(self) -> bool:
        """
        Validate the base database build.
        
        Returns:
            True if validation passes, False otherwise
        """
        table_name = self.config.get('entities', 'bills', 'table_name')
        
        logger.info("✅ Validating base database build")
        
        try:
            with self.db_handler:
                # Validate table structure and data
                bills_schema = get_entity_schema('Bills')
                bills_header_columns = bills_schema['header_columns']
                validation_passed = self.db_handler.validate_data_load(table_name, bills_header_columns)
                
                if validation_passed:
                    # Get table info for logging
                    table_info = self.db_handler.get_table_info(table_name)
                    logger.info(f"✅ Base build validation passed")
                    logger.info(f"   📊 Records: {table_info['record_count']:,}")
                    logger.info(f"   📋 Columns: {table_info['column_count']}")
                    
                else:
                    logger.error("❌ Base build validation failed")
                
                return validation_passed
                
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return False
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """Get detailed build statistics."""
        return self.stats.copy()


# Convenience function for simple base building
def build_base_from_csv(clean_rebuild: bool = True, config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to build base database from CSV.
    
    Args:
        clean_rebuild: If True, creates fresh database
        config_file: Optional path to configuration file
        
    Returns:
        Build statistics dictionary
    """
    from .config import reload_config
    
    # Reload config if specified
    if config_file:
        config_manager = reload_config(config_file)
    else:
        config_manager = get_config_manager()
    
    # Build base database
    builder = BaseBuilder(config_manager)
    stats = builder.build_base_database(clean_rebuild)
    
    # Validate build
    validation_passed = builder.validate_base_build()
    stats['validation_passed'] = validation_passed
    
    return stats
