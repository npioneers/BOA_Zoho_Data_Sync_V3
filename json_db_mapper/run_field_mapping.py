#!/usr/bin/env python3
"""
Field-Level Mapping Implementation
Populates the CSV_field column in JSON mapping tables with best-match CSV fields
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

def setup_logging() -> logging.Logger:
    """Setup logging for field-level mapping"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"field_level_mapping_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Field Level Mapping started - Logging to: {log_file}")
    return logger

def update_csv_data_count_for_csv_tables(db_path: str = "../data/database/production.db") -> bool:
    """
    Update CSV_data_count column in all map_csv_* tables by counting non-null values 
    for each specific field in the corresponding csv_* tables
    
    Args:
        db_path (str): Path to the database
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all clean map_csv tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name LIKE 'map_csv_%' 
            AND name NOT LIKE 'map_csv_csv_%'
            ORDER BY name
        """)
        map_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n🔢 Updating CSV_data_count for individual fields in {len(map_tables)} map_csv tables...")
        
        total_updates = 0
        
        for table_name in map_tables:
            # Get base table name (remove 'map_' prefix)
            base_table_name = table_name[4:]  # Remove 'map_' prefix
            
            # Check if base CSV table exists
            try:
                cursor.execute(f"SELECT 1 FROM {base_table_name} LIMIT 1")
            except sqlite3.OperationalError:
                print(f"   ⚠️  Table {base_table_name} not found, skipping {table_name}")
                continue
            
            # Get all field names from the mapping table
            cursor.execute(f"SELECT id, field_name FROM {table_name} ORDER BY field_position")
            field_records = cursor.fetchall()
            
            print(f"   📋 Processing {len(field_records)} fields in {table_name}...")
            
            table_updates = 0
            
            for record_id, field_name in field_records:
                try:
                    # Count non-null and non-empty values for this specific field
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {base_table_name} 
                        WHERE "{field_name}" IS NOT NULL 
                        AND "{field_name}" != ''
                        AND "{field_name}" != 'NULL'
                    """)
                    field_count = cursor.fetchone()[0]
                    
                    # Update CSV_data_count for this specific field
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET CSV_data_count = ?, updated_at = ? 
                        WHERE id = ?
                    """, (field_count, datetime.now(), record_id))
                    
                    table_updates += 1
                    
                    if table_updates <= 3:  # Show first few for verification
                        print(f"      {field_name}: {field_count} non-null values")
                    
                except sqlite3.OperationalError as e:
                    # Field might not exist in CSV table
                    print(f"      ⚠️  Field '{field_name}' not found in {base_table_name}")
                    # Set count to 0 for missing fields
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET CSV_data_count = 0, updated_at = ? 
                        WHERE id = ?
                    """, (datetime.now(), record_id))
                    table_updates += 1
            
            if table_updates > 3:
                print(f"      ... and {table_updates - 3} more fields processed")
                
            total_updates += table_updates
            print(f"   ✅ {table_name}: Updated {table_updates} field records")
        
        conn.commit()
        print(f"   📊 Total field updates: {total_updates}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating CSV_data_count: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def update_csv_data_count_for_json_tables(db_path: str = "../data/database/production.db") -> bool:
    """
    Update CSV_data_count column in all map_json_* tables by counting non-null values 
    for mapped CSV fields in the corresponding csv_* tables
    
    Args:
        db_path (str): Path to the database
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all map_json tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name LIKE 'map_json_%'
            ORDER BY name
        """)
        json_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n🔢 Updating CSV_data_count for mapped fields in {len(json_tables)} map_json tables...")
        
        total_updates = 0
        
        for table_name in json_tables:
            # Get all records that have CSV mappings
            cursor.execute(f"""
                SELECT id, field_name, CSV_field, CSV_table 
                FROM {table_name} 
                WHERE CSV_field IS NOT NULL AND CSV_table IS NOT NULL
                ORDER BY field_position
            """)
            mapped_records = cursor.fetchall()
            
            if not mapped_records:
                print(f"   ⚠️  No mapped fields found in {table_name}")
                continue
                
            print(f"   📋 Processing {len(mapped_records)} mapped fields in {table_name}...")
            
            table_updates = 0
            
            for record_id, field_name, csv_field, csv_table in mapped_records:
                # Get actual CSV table name (remove 'map_' prefix)
                actual_csv_table = csv_table[4:] if csv_table.startswith('map_') else csv_table
                
                try:
                    # Count non-null values for the mapped CSV field
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {actual_csv_table} 
                        WHERE "{csv_field}" IS NOT NULL 
                        AND "{csv_field}" != ''
                        AND "{csv_field}" != 'NULL'
                    """)
                    field_count = cursor.fetchone()[0]
                    
                    # Update CSV_data_count for this specific field mapping
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET CSV_data_count = ?, updated_at = ? 
                        WHERE id = ?
                    """, (field_count, datetime.now(), record_id))
                    
                    table_updates += 1
                    
                    if table_updates <= 3:  # Show first few for verification
                        print(f"      {field_name} -> {csv_field}: {field_count} non-null values")
                    
                except sqlite3.OperationalError as e:
                    # CSV table or field might not exist
                    print(f"      ⚠️  Error accessing {actual_csv_table}.{csv_field}: {e}")
                    # Set count to 0 for missing fields
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET CSV_data_count = 0, updated_at = ? 
                        WHERE id = ?
                    """, (datetime.now(), record_id))
                    table_updates += 1
            
            if table_updates > 3:
                print(f"      ... and {table_updates - 3} more fields processed")
                
            total_updates += table_updates
            print(f"   ✅ {table_name}: Updated {table_updates} field records")
        
        conn.commit()
        print(f"   📊 Total JSON field updates: {total_updates}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating CSV_data_count for JSON tables: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def calculate_field_similarity(field1: str, field2: str) -> float:
    """Calculate similarity score between two field names"""
    if not field1 or not field2:
        return 0.0
    
    # Exact match
    if field1.lower() == field2.lower():
        return 1.0
    
    # Clean field names for comparison
    field1_clean = clean_field_name(field1)
    field2_clean = clean_field_name(field2)
    
    if field1_clean.lower() == field2_clean.lower():
        return 0.95
    
    # Use sequence matcher for similarity
    similarity = SequenceMatcher(None, field1_clean.lower(), field2_clean.lower()).ratio()
    
    # Boost score for common patterns
    if any(keyword in field1.lower() and keyword in field2.lower() 
           for keyword in ['id', 'name', 'date', 'time', 'amount', 'total', 'status', 'email', 'phone']):
        similarity += 0.1
    
    return min(similarity, 1.0)

def clean_field_name(field_name: str) -> str:
    """Clean field name for better comparison"""
    if not field_name:
        return ""
    
    # Remove common prefixes and suffixes
    prefixes = ['csv_', 'json_', 'tbl_', 'fld_']
    suffixes = ['_id', '_name', '_date', '_time', '_amount']
    
    cleaned = field_name.lower().strip()
    
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    
    return cleaned

def map_fields_for_table(json_table: str, csv_table: str, 
                        conn: sqlite3.Connection, logger: logging.Logger) -> Dict[str, any]:
    """Map fields between a JSON table and its corresponding CSV table"""
    
    logger.info(f"Mapping fields: {json_table} -> {csv_table}")
    
    results = {
        'total_json_fields': 0,
        'mapped_fields': 0,
        'high_confidence_mappings': 0,
        'mappings': []
    }
    
    try:
        # Get JSON table fields
        cursor = conn.cursor()
        cursor.execute(f"SELECT field_name, field_type FROM {json_table} ORDER BY field_position")
        json_fields = cursor.fetchall()
        
        # Get CSV table fields  
        cursor.execute(f"SELECT field_name, field_type FROM {csv_table} ORDER BY field_position")
        csv_fields = cursor.fetchall()
        
        results['total_json_fields'] = len(json_fields)
        
        logger.info(f"Found {len(json_fields)} JSON fields and {len(csv_fields)} CSV fields")
        
        # Create a list of CSV field names for comparison
        csv_field_names = [field[0] for field in csv_fields]
        
        # Map each JSON field to best CSV field match
        for json_field_name, json_field_type in json_fields:
            best_match = None
            best_score = 0.0
            
            # Find best matching CSV field
            for csv_field_name in csv_field_names:
                score = calculate_field_similarity(json_field_name, csv_field_name)
                if score > best_score:
                    best_score = score
                    best_match = csv_field_name
            
            # Only accept mappings above threshold
            if best_score >= 0.3:  # 30% similarity threshold
                # Get the CSV table name (remove 'map_' prefix from csv_table)
                actual_csv_table = csv_table[4:]  # Remove 'map_' prefix to get csv_*
                
                # Count non-null values for the mapped CSV field
                csv_field_count = 0
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {actual_csv_table} 
                        WHERE "{best_match}" IS NOT NULL 
                        AND "{best_match}" != ''
                        AND "{best_match}" != 'NULL'
                    """)
                    csv_field_count = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    # CSV table or field doesn't exist
                    csv_field_count = 0
                
                # Update the JSON mapping table with field mapping AND CSV_data_count
                cursor.execute(f"""
                    UPDATE {json_table} 
                    SET CSV_field = ?, CSV_table = ?, CSV_data_count = ?, updated_at = ?
                    WHERE field_name = ?
                """, (best_match, csv_table, csv_field_count, datetime.now(), json_field_name))
                
                results['mapped_fields'] += 1
                
                if best_score >= 0.7:  # High confidence threshold
                    results['high_confidence_mappings'] += 1
                
                results['mappings'].append({
                    'json_field': json_field_name,
                    'csv_field': best_match,
                    'csv_data_count': csv_field_count,
                    'score': best_score,
                    'confidence': 'high' if best_score >= 0.7 else 'medium'
                })
                
                logger.debug(f"Mapped: {json_field_name} -> {best_match} (score: {best_score:.3f}, count: {csv_field_count})")
            else:
                logger.debug(f"No good match for {json_field_name} (best score: {best_score:.3f})")
        
        conn.commit()
        logger.info(f"Completed mapping for {json_table}: {results['mapped_fields']}/{results['total_json_fields']} fields mapped")
        
    except Exception as e:
        logger.error(f"Error mapping fields for {json_table}: {str(e)}")
        results['error'] = str(e)
    
    return results

def run_field_level_mapping(db_path: str = "../data/database/production.db") -> Dict[str, any]:
    """Run field-level mapping for all JSON tables"""
    logger = setup_logging()
    logger.info("Starting comprehensive field-level mapping process...")
    
    overall_results = {
        'tables_processed': 0,
        'total_json_fields': 0,
        'total_mapped_fields': 0,
        'total_high_confidence': 0,
        'table_results': {}
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all JSON mapping tables that have been mapped to CSV tables
        # Since we removed mapped_CSV column, we'll get mappings from CSV_table column
        mappings_to_process = []
        
        json_tables = [
            'map_json_bills', 'map_json_contacts', 'map_json_invoices', 'map_json_items',
            'map_json_customer_payments', 'map_json_vendor_payments', 'map_json_credit_notes',
            'map_json_sales_orders', 'map_json_purchase_orders', 'map_json_bills_line_items',
            'map_json_invoices_line_items', 'map_json_creditnotes_line_items',
            'map_json_salesorders_line_items', 'map_json_purchaseorders_line_items',
            'map_json_organizations'
        ]
        
        for json_table in json_tables:
            try:
                cursor.execute(f"SELECT DISTINCT CSV_table FROM {json_table} WHERE CSV_table IS NOT NULL LIMIT 1")
                result = cursor.fetchone()
                if result:
                    csv_table_name = result[0]
                    # CSV_table already contains the full mapping table name (e.g., 'map_csv_bills')
                    csv_mapping_table = csv_table_name
                    mappings_to_process.append((json_table, csv_mapping_table))
            except:
                continue
        
        print(f"\n🔄 Processing {len(mappings_to_process)} table mappings...")
        print("=" * 80)
        
        for json_table, csv_table in mappings_to_process:
            overall_results['tables_processed'] += 1
            
            print(f"\n📋 Mapping: {json_table} -> {csv_table}")
            
            table_results = map_fields_for_table(json_table, csv_table, conn, logger)
            overall_results['table_results'][json_table] = table_results
            
            overall_results['total_json_fields'] += table_results['total_json_fields']
            overall_results['total_mapped_fields'] += table_results['mapped_fields']
            overall_results['total_high_confidence'] += table_results['high_confidence_mappings']
            
            # Show progress
            mapped_pct = (table_results['mapped_fields'] / table_results['total_json_fields'] * 100) if table_results['total_json_fields'] > 0 else 0
            high_conf_pct = (table_results['high_confidence_mappings'] / table_results['mapped_fields'] * 100) if table_results['mapped_fields'] > 0 else 0
            
            print(f"   ✅ Mapped: {table_results['mapped_fields']}/{table_results['total_json_fields']} fields ({mapped_pct:.1f}%)")
            print(f"   🎯 High confidence: {table_results['high_confidence_mappings']} ({high_conf_pct:.1f}%)")
        
        # Update CSV data count in map_csv tables
        update_csv_success = update_csv_data_count_for_csv_tables(db_path)
        
        # Update CSV data count in map_json tables for mapped fields
        update_json_success = update_csv_data_count_for_json_tables(db_path)
        
        if update_csv_success and update_json_success:
            print(f"\n✅ Successfully updated CSV_data_count in both map_csv and map_json tables")
        elif update_csv_success:
            print(f"\n⚠️  Updated CSV_data_count in map_csv tables, but failed for map_json tables")
        elif update_json_success:
            print(f"\n⚠️  Updated CSV_data_count in map_json tables, but failed for map_csv tables")
        else:
            print(f"\n❌ Failed to update CSV_data_count in both table types")
        
        conn.close()
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 FIELD-LEVEL MAPPING SUMMARY")
        print("=" * 80)
        
        total_mapped_pct = (overall_results['total_mapped_fields'] / overall_results['total_json_fields'] * 100) if overall_results['total_json_fields'] > 0 else 0
        total_high_conf_pct = (overall_results['total_high_confidence'] / overall_results['total_mapped_fields'] * 100) if overall_results['total_mapped_fields'] > 0 else 0
        
        print(f"✅ Tables processed: {overall_results['tables_processed']}")
        print(f"📊 Total JSON fields: {overall_results['total_json_fields']}")
        print(f"🔗 Total mapped fields: {overall_results['total_mapped_fields']} ({total_mapped_pct:.1f}%)")
        print(f"🎯 High confidence mappings: {overall_results['total_high_confidence']} ({total_high_conf_pct:.1f}%)")
        
        logger.info(f"Field-level mapping complete: {overall_results['total_mapped_fields']}/{overall_results['total_json_fields']} fields mapped")
        
    except Exception as e:
        logger.error(f"Critical error in field-level mapping: {str(e)}")
        print(f"❌ CRITICAL ERROR: {str(e)}")
        overall_results['error'] = str(e)
    
    return overall_results

def main():
    """Main execution function"""
    print("🚀 Starting Field-Level Mapping Process")
    print("=" * 80)
    
    results = run_field_level_mapping()
    
    if 'error' in results:
        print(f"\n❌ FIELD MAPPING COMPLETED WITH ERRORS")
        return False
    else:
        print(f"\n✅ FIELD MAPPING COMPLETED SUCCESSFULLY")
        return True

if __name__ == "__main__":
    success = main()
