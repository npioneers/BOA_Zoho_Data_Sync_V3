"""
Final Schema Validation and Field Mapping Column Management
Comprehensive validation and setup of JSON mapping table schemas with field-level mapping support
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

def setup_logging() -> logging.Logger:
    """Setup comprehensive logging for schema validation"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"final_schema_validation_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Final Schema Validation started - Logging to: {log_file}")
    return logger

def get_expected_schema() -> Dict[str, str]:
    """Get the expected schema for JSON mapping tables"""
    return {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'field_name': 'TEXT NOT NULL',
        'field_type': 'TEXT',
        'max_length': 'INTEGER',
        'is_nullable': 'BOOLEAN DEFAULT 1',
        'is_primary_key': 'BOOLEAN DEFAULT 0',
        'field_position': 'INTEGER',
        'sample_values': 'TEXT',
        'field_description': 'TEXT',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'CSV_table': 'TEXT',
        'CSV_field': 'TEXT',
        'CSV_data_count': 'INTEGER'
    }

def validate_and_fix_schema(db_path: str = "../data/database/production.db") -> Dict[str, Any]:
    """Comprehensive validation and fixing of JSON mapping table schemas"""
    logger = setup_logging()
    
    logger.info("Starting comprehensive schema validation and update process...")
    
    results = {
        'tables_processed': 0,
        'tables_updated': 0,
        'columns_added': 0,
        'columns_removed': 0,
        'validation_errors': [],
        'summary': {}
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all JSON mapping tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_json_%'")
        json_mapping_tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(json_mapping_tables)} JSON mapping tables to validate")
        print(f"\n📋 Found {len(json_mapping_tables)} JSON mapping tables")
        print("=" * 80)
        
        expected_schema = get_expected_schema()
        
        for table in json_mapping_tables:
            results['tables_processed'] += 1
            logger.info(f"Validating schema for table: {table}")
            
            try:
                # Get current table structure
                cursor.execute(f"PRAGMA table_info({table})")
                current_columns = {col[1]: col[2] for col in cursor.fetchall()}
                
                print(f"\n🔍 Validating: {table}")
                print(f"   Current columns: {len(current_columns)}")
                
                # Check for unwanted columns and remove them
                unwanted_columns = []
                if 'mapped_CSV' in current_columns:
                    unwanted_columns.append('mapped_CSV')
                
                if unwanted_columns:
                    print(f"   🗑️  Found {len(unwanted_columns)} unwanted columns to remove...")
                    
                    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
                    for col_name in unwanted_columns:
                        try:
                            # Get all data except the unwanted column
                            remaining_columns = [col for col in current_columns.keys() if col != col_name]
                            columns_list = ', '.join(remaining_columns)
                            
                            # Create backup table
                            backup_table = f"{table}_backup_temp"
                            cursor.execute(f"CREATE TABLE {backup_table} AS SELECT {columns_list} FROM {table}")
                            
                            # Drop original table
                            cursor.execute(f"DROP TABLE {table}")
                            
                            # Recreate table without unwanted column
                            # Get the schema for remaining columns
                            remaining_schema = {col: current_columns[col] for col in remaining_columns}
                            
                            # Build CREATE TABLE statement
                            column_defs = []
                            for col_name_def, col_type in remaining_schema.items():
                                if col_name_def == 'id':
                                    column_defs.append(f"{col_name_def} INTEGER PRIMARY KEY AUTOINCREMENT")
                                else:
                                    column_defs.append(f"{col_name_def} {col_type}")
                            
                            create_sql = f"CREATE TABLE {table} ({', '.join(column_defs)})"
                            cursor.execute(create_sql)
                            
                            # Copy data back
                            cursor.execute(f"INSERT INTO {table} ({columns_list}) SELECT {columns_list} FROM {backup_table}")
                            
                            # Drop backup table
                            cursor.execute(f"DROP TABLE {backup_table}")
                            
                            results['columns_removed'] += 1
                            results['tables_updated'] += 1
                            logger.info(f"Removed column {col_name} from {table}")
                            print(f"     ✅ Removed: {col_name}")
                            
                            # Update current_columns for further processing
                            current_columns = remaining_schema
                            
                        except Exception as e:
                            error_msg = f"Failed to remove column {col_name} from {table}: {str(e)}"
                            results['validation_errors'].append(error_msg)
                            logger.error(error_msg)
                            print(f"     ❌ Failed to remove: {col_name} - {str(e)}")
                
                # Check for missing columns and add them
                missing_columns = []
                for expected_col, expected_type in expected_schema.items():
                    if expected_col not in current_columns:
                        missing_columns.append((expected_col, expected_type))
                
                if missing_columns:
                    results['tables_updated'] += 1
                    print(f"   ⚠️  Missing {len(missing_columns)} columns - Adding...")
                    
                    for col_name, col_type in missing_columns:
                        try:
                            # Handle special cases for column definitions
                            if col_name == 'id' and 'PRIMARY KEY AUTOINCREMENT' in col_type:
                                # Skip ID column if it already exists in some form
                                if any('id' in col.lower() for col in current_columns.keys()):
                                    continue
                            
                            # Simplify column type for ALTER TABLE
                            simple_type = col_type.split()[0] if col_type else 'TEXT'
                            
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {simple_type}")
                            results['columns_added'] += 1
                            logger.info(f"Added column {col_name} ({simple_type}) to {table}")
                            print(f"     ✅ Added: {col_name} ({simple_type})")
                            
                        except Exception as e:
                            error_msg = f"Failed to add column {col_name} to {table}: {str(e)}"
                            results['validation_errors'].append(error_msg)
                            logger.error(error_msg)
                            print(f"     ❌ Failed: {col_name} - {str(e)}")
                else:
                    print(f"   ✅ Schema complete - All columns present")
                
                # Verify final schema
                cursor.execute(f"PRAGMA table_info({table})")
                final_columns = {col[1]: col[2] for col in cursor.fetchall()}
                
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                record_count = cursor.fetchone()[0]
                
                # Get mapping status
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE CSV_field IS NOT NULL")
                mapped_count = cursor.fetchone()[0] if 'CSV_field' in final_columns else 0
                
                results['summary'][table] = {
                    'columns': len(final_columns),
                    'records': record_count,
                    'mapped_records': mapped_count,
                    'mapping_percentage': (mapped_count / record_count * 100) if record_count > 0 else 0
                }
                
                print(f"   📊 Final: {len(final_columns)} columns, {record_count} records, {mapped_count} mapped ({results['summary'][table]['mapping_percentage']:.1f}%)")
                
            except Exception as e:
                error_msg = f"Error processing table {table}: {str(e)}"
                results['validation_errors'].append(error_msg)
                logger.error(error_msg)
                print(f"   ❌ Error: {str(e)}")
        
        conn.commit()
        conn.close()
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 FINAL SCHEMA VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"✅ Tables processed: {results['tables_processed']}")
        print(f"🔧 Tables updated: {results['tables_updated']}")
        print(f"➕ Columns added: {results['columns_added']}")
        print(f"🗑️  Columns removed: {results['columns_removed']}")
        print(f"❌ Validation errors: {len(results['validation_errors'])}")
        
        if results['validation_errors']:
            print(f"\n⚠️  ERRORS ENCOUNTERED:")
            for i, error in enumerate(results['validation_errors'], 1):
                print(f"   {i}. {error}")
        
        print(f"\n📋 DETAILED TABLE STATUS:")
        print("-" * 80)
        print(f"{'Table Name':<35} {'Cols':<6} {'Records':<8} {'Mapped':<8} {'%':<6}")
        print("-" * 80)
        
        total_records = 0
        total_mapped = 0
        
        for table_name, stats in results['summary'].items():
            total_records += stats['records']
            total_mapped += stats['mapped_records']
            print(f"{table_name:<35} {stats['columns']:<6} {stats['records']:<8} {stats['mapped_records']:<8} {stats['mapping_percentage']:<6.1f}")
        
        overall_percentage = (total_mapped / total_records * 100) if total_records > 0 else 0
        print("-" * 80)
        print(f"{'TOTALS':<35} {'':<6} {total_records:<8} {total_mapped:<8} {overall_percentage:<6.1f}")
        print("=" * 80)
        
        logger.info(f"Schema validation complete: {results['tables_processed']} tables processed, {results['columns_added']} columns added, {results['columns_removed']} columns removed")
        
        return results
        
    except Exception as e:
        error_msg = f"Critical error during schema validation: {str(e)}"
        logger.error(error_msg)
        print(f"❌ CRITICAL ERROR: {str(e)}")
        results['validation_errors'].append(error_msg)
        return results

