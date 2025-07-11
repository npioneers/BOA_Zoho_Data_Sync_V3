"""
Clean up mapping tables and recreate with correct naming convention
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

def cleanup_and_recreate_mapping_tables():
    """Drop old mapping tables and create new ones with correct naming"""
    db_path = "../data/database/production.db"
    
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"cleanup_mapping_tables_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables with old naming convention
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_map'")
        old_mapping_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(old_mapping_tables)} old mapping tables to drop:")
        for table in old_mapping_tables:
            print(f"  - {table}")
        
        # Drop old mapping tables
        for table in old_mapping_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Dropped old mapping table: {table}")
        
        conn.commit()
        print(f"\n✅ Dropped {len(old_mapping_tables)} old mapping tables")
        
        # Verify no old mapping tables remain
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_map'")
        remaining_old = cursor.fetchall()
        
        if remaining_old:
            print(f"⚠️ Warning: {len(remaining_old)} old mapping tables still exist")
        else:
            print("✅ All old mapping tables successfully removed")
        
        # Check for new mapping tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_%'")
        new_mapping_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nExisting new mapping tables: {len(new_mapping_tables)}")
        for table in new_mapping_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    cleanup_and_recreate_mapping_tables()
