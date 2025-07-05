#!/usr/bin/env python3
"""
Project Bedrock V2 - Full Database Rebuild Orchestrator

This script orchestrates the complete dual-source synchronization process:
1. Stage 1 - Bulk Load: CSV backup files → Canonical Database  
2. Stage 2 - Incremental Sync: JSON API files → Canonical Database

Usage:
    python run_rebuild.py --full-rebuild
    python run_rebuild.py --csv-only 
    python run_rebuild.py --json-only
    python run_rebuild.py --config config.yaml

Features:
- Configuration-driven execution
- Robust error handling and logging
- Progress tracking and validation
- Support for partial rebuilds
- Comprehensive audit trail
"""

import argparse
import logging
import sys
import sqlite3
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_pipeline.transformer import BillsTransformer
from src.data_pipeline.mappings.bills_mapping_config import CANONICAL_BILLS_COLUMNS


class ProjectBedrockOrchestrator:
    """
    Main orchestrator for Project Bedrock V2 dual-source data pipeline.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # Initialize transformers
        self.bills_transformer = BillsTransformer()
        
        # Initialize database connection
        self.db_connection = None
        
        self.logger = logging.getLogger(__name__)
    
    def backup_database(self, db_path: Path) -> Path:
        """Create a timestamped backup of the existing database."""
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"{db_path.stem}_backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Database backed up to: {backup_path}")
        self.logger.info(f"Database backup created: {backup_path}")
        return backup_path
    
    def create_new_database(self, db_path: Path):
        """Create a new, empty database at the specified path."""
        if db_path.exists():
            db_path.unlink()
            print(f"✅ Old database cleared: {db_path}")
            
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create new database connection (will create the file)
        self.db_connection = sqlite3.connect(db_path)
        print(f"✅ New database created: {db_path}")
        self.logger.info(f"New database created: {db_path}")
    
    def execute_safety_first_protocol(self, is_full_rebuild: bool = False):
        """Execute the Safety First protocol for full rebuilds."""
        db_path = Path(self.config['data_sources']['target_database'])
        
        if not is_full_rebuild:
            # Normal initialization without safety protocol
            self._initialize_database()
            return
        
        print("🛡️ SAFETY FIRST PROTOCOL: Full Rebuild Mode")
        print("=" * 60)
        
        if db_path.exists():
            print(f"📋 Existing database found: {db_path}")
            
            # Step 1: Backup existing database
            backup_path = self.backup_database(db_path)
            
            # Step 2: Create new empty database
            self.create_new_database(db_path)
            
        else:
            print("📄 No existing database found. Creating a new one.")
            self.create_new_database(db_path)
        
        # Step 3: Create canonical table structure
        self._create_canonical_bills_table()
        
        print("✅ Clean slate ready. Proceeding with full rebuild.")
        print("=" * 60)
        self.logger.info("Project Bedrock V2 Orchestrator initialized")
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'data_sources': {
                'csv_backup_path': Path('data/csv'),
                'json_api_path': Path('data/json'),
                'target_database': Path('output/database/canonical.db')
            },
            'processing': {
                'batch_size': 1000,
                'validate_transformations': True,
                'create_backups': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'reports/rebuild.log'
            }
        }
        
        # Use default config file if none specified
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "settings.yaml"
        
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                # Merge with defaults
                default_config.update(file_config)
        
        return default_config
    
    def setup_logging(self):
        """Configure logging based on configuration."""
        log_level = getattr(logging, self.config['logging']['level'].upper())
        log_file = Path(self.config['logging']['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def execute_full_rebuild(self) -> Dict[str, Any]:
        """
        Execute complete dual-source rebuild process.
        
        Returns:
            Dictionary with execution results and statistics
        """
        self.logger.info("🚀 Starting Project Bedrock V2 Full Rebuild")
        
        results = {
            'stage1_csv_results': None,
            'stage2_json_results': None,
            'total_records_processed': 0,
            'execution_time': None,
            'success': False
        }
        
        try:
            # Initialize database
            self._initialize_database()
            
            # Stage 1: Bulk Load from CSV backup
            self.logger.info("📊 Stage 1: Bulk Load from CSV backup")
            results['stage1_csv_results'] = self._execute_csv_bulk_load()
            
            # Stage 2: Incremental Sync from JSON API
            self.logger.info("🌐 Stage 2: Incremental Sync from JSON API")  
            results['stage2_json_results'] = self._execute_json_incremental_sync()
            
            # Calculate totals
            csv_count = results['stage1_csv_results'].get('records_processed', 0)
            json_count = results['stage2_json_results'].get('records_processed', 0)
            results['total_records_processed'] = csv_count + json_count
            
            # Validate final database state
            if self.config['processing']['validate_transformations']:
                self._validate_final_database()
            
            results['success'] = True
            self.logger.info(f"🎉 Full rebuild completed successfully! "
                           f"Total records: {results['total_records_processed']}")
            
        except Exception as e:
            self.logger.error(f"❌ Full rebuild failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        finally:
            if self.db_connection:
                self.db_connection.close()
        
        return results
    
    def _execute_csv_bulk_load(self) -> Dict[str, Any]:
        """Execute Stage 1: CSV backup bulk loading."""
        csv_backup_path = Path(self.config['data_sources']['csv_backup_path'])
        bills_csv_path = csv_backup_path / 'bills.csv'
        
        results = {
            'source_file': str(bills_csv_path),
            'records_processed': 0,
            'validation_results': None,
            'success': False
        }
        
        try:
            if not bills_csv_path.exists():
                raise FileNotFoundError(f"CSV backup file not found: {bills_csv_path}")
            
            self.logger.info(f"Loading CSV data from: {bills_csv_path}")
            
            # Load CSV data with optimized settings
            csv_df = pd.read_csv(bills_csv_path, low_memory=False)
            self.logger.info(f"Loaded {len(csv_df)} records from CSV backup")
            
            # Validate CSV structure
            validation = self.bills_transformer.validate_csv_columns(csv_df)
            results['validation_results'] = validation
            
            if not validation['is_valid']:
                missing_cols = validation['missing_columns']
                raise ValueError(f"CSV validation failed. Missing columns: {missing_cols}")
            
            # Transform to canonical schema
            self.logger.info("Transforming CSV data to canonical schema...")
            canonical_df = self.bills_transformer.transform_from_csv(csv_df)
            
            # Load into database
            records_loaded = self._load_to_database(canonical_df, 'bills_canonical', 'CSV bulk load')
            results['records_processed'] = records_loaded
            results['success'] = True
            
            self.logger.info(f"✅ CSV bulk load completed: {records_loaded} records")
            
        except Exception as e:
            self.logger.error(f"❌ CSV bulk load failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        return results
    
    def _execute_json_incremental_sync(self) -> Dict[str, Any]:
        """Execute Stage 2: JSON API incremental synchronization."""
        json_api_path = Path(self.config['data_sources']['json_api_path'])
        
        results = {
            'source_path': str(json_api_path),
            'files_processed': 0,
            'records_processed': 0,
            'validation_results': None,
            'success': False
        }
        
        try:
            if not json_api_path.exists():
                raise FileNotFoundError(f"JSON API path not found: {json_api_path}")
            
            # Find all bills.json files in subdirectories
            json_files = list(json_api_path.rglob('bills.json'))
            
            if not json_files:
                self.logger.warning(f"No bills.json files found in: {json_api_path}")
                results['success'] = True  # Not an error, just no incremental data
                return results
            
            self.logger.info(f"Found {len(json_files)} JSON API files to process")
            
            total_records = 0
            
            for json_file in json_files:
                self.logger.info(f"Processing JSON file: {json_file}")
                
                # Load JSON data
                with open(json_file, 'r', encoding='utf-8') as f:
                    import json
                    json_data = json.load(f)
                
                if not json_data:
                    self.logger.warning(f"Empty JSON file: {json_file}")
                    continue
                
                json_df = pd.DataFrame(json_data)
                self.logger.info(f"Loaded {len(json_df)} records from {json_file.name}")
                
                # Validate JSON structure (only on first file)
                if results['validation_results'] is None:
                    validation = self.bills_transformer.validate_json_structure(json_df)
                    results['validation_results'] = validation
                    
                    if not validation['is_valid']:
                        raise ValueError(f"JSON validation failed: {validation}")
                
                # Transform to canonical schema
                canonical_df = self.bills_transformer.transform_from_json(json_df)
                
                # Load into database (append mode for incremental)
                records_loaded = self._load_to_database(canonical_df, 'bills_canonical', 'JSON incremental', append=True)
                total_records += records_loaded
                
                results['files_processed'] += 1
                self.logger.info(f"Processed {json_file.name}: {records_loaded} records")
            
            results['records_processed'] = total_records
            results['success'] = True
            
            self.logger.info(f"✅ JSON incremental sync completed: {total_records} records from {len(json_files)} files")
            
        except Exception as e:
            self.logger.error(f"❌ JSON incremental sync failed: {str(e)}")
            results['error'] = str(e)
            raise
        
        return results
    
    def _initialize_database(self):
        """Initialize the canonical database and create tables."""
        db_path = Path(self.config['data_sources']['target_database'])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists and configured
        if db_path.exists() and self.config['processing']['create_backups']:
            backup_path = db_path.with_suffix(f".backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.db")
            import shutil
            shutil.copy2(db_path, backup_path)
            self.logger.info(f"Created database backup: {backup_path}")
        
        self.db_connection = sqlite3.connect(db_path)
        self.logger.info(f"Connected to database: {db_path}")
        
        # Create canonical bills table
        self._create_canonical_bills_table()
    
    def _create_canonical_bills_table(self):
        """Create the canonical bills table with proper schema."""
        # Define column types for SQLite
        column_definitions = []
        for col in CANONICAL_BILLS_COLUMNS:
            if col in ['BillID', 'LineItemID']:
                col_type = 'TEXT PRIMARY KEY' if col == 'BillID' else 'TEXT'
            elif col in ['Quantity', 'Rate', 'Amount', 'SubTotal', 'TaxTotal', 'Total', 'Balance', 'ExchangeRate', 'LineItemTaxTotal', 'TaxPercentage']:
                col_type = 'REAL'
            elif col == 'IsInclusiveTax':
                col_type = 'INTEGER'
            else:
                col_type = 'TEXT'
            
            column_definitions.append(f'"{col}" {col_type}')
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS bills_canonical (
            {', '.join(column_definitions)}
        )
        """
        
        self.db_connection.execute("DROP TABLE IF EXISTS bills_canonical")
        self.db_connection.execute(create_sql)
        self.db_connection.commit()
        
        self.logger.info(f"Created canonical bills table with {len(CANONICAL_BILLS_COLUMNS)} columns")
    
    def _load_to_database(self, df: pd.DataFrame, table_name: str, operation: str, append: bool = False) -> int:
        """
        Load DataFrame to database table.
        
        Args:
            df: DataFrame to load
            table_name: Target table name
            operation: Description of the operation for logging
            append: Whether to append (True) or replace (False)
            
        Returns:
            Number of records loaded
        """
        if df.empty:
            self.logger.warning(f"No data to load for {operation}")
            return 0
        
        if_exists = 'append' if append else 'replace'
        
        try:
            df.to_sql(table_name, self.db_connection, if_exists=if_exists, index=False, method='multi')
            self.db_connection.commit()
            
            self.logger.info(f"Loaded {len(df)} records to {table_name} ({operation})")
            return len(df)
            
        except Exception as e:
            self.logger.error(f"Failed to load data to {table_name}: {str(e)}")
            raise
    
    def _validate_final_database(self):
        """Validate the final database state."""
        cursor = self.db_connection.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bills_canonical'")
        if not cursor.fetchone():
            raise ValueError("Canonical bills table not found in database")
        
        # Check record count
        cursor.execute("SELECT COUNT(*) FROM bills_canonical")
        total_records = cursor.fetchone()[0]
        
        # Check schema
        cursor.execute("PRAGMA table_info(bills_canonical)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if len(columns) != len(CANONICAL_BILLS_COLUMNS):
            raise ValueError(f"Schema validation failed: expected {len(CANONICAL_BILLS_COLUMNS)} columns, found {len(columns)}")
        
        self.logger.info(f"✅ Database validation passed: {total_records} total records, {len(columns)} columns")


def main():
    """Main entry point for the rebuild orchestrator."""
    parser = argparse.ArgumentParser(description='Project Bedrock V2 - Database Rebuild Orchestrator')
    parser.add_argument('--full-rebuild', action='store_true', help='Execute complete dual-source rebuild')
    parser.add_argument('--csv-only', action='store_true', help='Execute only CSV bulk load')
    parser.add_argument('--json-only', action='store_true', help='Execute only JSON incremental sync')
    parser.add_argument('--config', type=Path, help='Path to configuration file')
    parser.add_argument('--validate-only', action='store_true', help='Validate data sources without processing')
    
    args = parser.parse_args()
    
    try:
        orchestrator = ProjectBedrockOrchestrator(args.config)
        
        if args.validate_only:
            # TODO: Implement validation-only mode
            print("Validation-only mode not yet implemented")
            return
        
        if args.full_rebuild or (not args.csv_only and not args.json_only):
            results = orchestrator.execute_full_rebuild()
            print(f"\n🎉 Full rebuild completed successfully!")
            print(f"Total records processed: {results['total_records_processed']}")
            
        elif args.csv_only:
            # TODO: Implement CSV-only mode
            print("CSV-only mode not yet implemented")
            
        elif args.json_only:
            # TODO: Implement JSON-only mode  
            print("JSON-only mode not yet implemented")
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
