#!/usr/bin/env python3
"""
Compare CSV structure with database schema
"""

import pandas as pd
import sqlite3
import os

def compare_schemas():
    db_path = "data/database/production.db"
    csv_dir = "data/csv/Nangsel Pioneers_Latest"
    
    print("Comparing CSV structure with database schema...")
    print("=" * 60)
    
    # Get CSV files
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get database tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    db_tables = [table[0] for table in cursor.fetchall()]
    
    print(f"\nCSV files found: {len(csv_files)}")
    print(f"Database tables: {len(db_tables)}")
    
    # Compare each CSV with corresponding table
    for csv_file in sorted(csv_files):
        table_name = csv_file.replace('.csv', '')
        
        print(f"\n{'=' * 40}")
        print(f"Checking: {csv_file} -> {table_name}")
        
        if table_name in db_tables:
            # Get CSV column count
            csv_path = os.path.join(csv_dir, csv_file)
            df = pd.read_csv(csv_path, nrows=0)  # Just headers
            csv_columns = len(df.columns)
            
            # Get database column count
            cursor.execute(f"PRAGMA table_info({table_name})")
            db_columns = len(cursor.fetchall())
            
            print(f"  CSV columns: {csv_columns}")
            print(f"  DB columns:  {db_columns}")
            
            if csv_columns == db_columns:
                print("  ✅ MATCH")
            else:
                print(f"  ❌ MISMATCH (diff: {db_columns - csv_columns})")
                
        else:
            print(f"  ❌ Table '{table_name}' not found in database")
    
    # Check for extra tables in database
    csv_table_names = [f.replace('.csv', '') for f in csv_files]
    extra_tables = [t for t in db_tables if t not in csv_table_names]
    
    if extra_tables:
        print(f"\n⚠️ Extra tables in database: {extra_tables}")
    
    conn.close()
    print("\nSchema comparison complete.")

if __name__ == "__main__":
    compare_schemas()
