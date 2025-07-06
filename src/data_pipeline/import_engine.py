#!/usr/bin/env python3
"""
Import Engine Module
===================
Handles the actual importing of data from JSON to database.
"""

import traceback
from .transformer import UniversalTransformer

class ImportEngine:
    def __init__(self, database_manager, json_scanner):
        self.db = database_manager
        self.json_scanner = json_scanner
        self.data_transformer = UniversalTransformer()
    
    def import_single_table(self, table_info):
        """Import a single table with detailed progress tracking"""
        
        table_name = table_info['table']
        mapping = table_info['mapping']
        json_file = table_info['json_file']
        
        print(f"\n📥 IMPORTING TABLE: {table_name}")
        print("=" * 60)
        print(f"📂 Source file: {json_file}")
        print(f"🎯 Target table: {table_name}")
        print(f"📝 Description: {mapping['description']}")
        
        try:
            # Load records from JSON
            records = self.json_scanner.load_records(json_file)
            
            print(f"📊 Records to import: {len(records):,}")
            
            if not records:
                print(f"📭 No records to import - skipping")
                return True
            
            # Load records from JSON
            records = self.json_scanner.load_records(json_file)
            
            print(f"📊 Records to import: {len(records):,}")
            
            if not records:
                print(f"📭 No records to import - skipping")
                return True
            
            # Detect and add any missing custom fields
            columns = self._detect_and_add_custom_fields(table_name, records)
            
            # If no columns were returned, get the current table columns
            if not columns:
                columns = self.db.get_table_columns(table_name)
                
            if not columns:
                raise Exception(f"Could not get columns for table {table_name}")
            
            print(f"📋 Table columns ({len(columns)}): {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
            
            # Show sample record structure
            if records:
                sample = records[0]
                sample_keys = list(sample.keys())[:5]
                print(f"🔍 Sample record keys: {', '.join(sample_keys)}{'...' if len(sample.keys()) > 5 else ''}")
            
            # Import records with progress tracking
            success = self._import_records_with_progress(table_name, records, mapping)
            
            if success:
                # Verify import
                verification_passed = self._verify_import(table_name, len(records))
                
                if verification_passed:
                    print(f"✅ IMPORT SUCCESSFUL")
                    return True
                else:
                    print(f"⚠️  IMPORT COMPLETED WITH VERIFICATION ISSUES")
                    return False
            else:
                print(f"❌ IMPORT FAILED")
                return False
        
        except Exception as e:
            print(f"❌ Import failed with error: {e}")
            if hasattr(e, '__traceback__'):
                print(f"🔍 Traceback: {traceback.format_exc()}")
            return False
    
    def _import_records_with_progress(self, table_name, records, mapping):
        """Import records with detailed progress tracking"""
        
        batch_size = self.settings['batch_size']
        progress_display = self.settings['progress_display']
        max_display = self.settings['max_display_records']
        
        try:
            imported_count = 0
            total_records = len(records)
            
            print(f"\n🔄 Starting import...")
            print(f"   📦 Batch size: {batch_size}")
            print(f"   📊 Progress updates every: {progress_display} records")
            
            for i, record in enumerate(records, 1):
                try:
                    # Prepare record data
                    success = self._insert_single_record(table_name, record)
                    
                    if success:
                        imported_count += 1
                    
                    # Show progress for first few records or at intervals
                    if i <= max_display or i % progress_display == 0 or i == total_records:
                        self._display_import_progress(i, total_records, record, mapping, success)
                    
                    # Commit every batch_size records
                    if i % batch_size == 0:
                        self.db.conn.commit()
                        if i % (progress_display * 5) == 0:  # Less frequent batch notifications
                            print(f"   💾 Committed batch (up to record {i:,})")
                
                except Exception as e:
                    print(f"   ❌ Record {i:,} failed: {e}")
            
            # Final commit
            self.db.conn.commit()
            
            print(f"\n✅ Import phase complete")
            print(f"   📊 Successfully imported: {imported_count:,}/{total_records:,} records")
            print(f"   📈 Success rate: {(imported_count/total_records*100):.1f}%")
            
            # Show transformation statistics
            transform_stats = self.data_transformer.get_stats()
            if transform_stats['transformations_applied'] > 0:
                print(f"   🔄 Data transformations applied: {transform_stats['transformations_applied']:,}")
            if transform_stats['errors'] > 0:
                print(f"   ⚠️  Transformation errors: {transform_stats['errors']}")
            
            return imported_count > 0
            
        except Exception as e:
            print(f"❌ Import process failed: {e}")
            return False
    
    def _insert_single_record(self, table_name, record):
        """Insert a single record into the database with data transformation"""
        
        try:
            # Transform the record for SQLite compatibility
            transformed_record = self.data_transformer.transform_record(record, table_name)
            
            # Get table columns
            columns = self.db.get_table_columns(table_name)
            
            # Prepare record data
            record_data = {}
            for col in columns:
                record_data[col] = transformed_record.get(col, None)
            
            # Insert record
            cols = list(record_data.keys())
            placeholders = ', '.join(['?' for _ in cols])
            values = list(record_data.values())
            
            insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"
            self.db.cursor.execute(insert_sql, values)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Single record insert failed: {e}")
            return False
    
    def _display_import_progress(self, current, total, record, mapping, success):
        """Display import progress for a single record"""
        
        status = "✅" if success else "❌"
        percentage = (current / total) * 100
        
        # Get display value from record
        display_field = mapping.get('display_field', mapping.get('id_field', 'record'))
        display_value = record.get(display_field, f"Record {current}")
        
        # Truncate long display values
        if len(str(display_value)) > 50:
            display_value = str(display_value)[:47] + "..."
        
        print(f"   {status} {current:,}/{total:,} ({percentage:5.1f}%): {display_value}")
    
    def _verify_import(self, table_name, expected_count):
        """Verify that import was successful"""
        
        print(f"\n🔍 Verifying import...")
        
        if self.settings['verify_after_import']:
            actual_count = self.db.get_table_count(table_name)
            
            print(f"   📊 Expected minimum: {expected_count:,}")
            print(f"   📊 Actual count: {actual_count:,}")
            
            if actual_count >= expected_count:
                print(f"   ✅ Verification successful")
                return True
            else:
                print(f"   ⚠️  Verification warning: count mismatch")
                return False
        else:
            print(f"   ⏭️  Verification skipped (disabled in settings)")
            return True
    
    def import_multiple_tables(self, import_plan):
        """Import multiple tables according to the import plan"""
        
        print(f"\n🚀 STARTING MULTI-TABLE IMPORT")
        print("=" * 60)
        print(f"📋 Tables to import: {len(import_plan)}")
        
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        for i, table_info in enumerate(import_plan, 1):
            print(f"\n📋 STEP {i}/{len(import_plan)}")
            print("=" * 40)
            
            success = self.import_single_table(table_info)
            
            if success:
                results['success'].append(table_info['table'])
                print(f"✅ Table {table_info['table']} imported successfully")
            else:
                results['failed'].append(table_info['table'])
                print(f"❌ Table {table_info['table']} import failed")
                
                if self.settings['continue_on_error']:
                    print(f"⚠️  Continuing with next table (continue_on_error=True)")
                else:
                    print(f"🛑 Stopping import (continue_on_error=False)")
                    break
        
        return results
    

    def _detect_and_add_custom_fields(self, table_name, records):
        """Detect and add custom fields to the database schema if not present"""
        
        if not records or not isinstance(records[0], dict):
            return
            
        # Get sample record
        sample = records[0]
        
        # Collect all custom field names
        custom_fields = []
        for key in sample.keys():
            if key.startswith('cf_'):
                custom_fields.append(key)
        
        if not custom_fields:
            return
            
        # Get existing table columns
        existing_columns = self.db.get_table_columns(table_name)
        
        # Find missing custom fields
        missing_fields = [field for field in custom_fields if field not in existing_columns]
        
        if not missing_fields:
            return
            
        print(f"🔍 Detected {len(missing_fields)} missing custom fields in {table_name}: {', '.join(missing_fields)}")
        
        # Add missing custom fields to the database schema
        added_count = 0
        for field in missing_fields:
            try:
                # Add the column with TEXT type
                self.db.conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {field} TEXT")
                added_count += 1
                print(f"  ✓ Added custom field to schema: {field}")
            except Exception as e:
                print(f"  ✗ Error adding custom field {field}: {e}")
                
        # Commit changes
        self.db.conn.commit()
        
        if added_count > 0:
            print(f"✅ Added {added_count} new custom fields to {table_name} table schema")
            
            # Refresh columns in case more processing is needed
            return self.db.get_table_columns(table_name)
        
        return existing_columns
    
    def display_import_summary(self, results):
        """Display final import summary"""
        
        print(f"\n🎉 IMPORT SUMMARY")
        print("=" * 50)
        
        total_tables = len(results['success']) + len(results['failed']) + len(results['skipped'])
        success_count = len(results['success'])
        
        print(f"📊 Total tables processed: {total_tables}")
        print(f"✅ Successful imports: {success_count}")
        print(f"❌ Failed imports: {len(results['failed'])}")
        print(f"⏭️  Skipped tables: {len(results['skipped'])}")
        
        if success_count > 0:
            success_rate = (success_count / total_tables) * 100 if total_tables > 0 else 0
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        if results['success']:
            print(f"\n✅ Successfully imported tables:")
            for table in results['success']:
                print(f"   • {table}")
        
        if results['failed']:
            print(f"\n❌ Failed to import tables:")
            for table in results['failed']:
                print(f"   • {table}")
        
        if results['skipped']:
            print(f"\n⏭️  Skipped tables:")
            for table in results['skipped']:
                print(f"   • {table}")
        
        return success_count == total_tables
