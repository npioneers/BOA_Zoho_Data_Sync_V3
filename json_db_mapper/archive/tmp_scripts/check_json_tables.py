"""
Quick script to check existing JSON tables and mapping tables
"""
import sqlite3

def check_database_tables():
    conn = sqlite3.connect('../data/database/production.db')
    cursor = conn.cursor()
    
    # Check JSON tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%' ORDER BY name")
    json_tables = [row[0] for row in cursor.fetchall()]
    
    # Check existing JSON mapping tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'map_json_%' ORDER BY name")
    json_mapping_tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 60)
    print("DATABASE TABLE ANALYSIS")
    print("=" * 60)
    
    print(f"\nJSON TABLES ({len(json_tables)}):")
    print("-" * 40)
    for table in json_tables:
        print(f"- {table}")
    
    print(f"\nEXISTING JSON MAPPING TABLES ({len(json_mapping_tables)}):")
    print("-" * 40)
    for table in json_mapping_tables:
        print(f"- {table}")
    
    conn.close()
    
    return json_tables, json_mapping_tables

if __name__ == "__main__":
    json_tables, mapping_tables = check_database_tables()
