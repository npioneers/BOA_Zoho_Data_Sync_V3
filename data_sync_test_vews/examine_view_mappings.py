#!/usr/bin/env python3
"""
Examine view mappings to understand how CSV and JSON data are properly unified
"""

import sqlite3
import re

def examine_view_schema(db_path):
    """Examine the schema of working FINAL views to understand mapping patterns"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the definition of a working view (invoices)
        print("=== EXAMINING WORKING VIEW: FINAL_view_csv_json_invoices ===\n")
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE name = 'FINAL_view_csv_json_invoices' AND type = 'view'")
        result = cursor.fetchone()
        
        if result:
            view_definition = result[0]
            print("VIEW DEFINITION:")
            print("-" * 80)
            print(view_definition)
            print("-" * 80)
            
            # Parse the UNION structure
            print("\n=== ANALYZING UNION STRUCTURE ===\n")
            
            # Split by UNION ALL to see the two parts
            parts = view_definition.split('UNION ALL')
            
            if len(parts) >= 2:
                print("PART 1 (CSV Source):")
                print(parts[0])
                print("\n" + "="*50 + "\n")
                print("PART 2 (JSON Source):")  
                print(parts[1])
                
                # Look for mapping patterns
                print("\n=== MAPPING ANALYSIS ===\n")
                
                # Extract column mappings
                csv_columns = extract_select_columns(parts[0])
                json_columns = extract_select_columns(parts[1]) if len(parts) > 1 else []
                
                print(f"CSV side has {len(csv_columns)} columns")
                print(f"JSON side has {len(json_columns)} columns")
                
                # Show first few mappings
                print("\nFirst 10 column mappings:")
                for i, (csv_col, json_col) in enumerate(zip(csv_columns[:10], json_columns[:10])):
                    print(f"{i+1:2d}. CSV: {csv_col:<30} | JSON: {json_col}")
            
        else:
            print("Could not find FINAL_view_csv_json_invoices view definition")
            
        # Also check if there are any mapping tables
        print("\n=== CHECKING FOR MAPPING TABLES ===\n")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%mapping%'")
        mapping_tables = cursor.fetchall()
        
        if mapping_tables:
            print("Found mapping tables:")
            for table in mapping_tables:
                print(f"- {table[0]}")
                
                # Show structure of mapping table
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                print(f"  Columns: {[col[1] for col in columns]}")
                
                # Show sample data
                cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
                sample_data = cursor.fetchall()
                if sample_data:
                    print(f"  Sample data:")
                    for row in sample_data:
                        print(f"    {row}")
                print()
        else:
            print("No mapping tables found")
            
        conn.close()
        
    except Exception as e:
        print(f"Error examining view mappings: {e}")

def extract_select_columns(sql_part):
    """Extract column names from SELECT statement"""
    try:
        # Find SELECT and FROM
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_part, re.DOTALL | re.IGNORECASE)
        if select_match:
            columns_text = select_match.group(1)
            
            # Split by comma but be careful of nested functions
            columns = []
            depth = 0
            current_col = ""
            
            for char in columns_text:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                elif char == ',' and depth == 0:
                    columns.append(current_col.strip())
                    current_col = ""
                    continue
                current_col += char
                
            # Add the last column
            if current_col.strip():
                columns.append(current_col.strip())
                
            # Clean up column names (remove AS aliases, etc.)
            cleaned_columns = []
            for col in columns:
                # Extract just the column reference part
                col = col.strip()
                if ' AS ' in col.upper():
                    # Take the part after AS
                    col = col.split(' AS ')[-1].strip()
                cleaned_columns.append(col)
                
            return cleaned_columns
    except Exception as e:
        print(f"Error extracting columns: {e}")
        return []

if __name__ == "__main__":
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\data\database\production.db"
    examine_view_schema(db_path)
