#!/usr/bin/env python3
"""
Enhanced Duplicate Prevention System
Implements comprehensive safeguards against duplicate data during repeated runs
"""

import sqlite3
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

# Add the json2db_sync package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class DuplicatePreventionManager:
    """Manages duplicate prevention mechanisms for JSON2DB sync operations"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._ensure_tracking_tables()
    
    def _ensure_tracking_tables(self):
        """Create tracking tables for duplicate prevention"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create session tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_tracking (
                    session_id TEXT PRIMARY KEY,
                    session_path TEXT NOT NULL,
                    processing_started DATETIME,
                    processing_completed DATETIME,
                    status TEXT DEFAULT 'in_progress',
                    total_records_processed INTEGER DEFAULT 0,
                    modules_processed TEXT,  -- JSON array of module names
                    created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, session_path)
                )
            """)
            
            # Create data source tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_source_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    records_count INTEGER,
                    last_processed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    UNIQUE(table_name, source_file, file_hash),
                    FOREIGN KEY (session_id) REFERENCES session_tracking(session_id)
                )
            """)
            
            # Create record processing log for detailed tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS record_processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id TEXT NOT NULL,  -- Primary key of the record
                    operation TEXT NOT NULL,  -- 'insert', 'update', 'skip'
                    session_id TEXT,
                    processed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_file TEXT,
                    FOREIGN KEY (session_id) REFERENCES session_tracking(session_id)
                )
            """)
            
            # Create index separately
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_record_processing_log_table_record 
                ON record_processing_log(table_name, record_id)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to create tracking tables: {e}")
            raise
    
    def is_session_processed(self, session_id: str, session_path: str) -> bool:
        """Check if a session has already been fully processed"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, processing_completed 
                FROM session_tracking 
                WHERE session_id = ? AND session_path = ?
            """, (session_id, session_path))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                status, completed = result
                return status == 'completed' and completed is not None
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking session status: {e}")
            return False
    
    def start_session_processing(self, session_id: str, session_path: str) -> bool:
        """Mark session as started and check for conflicts"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check if session is already being processed
            cursor.execute("""
                SELECT status, processing_started 
                FROM session_tracking 
                WHERE session_id = ? AND session_path = ?
            """, (session_id, session_path))
            
            existing = cursor.fetchone()
            
            if existing:
                status, started = existing
                if status == 'in_progress':
                    print(f"⚠️ Session {session_id} is already being processed (started: {started})")
                    conn.close()
                    return False
                elif status == 'completed':
                    print(f"✅ Session {session_id} already completed successfully")
                    conn.close()
                    return False
            
            # Insert or update session tracking
            cursor.execute("""
                INSERT OR REPLACE INTO session_tracking 
                (session_id, session_path, processing_started, status)
                VALUES (?, ?, ?, 'in_progress')
            """, (session_id, session_path, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error starting session processing: {e}")
            return False
    
    def complete_session_processing(self, session_id: str, total_records: int, modules: List[str]):
        """Mark session as completed successfully"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE session_tracking 
                SET processing_completed = ?, 
                    status = 'completed',
                    total_records_processed = ?,
                    modules_processed = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), total_records, json.dumps(modules), session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error completing session processing: {e}")
    
    def fail_session_processing(self, session_id: str, error_msg: str):
        """Mark session as failed"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE session_tracking 
                SET status = 'failed',
                    modules_processed = ?
                WHERE session_id = ?
            """, (error_msg, session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error marking session as failed: {e}")
    
    def is_file_processed(self, table_name: str, file_path: str, session_id: str) -> bool:
        """Check if a specific file has been processed for this table"""
        try:
            file_hash = self._get_file_hash(file_path)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT records_count, last_processed 
                FROM data_source_tracking 
                WHERE table_name = ? AND source_file = ? AND file_hash = ?
            """, (table_name, str(file_path), file_hash))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            print(f"⚠️ Error checking file processing status: {e}")
            return False
    
    def track_file_processing(self, table_name: str, file_path: str, records_count: int, session_id: str):
        """Track that a file has been processed"""
        try:
            file_hash = self._get_file_hash(file_path)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO data_source_tracking 
                (table_name, source_file, file_hash, records_count, session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (table_name, str(file_path), file_hash, records_count, session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error tracking file processing: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get SHA256 hash of file content for change detection"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            # If we can't read the file, use path and modification time
            path = Path(file_path)
            fallback_data = f"{file_path}_{path.stat().st_mtime}_{path.stat().st_size}"
            return hashlib.sha256(fallback_data.encode()).hexdigest()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processed sessions and files"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Session stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_sessions,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_sessions,
                    SUM(total_records_processed) as total_records
                FROM session_tracking
            """)
            
            session_stats = cursor.fetchone()
            
            # File processing stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_files_processed,
                    COUNT(DISTINCT table_name) as tables_affected,
                    SUM(records_count) as total_file_records
                FROM data_source_tracking
            """)
            
            file_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'sessions': {
                    'total': session_stats[0] or 0,
                    'completed': session_stats[1] or 0,
                    'failed': session_stats[2] or 0,
                    'in_progress': session_stats[3] or 0,
                    'total_records': session_stats[4] or 0
                },
                'files': {
                    'total_processed': file_stats[0] or 0,
                    'tables_affected': file_stats[1] or 0,
                    'total_records': file_stats[2] or 0
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting processing stats: {e}")
            return {'error': str(e)}

def create_enhanced_data_populator():
    """Create enhanced data populator with duplicate prevention"""
    
    enhanced_populator_code = '''
# Enhanced Data Populator with Duplicate Prevention
# Add this to your existing data_populator.py

class EnhancedJSONDataPopulator(JSONDataPopulator):
    """Enhanced data populator with comprehensive duplicate prevention"""
    
    def __init__(self, db_path: str = None, json_dir: str = None):
        super().__init__(db_path, json_dir)
        self.duplicate_manager = DuplicatePreventionManager(self.db_path)
    
    def populate_session_safely(self, session_path: str, modules: List[str] = None) -> Dict[str, Any]:
        """Safely populate data from a session with full duplicate prevention"""
        session_id = Path(session_path).name
        
        # Check if session already processed
        if self.duplicate_manager.is_session_processed(session_id, session_path):
            return {
                'success': True,
                'skipped': True,
                'message': f'Session {session_id} already processed',
                'records_processed': 0
            }
        
        # Start session processing
        if not self.duplicate_manager.start_session_processing(session_id, session_path):
            return {
                'success': False,
                'error': 'Session already being processed or completed',
                'records_processed': 0
            }
        
        try:
            total_records = 0
            processed_modules = []
            
            # Get JSON files from session
            if self.is_session_based:
                json_files_dict = self._get_session_json_files()
            else:
                # Handle traditional structure
                json_files_dict = self._get_traditional_json_files()
            
            # Filter modules if specified
            if modules:
                json_files_dict = {k: v for k, v in json_files_dict.items() 
                                 if any(module in str(v) for module in modules)}
            
            for file_key, file_path in json_files_dict.items():
                # Determine table name from file
                table_name = f"json_{file_path.stem}"
                
                # Check if this specific file was already processed
                if self.duplicate_manager.is_file_processed(table_name, str(file_path), session_id):
                    self.logger.info(f"File {file_path} already processed, skipping")
                    continue
                
                # Process the file
                cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                result = self.populate_table_from_path(table_name, file_path, cutoff_date)
                
                if result.get('success'):
                    records_processed = result.get('records_inserted', 0)
                    total_records += records_processed
                    
                    # Track file processing
                    self.duplicate_manager.track_file_processing(
                        table_name, str(file_path), records_processed, session_id
                    )
                    
                    processed_modules.append(file_path.stem)
                    self.logger.info(f"Processed {file_path.stem}: {records_processed} records")
                else:
                    self.logger.error(f"Failed to process {file_path}: {result.get('error')}")
            
            # Mark session as completed
            self.duplicate_manager.complete_session_processing(session_id, total_records, processed_modules)
            
            return {
                'success': True,
                'session_id': session_id,
                'records_processed': total_records,
                'modules_processed': processed_modules,
                'files_processed': len(json_files_dict)
            }
            
        except Exception as e:
            # Mark session as failed
            self.duplicate_manager.fail_session_processing(session_id, str(e))
            
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'records_processed': total_records if 'total_records' in locals() else 0
            }
    
    def populate_with_smart_updates(self, table_name: str, json_file_path: Path, 
                                   cutoff_date: str, force_update: bool = False) -> Dict[str, Any]:
        """Populate with smart update logic based on last modified time"""
        try:
            # Load JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            # Get table schema
            analyzer = self.analyzer if hasattr(self, 'analyzer') else JSONAnalyzer(str(json_file_path.parent))
            columns = analyzer.get_table_columns(table_name.replace('json_', ''))
            
            # Connect to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return {'success': False, 'error': f'Table {table_name} does not exist'}
            
            # Get primary key columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_info = cursor.fetchall()
            pk_columns = [row[1] for row in table_info if row[5]]  # row[5] is pk flag
            
            if not pk_columns:
                # Fallback to INSERT OR REPLACE if no primary keys
                return super().populate_table_from_path(table_name, json_file_path, cutoff_date)
            
            # Filter records by cutoff date
            cutoff_datetime = datetime.strptime(cutoff_date, "%Y-%m-%d")
            filtered_data = []
            
            for record in data:
                # Check various timestamp fields
                record_date = None
                for date_field in ['last_modified_time', 'modified_time', 'updated_time', 'created_time']:
                    if date_field in record and record[date_field]:
                        try:
                            record_date = datetime.fromisoformat(str(record[date_field]).replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                if not record_date or record_date >= cutoff_datetime:
                    filtered_data.append(record)
            
            # Process records with smart update logic
            records_inserted = 0
            records_updated = 0
            records_skipped = 0
            
            for record in filtered_data:
                # Build WHERE clause for existing record check
                pk_conditions = []
                pk_values = []
                
                for pk_col in pk_columns:
                    if pk_col in record:
                        pk_conditions.append(f"{pk_col} = ?")
                        pk_values.append(record[pk_col])
                
                if not pk_conditions:
                    continue  # Skip records without primary key values
                
                # Check if record exists
                where_clause = " AND ".join(pk_conditions)
                cursor.execute(f"SELECT last_modified_time FROM {table_name} WHERE {where_clause}", pk_values)
                existing = cursor.fetchone()
                
                if existing and not force_update:
                    # Check if source record is newer
                    existing_time = existing[0]
                    source_time = record.get('last_modified_time') or record.get('modified_time')
                    
                    if existing_time and source_time:
                        try:
                            existing_dt = datetime.fromisoformat(str(existing_time).replace('Z', '+00:00'))
                            source_dt = datetime.fromisoformat(str(source_time).replace('Z', '+00:00'))
                            
                            if source_dt <= existing_dt:
                                records_skipped += 1
                                continue  # Skip older data
                        except:
                            pass  # If date parsing fails, proceed with update
                
                # Clean and insert/update record
                cleaned_record = self.clean_record_for_insert(record, columns)
                column_names = list(cleaned_record.keys())
                placeholders = ', '.join(['?' for _ in column_names])
                values = tuple(cleaned_record.get(col) for col in column_names)
                
                insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                cursor.execute(insert_sql, values)
                
                if existing:
                    records_updated += 1
                else:
                    records_inserted += 1
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'records_inserted': records_inserted,
                'records_updated': records_updated,
                'records_skipped': records_skipped,
                'total_processed': len(filtered_data)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
'''
    
    return enhanced_populator_code

def main():
    """Demonstrate and implement enhanced duplicate prevention"""
    print("🛡️ ENHANCED DUPLICATE PREVENTION SYSTEM")
    print("=" * 80)
    
    # Test with the actual database
    try:
        from json2db_config import JSON2DBSyncConfig
        config = JSON2DBSyncConfig()
        db_path = config.get_database_path()
        
        print(f"📁 Setting up duplicate prevention for: {db_path}")
        
        # Initialize duplicate prevention manager
        dup_manager = DuplicatePreventionManager(db_path)
        print("✅ Duplicate prevention manager initialized")
        
        # Get current stats
        stats = dup_manager.get_processing_stats()
        print(f"📊 Current processing stats:")
        print(f"   Sessions: {stats['sessions']['total']} total, {stats['sessions']['completed']} completed")
        print(f"   Files: {stats['files']['total_processed']} processed, {stats['files']['tables_affected']} tables affected")
        
        # Test with latest session
        latest_session = config.get_latest_session_folder()
        if latest_session:
            session_path = Path(config.get_api_sync_path()) / "data" / "sync_sessions" / latest_session
            session_id = str(latest_session).replace("sync_session_", "")
            
            print(f"\n🧪 Testing with session: {session_id}")
            
            # Check if already processed
            is_processed = dup_manager.is_session_processed(session_id, str(session_path))
            print(f"   Already processed: {is_processed}")
            
            if not is_processed:
                # Simulate starting processing
                can_start = dup_manager.start_session_processing(session_id, str(session_path))
                print(f"   Can start processing: {can_start}")
                
                if can_start:
                    # Simulate completion
                    dup_manager.complete_session_processing(session_id, 100, ["invoices", "bills"])
                    print("   ✅ Simulated successful processing")
        
        # Save enhanced populator code
        enhanced_code = create_enhanced_data_populator()
        with open("enhanced_data_populator.py", "w") as f:
            f.write(enhanced_code)
        print("\n📄 Enhanced data populator code saved to enhanced_data_populator.py")
        
        print("\n🎉 Enhanced duplicate prevention system ready!")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
