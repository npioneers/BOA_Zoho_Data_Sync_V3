"""
Field Mapping Module
Maps fields between JSON and CSV tables by finding best matches
"""
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import difflib


class FieldMapper:
    """Maps fields between JSON and CSV tables based on similarity"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for field mapper"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"field_mapper_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Field Mapper started - Logging to: {log_file}")

    def get_json_mapping_tables(self) -> List[str]:
        """Get all JSON mapping tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_json_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            self.logger.error(f"Error getting JSON mapping tables: {e}")
            return []

    def get_csv_mapping_tables(self) -> List[str]:
        """Get all CSV mapping tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_csv_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            self.logger.error(f"Error getting CSV mapping tables: {e}")
            return []

    def get_table_fields(self, table_name: str) -> List[str]:
        """Get field names from a mapping table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT field_name FROM {table_name} ORDER BY field_position")
            fields = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return fields
            
        except Exception as e:
            self.logger.error(f"Error getting fields from {table_name}: {e}")
            return []

    def calculate_table_similarity(self, json_fields: List[str], csv_fields: List[str]) -> float:
        """Calculate similarity between two sets of fields"""
        if not json_fields or not csv_fields:
            return 0.0
        
        # Convert to lowercase for comparison
        json_fields_lower = [field.lower() for field in json_fields]
        csv_fields_lower = [field.lower() for field in csv_fields]
        
        # Calculate Jaccard similarity (intersection over union)
        json_set = set(json_fields_lower)
        csv_set = set(csv_fields_lower)
        
        intersection = len(json_set.intersection(csv_set))
        union = len(json_set.union(csv_set))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Also consider field name similarity using difflib
        similarity_scores = []
        for json_field in json_fields_lower:
            best_match = difflib.get_close_matches(json_field, csv_fields_lower, n=1, cutoff=0.6)
            if best_match:
                similarity_scores.append(difflib.SequenceMatcher(None, json_field, best_match[0]).ratio())
        
        # Average field similarity
        avg_field_similarity = sum(similarity_scores) / len(json_fields) if similarity_scores else 0.0
        
        # Combined score: 70% Jaccard + 30% field similarity
        combined_score = (jaccard_similarity * 0.7) + (avg_field_similarity * 0.3)
        
        return combined_score

    def find_best_csv_match(self, json_table: str) -> Tuple[Optional[str], float]:
        """Find the best CSV table match for a JSON table"""
        # Extract base table name from JSON table
        # e.g., "map_json_invoices" -> "invoices"
        json_base_name = json_table.replace("map_json_", "")
        
        # Get fields from JSON table
        json_fields = self.get_table_fields(json_table)
        if not json_fields:
            return None, 0.0
        
        # Get all CSV mapping tables
        csv_tables = self.get_csv_mapping_tables()
        
        best_match = None
        best_score = 0.0
        
        for csv_table in csv_tables:
            # Extract base name from CSV table
            csv_base_name = csv_table.replace("map_csv_", "")
            
            # First check for exact name match (highest priority)
            if json_base_name == csv_base_name:
                csv_fields = self.get_table_fields(csv_table)
                similarity = self.calculate_table_similarity(json_fields, csv_fields)
                # Boost score for exact name match
                similarity = min(1.0, similarity + 0.3)
                if similarity > best_score:
                    best_match = csv_table
                    best_score = similarity
                continue
            
            # Check for partial name matches
            if json_base_name in csv_base_name or csv_base_name in json_base_name:
                csv_fields = self.get_table_fields(csv_table)
                similarity = self.calculate_table_similarity(json_fields, csv_fields)
                # Boost score for partial name match
                similarity = min(1.0, similarity + 0.2)
                if similarity > best_score:
                    best_match = csv_table
                    best_score = similarity
                continue
            
            # Calculate field-based similarity for all other tables
            csv_fields = self.get_table_fields(csv_table)
            similarity = self.calculate_table_similarity(json_fields, csv_fields)
            
            if similarity > best_score:
                best_match = csv_table
                best_score = similarity
        
        return best_match, best_score

    def update_json_mapping_table(self, json_table: str, csv_table: str) -> bool:
        """Update the CSV_table column in a JSON mapping table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean the CSV table name (remove "map_" prefix)
            clean_csv_table = csv_table.replace("map_", "")
            
            # Update all rows in the JSON mapping table with clean CSV_table name
            cursor.execute(f"UPDATE {json_table} SET CSV_table = ?", (clean_csv_table,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated {json_table} -> mapped to {clean_csv_table}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating {json_table}: {e}")
            return False

    def map_all_json_tables(self, min_similarity: float = 0.3) -> Dict[str, Dict]:
        """Map all JSON tables to their best CSV matches"""
        self.logger.info("Starting field mapping process...")
        
        results = {
            'mappings': {},
            'summary': {
                'total_json_tables': 0,
                'successful_mappings': 0,
                'failed_mappings': 0,
                'low_confidence_mappings': 0
            }
        }
        
        json_tables = self.get_json_mapping_tables()
        results['summary']['total_json_tables'] = len(json_tables)
        
        for json_table in json_tables:
            self.logger.info(f"Processing {json_table}...")
            
            best_csv_match, similarity_score = self.find_best_csv_match(json_table)
            
            if best_csv_match and similarity_score >= min_similarity:
                # Update the mapping table
                if self.update_json_mapping_table(json_table, best_csv_match):
                    results['mappings'][json_table] = {
                        'csv_match': best_csv_match,
                        'similarity_score': similarity_score,
                        'confidence': 'high' if similarity_score >= 0.7 else 'medium',
                        'status': 'success'
                    }
                    results['summary']['successful_mappings'] += 1
                    
                    if similarity_score < 0.7:
                        results['summary']['low_confidence_mappings'] += 1
                else:
                    results['mappings'][json_table] = {
                        'csv_match': best_csv_match,
                        'similarity_score': similarity_score,
                        'confidence': 'low',
                        'status': 'update_failed'
                    }
                    results['summary']['failed_mappings'] += 1
            else:
                results['mappings'][json_table] = {
                    'csv_match': best_csv_match,
                    'similarity_score': similarity_score,
                    'confidence': 'very_low',
                    'status': 'no_match'
                }
                results['summary']['failed_mappings'] += 1
                self.logger.warning(f"No suitable match found for {json_table} (best score: {similarity_score:.3f})")
        
        self.logger.info(f"Field mapping complete: {results['summary']['successful_mappings']}/{results['summary']['total_json_tables']} successful")
        return results

    def print_mapping_results(self, results: Dict[str, Dict]):
        """Print formatted mapping results"""
        print("\n" + "="*80)
        print("FIELD MAPPING RESULTS")
        print("="*80)
        
        print(f"\nSUMMARY:")
        print(f"  Total JSON tables: {results['summary']['total_json_tables']}")
        print(f"  Successful mappings: {results['summary']['successful_mappings']}")
        print(f"  Failed mappings: {results['summary']['failed_mappings']}")
        print(f"  Low confidence mappings: {results['summary']['low_confidence_mappings']}")
        
        print(f"\nDETAILED MAPPINGS:")
        print("-" * 80)
        print(f"{'JSON Table':<35} {'CSV Match':<35} {'Score':<8} {'Status'}")
        print("-" * 80)
        
        for json_table, mapping_info in results['mappings'].items():
            csv_match = mapping_info.get('csv_match', 'No match')
            score = mapping_info.get('similarity_score', 0.0)
            status = mapping_info.get('status', 'unknown')
            
            # Color coding for status
            status_symbol = "✅" if status == 'success' else "❌" if status == 'no_match' else "⚠️"
            
            print(f"{json_table:<35} {csv_match:<35} {score:<8.3f} {status_symbol} {status}")
        
        print("="*80)


def main():
    """Test the field mapping functionality"""
    # Test with main production database
    db_path = "../data/database/production.db"
    
    print(f"\nTesting field mapping with: {db_path}")
    print("-" * 60)
    
    try:
        mapper = FieldMapper(db_path)
        results = mapper.map_all_json_tables()
        mapper.print_mapping_results(results)
    except Exception as e:
        print(f"Error processing {db_path}: {e}")


if __name__ == "__main__":
    main()
