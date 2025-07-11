#!/usr/bin/env python3
"""Quick script to examine mapping table contents"""

import sqlite3
from pathlib import Path

def examine_mapping_table(table_name: str = "map_json_invoices"):
    db_path = Path("../data/database/production.db")
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    try:
        # Get sample of mapping data
        cursor = conn.execute(f"""
            SELECT field_name, field_type, mapped_CSV, CSV_table, CSV_field 
            FROM {table_name} 
            ORDER BY field_position 
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        print(f"\nMapping Table: {table_name}")
        print("="*80)
        print(f"{'JSON Field':<25} {'Type':<15} {'Mapped CSV':<20} {'CSV Table':<15} {'CSV Field':<15}")
        print("-"*80)
        
        for row in rows:
            json_field, field_type, mapped_csv, csv_table, csv_field = row
            mapped_csv = mapped_csv or "None"
            csv_table = csv_table or ""
            csv_field = csv_field or ""
            print(f"{json_field:<25} {field_type:<15} {mapped_csv:<20} {csv_table:<15} {csv_field:<15}")
        
        # Get total counts
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = cursor.fetchone()[0]
        
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE mapped_CSV IS NOT NULL")
        mapped = cursor.fetchone()[0]
        
        print("-"*80)
        print(f"Total fields: {total}, Mapped fields: {mapped}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    examine_mapping_table("map_json_invoices")
    print()
    examine_mapping_table("map_json_items")
