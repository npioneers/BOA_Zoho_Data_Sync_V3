"""
Rebuild Orchestrator for Project Bedrock V3 - Complete ETL Pipeline

This module contains the high-level orchestrator that manages the entire database
rebuild process. It coordinates between the Universal Transformer and DatabaseHandler
to execute the full ETL pipeline for all entities.

Key Features:
- Complete database rebuild orchestration
- Safety protocols with backup and validation
- Entity manifest-driven processing
- Progress tracking and comprehensive logging
- Schema creation and view generation
- End-to-end data integrity validation

Architecture:
- Orchestrator -> Transformer -> returns data -> Orchestrator -> DatabaseHandler -> saves data
- Clean separation of concerns: business logic vs. technical operations
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

from .config import get_config_manager
from .database import DatabaseHandler
from .transformer import create_transformer
from .mappings import get_all_entities, get_entity_csv_mapping

# Configure logging
logger = logging.getLogger(__name__)


class RebuildOrchestrator:
    """
    High-level orchestrator for managing complete database rebuild operations.
    
    This class coordinates the entire ETL pipeline by:
    1. Managing safety protocols (backup/clear)
    2. Creating database schemas for all entities
    3. Processing each entity through transformation and loading
    4. Creating views and performing final validation
    
    The orchestrator delegates technical operations to specialized components
    while maintaining control over the overall business workflow.
    """
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize the RebuildOrchestrator with required components.
        
        Args:
            database_path: Optional path to database file. If None, uses configuration.
        """
        # Initialize configuration
        self.config_manager = get_config_manager()
        self.processing_config = self.config_manager.get_processing_config()
        
        # Initialize database handler
        self.db_handler = DatabaseHandler(database_path)
        
        # Get data paths
        self.data_paths = self.config_manager.get_data_source_paths()
        self.csv_base_path = Path(self.data_paths['csv_backup_path'])
        
        # Define entity processing manifest
        self.entity_manifest = self._build_entity_manifest()
        
        # Processing statistics
        self.processing_stats = {
            'entities_processed': 0,
            'total_input_records': 0,
            'total_output_records': 0,
            'processing_errors': [],
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"RebuildOrchestrator initialized:")
        logger.info(f"  Database: {self.db_handler.db_path}")
        logger.info(f"  CSV Path: {self.csv_base_path}")
        logger.info(f"  Entities: {len(self.entity_manifest)} in manifest")
    
    def _build_entity_manifest(self) -> List[Dict[str, Any]]:
        """
        Build the entity processing manifest with CSV file mappings.
        
        Returns:
            List of entity configurations for processing
        """
        # Define entity-to-CSV file mapping (entities with CSV mappings)
        entity_csv_files = {
            'Bills': 'Bill.csv',
            'Invoices': 'Invoice.csv', 
            'Items': 'Item.csv',
            'Contacts': 'Contacts.csv',
            'CustomerPayments': 'Customer_Payment.csv',
            'VendorPayments': 'Vendor_Payment.csv',
            'SalesOrders': 'Sales_Order.csv',
            'PurchaseOrders': 'Purchase_Order.csv',
            'CreditNotes': 'Credit_Note.csv'
            # Note: Organizations excluded as it doesn't have CSV mapping yet
        }
        
        manifest = []
        for entity_name, csv_filename in entity_csv_files.items():
            # Verify CSV mapping exists
            csv_mapping = get_entity_csv_mapping(entity_name)
            if csv_mapping:
                manifest.append({
                    'entity_name': entity_name,
                    'csv_filename': csv_filename,
                    'csv_path': self.csv_base_path / csv_filename,
                    'has_csv_mapping': True,
                    'priority': self._get_entity_priority(entity_name)
                })
            else:
                logger.warning(f"Entity {entity_name} excluded: no CSV mapping found")
        
        # Sort by priority (Items first, then entities with dependencies)
        manifest.sort(key=lambda x: x['priority'])
        
        logger.info(f"Built entity manifest with {len(manifest)} entities")
        return manifest
    
    def _get_entity_priority(self, entity_name: str) -> int:
        """
        Get processing priority for entities (lower number = higher priority).
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Priority number (1-10, where 1 is highest priority)
        """
        # Process standalone entities first, then entities with relationships
        priority_map = {
            'Items': 1,           # No dependencies
            'Contacts': 2,        # No dependencies
            'Bills': 3,           # References Items
            'Invoices': 4,        # References Items, Contacts
            'SalesOrders': 5,     # References Items, Contacts
            'PurchaseOrders': 6,  # References Items, Contacts
            'CreditNotes': 7,     # References Invoices
            'CustomerPayments': 8,  # References Invoices
            'VendorPayments': 9,    # References Bills
        }
        return priority_map.get(entity_name, 10)
    
    def run_full_rebuild(self, clean_rebuild: bool = True) -> Dict[str, Any]:
        """
        Execute the complete database rebuild process.
        
        This is the main orchestration method that coordinates:
        1. Safety protocols and database preparation
        2. Schema creation for all entities
        3. Data transformation and loading for each entity
        4. View creation and final validation
        
        Args:
            clean_rebuild: If True, performs complete rebuild. If False, appends to existing data.
            
        Returns:
            Dictionary with comprehensive processing statistics
            
        Raises:
            Exception: If critical errors occur during processing
        """
        self.processing_stats['start_time'] = time.time()
        
        try:
            logger.info("Starting Complete Database Rebuild Process")
            logger.info("=" * 60)
            
            # Step 1: Safety Protocols and Database Preparation
            self._execute_safety_protocols(clean_rebuild)
            
            # Step 2: Schema Creation
            self._create_all_schemas()
            
            # Step 3: Main Processing Loop
            self._execute_main_processing_loop()
            
            # Step 4: View Creation
            self._create_all_views()
            
            # Step 5: Final Validation
            self._perform_final_validation()
            
            # Calculate final statistics
            self.processing_stats['end_time'] = time.time()
            duration = self.processing_stats['end_time'] - self.processing_stats['start_time']
            self.processing_stats['total_duration_seconds'] = duration
            
            logger.info("Database Rebuild Process Completed Successfully!")
            logger.info("=" * 60)
            logger.info(f"Final Statistics:")
            logger.info(f"   Entities Processed: {self.processing_stats['entities_processed']}")
            logger.info(f"   Total Input Records: {self.processing_stats['total_input_records']:,}")
            logger.info(f"   Total Output Records: {self.processing_stats['total_output_records']:,}")
            logger.info(f"   Total Duration: {duration:.2f} seconds")
            logger.info(f"   Processing Rate: {self.processing_stats['total_input_records']/duration:.0f} records/sec")
            
            return self.processing_stats
            
        except Exception as e:
            logger.error(f"Database rebuild failed: {str(e)}")
            self.processing_stats['fatal_error'] = str(e)
            raise
    
    def _execute_safety_protocols(self, clean_rebuild: bool):
        """Execute safety protocols and database preparation."""
        logger.info("Step 1: Executing Safety Protocols")
        logger.info("-" * 40)
        
        with self.db_handler:
            if clean_rebuild:
                # Backup and clear existing database
                backup_info = self.db_handler.backup_and_clear_database()
                logger.info(f"Database backup created: {backup_info.get('backup_path', 'N/A')}")
                logger.info(f"Database cleared for clean rebuild")
            else:                logger.info(f"Incremental rebuild mode - preserving existing data")
            
        logger.info(f"Safety protocols completed\n")
    
    def _create_all_schemas(self):
        """Create database schemas for all entities in the manifest."""
        logger.info("Step 2: Creating Database Schemas")
        logger.info("-" * 40)
        
        schemas_created = 0
        
        with self.db_handler:
            for entity_config in self.entity_manifest:
                entity_name = entity_config['entity_name']
                
                try:
                    # Create transformer to get schema information
                    transformer = create_transformer(entity_name)
                    
                    # Create header table
                    header_table = transformer.header_table
                    header_schema = transformer.entity_schema['header_columns']
                    self.db_handler.create_canonical_table(header_table, header_schema)
                    schemas_created += 1
                    
                    logger.info(f"Created table: {header_table}")
                    
                    # Create line items table if applicable
                    if transformer.has_line_items:
                        line_items_table = transformer.line_items_table
                        line_items_schema = transformer.entity_schema['line_item_columns']
                        self.db_handler.create_canonical_table(line_items_table, line_items_schema)
                        schemas_created += 1
                        
                        logger.info(f"Created table: {line_items_table}")
                
                except Exception as e:
                    error_msg = f"Failed to create schema for {entity_name}: {str(e)}"
                    logger.error(f"ERROR: {error_msg}")
                    self.processing_stats['processing_errors'].append(error_msg)
        
        logger.info(f"Schema creation completed: {schemas_created} tables created\n")
    
    def _execute_main_processing_loop(self):
        """Execute the main processing loop for all entities."""
        logger.info("Step 3: Main Processing Loop")
        logger.info("-" * 40)
        
        for entity_config in self.entity_manifest:
            entity_name = entity_config['entity_name']
            csv_path = entity_config['csv_path']
            
            logger.info(f"Processing {entity_name} from {csv_path.name}")
            
            try:
                # Check if CSV file exists
                if not csv_path.exists():
                    error_msg = f"CSV file not found for {entity_name}: {csv_path}"
                    logger.error(f"ERROR: {error_msg}")
                    self.processing_stats['processing_errors'].append(error_msg)
                    continue
                
                # Load CSV data
                df = pd.read_csv(csv_path)
                input_records = len(df)
                self.processing_stats['total_input_records'] += input_records
                
                logger.info(f"   Loaded CSV: {input_records:,} records")
                
                # Create transformer and process data
                transformer = create_transformer(entity_name)
                header_df, line_items_df = transformer.transform_from_csv(df)
                
                logger.info(f"   Transformed data successfully")
                
                # Load data into database
                with self.db_handler:
                    # Load header data
                    header_table = transformer.header_table
                    header_load_stats = self.db_handler.load_data(
                        header_table, header_df, if_exists='append'
                    )
                    
                    header_records = header_load_stats['records_loaded']
                    self.processing_stats['total_output_records'] += header_records
                    
                    logger.info(f"   Loaded {header_records:,} records to {header_table}")
                    
                    # Load line items data if applicable
                    if line_items_df is not None and len(line_items_df) > 0:
                        line_items_table = transformer.line_items_table
                        line_items_load_stats = self.db_handler.load_data(
                            line_items_table, line_items_df, if_exists='append'
                        )
                        
                        line_items_records = line_items_load_stats['records_loaded']
                        self.processing_stats['total_output_records'] += line_items_records
                        
                        logger.info(f"   Loaded {line_items_records:,} records to {line_items_table}")
                
                self.processing_stats['entities_processed'] += 1
                logger.info(f"{entity_name} processing completed")
                
            except Exception as e:
                error_msg = f"Failed to process {entity_name}: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                self.processing_stats['processing_errors'].append(error_msg)
        
        logger.info(f"Main processing loop completed\n")
    
    def _create_all_views(self):
        """Create database views for enhanced querying."""
        logger.info("Step 4: Creating Database Views")
        logger.info("-" * 40)
        
        views_created = 0
        
        try:
            with self.db_handler:
                # Create summary views for entities with line items
                entities_with_line_items = ['Bills', 'Invoices', 'SalesOrders', 'PurchaseOrders', 'CreditNotes']
                
                for entity_name in entities_with_line_items:
                    if entity_name in [config['entity_name'] for config in self.entity_manifest]:
                        view_name = f"{entity_name}_Summary"
                        
                        # Create a view that joins headers with aggregated line items
                        transformer = create_transformer(entity_name)
                        header_table = transformer.header_table
                        line_items_table = transformer.line_items_table
                        primary_key = transformer.entity_schema['primary_key']
                        
                        view_sql = f"""
                        CREATE VIEW IF NOT EXISTS {view_name} AS
                        SELECT 
                            h.*,
                            COALESCE(li.line_item_count, 0) as LineItemCount,
                            COALESCE(li.total_quantity, 0) as TotalQuantity
                        FROM {header_table} h
                        LEFT JOIN (
                            SELECT 
                                {primary_key},
                                COUNT(*) as line_item_count,
                                SUM(CAST(Quantity AS REAL)) as total_quantity
                            FROM {line_items_table}
                            GROUP BY {primary_key}
                        ) li ON h.{primary_key} = li.{primary_key}
                        """
                        
                        self.db_handler.execute_write_query(view_sql)
                        views_created += 1
                        logger.info(f"Created view: {view_name}")
                
        except Exception as e:
            error_msg = f"Error creating views: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            self.processing_stats['processing_errors'].append(error_msg)
        
        logger.info(f"View creation completed: {views_created} views created\n")
    
    def _perform_final_validation(self):
        """Perform final validation of the rebuild process."""
        logger.info("Step 5: Final Validation")
        logger.info("-" * 40)
        
        validation_results = {}
        
        try:
            with self.db_handler:
                for entity_config in self.entity_manifest:
                    entity_name = entity_config['entity_name']
                    transformer = create_transformer(entity_name)
                    
                    # Get header table record count
                    header_table = transformer.header_table
                    header_count_query = f"SELECT COUNT(*) as count FROM {header_table}"
                    header_result = self.db_handler.execute_query(header_count_query)
                    header_count = header_result[0][0] if header_result else 0
                    
                    validation_results[entity_name] = {
                        'header_table': header_table,
                        'header_records': header_count
                    }
                    
                    # Get line items table record count if applicable
                    if transformer.has_line_items:
                        line_items_table = transformer.line_items_table
                        line_items_count_query = f"SELECT COUNT(*) as count FROM {line_items_table}"
                        line_items_result = self.db_handler.execute_query(line_items_count_query)
                        line_items_count = line_items_result[0][0] if line_items_result else 0
                        
                        validation_results[entity_name]['line_items_table'] = line_items_table
                        validation_results[entity_name]['line_items_records'] = line_items_count
                    
                    logger.info(f"{entity_name}: {header_count:,} header records" + 
                              (f", {line_items_count:,} line items" if transformer.has_line_items else ""))
                
                # Store validation results
                self.processing_stats['validation_results'] = validation_results
                
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            self.processing_stats['processing_errors'].append(error_msg)
        
        logger.info(f"Final validation completed\n")
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the rebuild process.
        
        Returns:
            Dictionary with detailed processing statistics and results
        """
        return {
            'success': len(self.processing_stats['processing_errors']) == 0,
            'entities_in_manifest': len(self.entity_manifest),
            'entities_processed': self.processing_stats['entities_processed'],
            'total_input_records': self.processing_stats['total_input_records'],
            'total_output_records': self.processing_stats['total_output_records'],
            'processing_errors': self.processing_stats['processing_errors'],
            'validation_results': self.processing_stats.get('validation_results', {}),
            'duration_seconds': self.processing_stats.get('total_duration_seconds', 0),
            'records_per_second': (
                self.processing_stats['total_input_records'] / 
                self.processing_stats.get('total_duration_seconds', 1)
            ) if self.processing_stats.get('total_duration_seconds') else 0
        }


def run_full_rebuild(database_path: Optional[str] = None, clean_rebuild: bool = True) -> Dict[str, Any]:
    """
    Convenience function to execute a complete database rebuild.
    
    Args:
        database_path: Optional path to database file
        clean_rebuild: If True, performs clean rebuild. If False, appends data.
        
    Returns:
        Dictionary with processing statistics
        
    Raises:
        Exception: If rebuild process fails
    """
    orchestrator = RebuildOrchestrator(database_path)
    return orchestrator.run_full_rebuild(clean_rebuild)
