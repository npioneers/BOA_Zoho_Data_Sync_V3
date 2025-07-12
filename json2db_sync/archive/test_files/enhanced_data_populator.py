
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
