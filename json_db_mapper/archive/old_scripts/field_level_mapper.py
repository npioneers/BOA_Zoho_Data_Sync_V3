"""
Field-Level Mapper
Maps individual fields between JSON and CSV tables based on table-level mappings
"""
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher


class FieldLevelMapper:
    """Maps individual fields between JSON and CSV mapping tables"""
    
    def __init__(self, db_path: str = "../data/database/production.db"):
        self.db_path = Path(db_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for field-level mapper"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"field_level_mapper_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Field Level Mapper started - Logging to: {log_file}")

    def calculate_field_similarity(self, json_field: str, csv_field: str, 
                                 json_type: str = None, csv_type: str = None) -> float:
        """Calculate similarity score between two field names"""
        # Exact match gets highest score
        if json_field.lower() == csv_field.lower():
            return 1.0
        
        # Remove common prefixes/suffixes for comparison
        json_clean = self.clean_field_name(json_field)
        csv_clean = self.clean_field_name(csv_field)
        
        if json_clean.lower() == csv_clean.lower():
            return 0.95
        
        # Calculate string similarity
        similarity = SequenceMatcher(None, json_clean.lower(), csv_clean.lower()).ratio()
        
        # Boost score for partial matches
        if json_clean.lower() in csv_clean.lower() or csv_clean.lower() in json_clean.lower():
            similarity += 0.1
        
        # Boost score for type compatibility
        if json_type and csv_type:
            if self.are_types_compatible(json_type, csv_type):
                similarity += 0.05
        
        return min(similarity, 1.0)

    def clean_field_name(self, field_name: str) -> str:
        """Clean field name by removing common prefixes/suffixes"""
        # Remove common prefixes
        prefixes_to_remove = ['cf_', 'custom_', 'item_', 'contact_', 'bill_', 'invoice_', 'order_']
        cleaned = field_name.lower()
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        
        # Remove common suffixes
        suffixes_to_remove = ['_id', '_name', '_code', '_value', '_amount', '_date', '_time']
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                break
        
        return cleaned

    def are_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two field types are compatible"""
        if not type1 or not type2:
            return False
        
        type1_lower = type1.lower()
        type2_lower = type2.lower()
        
        # Exact match
        if type1_lower == type2_lower:
            return True
        
        # Text/string compatibility
        text_types = ['text', 'varchar', 'char', 'string']
        if any(t in type1_lower for t in text_types) and any(t in type2_lower for t in text_types):
            return True
        
        # Numeric compatibility
        numeric_types = ['int', 'integer', 'real', 'float', 'double', 'decimal', 'numeric']
        if any(t in type1_lower for t in numeric_types) and any(t in type2_lower for t in numeric_types):
            return True
        
        return False

    def get_json_table_mappings(self) -> Dict[str, str]:
        """Get table-level mappings by inferring from table names"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all JSON mapping tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'map_json_%'
            """)
            json_tables = [row[0] for row in cursor.fetchall()]
            
            # Get all CSV mapping tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'map_csv_%'
            """)
            csv_tables = [row[0] for row in cursor.fetchall()]
            
            mappings = {}
            for json_table in json_tables:
                # Extract the entity name (e.g., 'invoices' from 'map_json_invoices')
                entity_name = json_table.replace('map_json_', '')
                
                # Find the best matching CSV table
                best_match = None
                best_score = 0
                
                for csv_table in csv_tables:
                    csv_entity = csv_table.replace('map_csv_', '')
                    
                    # Direct match
                    if entity_name == csv_entity:
                        best_match = csv_table
                        break
                    
                    # Similarity matching for cases like 'invoices' vs 'invoice'
                    similarity = self.calculate_similarity(entity_name, csv_entity)
                    if similarity > best_score and similarity > 0.7:  # Minimum threshold
                        best_score = similarity
                        best_match = csv_table
                
                if best_match:
                    mappings[json_table] = best_match
                    self.logger.info(f"Mapped {json_table} -> {best_match}")
                else:
                    self.logger.warning(f"No suitable CSV table found for {json_table}")
            
            conn.close()
            return mappings
            
        except Exception as e:
            self.logger.error(f"Error getting table mappings: {e}")
            return {}

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        # Handle plurals and common variations
        str1_clean = str1.rstrip('s').lower()
        str2_clean = str2.rstrip('s').lower()
        
        if str1_clean == str2_clean:
            return 1.0
        
        # Use sequence matcher for similarity
        return SequenceMatcher(None, str1_clean, str2_clean).ratio()

    def get_table_fields(self, table_name: str) -> List[Dict]:
        """Get all fields from a mapping table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT field_name, field_type, id
                FROM {table_name}
                ORDER BY field_position
            """)
            
            fields = []
            for row in cursor.fetchall():
                fields.append({
                    'name': row[0],
                    'type': row[1],
                    'id': row[2]
                })
            
            conn.close()
            return fields
            
        except Exception as e:
            self.logger.error(f"Error getting fields from {table_name}: {e}")
            return []

    def find_best_field_match(self, json_field: Dict, csv_fields: List[Dict], 
                            min_score: float = 0.3) -> Optional[Tuple[Dict, float]]:
        """Find the best matching CSV field for a JSON field"""
        best_match = None
        best_score = 0.0
        
        for csv_field in csv_fields:
            score = self.calculate_field_similarity(
                json_field['name'], 
                csv_field['name'],
                json_field.get('type'),
                csv_field.get('type')
            )
            
            if score > best_score and score >= min_score:
                best_score = score
                best_match = csv_field
        
        return (best_match, best_score) if best_match else None

    def update_field_mapping(self, json_table: str, json_field_id: int, 
                           csv_table: str, csv_field: str) -> bool:
        """Update the CSV_table and CSV_field columns for a JSON field"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean the CSV table name by removing 'map_' prefix
            clean_csv_table = csv_table.replace('map_', '') if csv_table.startswith('map_') else csv_table
            
            cursor.execute(f"""
                UPDATE {json_table} 
                SET CSV_table = ?, CSV_field = ?
                WHERE id = ?
            """, (clean_csv_table, csv_field, json_field_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating field mapping: {e}")
            return False

    def map_fields_for_table(self, json_table: str, csv_table: str) -> Dict:
        """Map all fields from a JSON table to the best matching CSV fields"""
        self.logger.info(f"Mapping fields: {json_table} -> {csv_table}")
        
        # Get fields from both tables
        json_fields = self.get_table_fields(json_table)
        csv_fields = self.get_table_fields(csv_table)
        
        if not json_fields or not csv_fields:
            self.logger.warning(f"No fields found for {json_table} or {csv_table}")
            return {'mapped': 0, 'total': 0, 'mappings': []}
        
        mappings = []
        mapped_count = 0
        
        for json_field in json_fields:
            match_result = self.find_best_field_match(json_field, csv_fields)
            
            if match_result:
                csv_field, score = match_result
                
                # Update the database
                success = self.update_field_mapping(
                    json_table, 
                    json_field['id'], 
                    csv_table, 
                    csv_field['name']
                )
                
                if success:
                    mapped_count += 1
                    mappings.append({
                        'json_field': json_field['name'],
                        'csv_field': csv_field['name'],
                        'score': score,
                        'status': 'success'
                    })
                    self.logger.info(f"  {json_field['name']} -> {csv_field['name']} (score: {score:.3f})")
                else:
                    mappings.append({
                        'json_field': json_field['name'],
                        'csv_field': None,
                        'score': 0.0,
                        'status': 'update_failed'
                    })
            else:
                mappings.append({
                    'json_field': json_field['name'],
                    'csv_field': None,
                    'score': 0.0,
                    'status': 'no_match'
                })
                self.logger.info(f"  {json_field['name']} -> No suitable match found")
        
        return {
            'mapped': mapped_count,
            'total': len(json_fields),
            'mappings': mappings
        }

    def map_all_fields(self) -> Dict:
        """Map fields for all JSON tables based on their table-level mappings"""
        self.logger.info("Starting field-level mapping process...")
        
        table_mappings = self.get_json_table_mappings()
        results = {
            'table_results': {},
            'summary': {
                'total_tables': len(table_mappings),
                'total_fields_processed': 0,
                'total_fields_mapped': 0,
                'tables_processed': 0
            }
        }
        
        for json_table, csv_table in table_mappings.items():
            self.logger.info(f"Processing table mapping: {json_table} -> {csv_table}")
            
            table_result = self.map_fields_for_table(json_table, csv_table)
            results['table_results'][json_table] = table_result
            results['table_results'][json_table]['csv_table'] = csv_table
            
            # Update summary
            results['summary']['total_fields_processed'] += table_result['total']
            results['summary']['total_fields_mapped'] += table_result['mapped']
            results['summary']['tables_processed'] += 1
        
        self.logger.info(f"Field mapping complete: {results['summary']['total_fields_mapped']}/{results['summary']['total_fields_processed']} fields mapped across {results['summary']['tables_processed']} tables")
        
        return results

    def print_field_mapping_summary(self, results: Dict):
        """Print a formatted summary of field mapping results"""
        print("\n" + "="*100)
        print("FIELD-LEVEL MAPPING RESULTS")
        print("="*100)
        
        summary = results['summary']
        print(f"\nSUMMARY:")
        print(f"  Tables processed: {summary['tables_processed']}/{summary['total_tables']}")
        print(f"  Fields mapped: {summary['total_fields_mapped']}/{summary['total_fields_processed']}")
        
        if summary['total_fields_processed'] > 0:
            success_rate = (summary['total_fields_mapped'] / summary['total_fields_processed']) * 100
            print(f"  Success rate: {success_rate:.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        print("-" * 100)
        print(f"{'JSON Table':<35} {'CSV Table':<35} {'Fields':<10} {'Success'}")
        print("-" * 100)
        
        for json_table, result in results['table_results'].items():
            csv_table = result.get('csv_table', 'N/A')
            fields_info = f"{result['mapped']}/{result['total']}"
            success_rate = f"{(result['mapped']/result['total']*100):.1f}%" if result['total'] > 0 else "0%"
            
            print(f"{json_table:<35} {csv_table:<35} {fields_info:<10} {success_rate}")
        
        print("="*100)


def main():
    """Test the field-level mapper"""
    mapper = FieldLevelMapper()
    results = mapper.map_all_fields()
    mapper.print_field_mapping_summary(results)


if __name__ == "__main__":
    main()