def verify_mapping_functionality(db_path: str = "../data/database/production.db") -> bool:
    """Verify that field mapping functionality is working correctly"""
    logger = logging.getLogger(__name__)
    logger.info("Verifying mapping functionality...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test a sample mapping query
        test_query = """
            SELECT 
                jm.field_name as json_field,
                jm.CSV_table as csv_table,
                jm.CSV_field as csv_field
            FROM map_json_invoices jm 
            WHERE jm.CSV_field IS NOT NULL 
            LIMIT 5
        """
        
        cursor.execute(test_query)
        sample_mappings = cursor.fetchall()
        
        if sample_mappings:
            print(f"\n🔍 SAMPLE FIELD MAPPINGS (map_json_invoices):")
            print("-" * 60)
            print(f"{'JSON Field':<25} {'CSV Table':<20} {'CSV Field':<15}")
            print("-" * 60)
            
            for json_field, csv_table, csv_field in sample_mappings:
                csv_field_display = csv_field or "TBD"
                print(f"{json_field:<25} {csv_table:<20} {csv_field_display:<15}")
            
            logger.info("Mapping functionality verification successful")
            return True
        else:
            logger.warning("No mapped fields found - mapping may need to be run")
            print("⚠️  No mapped fields found. Run field mapping process.")
            return False
            
    except Exception as e:
        logger.error(f"Mapping functionality verification failed: {str(e)}")
        print(f"❌ Mapping verification failed: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """Main execution function for final schema validation"""
    print("🚀 Starting Final Schema Validation and Column Management")
    print("=" * 80)
    
    # Run comprehensive schema validation
    results = validate_and_fix_schema()
    
    # Verify mapping functionality
    mapping_status = verify_mapping_functionality()
    
    # Final status
    if results['validation_errors']:
        print(f"\n⚠️  COMPLETED WITH {len(results['validation_errors'])} ERRORS")
        exit_code = 1
    else:
        print(f"\n✅ SCHEMA VALIDATION COMPLETED SUCCESSFULLY")
        exit_code = 0
    
    if mapping_status:
        print("✅ Field mapping functionality verified")
    else:
        print("⚠️  Field mapping needs attention")
    
    print("\n📝 Next steps:")
    print("   1. Run field mapping: python runner.py map-fields --db '../data/database/production.db'")
    print("   2. Implement individual field-level mapping algorithms")
    print("   3. Add data validation and integrity checks")
    
    return exit_code == 0

if __name__ == "__main__":
    success = main()
